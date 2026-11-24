"""Exempted obligations (ERVO), SRE reallocation volumes (SRERV), category splits and
the family of timing rules.

EPA's method (91 FR 16438-16440; 91 FR 65703-65706):

* ERVO_X,y = Std_X,y * exempted fuel volume_y, printed to 10 million RINs (two decimals of
  billion RINs) in Table IV.C-2; nearest rounding reproduces 11 of the 12 printed cells.
* Reallocation share alpha applied to the (rounded) ERVOs; the 2026 volume is all of
  2023 plus half of 2024, the 2027 volume is the other half of 2024 plus all of 2025.
* Results rounded to 10 million RINs, downward for the first year and upward for the
  second year.  The proposal's note to Table IV-1 (91 FR 65706) states that "volumes
  ending in five were rounded down for 2026 and rounded up for 2027"; applied to the
  printed obligations that rule reproduces three of the six Set 2 volumes, whereas
  floor/ceiling regardless of the final digit reproduces all six (see tests).
* The additional 2025 exempted RVO is the difference between the actual (13.38 billion
  gallons of exempted fuel) and projected (7.55 billion gallons) ERVO for 2025.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction

from rfsrealloc import CATEGORIES, REALLOCATED_CATEGORIES

MILLION_PER_BILLION = Fraction(1000)


def exempted_rvo(exempt_fuel_bgal: Fraction, standard_percent: Fraction) -> Fraction:
    """Exempted RVO in million RINs from exempted fuel (billion gallons) and a standard (percent)."""
    return exempt_fuel_bgal * standard_percent / 100 * MILLION_PER_BILLION


def round_to(x: Fraction, step: int = 10, mode: str = "nearest") -> int:
    """Round to a multiple of ``step`` million RINs; ``mode`` in {nearest, floor, ceil}."""
    q = x / step
    if mode == "floor":
        return step * math.floor(q)
    if mode == "ceil":
        return step * math.ceil(q)
    if mode == "nearest":
        # ties away from zero, as a spreadsheet ROUND would do
        return step * int(math.floor(q + Fraction(1, 2)))
    raise ValueError(mode)


def ervo_table(
    exempt_fuel: Mapping[int, Fraction], standards_by_year: Mapping[int, Mapping[str, Fraction]], mode: str = "nearest"
) -> dict[int, dict[str, int]]:
    """ERVOs (million RINs, rounded to 10) by year and category."""
    out: dict[int, dict[str, int]] = {}
    for y, fuel in exempt_fuel.items():
        out[y] = {c: round_to(exempted_rvo(fuel, standards_by_year[y][c]), 10, mode) for c in CATEGORIES}
    return out


def set2_srerv(
    ervo: Mapping[int, Mapping[str, Fraction | int]], share: Fraction = Fraction(7, 10), first_year: int = 2026
) -> dict[int, dict[str, int]]:
    """Set 2 SRE reallocation volumes (million RINs) from 2023-2025 ERVOs.

    First year: alpha * (ERVO_2023 + ERVO_2024 / 2), rounded down to 10 million.
    Second year: alpha * (ERVO_2024 / 2 + ERVO_2025), rounded up to 10 million.
    """
    y1, y2 = first_year, first_year + 1
    out: dict[int, dict[str, int]] = {y1: {}, y2: {}}
    for c in REALLOCATED_CATEGORIES:
        e23, e24, e25 = (Fraction(ervo[y][c]) for y in (2023, 2024, 2025))
        out[y1][c] = round_to(share * (e23 + e24 / 2), 10, "floor")
        out[y2][c] = round_to(share * (e24 / 2 + e25), 10, "ceil")
    return out


def additional_ervo(
    actual_exempt_fuel_bgal: Fraction,
    standards_2025: Mapping[str, Fraction],
    projected_ervo_2025: Mapping[str, Fraction | int],
) -> dict[str, int]:
    """Additional 2025 exempted RVO (million RINs): actual (rounded to 10) minus projected."""
    return {
        c: round_to(exempted_rvo(actual_exempt_fuel_bgal, standards_2025[c]), 10, "nearest")
        - int(projected_ervo_2025[c])
        for c in REALLOCATED_CATEGORIES
    }


def allocate(
    base: Mapping[int, Mapping[str, Fraction | int]],
    additional: Mapping[str, Fraction | int],
    w: Fraction,
    first_year: int = 2026,
    rounding: bool = True,
) -> dict[int, dict[str, Fraction]]:
    """Timing-rule family: share ``w`` of the additional volume to the first year, ``1-w`` to the second.

    With ``rounding`` the EPA convention (floor first year, ceiling second year, 10
    million RINs) is applied; otherwise exact values are returned.
    """
    y1, y2 = first_year, first_year + 1
    out: dict[int, dict[str, Fraction]] = {y1: {}, y2: {}}
    for c in REALLOCATED_CATEGORIES:
        a = Fraction(additional[c])
        v1 = Fraction(base[y1][c]) + w * a
        v2 = Fraction(base[y2][c]) + (1 - w) * a
        if rounding:
            out[y1][c] = Fraction(round_to(v1, 10, "floor"))
            out[y2][c] = Fraction(round_to(v2, 10, "ceil"))
        else:
            out[y1][c] = v1
            out[y2][c] = v2
    return out


def million_to_billion(table: Mapping[int, Mapping[str, Fraction | int]]) -> dict[int, dict[str, Fraction]]:
    return {y: {c: Fraction(v) / MILLION_PER_BILLION for c, v in row.items()} for y, row in table.items()}


def category_shares(standards_2025: Mapping[str, Fraction]) -> dict[str, Fraction]:
    """Share of a total-renewable-fuel exempted RVO falling in each nested category.

    Biomass-based diesel share = Std_BBD / Std_RF, other advanced = (Std_AB - Std_BBD - Std_CB) / Std_RF,
    conventional = (Std_RF - Std_AB) / Std_RF, cellulosic = Std_CB / Std_RF.
    """
    rf = standards_2025["RF"]
    return {
        "CB": standards_2025["CB"] / rf,
        "BBD": standards_2025["BBD"] / rf,
        "OA": (standards_2025["AB"] - standards_2025["BBD"] - standards_2025["CB"]) / rf,
        "AB_MINUS_BBD": (standards_2025["AB"] - standards_2025["BBD"]) / rf,
        "CONV": (rf - standards_2025["AB"]) / rf,
    }


@dataclass(frozen=True)
class RetroactivityMeasure:
    """Share of the additional obligation imposed for a compliance period already elapsed
    at the final rule's effective date (RIN-years divided by total RINs reallocated)."""

    w: float
    effective_date: dt.date
    elapsed_fraction_first_year: float
    elapsed_fraction_second_year: float
    retroactive_share: float


def elapsed_fraction(effective_date: dt.date, year: int) -> float:
    start = dt.date(year, 1, 1)
    end = dt.date(year + 1, 1, 1)
    if effective_date <= start:
        return 0.0
    if effective_date >= end:
        return 1.0
    return (effective_date - start).days / (end - start).days


def retroactivity(w: float, effective_date: dt.date, first_year: int = 2026) -> RetroactivityMeasure:
    f1 = elapsed_fraction(effective_date, first_year)
    f2 = elapsed_fraction(effective_date, first_year + 1)
    return RetroactivityMeasure(w, effective_date, f1, f2, w * f1 + (1 - w) * f2)


def single_year_step(
    base_std: Mapping[int, Mapping[str, Fraction]], new_std: Mapping[int, Mapping[str, Fraction]]
) -> dict[int, dict[str, Fraction]]:
    """Change in each year's standard relative to the Set 2 standards (percentage points)."""
    return {y: {c: new_std[y][c] - base_std[y][c] for c in new_std[y]} for y in new_std}

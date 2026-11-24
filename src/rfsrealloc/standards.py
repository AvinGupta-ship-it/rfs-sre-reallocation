"""Percentage-standard equations of 40 CFR 80.1405 with EPA rounding conventions.

Equations (40 CFR 80.1405(c), 91 FR 16488, transcribed from the Set 2 final rule)::

    Std_X,i = 100 * (RFV_X,i + SRERV_X,i) / [(G_i - RG_i) - GE_i + (D_i - RD_i) - DE_i]

with SRERV_CB,i = 0 (no cellulosic reallocation volume).  Paragraph (b) (all other
years) is the same expression without SRERV.  Arithmetic is exact (rationals); the
published standards are rounded half-up to two decimals of a percent.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from rfsrealloc import CATEGORIES
from rfsrealloc.inputs import StandardInputs

ZERO = Fraction(0)


def obligated_volume(inp: StandardInputs) -> Fraction:
    """Projected non-renewable, non-exempt gasoline and diesel (billion gallons)."""
    return (inp.G - inp.RG) - inp.GE + (inp.D - inp.RD) - inp.DE


def percentage_standard(numerator: Fraction, denominator: Fraction) -> Fraction:
    """Exact percentage standard from a numerator (billion RINs) and denominator (billion gallons)."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return 100 * numerator / denominator


def numerators(inp: StandardInputs, srerv: Mapping[str, Fraction] | None = None) -> dict[str, Fraction]:
    out: dict[str, Fraction] = {}
    for c in CATEGORIES:
        if c not in inp.rfv:
            continue
        add = ZERO if (srerv is None or c == "CB") else srerv.get(c, ZERO)
        out[c] = inp.rfv[c] + add
    return out


def standards(inp: StandardInputs, srerv: Mapping[str, Fraction] | None = None) -> dict[str, Fraction]:
    """Exact standards (percent) for every category present in ``inp.rfv``."""
    den = obligated_volume(inp)
    return {c: percentage_standard(n, den) for c, n in numerators(inp, srerv).items()}


def round_half_up(x: Fraction, places: int = 2) -> Decimal:
    """EPA publishes percentage standards to two decimals; ties are rounded up."""
    d = Decimal(x.numerator) / Decimal(x.denominator)
    return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def rounded_standards(
    inp: StandardInputs, srerv: Mapping[str, Fraction] | None = None, places: int = 2
) -> dict[str, Decimal]:
    return {c: round_half_up(v, places) for c, v in standards(inp, srerv).items()}


def implied_denominator_interval(published: Decimal, numerator: Fraction, places: int = 2) -> tuple[Fraction, Fraction]:
    """Interval of denominators consistent with a published (rounded) standard."""
    half = Fraction(1, 2 * 10**places)
    p = Fraction(published)
    lo = 100 * numerator / (p + half)
    hi = 100 * numerator / (p - half)
    return lo, hi


def dstd_dnumerator(denominator: Fraction) -> Fraction:
    """Partial derivative of a standard with respect to its numerator (percent per billion RINs)."""
    return Fraction(100) / denominator


def dstd_ddenominator(numerator: Fraction, denominator: Fraction) -> Fraction:
    """Partial derivative of a standard with respect to the denominator (percent per billion gallons)."""
    return -100 * numerator / (denominator * denominator)


def effective_volume(std_percent: Fraction | float, actual_obligated_volume: Fraction | float) -> float:
    """RINs implied by a standard applied to a realized obligated volume (billion RINs)."""
    return float(std_percent) / 100.0 * float(actual_obligated_volume)

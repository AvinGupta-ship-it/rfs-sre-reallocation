"""Reproduction of EPA's RIN-cost table (proposal Table VI-1; docket memorandum
EPA-HQ-OAR-2024-0505-0961).

Total RIN cost per gallon of obligated fuel = sum over categories of the standard
(as a fraction) times the RIN price for the marginal RIN type: cellulosic (D3), biomass-
based diesel (D4), other advanced (D5), conventional (D6).  "Other advanced" and
"conventional" are differences of nested standards.  The price impact of an alternative
relative to the existing standards equals the change in total RIN cost, as in the
memorandum's Table 2.  No price inference is made beyond reproducing the table.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from rfsrealloc import ALTERNATIVES

D_CODE_FOR = {"CB": "D3", "BBD": "D4", "OA": "D5", "CONV": "D6"}


def implied_categories(std: Mapping[str, Fraction | float]) -> dict[str, float]:
    """Cellulosic, BBD, other advanced and conventional percentages from nested standards."""
    cb, bbd, ab, rf = (float(std[c]) for c in ("CB", "BBD", "AB", "RF"))
    return {"CB": cb, "BBD": bbd, "OA": ab - bbd - cb, "CONV": rf - ab}


def total_rin_cost_cents(std: Mapping[str, Fraction | float], prices: Mapping[str, Fraction | float]) -> float:
    """Cents per gallon of obligated gasoline or diesel."""
    parts = implied_categories(std)
    return sum(parts[c] / 100.0 * float(prices[D_CODE_FOR[c]]) for c in parts) * 100.0


def rin_cost_table(
    standards: Mapping[str, Mapping[int, Mapping[str, Fraction | float]]],
    prices: Mapping[str, Fraction | float],
    rounded_inputs: Mapping[str, Mapping[int, Mapping[str, float]]] | None = None,
) -> dict[str, dict[int, float]]:
    """Total RIN cost (cents per gallon) by alternative and year."""
    src = rounded_inputs if rounded_inputs is not None else standards
    return {alt: {y: total_rin_cost_cents(src[alt][y], prices) for y in src[alt]} for alt in ALTERNATIVES if alt in src}


def price_impact_relative(
    cost_table: Mapping[str, Mapping[int, float]], reference: str = "set2"
) -> dict[str, dict[int, float]]:
    """Change in total RIN cost relative to the existing standards (cents per gallon)."""
    return {alt: {y: cost_table[alt][y] - cost_table[reference][y] for y in cost_table[alt]} for alt in cost_table}

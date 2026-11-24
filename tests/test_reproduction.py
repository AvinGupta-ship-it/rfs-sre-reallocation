"""E1 and E7: exact reproduction of published standards, reallocation volumes and RIN costs."""

from __future__ import annotations

from fractions import Fraction

import pandas as pd
import pytest

from rfsrealloc import ALTERNATIVES, CATEGORIES, REALLOCATED_CATEGORIES, costs
from rfsrealloc import reallocation as ra
from rfsrealloc import standards as st
from rfsrealloc.inputs import (
    exempted_fuel,
    exempted_rvo_table,
    published_standards,
    rin_prices,
    set2_inputs,
    srerv,
    table_vi1,
    value,
)


@pytest.mark.parametrize("alternative", [*ALTERNATIVES, "no_srerv"])
@pytest.mark.parametrize("year", [2026, 2027])
def test_published_standards_reproduce(transcribed: pd.DataFrame, alternative: str, year: int) -> None:
    inp = set2_inputs(transcribed)[year]
    s = srerv(transcribed, alternative)[year]
    pub = published_standards(transcribed, alternative)[year]
    got = st.rounded_standards(inp, s)
    for c in CATEGORIES:
        assert str(got[c]) == pub[c], (alternative, year, c, got[c], pub[c])


def test_denominators(transcribed: pd.DataFrame) -> None:
    inp = set2_inputs(transcribed)
    assert st.obligated_volume(inp[2026]) == Fraction("173.02")
    assert st.obligated_volume(inp[2027]) == Fraction("171.24")


def test_published_standards_consistent_with_total_applicable_volume(transcribed: pd.DataFrame) -> None:
    """100 * 26.81 / 15.50 brackets the exact denominator within rounding."""
    inp = set2_inputs(transcribed)
    den = st.obligated_volume(inp[2026])
    lo, hi = st.implied_denominator_interval(st.round_half_up(Fraction("15.4953")), Fraction("26.81"))
    assert lo <= den <= hi


def test_ervo_table_reproduces_except_documented_cell(transcribed: pd.DataFrame) -> None:
    stds, pub = exempted_rvo_table(transcribed)
    fuel = exempted_fuel(transcribed)
    got = ra.ervo_table({y: fuel[y]["total"] for y in (2023, 2024, 2025)}, stds)
    mismatches = [(y, c) for y in (2023, 2024, 2025) for c in CATEGORIES if got[y][c] != int(pub[y][c])]
    # The 2024 advanced-biofuel cell (300 million) needs the unrounded exempted volume
    # (between 7.7836 and 7.79 billion gallons); the published 7.78 gives 290.
    assert mismatches == [(2024, "AB")]


def test_set2_srerv_requires_floor_ceiling_convention(transcribed: pd.DataFrame) -> None:
    _, pub = exempted_rvo_table(transcribed)
    got = ra.set2_srerv(pub)
    for y in (2026, 2027):
        for c in REALLOCATED_CATEGORIES:
            assert got[y][c] == int(value(transcribed, "srerv_set2_million", "set2", str(y), c))
    # nearest-10 rounding of the same inputs would give 220 (not 210) for 2026 BBD
    nearest = ra.round_to(Fraction(7, 10) * (Fraction(200) + Fraction(220) / 2), 10, "nearest")
    assert nearest == 220


def test_table_iv1_reproduces(transcribed: pd.DataFrame) -> None:
    stds, pub = exempted_rvo_table(transcribed)
    base = ra.set2_srerv(pub)
    add = ra.additional_ervo(
        value(transcribed, "proposal_2025_sre", "exempted_fuel_volume", "2025"), stds[2025], pub[2025]
    )
    assert add == {"BBD": 180, "AB": 250, "RF": 770}
    for alt, w in (("equal", Fraction(1, 2)), ("all2027", Fraction(0))):
        alloc = ra.allocate(base, add, w)
        s = srerv(transcribed, alt)
        for y in (2026, 2027):
            for c in REALLOCATED_CATEGORIES:
                assert int(alloc[y][c]) == int(s[y][c] * 1000), (alt, y, c)


def test_category_split_matches_manual_expectation(transcribed: pd.DataFrame) -> None:
    stds, _ = exempted_rvo_table(transcribed)
    shares = ra.category_shares(stds[2025])
    assert abs(float(shares["BBD"]) * 770 - 180) < 10
    assert abs(float(shares["AB_MINUS_BBD"]) * 770 - 70) < 10
    assert abs(float(shares["CONV"]) * 770 - 520) < 10


def test_rin_cost_table_reproduces(transcribed: pd.DataFrame) -> None:
    prices = rin_prices(transcribed, "proposal")
    vi1 = table_vi1(transcribed)
    for alt in ALTERNATIVES:
        key = "existing" if alt == "set2" else alt
        pub = published_standards(transcribed, alt)
        for y in (2026, 2027):
            got = round(costs.total_rin_cost_cents({c: float(pub[y][c]) for c in CATEGORIES}, prices), 1)
            exp = float(
                vi1[(vi1["alternative"] == key) & (vi1["year"] == y) & (vi1["category"] == "RINCOST")]["value"].iloc[0]
            )
            assert got == exp, (alt, y, got, exp)
            parts = costs.implied_categories({c: float(pub[y][c]) for c in CATEGORIES})
            for cat in ("OA", "CONV"):
                exp_part = float(
                    vi1[(vi1["alternative"] == key) & (vi1["year"] == y) & (vi1["category"] == cat)]["value"].iloc[0]
                )
                assert round(parts[cat], 2) == exp_part


def test_price_impact_relative_matches_memorandum(transcribed: pd.DataFrame) -> None:
    prices = rin_prices(transcribed, "proposal")
    rounded = {
        alt: {y: {c: float(published_standards(transcribed, alt)[y][c]) for c in CATEGORIES} for y in (2026, 2027)}
        for alt in ALTERNATIVES
    }
    table = costs.rin_cost_table({}, prices, rounded)
    rel = costs.price_impact_relative(table)
    for alt in ("equal", "all2027"):
        for y in (2026, 2027):
            exp = value(transcribed, "price_impact_relative", alt, str(y), "GASOLINE")
            assert abs(round(rel[alt][y], 1) - float(exp)) < 1e-9

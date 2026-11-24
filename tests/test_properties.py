"""Property-based tests of invariants: non-negativity, monotonicity, exact/float agreement,
rounding conventions, conservation in carryover accounting, timing-rule identities."""

from __future__ import annotations

import datetime as dt
from fractions import Fraction

from hypothesis import given, settings
from hypothesis import strategies as hs

from rfsrealloc import carryover as co
from rfsrealloc import reallocation as ra
from rfsrealloc import standards as st
from rfsrealloc.inputs import StandardInputs

frac = hs.fractions(min_value=Fraction(1, 100), max_value=Fraction(300), max_denominator=10_000)


def _inputs(
    G: Fraction, D: Fraction, RG: Fraction, RD: Fraction, GE: Fraction, DE: Fraction, rfv: Fraction
) -> StandardInputs:
    return StandardInputs(2026, {"CB": rfv / 20, "BBD": rfv / 3, "AB": rfv / 2, "RF": rfv}, G, D, RG, RD, GE, DE)


@given(G=frac, D=frac, rfv=frac, s=hs.fractions(min_value=0, max_value=Fraction(1, 2), max_denominator=1000))
@settings(max_examples=200)
def test_standards_positive_and_monotone_in_numerator(G: Fraction, D: Fraction, rfv: Fraction, s: Fraction) -> None:
    inp = _inputs(G, D, G * s / 2, D * s / 2, G * s / 4, D * s / 4, rfv)
    base = st.standards(inp)
    more = st.standards(inp, {"RF": Fraction(1, 10), "BBD": Fraction(1, 10), "AB": Fraction(1, 10)})
    assert all(v > 0 for v in base.values())
    assert more["RF"] > base["RF"] and more["CB"] == base["CB"]
    # increasing the denominator lowers every standard
    bigger = st.standards(inp.with_fuel(G + 1, D))
    assert all(bigger[c] < base[c] for c in base)
    # exact and float evaluation agree
    for c, v in base.items():
        assert abs(float(v) - 100 * float(st.numerators(inp)[c]) / float(st.obligated_volume(inp))) < 1e-9


@given(x=hs.fractions(min_value=0, max_value=Fraction(10_000), max_denominator=1000))
def test_round_to_conventions(x: Fraction) -> None:
    f, n, c = (ra.round_to(x, 10, m) for m in ("floor", "nearest", "ceil"))
    assert f <= n <= c and f % 10 == 0 and c % 10 == 0 and c - f <= 10


@given(w=hs.fractions(min_value=0, max_value=1, max_denominator=100), add=hs.integers(min_value=0, max_value=2000))
def test_allocation_conserves_additional_volume(w: Fraction, add: int) -> None:
    base = {2026: {"BBD": 210, "AB": 280, "RF": 990}, 2027: {"BBD": 250, "AB": 340, "RF": 1040}}
    out = ra.allocate(base, {"BBD": add, "AB": add, "RF": add}, w, rounding=False)
    for c in ("BBD", "AB", "RF"):
        assert out[2026][c] + out[2027][c] == base[2026][c] + base[2027][c] + add
    rounded = ra.allocate(base, {"BBD": add, "AB": add, "RF": add}, w, rounding=True)
    for c in ("BBD", "AB", "RF"):
        assert abs(rounded[2026][c] + rounded[2027][c] - (base[2026][c] + base[2027][c] + add)) <= 10


@given(w=hs.floats(min_value=0, max_value=1), days=hs.integers(min_value=0, max_value=1500))
def test_retroactivity_bounds_and_monotonicity(w: float, days: int) -> None:
    d = dt.date(2026, 1, 1) + dt.timedelta(days=days)
    r = ra.retroactivity(w, d)
    assert 0.0 <= r.retroactive_share <= 1.0
    later = ra.retroactivity(w, d + dt.timedelta(days=30))
    assert later.retroactive_share >= r.retroactive_share - 1e-12
    # putting more into the first year never lowers retroactivity once the first year has begun
    assert (
        ra.retroactivity(min(1.0, w + 0.1), d).retroactive_share >= r.retroactive_share - 1e-12
        or r.elapsed_fraction_first_year < r.elapsed_fraction_second_year
    )


@given(
    rvo=hs.floats(min_value=1, max_value=50),
    bank=hs.floats(min_value=0, max_value=20),
    gen=hs.floats(min_value=0, max_value=60),
    cap=hs.floats(min_value=0, max_value=0.5),
)
def test_carryover_conservation(rvo: float, bank: float, gen: float, cap: float) -> None:
    acc = co.account_year(2026, rvo, bank, gen, cap, allow_deficit=True)
    assert acc.conserved(1e-9)
    assert 0 <= acc.carryover_used_brins <= min(bank, cap * rvo) + 1e-12
    assert acc.bank_out_brins >= 0 and acc.expired_brins >= 0 and acc.deficit_brins >= 0


@given(days=hs.integers(min_value=0, max_value=800))
def test_next_quarterly_deadline(days: int) -> None:
    d = dt.date(2026, 10, 16) + dt.timedelta(days=days)
    q = co.next_quarterly_deadline(d)
    assert q > d and (q.month, q.day) in co.QUARTERLY_DEADLINES and (q - d).days <= 121

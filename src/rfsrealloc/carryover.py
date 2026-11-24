"""Compliance-timing accounting under the carryover-RIN cap and deficit rules.

Rules (40 CFR 80.1427): RINs are valid for the year generated and the following year;
prior-year RINs may satisfy at most 20 percent of an obligation; a deficit may be
carried one year.  Accounting identity for each year t::

    bank_{t-1} + generation_t = RVO_t + bank_t + expired_t

where ``bank_t`` is the vintage-t surplus carried into t+1, ``carryover_used_t`` is
``min(bank_{t-1}, cap * RVO_t)``, ``expired_t = bank_{t-1} - carryover_used_t``, and
``bank_t = generation_t - (RVO_t - carryover_used_t)``.  No prices are inferred.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class YearAccount:
    year: int
    rvo_brins: float
    bank_in_brins: float
    cap_brins: float
    carryover_used_brins: float
    new_rins_required_brins: float
    generation_brins: float
    bank_out_brins: float
    expired_brins: float
    deficit_brins: float

    def conserved(self, tol: float = 1e-9) -> bool:
        lhs = self.bank_in_brins + self.generation_brins
        rhs = self.rvo_brins - self.deficit_brins + self.bank_out_brins + self.expired_brins
        return abs(lhs - rhs) <= tol


def account_year(
    year: int, rvo: float, bank_in: float, generation: float, cap: float = 0.20, allow_deficit: bool = False
) -> YearAccount:
    cap_brins = cap * rvo
    used = min(bank_in, cap_brins)
    required_new = rvo - used
    deficit = 0.0
    if generation < required_new:
        if not allow_deficit:
            raise ValueError(f"{year}: new RINs required {required_new:.3f} exceed generation {generation:.3f}")
        deficit = required_new - generation
    bank_out = max(0.0, generation - required_new)
    expired = bank_in - used
    return YearAccount(year, rvo, bank_in, cap_brins, used, required_new, generation, bank_out, expired, deficit)


def obligation(std_percent: float, obligated_volume_bgal: float) -> float:
    """Aggregate obligation in billion RINs."""
    return std_percent / 100.0 * obligated_volume_bgal


def two_year_accounting(
    standards: Mapping[int, float],
    obligated_volumes: Mapping[int, float],
    generation: Mapping[int, float],
    bank0: float,
    cap: float = 0.20,
    allow_deficit: bool = True,
) -> list[YearAccount]:
    """Sequential accounting over the years in ``standards`` (ascending)."""
    out: list[YearAccount] = []
    bank = bank0
    for y in sorted(standards):
        acc = account_year(y, obligation(standards[y], obligated_volumes[y]), bank, generation[y], cap, allow_deficit)
        out.append(acc)
        bank = acc.bank_out_brins
    return out


def accounts_frame(accounts: list[YearAccount], label: str) -> pd.DataFrame:
    rows = [{"alternative": label, **a.__dict__, "conserved": a.conserved()} for a in accounts]
    return pd.DataFrame(rows)


def coverage_within_cap(alt: list[YearAccount], base: list[YearAccount]) -> dict[int, float | None]:
    """Fraction of the additional obligation (alt minus base) met by extra carryover use within the cap."""
    out: dict[int, float | None] = {}
    for a, b in zip(alt, base, strict=True):
        add = a.rvo_brins - b.rvo_brins
        out[a.year] = None if add <= 0 else (a.carryover_used_brins - b.carryover_used_brins) / add
    return out


QUARTERLY_DEADLINES: tuple[tuple[int, int], ...] = ((3, 31), (6, 1), (9, 1), (12, 1))


def next_quarterly_deadline(after: dt.date) -> dt.date:
    """First quarterly reporting deadline (40 CFR 80.1451(f)(2)) strictly after ``after``."""
    candidates = []
    for y in (after.year, after.year + 1):
        for m, d in QUARTERLY_DEADLINES:
            c = dt.date(y, m, d)
            if c > after:
                candidates.append(c)
    return min(candidates)


def compliance_deadline_after_revision(effective_date: dt.date, current_deadline: dt.date) -> dt.date:
    """40 CFR 80.1451(f)(1)(i)(C)(1): the later of the next quarterly deadline after the
    revised standard's effective date and the otherwise applicable deadline."""
    return max(next_quarterly_deadline(effective_date), current_deadline)


def deadline_if_not_finalized(proposal_date: dt.date, current_deadline: dt.date) -> dt.date:
    """(C)(3): if neither finalized nor withdrawn within 12 months, the next quarterly
    deadline that is 12 months after publication of the proposal (or the current deadline if later)."""
    twelve = dt.date(proposal_date.year + 1, proposal_date.month, proposal_date.day)
    return max(next_quarterly_deadline(twelve - dt.timedelta(days=1)), current_deadline)

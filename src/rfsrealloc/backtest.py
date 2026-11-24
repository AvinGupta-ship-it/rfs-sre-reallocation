"""Historical evaluation of exemption projections and of timing rules.

Two questions are asked of the record of exempted obligations by compliance year
(EPA dashboard Table SRE-1), the dates on which those obligations became known
(decision actions), and the dates on which each year's standards were set:

1. How accurate was a prospective projection of the exempted obligation (the
   three-year average EPA used in 2020 and 2026) when applied to each past year?
2. For a reallocation rule that assigns share ``w`` of a year's exemption shortfall to
   the next year and ``1 - w`` to the year after, how much of the reallocated amount
   was unknown when the receiving year's standard was set?  The absolute size of that
   unknown part is the forecast error of the total applicable volume attributable to
   the timing rule.  A lead-time policy delays the true-up until a standard is set at
   least ``L`` months after the decision.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import pandas as pd

from rfsrealloc.config import BacktestConfig


@dataclass(frozen=True)
class DecisionRecord:
    """Exempted RVO (million RINs) for a compliance year, decided on ``date``."""

    year: int
    date: dt.date
    amount_mrins: float


def decision_records(decisions: pd.DataFrame, dates: dict[str, dt.date]) -> list[DecisionRecord]:
    acts = decisions[(decisions["variable"] == "exempted_rvo") & (decisions["action"].isin(dates))]
    return [DecisionRecord(int(r["year"]), dates[str(r["action"])], float(r["value"])) for _, r in acts.iterrows()]


def known_amount(records: list[DecisionRecord], year: int, as_of: dt.date) -> float:
    return float(sum(r.amount_mrins for r in records if r.year == year and r.date <= as_of))


def final_amounts(sre1: pd.DataFrame) -> dict[int, float]:
    df = sre1.dropna(subset=["exempted_rvo_mrins"])
    return {int(y): float(v) for y, v in zip(df["year"], df["exempted_rvo_mrins"], strict=True)}


def moving_average_projection(final: dict[int, float], year: int, window: int) -> float | None:
    vals = [final[y] for y in range(year - window, year) if y in final]
    if len(vals) < window:
        return None
    return float(np.mean(vals))


def projection_backtest(
    final: dict[int, float],
    cfg: BacktestConfig,
    known_at: dict[int, dt.date] | None = None,
    records: list[DecisionRecord] | None = None,
) -> pd.DataFrame:
    """Error of the three-year-average projection applied to each year.

    Two variants: ``hindsight`` uses the final record of prior years; ``real_time`` uses
    only amounts decided before the rule for the target year was published (requires
    ``known_at`` and ``records``).
    """
    rows: list[dict[str, float | int | None]] = []
    for y in range(cfg.projection_first_year, cfg.last_target_year + 1):
        if y not in final or (y > 2025 and final[y] == 0):
            continue
        hind = moving_average_projection(final, y, cfg.projection_window_years)
        rt: float | None = None
        if known_at is not None and records is not None and y in known_at:
            src_years = range(y - cfg.projection_window_years, y)
            if all(any(r.year == yy for r in records) for yy in src_years):
                vals = [known_amount(records, yy, known_at[y]) for yy in src_years]
                rt = float(np.mean(vals))
        rows.append(
            {
                "year": y,
                "realized_mrins": final[y],
                "projection_hindsight_mrins": hind,
                "projection_real_time_mrins": rt,
                "error_hindsight": None if hind is None else final[y] - hind,
                "error_real_time": None if rt is None else final[y] - rt,
            }
        )
    return pd.DataFrame(rows)


def timing_rule_backtest(
    final: dict[int, float],
    records: list[DecisionRecord],
    rule_dates: dict[int, dt.date],
    w_grid: np.ndarray,
    cfg: BacktestConfig,
    lead_months: int = 0,
) -> pd.DataFrame:
    """Unknown share of reallocated amounts at the time each receiving year's standard was set.

    For source year ``y`` with final exempted RVO ``E_y`` and a rule ``w``, the amount
    ``w E_y`` is reallocated to year ``y+1`` and ``(1-w) E_y`` to year ``y+2``.  With a
    lead-time policy of ``L`` months, an amount decided on date ``d`` can only be
    reallocated to a year whose standard is set on or after ``d + L``; later-decided
    amounts move to the first eligible receiving year ("adaptive"), while the fixed
    rule leaves them as a forecast error of the receiving year.
    """
    rows: list[dict[str, float | int]] = []
    years = [y for y in range(cfg.first_target_year, cfg.last_target_year + 1) if y in final]
    recorded_years = {r.year for r in records}
    for w in w_grid:
        for t in years:
            if t not in rule_dates:
                continue
            if any((y in final and final[y] > 0 and y not in recorded_years) for y in (t - 1, t - 2)):
                continue
            set_date = rule_dates[t]
            err_fixed = 0.0
            err_adaptive = 0.0
            total = 0.0
            for y, share in ((t - 1, float(w)), (t - 2, 1 - float(w))):
                if y not in final or share == 0.0:
                    continue
                # amounts on the decided (petition-based) basis so that shares are bounded by one
                total += share * sum(r.amount_mrins for r in records if r.year == y)
                for rec in (r for r in records if r.year == y):
                    eligible = rec.date + dt.timedelta(days=int(30.4375 * lead_months)) <= set_date
                    if not eligible:
                        err_fixed += share * rec.amount_mrins
                # adaptive: amounts not eligible for t are deferred, contributing no error to t
                # (they are reallocated to a later year); error is the share decided after
                # the last set date in the record, which can never be reallocated prospectively
                last_set = max(rule_dates.values())
                for rec in (r for r in records if r.year == y):
                    if rec.date + dt.timedelta(days=int(30.4375 * lead_months)) > last_set:
                        err_adaptive += share * rec.amount_mrins
            rows.append(
                {
                    "w": float(w),
                    "target_year": t,
                    "reallocated_mrins": total,
                    "unknown_fixed_mrins": err_fixed,
                    "unknown_adaptive_mrins": err_adaptive,
                    "lead_months": lead_months,
                }
            )
    df = pd.DataFrame(rows)
    return df


def backtest_summary(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["lead_months", "w"])
    out = g.agg(
        mae_fixed=("unknown_fixed_mrins", "mean"),
        max_fixed=("unknown_fixed_mrins", "max"),
        mae_adaptive=("unknown_adaptive_mrins", "mean"),
        mean_reallocated=("reallocated_mrins", "mean"),
    ).reset_index()
    out["unknown_share_fixed"] = out["mae_fixed"] / out["mean_reallocated"].replace(0, np.nan)
    return out


def decision_lag_summary(lags: pd.DataFrame) -> pd.DataFrame:
    g = lags.groupby("year")["lag_years"]
    return g.agg(["count", "mean", "median", "min", "max"]).reset_index()

"""Uncertainty model for exempted volumes, fuel-use projections and decision timing,
with Monte Carlo propagation to standards and Sobol sensitivity indices.

Three sources of uncertainty (manual section 1.B.3):

(a) *Exemption revision*: the ratio of the exempted RVO reported in compliance data to
    the petition-based estimate announced with the decisions.  Empirical pairs come from
    EPA decision documents (petition-based) and the EPA dashboard (reported).
(b) *Fuel-use projection error*: log ratio of reported to projected non-renewable
    gasoline-plus-diesel volume for past standards, from the EPA dashboard, by lead time.
(c) *Decision timing*: lag between the end of a compliance year and the decision on
    its petitions, from the per-petition dashboard table.

All random draws take an explicit :class:`numpy.random.Generator`; parallel streams are
spawned from a :class:`numpy.random.SeedSequence` so results do not depend on worker
count.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from rfsrealloc import REALLOCATED_CATEGORIES
from rfsrealloc.config import PipelineConfig
from rfsrealloc.inputs import StandardInputs
from rfsrealloc.standards import obligated_volume

FloatArray = NDArray[np.float64]

ACTIONS_AFTER_RULE: dict[str, dt.date] = {}


# --------------------------------------------------------------------------- (a)


def revision_pairs(decisions: pd.DataFrame, dates: dict[str, dt.date], sre1: pd.DataFrame) -> pd.DataFrame:
    """Petition-based exempted RVO (sum of decision actions) versus reported RVO by year.

    Only years with a ``Reported`` dashboard value and at least one decision action are
    retained.  ``ratio`` is reported divided by petition-based.
    """
    acts = decisions[(decisions["variable"] == "exempted_rvo") & (decisions["action"].isin(dates))]
    petition = acts.groupby("year")["value"].sum().rename("petition_based_mrins")
    rep = sre1[sre1["data_type"] == "Reported"].set_index("year")["exempted_rvo_mrins"].rename("reported_mrins")
    df = pd.concat([petition, rep], axis=1).dropna()
    df = df[df["petition_based_mrins"] > 0]
    df["ratio"] = df["reported_mrins"] / df["petition_based_mrins"]
    df["log_ratio"] = np.log(df["ratio"])
    return df.reset_index().rename(columns={"index": "year"})


def later_decision_additions(decisions: pd.DataFrame, dates: dict[str, dt.date], rule_date: dt.date) -> pd.DataFrame:
    """Exempted RVO decided after ``rule_date`` as a share of the amount known at that date.

    Measures how much the exempted obligation for a year grew through decisions issued
    after a rule relied on it (the second component of revision risk).
    """
    acts = decisions[decisions["variable"] == "exempted_rvo"].copy()
    acts["date"] = acts["action"].map(dates)
    acts = acts.dropna(subset=["date"])
    before = acts[acts["date"] <= rule_date].groupby("year")["value"].sum()
    after = acts[acts["date"] > rule_date].groupby("year")["value"].sum()
    df = pd.concat([before.rename("known_mrins"), after.rename("later_mrins")], axis=1).fillna(0.0)
    df = df[df["known_mrins"] > 0]
    df["later_share"] = df["later_mrins"] / df["known_mrins"]
    return df.reset_index()


# --------------------------------------------------------------------------- (b)


def fuel_error_samples(
    rvo1: pd.DataFrame, rule_dates: dict[int, dt.date], revised_years: set[int] | None = None
) -> pd.DataFrame:
    """Log ratio of reported to projected non-renewable gasoline-plus-diesel volume.

    ``lead_years`` is the time from the final rule's publication to mid-year of the
    compliance year.  Years whose projection was revised after the fact (negative lead)
    are flagged as retroactive.
    """
    df = rvo1.dropna(subset=["reported_total_gal"]).copy()
    df = df[df["year"].isin(rule_dates)]
    df["log_ratio"] = np.log(df["reported_total_gal"] / df["projected_use_gal"])
    df["ratio"] = df["reported_total_gal"] / df["projected_use_gal"]
    df["rule_date"] = df["year"].map(rule_dates)
    mid = pd.to_datetime(df["year"].astype(str) + "-07-01").dt.date
    df["lead_years"] = [(m - r).days / 365.25 for m, r in zip(mid, df["rule_date"], strict=True)]
    df["retroactive"] = df["year"].isin(revised_years or set()) | (df["lead_years"] < 0)
    # obligated-volume error: reported obligated versus projected non-exempt volume
    df["obligated_log_ratio"] = np.log(
        df["reported_obligated_gal"] / (df["projected_use_gal"] - df["projected_exempt_gal"])
    )
    return df[
        [
            "year",
            "projected_use_gal",
            "projected_exempt_gal",
            "reported_total_gal",
            "reported_obligated_gal",
            "ratio",
            "log_ratio",
            "obligated_log_ratio",
            "rule_date",
            "lead_years",
            "retroactive",
        ]
    ].reset_index(drop=True)


def lead_bin(lead_years: float, edges: list[float]) -> int:
    """Index of the lead-time bin (edges sorted ascending; last bin is open)."""
    idx = 0
    for i, e in enumerate(edges):
        if lead_years >= e:
            idx = i
    return idx


# --------------------------------------------------------------------------- draws


@dataclass(frozen=True)
class UncertaintyInputs:
    revision_log_ratios: FloatArray
    fuel_log_errors_by_bin: dict[int, FloatArray]
    lead_bin_first: int
    lead_bin_second: int
    uniform_half_width: float
    revision_model: str
    fuel_model: str
    correlation: float


def build_uncertainty_inputs(
    cfg: PipelineConfig, pairs: pd.DataFrame, fuel: pd.DataFrame, lead_first: float, lead_second: float
) -> UncertaintyInputs:
    edges = cfg.uncertainty.fuel_error.lead_time_bins_years
    f = fuel if cfg.uncertainty.fuel_error.include_retroactive_rules else fuel[~fuel["retroactive"]]
    by_bin: dict[int, FloatArray] = {}
    for i in range(len(edges)):
        sel = f[[lead_bin(float(x), edges) == i for x in f["lead_years"]]]
        by_bin[i] = np.asarray(sel["log_ratio"], dtype=float)
    # pool with the nearest bin if a bin has fewer than three observations
    all_vals = np.asarray(f["log_ratio"], dtype=float)
    for i in by_bin:
        if by_bin[i].size < 3:
            by_bin[i] = all_vals
    return UncertaintyInputs(
        revision_log_ratios=np.asarray(pairs["log_ratio"], dtype=float),
        fuel_log_errors_by_bin=by_bin,
        lead_bin_first=lead_bin(lead_first, edges),
        lead_bin_second=lead_bin(lead_second, edges),
        uniform_half_width=cfg.uncertainty.revision.uniform_half_width,
        revision_model=cfg.uncertainty.revision.model,
        fuel_model=cfg.uncertainty.fuel_error.model,
        correlation=cfg.uncertainty.fuel_error.correlation_between_years,
    )


def draw_revision_ratio(rng: np.random.Generator, u: UncertaintyInputs, n: int) -> FloatArray:
    """Reported/petition-based ratio of the 2025 exempted RVO."""
    if u.revision_model == "uniform" or u.revision_log_ratios.size == 0:
        return rng.uniform(1 - u.uniform_half_width, 1 + u.uniform_half_width, size=n)
    # smoothed bootstrap: resample empirical log ratios with a Gaussian kernel (Silverman)
    x = u.revision_log_ratios
    h = (
        0.9 * min(x.std(ddof=1), (np.quantile(x, 0.75) - np.quantile(x, 0.25)) / 1.34) * x.size ** (-0.2)
        if x.size > 1
        else 0.0
    )
    base = rng.choice(x, size=n, replace=True)
    return np.exp(base + rng.normal(0.0, h, size=n))


def draw_fuel_errors(rng: np.random.Generator, u: UncertaintyInputs, n: int) -> tuple[FloatArray, FloatArray]:
    """Log fuel-use errors for the first and second year with the configured rank correlation."""

    def one(vals: FloatArray, z: FloatArray) -> FloatArray:
        if u.fuel_model == "lognormal":
            return vals.mean() + vals.std(ddof=1) * z
        # smoothed bootstrap driven by the Gaussian z through its rank
        order = np.argsort(np.argsort(z))
        sorted_sample = np.sort(rng.choice(vals, size=n, replace=True))
        h = (
            0.9
            * min(vals.std(ddof=1), (np.quantile(vals, 0.75) - np.quantile(vals, 0.25)) / 1.34)
            * vals.size ** (-0.2)
        )
        return sorted_sample[order] + rng.normal(0.0, h, size=n)

    rho = u.correlation
    z1 = rng.normal(size=n)
    z2 = rho * z1 + np.sqrt(max(0.0, 1 - rho**2)) * rng.normal(size=n)
    return one(u.fuel_log_errors_by_bin[u.lead_bin_first], z1), one(u.fuel_log_errors_by_bin[u.lead_bin_second], z2)


# --------------------------------------------------------------------------- model


@dataclass(frozen=True)
class TimingModel:
    """Deterministic map from (revision ratio, fuel errors, timing share w) to outcomes."""

    inputs: dict[int, StandardInputs]
    base_srerv_mrins: dict[int, dict[str, float]]
    actual_ervo_2025_mrins: dict[str, float]
    projected_ervo_2025_mrins: dict[str, float]
    first_year: int = 2026

    def denominators(self) -> dict[int, float]:
        return {y: float(obligated_volume(i)) for y, i in self.inputs.items()}

    def additional(self, r: FloatArray, cat: str) -> FloatArray:
        """Additional 2025 exempted RVO (million RINs) if the reported/petition ratio is r."""
        return r * self.actual_ervo_2025_mrins[cat] - self.projected_ervo_2025_mrins[cat]

    def standards(self, r: FloatArray, w: float, cat: str) -> tuple[FloatArray, FloatArray]:
        """Exact (unrounded) standards for both years in percent."""
        y1, y2 = self.first_year, self.first_year + 1
        den = self.denominators()
        add = self.additional(r, cat)
        n1 = float(self.inputs[y1].rfv[cat]) + (self.base_srerv_mrins[y1][cat] + w * add) / 1000.0
        n2 = float(self.inputs[y2].rfv[cat]) + (self.base_srerv_mrins[y2][cat] + (1 - w) * add) / 1000.0
        return 100.0 * n1 / den[y1], 100.0 * n2 / den[y2]

    def realized_rins(self, std_pct: FloatArray, year: int, log_fuel_error: FloatArray) -> FloatArray:
        """RINs (billion) implied by a standard applied to the realized obligated volume."""
        den = self.denominators()[year]
        return std_pct / 100.0 * den * np.exp(log_fuel_error)


def evaluate(
    model: TimingModel, r: FloatArray, e1: FloatArray, e2: FloatArray, w_grid: FloatArray, cat: str = "RF"
) -> dict[str, FloatArray]:
    """Vectorised evaluation over draws (rows) and timing shares (columns)."""
    y1, y2 = model.first_year, model.first_year + 1
    n, m = r.size, w_grid.size
    std1 = np.empty((n, m))
    std2 = np.empty((n, m))
    for j, w in enumerate(w_grid):
        s1, s2 = model.standards(r, float(w), cat)
        std1[:, j] = s1
        std2[:, j] = s2
    base1, base2 = model.standards(np.ones(1), 0.0, cat)
    rins1 = std1 / 100.0 * model.denominators()[y1] * np.exp(e1)[:, None]
    rins2 = std2 / 100.0 * model.denominators()[y2] * np.exp(e2)[:, None]
    intended1 = (
        float(model.inputs[y1].rfv[cat])
        + (model.base_srerv_mrins[y1][cat] + w_grid * model.additional(np.ones(1), cat)[0]) / 1000.0
    )
    intended2 = (
        float(model.inputs[y2].rfv[cat])
        + (model.base_srerv_mrins[y2][cat] + (1 - w_grid) * model.additional(np.ones(1), cat)[0]) / 1000.0
    )
    # standards if the exemption estimate is not updated (petition-based, r = 1)
    s1_fixed, s2_fixed = model.standards(np.ones(1), 0.0, cat)
    return {
        "std_first": std1,
        "std_second": std2,
        "delta_first_vs_set2": std1 - base1[0],
        "delta_second_vs_set2": std2 - base2[0],
        "realized_rins_first": rins1,
        "realized_rins_second": rins2,
        "realized_minus_intended_first": rins1 - intended1[None, :],
        "realized_minus_intended_second": rins2 - intended2[None, :],
        "revision_first": std1 - np.stack([model.standards(np.ones(n), float(w), cat)[0] for w in w_grid], axis=1),
        "revision_second": std2 - np.stack([model.standards(np.ones(n), float(w), cat)[1] for w in w_grid], axis=1),
    }


def summarize(
    results: dict[str, FloatArray], w_grid: FloatArray, quantiles: tuple[float, ...] = (0.05, 0.5, 0.95)
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for name, arr in results.items():
        for j, w in enumerate(w_grid):
            col = arr[:, j]
            row: dict[str, float | str] = {
                "quantity": name,
                "w": float(w),
                "mean": float(col.mean()),
                "sd": float(col.std(ddof=1)),
                "mean_abs": float(np.abs(col).mean()),
                "mcse_mean": float(col.std(ddof=1) / np.sqrt(col.size)),
                "n": float(col.size),
            }
            for q in quantiles:
                row[f"q{int(q * 100):02d}"] = float(np.quantile(col, q))
            rows.append(row)
    return pd.DataFrame(rows)


def convergence(
    results: dict[str, FloatArray], w_grid: FloatArray, checkpoints: list[int], w_values: tuple[float, ...] = (0.0, 0.5)
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for name in ("std_first", "std_second", "realized_minus_intended_second", "revision_second"):
        arr = results[name]
        for w in w_values:
            j = int(np.argmin(np.abs(w_grid - w)))
            for n in checkpoints:
                col = arr[:n, j]
                rows.append(
                    {
                        "quantity": name,
                        "w": w,
                        "n": float(n),
                        "mean": float(col.mean()),
                        "sd": float(col.std(ddof=1)),
                        "mcse_mean": float(col.std(ddof=1) / np.sqrt(n)),
                        "mcse_sd_relative": float(1 / np.sqrt(2 * (n - 1))),
                    }
                )
    return pd.DataFrame(rows)


def spawn_generators(seed: int, n_workers: int) -> list[np.random.Generator]:
    ss = np.random.SeedSequence(seed)
    return [np.random.default_rng(child) for child in ss.spawn(n_workers)]


def monte_carlo_draws(cfg: PipelineConfig, u: UncertaintyInputs) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Draw (r, e_first, e_second) using worker-independent streams."""
    gens = spawn_generators(cfg.monte_carlo.seed, cfg.monte_carlo.n_workers)
    n = cfg.monte_carlo.n_draws
    sizes = [n // len(gens) + (1 if i < n % len(gens) else 0) for i in range(len(gens))]
    rs, e1s, e2s = [], [], []
    for g, k in zip(gens, sizes, strict=True):
        rs.append(draw_revision_ratio(g, u, k))
        a, b = draw_fuel_errors(g, u, k)
        e1s.append(a)
        e2s.append(b)
    return np.concatenate(rs), np.concatenate(e1s), np.concatenate(e2s)


# --------------------------------------------------------------------------- Sobol


def sobol_indices(
    cfg: PipelineConfig, model: TimingModel, u: UncertaintyInputs, w: float, cat: str = "RF"
) -> pd.DataFrame:
    """First-order and total Sobol indices (Saltelli sampling, Jansen estimators) with bootstrap intervals.

    Factors are independent by construction: the revision ratio and the two fuel-use
    errors (the latter drawn with the configured correlation set to zero here, so that
    the variance decomposition is well defined; the correlated case is reported by the
    Monte Carlo summaries instead).
    """
    from SALib.analyze import sobol as sobol_analyze
    from SALib.sample import sobol as sobol_sample

    x = u.revision_log_ratios
    rev_bounds = (
        [float(np.exp(np.min(x) - 0.02)), float(np.exp(np.max(x) + 0.02))]
        if x.size
        else [1 - u.uniform_half_width, 1 + u.uniform_half_width]
    )
    f1 = u.fuel_log_errors_by_bin[u.lead_bin_first]
    f2 = u.fuel_log_errors_by_bin[u.lead_bin_second]
    names = ["revision_ratio", "fuel_error_first", "fuel_error_second"]
    problem: dict[str, Any] = {
        "num_vars": 3,
        "names": names,
        "bounds": [rev_bounds, [float(np.min(f1)), float(np.max(f1))], [float(np.min(f2)), float(np.max(f2))]],
    }
    sample = sobol_sample.sample(
        problem, cfg.sobol.n_base, calc_second_order=False, seed=cfg.monte_carlo.seed + cfg.sobol.seed_offset
    )
    r, e1, e2 = sample[:, 0], sample[:, 1], sample[:, 2]
    out = evaluate(model, r, e1, e2, np.array([w]), cat)
    rows: list[dict[str, float | str]] = []
    for name in ("std_first", "std_second", "realized_rins_first", "realized_rins_second"):
        y = out[name][:, 0]
        if np.allclose(y.std(), 0.0):
            for n_ in names:
                rows.append(
                    {"output": name, "factor": n_, "S1": 0.0, "S1_conf": 0.0, "ST": 0.0, "ST_conf": 0.0, "w": w}
                )
            continue
        si = sobol_analyze.analyze(
            problem,
            y,
            calc_second_order=False,
            num_resamples=cfg.sobol.bootstrap,
            seed=cfg.monte_carlo.seed + cfg.sobol.seed_offset,
            print_to_console=False,
        )
        for i, n_ in enumerate(names):
            rows.append(
                {
                    "output": name,
                    "factor": n_,
                    "S1": float(si["S1"][i]),
                    "S1_conf": float(si["S1_conf"][i]),
                    "ST": float(si["ST"][i]),
                    "ST_conf": float(si["ST_conf"][i]),
                    "w": w,
                }
            )
    return pd.DataFrame(rows)


def analytic_variance_shares(model: TimingModel, u: UncertaintyInputs, w: float, cat: str = "RF") -> dict[str, float]:
    """Linearised variance shares of a standard: revision versus fuel-use error (dimensionless check)."""
    y1, y2 = model.first_year, model.first_year + 1
    den = model.denominators()
    a = model.actual_ervo_2025_mrins[cat] / 1000.0
    var_r = (
        float(np.var(np.exp(u.revision_log_ratios), ddof=1))
        if u.revision_log_ratios.size > 1
        else (u.uniform_half_width**2) / 3
    )
    s1 = (100.0 * w * a / den[y1]) ** 2 * var_r
    s2 = (100.0 * (1 - w) * a / den[y2]) ** 2 * var_r
    return {"var_std_first_from_revision": s1, "var_std_second_from_revision": s2}


def frac_dict(d: dict[str, Fraction | int]) -> dict[str, float]:
    return {k: float(v) for k, v in d.items() if k in REALLOCATED_CATEGORIES}

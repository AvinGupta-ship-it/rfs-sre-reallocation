"""Single entry point: ``python -m rfsrealloc.pipeline run --config configs/paper.yaml``.

Runs experiments E1-E7 of the project specification, writes every result table with a
provenance sidecar under ``results/<name>/``, and generates the LaTeX macros and tables
consumed by the manuscript and the comment attachment.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from rfsrealloc import ALTERNATIVES, CATEGORIES, REALLOCATED_CATEGORIES, costs
from rfsrealloc import backtest as bt
from rfsrealloc import carryover as co
from rfsrealloc import reallocation as ra
from rfsrealloc import standards as st
from rfsrealloc import uncertainty as un
from rfsrealloc.config import PipelineConfig, config_hash, load_config
from rfsrealloc.data import PROCESSED
from rfsrealloc.data import dashboard as dash
from rfsrealloc.inputs import (
    ENTRY_A,
    ENTRY_B,
    carryover_2024,
    deadline,
    decision_dates,
    exempted_fuel,
    exempted_rvo_table,
    load_transcribed,
    load_wide,
    published_standards,
    reconcile,
    regulatory_parameter,
    rin_prices,
    set2_inputs,
    sre_decisions,
    srerv,
    table_vi1,
    text_value,
    value,
)
from rfsrealloc.provenance import ROOT, write_sidecar
from rfsrealloc.reporting import write_tables, write_values

PAPER_GENERATED = ROOT / "paper" / "generated"


class Pipeline:
    def __init__(self, cfg: PipelineConfig, write_paper: bool = False) -> None:
        self.cfg = cfg
        self.hash = config_hash(cfg)
        self.out = cfg.results_dir
        self.out.mkdir(parents=True, exist_ok=True)
        self.df = load_transcribed(ENTRY_A)
        self.values: dict[str, Any] = {}
        self.write_paper = write_paper
        self.first = cfg.timing.first_year
        self.second = cfg.timing.second_year

    # ------------------------------------------------------------------ helpers
    def save(self, name: str, df: pd.DataFrame, seed: int | None = None, **meta: Any) -> Path:
        path = self.out / f"{name}.csv"
        df.to_csv(path, index=False)
        write_sidecar(path, config_hash=self.hash, seed=seed, metadata=meta or None)
        return path

    def inputs(self) -> dict[int, Any]:
        return set2_inputs(self.df)

    # ------------------------------------------------------------------ E1
    def e1_reproduction(self) -> None:
        inp = self.inputs()
        rows: list[dict[str, Any]] = []
        for alt in (*ALTERNATIVES, "no_srerv"):
            s = srerv(self.df, alt)
            pub = published_standards(self.df, alt)
            for y in (self.first, self.second):
                den = st.obligated_volume(inp[y])
                nums = st.numerators(inp[y], s[y])
                for c in CATEGORIES:
                    exact = st.percentage_standard(nums[c], den)
                    rounded = st.round_half_up(exact)
                    lo, hi = st.implied_denominator_interval(rounded, nums[c])
                    rows.append(
                        {
                            "alternative": alt,
                            "year": y,
                            "category": c,
                            "numerator_brins": float(nums[c]),
                            "denominator_bgal": float(den),
                            "exact_percent": float(exact),
                            "rounded_percent": str(rounded),
                            "published_percent": pub[y][c],
                            "match": str(rounded) == pub[y][c],
                            "residual_points": float(exact) - float(pub[y][c]),
                            "implied_denominator_lo": float(lo),
                            "implied_denominator_hi": float(hi),
                        }
                    )
        rep = pd.DataFrame(rows)
        self.save("e1_standards_reproduction", rep)
        self.values["nStandardsChecked"] = int(len(rep))
        self.values["nStandardsMatched"] = int(rep["match"].sum())
        self.values["denominatorFirst"] = round(float(st.obligated_volume(inp[self.first])), 2)
        self.values["denominatorSecond"] = round(float(st.obligated_volume(inp[self.second])), 2)
        self.values["maxAbsResidualPoints"] = round(float(rep["residual_points"].abs().max()), 4)
        # intersection of implied denominator intervals per year (all alternatives/categories)
        inter = (
            rep.groupby("year")
            .agg(lo=("implied_denominator_lo", "max"), hi=("implied_denominator_hi", "min"))
            .reset_index()
        )
        self.save("e1_implied_denominator_intervals", inter)
        for _, r in inter.iterrows():
            key = "First" if int(float(str(r["year"]))) == self.first else "Second"
            self.values[f"impliedDenominatorLo{key}"] = round(float(r["lo"]), 3)
            self.values[f"impliedDenominatorHi{key}"] = round(float(r["hi"]), 3)

        # ERVO table and SRERVs
        stds, ervo_pub = exempted_rvo_table(self.df)
        fuel = exempted_fuel(self.df)
        computed = ra.ervo_table({y: fuel[y]["total"] for y in (2023, 2024, 2025)}, stds)
        erows = []
        for y in (2023, 2024, 2025):
            for c in CATEGORIES:
                exact = ra.exempted_rvo(fuel[y]["total"], stds[y][c])
                erows.append(
                    {
                        "year": y,
                        "category": c,
                        "exempted_fuel_bgal": float(fuel[y]["total"]),
                        "standard_percent": float(stds[y][c]),
                        "exact_mrins": float(exact),
                        "rounded_mrins": computed[y][c],
                        "published_mrins": int(ervo_pub[y][c]),
                        "match": computed[y][c] == int(ervo_pub[y][c]),
                    }
                )
        e = pd.DataFrame(erows)
        self.save("e1_ervo_reproduction", e)
        self.values["nErvoChecked"] = int(len(e))
        self.values["nErvoMatched"] = int(e["match"].sum())
        mism = e[~e["match"]]
        self.values["ervoMismatchDescription"] = (
            "; ".join(
                f"{r.year} {r.category}: computed {r.rounded_mrins}, published {r.published_mrins}"
                for r in mism.itertuples()
            )
            or "none"
        )

        base = ra.set2_srerv(ervo_pub)
        base_nearest = {
            y: {
                c: ra.round_to(
                    Fraction(7, 10) * (Fraction(ervo_pub[2023][c]) + Fraction(ervo_pub[2024][c]) / 2)
                    if y == self.first
                    else Fraction(7, 10) * (Fraction(ervo_pub[2024][c]) / 2 + Fraction(ervo_pub[2025][c])),
                    10,
                    "nearest",
                )
                for c in REALLOCATED_CATEGORIES
            }
            for y in (self.first, self.second)
        }
        srows = []
        for y in (self.first, self.second):
            for c in REALLOCATED_CATEGORIES:
                pubv = int(value(self.df, "srerv_set2_million", "set2", str(y), c))
                srows.append(
                    {
                        "year": y,
                        "category": c,
                        "floor_ceiling_mrins": base[y][c],
                        "nearest_mrins": base_nearest[y][c],
                        "published_mrins": pubv,
                        "match_floor_ceiling": base[y][c] == pubv,
                        "match_nearest": base_nearest[y][c] == pubv,
                    }
                )
        srerv_rep = pd.DataFrame(srows)
        self.save("e1_srerv_reproduction", srerv_rep)
        self.values["nSrervFloorCeilMatched"] = int(srerv_rep["match_floor_ceiling"].sum())
        self.values["nSrervNearestMatched"] = int(srerv_rep["match_nearest"].sum())

        actual_fuel = value(self.df, "proposal_2025_sre", "exempted_fuel_volume", "2025")
        add = ra.additional_ervo(actual_fuel, stds[2025], ervo_pub[2025])
        arows = []
        for alt, w in (("equal", Fraction(1, 2)), ("all2027", Fraction(0))):
            alloc = ra.allocate(base, add, w)
            s = srerv(self.df, alt)
            for y in (self.first, self.second):
                for c in REALLOCATED_CATEGORIES:
                    arows.append(
                        {
                            "alternative": alt,
                            "year": y,
                            "category": c,
                            "computed_mrins": int(alloc[y][c]),
                            "published_mrins": int(s[y][c] * 1000),
                            "match": int(alloc[y][c]) == int(s[y][c] * 1000),
                        }
                    )
        tab = pd.DataFrame(arows)
        self.save("e1_table_iv1_reproduction", tab)
        self.values["nTableIVOneMatched"] = int(tab["match"].sum())
        self.values["nTableIVOneChecked"] = int(len(tab))
        self.values["additionalBBD"] = add["BBD"]
        self.values["additionalAB"] = add["AB"]
        self.values["additionalRF"] = add["RF"]
        shares = ra.category_shares(stds[2025])
        for k, v in shares.items():
            self.values[f"share{k}"] = round(float(v), 4)
        self.values["additionalExactRF"] = round(
            float(ra.exempted_rvo(actual_fuel, stds[2025]["RF"])) - int(ervo_pub[2025]["RF"]), 1
        )
        self._base_srerv = base
        self._stds_2025 = stds[2025]
        self._ervo_pub = ervo_pub
        self._additional = add

    # ------------------------------------------------------------------ E2/E3/E4 (Monte Carlo)
    def monte_carlo(self) -> None:
        cfg = self.cfg
        inp = self.inputs()
        decisions = sre_decisions(self.df)
        dates = decision_dates(self.df)
        sre1 = dash.sre_table1()
        pairs = un.revision_pairs(decisions, dates, sre1)
        self.save("e2_revision_pairs", pairs)
        self.values["nRevisionPairs"] = int(len(pairs))
        self.values["revisionRatioMin"] = round(float(pairs["ratio"].min()), 3)
        self.values["revisionRatioMax"] = round(float(pairs["ratio"].max()), 3)
        self.values["revisionRatioMean"] = round(float(pairs["ratio"].mean()), 3)
        self.values["revisionRatioSd"] = round(float(pairs["ratio"].std(ddof=1)), 3)
        # 2025 specific: petition-based versus reported as of the dashboard
        rep25 = sre1[(sre1["year"] == 2025)]
        reported_rvo_2025 = float(str(rep25["exempted_rvo_mrins"].iloc[0]))
        self.values["reported2025ExemptedRvo"] = reported_rvo_2025
        self.values["reported2025ExemptedVolume"] = float(str(rep25["exempted_volume_mgal"].iloc[0]))
        self.values["reported2025Ratio"] = round(reported_rvo_2025 / 1760.0, 4)
        rule_date = dt.date.fromisoformat(text_value(self.df, "rule_dates", "publication_date", "2026"))
        later = un.later_decision_additions(decisions, dates, rule_date)
        self.save("e2_later_decisions", later)

        rvo1 = dash.rvo_table1()
        rule_dates = {
            int(y): dt.date.fromisoformat(text_value(self.df, "rule_dates", "publication_date", str(y)))
            for y in range(2011, 2028)
        }
        rule_dates[2020] = dt.date.fromisoformat(text_value(self.df, "rule_dates", "revision_publication_date", "2020"))
        fuel = un.fuel_error_samples(rvo1, rule_dates, revised_years={2020})
        self.save("e3_fuel_projection_errors", fuel)
        nonretro = fuel[~fuel["retroactive"]]
        self.values["nFuelErrorsAll"] = int(len(fuel))
        self.values["nFuelErrorsProspective"] = int(len(nonretro))
        self.values["fuelErrorMeanPct"] = round(100 * float(np.expm1(nonretro["log_ratio"]).mean()), 2)
        self.values["fuelErrorSdPct"] = round(100 * float(np.expm1(nonretro["log_ratio"]).std(ddof=1)), 2)
        self.values["fuelErrorMinPct"] = round(100 * float(np.expm1(nonretro["log_ratio"]).min()), 2)
        self.values["fuelErrorMaxPct"] = round(100 * float(np.expm1(nonretro["log_ratio"]).max()), 2)
        mid1 = dt.date(self.first, 7, 1)
        mid2 = dt.date(self.second, 7, 1)
        lead1 = (mid1 - rule_dates[self.first]).days / 365.25
        lead2 = (mid2 - rule_dates[self.second]).days / 365.25
        u = un.build_uncertainty_inputs(cfg, pairs, fuel, lead1, lead2)

        model = un.TimingModel(
            inputs=inp,
            base_srerv_mrins={y: {c: float(v) for c, v in self._base_srerv[y].items()} for y in self._base_srerv},
            actual_ervo_2025_mrins={
                c: float(
                    ra.round_to(
                        ra.exempted_rvo(
                            value(self.df, "proposal_2025_sre", "exempted_fuel_volume", "2025"), self._stds_2025[c]
                        ),
                        10,
                        "nearest",
                    )
                )
                for c in REALLOCATED_CATEGORIES
            },
            projected_ervo_2025_mrins={c: float(self._ervo_pub[2025][c]) for c in REALLOCATED_CATEGORIES},
            first_year=self.first,
        )
        self._model = model
        r, e1, e2 = un.monte_carlo_draws(cfg, u)
        w_grid = np.linspace(0.0, 1.0, cfg.timing.w_grid_points)
        results = un.evaluate(model, r, e1, e2, w_grid, "RF")
        summary = un.summarize(results, w_grid)
        self.save("e2e4_monte_carlo_summary", summary, seed=cfg.monte_carlo.seed, n_draws=cfg.monte_carlo.n_draws)
        conv = un.convergence(results, w_grid, cfg.monte_carlo.convergence_checkpoints)
        self.save("mc_convergence", conv, seed=cfg.monte_carlo.seed)
        # deterministic sensitivities
        den = model.denominators()
        srows = []
        for alt, w in (("equal", 0.5), ("all2027", 0.0)):
            for y, wi in ((self.first, w), (self.second, 1 - w)):
                srows.append(
                    {
                        "alternative": alt,
                        "year": y,
                        "dstd_dervo_points_per_brins": 100 * wi / den[y],
                        "dstd_per_100mrins": 100 * wi * 0.1 / den[y],
                    }
                )
        self.save("e2_revision_sensitivity", pd.DataFrame(srows))
        self.values["dStdPer100MRinsFirst"] = round(100 * 0.1 / den[self.first], 4)
        self.values["dStdPer100MRinsSecond"] = round(100 * 0.1 / den[self.second], 4)

        def pick(name: str, w: float, col: str) -> float:
            sub = summary[(summary["quantity"] == name) & (np.isclose(summary["w"], w))]
            return float(sub[col].iloc[0])

        for label, w in (("Equal", 0.5), ("AllSecond", 0.0)):
            for yl, name in (("First", "std_first"), ("Second", "std_second")):
                self.values[f"stdSd{yl}{label}"] = round(pick(name, w, "sd"), 4)
                self.values[f"stdQ05{yl}{label}"] = round(pick(name, w, "q05"), 3)
                self.values[f"stdQ95{yl}{label}"] = round(pick(name, w, "q95"), 3)
                self.values[f"stdMean{yl}{label}"] = round(pick(name, w, "mean"), 3)
                self.values[f"revisionMeanAbs{yl}{label}"] = round(pick("revision_" + yl.lower(), w, "mean_abs"), 4)
                self.values[f"realizedMinusIntendedSd{yl}{label}"] = round(
                    pick("realized_minus_intended_" + yl.lower(), w, "sd"), 3
                )
                self.values[f"realizedMinusIntendedMean{yl}{label}"] = round(
                    pick("realized_minus_intended_" + yl.lower(), w, "mean"), 3
                )
                self.values[f"realizedMinusIntendedQ05{yl}{label}"] = round(
                    pick("realized_minus_intended_" + yl.lower(), w, "q05"), 3
                )
                self.values[f"realizedMinusIntendedQ95{yl}{label}"] = round(
                    pick("realized_minus_intended_" + yl.lower(), w, "q95"), 3
                )
        # Monte Carlo standard error check for the headline quantity (sd of the 2027 standard, equal split)
        head = conv[(conv["quantity"] == "std_second") & (conv["w"] == 0.5)].iloc[-1]
        self.values["mcseHeadlineRelative"] = round(float(head["mcse_sd_relative"]), 5)
        self.values["mcDraws"] = int(cfg.monte_carlo.n_draws)

        # E4 trade-off table
        trows = []
        base_exact = {
            y: float(
                st.percentage_standard(
                    st.numerators(inp[y], {c: Fraction(v) / 1000 for c, v in self._base_srerv[y].items()})["RF"],
                    st.obligated_volume(inp[y]),
                )
            )
            for y in (self.first, self.second)
        }
        for w in w_grid:
            s1, s2 = model.standards(np.ones(1), float(w), "RF")
            row: dict[str, float] = {
                "w": float(w),
                "std_first": float(s1[0]),
                "std_second": float(s2[0]),
                "step_first_points": float(s1[0]) - base_exact[self.first],
                "step_second_points": float(s2[0]) - base_exact[self.second],
                "max_step_points": max(float(s1[0]) - base_exact[self.first], float(s2[0]) - base_exact[self.second]),
                "sd_std_first": pick("std_first", float(w), "sd"),
                "sd_std_second": pick("std_second", float(w), "sd"),
                "mean_abs_revision_first": pick("revision_first", float(w), "mean_abs"),
                "mean_abs_revision_second": pick("revision_second", float(w), "mean_abs"),
                "sd_realized_minus_intended_first": pick("realized_minus_intended_first", float(w), "sd"),
                "sd_realized_minus_intended_second": pick("realized_minus_intended_second", float(w), "sd"),
            }
            for name, d in cfg.timing.finalization_scenarios.items():
                row[f"retroactive_share_{name}"] = ra.retroactivity(float(w), d, self.first).retroactive_share
            trows.append(row)
        trade = pd.DataFrame(trows)
        self.save("e4_timing_tradeoff", trade, seed=cfg.monte_carlo.seed)
        for name, d in cfg.timing.finalization_scenarios.items():
            for label, w in (("Equal", 0.5), ("AllSecond", 0.0)):
                self.values[f"retro{label}{_camel(name)}"] = round(
                    ra.retroactivity(w, d, self.first).retroactive_share, 3
                )
        self.values["stepSecondAllSecond"] = round(
            float(trade.loc[np.isclose(trade["w"], 0.0), "step_second_points"].iloc[0]), 3
        )
        self.values["stepFirstEqual"] = round(
            float(trade.loc[np.isclose(trade["w"], 0.5), "step_first_points"].iloc[0]), 3
        )
        self.values["stepSecondEqual"] = round(
            float(trade.loc[np.isclose(trade["w"], 0.5), "step_second_points"].iloc[0]), 3
        )

        # Sobol indices for both alternatives (independent factors)
        sob = pd.concat(
            [un.sobol_indices(cfg, model, u, 0.5, "RF"), un.sobol_indices(cfg, model, u, 0.0, "RF")], ignore_index=True
        )
        self.save("sobol_indices", sob, seed=cfg.monte_carlo.seed + cfg.sobol.seed_offset, n_base=cfg.sobol.n_base)
        for alt, w in (("Equal", 0.5), ("AllSecond", 0.0)):
            for out_name, yl in (
                ("std_second", "StdSecond"),
                ("realized_rins_second", "RealizedSecond"),
                ("std_first", "StdFirst"),
                ("realized_rins_first", "RealizedFirst"),
            ):
                sub = sob[(sob["output"] == out_name) & (sob["w"] == w)].set_index("factor")
                self.values[f"sobolRevision{yl}{alt}"] = round(float(str(sub.loc["revision_ratio", "ST"])), 3)
                self.values[f"sobolFuel{yl}{alt}"] = round(
                    float(str(sub.loc["fuel_error_second" if "Second" in yl else "fuel_error_first", "ST"])), 3
                )
        # Updated standards if the reported 2025 figure replaces the petition-based figure
        urows = []
        rep_ratio = reported_rvo_2025 / model.actual_ervo_2025_mrins["RF"]
        add_rep = {
            c: Fraction(int(round(rep_ratio * model.actual_ervo_2025_mrins[c] / 10)) * 10)
            - Fraction(int(self._ervo_pub[2025][c]))
            for c in REALLOCATED_CATEGORIES
        }
        for alt, wf in (("equal", Fraction(1, 2)), ("all2027", Fraction(0))):
            alloc = ra.allocate(self._base_srerv, add_rep, wf)
            pub = published_standards(self.df, alt)
            for y in (self.first, self.second):
                rs = st.rounded_standards(inp[y], {c: alloc[y][c] / 1000 for c in REALLOCATED_CATEGORIES})
                for c in CATEGORIES:
                    urows.append(
                        {
                            "alternative": alt,
                            "year": y,
                            "category": c,
                            "srerv_reported_basis_mrins": float(alloc[y].get(c, Fraction(0))),
                            "standard_reported_basis": str(rs[c]),
                            "standard_published": pub[y][c],
                            "changed": str(rs[c]) != pub[y][c],
                        }
                    )
        upd = pd.DataFrame(urows)
        self.save("e2_reported_basis_update", upd)
        self.values["nStandardsChangedByReportedBasis"] = int(upd["changed"].sum())
        self.values["additionalRFReportedBasis"] = float(add_rep["RF"])

    # ------------------------------------------------------------------ E5
    def backtest(self) -> None:
        cfg = self.cfg
        sre1 = dash.sre_table1()
        decisions = sre_decisions(self.df)
        dates = decision_dates(self.df)
        records = bt.decision_records(decisions, dates)
        final = bt.final_amounts(sre1)
        rule_dates = {
            int(y): dt.date.fromisoformat(text_value(self.df, "rule_dates", "publication_date", str(y)))
            for y in range(2011, 2028)
        }
        proj = bt.projection_backtest(final, cfg.backtest, known_at=rule_dates, records=records)
        self.save("e5_projection_backtest", proj)
        err = proj.dropna(subset=["error_hindsight"])
        self.values["projMaeHindsight"] = round(float(err["error_hindsight"].abs().mean()), 0)
        self.values["projMaxAbsHindsight"] = round(float(err["error_hindsight"].abs().max()), 0)
        self.values["projMaeHindsightPct"] = round(
            100 * float((err["error_hindsight"].abs() / err["realized_mrins"]).mean()), 1
        )
        self.values["nProjYears"] = int(len(err))
        errrt = proj.dropna(subset=["error_real_time"])
        self.values["nProjYearsRealTime"] = int(len(errrt))
        self.values["projMaeRealTime"] = round(float(errrt["error_real_time"].abs().mean()), 0) if len(errrt) else 0.0
        w_grid = np.linspace(0.0, 1.0, 11)
        frames = [
            bt.timing_rule_backtest(final, records, rule_dates, w_grid, cfg.backtest, lead_months=L)
            for L in cfg.backtest.lead_time_policies_months
        ]
        tb = pd.concat(frames, ignore_index=True)
        self.save("e5_timing_rule_backtest", tb)
        summ = bt.backtest_summary(tb)
        self.save("e5_timing_rule_summary", summ)
        s0 = summ[summ["lead_months"] == 0]
        self.values["btUnknownShareEqual"] = round(
            float(s0.loc[np.isclose(s0["w"], 0.5), "unknown_share_fixed"].iloc[0]), 3
        )
        self.values["btUnknownShareAllSecond"] = round(
            float(s0.loc[np.isclose(s0["w"], 0.0), "unknown_share_fixed"].iloc[0]), 3
        )
        self.values["btUnknownShareAllFirst"] = round(
            float(s0.loc[np.isclose(s0["w"], 1.0), "unknown_share_fixed"].iloc[0]), 3
        )
        self.values["btMaeEqual"] = round(float(s0.loc[np.isclose(s0["w"], 0.5), "mae_fixed"].iloc[0]), 0)
        self.values["btMaeAllSecond"] = round(float(s0.loc[np.isclose(s0["w"], 0.0), "mae_fixed"].iloc[0]), 0)
        t0 = tb[tb["lead_months"] == 0]
        self.values["btFirstTargetYear"] = int(t0["target_year"].min())
        self.values["btLastTargetYear"] = int(t0["target_year"].max())
        self.values["btNTargetYears"] = int(t0["target_year"].nunique())
        fully = t0[(np.isclose(t0["w"], 0.5)) & (t0["reallocated_mrins"] > 0)]
        self.values["btNYearsFullyUnknownEqual"] = int(
            (fully["unknown_fixed_mrins"] >= fully["reallocated_mrins"] - 1e-9).sum()
        )
        for ty in (self.first, self.second):
            for w, lab in ((0.5, "Equal"), (0.0, "AllSecond")):
                sub = t0[(np.isclose(t0["w"], w)) & (t0["target_year"] == ty)]
                if len(sub):
                    tot = float(sub["reallocated_mrins"].iloc[0])
                    self.values[f"btUnknown{lab}{'First' if ty == self.first else 'Second'}"] = round(
                        float(sub["unknown_fixed_mrins"].iloc[0]), 0
                    )
                    self.values[f"btUnknownShare{lab}{'First' if ty == self.first else 'Second'}"] = (
                        round(float(sub["unknown_fixed_mrins"].iloc[0]) / tot, 3) if tot > 0 else 0.0
                    )
        lags = dash.decision_lags(dash.sre_table3())
        self.save(
            "e5_decision_lags",
            lags[["year", "submitted", "decision", "decision_date", "lag_years", "submission_to_decision_years"]],
        )
        self.save("e5_decision_lag_summary", bt.decision_lag_summary(lags))
        sel = lags[lags["year"].isin(cfg.uncertainty.decision_lag_years)]
        self.values["lagYearsFirst"] = int(min(cfg.uncertainty.decision_lag_years))
        self.values["lagYearsLast"] = int(max(cfg.uncertainty.decision_lag_years))
        self.values["lagMedianYears"] = round(float(sel["lag_years"].median()), 2)
        self.values["lagMinYears"] = round(float(sel["lag_years"].min()), 2)
        self.values["lagMaxYears"] = round(float(sel["lag_years"].max()), 2)
        self.values["nLagPetitions"] = int(len(sel))
        l25 = lags[lags["year"] == 2025]
        self.values["lag2025MedianYears"] = round(float(l25["lag_years"].median()), 2)
        pend = dash.pending_petitions(dash.sre_table3())
        self.values["nPending2025"] = int((pend["year"] == 2025).sum())
        self.values["nPending2026"] = int((pend["year"] == 2026).sum())
        self.values["nPending2027"] = int((pend["year"] == 2027).sum())
        self.save("e5_pending_petitions", pend)

    # ------------------------------------------------------------------ E6
    def carryover(self) -> None:
        cfg = self.cfg
        inp = self.inputs()
        cap = float(Fraction(regulatory_parameter(self.df, "carryover_cap")))
        c24 = carryover_2024(self.df)
        bank_ria = (
            float(str(c24.loc["RF", "effective" if cfg.carryover.bank_basis == "ria_effective_2024" else "carryover"]))
            / 1e9
        )
        add25 = (
            float(value(self.df, "proposal_2025_sre", "additional_exempted_rvo", "2025"))
            if cfg.carryover.additional_2025_rins_to_bank
            else 0.0
        )
        bank0 = bank_ria + add25
        self.values["bankRia"] = round(bank_ria, 2)
        self.values["bankBaseline"] = round(bank0, 2)
        den = {y: float(st.obligated_volume(inp[y])) for y in (self.first, self.second)}
        gen = {y: float(inp[y].rfv["RF"]) for y in (self.first, self.second)}
        frames = []
        banks = {"baseline": bank0, **cfg.carryover.hypothetical_bank_scenarios}
        base_accounts: dict[str, list[co.YearAccount]] = {}
        for bname, b0 in banks.items():
            for alt in ALTERNATIVES:
                pub = published_standards(self.df, alt)
                stds = {y: float(pub[y]["RF"]) for y in (self.first, self.second)}
                accts = co.two_year_accounting(stds, den, gen, b0, cap, allow_deficit=True)
                fr = co.accounts_frame(accts, alt)
                fr.insert(0, "bank_scenario", bname)
                frames.append(fr)
                if alt == "set2":
                    base_accounts[bname] = accts
                else:
                    cov = co.coverage_within_cap(accts, base_accounts[bname])
                    for a in accts:
                        fr.loc[fr["year"] == a.year, "coverage_within_cap"] = cov[a.year]
        acc = pd.concat(frames, ignore_index=True)
        self.save("e6_carryover_accounting", acc)
        base = acc[acc["bank_scenario"] == "baseline"]
        for alt in ALTERNATIVES:
            for y, yl in ((self.first, "First"), (self.second, "Second")):
                row = base[(base["alternative"] == alt) & (base["year"] == y)].iloc[0]
                lab = _camel(alt)
                self.values[f"rvo{yl}{lab}"] = round(float(row["rvo_brins"]), 2)
                self.values[f"cap{yl}{lab}"] = round(float(row["cap_brins"]), 2)
                self.values[f"carryoverUsed{yl}{lab}"] = round(float(row["carryover_used_brins"]), 2)
                self.values[f"newRins{yl}{lab}"] = round(float(row["new_rins_required_brins"]), 2)
                self.values[f"bankOut{yl}{lab}"] = round(float(row["bank_out_brins"]), 2)
                self.values[f"deficit{yl}{lab}"] = round(float(row["deficit_brins"]), 2)
        self.values["drawdownTwoYearsEqual"] = round(bank0 - self.values["bankOutSecondEqual"], 2)
        self.values["drawdownTwoYearsAllSecond"] = round(bank0 - self.values["bankOutSecondAll2027"], 2)
        self.values["drawdownTwoYearsSet2"] = round(bank0 - self.values["bankOutSecondSet2"], 2)
        self.values["absorbableDrawdown"] = float(value(self.df, "set2_preamble", "absorbable_drawdown_total"))
        self.values["capBindsAnywhere"] = bool((base["carryover_used_brins"] >= base["cap_brins"] - 1e-9).any())
        # deadlines
        current = deadline(self.df, "compliance_deadline_current", "2026")
        proposal_date = deadline(self.df, "proposal_publication_date")
        drows = []
        for name, d in cfg.timing.finalization_scenarios.items():
            dl = co.compliance_deadline_after_revision(d, current)
            drows.append(
                {
                    "scenario": name,
                    "effective_date": d,
                    "deadline_2026": dl,
                    "days_after_current": (dl - current).days,
                    "days_from_effective_to_deadline": (dl - d).days,
                }
            )
            self.values[f"deadline{_camel(name)}"] = dl.isoformat()
            self.values[f"deadlineDays{_camel(name)}"] = (dl - d).days
        nf = co.deadline_if_not_finalized(proposal_date, current)
        drows.append(
            {
                "scenario": "not_finalized_within_12_months",
                "effective_date": None,
                "deadline_2026": nf,
                "days_after_current": (nf - current).days,
                "days_from_effective_to_deadline": None,
            }
        )
        self.values["deadlineNotFinalized"] = nf.isoformat()
        self.save("e6_compliance_deadlines", pd.DataFrame(drows))

    # ------------------------------------------------------------------ cross-check against a secondary analysis
    def cross_check(self) -> None:
        """Obligation reduction from the additional 2025 exempted fuel if it were not reallocated,
        at the 2026 standards (compared in the SI with the published secondary analysis)."""
        pub = published_standards(self.df, "set2")
        extra_fuel = float(
            value(self.df, "proposal_2025_sre", "exempted_fuel_volume", "2025")
            - value(self.df, "proposal_2025_sre", "projected_exempted_fuel_volume", "2025")
        )
        self.values["crossCheckExtraExemptFuel"] = round(extra_fuel, 2)
        self.values["crossCheckBbdReduction"] = round(extra_fuel * float(pub[self.first]["BBD"]) / 100, 2)
        self.values["crossCheckRfReduction"] = round(extra_fuel * float(pub[self.first]["RF"]) / 100, 2)

    # ------------------------------------------------------------------ E7
    def costs(self) -> None:
        inp = self.inputs()
        prices = rin_prices(self.df, "proposal")
        rounded: dict[str, dict[int, dict[str, float]]] = {}
        for alt in ALTERNATIVES:
            pub = published_standards(self.df, alt)
            rounded[alt] = {y: {c: float(pub[y][c]) for c in CATEGORIES} for y in (self.first, self.second)}
        table = costs.rin_cost_table({}, prices, rounded)
        rel = costs.price_impact_relative(table)
        vi1 = table_vi1(self.df)
        rows = []
        for alt in ALTERNATIVES:
            key = "existing" if alt == "set2" else alt
            for y in (self.first, self.second):
                pubcost = float(
                    vi1[(vi1["alternative"] == key) & (vi1["year"] == y) & (vi1["category"] == "RINCOST")][
                        "value"
                    ].iloc[0]
                )
                parts = costs.implied_categories(rounded[alt][y])
                rows.append(
                    {
                        "alternative": alt,
                        "year": y,
                        "other_advanced_percent": round(parts["OA"], 2),
                        "conventional_percent": round(parts["CONV"], 2),
                        "rin_cost_cents": table[alt][y],
                        "rin_cost_rounded": round(table[alt][y], 1),
                        "published_rin_cost_cents": pubcost,
                        "match": abs(round(table[alt][y], 1) - pubcost) < 1e-9,
                        "relative_to_existing_cents": rel[alt][y],
                    }
                )
        ct = pd.DataFrame(rows)
        self.save("e7_rin_cost_reproduction", ct)
        self.values["nCostChecked"] = int(len(ct))
        self.values["nCostMatched"] = int(ct["match"].sum())
        for alt in ("equal", "all2027"):
            for y, yl in ((self.first, "First"), (self.second, "Second")):
                self.values[f"costRel{yl}{_camel(alt)}"] = round(float(rel[alt][y]), 2)
        del inp

    # ------------------------------------------------------------------ double entry
    def double_entry(self) -> None:
        if ENTRY_B.exists():
            mism = reconcile(load_transcribed(ENTRY_A), load_wide(ENTRY_B))
            self.save("double_entry_mismatches", mism)
            self.values["nDoubleEntryMismatches"] = int(len(mism))

    # ------------------------------------------------------------------ run
    def run(self) -> None:
        self.e1_reproduction()
        self.monte_carlo()
        self.backtest()
        self.carryover()
        self.costs()
        self.cross_check()
        self.double_entry()
        self.values["configName"] = self.cfg.name
        self.values["configHash"] = self.hash
        vpath = self.out / "values.json"
        vpath.write_text(json.dumps(self.values, indent=2, default=str))
        write_sidecar(vpath, config_hash=self.hash, seed=self.cfg.monte_carlo.seed)
        gen = self.out / "generated"
        gen.mkdir(exist_ok=True)
        write_values(self.values, gen / "values.tex")
        write_tables(self.out, gen)
        if self.write_paper:
            PAPER_GENERATED.mkdir(parents=True, exist_ok=True)
            for p in gen.iterdir():
                shutil.copy(p, PAPER_GENERATED / p.name)
            shutil.copy(vpath, PAPER_GENERATED / "values.json")
        summary_dir = ROOT / "results" / "summary"
        summary_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(vpath, summary_dir / f"values_{self.cfg.name}.json")


def _camel(name: str) -> str:
    parts = name.replace("-", "_").split("_")
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run all experiments for a configuration")
    run.add_argument("--config", required=True)
    run.add_argument("--paper", action="store_true", help="also copy generated macros and tables to paper/generated")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    write_paper = args.paper or cfg.name == "paper"
    Pipeline(cfg, write_paper=write_paper).run()
    print(f"results written to {cfg.results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

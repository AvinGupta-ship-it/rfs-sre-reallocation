"""Produce every manuscript figure from saved pipeline results.

Usage: ``python figures/make_figures.py --results results/paper --out paper/figures``

Figures are vector PDFs with embedded fonts and an Okabe-Ito palette (shared
``matplotlibrc``).  Captions in the manuscript state the data basis of each panel.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
matplotlib.rc_file(HERE / "matplotlibrc")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]
ALT_LABEL = {"set2": "Set 2 rule (existing)", "equal": "Equal reallocation", "all2027": "2027 reallocation"}
ALT_COLOR = {"set2": OKABE[7], "equal": OKABE[0], "all2027": OKABE[1]}


def save(fig: plt.Figure, out: Path, name: str, meta: dict[str, object]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.pdf"
    fig.savefig(path, metadata={"Title": name, "Subject": json.dumps(meta)})
    fig.savefig(out / f"{name}.png", dpi=200)
    path.with_suffix(".pdf.json").write_text(json.dumps(meta, indent=2, default=str))
    plt.close(fig)


# ------------------------------------------------------------------ Figure 1: flow of volumes
def fig1_flow(results: Path, out: Path, values: dict[str, object]) -> None:
    ervo = pd.read_csv(results / "e1_ervo_reproduction.csv")
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.set_axis_off()
    ax.set_xlim(0, 10.6)
    ax.set_ylim(0, 6)

    def box(x: float, y: float, w: float, h: float, text: str, color: str, fontsize: float = 7) -> None:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="black", linewidth=0.8, alpha=0.25))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize)

    def arrow(x0: float, y0: float, x1: float, y1: float, text: str = "") -> None:
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="->", mutation_scale=12, linewidth=0.9))
        if text:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.18, text, ha="center", va="bottom", fontsize=7)

    rf = ervo[ervo["category"] == "RF"].set_index("year")
    box(0.2, 4.6, 2.2, 1.0, "2023 exemptions\n7.79 bn gal exempted fuel", OKABE[5])
    box(0.2, 3.2, 2.2, 1.0, "2024 exemptions\n7.78 bn gal", OKABE[5])
    box(0.2, 1.8, 2.2, 1.0, "2025 exemptions\nprojected 7.55 bn gal\nactual 13.38 bn gal", OKABE[5])
    box(3.4, 4.6, 2.2, 1.0, f"ERVO 2023\n{int(rf.loc[2023, 'published_mrins'])} M RINs", OKABE[2])
    box(3.4, 3.2, 2.2, 1.0, f"ERVO 2024\n{int(rf.loc[2024, 'published_mrins'])} M RINs", OKABE[2])
    box(3.4, 1.8, 2.2, 1.0, f"ERVO 2025\nprojected {int(rf.loc[2025, 'published_mrins'])} M\nactual 1,760 M", OKABE[2])
    box(6.6, 4.3, 3.9, 1.0, "SRERV 2026 = 0.7 (ERVO 2023 + ½ ERVO 2024)\n= 990 M RINs (+ w × 770 M)", OKABE[0], 6.3)
    box(
        6.6,
        2.1,
        3.9,
        1.0,
        "SRERV 2027 = 0.7 (½ ERVO 2024 + ERVO 2025)\n= 1,040 M RINs (+ (1 − w) × 770 M)",
        OKABE[1],
        6.3,
    )
    box(
        6.6,
        0.3,
        3.9,
        1.0,
        "Std = 100 (RFV + SRERV) / obligated volume\n2026: 173.02 bn gal; 2027: 171.24 bn gal",
        OKABE[4],
        6.3,
    )
    for y in (5.1, 3.7, 2.3):
        arrow(2.4, y, 3.4, y, "× Std_2025" if y == 2.3 else "× Std")
    arrow(5.6, 5.1, 6.6, 4.9)
    arrow(5.6, 3.7, 6.6, 4.5, "½")
    arrow(5.6, 3.5, 6.6, 2.7, "½")
    arrow(5.6, 2.3, 6.6, 2.5)
    arrow(8.55, 4.3, 8.55, 3.1)
    arrow(8.55, 2.1, 8.55, 1.3)
    ax.text(
        0.2,
        0.15,
        "Data basis: 91 FR 16439–16440 (Tables IV.C-1 to IV.C-3); 91 FR 65703 (Table IV-1);\ndocket EPA-HQ-OAR-2024-0505-0789. Published values.",
        fontsize=6.5,
    )
    save(fig, out, "fig1_flow", {"sources": ["e1_ervo_reproduction.csv"]})


# ------------------------------------------------------------------ Figure 2: reproduction residuals
def fig2_residuals(results: Path, out: Path) -> None:
    rep = pd.read_csv(results / "e1_standards_reproduction.csv")
    rep = rep[rep["alternative"] != "no_srerv"]
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    cats = ["CB", "BBD", "AB", "RF"]
    x = np.arange(len(cats))
    width = 0.13
    i = 0
    for alt in ("set2", "equal", "all2027"):
        for year, hatch in ((2026, ""), (2027, "//")):
            sub = rep[(rep["alternative"] == alt) & (rep["year"] == year)].set_index("category").loc[cats]
            ax.bar(
                x + (i - 2.5) * width,
                sub["residual_points"] * 100,
                width,
                color=ALT_COLOR[alt],
                hatch=hatch,
                edgecolor="black",
                linewidth=0.4,
                label=f"{ALT_LABEL[alt]}, {year}",
            )
            i += 1
    ax.axhline(0.5, color="grey", linestyle=":", linewidth=0.8)
    ax.axhline(-0.5, color="grey", linestyle=":", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Cellulosic", "Biomass-based diesel", "Advanced", "Total renewable"])
    ax.set_ylabel("Exact minus published standard\n(hundredths of a percentage point)")
    ax.set_ylim(-0.6, 0.6)
    ax.legend(ncol=2, fontsize=6.5, loc="upper left")
    ax.set_title("Reconstruction residuals lie within the publication rounding band (±0.5)")
    save(fig, out, "fig2_residuals", {"sources": ["e1_standards_reproduction.csv"]})


# ------------------------------------------------------------------ Figure 3: standards with uncertainty bands
def fig3_bands(results: Path, out: Path) -> None:
    summ = pd.read_csv(results / "e2e4_monte_carlo_summary.csv")
    rep = pd.read_csv(results / "e1_standards_reproduction.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.4), sharey=False, constrained_layout=True)
    for ax, (year, name) in zip(axes, ((2026, "std_first"), (2027, "std_second")), strict=True):
        s = summ[summ["quantity"] == name]
        ax.fill_between(
            s["w"], s["q05"], s["q95"], color=OKABE[5], alpha=0.4, label="5–95% band (revision uncertainty)"
        )
        ax.plot(s["w"], s["mean"], color=OKABE[0], label="Mean")
        for alt, w in (("equal", 0.5), ("all2027", 0.0)):
            pub = float(
                rep[(rep["alternative"] == alt) & (rep["year"] == year) & (rep["category"] == "RF")][
                    "published_percent"
                ].iloc[0]
            )
            ax.plot(
                [w], [pub], marker="o", color=ALT_COLOR[alt], linestyle="none", label=f"{ALT_LABEL[alt]} (published)"
            )
        base = float(
            rep[(rep["alternative"] == "set2") & (rep["year"] == year) & (rep["category"] == "RF")][
                "published_percent"
            ].iloc[0]
        )
        ax.axhline(base, color=OKABE[7], linestyle="--", linewidth=0.8, label="Set 2 rule standard")
        ax.set_xlabel("Share w assigned to 2026")
        ax.set_title(f"{year} total renewable fuel standard")
        ax.set_ylabel("Percent")
    axes[0].legend(fontsize=6.5, loc="lower right")
    save(
        fig,
        out,
        "fig3_bands",
        {
            "sources": ["e2e4_monte_carlo_summary.csv", "e1_standards_reproduction.csv"],
            "basis": "Monte Carlo on empirical revision ratios; fuel-use error does not enter the standard",
        },
    )


# ------------------------------------------------------------------ Figure 4: trade-off curves
def fig4_tradeoff(results: Path, out: Path) -> None:
    t = pd.read_csv(results / "e4_timing_tradeoff.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(t["w"], t["step_first_points"], label="2026 step", color=OKABE[0])
    ax.plot(t["w"], t["step_second_points"], label="2027 step", color=OKABE[1])
    ax.plot(t["w"], t["max_step_points"], label="Larger of the two", color=OKABE[7], linestyle="--")
    ax.set_ylabel("Step vs Set 2 standard (points)")
    ax.legend(fontsize=6.5)
    ax = axes[1]
    ax.plot(t["w"], t["mean_abs_revision_first"], label="2026", color=OKABE[0])
    ax.plot(t["w"], t["mean_abs_revision_second"], label="2027", color=OKABE[1])
    ax.set_ylabel("Expected |revision| of standard (points)")
    ax.legend(fontsize=6.5)
    ax = axes[2]
    cols = [c for c in t.columns if c.startswith("retroactive_share_")]
    for c, col in zip(cols, OKABE, strict=False):
        label = c.replace("retroactive_share_scenario_hypothetical_", "hypothetical effective date: ").replace("_", " ")
        ax.plot(t["w"], t[c], label=label, color=col)
    ax.set_ylabel("Retroactive share of additional obligation")
    ax.legend(fontsize=5.5)
    for ax in axes:
        ax.set_xlabel("Share w assigned to 2026")
        ax.axvline(0.5, color="grey", linewidth=0.6, linestyle=":")
    save(
        fig,
        out,
        "fig4_tradeoff",
        {
            "sources": ["e4_timing_tradeoff.csv"],
            "basis": "deterministic steps; Monte Carlo revisions; hypothetical finalization scenarios",
        },
    )


# ------------------------------------------------------------------ Figure 5: backtest
def fig5_backtest(results: Path, out: Path) -> None:
    proj = pd.read_csv(results / "e5_projection_backtest.csv")
    tb = pd.read_csv(results / "e5_timing_rule_backtest.csv")
    lags = pd.read_csv(results / "e5_decision_lags.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.1), constrained_layout=True)
    ax = axes[0]
    ax.plot(proj["year"], proj["realized_mrins"], marker="o", color=OKABE[7], label="Realized exempted RVO")
    ax.plot(
        proj["year"],
        proj["projection_hindsight_mrins"],
        marker="s",
        color=OKABE[0],
        label="Three-year average of prior years",
    )
    ax.set_ylabel("Million RINs")
    ax.set_xlabel("Compliance year")
    ax.legend(fontsize=6)
    ax = axes[1]
    t0 = tb[tb["lead_months"] == 0]
    yrs = sorted(t0["target_year"].unique())
    x = np.arange(len(yrs))
    for i, (w, col, lab) in enumerate(
        ((0.0, OKABE[1], "w = 0 (2027 approach)"), (0.5, OKABE[0], "w = 0.5 (equal split)"))
    ):
        s = t0[np.isclose(t0["w"], w)].set_index("target_year").loc[yrs]
        share = (s["unknown_fixed_mrins"] / s["reallocated_mrins"].replace(0, np.nan)).fillna(0.0)
        ax.bar(x + (i - 0.5) * 0.4, share, 0.4, color=col, label=lab)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in yrs], fontsize=7)
    ax.set_xlabel("Receiving year")
    ax.set_ylabel("Undecided share of reallocated amount\nwhen the receiving year's standard was set")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=6, loc="lower left")
    ax = axes[2]
    ax.hist(lags["lag_years"], bins=np.arange(0, 4.5, 0.25), color=OKABE[2], edgecolor="black", linewidth=0.4)
    ax.set_xlabel("Decision lag after end of compliance year (years)")
    ax.set_ylabel("Petitions (2021–2025 compliance years)")
    save(
        fig,
        out,
        "fig5_backtest",
        {
            "sources": ["e5_projection_backtest.csv", "e5_timing_rule_backtest.csv", "e5_decision_lags.csv"],
            "basis": "observed EPA record",
        },
    )


# ------------------------------------------------------------------ Figure 6: carryover coverage
def fig6_carryover(results: Path, out: Path) -> None:
    acc = pd.read_csv(results / "e6_carryover_accounting.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), constrained_layout=True)
    base = acc[acc["bank_scenario"] == "baseline"]
    ax = axes[0]
    x = np.arange(2)
    width = 0.25
    for i, alt in enumerate(("set2", "equal", "all2027")):
        s = base[base["alternative"] == alt].sort_values("year")
        ax.bar(x + (i - 1) * width, s["new_rins_required_brins"], width, color=ALT_COLOR[alt], label=ALT_LABEL[alt])
        ax.plot(x + (i - 1) * width, s["cap_brins"], marker="_", markersize=14, color="black", linestyle="none")
    ax.set_xticks(x)
    ax.set_xticklabels(["2026", "2027"])
    ax.set_ylabel("New RINs required (billion)")
    ax.set_title("Ticks mark the 20% carryover cap", fontsize=8)
    ax.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=1)
    ax = axes[1]
    for alt in ("set2", "equal", "all2027"):
        for scen, ls in (
            ("baseline", "-"),
            ("scenario_hypothetical_low_bank", ":"),
            ("scenario_hypothetical_high_bank", "--"),
        ):
            s = acc[(acc["alternative"] == alt) & (acc["bank_scenario"] == scen)].sort_values("year")
            if s.empty:
                continue
            yrs = [2025, *s["year"].tolist()]
            banks = [float(s["bank_in_brins"].iloc[0]), *s["bank_out_brins"].tolist()]
            ax.plot(
                yrs,
                banks,
                marker="o",
                markersize=3,
                color=ALT_COLOR[alt],
                linestyle=ls,
                label=f"{ALT_LABEL[alt]}, {scen.replace('scenario_hypothetical_', 'hypothetical ').replace('_', ' ')}",
            )
    ax.set_ylabel("Carryover RINs at year end (billion)")
    ax.set_xticks([2025, 2026, 2027])
    ax.legend(fontsize=5, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)
    save(
        fig,
        out,
        "fig6_carryover",
        {
            "sources": ["e6_carryover_accounting.csv"],
            "basis": "accounting under stated assumptions; hypothetical bank scenarios labelled",
        },
    )


# ------------------------------------------------------------------ SI figures
def si_convergence(results: Path, out: Path) -> None:
    conv = pd.read_csv(results / "mc_convergence.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.0))
    for ax, qty in zip(axes, ("std_second", "realized_minus_intended_second"), strict=True):
        for w, col in ((0.0, OKABE[1]), (0.5, OKABE[0])):
            s = conv[(conv["quantity"] == qty) & (conv["w"] == w)]
            ax.errorbar(
                s["n"], s["mean"], yerr=1.96 * s["mcse_mean"], marker="o", markersize=3, color=col, label=f"w = {w}"
            )
        ax.set_xscale("log")
        ax.set_xlabel("Monte Carlo draws")
        ax.set_ylabel(f"Mean of {qty.replace('_', ' ')}")
        ax.legend(fontsize=6.5)
    save(fig, out, "si_convergence", {"sources": ["mc_convergence.csv"]})


def si_sobol(results: Path, out: Path) -> None:
    sob = pd.read_csv(results / "sobol_indices.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.0), sharey=True)
    for ax, w in zip(axes, (0.5, 0.0), strict=True):
        s = sob[(sob["w"] == w) & (sob["output"].isin(["std_second", "realized_rins_second"]))]
        outs = ["std_second", "realized_rins_second"]
        facs = ["revision_ratio", "fuel_error_first", "fuel_error_second"]
        x = np.arange(len(outs))
        for i, f in enumerate(facs):
            vals = [float(s[(s["output"] == o) & (s["factor"] == f)]["ST"].iloc[0]) for o in outs]
            errs = [float(s[(s["output"] == o) & (s["factor"] == f)]["ST_conf"].iloc[0]) for o in outs]
            ax.bar(x + (i - 1) * 0.25, vals, 0.25, yerr=errs, color=OKABE[i], label=f.replace("_", " "), capsize=2)
        ax.set_xticks(x)
        ax.set_xticklabels(["2027 standard", "2027 realized RINs"])
        ax.set_title(f"w = {w}")
        ax.set_ylim(0, 1.1)
    axes[0].set_ylabel("Total-order Sobol index")
    axes[0].legend(fontsize=6.5)
    save(fig, out, "si_sobol", {"sources": ["sobol_indices.csv"]})


def si_distributions(results: Path, out: Path) -> None:
    pairs = pd.read_csv(results / "e2_revision_pairs.csv")
    fuel = pd.read_csv(results / "e3_fuel_projection_errors.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.0))
    ax = axes[0]
    ax.bar(pairs["year"].astype(str), pairs["ratio"], color=OKABE[0])
    ax.axhline(1.0, color="black", linewidth=0.8)
    ax.set_ylabel("Reported / petition-based exempted RVO")
    ax.set_ylim(0.7, 1.1)
    ax = axes[1]
    nr = fuel[~fuel["retroactive"]]
    rt = fuel[fuel["retroactive"]]
    ax.scatter(nr["lead_years"], 100 * (nr["ratio"] - 1), color=OKABE[0], label="used")
    ax.scatter(
        rt["lead_years"],
        100 * (rt["ratio"] - 1),
        color=OKABE[1],
        marker="x",
        label="excluded",
    )
    for _, r in fuel.iterrows():
        ax.annotate(
            str(int(r["year"])),
            (r["lead_years"], 100 * (r["ratio"] - 1)),
            fontsize=6,
            xytext=(2, 2),
            textcoords="offset points",
        )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Lead time from final rule to mid-year (years)")
    ax.set_ylabel("Reported minus projected volume (%)")
    ax.legend(fontsize=6.5, loc="lower right")
    save(fig, out, "si_distributions", {"sources": ["e2_revision_pairs.csv", "e3_fuel_projection_errors.csv"]})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    results, out = Path(args.results), Path(args.out)
    values = json.loads((results / "values.json").read_text())
    fig1_flow(results, out, values)
    fig2_residuals(results, out)
    fig3_bands(results, out)
    fig4_tradeoff(results, out)
    fig5_backtest(results, out)
    fig6_carryover(results, out)
    si_convergence(results, out)
    si_sobol(results, out)
    si_distributions(results, out)
    print(f"figures written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

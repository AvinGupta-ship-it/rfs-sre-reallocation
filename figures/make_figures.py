"""Produce every manuscript figure from saved pipeline results.

Usage: ``python figures/make_figures.py --results results/paper --out paper/figures``

Figures are vector PDFs with embedded fonts, serif text matching the manuscript body and an
Okabe-Ito palette (shared ``matplotlibrc``).  Panels carry labels (a), (b), (c); captions in
the manuscript state the data basis of each panel.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
matplotlib.rc_file(HERE / "matplotlibrc")


def _register_latin_modern() -> None:
    """Use the Latin Modern fonts of a local TeX installation when present (fallback: rc list)."""
    if shutil.which("kpsewhich") is None:
        return
    for name in ("lmroman10-regular.otf", "lmroman10-bold.otf", "lmroman10-italic.otf", "lmroman10-bolditalic.otf"):
        try:
            path = subprocess.run(["kpsewhich", name], capture_output=True, text=True, timeout=30).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return
        if path:
            font_manager.fontManager.addfont(path)


_register_latin_modern()
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]
ALT_LABEL = {"set2": "Set 2 rule (existing)", "equal": "Equal reallocation", "all2027": "2027 reallocation"}
ALT_COLOR = {"set2": OKABE[7], "equal": OKABE[0], "all2027": OKABE[1]}
YEAR_COLOR = {2026: OKABE[0], 2027: OKABE[1]}
SCENARIO_STYLE = {"baseline": "-", "scenario_hypothetical_low_bank": ":", "scenario_hypothetical_high_bank": "--"}
SCENARIO_LABEL = {
    "baseline": "baseline bank",
    "scenario_hypothetical_low_bank": "hypothetical low bank",
    "scenario_hypothetical_high_bank": "hypothetical high bank",
}
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def long_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


def label_panels(axes: list[plt.Axes], x: float = -0.18, y: float = 1.02) -> None:
    for ax, letter in zip(axes, "abcdef", strict=False):
        ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="left")


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
    rf = ervo[ervo["category"] == "RF"].set_index("year")
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    ax.set_axis_off()
    ax.grid(False)
    ax.set_xlim(0, 12.6)
    ax.set_ylim(0, 6.4)

    def box(x: float, y: float, w: float, h: float, text: str, color: str) -> None:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="black", linewidth=0.8, alpha=0.25))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8)

    def arrow(x0: float, y0: float, x1: float, y1: float, text: str = "", frac: float = 0.5, dy: float = 0.12) -> None:
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="->", mutation_scale=12, linewidth=0.9))
        if text:
            ax.text(x0 + frac * (x1 - x0), y0 + frac * (y1 - y0) + dy, text, ha="center", va="bottom", fontsize=8)

    lh, lw = 1.1, 3.0  # left column
    box(0.2, 4.9, lw, lh, "2023 exemptions\n7.79 billion gal", OKABE[5])
    box(0.2, 3.4, lw, lh, "2024 exemptions\n7.78 billion gal", OKABE[5])
    box(0.2, 1.9, lw, lh, "2025 exemptions\nprojected 7.55 billion gal\nactual 13.38 billion gal", OKABE[5])
    mw = 2.4  # middle column
    box(4.4, 4.9, mw, lh, f"ERVO 2023\n{int(rf.loc[2023, 'published_mrins'])} M RINs", OKABE[2])
    box(4.4, 3.4, mw, lh, f"ERVO 2024\n{int(rf.loc[2024, 'published_mrins'])} M RINs", OKABE[2])
    box(4.4, 1.9, mw, lh, f"ERVO 2025\nprojected {int(rf.loc[2025, 'published_mrins'])} M\nactual 1,760 M", OKABE[2])
    rx, rw = 7.9, 4.3  # right column
    box(
        rx,
        4.5,
        rw,
        1.5,
        "SRERV$_{2026}$ =\n0.7 (ERVO$_{2023}$ + ½ ERVO$_{2024}$)\n= 990 M RINs, plus $w$ × 770 M",
        OKABE[0],
    )
    box(
        rx,
        2.4,
        rw,
        1.5,
        "SRERV$_{2027}$ =\n0.7 (½ ERVO$_{2024}$ + ERVO$_{2025}$)\n= 1,040 M RINs, plus (1 − $w$) × 770 M",
        OKABE[1],
    )
    box(
        rx,
        0.2,
        rw + 0.4,
        1.5,
        "Std = 100 (RFV + SRERV) / $V$\n$V_{2026}$ = 173.02 billion gal\n$V_{2027}$ = 171.24 billion gal",
        OKABE[4],
    )
    for y, year in ((5.45, 2023), (3.95, 2024), (2.45, 2025)):
        arrow(3.2, y, 4.4, y, f"× Std$_{{{year}}}$" if year == 2025 else "× Std")
    arrow(6.8, 5.45, rx, 5.4)
    arrow(6.8, 4.05, rx, 4.9, "½", 0.45, 0.05)
    arrow(6.8, 3.85, rx, 3.1, "½", 0.45, -0.3)
    arrow(6.8, 2.45, rx, 2.9)
    arrow(rx + rw / 2, 2.4, rx + rw / 2, 1.7)
    ax.add_patch(
        FancyArrowPatch(
            (rx + rw, 5.25),
            (rx + rw + 0.2, 1.7),
            arrowstyle="->",
            mutation_scale=12,
            linewidth=0.9,
            connectionstyle="angle,angleA=0,angleB=90,rad=0",
        )
    )
    save(fig, out, "fig1_flow", {"sources": ["e1_ervo_reproduction.csv"]})


# ------------------------------------------------------------------ Figure 2: reproduction residuals
def fig2_residuals(results: Path, out: Path) -> None:
    rep = pd.read_csv(results / "e1_standards_reproduction.csv")
    rep = rep[rep["alternative"] != "no_srerv"]
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
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
                edgecolor="white" if (alt == "set2" and hatch) else "black",
                linewidth=0.4,
                label=f"{ALT_LABEL[alt]}, {year}",
            )
            i += 1
    ax.axhline(0.5, color="gray", linestyle=":", linewidth=0.8)
    ax.axhline(-0.5, color="gray", linestyle=":", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Cellulosic", "Biomass-based diesel", "Advanced", "Total renewable"])
    ax.set_ylabel("Exact minus published standard\n(hundredths of a percentage point)")
    ax.set_ylim(-0.6, 0.6)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.14), frameon=False)
    save(fig, out, "fig2_residuals", {"sources": ["e1_standards_reproduction.csv"]})


# ------------------------------------------------------------------ Figure 3: standards with uncertainty bands
def fig3_bands(results: Path, out: Path) -> None:
    summ = pd.read_csv(results / "e2e4_monte_carlo_summary.csv")
    rep = pd.read_csv(results / "e1_standards_reproduction.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.6), sharey=False, constrained_layout=True)
    for ax, (year, name) in zip(axes, ((2026, "std_first"), (2027, "std_second")), strict=True):
        s = summ[summ["quantity"] == name]
        ax.fill_between(
            s["w"], s["q05"], s["q95"], color=OKABE[5], alpha=0.4, label="5–95% band (revision uncertainty)"
        )
        ax.plot(s["w"], s["mean"], color=OKABE[7], label="Mean under the revision distribution")
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
        ax.set_xlabel("Share $w$ assigned to 2026")
        ax.set_ylabel(f"{year} total renewable fuel standard (%)")
    label_panels(list(axes))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
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
    deadlines = pd.read_csv(results / "e6_compliance_deadlines.csv").dropna(subset=["effective_date"])
    dates = dict(zip(deadlines["scenario"], deadlines["effective_date"], strict=True))
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.6), constrained_layout=True)
    ax = axes[0]
    ax.plot(t["w"], t["max_step_points"], color="#BBBBBB", linewidth=5, alpha=0.8, label="Larger of the two")
    ax.plot(t["w"], t["step_first_points"], label="2026 step", color=YEAR_COLOR[2026])
    ax.plot(t["w"], t["step_second_points"], label="2027 step", color=YEAR_COLOR[2027])
    ax.set_ylabel("Step vs Set 2 standard (points)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False)
    ax = axes[1]
    ax.plot(t["w"], t["mean_abs_revision_first"], label="2026 standard", color=YEAR_COLOR[2026])
    ax.plot(t["w"], t["mean_abs_revision_second"], label="2027 standard", color=YEAR_COLOR[2027])
    ax.set_ylabel("Expected absolute revision (points)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False)
    ax = axes[2]
    cols = [c for c in t.columns if c.startswith("retroactive_share_")]
    for c, col in zip(cols, (OKABE[0], OKABE[1], OKABE[2]), strict=False):
        scen = c.replace("retroactive_share_", "")
        label = f"effective {long_date(str(dates[scen]))}" if scen in dates else scen
        ax.plot(t["w"], t[c], label=label, color=col)
    ax.set_ylabel("Share of additional obligation on fuel\nalready produced at the effective date")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False)
    for ax in axes:
        ax.set_xlabel("Share $w$ assigned to 2026")
        ax.axvline(0.5, color="gray", linewidth=0.6, linestyle=":")
    label_panels(list(axes), x=-0.3, y=1.04)
    save(
        fig,
        out,
        "fig4_tradeoff",
        {
            "sources": ["e4_timing_tradeoff.csv", "e6_compliance_deadlines.csv"],
            "basis": "deterministic steps; Monte Carlo revisions; hypothetical finalization scenarios",
        },
    )


# ------------------------------------------------------------------ Figure 5: backtest
def fig5_backtest(results: Path, out: Path) -> None:
    proj = pd.read_csv(results / "e5_projection_backtest.csv")
    tb = pd.read_csv(results / "e5_timing_rule_backtest.csv")
    lags = pd.read_csv(results / "e5_decision_lags.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 3.5), constrained_layout=True)
    ax = axes[0]
    ax.plot(proj["year"], proj["realized_mrins"], marker="o", color=OKABE[7], label="Realized exempted obligation")
    ax.plot(
        proj["year"],
        proj["projection_hindsight_mrins"],
        marker="s",
        color=OKABE[0],
        label="Three-year average of prior years",
    )
    ax.set_ylabel("Million RINs")
    ax.set_xlabel("Compliance year")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False)
    ax = axes[1]
    t0 = tb[tb["lead_months"] == 0]
    yrs = sorted(t0["target_year"].unique())
    x = np.arange(len(yrs))
    for i, (w, col, lab) in enumerate(
        ((0.0, ALT_COLOR["all2027"], "$w$ = 0 (2027 approach)"), (0.5, ALT_COLOR["equal"], "$w$ = 1/2 (equal split)"))
    ):
        s = t0[np.isclose(t0["w"], w)].set_index("target_year").loc[yrs]
        share = (s["unknown_fixed_mrins"] / s["reallocated_mrins"].replace(0, np.nan)).fillna(0.0)
        ax.bar(x + (i - 0.5) * 0.4, share, 0.4, color=col, label=lab)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in yrs], rotation=45, ha="right")
    ax.set_xlabel("Receiving year")
    ax.set_ylabel("Undecided share of reallocated\namount when standard was set")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=1, frameon=False)
    ax = axes[2]
    ax.hist(lags["lag_years"], bins=np.arange(0.5, 4.51, 0.5), color=OKABE[2], edgecolor="black", linewidth=0.4)
    ax.set_xlabel("Decision lag after end of\ncompliance year (years)")
    ax.set_ylabel("Petitions (2021–2025 compliance years)")
    label_panels(list(axes), x=-0.3, y=1.04)
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
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.8), constrained_layout=True)
    base = acc[acc["bank_scenario"] == "baseline"]
    ax = axes[0]
    x = np.arange(2)
    width = 0.25
    for i, alt in enumerate(("set2", "equal", "all2027")):
        s = base[base["alternative"] == alt].sort_values("year")
        xs = x + (i - 1) * width
        ax.bar(xs, s["new_rins_required_brins"], width, color=ALT_COLOR[alt], label=ALT_LABEL[alt])
        ax.hlines(s["cap_brins"], xs - width / 2, xs + width / 2, color="white", linewidth=3, zorder=3)
        ax.hlines(s["cap_brins"], xs - width / 2, xs + width / 2, color=OKABE[2], linewidth=1.6, zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(["2026", "2027"])
    ax.set_ylabel("New RINs required (billion)")
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([0], [0], color=OKABE[2], linewidth=1.6, label="20% cap on prior-year RINs"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1, frameon=False)
    ax = axes[1]
    for alt in ("set2", "equal", "all2027"):
        for scen, ls in SCENARIO_STYLE.items():
            s = acc[(acc["alternative"] == alt) & (acc["bank_scenario"] == scen)].sort_values("year")
            if s.empty:
                continue
            yrs = [2025, *s["year"].tolist()]
            banks = [float(s["bank_in_brins"].iloc[0]), *s["bank_out_brins"].tolist()]
            ax.plot(yrs, banks, marker="o", markersize=3, color=ALT_COLOR[alt], linestyle=ls)
    ax.set_ylabel("Carryover RINs at year end (billion)")
    ax.set_xticks([2025, 2026, 2027])
    alt_handles = [Line2D([0], [0], color=ALT_COLOR[a], linewidth=1.4, label=ALT_LABEL[a]) for a in ALT_COLOR]
    scen_handles = [
        Line2D([0], [0], color="black", linestyle=ls, linewidth=1.2, label=SCENARIO_LABEL[s])
        for s, ls in SCENARIO_STYLE.items()
    ]
    leg1 = ax.legend(handles=alt_handles, loc="upper center", bbox_to_anchor=(0.25, -0.12), ncol=1, frameon=False)
    ax.add_artist(leg1)
    ax.legend(handles=scen_handles, loc="upper center", bbox_to_anchor=(0.78, -0.12), ncol=1, frameon=False)
    label_panels(list(axes))
    save(
        fig,
        out,
        "fig6_carryover",
        {
            "sources": ["e6_carryover_accounting.csv"],
            "basis": "accounting under stated assumptions; hypothetical bank scenarios labeled",
        },
    )


# ------------------------------------------------------------------ SI figures
def si_convergence(results: Path, out: Path) -> None:
    conv = pd.read_csv(results / "mc_convergence.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.2), constrained_layout=True)
    names = {
        "std_second": "2027 standard (%)",
        "realized_minus_intended_second": "Realized minus intended 2027 RINs (bn)",
    }
    for ax, qty in zip(axes, ("std_second", "realized_minus_intended_second"), strict=True):
        for w, col, lab in ((0.0, ALT_COLOR["all2027"], "$w$ = 0"), (0.5, ALT_COLOR["equal"], "$w$ = 1/2")):
            s = conv[(conv["quantity"] == qty) & (conv["w"] == w)]
            ax.errorbar(s["n"], s["mean"], yerr=1.96 * s["mcse_mean"], marker="o", markersize=3, color=col, label=lab)
        ax.set_xscale("log")
        ax.set_xlabel("Monte Carlo draws")
        ax.set_ylabel(f"Running mean: {names[qty]}")
        ax.legend(frameon=False)
    label_panels(list(axes))
    save(fig, out, "si_convergence", {"sources": ["mc_convergence.csv"]})


def si_sobol(results: Path, out: Path) -> None:
    sob = pd.read_csv(results / "sobol_indices.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.2), sharey=True, constrained_layout=True)
    facs = ["revision_ratio", "fuel_error_first", "fuel_error_second"]
    fac_label = {
        "revision_ratio": "revision ratio",
        "fuel_error_first": "2026 fuel error",
        "fuel_error_second": "2027 fuel error",
    }
    for ax, w in zip(axes, (0.5, 0.0), strict=True):
        s = sob[(sob["w"] == w) & (sob["output"].isin(["std_second", "realized_rins_second"]))]
        outs = ["std_second", "realized_rins_second"]
        x = np.arange(len(outs))
        for i, f in enumerate(facs):
            vals = [float(s[(s["output"] == o) & (s["factor"] == f)]["ST"].iloc[0]) for o in outs]
            errs = [float(s[(s["output"] == o) & (s["factor"] == f)]["ST_conf"].iloc[0]) for o in outs]
            ax.bar(x + (i - 1) * 0.25, vals, 0.25, yerr=errs, color=OKABE[i], label=fac_label[f], capsize=2)
        ax.set_xticks(x)
        ax.set_xticklabels(["2027 standard", "2027 realized RINs"])
        ax.set_ylim(0, 1.1)
    axes[0].set_ylabel("Total-order Sobol index")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=3, frameon=False)
    label_panels(list(axes))
    save(fig, out, "si_sobol", {"sources": ["sobol_indices.csv"], "panels": {"a": "w = 1/2", "b": "w = 0"}})


def si_distributions(results: Path, out: Path) -> None:
    pairs = pd.read_csv(results / "e2_revision_pairs.csv")
    fuel = pd.read_csv(results / "e3_fuel_projection_errors.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.2), constrained_layout=True)
    ax = axes[0]
    ax.bar(pairs["year"].astype(str), pairs["ratio"], color=OKABE[0])
    ax.axhline(1.0, color="black", linewidth=0.8)
    ax.set_ylabel("Reported / petition-based exempted obligation")
    ax.set_xlabel("Compliance year")
    ax.set_ylim(0.7, 1.1)
    ax = axes[1]
    nr = fuel[~fuel["retroactive"]]
    rt = fuel[fuel["retroactive"]]
    ax.scatter(nr["lead_years"], 100 * (nr["ratio"] - 1), color=OKABE[0], label="used")
    ax.scatter(rt["lead_years"], 100 * (rt["ratio"] - 1), color=OKABE[1], marker="x", label="excluded")
    for _, r in fuel.iterrows():
        ax.annotate(
            str(int(r["year"])),
            (r["lead_years"], 100 * (r["ratio"] - 1)),
            fontsize=8,
            xytext=(3, 2),
            textcoords="offset points",
        )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Lead time from final rule to mid-year (years)")
    ax.set_ylabel("Reported minus projected volume (%)")
    ax.legend(loc="lower right", frameon=False)
    label_panels(list(axes))
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

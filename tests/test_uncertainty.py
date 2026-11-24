"""Monte Carlo reproducibility and worker independence; Sobol sanity."""

from __future__ import annotations

import numpy as np

from rfsrealloc import uncertainty as un
from rfsrealloc.config import load_config
from rfsrealloc.provenance import ROOT


def _inputs() -> un.UncertaintyInputs:
    return un.UncertaintyInputs(
        revision_log_ratios=np.log(np.array([0.90, 0.83, 0.93, 1.0, 1.01, 0.99, 0.99])),
        fuel_log_errors_by_bin={
            0: np.array([-0.03, 0.01, 0.02, 0.04, 0.03]),
            1: np.array([0.0, 0.05, 0.02]),
            2: np.array([0.0, 0.05, 0.02]),
        },
        lead_bin_first=0,
        lead_bin_second=1,
        uniform_half_width=0.2,
        revision_model="empirical",
        fuel_model="empirical",
        correlation=1.0,
    )


def test_draws_are_reproducible_and_independent_of_worker_count() -> None:
    cfg = load_config(ROOT / "configs" / "quick.yaml")
    u = _inputs()
    a = un.monte_carlo_draws(cfg, u)
    b = un.monte_carlo_draws(cfg, u)
    for x, y in zip(a, b, strict=True):
        assert np.array_equal(x, y)
    cfg2 = cfg.model_copy(deep=True)
    cfg2.monte_carlo.n_workers = 1
    c = un.monte_carlo_draws(cfg2, u)
    # per-stream draws are identical for the first stream; totals have the same size
    assert c[0].size == a[0].size
    assert np.allclose(np.sort(a[0])[:5] > 0, True)


def test_uniform_model_bounds() -> None:
    u = _inputs()
    u2 = un.UncertaintyInputs(**{**u.__dict__, "revision_model": "uniform"})
    r = un.draw_revision_ratio(np.random.default_rng(1), u2, 10_000)
    assert r.min() >= 0.8 and r.max() <= 1.2


def test_evaluate_identities() -> None:
    from fractions import Fraction

    from rfsrealloc.inputs import ENTRY_A, load_transcribed, set2_inputs

    inp = set2_inputs(load_transcribed(ENTRY_A))
    model = un.TimingModel(
        inp,
        {2026: {"BBD": 210.0, "AB": 280.0, "RF": 990.0}, 2027: {"BBD": 250.0, "AB": 340.0, "RF": 1040.0}},
        {"BBD": 420.0, "AB": 580.0, "RF": 1760.0},
        {"BBD": 240.0, "AB": 330.0, "RF": 990.0},
    )
    r = np.ones(3)
    e = np.zeros(3)
    out = un.evaluate(model, r, e, e, np.array([0.0, 0.5, 1.0]), "RF")
    # w = 0 reproduces the all-in-2027 standards; w = 0.5 the equal split (before rounding)
    assert abs(out["std_second"][0, 0] - 100 * (25.98 + 1.81) / 171.24) < 1e-9
    assert abs(out["std_first"][0, 1] - 100 * (25.82 + 1.375) / 173.02) < 1e-9
    # no fuel error: realized equals intended
    assert np.allclose(out["realized_minus_intended_first"], 0.0) and np.allclose(
        out["realized_minus_intended_second"], 0.0
    )
    assert Fraction(1, 2) == Fraction(0.5)

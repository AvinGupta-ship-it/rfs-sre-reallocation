from __future__ import annotations

import pytest
from pydantic import ValidationError

from rfsrealloc.config import PipelineConfig, config_hash, load_config
from rfsrealloc.provenance import ROOT


def test_all_configs_validate() -> None:
    hashes = set()
    for p in (ROOT / "configs").glob("*.yaml"):
        cfg = load_config(p)
        assert isinstance(cfg, PipelineConfig)
        hashes.add(config_hash(cfg))
    assert len(hashes) == len(list((ROOT / "configs").glob("*.yaml")))


def test_hypothetical_scenarios_are_labelled() -> None:
    cfg = load_config(ROOT / "configs" / "paper.yaml")
    for name in cfg.timing.finalization_scenarios:
        assert name.startswith("scenario_hypothetical_")
    for name in cfg.carryover.hypothetical_bank_scenarios:
        assert name.startswith("scenario_hypothetical_")


def test_invalid_config_rejected() -> None:
    cfg = load_config(ROOT / "configs" / "quick.yaml").model_dump(mode="json")
    cfg["monte_carlo"]["n_draws"] = 10
    with pytest.raises(ValidationError):
        PipelineConfig.model_validate(cfg)

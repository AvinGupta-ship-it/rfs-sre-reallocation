"""Experiment configuration: YAML files under ``configs/`` validated by pydantic."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class MonteCarloConfig(BaseModel):
    n_draws: int = Field(ge=100, description="number of Monte Carlo replicates")
    seed: int = Field(ge=0, description="root seed for numpy.random.SeedSequence")
    n_workers: int = Field(default=1, ge=1, description="SeedSequence.spawn children, independent of worker count")
    convergence_checkpoints: list[int] = Field(default_factory=lambda: [100, 1_000, 10_000, 100_000])
    headline_mcse_tolerance: float = Field(
        default=0.02, gt=0, description="MC standard error tolerance as a fraction of the headline value"
    )


class SobolConfig(BaseModel):
    n_base: int = Field(ge=64, description="Saltelli base sample size N; total evaluations N(k+2)")
    bootstrap: int = Field(default=200, ge=10)
    seed_offset: int = Field(default=1, ge=0)


class TimingConfig(BaseModel):
    w_grid_points: int = Field(default=101, ge=3)
    finalization_scenarios: dict[str, dt.date] = Field(
        description="hypothetical final-rule effective dates used for the retroactivity measure"
    )
    first_year: int = 2026
    second_year: int = 2027


class RevisionConfig(BaseModel):
    model: Literal["empirical", "uniform"] = "empirical"
    uniform_half_width: float = Field(
        default=0.20, gt=0, description="assumed +/- range if no empirical pairs are available"
    )
    include_later_decisions: bool = Field(
        default=True, description="include revisions from decisions issued after a rule in the empirical set"
    )


class FuelErrorConfig(BaseModel):
    model: Literal["empirical", "lognormal"] = "empirical"
    lead_time_bins_years: list[float] = Field(default_factory=lambda: [0.0, 1.0, 2.5])
    correlation_between_years: float = Field(
        default=1.0, ge=-1.0, le=1.0, description="rank correlation of the 2026 and 2027 draws"
    )
    include_retroactive_rules: bool = False


class UncertaintyConfig(BaseModel):
    revision: RevisionConfig = Field(default_factory=RevisionConfig)
    fuel_error: FuelErrorConfig = Field(default_factory=FuelErrorConfig)
    decision_lag_years: list[int] = Field(default_factory=lambda: [2021, 2022, 2023, 2024, 2025])


class CarryoverConfig(BaseModel):
    bank_basis: Literal["ria_effective_2024", "ria_absolute_2024"] = "ria_effective_2024"
    additional_2025_rins_to_bank: bool = Field(
        default=True, description="add the 0.77 billion RINs freed by the 2025 SREs to the bank available for 2026"
    )
    hypothetical_bank_scenarios: dict[str, float] = Field(
        default_factory=dict, description="hypothetical bank sizes in billion RINs"
    )


class BacktestConfig(BaseModel):
    projection_first_year: int = Field(default=2016, description="first year evaluated in the projection backtest")
    first_target_year: int = Field(
        default=2021,
        description="first receiving year in the timing-rule backtest; source years must have dated decision records",
    )
    last_target_year: int = 2027
    projection_window_years: int = 3
    lead_time_policies_months: list[int] = Field(default_factory=lambda: [1, 7, 13])


class PipelineConfig(BaseModel):
    name: str
    description: str = ""
    output_dir: Path = Path("results")
    monte_carlo: MonteCarloConfig
    sobol: SobolConfig
    timing: TimingConfig
    uncertainty: UncertaintyConfig = Field(default_factory=UncertaintyConfig)
    carryover: CarryoverConfig = Field(default_factory=CarryoverConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)

    @model_validator(mode="after")
    def _check_checkpoints(self) -> PipelineConfig:
        cps = [c for c in self.monte_carlo.convergence_checkpoints if c <= self.monte_carlo.n_draws]
        if not cps:
            raise ValueError("no convergence checkpoint is <= n_draws")
        self.monte_carlo.convergence_checkpoints = cps
        return self

    @property
    def results_dir(self) -> Path:
        return self.output_dir / self.name


def load_config(path: str | Path) -> PipelineConfig:
    raw = yaml.safe_load(Path(path).read_text())
    return PipelineConfig.model_validate(raw)


def config_hash(cfg: PipelineConfig) -> str:
    payload = json.dumps(cfg.model_dump(mode="json"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()[:16]

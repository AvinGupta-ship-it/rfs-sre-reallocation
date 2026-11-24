"""Run every configuration under ``configs/`` (thin wrapper around the pipeline)."""

from __future__ import annotations

import sys
from pathlib import Path

from rfsrealloc.pipeline import main

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    names = sys.argv[1:] or ["sensitivity_uniform_revision", "sensitivity_independent_fuel_errors", "paper"]
    for name in names:
        main(["run", "--config", str(ROOT / "configs" / f"{name}.yaml")])

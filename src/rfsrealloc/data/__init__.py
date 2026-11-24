"""Idempotent transformations from raw downloads to analysis-ready tables."""

from __future__ import annotations

from pathlib import Path

from rfsrealloc.provenance import RAW, ROOT

PROCESSED: Path = ROOT / "data" / "processed"

__all__ = ["PROCESSED", "RAW"]

"""Output provenance: JSON sidecars with git commit, configuration hash, input checksums,
package versions and seed."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata as md
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TRANSCRIBED = ROOT / "data" / "transcribed"
RAW = ROOT / "data" / "raw"

PACKAGES = ("numpy", "pandas", "scipy", "matplotlib", "pydantic", "SALib", "pint", "pyyaml")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        commit = out.stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        return commit + ("-dirty" if dirty else "")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in PACKAGES:
        try:
            versions[name] = md.version(name)
        except md.PackageNotFoundError:
            versions[name] = "not installed"
    return versions


def input_checksums(extra: list[Path] | None = None) -> dict[str, str]:
    files = sorted(TRANSCRIBED.glob("*.csv")) + list(extra or [])
    return {str(p.relative_to(ROOT)): sha256_file(p) for p in files if p.exists()}


def write_sidecar(
    output: Path,
    *,
    config_hash: str,
    seed: int | None,
    extra_inputs: list[Path] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Path:
    sidecar = output.with_suffix(output.suffix + ".json")
    payload: dict[str, Any] = {
        "output": output.name,
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "config_hash": config_hash,
        "seed": seed,
        "input_checksums": input_checksums(extra_inputs),
        "package_versions": package_versions(),
    }
    if metadata:
        payload["metadata"] = metadata
    sidecar.write_text(json.dumps(payload, indent=2, default=str))
    return sidecar

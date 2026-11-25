# Reallocating exempted obligations under the Renewable Fuel Standard

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24514815.svg)](https://doi.org/10.5281/zenodo.24514815)

Exact reconstruction of the 2026–2027 Renewable Fuel Standard (RFS) percentage standards,
propagation of small-refinery-exemption (SRE) uncertainty, and evaluation of the timing
rules for reallocating the additional 2025 exempted volume co-proposed by EPA in
docket EPA-HQ-OAR-2024-0505 (91 FR 65699, October 16, 2026; document
EPA-HQ-OAR-2024-0505-0951; comments due December 4, 2026).

The repository contains the Python package `rfsrealloc`, the transcribed and raw input
data with provenance, the experiments (E1–E7 of the project specification), the
manuscript and supporting information (`paper/`), and the formal regulatory comment
with its technical attachment (`comment/`).

## Installation

```bash
uv sync --extra dev
```

## Reproduction

```bash
make quick     # reduced configuration (seconds)
make all       # data checks, full experiments, figures, manuscript, SI, comment, attachment
pytest
```

See `docs/reproduction.md` for step-by-step instructions and expected runtimes,
`docs/model.md` for the mathematical specification and `docs/data.md` for data sources.

## Layout

```
configs/      experiment configurations (YAML, schema-validated)
data/         MANIFEST.yaml, raw downloads, transcribed values (double-entered), processed tables
src/rfsrealloc/  inputs, standards, reallocation, uncertainty, backtest, carryover, costs, pipeline
scripts/      fetch_data.py, check_refs.py, run_experiments.py
figures/      one script producing every manuscript figure from saved results
tests/        unit, property-based, validation and regression tests
results/      generated outputs (git-ignored except small summaries)
docs/         model, data and reproduction documentation
paper/        LaTeX manuscript, SI, bibliography, generated values and tables
comment/      regulatory comment source, technical attachment, final PDFs
```

## Citation

The code, data and figures are archived on Zenodo under the concept DOI
[10.5281/zenodo.24514815](https://doi.org/10.5281/zenodo.24514815), which resolves to all
versions. Please cite:

> Gupta, A. (2026). rfs-sre-reallocation: exact reconstruction of Renewable Fuel Standard
> percentage standards and evaluation of exemption-reallocation timing rules (v1.0.3).
> Zenodo. https://doi.org/10.5281/zenodo.24514815

Machine-readable metadata are in `CITATION.cff`. Code is BSD-3-Clause; text, figures and
derived data are CC BY 4.0.

# Reproduction

## Requirements

Python 3.11 or later with `uv` (the lock file pins every package), `latexmk` with a
TeX Live installation that provides `elsarticle`, `booktabs` and `siunitx`, and
`pandoc` (3.x) for the DOCX outputs. The `Dockerfile` builds an equivalent environment.

## Steps

```bash
uv sync --extra dev                       # environment from uv.lock
python scripts/fetch_data.py --verify     # raw-file checksums against data/MANIFEST.yaml
python -m rfsrealloc.data.build           # processed tables
python -m rfsrealloc.pipeline run --config configs/quick.yaml   # reduced run, about 10 s
python -m rfsrealloc.pipeline run --config configs/paper.yaml   # full run, a few minutes
python figures/make_figures.py --results results/paper --out paper/figures
make paper si comment attachment          # PDFs and DOCX files
pytest                                    # unit, property, validation and regression tests
```

`make all` runs the whole chain; `make quick` runs the reduced configuration used in
continuous integration. Every output under `results/<config>/` has a JSON sidecar with
the git commit, configuration hash, input checksums, package versions and seed.

## Expected runtimes (Apple M-series laptop)

| Step | Time |
|---|---|
| `configs/quick.yaml` | about 10 s |
| `configs/paper.yaml` (100,000 draws; Sobol N = 4096) | about 1–2 min |
| each sensitivity configuration | about 1–2 min |
| figures | under 30 s |
| LaTeX and pandoc builds | under 2 min |

## Regenerating the manifest

`python scripts/fetch_data.py` downloads any missing file from a host that accepts
non-browser clients and rewrites the manifest. Files from `downloads.regulations.gov`
and `edap.epa.gov` must be retrieved through a browser (URLs are in the manifest) and
placed under `data/raw/`; the script then records their checksums.

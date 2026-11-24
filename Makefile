PY ?= .venv/bin/python
CONFIG ?= configs/paper.yaml

.PHONY: all quick env data results figures tables paper si comment attachment docx test lint typecheck refs clean

all: env data results figures paper si comment attachment

env:
	uv sync --extra dev

data:
	$(PY) scripts/fetch_data.py --verify
	$(PY) -m rfsrealloc.data.build

results: data
	$(PY) -m rfsrealloc.pipeline run --config configs/sensitivity_uniform_revision.yaml
	$(PY) -m rfsrealloc.pipeline run --config configs/sensitivity_independent_fuel_errors.yaml
	$(PY) -m rfsrealloc.pipeline run --config $(CONFIG)

quick: data
	$(PY) -m rfsrealloc.pipeline run --config configs/quick.yaml
	$(PY) figures/make_figures.py --results results/quick --out results/quick/figures

figures:
	$(PY) figures/make_figures.py --results results/paper --out paper/figures

paper: figures
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex
	cd paper && pandoc manuscript.tex --citeproc --bibliography=references.bib --resource-path=.:figures --default-image-extension=png -o manuscript.docx

si:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error si.tex

comment:
	cd comment && latexmk -pdf -interaction=nonstopmode -halt-on-error comment.tex
	cd comment && pandoc comment.tex --citeproc --bibliography=../paper/references.bib --resource-path=.:../paper/figures --default-image-extension=png -o comment.docx

attachment:
	cd comment && latexmk -pdf -interaction=nonstopmode -halt-on-error attachment_technical.tex

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check src tests scripts figures

typecheck:
	$(PY) -m mypy --strict src

refs:
	$(PY) scripts/check_refs.py

clean:
	rm -rf results/quick paper/generated
	cd paper && latexmk -C manuscript.tex si.tex || true
	cd comment && latexmk -C comment.tex attachment_technical.tex || true

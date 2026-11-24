"""Every macro used in the manuscript, SI, comment and attachment is defined in the
generated values file, and the generated file is not stale relative to the summary values."""

from __future__ import annotations

import json
import re

import pytest

from rfsrealloc.provenance import ROOT
from rfsrealloc.reporting import _macro_name, macro_names_in

GENERATED = ROOT / "paper" / "generated"
DOCS = [
    ROOT / "paper" / "manuscript.tex",
    ROOT / "paper" / "si.tex",
    ROOT / "comment" / "comment.tex",
    ROOT / "comment" / "attachment_technical.tex",
]


@pytest.mark.skipif(not (GENERATED / "values.tex").exists(), reason="run the paper pipeline first")
def test_macros_defined_and_fresh() -> None:
    tex = (GENERATED / "values.tex").read_text()
    defined = set(re.findall(r"\\newcommand\{\\(val[A-Za-z]+)\}", tex))
    used: set[str] = set()
    for d in DOCS:
        if d.exists():
            used |= macro_names_in(d.read_text())
    missing = used - defined
    assert not missing, f"undefined macros: {sorted(missing)}"
    values = json.loads((GENERATED / "values.json").read_text())
    regenerated = {_macro_name(k) for k in values}
    assert regenerated == defined, "values.tex is stale relative to values.json"
    summary = ROOT / "results" / "summary" / "values_paper.json"
    if summary.exists():
        assert json.loads(summary.read_text()) == values

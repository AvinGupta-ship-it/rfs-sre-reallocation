"""The comment's references to the technical attachment (section, figure and table numbers)
match the numbering that LaTeX will assign to the attachment source."""

from __future__ import annotations

import re

from rfsrealloc.provenance import ROOT

ATTACHMENT = ROOT / "comment" / "attachment_technical.tex"
COMMENT = ROOT / "comment" / "comment.tex"


def attachment_numbers() -> dict[str, str]:
    """Map every \\label in the attachment to the number LaTeX assigns it, in source order."""
    tex = ATTACHMENT.read_text()
    body = tex[tex.index(r"\begin{document}") :]
    numbers: dict[str, str] = {}
    section = subsection = figure = table = 0
    pending: str | None = None
    for m in re.finditer(r"\\(section|subsection|begin\{figure\}|begin\{table\}|label|input)(?:\{([^}]*)\})?", body):
        kind, arg = m.group(1), m.group(2)
        if kind == "section":
            section += 1
            subsection = 0
            pending = str(section)
        elif kind == "subsection":
            subsection += 1
            pending = f"{section}.{subsection}"
        elif kind == "begin{figure}":
            figure += 1
            pending = str(figure)
        elif kind == "begin{table}":
            table += 1
            pending = str(table)
        elif kind == "input" and arg and "table_" in arg:
            table += 1
            label = "tab:" + arg.split("table_")[-1].replace(".tex", "")
            numbers[label] = str(table)
        elif kind == "label" and arg and pending is not None:
            numbers[arg] = pending
            pending = None
    return numbers


def comment_macros() -> dict[str, str]:
    tex = COMMENT.read_text()
    return dict(re.findall(r"\\newcommand\{\\Att(\w+)\}\{([^}]*)\}", tex))


def test_comment_attachment_references_match() -> None:
    numbers = attachment_numbers()
    macros = comment_macros()
    assert macros, "comment defines no \\Att... cross-reference macros"
    expected = {
        "FigResiduals": numbers["fig:residuals"],
        "FigBands": numbers["fig:bands"],
        "FigDistributions": numbers["fig:distributions"],
        "FigTradeoff": numbers["fig:tradeoff"],
        "FigBacktest": numbers["fig:backtest"],
        "FigCarryover": numbers["fig:carryover"],
        "TabInputs": numbers["tab:inputs"],
        "TabReconstruction": numbers["tab:reconstruction"],
        "TabUncertainty": numbers["tab:uncertainty"],
        "TabAccounting": numbers["tab:accounting"],
        "SecReconstruction": numbers["sec:recon"],
        "SecUncertainty": numbers["sec:uncertainty"],
        "SecDeadlines": numbers["sec:deadlines"],
        "SecBacktest": numbers["sec:backtest"],
        "SecCarryover": numbers["sec:carryover"],
    }
    for key, value in expected.items():
        assert macros.get(key) == value, (
            f"\\Att{key} is {macros.get(key)!r} in the comment but {value!r} in the attachment"
        )


def test_comment_uses_only_macro_cross_references() -> None:
    tex = COMMENT.read_text()
    body = tex[tex.index(r"\begin{document}") :]
    stray = re.findall(r"Attachment[,]? (?:Figure|Table|Section)s?~?\d", body)
    assert not stray, f"hard-coded attachment references: {stray}"

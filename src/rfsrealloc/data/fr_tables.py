"""Parse the "Values for Terms in Calculation of the Standards" tables from Federal
Register XML (model-verification check of the hand transcription)."""

from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd

from rfsrealloc.provenance import RAW

FR = RAW / "federal_register"

TERM_RE = re.compile(r"^(RFV|GE|DE|RG|RD|RGS|RDS|GS|DS|G|D)(CB|BBD|AB|RF)?,?(\d{4})?$")

# Column layout of the table in each rule: (document, table title fragment, years per value column)
LAYOUTS: dict[str, tuple[str, list[int | str]]] = {
    "2010-30296": ("Values for Terms in Calculation of the Standards", [2011]),
    "2011-33451": ("Values for Terms in Calculation of the Standards", [2012]),
    "2013-19557": ("Values for Terms in Calculation of the Standards", [2013]),
    "2015-30893": ("Values for Terms in Calculation of the Final Standards", [2014, 2015, 2016]),
    "2016-28879": ("Values for Terms in Calculation of the 2017 Standards", [2017]),
    "2017-26426": ("Values for Terms in Calculation of the 2018 Standards", [2018]),
    "2018-26566": ("Values for Terms in Calculation of the Final 2019 Standards", [2019]),
    "2020-00431": ("Values for Terms in Calculation of the Final 2020 Standards", [2020]),
    "2022-12376": (
        "Volumes for Terms in Calculation of the Percentage Standards",
        [2020, 2021, 2022, "2022_supplemental"],
    ),
    "2023-13462": (
        "Volumes for Terms in Calculation of the Percentage Standards",
        [2023, "2023_supplemental", 2024, 2025],
    ),
}


def _clean_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return re.sub(r"\s+", "", s)


def _clean_value(s: str) -> float | None:
    s = re.sub(r"<SU>[^<]*</SU>", "", s)  # footnote markers
    s = _clean_text(s).rstrip(".")
    s = re.sub(r"^[a-z]", "", s)  # leading footnote letter
    if s.lower().startswith("confidential") or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_terms_table(doc: str) -> pd.DataFrame:
    """Return a long table (document, year, variable, category, value) for one rule."""
    title_fragment, years = LAYOUTS[doc]
    xml = (FR / f"{doc}.xml").read_text(encoding="utf-8", errors="replace")
    tables = re.findall(r"<GPOTABLE.*?</GPOTABLE>", xml, flags=re.S)
    target = None
    for t in tables:
        if title_fragment in html.unescape(re.sub(r"<[^>]+>", "", t)):
            target = t
            break
    if target is None:
        raise ValueError(f"no table with title fragment {title_fragment!r} in {doc}")
    rows: list[dict[str, object]] = []
    for row in re.findall(r"<ROW>(.*?)</ROW>", target, flags=re.S):
        cells = re.findall(r"<ENT[^>]*>(.*?)</ENT>", row, flags=re.S)
        if not cells:
            continue
        term = _clean_text(cells[0])
        m = TERM_RE.match(term)
        if not m:
            continue
        variable, category, _ = m.groups()
        value_cells = cells[1:]
        # drop a description column when present
        if value_cells and _clean_value(value_cells[0]) is None and len(value_cells) > len(years):
            value_cells = value_cells[1:]
        for year, cell in zip(years, value_cells[: len(years)], strict=False):
            rows.append(
                {
                    "document": doc,
                    "year": str(year),
                    "variable": variable,
                    "category": category or "",
                    "value": _clean_value(cell),
                }
            )
    return pd.DataFrame(rows)


def parse_all(docs: list[str] | None = None) -> pd.DataFrame:
    frames = [parse_terms_table(d) for d in (docs or list(LAYOUTS))]
    return pd.concat(frames, ignore_index=True)


def ecfr_standards_table(path: Path = RAW / "ecfr" / "80.1405.xml") -> pd.DataFrame:
    """Annual standards (percent) from Table 1 to 40 CFR 80.1405(a)."""
    xml = path.read_text(encoding="utf-8")
    table = re.search(r"<(?:table|GPOTABLE).*?</(?:table|GPOTABLE)>", xml, flags=re.S | re.I)
    if table is None:
        raise ValueError("no table in eCFR section")
    rows: list[dict[str, object]] = []
    for tr in re.findall(r"<tr.*?</tr>", table.group(0), flags=re.S | re.I):
        cells = [
            html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S | re.I)
        ]
        if len(cells) >= 5 and re.fullmatch(r"\d{4}", cells[0]):

            def num(s: str) -> float | None:
                try:
                    return float(s)
                except ValueError:
                    return None

            rows.append(
                {
                    "year": int(cells[0]),
                    "CB": num(cells[1]),
                    "BBD": num(cells[2]),
                    "AB": num(cells[3]),
                    "RF": num(cells[4]),
                    "SUPP": num(cells[5]) if len(cells) > 5 else None,
                }
            )
    return pd.DataFrame(rows)

"""EIA annual product-supplied series (thousand barrels per day) from the dnav XLS files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import xlrd

from rfsrealloc.provenance import RAW

EIA = RAW / "eia"


def annual_series(path: Path, name: str) -> pd.DataFrame:
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_name("Data 1")
    rows: list[dict[str, float]] = []
    for r in range(3, sh.nrows):
        d = sh.cell_value(r, 0)
        v = sh.cell_value(r, 1)
        if isinstance(d, float) and isinstance(v, float):
            date = xlrd.xldate_as_datetime(d, wb.datemode)
            rows.append({"year": float(date.year), name: v})
    df = pd.DataFrame(rows)
    df["year"] = df["year"].astype(int)
    return df


def product_supplied() -> pd.DataFrame:
    """Finished motor gasoline and distillate product supplied, billion gallons per year."""
    g = annual_series(EIA / "MGFUPUS2a.xls", "gasoline_kbd")
    d = annual_series(EIA / "MDIUPUS2a.xls", "distillate_kbd")
    df = g.merge(d, on="year", how="inner")
    days = df["year"].apply(lambda y: 366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365)
    df["gasoline_bgal"] = df["gasoline_kbd"] * 1000 * 42 * days / 1e9
    df["distillate_bgal"] = df["distillate_kbd"] * 1000 * 42 * days / 1e9
    return df

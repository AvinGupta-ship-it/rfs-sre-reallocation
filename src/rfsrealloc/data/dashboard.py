"""Readers for the EPA RFS public-data dashboard exports stored under ``data/raw/epa_dashboard``."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from rfsrealloc.provenance import RAW

DASH = RAW / "epa_dashboard"


def _num(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace(",", "", regex=False).str.strip()
    s = s.where(~s.isin(["-", "n/a", "", "nan", "None"]))
    return pd.to_numeric(s, errors="coerce")


def sre_table1(path: Path = DASH / "sre_table1_exempted_volumes.csv") -> pd.DataFrame:
    """Exempted gasoline+diesel volume (million gallons) and exempted RVO (million RINs) by year."""
    df = pd.read_csv(path, dtype=str)
    out = pd.DataFrame(
        {
            "year": df["Compliance Year"].astype(int),
            "exempted_volume_mgal": _num(df.iloc[:, 1]),
            "exempted_rvo_mrins": _num(df.iloc[:, 2]),
            "data_type": df["Data Type"].str.strip(),
        }
    )
    return out.sort_values("year").reset_index(drop=True)


def sre_table2(path: Path = DASH / "sre_table2_petition_decisions.csv") -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df = df.rename(columns={"Compliance Year": "year"})
    for c in df.columns:
        if c != "year":
            df[c] = _num(df[c])
    df["year"] = df["year"].astype(int)
    df.columns = [c.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("%", "pct") for c in df.columns]
    return df.sort_values("year").reset_index(drop=True)


def sre_table3(path: Path = DASH / "sre_table3_petitions_since_2022.csv") -> pd.DataFrame:
    """Per-petition submissions since July 2022 with decision and decision date."""
    df = pd.read_csv(path, dtype=str)
    df.columns = ["submitted", "submitter", "location", "year", "decision", "decision_date"]
    df["submitted"] = pd.to_datetime(df["submitted"], format="%m/%d/%Y", errors="coerce")
    df["decision_date"] = pd.to_datetime(df["decision_date"], format="%m/%d/%Y", errors="coerce")
    df["year"] = df["year"].astype(int)
    return df


def rvo_table1(path: Path = DASH / "rvo_table1_projected_vs_actual_volumes.csv") -> pd.DataFrame:
    """Projected versus reported gasoline and diesel volumes (gallons) by compliance year."""
    df = pd.read_csv(path, dtype=str)
    out = pd.DataFrame(
        {
            "year": df["Compliance Year"].astype(int),
            "projected_use_gal": _num(df.iloc[:, 1]),
            "projected_exempt_gal": _num(df.iloc[:, 2]),
            "reported_obligated_gal": _num(df.iloc[:, 3]),
            "reported_exempt_gal": _num(df.iloc[:, 4]),
            "reported_total_gal": _num(df.iloc[:, 5]),
        }
    )
    return out.sort_values("year").reset_index(drop=True)


def _xlsx(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    return df


def rvo_table2(path: Path = DASH / "rvo_table2_obligations_by_year.xlsx") -> pd.DataFrame:
    """Projected and reported volume obligations (RINs) by year, parameter and category."""
    df = _xlsx(path)
    df.columns = ["year", "parameter", "CB", "BBD", "AB", "RF"]
    for c in ("CB", "BBD", "AB", "RF"):
        df[c] = _num(df[c])
    df["year"] = df["year"].astype(int)
    return df


def rvo_table5(path: Path = DASH / "rvo_table5_rins_retired_by_year.xlsx") -> pd.DataFrame:
    df = _xlsx(path)
    df.columns = ["year", "CB", "BBD", "AB", "RF"]
    for c in ("CB", "BBD", "AB", "RF"):
        df[c] = _num(df[c])
    df["year"] = df["year"].astype(int)
    return df.sort_values("year").reset_index(drop=True)


def rvo_table6(path: Path = DASH / "rvo_table6_deficits_by_year.xlsx") -> pd.DataFrame:
    df = _xlsx(path)
    df.columns = ["year", "CB", "BBD", "AB", "RF"]
    for c in ("CB", "BBD", "AB", "RF"):
        df[c] = _num(df[c])
    df["year"] = df["year"].astype(int)
    return df.sort_values("year").reset_index(drop=True)


def decision_lags(sre3: pd.DataFrame) -> pd.DataFrame:
    """Lag (years) between the end of the compliance year and the decision date, decided petitions only."""
    d = sre3.dropna(subset=["decision_date"]).copy()
    d = d[d["decision"].str.lower() != "pending"]
    year_end = pd.to_datetime(d["year"].astype(str) + "-12-31")
    d["lag_years"] = (d["decision_date"] - year_end).dt.days / 365.25
    d["submission_to_decision_years"] = (d["decision_date"] - d["submitted"]).dt.days / 365.25
    return d


def pending_petitions(sre3: pd.DataFrame, as_of: dt.date | None = None) -> pd.DataFrame:
    p = sre3[sre3["decision"].str.lower() == "pending"]
    return p.sort_values(["year", "submitted"]).reset_index(drop=True)

"""Transcribed inputs with citations, loaded as exact rationals.

Values come from ``data/transcribed/entry_a.csv`` (long layout) and are reconciled
against ``entry_b.csv`` (wide layout, typed independently) by :func:`reconcile`.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import pandas as pd

from rfsrealloc import CATEGORIES, REALLOCATED_CATEGORIES
from rfsrealloc.provenance import TRANSCRIBED

ENTRY_A = TRANSCRIBED / "entry_a.csv"
ENTRY_B = TRANSCRIBED / "entry_b.csv"


@dataclass(frozen=True)
class StandardInputs:
    """Inputs to the percentage-standard equations for one compliance year.

    Volumes in billion gallons; required volumes (``rfv``) in billion gallon-RINs
    (physical gallons for biomass-based diesel before the Set 2 rule).
    """

    year: int
    rfv: Mapping[str, Fraction]
    G: Fraction
    D: Fraction
    RG: Fraction
    RD: Fraction
    GE: Fraction
    DE: Fraction
    source: str = ""

    def with_exempt(self, GE: Fraction, DE: Fraction) -> StandardInputs:
        return StandardInputs(self.year, self.rfv, self.G, self.D, self.RG, self.RD, GE, DE, self.source)

    def with_fuel(self, G: Fraction, D: Fraction) -> StandardInputs:
        return StandardInputs(self.year, self.rfv, G, D, self.RG, self.RD, self.GE, self.DE, self.source)


def load_transcribed(path: Path = ENTRY_A) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"table", "year", "category", "variable", "value", "unit", "source", "locator"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} lacks columns {sorted(missing)}")
    return df


def load_wide(path: Path = ENTRY_B) -> pd.DataFrame:
    """Load the wide second entry (one column per variable)."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {"table", "year", "category", "unit", "source", "locator"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} lacks columns {sorted(missing)}")
    return df


def _frac(x: str) -> Fraction:
    return Fraction(x)


def _lookup(df: pd.DataFrame, table: str, **keys: str) -> pd.DataFrame:
    sub = df[df["table"] == table]
    for k, v in keys.items():
        sub = sub[sub[k] == v]
    return sub


def value(df: pd.DataFrame, table: str, variable: str, year: str = "", category: str = "") -> Fraction:
    sub = _lookup(df, table, variable=variable, year=year, category=category)
    if len(sub) != 1:
        raise KeyError(f"expected one row for {table}/{variable}/{year}/{category}, found {len(sub)}")
    return _frac(str(sub["value"].iloc[0]))


def text_value(df: pd.DataFrame, table: str, variable: str, year: str = "", category: str = "") -> str:
    sub = _lookup(df, table, variable=variable, year=year, category=category)
    if len(sub) != 1:
        raise KeyError(f"expected one row for {table}/{variable}/{year}/{category}, found {len(sub)}")
    return str(sub["value"].iloc[0])


def _inputs_from_table(df: pd.DataFrame, table: str, year: int, source: str) -> StandardInputs:
    y = str(year)
    rfv = {
        c: value(df, table, "RFV", y, c)
        for c in CATEGORIES
        if len(_lookup(df, table, variable="RFV", year=y, category=c))
    }
    extra = _lookup(df, table, variable="RFV", year=y, category="SUPP")
    if len(extra):
        rfv["SUPP"] = _frac(str(extra["value"].iloc[0]))

    def opt(var: str) -> Fraction:
        sub = _lookup(df, table, variable=var, year=y, category="")
        return _frac(str(sub["value"].iloc[0])) if len(sub) else Fraction(0)

    return StandardInputs(
        year=year,
        rfv=rfv,
        G=opt("G"),
        D=opt("D"),
        RG=opt("RG"),
        RD=opt("RD"),
        GE=opt("GE"),
        DE=opt("DE"),
        source=source,
    )


def set2_inputs(df: pd.DataFrame) -> dict[int, StandardInputs]:
    """Inputs for 2026 and 2027 from the Set 2 docket memoranda."""
    return {y: _inputs_from_table(df, "set2_inputs", y, "docket_0789") for y in (2026, 2027)}


def srerv(df: pd.DataFrame, alternative: str) -> dict[int, dict[str, Fraction]]:
    """SRE reallocation volumes (billion RINs) by year and category for an alternative."""
    if alternative == "no_srerv":
        return {y: dict.fromkeys(REALLOCATED_CATEGORIES, Fraction(0)) for y in (2026, 2027)}
    return {y: {c: value(df, "srerv", alternative, str(y), c) for c in REALLOCATED_CATEGORIES} for y in (2026, 2027)}


def published_standards(df: pd.DataFrame, alternative: str) -> dict[int, dict[str, str]]:
    """Published percentage standards (as printed, two decimals) by year and category."""
    out: dict[int, dict[str, str]] = {}
    for y in (2026, 2027):
        out[y] = {c: text_value(df, "standards", alternative, str(y), c) for c in CATEGORIES}
    return out


def exempted_fuel(df: pd.DataFrame, table: str = "set2_exempted_fuel") -> dict[int, dict[str, Fraction]]:
    years = sorted({int(y) for y in df[df["table"] == table]["year"]})
    return {y: {k: value(df, table, k, str(y)) for k in ("gasoline", "diesel", "total")} for y in years}


def exempted_rvo_table(df: pd.DataFrame) -> tuple[dict[int, dict[str, Fraction]], dict[int, dict[str, Fraction]]]:
    """Set 2 Table IV.C-2: (percentage standards by year, exempted RVOs in million RINs)."""
    years = (2023, 2024, 2025)
    stds = {y: {c: value(df, "set2_exempted_rvo", "standard", str(y), c) for c in CATEGORIES} for y in years}
    ervo = {y: {c: value(df, "set2_exempted_rvo", "ervo", str(y), c) for c in CATEGORIES} for y in years}
    return stds, ervo


def rin_prices(df: pd.DataFrame, which: str) -> dict[str, Fraction]:
    return {d: value(df, "rin_prices", which, "", d) for d in ("D3", "D4", "D5", "D6")}


def table_vi1(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["table"] == "table_vi1"].copy()
    sub["year"] = sub["year"].astype(int)
    sub["value"] = sub["value"].astype(float)
    return sub.rename(columns={"variable": "alternative"})[["year", "category", "alternative", "value", "unit"]]


def past_rule_inputs(df: pd.DataFrame) -> dict[int, StandardInputs]:
    years = sorted({int(y) for y in df[df["table"] == "past_rule_inputs"]["year"]})
    out: dict[int, StandardInputs] = {}
    for y in years:
        src = str(_lookup(df, "past_rule_inputs", year=str(y))["source"].iloc[0])
        out[y] = _inputs_from_table(df, "past_rule_inputs", y, src)
    return out


def past_rule_inputs_revised(df: pd.DataFrame) -> dict[int, StandardInputs]:
    years = sorted({int(y) for y in df[df["table"] == "past_rule_inputs_revised"]["year"]})
    return {y: _inputs_from_table(df, "past_rule_inputs_revised", y, "fr_2022_12376") for y in years}


def carryover_2024(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["table"] == "carryover_2024"].copy()
    sub["value"] = sub["value"].astype(float)
    return sub.pivot(index="category", columns="variable", values="value")


def carryover_history(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["table"] == "carryover_history"].copy()
    sub["value"] = sub["value"].astype(float)
    sub["year"] = sub["year"].astype(int)
    return sub.pivot_table(index="year", columns=["category", "variable"], values="value")


def sre_decisions(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["table"] == "sre_decisions"].copy()
    sub = sub[sub["year"] != ""]
    sub["year"] = sub["year"].astype(int)
    sub["value"] = sub["value"].astype(float)
    return sub.rename(columns={"category": "action"})[["year", "action", "variable", "value"]]


def decision_dates(df: pd.DataFrame) -> dict[str, dt.date]:
    sub = df[(df["table"] == "sre_decision_dates")]
    return {str(r["category"]): dt.date.fromisoformat(str(r["value"])) for _, r in sub.iterrows()}


def deadline(df: pd.DataFrame, variable: str, year: str = "") -> dt.date:
    return dt.date.fromisoformat(text_value(df, "deadlines", variable, year))


def regulatory_parameter(df: pd.DataFrame, variable: str) -> str:
    return text_value(df, "regulatory_parameters", variable)


def _wide_to_long(df_b: pd.DataFrame) -> pd.DataFrame:
    """Convert the wide second entry to the long layout for comparison."""
    rows: list[dict[str, str]] = []
    id_cols = ["table", "year", "category", "unit", "source", "locator"]
    for _, r in df_b.iterrows():
        for col in df_b.columns:
            if col in id_cols or str(r[col]) == "":
                continue
            rows.append(
                {
                    "table": r["table"],
                    "year": r["year"],
                    "category": r["category"],
                    "variable": col,
                    "value": str(r[col]),
                }
            )
    return pd.DataFrame(rows)


def reconcile(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    """Return rows where the two entries disagree or where either entry lacks a value.

    Entry A is in long layout; entry B is in wide layout (one column per variable).
    Comparison is numeric where both parse as rationals, textual otherwise.
    """
    long_b = _wide_to_long(df_b)
    key = ["table", "year", "category", "variable"]
    merged = df_a[key + ["value"]].merge(long_b, on=key, how="outer", suffixes=("_a", "_b"), indicator=True)

    def differs(row: pd.Series) -> bool:
        a, b = row["value_a"], row["value_b"]
        if row["_merge"] != "both":
            return True
        try:
            return Fraction(str(a)) != Fraction(str(b))
        except ValueError:
            return str(a) != str(b)

    mask = merged.apply(differs, axis=1)
    return merged[mask].reset_index(drop=True)

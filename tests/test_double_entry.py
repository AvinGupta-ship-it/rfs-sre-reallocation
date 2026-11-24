"""Transcribed inputs are double-entered and reconciled; hand transcription agrees with
values parsed by code from the Federal Register XML and the eCFR."""

from __future__ import annotations

import pandas as pd
import pytest

from rfsrealloc.data.fr_tables import ecfr_standards_table, parse_all
from rfsrealloc.inputs import ENTRY_A, ENTRY_B, load_transcribed, load_wide, reconcile


def test_entries_agree() -> None:
    if not ENTRY_B.exists():
        pytest.fail("second transcription entry is missing")
    mism = reconcile(load_transcribed(ENTRY_A), load_wide(ENTRY_B))
    assert mism.empty, mism.to_string()


def test_every_row_has_source_and_locator(transcribed: pd.DataFrame) -> None:
    assert (transcribed["source"] != "").all()
    assert (transcribed["locator"] != "").all()


def test_transcription_matches_parsed_federal_register_tables(transcribed: pd.DataFrame) -> None:
    parsed = parse_all()
    parsed["category"] = parsed["category"].fillna("")
    t = transcribed[transcribed["table"].isin(["past_rule_inputs", "past_rule_inputs_revised"])]
    compared = 0
    for r in t.itertuples():
        if r.category == "SUPP":
            continue
        if r.table == "past_rule_inputs_revised":
            sub = parsed[
                (parsed.document == "2022-12376")
                & (parsed.year == "2020")
                & (parsed.variable == r.variable)
                & (parsed.category == r.category)
            ]
        else:
            sub = parsed[
                (parsed.year == r.year)
                & (parsed.variable == r.variable)
                & (parsed.category == r.category)
                & ~((parsed.document == "2022-12376") & (parsed.year == "2020"))
            ]
        if sub.empty or pd.isna(sub.value.iloc[0]):
            continue
        compared += 1
        assert abs(float(r.value) - float(sub.value.iloc[0])) < 1e-9, (r.table, r.year, r.variable, r.category)
    assert compared >= 150


def test_transcribed_standards_match_ecfr(transcribed: pd.DataFrame) -> None:
    ecfr = ecfr_standards_table().set_index("year")
    sub = transcribed[(transcribed["table"] == "standards") & (transcribed["variable"] == "set2")]
    for r in sub.itertuples():
        assert abs(float(r.value) - float(ecfr.loc[int(r.year), r.category])) < 1e-9
    sub = transcribed[(transcribed["table"] == "set2_exempted_rvo") & (transcribed["variable"] == "standard")]
    for r in sub.itertuples():
        assert abs(float(r.value) - float(ecfr.loc[int(r.year), r.category])) < 1e-9

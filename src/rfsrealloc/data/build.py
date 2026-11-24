"""Build analysis-ready tables under ``data/processed`` from the raw downloads."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rfsrealloc.data import PROCESSED
from rfsrealloc.data import dashboard as dash
from rfsrealloc.data.eia import product_supplied
from rfsrealloc.data.fr_tables import ecfr_standards_table, parse_all


def build(out: Path = PROCESSED) -> dict[str, Path]:
    out.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    def save(name: str, df: pd.DataFrame) -> None:
        p = out / f"{name}.csv"
        df.to_csv(p, index=False)
        written[name] = p

    save("sre_exempted_by_year", dash.sre_table1())
    save("sre_petition_decisions", dash.sre_table2())
    save("sre_petitions_since_2022", dash.sre_table3())
    save("rvo_projected_vs_actual", dash.rvo_table1())
    save("rvo_obligations_by_year", dash.rvo_table2())
    save("rins_retired_by_year", dash.rvo_table5())
    save("deficits_by_year", dash.rvo_table6())
    save("fr_values_for_terms", parse_all())
    save("ecfr_standards", ecfr_standards_table())
    save("eia_product_supplied", product_supplied())
    return written


if __name__ == "__main__":
    for name, path in build().items():
        print(name, path)

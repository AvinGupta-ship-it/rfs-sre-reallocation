# Transcribed values

Values transcribed by hand from Federal Register documents, docket memoranda, EPA
decision documents and the Set 2 Regulatory Impact Analysis. Each value carries a
source identifier (a key in `paper/references.bib`) and a locator (table, page or
section). The two files `entry_a.csv` (long layout) and `entry_b.csv` (wide layout)
were typed in separate passes from the source documents; `tests/test_double_entry.py`
reconciles them, and `tests/test_fr_parsing.py` compares the Federal Register tables
with values parsed by code from the raw XML.

Units: percentage standards in percent; volumes in billion gallons or billion
gallon-RINs unless the `unit` column says otherwise; RIN prices in dollars per RIN;
fuel prices in cents per gallon.

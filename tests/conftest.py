from __future__ import annotations

import pandas as pd
import pytest

from rfsrealloc.inputs import ENTRY_A, load_transcribed


@pytest.fixture(scope="session")
def transcribed() -> pd.DataFrame:
    return load_transcribed(ENTRY_A)

"""Loads the cached Elexon CSVs once and keeps them in memory."""
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    actuals = pd.read_csv(DATA_DIR / "actuals.csv")
    actuals["startTime"] = pd.to_datetime(actuals["startTime"], utc=True)

    forecasts = pd.read_csv(DATA_DIR / "forecasts.csv")
    forecasts["startTime"] = pd.to_datetime(forecasts["startTime"], utc=True)
    forecasts["publishTime"] = pd.to_datetime(forecasts["publishTime"], utc=True)

    return actuals, forecasts
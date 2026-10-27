"""
Fetch January 2026 wind data from the Elexon Insights API (no API key needed).

Outputs (in ../data/):
  actuals.csv    -> startTime, actual        (FUELHH, fuelType = WIND)
  forecasts.csv  -> startTime, publishTime, forecast   (WINDFOR)

Run from the backend/ folder:
  pip install requests pandas
  python scripts/fetch_data.py
"""
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Target period: January 2026 (UTC)
TARGET_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
TARGET_END = datetime(2026, 2, 1, tzinfo=timezone.utc)  # exclusive

# Forecasts for early January may have been published well before 1 Jan,
# so we fetch publish times from earlier in December too.
PUBLISH_FROM = datetime(2025, 12, 17, tzinfo=timezone.utc)
PUBLISH_TO = datetime(2026, 2, 1, tzinfo=timezone.utc)

CHUNK_DAYS = 7  # keep each request small and safe


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%MZ")


def get_json(url: str, params: dict, retries: int = 4):
    """GET with simple retry/backoff. Handles both a bare list and {"data": [...]}."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict) and "data" in payload:
                return payload["data"]
            return payload
        except requests.RequestException as exc:
            wait = 2 ** attempt
            print(f"  request failed ({exc}); retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url} with {params}")


def chunks(start: datetime, end: datetime, days: int):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def fetch_actuals() -> pd.DataFrame:
    print("Fetching actuals (FUELHH, WIND)...")
    rows = []
    for start, end in chunks(TARGET_START, TARGET_END, CHUNK_DAYS):
        params = {
            "settlementDateFrom": start.strftime("%Y-%m-%d"),
            # settlementDateTo is inclusive, so step back one day
            "settlementDateTo": (end - timedelta(days=1)).strftime("%Y-%m-%d"),
            "fuelType": "WIND",
        }
        data = get_json(f"{BASE_URL}/FUELHH/stream", params)
        print(f"  {params['settlementDateFrom']} -> {params['settlementDateTo']}: {len(data)} rows")
        rows.extend(data)

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No actuals returned. Check the parameters against the Elexon docs.")

    df = df[df["fuelType"] == "WIND"].copy()
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df = df.rename(columns={"generation": "actual"})[["startTime", "actual"]]
    df = df[(df["startTime"] >= TARGET_START) & (df["startTime"] < TARGET_END)]
    df = df.drop_duplicates(subset="startTime", keep="last").sort_values("startTime")
    return df.reset_index(drop=True)


def fetch_forecasts() -> pd.DataFrame:
    print("Fetching forecasts (WINDFOR)...")
    rows = []
    for start, end in chunks(PUBLISH_FROM, PUBLISH_TO, CHUNK_DAYS):
        params = {
            "publishDateTimeFrom": iso(start),
            "publishDateTimeTo": iso(end),
        }
        data = get_json(f"{BASE_URL}/WINDFOR/stream", params)
        print(f"  publish {params['publishDateTimeFrom']} -> {params['publishDateTimeTo']}: {len(data)} rows")
        rows.extend(data)

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No forecasts returned. Check the parameters against the Elexon docs.")

    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df = df.rename(columns={"generation": "forecast"})[["startTime", "publishTime", "forecast"]]
    # Keep only forecasts whose target time is in January 2026
    df = df[(df["startTime"] >= TARGET_START) & (df["startTime"] < TARGET_END)]
    df = df.drop_duplicates(subset=["startTime", "publishTime"], keep="last")
    df = df.sort_values(["startTime", "publishTime"])
    return df.reset_index(drop=True)


def sanity_report(actuals: pd.DataFrame, forecasts: pd.DataFrame) -> None:
    expected = 31 * 48  # half-hours in January
    print("\n--- Sanity check ---")
    print(f"Actuals:   {len(actuals)} rows (expected about {expected})")
    print(f"Forecasts: {len(forecasts)} rows, {forecasts['publishTime'].nunique()} distinct publish times")
    lead = (forecasts["startTime"] - forecasts["publishTime"]).dt.total_seconds() / 3600
    print(f"Forecast horizon range: {lead.min():.1f}h to {lead.max():.1f}h")
    missing = pd.date_range(TARGET_START, TARGET_END - timedelta(minutes=30), freq="30min")
    gaps = missing.difference(pd.DatetimeIndex(actuals["startTime"]))
    print(f"Missing actual half-hours: {len(gaps)}")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    actuals = fetch_actuals()
    forecasts = fetch_forecasts()
    actuals.to_csv(DATA_DIR / "actuals.csv", index=False)
    forecasts.to_csv(DATA_DIR / "forecasts.csv", index=False)
    sanity_report(actuals, forecasts)
    print(f"\nSaved to {DATA_DIR}")


if __name__ == "__main__":
    main()
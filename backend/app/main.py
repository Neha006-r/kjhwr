"""FastAPI app: wind forecast monitoring for day-ahead power purchasing."""
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import metrics
from .data_loader import load_data
from .forecast_logic import build_comparison, select_forecasts

DATA_START = pd.Timestamp("2026-01-01", tz="UTC")
DATA_END = pd.Timestamp("2026-02-01", tz="UTC")  # exclusive
MAX_HORIZON = 48
DEFAULT_HORIZON = 24

app = FastAPI(title="Wind Forecast Monitor", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # public, read-only data
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _to_utc(value: Optional[str], default: pd.Timestamp) -> pd.Timestamp:
    if value is None:
        return default
    try:
        ts = pd.Timestamp(value)
    except (ValueError, TypeError):
        raise HTTPException(400, f"Invalid datetime: {value}")
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _resolve_range(start: Optional[str], end: Optional[str]):
    s = _to_utc(start, DATA_START)
    e = _to_utc(end, DATA_END)
    if s >= e:
        raise HTTPException(400, "start must be before end")
    if s < DATA_START or e > DATA_END:
        raise HTTPException(400, "Range must be within January 2026 (UTC)")
    return s, e


def _records(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    out = df[cols].copy()
    for c in ("startTime", "publishTime"):
        if c in out.columns:
            out[c] = out[c].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out = out.astype(object).where(out.notna(), None)
    return out.to_dict("records")


def _in_range(df: pd.DataFrame, s: pd.Timestamp, e: pd.Timestamp) -> pd.DataFrame:
    return df[(df["startTime"] >= s) & (df["startTime"] < e)]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    actuals, forecasts = load_data()
    return {
        "data_start": DATA_START.isoformat(),
        "data_end": DATA_END.isoformat(),
        "max_horizon_hours": MAX_HORIZON,
        "default_horizon_hours": DEFAULT_HORIZON,
        "actual_rows": int(len(actuals)),
        "forecast_rows": int(len(forecasts)),
    }


@app.get("/api/actuals")
def get_actuals(start: Optional[str] = None, end: Optional[str] = None):
    """Actual wind generation (MW). start inclusive, end exclusive."""
    s, e = _resolve_range(start, end)
    actuals, _ = load_data()
    return _records(_in_range(actuals, s, e), ["startTime", "actual"])


@app.get("/api/forecasts")
def get_forecasts(
    start: Optional[str] = None,
    end: Optional[str] = None,
    horizon: float = Query(DEFAULT_HORIZON, ge=0, le=MAX_HORIZON),
):
    """Latest forecast available at least `horizon` hours before each target time."""
    s, e = _resolve_range(start, end)
    _, forecasts = load_data()
    chosen = select_forecasts(forecasts, horizon)
    return _records(
        _in_range(chosen, s, e),
        ["startTime", "publishTime", "forecast", "horizon_hours"],
    )


@app.get("/api/series")
def get_series(
    start: Optional[str] = None,
    end: Optional[str] = None,
    horizon: float = Query(DEFAULT_HORIZON, ge=0, le=MAX_HORIZON),
):
    """Actual vs forecast, joined per half-hour, with error = forecast - actual."""
    s, e = _resolve_range(start, end)
    actuals, forecasts = load_data()
    df = _in_range(build_comparison(actuals, forecasts, horizon), s, e)
    return _records(df, ["startTime", "actual", "forecast", "error", "publishTime", "horizon_hours"])


@app.get("/api/metrics")
def get_metrics(
    start: Optional[str] = None,
    end: Optional[str] = None,
    horizon: float = Query(DEFAULT_HORIZON, ge=0, le=MAX_HORIZON),
):
    """Accuracy summary and error by hour of day for the chosen horizon."""
    s, e = _resolve_range(start, end)
    actuals, forecasts = load_data()
    df = _in_range(build_comparison(actuals, forecasts, horizon), s, e)
    return {
        "horizon_hours": horizon,
        "start": s.isoformat(),
        "end": e.isoformat(),
        "summary": metrics.summarize(df),
        "by_hour_of_day": metrics.by_hour_of_day(df),
    }


@app.get("/api/metrics/by-horizon")
def get_metrics_by_horizon(
    start: Optional[str] = None,
    end: Optional[str] = None,
    horizons: str = "0,3,6,12,18,24,30,36,42,48",
):
    """How accuracy changes as the forecast gets older (longer horizon)."""
    s, e = _resolve_range(start, end)
    try:
        hs = sorted({float(h) for h in horizons.split(",") if h.strip()})
    except ValueError:
        raise HTTPException(400, "horizons must be comma-separated numbers")
    if not hs or hs[0] < 0 or hs[-1] > MAX_HORIZON:
        raise HTTPException(400, f"horizons must be between 0 and {MAX_HORIZON}")
    actuals, forecasts = load_data()
    result = []
    for h in hs:
        df = _in_range(build_comparison(actuals, forecasts, h), s, e)
        result.append({"horizon_hours": h, **metrics.summarize(df)})
    return result
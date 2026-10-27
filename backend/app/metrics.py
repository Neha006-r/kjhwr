"""Accuracy metrics. error = forecast - actual (positive = over-forecast)."""
import numpy as np
import pandas as pd


def _f(x):
    """numpy -> plain float, NaN -> None (JSON safe)."""
    if x is None or pd.isna(x):
        return None
    return float(x)


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "n": 0, "mae": None, "rmse": None, "bias": None,
            "mae_pct_of_mean_actual": None,
            "p50_abs_error": None, "p90_abs_error": None,
            "p99_abs_error": None, "max_abs_error": None,
        }
    err = df["error"]
    abs_err = err.abs()
    mae = abs_err.mean()
    mean_actual = df["actual"].mean()
    return {
        "n": int(len(df)),
        "mae": _f(mae),
        "rmse": _f(np.sqrt((err ** 2).mean())),
        "bias": _f(err.mean()),
        "mae_pct_of_mean_actual": _f(mae / mean_actual * 100) if mean_actual else None,
        "p50_abs_error": _f(abs_err.quantile(0.50)),
        "p90_abs_error": _f(abs_err.quantile(0.90)),
        "p99_abs_error": _f(abs_err.quantile(0.99)),
        "max_abs_error": _f(abs_err.max()),
    }


def by_hour_of_day(df: pd.DataFrame) -> list[dict]:
    """Hour is UTC, which equals UK local time in January (GMT)."""
    if df.empty:
        return []
    tmp = df.assign(hour=df["startTime"].dt.hour, abs_error=df["error"].abs())
    grouped = tmp.groupby("hour").agg(
        mae=("abs_error", "mean"), bias=("error", "mean"), n=("error", "size")
    )
    return [
        {"hour": int(h), "mae": _f(r["mae"]), "bias": _f(r["bias"]), "n": int(r["n"])}
        for h, r in grouped.iterrows()
    ]
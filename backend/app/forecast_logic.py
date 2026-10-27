"""Core business rule: which forecast would a buyer actually have seen?"""
import pandas as pd


def select_forecasts(forecasts: pd.DataFrame, horizon_hours: float) -> pd.DataFrame:
    """
    For each target startTime, keep the LATEST forecast that was published at
    least `horizon_hours` before startTime. Forecasts published later than that
    would not have been available when the purchase decision was made.

    Returns columns: startTime, publishTime, forecast, horizon_hours
    """
    cols = ["startTime", "publishTime", "forecast", "horizon_hours"]
    if forecasts.empty:
        return pd.DataFrame(columns=cols)

    lead = forecasts["startTime"] - forecasts["publishTime"]
    eligible = forecasts[lead >= pd.Timedelta(hours=horizon_hours)]
    if eligible.empty:
        return pd.DataFrame(columns=cols)

    chosen = (
        eligible.sort_values(["startTime", "publishTime"])
        .drop_duplicates(subset="startTime", keep="last")
        .copy()
    )
    chosen["horizon_hours"] = (
        (chosen["startTime"] - chosen["publishTime"]).dt.total_seconds() / 3600
    )
    return chosen[cols].reset_index(drop=True)


def build_comparison(
    actuals: pd.DataFrame, forecasts: pd.DataFrame, horizon_hours: float
) -> pd.DataFrame:
    """Join actuals with the horizon-selected forecast. error = forecast - actual."""
    chosen = select_forecasts(forecasts, horizon_hours)
    merged = actuals.merge(chosen, on="startTime", how="inner")
    merged["error"] = merged["forecast"] - merged["actual"]
    return merged.sort_values("startTime").reset_index(drop=True)
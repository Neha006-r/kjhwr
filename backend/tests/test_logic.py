import math

import pandas as pd

from app.forecast_logic import build_comparison, select_forecasts
from app.metrics import summarize


def ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


def make_forecasts() -> pd.DataFrame:
    # Target 12:00 on 10 Jan; forecasts published 48h, 30h and 2h before it.
    return pd.DataFrame(
        {
            "startTime": [ts("2026-01-10 12:00")] * 3,
            "publishTime": [
                ts("2026-01-08 12:00"),
                ts("2026-01-09 06:00"),
                ts("2026-01-10 10:00"),
            ],
            "forecast": [100.0, 200.0, 300.0],
        }
    )


def pick(h: float) -> float:
    return select_forecasts(make_forecasts(), h)["forecast"].iloc[0]


def test_picks_latest_forecast_at_least_horizon_old():
    assert pick(24) == 200.0  # the 2h-old forecast is too recent
    assert pick(3) == 200.0
    assert pick(0) == 300.0
    assert pick(48) == 100.0


def test_no_forecast_old_enough_returns_empty():
    assert select_forecasts(make_forecasts(), 60).empty


def test_forecast_published_after_target_is_never_used():
    f = make_forecasts()
    f.loc[len(f)] = [ts("2026-01-10 12:00"), ts("2026-01-10 14:00"), 999.0]
    assert select_forecasts(f, 0)["forecast"].iloc[0] == 300.0


def test_build_comparison_error_is_forecast_minus_actual():
    actuals = pd.DataFrame({"startTime": [ts("2026-01-10 12:00")], "actual": [250.0]})
    df = build_comparison(actuals, make_forecasts(), 24)
    assert df["forecast"].iloc[0] == 200.0
    assert df["error"].iloc[0] == -50.0


def test_summarize_metrics():
    df = pd.DataFrame(
        {"actual": [100.0] * 4, "forecast": [110.0, 90.0, 120.0, 80.0]}
    )
    df["error"] = df["forecast"] - df["actual"]
    m = summarize(df)
    assert m["n"] == 4
    assert m["mae"] == 15.0
    assert m["bias"] == 0.0
    assert math.isclose(m["rmse"], math.sqrt(250))


def test_summarize_empty():
    assert summarize(pd.DataFrame(columns=["actual", "forecast", "error"]))["n"] == 0
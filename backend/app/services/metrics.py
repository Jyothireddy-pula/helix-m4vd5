"""Quantitative metrics for wind forecast accuracy analysis."""
import math
from typing import Optional
import pandas as pd
import numpy as np


def compute_metrics(df: pd.DataFrame) -> dict:
    """Compute all accuracy metrics from the analysis table.

    Requires columns: actual_generation, selected_forecast, signed_error,
                      abs_error, squared_error, pct_error, forecast_status
    Error convention: signed_error = forecast - actual
      Positive = overforecast, Negative = underforecast
    """
    total_intervals = len(df)
    if df.empty or "forecast_status" not in df.columns:
        available = df
        n = 0
    else:
        available = df[df["forecast_status"] == "available"].copy()
        n = len(available)

    if n == 0:
        return {
            "total_intervals": total_intervals,
            "n_with_forecast": 0,
            "n_without_forecast": total_intervals,
            "forecast_coverage_pct": 0.0,
            "mae": None,
            "rmse": None,
            "mean_bias_error": None,
            "median_abs_error": None,
            "mape": None,
            "wape": None,
            "mean_actual": None,
            "mean_forecast": None,
            "n_overforecast": None,
            "n_underforecast": None,
            "n_exact": None,
            "overforecast_pct": None,
            "underforecast_pct": None,
        }

    forecast_coverage = round(100.0 * n / total_intervals, 2) if total_intervals > 0 else 0.0

    mae = float(available["abs_error"].mean()) if available["abs_error"].notna().any() else None
    rmse = float(np.sqrt(available["squared_error"].mean())) if available["squared_error"].notna().any() else None
    mean_bias = float(available["signed_error"].mean()) if available["signed_error"].notna().any() else None
    median_abs = float(available["abs_error"].median()) if available["abs_error"].notna().any() else None
    mean_actual = float(available["actual_generation"].mean()) if available["actual_generation"].notna().any() else None
    mean_forecast = float(available["selected_forecast"].mean()) if available["selected_forecast"].notna().any() else None

    # MAPE: only when actual != 0
    valid_pct = available[available["pct_error"].notna()]
    mape = float(valid_pct["pct_error"].abs().mean()) if len(valid_pct) > 0 else None

    # WAPE: sum(|forecast-actual|) / sum(|actual|) * 100
    sum_actual = available["actual_generation"].abs().sum()
    sum_abs_error = available["abs_error"].sum()
    wape = float(100.0 * sum_abs_error / sum_actual) if sum_actual > 0 else None

    # Directional
    n_over = int((available["signed_error"] > 0).sum())
    n_under = int((available["signed_error"] < 0).sum())
    n_exact = int((available["signed_error"] == 0).sum())

    return {
        "total_intervals": total_intervals,
        "n_with_forecast": n,
        "n_without_forecast": total_intervals - n,
        "forecast_coverage_pct": forecast_coverage,
        "mae": round(mae, 2) if mae is not None else None,
        "rmse": round(rmse, 2) if rmse is not None else None,
        "mean_bias_error": round(mean_bias, 2) if mean_bias is not None else None,
        "median_abs_error": round(median_abs, 2) if median_abs is not None else None,
        "mape": round(mape, 2) if mape is not None else None,
        "wape": round(wape, 2) if wape is not None else None,
        "mean_actual": round(mean_actual, 2) if mean_actual is not None else None,
        "mean_forecast": round(mean_forecast, 2) if mean_forecast is not None else None,
        "n_overforecast": n_over,
        "n_underforecast": n_under,
        "n_exact": n_exact,
        "overforecast_pct": round(100.0 * n_over / n, 2) if n > 0 else None,
        "underforecast_pct": round(100.0 * n_under / n, 2) if n > 0 else None,
    }


def compute_daily_metrics(df: pd.DataFrame) -> list[dict]:
    """Compute per-day metrics."""
    if df.empty:
        return []
    df2 = df.copy()
    df2["date"] = df2["delivery_start"].dt.date
    results = []
    for d, group in df2.groupby("date"):
        m = compute_metrics(group)
        m["date"] = d.isoformat()
        results.append(m)
    return results


def compute_lead_time_metrics(df: pd.DataFrame) -> list[dict]:
    """Group metrics by lead-time buckets."""
    if df.empty or "lead_time_hours" not in df.columns:
        return []
    avail = df[df["forecast_status"] == "available"].copy()
    if avail.empty:
        return []

    bins = [0, 12, 24, 36, 48, float("inf")]
    labels = ["0-12h", "12-24h", "24-36h", "36-48h", ">48h"]
    avail["lead_bucket"] = pd.cut(avail["lead_time_hours"], bins=bins, labels=labels, right=False)

    results = []
    for label, group in avail.groupby("lead_bucket", observed=True):
        m = compute_metrics(group)
        m["lead_time_bucket"] = str(label)
        results.append(m)
    return results

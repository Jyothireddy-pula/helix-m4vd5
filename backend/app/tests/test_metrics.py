"""Unit tests for metric calculations."""
import pytest
import pandas as pd
from datetime import datetime, timezone
from app.services.metrics import compute_metrics, compute_daily_metrics

UTC = timezone.utc


def make_df(rows: list[dict]) -> pd.DataFrame:
    """Create analysis DataFrame from simplified rows."""
    full_rows = []
    for r in rows:
        actual = r.get("actual")
        forecast = r.get("forecast")
        signed = (forecast - actual) if actual is not None and forecast is not None else None
        abs_e = abs(signed) if signed is not None else None
        sq_e = signed ** 2 if signed is not None else None
        pct = 100.0 * signed / actual if signed is not None and actual != 0 else None
        status = r.get("status", "available" if forecast is not None else "unavailable")
        full_rows.append({
            "delivery_start": r.get("ts", datetime(2026, 1, 1, tzinfo=UTC)),
            "actual_generation": actual,
            "selected_forecast": forecast,
            "forecast_publish_time": None,
            "decision_cutoff": None,
            "lead_time_hours": None,
            "signed_error": signed,
            "abs_error": abs_e,
            "squared_error": sq_e,
            "pct_error": pct,
            "forecast_status": status,
            "data_quality_flag": None,
        })
    return pd.DataFrame(full_rows)


class TestComputeMetrics:
    def test_empty(self):
        df = make_df([])
        m = compute_metrics(df)
        assert m["n_with_forecast"] == 0
        assert m["mae"] is None

    def test_simple_mae(self):
        df = make_df([
            {"actual": 1000, "forecast": 1100},
            {"actual": 2000, "forecast": 1900},
        ])
        m = compute_metrics(df)
        assert m["mae"] == pytest.approx(100.0)

    def test_rmse(self):
        df = make_df([
            {"actual": 1000, "forecast": 1200},  # error=200
            {"actual": 1000, "forecast": 800},   # error=-200
        ])
        m = compute_metrics(df)
        assert m["rmse"] == pytest.approx(200.0)

    def test_mean_bias_positive_is_overforecast(self):
        df = make_df([
            {"actual": 1000, "forecast": 1100},  # +100
            {"actual": 1000, "forecast": 1200},  # +200
        ])
        m = compute_metrics(df)
        assert m["mean_bias_error"] == pytest.approx(150.0)

    def test_mean_bias_negative_is_underforecast(self):
        df = make_df([
            {"actual": 1000, "forecast": 900},  # -100
        ])
        m = compute_metrics(df)
        assert m["mean_bias_error"] == pytest.approx(-100.0)

    def test_coverage(self):
        df = make_df([
            {"actual": 1000, "forecast": 1100},
            {"actual": 1000, "forecast": None, "status": "unavailable"},
        ])
        m = compute_metrics(df)
        assert m["n_with_forecast"] == 1
        assert m["forecast_coverage_pct"] == 50.0

    def test_no_divide_by_zero_on_zero_actual(self):
        df = make_df([{"actual": 0, "forecast": 500}])
        m = compute_metrics(df)
        assert m["mae"] == pytest.approx(500.0)
        # mape should be None (undefined for zero actual)
        assert m["mape"] is None

    def test_wape_denominator(self):
        df = make_df([
            {"actual": 1000, "forecast": 1200},
            {"actual": 2000, "forecast": 1800},
        ])
        m = compute_metrics(df)
        # WAPE = (200 + 200) / (1000 + 2000) * 100 = 400/3000*100 = 13.33...
        assert m["wape"] == pytest.approx(400.0 / 3000.0 * 100, rel=1e-3)

    def test_directional_counts(self):
        df = make_df([
            {"actual": 1000, "forecast": 1100},  # over
            {"actual": 1000, "forecast": 900},   # under
            {"actual": 1000, "forecast": 1000},  # exact
        ])
        m = compute_metrics(df)
        assert m["n_overforecast"] == 1
        assert m["n_underforecast"] == 1
        assert m["n_exact"] == 1

"""Unit tests for forecast vintage selection logic."""
import pytest
from datetime import datetime, timezone
from app.services.forecast_selection import (
    compute_decision_cutoff,
    select_forecast_vintage,
    build_analysis_table,
)

UTC = timezone.utc


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


class TestDecisionCutoff:
    def test_basic(self):
        delivery = dt("2026-01-05T10:00:00")
        cutoff = compute_decision_cutoff(delivery, 16, 0)
        assert cutoff == dt("2026-01-04T16:00:00")

    def test_midnight_boundary(self):
        delivery = dt("2026-01-01T00:00:00")
        cutoff = compute_decision_cutoff(delivery, 16, 0)
        assert cutoff == dt("2025-12-31T16:00:00")

    def test_end_of_day(self):
        delivery = dt("2026-01-31T23:30:00")
        cutoff = compute_decision_cutoff(delivery, 16, 0)
        assert cutoff == dt("2026-01-30T16:00:00")


class TestSelectForecastVintage:
    def _forecasts(self, publish_times: list[str], gen_start=5000):
        delivery = dt("2026-01-10T12:00:00")
        return [
            {"start_time_utc": delivery, "publish_time_utc": dt(pt), "generation": gen_start + i * 100}
            for i, pt in enumerate(publish_times)
        ]

    def test_selects_latest_eligible(self):
        forecasts = self._forecasts(["2026-01-09T12:00:00", "2026-01-09T14:00:00", "2026-01-09T16:00:00"])
        delivery = dt("2026-01-10T12:00:00")
        result = select_forecast_vintage(delivery, forecasts, 16, 0)
        assert result["status"] == "available"
        # cutoff is 2026-01-09T16:00 — all three are eligible, pick latest (2026-01-09T16:00)
        assert result["publish_time_utc"] == dt("2026-01-09T16:00:00")
        assert result["selected_generation"] == 5200

    def test_excludes_after_cutoff(self):
        forecasts = self._forecasts(["2026-01-09T15:00:00", "2026-01-09T17:00:00"])
        delivery = dt("2026-01-10T12:00:00")
        result = select_forecast_vintage(delivery, forecasts, 16, 0)
        assert result["status"] == "available"
        assert result["publish_time_utc"] == dt("2026-01-09T15:00:00")

    def test_no_eligible_forecast(self):
        forecasts = self._forecasts(["2026-01-09T17:00:00", "2026-01-09T20:00:00"])
        delivery = dt("2026-01-10T12:00:00")
        result = select_forecast_vintage(delivery, forecasts, 16, 0)
        assert result["status"] == "unavailable"
        assert result["selected_generation"] is None

    def test_empty_forecasts(self):
        delivery = dt("2026-01-10T12:00:00")
        result = select_forecast_vintage(delivery, [], 16, 0)
        assert result["status"] == "unavailable"

    def test_identical_publish_times(self):
        delivery = dt("2026-01-10T12:00:00")
        forecasts = [
            {"start_time_utc": delivery, "publish_time_utc": dt("2026-01-09T14:00:00"), "generation": 5000},
            {"start_time_utc": delivery, "publish_time_utc": dt("2026-01-09T14:00:00"), "generation": 5100},
        ]
        result = select_forecast_vintage(delivery, forecasts, 16, 0)
        assert result["status"] == "available"
        assert result["selected_generation"] in (5000, 5100)

    def test_lead_time_calculation(self):
        delivery = dt("2026-01-10T12:00:00")
        forecasts = [{"start_time_utc": delivery, "publish_time_utc": dt("2026-01-09T14:00:00"), "generation": 5000}]
        result = select_forecast_vintage(delivery, forecasts, 16, 0)
        # From 2026-01-09T14:00 to 2026-01-10T12:00 = 22 hours
        assert result["lead_time_hours"] == 22.0

    def test_cutoff_at_exact_boundary(self):
        delivery = dt("2026-01-10T12:00:00")
        # Forecast published exactly at cutoff (16:00 D-1) should be eligible
        forecasts = [{"start_time_utc": delivery, "publish_time_utc": dt("2026-01-09T16:00:00"), "generation": 5000}]
        result = select_forecast_vintage(delivery, forecasts, 16, 0)
        assert result["status"] == "available"


class TestBuildAnalysisTable:
    def test_basic(self):
        actuals = [
            {"start_time_utc": dt("2026-01-10T12:00:00"), "generation": 5000.0},
        ]
        forecasts = [
            {"start_time_utc": dt("2026-01-10T12:00:00"), "publish_time_utc": dt("2026-01-09T14:00:00"), "generation": 5200.0},
        ]
        df = build_analysis_table(actuals, forecasts)
        assert len(df) == 1
        assert df.iloc[0]["signed_error"] == pytest.approx(200.0)
        assert df.iloc[0]["abs_error"] == pytest.approx(200.0)
        assert df.iloc[0]["forecast_status"] == "available"

    def test_missing_forecast(self):
        actuals = [{"start_time_utc": dt("2026-01-10T12:00:00"), "generation": 5000.0}]
        df = build_analysis_table(actuals, [])
        assert df.iloc[0]["forecast_status"] == "unavailable"
        assert df.iloc[0]["signed_error"] is None or str(df.iloc[0]["signed_error"]) == "None"

    def test_negative_actual_flagged(self):
        actuals = [{"start_time_utc": dt("2026-01-10T12:00:00"), "generation": -100.0}]
        df = build_analysis_table(actuals, [])
        flag = df.iloc[0]["data_quality_flag"]
        assert flag is not None and "negative_actual" in str(flag)

    def test_error_convention_overforecast(self):
        actuals = [{"start_time_utc": dt("2026-01-10T12:00:00"), "generation": 4000.0}]
        forecasts = [{"start_time_utc": dt("2026-01-10T12:00:00"), "publish_time_utc": dt("2026-01-09T14:00:00"), "generation": 5000.0}]
        df = build_analysis_table(actuals, forecasts)
        # forecast > actual → positive signed_error
        assert df.iloc[0]["signed_error"] > 0

    def test_error_convention_underforecast(self):
        actuals = [{"start_time_utc": dt("2026-01-10T12:00:00"), "generation": 6000.0}]
        forecasts = [{"start_time_utc": dt("2026-01-10T12:00:00"), "publish_time_utc": dt("2026-01-09T14:00:00"), "generation": 5000.0}]
        df = build_analysis_table(actuals, forecasts)
        # forecast < actual → negative signed_error
        assert df.iloc[0]["signed_error"] < 0

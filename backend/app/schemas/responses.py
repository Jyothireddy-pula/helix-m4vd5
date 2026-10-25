"""Pydantic response schemas for all API endpoints."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    database: str


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class AnalysisPeriod(BaseModel):
    start: str
    end: str


class DecisionCutoffMeta(BaseModel):
    hour: int
    minute: int
    description: str


class DataSourcesMeta(BaseModel):
    actuals: str
    forecasts: str


class MetadataResponse(BaseModel):
    analysis_period: AnalysisPeriod
    unit: str
    timezone: str
    sources: DataSourcesMeta
    decision_cutoff_default: DecisionCutoffMeta
    error_convention: str


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class MetricsResponse(BaseModel):
    n: int = Field(description="Number of eligible intervals included in metrics")
    mae: Optional[float] = Field(None, description="Mean Absolute Error (MW)")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error (MW)")
    mean_bias: Optional[float] = Field(None, description="Mean Bias Error (MW); positive = overforecast")
    median_abs_error: Optional[float] = Field(None, description="Median Absolute Error (MW)")
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error (%); null when actuals contain zeros")
    wape: Optional[float] = Field(None, description="Weighted Absolute Percentage Error (%)")
    mean_actual: Optional[float] = Field(None, description="Mean actual wind generation (MW)")
    mean_forecast: Optional[float] = Field(None, description="Mean selected forecast (MW)")
    forecast_coverage_pct: Optional[float] = Field(None, description="% of intervals with an eligible forecast")
    overforecast_count: int = 0
    underforecast_count: int = 0
    exact_count: int = 0


# ---------------------------------------------------------------------------
# Timeseries
# ---------------------------------------------------------------------------

class TimeseriesPoint(BaseModel):
    delivery_start: str
    actual_generation: Optional[float]
    selected_forecast: Optional[float]
    forecast_publish_time: Optional[str]
    decision_cutoff: Optional[str]
    lead_time_hours: Optional[float]
    signed_error: Optional[float]
    abs_error: Optional[float]
    pct_error: Optional[float]
    forecast_status: str
    data_quality_flag: Optional[str]


class TimeseriesResponse(BaseModel):
    data: list[TimeseriesPoint]
    count: int


# ---------------------------------------------------------------------------
# Daily metrics
# ---------------------------------------------------------------------------

class DailyMetricsPoint(BaseModel):
    date: str
    n: int
    mae: Optional[float]
    rmse: Optional[float]
    mean_bias: Optional[float]
    forecast_coverage_pct: Optional[float]


class DailyMetricsResponse(BaseModel):
    data: list[DailyMetricsPoint]


# ---------------------------------------------------------------------------
# Lead-time metrics
# ---------------------------------------------------------------------------

class LeadTimeMetricsPoint(BaseModel):
    bin_label: str
    n: int
    mae: Optional[float]
    rmse: Optional[float]
    mean_bias: Optional[float]


class LeadTimeMetricsResponse(BaseModel):
    data: list[LeadTimeMetricsPoint]


# ---------------------------------------------------------------------------
# Forecast vintages
# ---------------------------------------------------------------------------

class VintageRecord(BaseModel):
    start_time_utc: str
    publish_time_utc: str
    generation: float
    eligible: bool
    decision_cutoff: str


class VintagesResponse(BaseModel):
    delivery_start: str
    actual_generation: Optional[float]
    decision_cutoff: str
    selected_forecast: Optional[float]
    selected_publish_time: Optional[str]
    lead_time_hours: Optional[float]
    signed_error: Optional[float]
    forecast_status: str
    vintages: list[VintageRecord]


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

class IngestionRunRecord(BaseModel):
    dataset: str
    status: str
    finished_at: str
    records_inserted: Optional[int]


class DataSourceInfo(BaseModel):
    dataset: str
    url: str
    unit: str


class DataQualityResponse(BaseModel):
    expected_intervals: int
    actual_intervals_retrieved: int
    forecast_records: int
    forecast_vintages: int
    missing_actual_intervals: int
    earliest_publish_time: Optional[str]
    latest_publish_time: Optional[str]
    last_ingestion_runs: list[IngestionRunRecord]
    timezone: str
    decision_cutoff_assumption: str


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class QualitySummary(BaseModel):
    actual_intervals: int
    expected_intervals: int
    forecast_records: int


class CutoffConfig(BaseModel):
    hour: int
    minute: int
    description: str


class DashboardResponse(BaseModel):
    metrics: MetricsResponse
    quality_summary: QualitySummary
    cutoff_config: CutoffConfig

export interface Metrics {
  total_intervals: number
  n_with_forecast: number
  n_without_forecast: number
  forecast_coverage_pct: number
  mae: number | null
  rmse: number | null
  mean_bias_error: number | null
  median_abs_error: number | null
  mape: number | null
  wape: number | null
  mean_actual: number | null
  mean_forecast: number | null
  n_overforecast: number | null
  n_underforecast: number | null
  n_exact: number | null
  overforecast_pct: number | null
  underforecast_pct: number | null
}

export interface TimeseriesPoint {
  delivery_start: string
  actual_generation: number | null
  selected_forecast: number | null
  forecast_publish_time: string | null
  decision_cutoff: string | null
  lead_time_hours: number | null
  signed_error: number | null
  abs_error: number | null
  pct_error: number | null
  forecast_status: 'available' | 'unavailable'
  data_quality_flag: string | null
}

export interface DailyMetrics extends Metrics {
  date: string
}

export interface LeadTimeMetrics extends Metrics {
  lead_time_bucket: string
}

export interface Vintage {
  start_time_utc: string
  publish_time_utc: string
  generation: number
  eligible: boolean
  decision_cutoff: string
}

export interface VintageResponse {
  delivery_start: string
  actual_generation: number | null
  decision_cutoff: string
  selected_forecast: number | null
  selected_publish_time: string | null
  lead_time_hours: number | null
  signed_error: number | null
  forecast_status: 'available' | 'unavailable'
  vintages: Vintage[]
}

export interface DataQuality {
  expected_intervals: number
  actual_intervals_retrieved: number
  forecast_records: number
  forecast_vintages: number
  missing_actual_intervals: number
  earliest_publish_time: string | null
  latest_publish_time: string | null
  last_ingestion_runs: Array<{
    dataset: string
    status: string
    finished_at: string
    records_inserted: number
  }>
  sources: {
    actuals: { dataset: string; url: string; unit: string }
    forecasts: { dataset: string; url: string; unit: string }
  }
  timezone: string
  decision_cutoff_assumption: string
}

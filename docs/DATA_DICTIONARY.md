# Data Dictionary

## Source Datasets

### FUELHH (Actual Wind Generation)
Source: Elexon BMRS  
URL: https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream  
Filter applied: fuelType=WIND  
Resolution: half-hourly (30-minute intervals)

| Field | Type | Description |
|---|---|---|
| dataset | string | "FUELHH" |
| publishTime | ISO 8601 UTC | When this record became available |
| startTime | ISO 8601 UTC | Start of the half-hourly settlement period |
| settlementDate | date string | Settlement date (YYYY-MM-DD) |
| settlementPeriod | integer | Period number 1–48 (1 = 00:00–00:30 UTC) |
| fuelType | string | "WIND" (filtered) |
| generation | number | Actual wind generation in MW |

### WINDFOR (Wind Generation Forecast)
Source: Elexon BMRS  
URL: https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream  
Resolution: hourly delivery intervals

| Field | Type | Description |
|---|---|---|
| dataset | string | "WINDFOR" |
| publishTime | ISO 8601 UTC | When this forecast was published |
| startTime | ISO 8601 UTC | Target delivery interval (hourly) |
| generation | number | Forecasted wind generation in MW |

---

## Database Tables

### actual_generation
| Column | Type | Notes |
|---|---|---|
| id | integer | PK |
| start_time_utc | datetime with timezone | Delivery interval start |
| settlement_date | text | YYYY-MM-DD |
| settlement_period | integer | 1–48 |
| fuel_type | text | "WIND" |
| generation | float | MW |
| source_dataset | text | "FUELHH" |
| retrieved_at_utc | datetime | Ingestion timestamp |

Unique constraint: (settlement_date, settlement_period, fuel_type)

### wind_forecast
| Column | Type | Notes |
|---|---|---|
| id | integer | PK |
| start_time_utc | datetime with timezone | Target delivery interval |
| publish_time_utc | datetime with timezone | When forecast was published |
| generation | float | MW |
| source_dataset | text | "WINDFOR" |
| retrieved_at_utc | datetime | Ingestion timestamp |

Unique constraint: (start_time_utc, publish_time_utc)  
Note: multiple rows per start_time_utc (different vintages)

### ingestion_run
| Column | Type | Notes |
|---|---|---|
| id | integer | PK |
| dataset | text | "FUELHH" or "WINDFOR" |
| started_at | datetime | |
| finished_at | datetime | Nullable |
| status | text | running/success/failed |
| records_fetched | integer | API response count |
| records_inserted | integer | New rows added |
| records_updated | integer | Existing rows updated |
| error_summary | text | Nullable; error message if failed |

---

## Analysis Table (computed, not persisted)

| Column | Description |
|---|---|
| delivery_start | UTC datetime of the half-hourly interval |
| actual_generation | Actual wind MW (null if missing) |
| selected_forecast | Day-ahead forecast MW at cutoff (null if unavailable) |
| forecast_publish_time | UTC publish time of the selected forecast |
| decision_cutoff | The cutoff datetime used for this interval |
| lead_time_hours | Hours from publish to delivery |
| signed_error | forecast − actual (null if either missing) |
| abs_error | |signed_error| |
| squared_error | signed_error² |
| pct_error | 100 × signed_error / actual (null if actual = 0) |
| forecast_status | "available" or "unavailable" |
| data_quality_flag | Pipe-separated flags: missing_actual, negative_actual, etc. |

---

## Units

All generation values are in **megawatts (MW)** as returned by Elexon BMRS.  
All timestamps are **UTC**.  
Analysis period: **2026-01-01 00:00 UTC to 2026-01-31 23:30 UTC** inclusive (1,488 half-hourly intervals).

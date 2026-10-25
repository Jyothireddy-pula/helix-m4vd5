# Validation Report

## Backend Unit Tests

Run with: `cd backend && pytest -v`

### Test Files
- `app/tests/test_forecast_selection.py` — 9 tests covering:
  - Decision cutoff calculation (basic, midnight boundary, end-of-day)
  - Vintage selection (latest eligible, excludes after cutoff, no eligible, empty, identical timestamps, lead time, exact boundary)
  - Analysis table build (basic, missing forecast, negative actual flag, error convention)

- `app/tests/test_metrics.py` — 9 tests covering:
  - Empty dataset
  - MAE, RMSE calculation
  - Mean bias (positive = overforecast, negative = underforecast)
  - Forecast coverage
  - Zero-actual MAPE guard
  - WAPE denominator
  - Directional counts

### Expected Outcome
All 18 tests should pass. Tests use deterministic fixtures with manually verified expected values.

## API Verification

### Elexon FUELHH Schema (verified by direct API call)
```json
{"dataset":"FUELHH","publishTime":"2026-01-02T00:00:00Z","startTime":"2026-01-01T23:30:00Z",
 "settlementDate":"2026-01-01","settlementPeriod":48,"fuelType":"WIND","generation":15538}
```
- Field `generation` is numeric MW ✅
- `fuelType=WIND` filter works via `settlementDateFrom/To` parameters ✅

### Elexon WINDFOR Schema (verified by direct API call)
```json
{"dataset":"WINDFOR","publishTime":"2026-01-01T22:30:00Z","startTime":"2026-01-01T00:00:00Z","generation":19960}
```
- Historical vintages retrievable via `publishDateTimeFrom/To` ✅
- Resolution is **hourly** (not half-hourly) — documented ✅

## Data Coverage (after ingestion)

Verify with: `GET /api/v1/quality`

Expected:
- `expected_intervals`: 1488 (31 × 48)
- `actual_intervals_retrieved`: should be close to 1488
- `forecast_records`: varies by number of vintages; typically several thousand
- `forecast_vintages`: number of distinct publish times

## Frontend Build

Run: `cd frontend && npm run build`
Expected: `dist/` directory created, no TypeScript errors.

## Docker Build

Run: `docker-compose build`
Expected: both images build successfully without errors.

## Known Issues / Limitations

1. **WINDFOR hourly vs FUELHH half-hourly**: Forecasts are matched to both :00 and :30 actual intervals. If the API changes resolution this may need updating.

2. **API rate limits**: Large publish-time windows may trigger 429 responses. The client handles these with Retry-After but ingestion may be slow.

3. **SQLite concurrency**: SQLite is single-writer; concurrent API requests work fine for reads but ingestion should run separately from serving.

4. **Timestamp parsing**: All timestamps must be UTC-aware. The code ensures this but if Elexon ever returns naive timestamps, parsing will need updating.

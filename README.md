# Wind Forecast Intelligence

**UK National Wind Generation Forecast Accuracy Analytics — January 2026**

A production-quality full-stack web application for a UK electricity utility trading team. It answers two questions:

1. **What was the latest available wind generation forecast** when a day-ahead purchasing decision needed to be made?
2. **How accurate were those forecasts** compared with actual wind generation?

---

## Business Problem

Wind generation is weather-dependent. UK electricity traders buy power in the day-ahead wholesale market, typically one day before delivery. To do that effectively, they need to understand:

- What the published wind forecast was at the time of their purchasing decision
- How far off that forecast turned out to be — and in which direction

This application analyses January 2026 historical data from Elexon BMRS, reconstructing the forecast that was available at a configurable day-ahead decision cutoff, and quantifying forecast accuracy using standard meteorological and energy metrics.

---

## Features

- **Overview dashboard** — MAE, RMSE, mean bias, forecast coverage, mean actual vs forecast generation
- **Actual vs forecast chart** — half-hourly time series for January 2026
- **Error analysis** — signed error time series, directional breakdown, daily MAE chart
- **Forecast vintage explorer** — select any delivery interval and see all available forecast vintages, which was eligible at the decision cutoff, and why
- **Configurable decision cutoff** — change the assumed cutoff time and all analysis updates instantly
- **Data quality page** — coverage, provenance, ingestion history, metric definitions
- **Searchable data table** — all 1,488 half-hourly intervals with sorting, pagination, and CSV export

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React Frontend (Vite + TypeScript + Tailwind + Recharts)│
│  Dashboard | Vintage Explorer | Data Table | Quality     │
└──────────────┬──────────────────────────────────────────┘
               │ HTTP / REST API (/api/v1/*)
┌──────────────▼──────────────────────────────────────────┐
│  FastAPI Backend (Python 3.12)                           │
│  Routes → Analysis Service → Forecast Selection →       │
│  Metrics Engine → SQLAlchemy ORM                        │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│  SQLite (local dev) / PostgreSQL (production)            │
│  Tables: actual_generation, wind_forecast, ingestion_run │
└─────────────────────────────────────────────────────────┘
               ↑ ingestion
┌─────────────────────────────────────────────────────────┐
│  Elexon BMRS Public API (no auth required)              │
│  FUELHH (actual wind)  · WINDFOR (wind forecasts)       │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Router |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2, Pydantic v2 |
| Database | SQLite (dev), PostgreSQL (prod) |
| HTTP client | httpx + tenacity (retries, backoff) |
| Analysis | pandas, numpy |
| Testing | pytest, pytest-asyncio, vitest |
| Deployment | Docker, docker-compose |

---

## Repository Structure

```
helix-m4vd/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes.py        — FastAPI endpoints
│   │   ├── core/config.py          — Settings (env-based)
│   │   ├── db/database.py          — SQLAlchemy engine
│   │   ├── models/                 — ORM models
│   │   ├── services/
│   │   │   ├── elexon_client.py    — Elexon API client
│   │   │   ├── ingestion.py        — Historical data ingestion
│   │   │   ├── forecast_selection.py — Vintage selection logic
│   │   │   ├── metrics.py          — MAE, RMSE, bias, WAPE…
│   │   │   └── analysis.py         — Main analysis orchestration
│   │   ├── tests/
│   │   │   ├── test_forecast_selection.py
│   │   │   └── test_metrics.py
│   │   └── main.py                 — App entry point
│   ├── ingest.py                   — CLI ingestion script
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                  — Dashboard, VintageExplorer, DataTable, DataQuality
│   │   ├── components/             — KpiCard, CutoffSelector, LoadingState
│   │   ├── services/api.ts         — API client
│   │   ├── hooks/useApi.ts         — Data-fetching hook
│   │   └── types/api.ts            — TypeScript interfaces
│   ├── Dockerfile
│   └── nginx.conf
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── VALIDATION_REPORT.md
│   ├── DEMO_SCRIPT.md
│   └── SUBMISSION_CHECKLIST.md
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## Data Sources

### Actual Generation — FUELHH
- **Endpoint**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream`
- **Filter**: `fuelType=WIND`, `settlementDateFrom`, `settlementDateTo`
- **Key fields**: `startTime` (UTC), `settlementDate`, `settlementPeriod`, `generation` (MW)
- **Resolution**: half-hourly (48 periods per day)

### Wind Forecasts — WINDFOR
- **Endpoint**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream`
- **Filter**: `publishDateTimeFrom`, `publishDateTimeTo` (for historical vintages)
- **Key fields**: `startTime` (UTC delivery interval), `publishTime` (UTC), `generation` (MW)
- **Resolution**: hourly forecast delivery intervals (matched to half-hourly actuals)

**Official documentation**: https://bmrs.elexon.co.uk/api-documentation

---

## Forecast Vintage Selection Logic

This is the most critical part of the application. It prevents data leakage (using future information).

For each delivery interval **T** with decision cutoff **C** (default: 16:00 UTC on the calendar day before delivery):

1. Find all WINDFOR records where `startTime == T`
2. Keep only records where `publishTime ≤ C`
3. Select the record with the **latest** eligible `publishTime`
4. If no eligible record exists, mark the interval as `unavailable`
5. Calculate lead time = T − selected publishTime (hours)

**Decision cutoff assumption**: 16:00 UTC on the calendar day before delivery is used as a default. This is an **analytical assumption**, not an official Elexon or market rule. It can be changed in the UI via the cutoff selector, and the result updates immediately.

---

## Metric Definitions

**Error convention**: `signed_error = forecast − actual`
- Positive → forecast overestimated wind generation
- Negative → forecast underestimated wind generation

| Metric | Definition |
|---|---|
| MAE | Mean of \|forecast − actual\| across eligible intervals |
| RMSE | √(mean of (forecast − actual)²); penalises larger errors more |
| Mean Bias Error | Mean of signed errors; positive = systematic overforecast |
| Median Absolute Error | Median of \|forecast − actual\| |
| WAPE | sum(\|error\|) / sum(\|actual\|) × 100; only when sum(actual) > 0 |
| MAPE | Mean of \|error / actual\| × 100; only for non-zero actuals |
| Forecast Coverage | % of intervals with an eligible vintage at the cutoff |

All metrics use the **same set of comparable intervals** (those with both an actual and a selected forecast).

---

## Local Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- pip

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Copy the example env file:
```bash
cp ../.env.example .env
```

Initialize the database and ingest data:
```bash
python ingest.py --dataset all
```

Start the backend:
```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

---

## Docker Setup

Build and start everything:
```bash
docker-compose up --build
```

Frontend: http://localhost:3000  
Backend API: http://localhost:8000  
API docs: http://localhost:8000/docs

Run ingestion inside Docker:
```bash
docker-compose exec backend python ingest.py --dataset all
```

---

## Data Ingestion

The ingestion script fetches January 2026 data from the Elexon BMRS API.

```bash
# Ingest everything (actuals + forecasts)
python ingest.py --dataset all

# Ingest only actuals
python ingest.py --dataset FUELHH

# Ingest only forecasts (may take several minutes due to API volume)
python ingest.py --dataset WINDFOR
```

Running ingestion twice is **safe** — duplicate records are detected and skipped. The script logs progress per day/chunk.

**WINDFOR ingestion note**: Forecast vintages are fetched by `publishDateTimeFrom/To` in 3-day chunks from Dec 31, 2025 through Jan 31, 2026, capturing all day-ahead vintages. This requires ~20 API requests and may take 2–5 minutes.

---

## Running Tests

```bash
cd backend
pytest
```

Expected output: all unit tests pass, covering forecast vintage selection, metric calculations, and edge cases.

```bash
cd frontend
npm run test
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/metadata` | Analysis config and source info |
| GET | `/api/v1/dashboard` | KPI metrics + quality summary |
| GET | `/api/v1/analysis/timeseries` | Half-hourly aligned actuals, forecasts, errors |
| GET | `/api/v1/analysis/metrics` | All quantitative metrics |
| GET | `/api/v1/analysis/daily` | Per-day metrics |
| GET | `/api/v1/analysis/lead-times` | Lead-time group metrics |
| GET | `/api/v1/forecasts/vintages` | All vintages for a delivery interval |
| GET | `/api/v1/quality` | Data quality summary |
| GET | `/api/v1/analysis/export.csv` | CSV export |
| POST | `/api/v1/ingestion/run` | Trigger ingestion (optional secret) |

Query parameters `cutoff_hour` (0–23) and `cutoff_minute` (0–59) control the decision cutoff for all analysis endpoints.

---

## Known Limitations

1. **WINDFOR hourly resolution**: WINDFOR publishes hourly forecasts; FUELHH actuals are half-hourly. The application matches forecasts to both half-hours within each hour (e.g., a forecast for 12:00 matches actual intervals at 12:00 and 12:30). This is documented in the code and UI.

2. **Forecast vintage coverage**: The number of distinct WINDFOR vintages available for January 2026 depends on what Elexon's API returns. Some intervals near the start of January may have limited vintages if the publish-time window doesn't capture all historical forecasts.

3. **SQLite for development**: The default SQLite database is suitable for local development and Docker. For a durable production deployment, use PostgreSQL and set `DATABASE_URL` accordingly.

4. **No real-time data**: The application is a historical analysis of January 2026 only. The system date is later but the analysis period is fixed.

---

## Deployment

### Recommended Production Architecture

- **Frontend**: Deploy `frontend/dist/` to Vercel, Netlify, or any static host
- **Backend**: Deploy to Railway, Render, Fly.io, or Heroku (Python support)
- **Database**: Managed PostgreSQL (Railway, Render, Supabase, Heroku Postgres)

### Environment Variables (Backend)

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLAlchemy async database URL |
| `DATABASE_URL_SYNC` | SQLAlchemy sync database URL (for migrations) |
| `CORS_ORIGINS` | JSON list of allowed frontend origins |
| `INGESTION_SECRET` | Optional secret for the ingestion endpoint |

### Deployment Steps

1. Provision PostgreSQL database
2. Set `DATABASE_URL` and `DATABASE_URL_SYNC` environment variables
3. Deploy backend; it will run `init_db()` on startup
4. Run ingestion: `python ingest.py --dataset all`
5. Deploy frontend with `VITE_API_URL` set to backend URL
6. Verify health: `GET /api/v1/health`

---

## AI Tools Used

This project was developed with the assistance of **Claude** (Anthropic), an AI coding assistant. Claude assisted with:

- Full-stack application architecture and scaffolding
- FastAPI route design and SQLAlchemy model implementation
- Forecast vintage selection algorithm design
- Metric calculation implementation
- React component development
- Docker configuration
- Test suite structure

All code was reviewed and the analytical logic — particularly the forecast selection and error convention — was verified against the challenge specification. The Elexon API schema was independently verified by direct API calls before implementing field mappings.

---

## Links

- Elexon BMRS API documentation: https://bmrs.elexon.co.uk/api-documentation
- FUELHH stream: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- WINDFOR stream: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream

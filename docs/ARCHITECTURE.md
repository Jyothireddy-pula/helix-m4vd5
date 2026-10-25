# Architecture

## System Overview

```
User Browser
    │
    ▼
┌─────────────────────────────────────────┐
│ React SPA (Vite + TypeScript)           │
│ Pages: Dashboard, Vintage Explorer,     │
│        Data Table, Data Quality         │
│ Components: KpiCard, CutoffSelector,   │
│             Charts (Recharts)           │
└────────────┬────────────────────────────┘
             │ HTTP GET /api/v1/*
             ▼
┌─────────────────────────────────────────┐
│ FastAPI Backend                         │
│ routes.py → analysis.py                │
│           → forecast_selection.py       │
│           → metrics.py                 │
│           → elexon_client.py           │
└────────────┬────────────────────────────┘
             │ SQLAlchemy async
             ▼
┌─────────────────────────────────────────┐
│ SQLite (dev) / PostgreSQL (prod)        │
│ actual_generation                       │
│ wind_forecast                           │
│ ingestion_run                           │
└─────────────────────────────────────────┘
             ↑ ingest.py (one-time / on-demand)
┌─────────────────────────────────────────┐
│ Elexon BMRS Public API                  │
│ FUELHH: actual wind generation          │
│ WINDFOR: wind forecast vintages         │
└─────────────────────────────────────────┘
```

## Data Flow

1. **Ingestion** (one-time): `ingest.py` fetches 31 days of FUELHH actuals + ~60 days of WINDFOR publishes, upserts to DB
2. **Analysis request**: Frontend sends GET with `cutoff_hour/cutoff_minute` params
3. **Backend**: loads actuals + forecasts from DB, runs `build_analysis_table()`, computes metrics
4. **Response**: JSON with aligned data, metrics, quality summary

## Decision Cutoff Logic

```
For each delivery interval T:
  cutoff C = T.date - 1 day, at hour:minute UTC
  eligible = [f for f in forecasts(T) if f.publishTime ≤ C]
  selected = max(eligible, key=publishTime)
  if not eligible: status = "unavailable"
```

## Production Deployment

```
Vercel (static)          Railway/Render (API)      Railway Postgres
  └─ frontend/dist/   →  └─ FastAPI :8000   →   └─ PostgreSQL DB
```

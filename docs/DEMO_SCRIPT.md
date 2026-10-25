# Demo Script — Wind Forecast Intelligence

## Video Structure (max 10 minutes)

---

## Part 1: Customer Presentation (0:00–5:00)

### 0:00–0:30 — Business Problem
> "UK electricity traders buy power in the day-ahead wholesale market — typically making decisions by around 16:00 the day before delivery.
> Wind generation is weather-dependent, so the quality of the forecast they had at that moment directly affects how well-prepared they are.
> This application answers two questions: what forecast was available when the decision was made, and how accurate was it?"

### 0:30–1:15 — Data Sources
> "We're using two Elexon BMRS datasets — publicly available, no API key required.
> FUELHH gives us actual half-hourly wind generation.
> WINDFOR gives us the published wind generation forecasts, including the exact time each forecast was published.
> Our analysis covers all 1,488 half-hourly intervals in January 2026."

*Show the Data Quality page. Point to coverage numbers, source links, last ingestion.*

### 1:15–2:15 — Main Dashboard
> "Here's the main dashboard. At the top we have key metrics across the full month.
> MAE tells us the average error in MW.
> RMSE penalises larger errors more.
> Mean Bias Error tells us whether forecasts systematically ran high or low.
> Forecast coverage shows what percentage of intervals had an eligible forecast at the decision cutoff."

*Point to each KPI card. Show the actual vs forecast chart. Highlight any visible periods of large deviation.*

### 2:15–3:15 — Forecast Accuracy
> "MAE of [X] MW means on average, the day-ahead forecast was off by that amount.
> The mean bias of [±X] MW suggests forecasts were [slightly over/under]-estimating wind generation.
> The signed error chart shows this isn't uniform — some days had much larger errors than others.
> That's where the daily MAE chart is useful: it helps traders see which days were particularly hard to forecast."

*Scroll to daily MAE bar chart. Point out days with high error.*

### 3:15–4:15 — Vintage Explorer
> "This is the most important feature for understanding the forecasting process.
> I'll select January 15th at 12:00 UTC as the delivery interval.
> You can see all the forecast vintages published for that interval — each one published at a different time.
> The ones in green were published before the 16:00 day-ahead cutoff. The selected forecast — highlighted in amber — is the latest eligible one."

*Show the Vintage Explorer. Demonstrate a few different delivery intervals.*

### 4:15–5:00 — Summary
> "This tells the trading team: at the moment of their purchasing decision, this was the forecast they had.
> They can also change the assumed cutoff — maybe they want to see what was available at noon instead of 4pm — and the entire analysis updates instantly.
> The application helps them understand not just the average error, but the specific forecasts they were working with on each day."

---

## Part 2: Technical Review (5:00–10:00)

### 5:00–5:45 — Architecture
> "The architecture is a React frontend, FastAPI Python backend, and SQLite database — PostgreSQL for production.
> Everything runs in Docker. The frontend proxies API calls to the backend."

*Show the repository structure. Point out key directories.*

### 5:45–6:30 — Elexon API Integration
> "The Elexon client uses httpx with explicit timeouts and tenacity for retries with exponential backoff.
> It handles HTTP 429 rate limits with Retry-After.
> For actuals, we fetch by settlementDate. For forecasts, we fetch by publishDateTimeFrom/To to get historical vintages.
> Ingestion chunks WINDFOR into 3-day windows to stay within API limits."

*Show elexon_client.py and ingestion.py.*

### 6:30–7:30 — Forecast Vintage Selection
> "This is the critical piece for preventing data leakage.
> compute_decision_cutoff returns 16:00 UTC on the day before delivery — configurable.
> select_forecast_vintage filters to eligible forecasts (publishTime ≤ cutoff) and picks the latest one.
> build_analysis_table applies this to all 1,488 intervals and calculates all error fields."

*Show forecast_selection.py. Show the unit tests.*

### 7:30–8:30 — Metrics and Validation
> "Metrics are calculated in metrics.py with guard clauses — we never divide by zero.
> MAPE is only calculated for non-zero actuals.
> WAPE is only calculated when the sum of actuals is positive.
> All metrics are over the same set of intervals."

*Show test_metrics.py. Run pytest briefly.*

### 8:30–9:15 — Tests and Docker
> "The test suite covers forecast selection edge cases, metric calculations, and error conventions.
> The Docker setup is a multi-stage build — separate containers for frontend and backend.
> The frontend container uses nginx to serve the React build and proxy API calls."

*Show Docker files. Show a passing pytest run.*

### 9:15–10:00 — Deployment and Limitations
> "The app is configured for deployment to any Python host (Railway, Render, Fly.io) for the backend,
> and Vercel or similar for the frontend static build.
> Known limitations: WINDFOR is hourly but actuals are half-hourly — we match both half-hours to the hour forecast.
> The 16:00 cutoff is an analytical assumption, not an official market rule — the UI makes this explicit."

*Show the README limitations section.*

---

## Pre-Recording Checklist

- [ ] Backend running locally at :8000
- [ ] Data ingested (python ingest.py --dataset all)
- [ ] Frontend running locally at :5173
- [ ] Dashboard showing real data (not empty state)
- [ ] Vintage explorer tested with Jan 15 12:00 UTC
- [ ] Browser zoom set to readable size
- [ ] Screen recording tool ready
- [ ] Script reviewed once
- [ ] Total runtime under 10 minutes

"""FastAPI route handlers for Wind Forecast Intelligence API."""
import io
import csv
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.services.analysis import run_analysis, get_data_quality, get_vintages_for_interval
from app.services.metrics import compute_metrics, compute_daily_metrics, compute_lead_time_metrics

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)
UTC = timezone.utc


def _parse_dt(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database": "ok" if db_ok else "unavailable"}


@router.get("/metadata")
async def metadata():
    return {
        "analysis_period": {"start": "2026-01-01T00:00:00Z", "end": "2026-01-31T23:30:00Z"},
        "unit": "MW",
        "timezone": "UTC",
        "sources": {
            "actuals": "Elexon BMRS FUELHH (fuelType=WIND)",
            "forecasts": "Elexon BMRS WINDFOR",
        },
        "decision_cutoff_default": {
            "hour": settings.DEFAULT_DECISION_CUTOFF_HOUR,
            "minute": settings.DEFAULT_DECISION_CUTOFF_MINUTE,
            "description": "16:00 UTC on the calendar day before delivery — analytical assumption, not an official market deadline",
        },
        "error_convention": "signed_error = forecast - actual; positive = overforecast",
        "docs": {
            "FUELHH": "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream",
            "WINDFOR": "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream",
        },
    }


@router.get("/dashboard")
async def dashboard(
    cutoff_hour: int = Query(16, ge=0, le=23),
    cutoff_minute: int = Query(0, ge=0, le=59),
    db: AsyncSession = Depends(get_db),
):
    df = await run_analysis(db, cutoff_hour, cutoff_minute)
    metrics = compute_metrics(df)
    quality = await get_data_quality(db)
    return {
        "metrics": metrics,
        "quality_summary": {
            "actual_intervals": quality["actual_intervals_retrieved"],
            "expected_intervals": quality["expected_intervals"],
            "forecast_records": quality["forecast_records"],
        },
        "cutoff_config": {
            "hour": cutoff_hour,
            "minute": cutoff_minute,
            "description": f"{cutoff_hour:02d}:{cutoff_minute:02d} UTC on day-1 (analytical assumption)",
        },
    }


@router.get("/analysis/timeseries")
async def timeseries(
    cutoff_hour: int = Query(16, ge=0, le=23),
    cutoff_minute: int = Query(0, ge=0, le=59),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    s = _parse_dt(start) if start else datetime(2026, 1, 1, tzinfo=UTC)
    e = _parse_dt(end) if end else datetime(2026, 2, 1, tzinfo=UTC)
    df = await run_analysis(db, cutoff_hour, cutoff_minute, s, e)
    if df.empty:
        return {"data": [], "count": 0}

    records = []
    for _, row in df.iterrows():
        records.append({
            "delivery_start": row["delivery_start"].isoformat() if hasattr(row["delivery_start"], "isoformat") else str(row["delivery_start"]),
            "actual_generation": row["actual_generation"],
            "selected_forecast": row["selected_forecast"],
            "forecast_publish_time": row["forecast_publish_time"].isoformat() if row["forecast_publish_time"] is not None and hasattr(row["forecast_publish_time"], "isoformat") else None,
            "decision_cutoff": row["decision_cutoff"].isoformat() if row["decision_cutoff"] is not None and hasattr(row["decision_cutoff"], "isoformat") else None,
            "lead_time_hours": row["lead_time_hours"],
            "signed_error": row["signed_error"],
            "abs_error": row["abs_error"],
            "pct_error": row["pct_error"],
            "forecast_status": row["forecast_status"],
            "data_quality_flag": row["data_quality_flag"],
        })
    return {"data": records, "count": len(records)}


@router.get("/analysis/metrics")
async def analysis_metrics(
    cutoff_hour: int = Query(16, ge=0, le=23),
    cutoff_minute: int = Query(0, ge=0, le=59),
    db: AsyncSession = Depends(get_db),
):
    df = await run_analysis(db, cutoff_hour, cutoff_minute)
    return compute_metrics(df)


@router.get("/analysis/daily")
async def daily_metrics(
    cutoff_hour: int = Query(16, ge=0, le=23),
    cutoff_minute: int = Query(0, ge=0, le=59),
    db: AsyncSession = Depends(get_db),
):
    df = await run_analysis(db, cutoff_hour, cutoff_minute)
    return compute_daily_metrics(df)


@router.get("/analysis/lead-times")
async def lead_time_metrics(
    cutoff_hour: int = Query(16, ge=0, le=23),
    cutoff_minute: int = Query(0, ge=0, le=59),
    db: AsyncSession = Depends(get_db),
):
    df = await run_analysis(db, cutoff_hour, cutoff_minute)
    return compute_lead_time_metrics(df)


@router.get("/forecasts/vintages")
async def forecast_vintages(
    delivery_start: str = Query(..., description="ISO timestamp of delivery interval"),
    cutoff_hour: int = Query(16, ge=0, le=23),
    cutoff_minute: int = Query(0, ge=0, le=59),
    db: AsyncSession = Depends(get_db),
):
    from app.services.forecast_selection import compute_decision_cutoff, select_forecast_vintage

    try:
        dt = _parse_dt(delivery_start)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid delivery_start timestamp")

    vintages = await get_vintages_for_interval(db, dt)
    cutoff = compute_decision_cutoff(dt, cutoff_hour, cutoff_minute)

    # Get actual — DB stores strings like "2026-01-15 12:30:00.000000"
    from sqlalchemy import text
    dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    actual_result = await db.execute(
        text("SELECT generation FROM actual_generation WHERE start_time_utc LIKE :st AND fuel_type='WIND'"),
        {"st": dt_str + "%"},
    )
    actual_row = actual_result.fetchone()
    actual_gen = actual_row[0] if actual_row else None

    # Annotate vintages with eligibility
    annotated = []
    for v in vintages:
        pt = datetime.fromisoformat(v["publish_time_utc"])
        eligible = pt <= cutoff
        annotated.append({**v, "eligible": eligible, "decision_cutoff": cutoff.isoformat()})

    # Compute selected
    candidates = [
        {"start_time_utc": dt, "publish_time_utc": datetime.fromisoformat(v["publish_time_utc"]), "generation": v["generation"]}
        for v in vintages
    ]
    sel = select_forecast_vintage(dt, candidates, cutoff_hour, cutoff_minute)

    signed_error = None
    if actual_gen is not None and sel["selected_generation"] is not None:
        signed_error = round(sel["selected_generation"] - actual_gen, 2)

    return {
        "delivery_start": dt.isoformat(),
        "actual_generation": actual_gen,
        "decision_cutoff": cutoff.isoformat(),
        "selected_forecast": sel["selected_generation"],
        "selected_publish_time": sel["publish_time_utc"].isoformat() if sel["publish_time_utc"] else None,
        "lead_time_hours": sel["lead_time_hours"],
        "signed_error": signed_error,
        "forecast_status": sel["status"],
        "vintages": annotated,
    }


@router.get("/quality")
async def data_quality(db: AsyncSession = Depends(get_db)):
    return await get_data_quality(db)


@router.get("/analysis/export.csv")
async def export_csv(
    cutoff_hour: int = Query(16, ge=0, le=23),
    cutoff_minute: int = Query(0, ge=0, le=59),
    db: AsyncSession = Depends(get_db),
):
    df = await run_analysis(db, cutoff_hour, cutoff_minute)
    if df.empty:
        raise HTTPException(status_code=404, detail="No analysis data available")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "# Wind Forecast Intelligence - Analysis Export",
        f"Decision Cutoff: {cutoff_hour:02d}:{cutoff_minute:02d} UTC (day-1, analytical assumption)",
        "Unit: MW",
        "Error convention: signed_error = forecast - actual",
        "Source: Elexon BMRS FUELHH (actuals) + WINDFOR (forecasts)",
    ])
    writer.writerow([
        "delivery_start_utc", "actual_generation_mw", "selected_forecast_mw",
        "forecast_publish_time_utc", "decision_cutoff_utc", "lead_time_hours",
        "signed_error_mw", "abs_error_mw", "pct_error", "forecast_status", "data_quality_flag",
    ])
    for _, row in df.iterrows():
        writer.writerow([
            row["delivery_start"].isoformat() if hasattr(row["delivery_start"], "isoformat") else row["delivery_start"],
            row["actual_generation"],
            row["selected_forecast"],
            row["forecast_publish_time"].isoformat() if row["forecast_publish_time"] is not None and hasattr(row["forecast_publish_time"], "isoformat") else "",
            row["decision_cutoff"].isoformat() if row["decision_cutoff"] is not None and hasattr(row["decision_cutoff"], "isoformat") else "",
            row["lead_time_hours"],
            row["signed_error"],
            row["abs_error"],
            row["pct_error"],
            row["forecast_status"],
            row["data_quality_flag"] or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=wind_forecast_analysis.csv"},
    )


@router.post("/ingestion/run")
async def trigger_ingestion(
    dataset: str = Query(..., description="'FUELHH' or 'WINDFOR' or 'all'"),
    secret: Optional[str] = Query(None),
):
    if settings.INGESTION_SECRET and secret != settings.INGESTION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid ingestion secret")

    from app.services.ingestion import ingest_actuals, ingest_forecasts
    import asyncio

    results = {}
    if dataset in ("FUELHH", "all"):
        results["FUELHH"] = await ingest_actuals()
    if dataset in ("WINDFOR", "all"):
        results["WINDFOR"] = await ingest_forecasts()
    return results

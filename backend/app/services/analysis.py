"""Main analysis service: loads data from DB and runs analysis."""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.forecast_selection import build_analysis_table
from app.services.metrics import compute_metrics, compute_daily_metrics, compute_lead_time_metrics

logger = logging.getLogger(__name__)
UTC = timezone.utc


async def load_actuals(session: AsyncSession, start: datetime, end: datetime) -> list[dict]:
    result = await session.execute(
        text(
            "SELECT start_time_utc, settlement_date, settlement_period, generation "
            "FROM actual_generation "
            "WHERE start_time_utc >= :start AND start_time_utc < :end "
            "AND fuel_type='WIND' ORDER BY start_time_utc"
        ),
        {"start": start, "end": end},
    )
    rows = result.fetchall()
    return [
        {
            "start_time_utc": datetime.fromisoformat(str(r[0])).replace(tzinfo=UTC)
            if isinstance(r[0], str) else r[0].replace(tzinfo=UTC) if r[0].tzinfo is None else r[0],
            "settlement_date": r[1],
            "settlement_period": r[2],
            "generation": r[3],
        }
        for r in rows
    ]


async def load_forecasts(session: AsyncSession, start: datetime, end: datetime) -> list[dict]:
    result = await session.execute(
        text(
            "SELECT start_time_utc, publish_time_utc, generation "
            "FROM wind_forecast "
            "WHERE start_time_utc >= :start AND start_time_utc < :end "
            "ORDER BY start_time_utc, publish_time_utc"
        ),
        {"start": start, "end": end},
    )
    rows = result.fetchall()
    out = []
    for r in rows:
        st = r[0]
        pt = r[1]
        if isinstance(st, str):
            st = datetime.fromisoformat(st)
        if isinstance(pt, str):
            pt = datetime.fromisoformat(pt)
        if st.tzinfo is None:
            st = st.replace(tzinfo=UTC)
        if pt.tzinfo is None:
            pt = pt.replace(tzinfo=UTC)
        out.append({"start_time_utc": st, "publish_time_utc": pt, "generation": r[2]})
    return out


async def run_analysis(
    session: AsyncSession,
    cutoff_hour: int = 16,
    cutoff_minute: int = 0,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
):
    """Run full analysis and return structured results."""
    start = start or datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
    end = end or datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)

    actuals = await load_actuals(session, start, end)
    forecasts = await load_forecasts(session, start, end)

    logger.info("Analysis: %d actuals, %d forecast vintages", len(actuals), len(forecasts))

    df = build_analysis_table(actuals, forecasts, cutoff_hour, cutoff_minute)
    return df


async def get_vintages_for_interval(
    session: AsyncSession,
    delivery_start: datetime,
) -> list[dict]:
    """Return all forecast vintages for a single delivery interval."""
    # Match on the hour (WINDFOR is hourly); use LIKE to match SQLite string format
    hour_start = delivery_start.replace(minute=0, second=0, microsecond=0, tzinfo=None)
    st_prefix = hour_start.strftime("%Y-%m-%d %H:%M:%S")
    result = await session.execute(
        text(
            "SELECT start_time_utc, publish_time_utc, generation "
            "FROM wind_forecast "
            "WHERE start_time_utc LIKE :st "
            "ORDER BY publish_time_utc"
        ),
        {"st": st_prefix + "%"},
    )
    rows = result.fetchall()
    out = []
    for r in rows:
        st = r[0]
        pt = r[1]
        if isinstance(st, str):
            st = datetime.fromisoformat(st)
        if isinstance(pt, str):
            pt = datetime.fromisoformat(pt)
        if st.tzinfo is None:
            st = st.replace(tzinfo=UTC)
        if pt.tzinfo is None:
            pt = pt.replace(tzinfo=UTC)
        out.append({"start_time_utc": st.isoformat(), "publish_time_utc": pt.isoformat(), "generation": r[2]})
    return out


async def get_data_quality(session: AsyncSession) -> dict:
    """Return data quality summary."""
    from datetime import date

    # Actuals
    a_result = await session.execute(
        text("SELECT COUNT(*) FROM actual_generation WHERE fuel_type='WIND' AND settlement_date >= '2026-01-01' AND settlement_date <= '2026-01-31'")
    )
    n_actuals = a_result.scalar() or 0

    # Forecasts
    f_result = await session.execute(
        text("SELECT COUNT(*), COUNT(DISTINCT publish_time_utc) FROM wind_forecast WHERE start_time_utc >= '2026-01-01' AND start_time_utc < '2026-02-01'")
    )
    f_row = f_result.fetchone()
    n_forecasts = f_row[0] if f_row else 0
    n_vintages = f_row[1] if f_row else 0

    # Last ingestion
    last_result = await session.execute(
        text("SELECT dataset, status, finished_at, records_inserted FROM ingestion_run ORDER BY id DESC LIMIT 5")
    )
    last_runs = [{"dataset": r[0], "status": r[1], "finished_at": str(r[2]), "records_inserted": r[3]} for r in last_result.fetchall()]

    # Min/max publish times
    pt_result = await session.execute(
        text("SELECT MIN(publish_time_utc), MAX(publish_time_utc) FROM wind_forecast WHERE start_time_utc >= '2026-01-01'")
    )
    pt_row = pt_result.fetchone()

    return {
        "expected_intervals": 31 * 48,  # Jan 2026
        "actual_intervals_retrieved": n_actuals,
        "forecast_records": n_forecasts,
        "forecast_vintages": n_vintages,
        "missing_actual_intervals": max(0, 31 * 48 - n_actuals),
        "earliest_publish_time": str(pt_row[0]) if pt_row and pt_row[0] else None,
        "latest_publish_time": str(pt_row[1]) if pt_row and pt_row[1] else None,
        "last_ingestion_runs": last_runs,
        "sources": {
            "actuals": {"dataset": "FUELHH", "url": "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream", "unit": "MW"},
            "forecasts": {"dataset": "WINDFOR", "url": "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream", "unit": "MW"},
        },
        "timezone": "UTC",
        "decision_cutoff_assumption": "16:00 UTC on the calendar day before delivery (analytical assumption, not an official market deadline)",
    }

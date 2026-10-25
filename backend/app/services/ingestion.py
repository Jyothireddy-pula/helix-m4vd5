"""Historical data ingestion for January 2026."""
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.models.actual_generation import ActualGeneration
from app.models.ingestion_run import IngestionRun
from app.models.wind_forecast import WindForecast
from app.services.elexon_client import ElexonClient

logger = logging.getLogger(__name__)

UTC = timezone.utc
ANALYSIS_START = date(2026, 1, 1)
ANALYSIS_END = date(2026, 1, 31)


def parse_utc(ts: str) -> datetime:
    """Parse ISO timestamp to UTC-aware datetime."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


async def _upsert_actual(session, records: list[dict]) -> tuple[int, int]:
    inserted = updated = 0
    for r in records:
        try:
            existing = await session.execute(
                text(
                    "SELECT id FROM actual_generation "
                    "WHERE settlement_date=:sd AND settlement_period=:sp AND fuel_type=:ft"
                ),
                {"sd": r["settlementDate"], "sp": r["settlementPeriod"], "ft": r.get("fuelType", "WIND")},
            )
            row = existing.fetchone()
            gen_val = r.get("generation")
            if gen_val is None:
                continue
            if row:
                await session.execute(
                    text(
                        "UPDATE actual_generation SET generation=:g, start_time_utc=:st "
                        "WHERE id=:id"
                    ),
                    {"g": float(gen_val), "st": parse_utc(r["startTime"]), "id": row[0]},
                )
                updated += 1
            else:
                ag = ActualGeneration(
                    start_time_utc=parse_utc(r["startTime"]),
                    settlement_date=r["settlementDate"],
                    settlement_period=int(r["settlementPeriod"]),
                    fuel_type=r.get("fuelType", "WIND"),
                    generation=float(gen_val),
                    source_dataset="FUELHH",
                )
                session.add(ag)
                inserted += 1
        except Exception as exc:
            logger.warning("Skip actual record %s: %s", r, exc)
    return inserted, updated


async def _upsert_forecast(session, records: list[dict]) -> tuple[int, int]:
    inserted = updated = 0
    for r in records:
        try:
            st = parse_utc(r["startTime"])
            pt = parse_utc(r["publishTime"])
            gen_val = r.get("generation")
            if gen_val is None:
                continue
            existing = await session.execute(
                text(
                    "SELECT id FROM wind_forecast "
                    "WHERE start_time_utc=:st AND publish_time_utc=:pt"
                ),
                {"st": st, "pt": pt},
            )
            row = existing.fetchone()
            if row:
                await session.execute(
                    text("UPDATE wind_forecast SET generation=:g WHERE id=:id"),
                    {"g": float(gen_val), "id": row[0]},
                )
                updated += 1
            else:
                wf = WindForecast(
                    start_time_utc=st,
                    publish_time_utc=pt,
                    generation=float(gen_val),
                    source_dataset="WINDFOR",
                )
                session.add(wf)
                inserted += 1
        except Exception as exc:
            logger.warning("Skip forecast record %s: %s", r, exc)
    return inserted, updated


async def ingest_actuals() -> dict:
    """Ingest FUELHH WIND actuals for January 2026."""
    logger.info("Starting FUELHH ingestion for Jan 2026")
    total_inserted = total_updated = total_fetched = 0

    async with AsyncSessionLocal() as session:
        run = IngestionRun(dataset="FUELHH", status="running")
        session.add(run)
        await session.commit()
        run_id = run.id

        try:
            with ElexonClient() as client:
                current = ANALYSIS_START
                while current <= ANALYSIS_END:
                    records = client.get_fuelhh_wind(current)
                    total_fetched += len(records)
                    ins, upd = await _upsert_actual(session, records)
                    total_inserted += ins
                    total_updated += upd
                    await session.commit()
                    logger.info("FUELHH %s: %d fetched, %d inserted, %d updated", current, len(records), ins, upd)
                    current += timedelta(days=1)

            await session.execute(
                text(
                    "UPDATE ingestion_run SET status='success', finished_at=datetime('now'), "
                    "records_fetched=:f, records_inserted=:i, records_updated=:u WHERE id=:id"
                ),
                {"f": total_fetched, "i": total_inserted, "u": total_updated, "id": run_id},
            )
            await session.commit()
            return {"status": "success", "fetched": total_fetched, "inserted": total_inserted, "updated": total_updated}

        except Exception as exc:
            logger.error("FUELHH ingestion failed: %s", exc)
            await session.execute(
                text("UPDATE ingestion_run SET status='failed', finished_at=datetime('now'), error_summary=:e WHERE id=:id"),
                {"e": str(exc), "id": run_id},
            )
            await session.commit()
            raise


async def ingest_forecasts() -> dict:
    """Ingest WINDFOR forecast vintages for January 2026.

    We fetch forecasts published from Dec 31, 2025 16:00 UTC through Jan 31, 2026 23:59 UTC
    to capture day-ahead forecasts for every January delivery interval.
    """
    logger.info("Starting WINDFOR ingestion for Jan 2026 forecasts")
    total_inserted = total_updated = total_fetched = 0

    # Publish time range: D-1 cutoff (16:00) for Jan 1 = Dec 31 16:00
    # through end of Jan 31
    publish_start = datetime(2025, 12, 31, 0, 0, 0, tzinfo=UTC)
    publish_end = datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)

    async with AsyncSessionLocal() as session:
        run = IngestionRun(dataset="WINDFOR", status="running")
        session.add(run)
        await session.commit()
        run_id = run.id

        try:
            with ElexonClient() as client:
                records = client.get_windfor_for_period(publish_start, publish_end, chunk_days=3)

            total_fetched = len(records)
            # Filter: only keep records where startTime is in Jan 2026
            jan_start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
            jan_end = datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)
            relevant = [
                r for r in records
                if jan_start <= parse_utc(r["startTime"]) < jan_end
            ]
            logger.info("WINDFOR total fetched=%d, relevant to Jan 2026=%d", total_fetched, len(relevant))

            batch_size = 500
            for i in range(0, len(relevant), batch_size):
                batch = relevant[i:i + batch_size]
                ins, upd = await _upsert_forecast(session, batch)
                total_inserted += ins
                total_updated += upd
                await session.commit()

            await session.execute(
                text(
                    "UPDATE ingestion_run SET status='success', finished_at=datetime('now'), "
                    "records_fetched=:f, records_inserted=:i, records_updated=:u WHERE id=:id"
                ),
                {"f": total_fetched, "i": total_inserted, "u": total_updated, "id": run_id},
            )
            await session.commit()
            return {"status": "success", "fetched": total_fetched, "inserted": total_inserted, "updated": total_updated}

        except Exception as exc:
            logger.error("WINDFOR ingestion failed: %s", exc)
            await session.execute(
                text("UPDATE ingestion_run SET status='failed', finished_at=datetime('now'), error_summary=:e WHERE id=:id"),
                {"e": str(exc), "id": run_id},
            )
            await session.commit()
            raise

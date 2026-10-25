#!/usr/bin/env python3
"""CLI script to run historical data ingestion for January 2026."""
import asyncio
import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


async def main(dataset: str):
    from app.db.database import init_db
    from app.services.ingestion import ingest_actuals, ingest_forecasts

    await init_db()

    if dataset in ("FUELHH", "all"):
        print("Ingesting FUELHH (actual wind generation)...")
        result = await ingest_actuals()
        print(f"FUELHH: {result}")

    if dataset in ("WINDFOR", "all"):
        print("Ingesting WINDFOR (wind forecasts — this may take several minutes)...")
        result = await ingest_forecasts()
        print(f"WINDFOR: {result}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Elexon data for January 2026")
    parser.add_argument("--dataset", choices=["FUELHH", "WINDFOR", "all"], default="all")
    args = parser.parse_args()
    asyncio.run(main(args.dataset))

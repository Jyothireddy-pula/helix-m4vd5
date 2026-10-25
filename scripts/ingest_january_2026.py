#!/usr/bin/env python3
"""
Ingest January 2026 wind generation data from Elexon BMRS.

Usage:
    python scripts/ingest_january_2026.py [--dataset FUELHH|WINDFOR|all]

This script fetches:
  - FUELHH: actual wind generation (half-hourly, settlement periods)
  - WINDFOR: wind generation forecasts (hourly, all historical vintages)

Both datasets cover January 2026 (2026-01-01 to 2026-01-31 inclusive).
Running this script twice is safe — duplicate records are skipped.
"""
import sys
import os
import asyncio
import argparse

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

async def main(dataset: str) -> None:
    from app.db.database import init_db
    from app.services.ingestion import ingest_actuals, ingest_forecasts

    print("Initialising database...")
    await init_db()

    if dataset in ("FUELHH", "all"):
        print("\nIngesting FUELHH (actual wind generation)...")
        result = await ingest_actuals()
        print(f"  Status  : {result['status']}")
        print(f"  Fetched : {result.get('records_fetched', 0)}")
        print(f"  Inserted: {result.get('records_inserted', 0)}")
        if result.get("error"):
            print(f"  Error   : {result['error']}")

    if dataset in ("WINDFOR", "all"):
        print("\nIngesting WINDFOR (wind generation forecasts)...")
        result = await ingest_forecasts()
        print(f"  Status  : {result['status']}")
        print(f"  Fetched : {result.get('records_fetched', 0)}")
        print(f"  Inserted: {result.get('records_inserted', 0)}")
        if result.get("error"):
            print(f"  Error   : {result['error']}")

    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest January 2026 Elexon wind data")
    parser.add_argument(
        "--dataset",
        choices=["FUELHH", "WINDFOR", "all"],
        default="all",
        help="Dataset to ingest (default: all)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.dataset))

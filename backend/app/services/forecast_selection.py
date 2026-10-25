"""Forecast vintage selection logic.

For each delivery interval T with decision cutoff C:
  1. Find all forecast records targeting T
  2. Keep records where publishTime <= C
  3. Select the record with the latest eligible publishTime
  4. If none exists, mark as unavailable
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd

UTC = timezone.utc


def compute_decision_cutoff(delivery_start: datetime, cutoff_hour: int = 16, cutoff_minute: int = 0) -> datetime:
    """Return the day-ahead decision cutoff for a delivery interval.

    The cutoff is at cutoff_hour:cutoff_minute UTC on the calendar day before delivery.
    This is an analytical assumption, not an official market rule.
    """
    delivery_date = delivery_start.astimezone(UTC).date()
    day_before = delivery_date - timedelta(days=1)
    return datetime(day_before.year, day_before.month, day_before.day, cutoff_hour, cutoff_minute, tzinfo=UTC)


def select_forecast_vintage(
    delivery_start: datetime,
    forecasts: list[dict],
    cutoff_hour: int = 16,
    cutoff_minute: int = 0,
) -> dict:
    """Select the appropriate forecast vintage for a delivery interval.

    Args:
        delivery_start: UTC-aware delivery interval start time
        forecasts: List of dicts with keys: start_time_utc, publish_time_utc, generation
        cutoff_hour: Hour of day-ahead cutoff (UTC)
        cutoff_minute: Minute of day-ahead cutoff (UTC)

    Returns:
        dict with keys: selected_generation, publish_time_utc, lead_time_hours,
                        decision_cutoff, status
    """
    cutoff = compute_decision_cutoff(delivery_start, cutoff_hour, cutoff_minute)

    eligible = [
        f for f in forecasts
        if f["publish_time_utc"] <= cutoff
    ]

    if not eligible:
        return {
            "selected_generation": None,
            "publish_time_utc": None,
            "lead_time_hours": None,
            "decision_cutoff": cutoff,
            "status": "unavailable",
        }

    # Pick the one with the latest publishTime among eligible
    selected = max(eligible, key=lambda f: f["publish_time_utc"])
    lead_time = (delivery_start - selected["publish_time_utc"]).total_seconds() / 3600.0

    return {
        "selected_generation": selected["generation"],
        "publish_time_utc": selected["publish_time_utc"],
        "lead_time_hours": round(lead_time, 2),
        "decision_cutoff": cutoff,
        "status": "available",
    }


def build_analysis_table(
    actuals: list[dict],
    forecasts: list[dict],
    cutoff_hour: int = 16,
    cutoff_minute: int = 0,
) -> pd.DataFrame:
    """Build the canonical half-hourly analysis table.

    Args:
        actuals: list of dicts {start_time_utc, generation}
        forecasts: list of dicts {start_time_utc, publish_time_utc, generation}
        cutoff_hour: decision cutoff hour (UTC)
        cutoff_minute: decision cutoff minute

    Returns:
        DataFrame with columns:
            delivery_start, actual_generation, selected_forecast, forecast_publish_time,
            decision_cutoff, lead_time_hours, signed_error, abs_error, squared_error,
            pct_error, forecast_status, data_quality_flag
    """
    # Group forecasts by start_time_utc
    from collections import defaultdict
    fc_map: dict[datetime, list[dict]] = defaultdict(list)
    for f in forecasts:
        st = f["start_time_utc"]
        if not isinstance(st, datetime):
            continue
        if st.tzinfo is None:
            st = st.replace(tzinfo=UTC)
        fc_map[st].append(f)

    rows = []
    for actual in actuals:
        delivery = actual["start_time_utc"]
        if not isinstance(delivery, datetime):
            continue
        if delivery.tzinfo is None:
            delivery = delivery.replace(tzinfo=UTC)

        actual_gen = actual.get("generation")
        quality_flag = []

        if actual_gen is None:
            quality_flag.append("missing_actual")
        elif actual_gen < 0:
            quality_flag.append("negative_actual")

        # Find forecasts that target this delivery interval or within 30 min window
        # WINDFOR is hourly; match on the start_time_utc hour
        delivery_hour = delivery.replace(minute=0, second=0, microsecond=0)
        forecast_candidates = fc_map.get(delivery_hour, []) + fc_map.get(delivery, [])
        # deduplicate
        seen = set()
        unique_candidates = []
        for fc in forecast_candidates:
            key = (fc["publish_time_utc"], fc["start_time_utc"])
            if key not in seen:
                seen.add(key)
                unique_candidates.append(fc)

        sel = select_forecast_vintage(delivery, unique_candidates, cutoff_hour, cutoff_minute)
        selected_gen = sel["selected_generation"]

        signed_error = None
        abs_error = None
        squared_error = None
        pct_error = None

        if actual_gen is not None and selected_gen is not None:
            signed_error = round(selected_gen - actual_gen, 2)
            abs_error = round(abs(signed_error), 2)
            squared_error = round(signed_error ** 2, 4)
            if actual_gen != 0:
                pct_error = round(100.0 * signed_error / actual_gen, 4)
            else:
                quality_flag.append("zero_actual_pct_undefined")
        elif selected_gen is None and actual_gen is not None:
            quality_flag.append("no_eligible_forecast")

        rows.append({
            "delivery_start": delivery,
            "actual_generation": actual_gen,
            "selected_forecast": selected_gen,
            "forecast_publish_time": sel["publish_time_utc"],
            "decision_cutoff": sel["decision_cutoff"],
            "lead_time_hours": sel["lead_time_hours"],
            "signed_error": signed_error,
            "abs_error": abs_error,
            "squared_error": squared_error,
            "pct_error": pct_error,
            "forecast_status": sel["status"],
            "data_quality_flag": "|".join(quality_flag) if quality_flag else None,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("delivery_start").reset_index(drop=True)
    return df

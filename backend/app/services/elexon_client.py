"""Elexon BMRS API client with retries, timeouts, and caching."""
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str) -> Any | None:
    if key in _cache:
        ts, value = _cache[key]
        if time.time() - ts < settings.ELEXON_CACHE_TTL_SECONDS:
            return value
        del _cache[key]
    return None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.time(), value)


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError))


class ElexonClient:
    def __init__(self):
        self.base_url = settings.ELEXON_BASE_URL
        timeout = httpx.Timeout(
            connect=settings.ELEXON_TIMEOUT_CONNECT,
            read=settings.ELEXON_TIMEOUT_READ,
            write=10.0,
            pool=5.0,
        )
        self.client = httpx.Client(timeout=timeout, headers={"Accept": "application/json"})

    @retry(
        stop=stop_after_attempt(settings.ELEXON_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    def _get(self, path: str, params: dict) -> list[dict]:
        cache_key = f"{path}?{sorted(params.items())}"
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.debug("Cache hit: %s", cache_key)
            return cached

        url = f"{self.base_url}/{path}"
        logger.info("GET %s params=%s", url, params)
        resp = self.client.get(url, params=params)

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "10"))
            logger.warning("Rate limited, sleeping %ds", retry_after)
            time.sleep(retry_after)
            resp = self.client.get(url, params=params)

        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise ValueError(f"Unexpected response shape: {type(data)}")
        _cache_set(cache_key, data)
        return data

    def get_fuelhh_wind(self, settlement_date: date) -> list[dict]:
        """Fetch actual WIND generation for a single settlement date."""
        params = {
            "settlementDateFrom": settlement_date.isoformat(),
            "settlementDateTo": settlement_date.isoformat(),
            "fuelType": "WIND",
        }
        records = self._get("datasets/FUELHH/stream", params)
        return [r for r in records if r.get("fuelType") == "WIND"]

    def get_windfor_by_publish(
        self,
        publish_from: datetime,
        publish_to: datetime,
    ) -> list[dict]:
        """Fetch WINDFOR forecasts by publishTime range."""
        params = {
            "publishDateTimeFrom": publish_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": publish_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return self._get("datasets/WINDFOR/stream", params)

    def get_windfor_for_period(
        self,
        start: datetime,
        end: datetime,
        chunk_days: int = 2,
    ) -> list[dict]:
        """Fetch all WINDFOR vintages published in a publish-time window, chunked."""
        all_records: list[dict] = []
        current = start
        while current < end:
            next_chunk = min(current + timedelta(days=chunk_days), end)
            try:
                records = self.get_windfor_by_publish(current, next_chunk)
                all_records.extend(records)
                logger.info(
                    "WINDFOR %s→%s: %d records", current.date(), next_chunk.date(), len(records)
                )
            except Exception as exc:
                logger.error("Failed WINDFOR chunk %s→%s: %s", current, next_chunk, exc)
            current = next_chunk
        return all_records

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

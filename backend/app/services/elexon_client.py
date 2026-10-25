
from datetime import datetime, timezone
from typing import Any
import os

import httpx

BASE_URL = os.getenv(
    "ELEXON_API_BASE",
    "https://data.elexon.co.uk/bmrs/api/v1",
)
TIMEOUT_SECONDS = float(os.getenv("ELEXON_TIMEOUT_SECONDS", "45"))


def _utc_string(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


async def _fetch(
    path: str,
    params: dict[str, str],
) -> list[dict[str, Any]]:
    url = f"{BASE_URL}/{path}"

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("data", payload.get("results", []))
    else:
        records = []

    if not isinstance(records, list):
        raise ValueError(f"Unexpected response format from {path}")

    records = [record for record in records if isinstance(record, dict)]
    print(f"[ELEXON DEBUG] URL: {response.url}")
    print(f"[ELEXON DEBUG] Records received: {len(records)}")
    if records:
        print(f"[ELEXON DEBUG] First record: {records[0]}")

    return records


async def fetch_actuals(
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    records = await _fetch(
        "datasets/FUELHH/stream",
        {
            "settlementDateFrom": start.date().isoformat(),
            "settlementDateTo": end.date().isoformat(),
        },
    )

    actuals = [
        record
        for record in records
        if str(record.get("fuelType", "")).upper() == "WIND"
        and start <= datetime.fromisoformat(
            str(record["startTime"]).replace("Z", "+00:00")
        ) < end
    ]

    print(f"[ELEXON DEBUG] WIND actuals in date range: {len(actuals)}")
    return actuals





async def fetch_forecasts(
    publication_time: datetime,
) -> list[dict[str, Any]]:
    records = await _fetch(
        "forecast/generation/wind/history",
        {
            "publishTime": _utc_string(publication_time),
        },
    )

    print(
        f"[FORECAST DEBUG] Requested publication: "
        f"{_utc_string(publication_time)}"
    )
    print(f"[FORECAST DEBUG] Historical records: {len(records)}")

    return records
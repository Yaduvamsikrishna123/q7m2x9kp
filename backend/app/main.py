from datetime import date, datetime, time, timedelta, timezone
from typing import Any
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .services.elexon_client import fetch_actuals, fetch_forecasts
from .services.analysis import build_comparison, calculate_metrics

app = FastAPI(
    title="Wind Forecast Analytics API",
    description="Historical UK wind generation forecast and accuracy analysis for January 2026.",
    version="0.1.0",
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "wind-forecast-analytics"}


@app.get("/api/comparison")
async def comparison(
    delivery_date: date = Query(..., description="Delivery date in January 2026, YYYY-MM-DD"),
    cutoff_hour: int = Query(18, ge=0, le=23, description="Illustrative local UK decision cutoff hour"),
) -> dict[str, Any]:
    if delivery_date < date(2026, 1, 1) or delivery_date > date(2026, 1, 31):
        raise HTTPException(status_code=400, detail="delivery_date must be in January 2026")

    start = datetime.combine(delivery_date, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    # The cutoff is configured as a UK local clock hour. January is GMT (UTC+0).
    cutoff = datetime.combine(delivery_date - timedelta(days=1), time(cutoff_hour), tzinfo=timezone.utc)

    try:
        actuals, forecasts = await _load_data(
    start,
    end,
    cutoff_hour,
)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not retrieve Elexon data: {exc}") from exc

    rows = build_comparison(actuals, forecasts, cutoff=cutoff)
    day_rows = [row for row in rows if row["startTime"].startswith(delivery_date.isoformat())]
    return {
        "delivery_date": delivery_date.isoformat(),
        "decision_cutoff": cutoff.isoformat(),
        "cutoff_hour_uk": cutoff_hour,
        "note": "The default 18:00 cutoff is a prototype assumption; confirm the client's applicable market/trading deadline.",
        "records": day_rows,
        "metrics": calculate_metrics(day_rows, expected_intervals=24),
        "source": "Elexon BMRS FUELHH and WINDFOR",
    }


@app.get("/api/accuracy")
async def accuracy(
    month: str = Query("2026-01", pattern=r"^2026-01$"),
    cutoff_hour: int = Query(18, ge=0, le=23),
) -> dict[str, Any]:
    # The endpoint evaluates delivery days in January. We request an extra prior day
    # of forecasts so the day-ahead cutoff can be applied to Jan 1 as well.
    start = datetime(2025, 12, 31, tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, tzinfo=timezone.utc)
    try:
        actuals, forecasts = await _load_data(start, end)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not retrieve Elexon data: {exc}") from exc

    all_rows: list[dict[str, Any]] = []
    for day in range(1, 32):
        delivery_date = date(2026, 1, day)
        cutoff = datetime.combine(delivery_date - timedelta(days=1), time(cutoff_hour), tzinfo=timezone.utc)
        rows = build_comparison(actuals, forecasts, cutoff=cutoff)
        all_rows.extend(row for row in rows if row["startTime"].startswith(delivery_date.isoformat()))

    return {
        "month": month,
        "cutoff_hour_uk": cutoff_hour,
        "metrics": calculate_metrics(all_rows, expected_intervals=31 * 24),
        "records": all_rows,
        "note": "Cutoff hour is a prototype assumption and must be confirmed with the client.",
        "source": "Elexon BMRS FUELHH and WINDFOR",
    }
  
def get_publication_time(delivery_date: date, cutoff_hour: int) -> datetime:
    cutoff = datetime.combine(
        delivery_date - timedelta(days=1),
        time(cutoff_hour),
        tzinfo=timezone.utc,
    )

    # Standard Elexon wind forecast publication times (UTC).
    publication_hours = [
        (3, 30),
        (5, 30),
        (8, 30),
        (10, 30),
        (12, 30),
        (16, 30),
        (19, 30),
        (23, 30),
    ]

    candidates = [
        datetime.combine(
            delivery_date - timedelta(days=1),
            time(hour, minute),
            tzinfo=timezone.utc,
        )
        for hour, minute in publication_hours
    ]

    eligible = [published for published in candidates if published <= cutoff]

    if not eligible:
        raise ValueError("No standard forecast publication exists before this cutoff.")

    return max(eligible)  


async def _load_data(
    start: datetime,
    end: datetime,
    cutoff_hour: int = 18,
):
    actuals = await fetch_actuals(start, end)

    publication_time = get_publication_time(
        start.date(),
        cutoff_hour,
    )

    forecasts = await fetch_forecasts(publication_time)
    return actuals, forecasts
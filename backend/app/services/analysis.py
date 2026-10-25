from datetime import datetime
from math import sqrt
from statistics import mean
from typing import Any


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            # Source timestamps without an offset are treated as UTC for this prototype.
            from datetime import timezone
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def numeric(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        result = float(value)
        if result != result or result in (float("inf"), float("-inf")):
            return None
        return result
    except (ValueError, TypeError):
        return None


def _interval_key(value: Any) -> str | None:
    parsed = parse_timestamp(value)
    return parsed.isoformat() if parsed else None



def build_comparison(
    actuals: list[dict[str, Any]],
    forecasts: list[dict[str, Any]],
    cutoff: datetime,
) -> list[dict[str, Any]]:
    """Compare hourly forecasts with hourly averages of half-hourly actuals."""

    actual_groups: dict[str, list[float]] = {}

    # Group half-hourly actuals into hourly averages.
    for row in actuals:
        parsed = parse_timestamp(row.get("startTime"))
        value = numeric(row.get("generation"))

        if parsed is None or value is None:
            continue

        hour_start = parsed.replace(
            minute=0, second=0, microsecond=0
        )
        key = hour_start.isoformat()
        actual_groups.setdefault(key, []).append(value)

    actual_by_interval = {
        key: sum(values) / len(values)
        for key, values in actual_groups.items()
    }

    # Keep only forecasts published by the decision cutoff.
    forecasts_by_interval: dict[
        str, list[tuple[datetime, float]]
    ] = {}

    for row in forecasts:
        key = _interval_key(row.get("startTime"))
        published = parse_timestamp(row.get("publishTime"))
        generation = numeric(row.get("generation"))

        if not key or published is None or generation is None:
            continue

        if published <= cutoff:
            forecasts_by_interval.setdefault(key, []).append(
                (published, generation)
            )

    rows: list[dict[str, Any]] = []
    keys = sorted(set(actual_by_interval) | set(forecasts_by_interval))

    for key in keys:
        actual = actual_by_interval.get(key)
        candidates = forecasts_by_interval.get(key, [])
        selected = max(candidates, key=lambda item: item[0]) if candidates else None

        forecast = selected[1] if selected else None
        published = selected[0].isoformat() if selected else None
        error = (
            forecast - actual
            if forecast is not None and actual is not None
            else None
        )

        rows.append({
            "startTime": key,
            "publishTime": published,
            "forecast_mw": forecast,
            "actual_mw": round(actual, 3) if actual is not None else None,
            "error_mw": round(error, 3) if error is not None else None,
            "status": (
                "matched" if error is not None
                else "missing_forecast" if actual is not None
                else "missing_actual"
            ),
        })

    return rows


def calculate_metrics(rows: list[dict[str, Any]], expected_intervals: int | None = None) -> dict[str, Any]:
    errors = [row["error_mw"] for row in rows if row.get("error_mw") is not None]
    matched = len(errors)
    expected = expected_intervals if expected_intervals is not None else len(rows)
    abs_errors = [abs(error) for error in errors]
    return {
        "matched_intervals": matched,
        "intervals_returned": len(rows),
        "coverage_pct": round(100 * matched / expected, 2) if expected else 0,
        "mae_mw": round(mean(abs_errors), 3) if abs_errors else None,
        "rmse_mw": round(sqrt(mean(error * error for error in errors)), 3) if errors else None,
        "bias_mw": round(mean(errors), 3) if errors else None,
    }

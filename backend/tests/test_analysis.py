from datetime import datetime, timezone
from app.services.analysis import build_comparison, calculate_metrics


def test_selects_latest_forecast_before_cutoff():
    actuals = [{"startTime": "2026-01-15T10:00:00Z", "fuelType": "WIND", "generation": 550}]
    forecasts = [
        {"startTime": "2026-01-15T10:00:00Z", "publishTime": "2026-01-14T08:00:00Z", "generation": 500},
        {"startTime": "2026-01-15T10:00:00Z", "publishTime": "2026-01-14T16:00:00Z", "generation": 580},
        {"startTime": "2026-01-15T10:00:00Z", "publishTime": "2026-01-14T20:00:00Z", "generation": 610},
    ]
    cutoff = datetime(2026, 1, 14, 18, tzinfo=timezone.utc)
    result = build_comparison(actuals, forecasts, cutoff)
    assert len(result) == 1
    assert result[0]["forecast_mw"] == 580
    assert result[0]["actual_mw"] == 550
    assert result[0]["error_mw"] == 30


def test_metrics():
    rows = [
        {"error_mw": 30},
        {"error_mw": -40},
        {"error_mw": 20},
    ]
    metrics = calculate_metrics(rows)
    assert metrics["matched_intervals"] == 3
    assert metrics["mae_mw"] == 30
    assert metrics["bias_mw"] == 3.333
    assert metrics["rmse_mw"] == 31.091


def test_missing_actual_is_not_zero():
    actuals = []
    forecasts = [{"startTime": "2026-01-15T10:00:00Z", "publishTime": "2026-01-14T16:00:00Z", "generation": 580}]
    cutoff = datetime(2026, 1, 14, 18, tzinfo=timezone.utc)
    result = build_comparison(actuals, forecasts, cutoff)
    assert result[0]["actual_mw"] is None
    assert result[0]["error_mw"] is None

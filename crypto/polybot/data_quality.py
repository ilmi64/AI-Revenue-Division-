"""Offline historical candle coverage and feed-quality evaluation.

This module performs no network requests and emits no trading signals.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


class DataQualityError(ValueError):
    """Raised when the requested quality-evaluation window is invalid."""


def _aware_utc(value: str | datetime, field: str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DataQualityError(f"{field} must be an ISO-8601 timestamp") from exc
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DataQualityError(f"{field} must include a timezone")
    return value.astimezone(timezone.utc)


def _positive_decimal(value: Any, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return parsed


def _gap_ranges(expected: list[datetime], present: set[datetime], step: timedelta) -> list[dict[str, Any]]:
    missing = [stamp for stamp in expected if stamp not in present]
    ranges: list[dict[str, Any]] = []
    for stamp in missing:
        if ranges and stamp == ranges[-1]["_last"] + step:
            ranges[-1]["_last"] = stamp
            ranges[-1]["count"] += 1
        else:
            ranges.append({"start": stamp, "_last": stamp, "count": 1})
    return [
        {
            "start": item["start"].isoformat(),
            "end": item["_last"].isoformat(),
            "missing_candles": item["count"],
        }
        for item in ranges
    ]


def evaluate_candle_quality(
    candles: Iterable[dict[str, Any]],
    *,
    expected_start: str | datetime,
    expected_end: str | datetime,
    now: str | datetime,
    interval_seconds: int = 3600,
    max_age_seconds: float = 5400,
    minimum_coverage: float = 0.95,
    comparison_rows: Iterable[dict[str, Any]] | None = None,
    divergence_threshold_percentage_points: float = 1.0,
    minimum_comparison_samples: int = 3,
) -> dict[str, Any]:
    """Assess one source's expected candle grid and optional cross-venue returns.

    The expected window is inclusive of candle-open times. Invalid, duplicate,
    incomplete, out-of-window, missing and stale data are kept distinct.
    """
    start = _aware_utc(expected_start, "expected_start")
    end = _aware_utc(expected_end, "expected_end")
    current = _aware_utc(now, "now")
    if interval_seconds <= 0:
        raise DataQualityError("interval_seconds must be positive")
    if end < start:
        raise DataQualityError("expected_end must not precede expected_start")
    if not 0 <= minimum_coverage <= 1:
        raise DataQualityError("minimum_coverage must be between 0 and 1")
    if max_age_seconds < 0 or divergence_threshold_percentage_points < 0:
        raise DataQualityError("age and divergence thresholds cannot be negative")
    if minimum_comparison_samples < 1:
        raise DataQualityError("minimum_comparison_samples must be at least one")
    step = timedelta(seconds=interval_seconds)
    if start.timestamp() % interval_seconds or end.timestamp() % interval_seconds:
        raise DataQualityError("expected window boundaries must align to the interval")

    expected: list[datetime] = []
    cursor = start
    while cursor <= end:
        expected.append(cursor)
        cursor += step
    expected_set = set(expected)

    source = base_asset = quote_asset = interval = None
    seen: set[datetime] = set()
    valid_times: set[datetime] = set()
    collection_times: list[datetime] = []
    duplicate_count = malformed_count = incomplete_count = out_of_window_count = 0
    input_count = 0

    for row in candles:
        input_count += 1
        try:
            if not isinstance(row, dict) or row.get("data_type") != "candle":
                raise ValueError("record is not a candle")
            metadata = (row.get("source"), row.get("base_asset"), row.get("quote_asset"), row.get("interval"))
            if any(not isinstance(value, str) or not value for value in metadata):
                raise ValueError("source, assets and interval are required")
            if source is None:
                source, base_asset, quote_asset, interval = metadata
            elif metadata != (source, base_asset, quote_asset, interval):
                raise ValueError("mixed source, asset or interval provenance")
            unit_seconds = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
            suffix, amount = interval[-1], interval[:-1]
            if suffix in unit_seconds and amount.isdigit():
                if int(amount) * unit_seconds[suffix] != interval_seconds:
                    raise ValueError("candle interval does not match evaluation grid")
            stamp = _aware_utc(row.get("event_time"), "event_time")
            collected = _aware_utc(row.get("collected_at"), "collected_at")
            _positive_decimal(row.get("payload", {}).get("close"), "close")
            collection_times.append(collected)
            if stamp not in expected_set:
                out_of_window_count += 1
                continue
            if stamp in seen:
                duplicate_count += 1
                continue
            seen.add(stamp)
            if not row.get("is_complete", False):
                incomplete_count += 1
                continue
            valid_times.add(stamp)
        except (ValueError, TypeError, AttributeError, KeyError):
            malformed_count += 1

    missing = len(expected_set - valid_times)
    coverage = len(valid_times) / len(expected) if expected else 0.0
    latest_collection = max(collection_times) if collection_times else None
    age_seconds = (current - latest_collection).total_seconds() if latest_collection else None
    future_collection = age_seconds is not None and age_seconds < 0
    stale = age_seconds is None or future_collection or age_seconds > max_age_seconds
    gaps = _gap_ranges(expected, valid_times, step)

    comparisons = list(comparison_rows or [])
    divergence_flags: list[dict[str, Any]] = []
    valid_comparison_count = 0
    for item in comparisons:
        try:
            difference = Decimal(str(item.get("return_difference_percentage_points")))
            if not difference.is_finite():
                continue
            valid_comparison_count += 1
            if abs(difference) > Decimal(str(divergence_threshold_percentage_points)):
                divergence_flags.append({
                    "event_time": item.get("event_time"),
                    "return_difference_percentage_points": str(difference),
                    "review_required": True,
                    "interpretation": "unusual_return_divergence; investigate data quality and market context; not a trade signal",
                })
        except (InvalidOperation, TypeError, ValueError, AttributeError):
            continue

    insufficient_comparison = bool(comparisons) and valid_comparison_count < minimum_comparison_samples
    quality_flags = []
    if missing:
        quality_flags.append("missing_candles")
    if duplicate_count:
        quality_flags.append("duplicate_timestamps")
    if malformed_count:
        quality_flags.append("malformed_records")
    if incomplete_count:
        quality_flags.append("incomplete_candles")
    if out_of_window_count:
        quality_flags.append("out_of_window_records")
    if stale:
        quality_flags.append("stale_or_unavailable_feed")
    if insufficient_comparison:
        quality_flags.append("insufficient_comparison_samples")
    if divergence_flags:
        quality_flags.append("unusual_cross_venue_return_divergence")

    usable = (
        bool(expected)
        and coverage >= minimum_coverage
        and not stale
        and duplicate_count == 0
        and malformed_count == 0
        and incomplete_count == 0
        and out_of_window_count == 0
        and not future_collection
        and not insufficient_comparison
    )
    return {
        "source": source,
        "base_asset": base_asset,
        "quote_asset": quote_asset,
        "interval": interval,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "expected_candles": len(expected),
        "input_records": input_count,
        "valid_candles": len(valid_times),
        "missing_candles": missing,
        "duplicate_records": duplicate_count,
        "malformed_records": malformed_count,
        "incomplete_candles": incomplete_count,
        "out_of_window_records": out_of_window_count,
        "coverage_ratio": round(coverage, 6),
        "coverage_percent": round(coverage * 100, 2),
        "missing_ranges": gaps,
        "freshness": {
            "latest_collected_at": latest_collection.isoformat() if latest_collection else None,
            "age_seconds": age_seconds,
            "max_age_seconds": max_age_seconds,
            "stale": stale,
            "future_collection_time": future_collection,
        },
        "comparison": {
            "valid_samples": valid_comparison_count,
            "minimum_samples": minimum_comparison_samples,
            "insufficient_samples": insufficient_comparison,
            "divergence_threshold_percentage_points": divergence_threshold_percentage_points,
            "divergence_flags": divergence_flags,
        },
        "quality_flags": quality_flags,
        "usable_for_research": usable,
        "interpretation": "quality_assessment_only; not a strategy, trade signal, executable spread, or execution authorization",
    }

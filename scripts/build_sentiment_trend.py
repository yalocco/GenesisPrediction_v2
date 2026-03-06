#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_sentiment_trend.py

Purpose:
    Build sentiment trend metrics from daily sentiment history snapshots and
    publish the latest trend result into analysis.

Design:
    - history = observation memory
    - analysis = current truth / latest consumable output
    - UI reads analysis only
    - This script computes trend metrics from dated history files

Input:
    data/world_politics/history/sentiment/sentiment_YYYY-MM-DD.json

Output:
    data/world_politics/analysis/sentiment_trend_latest.json

Usage:
    python scripts/build_sentiment_trend.py
    python scripts/build_sentiment_trend.py --window 7
    python scripts/build_sentiment_trend.py --as-of 2026-03-07
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent

HISTORY_DIR = REPO_ROOT / "data" / "world_politics" / "history" / "sentiment"
OUTPUT_PATH = REPO_ROOT / "data" / "world_politics" / "analysis" / "sentiment_trend_latest.json"

FILENAME_RE = re.compile(r"^sentiment_(\d{4}-\d{2}-\d{2})\.json$")


@dataclass
class DailyCounts:
    date: str
    articles: int
    positive: int
    negative: int
    neutral: int
    mixed: int
    unknown: int
    negative_ratio: float
    positive_ratio: float
    mixed_ratio: float
    unknown_ratio: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build sentiment trend from observation history.")
    parser.add_argument(
        "--window",
        type=int,
        default=7,
        help="Trend window size. Default: 7",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        default=None,
        help="Use history up to this date (YYYY-MM-DD). Default: latest available date.",
    )
    parser.add_argument(
        "--min-days",
        type=int,
        default=3,
        help="Minimum required days to publish a meaningful trend. Default: 3",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra details.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def normalize_label(value: Any) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    if text in {"positive", "negative", "neutral", "mixed", "unknown"}:
        return text
    return "unknown"


def extract_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if not isinstance(payload, dict):
        return []

    # Likely structures
    for key in ("items", "articles", "news", "rows"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]

    # Fallback: if payload itself looks like one-day summary but contains list-like nested values
    return []


def count_sentiments(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "mixed": 0,
        "unknown": 0,
    }

    for item in items:
        label = (
            item.get("sentiment_label")
            if isinstance(item, dict) else None
        )
        if label is None and isinstance(item, dict):
            label = item.get("sentiment")
        if label is None and isinstance(item, dict):
            label = item.get("label")

        normalized = normalize_label(label)
        counts[normalized] += 1

    return counts


def build_daily_counts(date_str: str, payload: Any) -> DailyCounts:
    items = extract_items(payload)
    counts = count_sentiments(items)
    articles = len(items)

    return DailyCounts(
        date=date_str,
        articles=articles,
        positive=counts["positive"],
        negative=counts["negative"],
        neutral=counts["neutral"],
        mixed=counts["mixed"],
        unknown=counts["unknown"],
        negative_ratio=safe_ratio(counts["negative"], articles),
        positive_ratio=safe_ratio(counts["positive"], articles),
        mixed_ratio=safe_ratio(counts["mixed"], articles),
        unknown_ratio=safe_ratio(counts["unknown"], articles),
    )


def list_history_files(as_of: str | None) -> list[tuple[str, Path]]:
    if not HISTORY_DIR.exists():
        return []

    results: list[tuple[str, Path]] = []
    for path in sorted(HISTORY_DIR.glob("sentiment_*.json")):
        m = FILENAME_RE.match(path.name)
        if not m:
            continue
        date_str = m.group(1)
        if as_of and date_str > as_of:
            continue
        results.append((date_str, path))

    return sorted(results, key=lambda x: x[0])


def moving_average(values: list[float]) -> float:
    if not values:
        return 0.0
    return mean(values)


def slope(values: list[float]) -> float:
    """
    Simple linear regression slope against index 0..n-1.
    """
    n = len(values)
    if n < 2:
        return 0.0

    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    denominator = sum((x - x_mean) ** 2 for x in xs)

    if math.isclose(denominator, 0.0):
        return 0.0

    return numerator / denominator


def classify_direction(value: float, epsilon: float = 1e-9) -> str:
    if value > epsilon:
        return "up"
    if value < -epsilon:
        return "down"
    return "flat"


def build_regime(latest: DailyCounts, ma_negative: float, neg_slope: float) -> str:
    """
    Very simple first version regime.
    """
    if latest.negative_ratio >= 0.45 and neg_slope > 0:
        return "high_risk_rising"
    if latest.negative_ratio >= 0.35:
        return "high_risk"
    if latest.mixed_ratio >= 0.25 and neg_slope > 0:
        return "uncertain_rising"
    if latest.negative_ratio < 0.20 and ma_negative < 0.20:
        return "stable"
    return "watch"


def build_alerts(series: list[DailyCounts], ma_negative: float) -> list[str]:
    alerts: list[str] = []
    if not series:
        return alerts

    latest = series[-1]
    prev = series[-2] if len(series) >= 2 else None

    if latest.negative_ratio >= 0.40:
        alerts.append("negative_ratio_high")

    if latest.mixed_ratio >= 0.25:
        alerts.append("mixed_ratio_high")

    if latest.unknown_ratio >= 0.30:
        alerts.append("unknown_ratio_high")

    if prev and latest.negative_ratio > prev.negative_ratio + 0.10:
        alerts.append("negative_surge_day_over_day")

    if latest.negative_ratio > ma_negative + 0.10:
        alerts.append("negative_above_moving_average")

    return alerts


def build_output(series: list[DailyCounts], window: int, min_days: int) -> dict[str, Any]:
    if not series:
        return {
            "status": "no_data",
            "message": "No sentiment history files found.",
            "history_dir": str(HISTORY_DIR),
            "window": window,
            "min_days": min_days,
            "days_available": 0,
            "series": [],
        }

    latest = series[-1]
    recent = series[-window:] if len(series) >= window else series[:]

    negative_ratios = [d.negative_ratio for d in recent]
    positive_ratios = [d.positive_ratio for d in recent]
    mixed_ratios = [d.mixed_ratio for d in recent]
    unknown_ratios = [d.unknown_ratio for d in recent]

    negative_ma = moving_average(negative_ratios)
    positive_ma = moving_average(positive_ratios)
    mixed_ma = moving_average(mixed_ratios)
    unknown_ma = moving_average(unknown_ratios)

    negative_slope = slope(negative_ratios)
    positive_slope = slope(positive_ratios)
    mixed_slope = slope(mixed_ratios)

    alerts = build_alerts(recent, negative_ma)
    regime = build_regime(latest, negative_ma, negative_slope)

    enough_days = len(series) >= min_days

    return {
        "status": "ok" if enough_days else "insufficient_history",
        "as_of": latest.date,
        "window": window,
        "min_days": min_days,
        "days_available": len(series),
        "regime": regime,
        "alerts": alerts,
        "latest": {
            "date": latest.date,
            "articles": latest.articles,
            "counts": {
                "positive": latest.positive,
                "negative": latest.negative,
                "neutral": latest.neutral,
                "mixed": latest.mixed,
                "unknown": latest.unknown,
            },
            "ratios": {
                "positive": round(latest.positive_ratio, 6),
                "negative": round(latest.negative_ratio, 6),
                "mixed": round(latest.mixed_ratio, 6),
                "unknown": round(latest.unknown_ratio, 6),
            },
        },
        "moving_average": {
            "positive_ratio": round(positive_ma, 6),
            "negative_ratio": round(negative_ma, 6),
            "mixed_ratio": round(mixed_ma, 6),
            "unknown_ratio": round(unknown_ma, 6),
        },
        "direction": {
            "positive_ratio": classify_direction(positive_slope),
            "negative_ratio": classify_direction(negative_slope),
            "mixed_ratio": classify_direction(mixed_slope),
        },
        "slope": {
            "positive_ratio": round(positive_slope, 6),
            "negative_ratio": round(negative_slope, 6),
            "mixed_ratio": round(mixed_slope, 6),
        },
        "series": [
            {
                "date": d.date,
                "articles": d.articles,
                "counts": {
                    "positive": d.positive,
                    "negative": d.negative,
                    "neutral": d.neutral,
                    "mixed": d.mixed,
                    "unknown": d.unknown,
                },
                "ratios": {
                    "positive": round(d.positive_ratio, 6),
                    "negative": round(d.negative_ratio, 6),
                    "mixed": round(d.mixed_ratio, 6),
                    "unknown": round(d.unknown_ratio, 6),
                },
            }
            for d in recent
        ],
    }


def write_output(payload: dict[str, Any]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> int:
    args = parse_args()

    file_entries = list_history_files(args.as_of)

    series: list[DailyCounts] = []
    for date_str, path in file_entries:
        try:
            payload = load_json(path)
            daily = build_daily_counts(date_str, payload)
            series.append(daily)
        except Exception as exc:
            print(f"[WARN] failed to read {path}: {exc}", file=sys.stderr)

    output = build_output(series, window=args.window, min_days=args.min_days)
    write_output(output)

    if args.verbose:
        print(f"history_dir : {HISTORY_DIR}")
        print(f"output_path : {OUTPUT_PATH}")
        print(f"days        : {output.get('days_available', 0)}")
        print(f"status      : {output.get('status')}")
        print(f"as_of       : {output.get('as_of')}")
        print(f"regime      : {output.get('regime')}")
        print(f"alerts      : {', '.join(output.get('alerts', [])) if output.get('alerts') else '(none)'}")
    else:
        print("build_sentiment_trend")
        print(f"history_dir : {HISTORY_DIR}")
        print(f"output_path : {OUTPUT_PATH}")
        print(f"days        : {output.get('days_available', 0)}")
        print(f"status      : {output.get('status')}")
        if output.get("as_of"):
            print(f"as_of       : {output.get('as_of')}")
        if output.get("regime"):
            print(f"regime      : {output.get('regime')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
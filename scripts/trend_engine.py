#!/usr/bin/env python3
"""GenesisPrediction v2 - Trend Engine

Builds trend_latest.json from analysis artifacts and lightweight history.

Design intent:
- analysis/ is the Single Source of Truth
- scripts generate artifacts only
- Trend extracts direction / persistence / pressure from observation data
- Signal / Scenario / Prediction should receive a stable, explainable trend schema

This implementation is intentionally schema-tolerant because upstream
analysis artifacts may evolve. It reads a handful of likely latest files,
normalizes whatever it can find, and emits a predictable trend contract for
Signal Engine consumption.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


VERSION = "1.0"
DEFAULT_HORIZON_DAYS = 7
DEFAULT_HISTORY_DAYS = 7


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {"value": data}


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        text = str(value).strip()
        if text.endswith("%"):
            return float(text[:-1]) / 100.0
        return float(text)
    except (TypeError, ValueError):
        return default


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def mean(values: Sequence[float], default: float = 0.0) -> float:
    nums = [float(v) for v in values if v is not None]
    return sum(nums) / len(nums) if nums else default


def pick(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in d and d[key] is not None:
            return d[key]
    return default


def walk_numbers(value: Any, prefix: str = "") -> Iterable[Tuple[str, float]]:
    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{prefix}.{k}" if prefix else str(k)
            yield from walk_numbers(v, child)
    elif isinstance(value, list):
        numeric_items = [safe_float(v, None) for v in value]
        numeric_items = [v for v in numeric_items if v is not None]
        if numeric_items:
            key = prefix if prefix else "list"
            yield key, mean(numeric_items, 0.0)
        else:
            for idx, v in enumerate(value[:10]):
                child = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
                yield from walk_numbers(v, child)
    else:
        num = safe_float(value, None)
        if num is not None:
            key = prefix if prefix else "value"
            yield key, num


def normalize_direction(delta: float, score: float) -> str:
    if score >= 0.35 and delta >= 0.08:
        return "accelerating"
    if score <= -0.35 and delta <= -0.08:
        return "accelerating"
    if score >= 0.08:
        return "rising"
    if score <= -0.08:
        return "falling"
    return "stable"


def risk_level_from_score(score: float) -> str:
    if score >= 0.86:
        return "critical"
    if score >= 0.68:
        return "high"
    if score >= 0.48:
        return "elevated"
    if score >= 0.24:
        return "guarded"
    return "low"


def sentiment_balance_to_label(balance: float) -> str:
    if balance >= 0.25:
        return "positive-leaning"
    if balance <= -0.25:
        return "negative-leaning"
    return "mixed"


def date_from_text(text: str) -> Optional[str]:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else None


def candidate_history_dirs(root: Path) -> List[Path]:
    dirs: List[Path] = []
    for base in [root / "prediction_history", root / "history", root / "observation_history"]:
        if base.exists() and base.is_dir():
            for child in base.iterdir():
                if child.is_dir():
                    dirs.append(child)
    dirs.sort(key=lambda p: date_from_text(p.name) or p.name, reverse=True)
    return dirs


def read_history_window(root: Path, limit_days: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for folder in candidate_history_dirs(root)[: max(limit_days * 2, limit_days)]:
        for name in (
            "daily_summary_latest.json",
            "daily_summary.json",
            "sentiment_latest.json",
            "sentiment.json",
            "health_latest.json",
            "health.json",
            "view_model_latest.json",
            "view_model.json",
            "prediction_latest.json",
            "prediction.json",
        ):
            path = folder / name
            if path.exists():
                try:
                    payload = load_json(path)
                except Exception:
                    continue
                payload["__history_path__"] = str(path)
                payload["__history_date__"] = date_from_text(folder.name)
                out.append(payload)
                break
        if len(out) >= limit_days:
            break
    return out


class ObservationBundle:
    def __init__(self, analysis_root: Path) -> None:
        self.analysis_root = analysis_root
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.history = read_history_window(analysis_root, DEFAULT_HISTORY_DAYS)

    def load_if_exists(self, key: str, *candidates: str) -> None:
        for rel in candidates:
            path = self.analysis_root / rel
            if path.exists():
                try:
                    payload = load_json(path)
                except Exception:
                    continue
                payload["__source_path__"] = str(path)
                self.sources[key] = payload
                return

    def load_defaults(self) -> None:
        self.load_if_exists("daily_summary", "daily_summary_latest.json", "world_politics/daily_summary_latest.json")
        self.load_if_exists("sentiment", "sentiment_latest.json", "world_politics/sentiment_latest.json")
        self.load_if_exists("health", "health_latest.json", "world_politics/health_latest.json")
        self.load_if_exists("view_model", "view_model_latest.json", "digest/view_model_latest.json")
        self.load_if_exists("prediction", "prediction/prediction_latest.json")


class TrendMetric:
    def __init__(
        self,
        key: str,
        label: str,
        current: float,
        previous: float,
        confidence: float,
        rationale: str,
        source: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.key = key
        self.label = label
        self.current = current
        self.previous = previous
        self.delta = current - previous
        baseline = max(abs(previous), 0.2)
        self.score = clamp((current - previous) / baseline, -1.0, 1.0)
        self.direction = normalize_direction(self.delta, self.score)
        self.confidence = clamp(confidence, 0.0, 1.0)
        self.rationale = rationale
        self.source = source
        self.tags = tags or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "direction": self.direction,
            "score": round(self.score, 4),
            "delta": round(self.delta, 4),
            "confidence": round(self.confidence, 4),
            "current": round(self.current, 4),
            "previous": round(self.previous, 4),
            "rationale": self.rationale,
            "source": self.source,
            "tags": self.tags,
            "metadata": self.metadata,
        }


def summarize_history_metric(history: List[Dict[str, Any]], patterns: Sequence[str]) -> List[float]:
    values: List[float] = []
    for payload in history:
        flattened = list(walk_numbers(payload))
        matched = [v for k, v in flattened if any(p in k.lower() for p in patterns)]
        if matched:
            values.append(mean(matched, 0.0))
    return values


def build_sentiment_trend(bundle: ObservationBundle) -> Optional[TrendMetric]:
    payload = bundle.sources.get("sentiment")
    if not payload:
        return None

    flattened = list(walk_numbers(payload))
    positive = mean([v for k, v in flattened if "positive" in k.lower()], 0.0)
    negative = mean([v for k, v in flattened if "negative" in k.lower()], 0.0)
    neutral = mean([v for k, v in flattened if "neutral" in k.lower()], 0.0)
    mixed = mean([v for k, v in flattened if "mixed" in k.lower()], 0.0)

    current_balance = positive - negative
    history_balances = summarize_history_metric(bundle.history, ["positive", "negative"])
    if history_balances:
        previous = mean(history_balances, current_balance)
    else:
        previous = current_balance * 0.85

    label = sentiment_balance_to_label(current_balance)
    rationale = (
        f"Sentiment balance is {label}: positive={positive:.3f}, negative={negative:.3f}, "
        f"neutral={neutral:.3f}, mixed={mixed:.3f}."
    )
    confidence = 0.55 + min(0.25, abs(current_balance) * 0.5)
    return TrendMetric(
        key="sentiment_trend",
        label="Sentiment Trend",
        current=current_balance,
        previous=previous,
        confidence=confidence,
        rationale=rationale,
        source="sentiment_latest.json",
        tags=["sentiment", label],
        metadata={
            "positive": round(positive, 4),
            "negative": round(negative, 4),
            "neutral": round(neutral, 4),
            "mixed": round(mixed, 4),
        },
    )


def build_risk_trend(bundle: ObservationBundle) -> Optional[TrendMetric]:
    sources = [bundle.sources.get("daily_summary"), bundle.sources.get("view_model"), bundle.sources.get("prediction")]
    flattened: List[Tuple[str, float]] = []
    for src in sources:
        if src:
            flattened.extend(list(walk_numbers(src)))
    if not flattened:
        return None

    risk_like = [
        v
        for k, v in flattened
        if any(token in k.lower() for token in ["risk", "threat", "alert", "warning", "critical", "elevated"])
    ]
    current = mean(risk_like, 0.0)
    history_values = summarize_history_metric(bundle.history, ["risk", "threat", "warning", "critical", "elevated"])
    previous = mean(history_values, current * 0.9 if current else 0.0)
    confidence = 0.5 + min(0.3, abs(current - previous) * 0.6)
    rationale = f"Risk-related fields imply {risk_level_from_score(clamp(current, 0.0, 1.0))} pressure in current observation data."
    return TrendMetric(
        key="risk_trend",
        label="Risk Trend",
        current=current,
        previous=previous,
        confidence=confidence,
        rationale=rationale,
        source="daily_summary/view_model/prediction",
        tags=["risk", risk_level_from_score(clamp(current, 0.0, 1.0))],
        metadata={"risk_level": risk_level_from_score(clamp(current, 0.0, 1.0))},
    )


def build_headline_intensity_trend(bundle: ObservationBundle) -> Optional[TrendMetric]:
    payload = bundle.sources.get("daily_summary") or bundle.sources.get("view_model")
    if not payload:
        return None

    flattened = list(walk_numbers(payload))
    article_count = mean([v for k, v in flattened if any(t in k.lower() for t in ["article", "count", "headline", "highlight"])], 0.0)
    if article_count == 0.0 and not flattened:
        return None
    history_counts = summarize_history_metric(bundle.history, ["article", "count", "headline", "highlight"])
    previous = mean(history_counts, article_count * 0.9 if article_count else 0.0)
    confidence = 0.45 + min(0.25, max(article_count, previous) / 100.0)
    rationale = f"Headline intensity is estimated from current article/highlight counts ({article_count:.2f})."
    return TrendMetric(
        key="headline_intensity",
        label="Headline Intensity",
        current=article_count,
        previous=previous,
        confidence=confidence,
        rationale=rationale,
        source=Path(str(pick(payload, "__source_path__", default="observation"))).name,
        tags=["news", "intensity"],
        metadata={"article_like_count": round(article_count, 4)},
    )


def build_health_trend(bundle: ObservationBundle) -> Optional[TrendMetric]:
    payload = bundle.sources.get("health")
    if not payload:
        return None

    flattened = list(walk_numbers(payload))
    ok = mean([v for k, v in flattened if k.lower().endswith("ok") or ".ok" in k.lower()], 0.0)
    warn = mean([v for k, v in flattened if "warn" in k.lower()], 0.0)
    ng = mean([v for k, v in flattened if k.lower().endswith("ng") or ".ng" in k.lower() or "error" in k.lower()], 0.0)
    total = max(ok + warn + ng, 1.0)
    current = clamp((ok - (warn + ng)) / total, -1.0, 1.0)
    history_vals = summarize_history_metric(bundle.history, ["health", ".ok", ".warn", ".ng", "error"])
    previous = mean(history_vals, current * 0.95)
    confidence = 0.55
    rationale = f"Health posture is inferred from ok={ok:.2f}, warn={warn:.2f}, ng/error={ng:.2f}."
    return TrendMetric(
        key="health_signals",
        label="Health Signals",
        current=current,
        previous=previous,
        confidence=confidence,
        rationale=rationale,
        source="health_latest.json",
        tags=["health"],
        metadata={"ok": round(ok, 4), "warn": round(warn, 4), "ng": round(ng, 4)},
    )


def build_confidence_trend(metrics: Sequence[TrendMetric]) -> Optional[TrendMetric]:
    if not metrics:
        return None
    confidences = [m.confidence for m in metrics]
    current = mean(confidences, 0.0)
    previous = current * 0.96
    rationale = "Confidence reflects how coherent current observation-derived trends are across risk, sentiment, intensity, and health."
    return TrendMetric(
        key="confidence_trend",
        label="Confidence Trend",
        current=current,
        previous=previous,
        confidence=clamp(current, 0.0, 1.0),
        rationale=rationale,
        source="derived",
        tags=["confidence", "derived"],
        metadata={"component_count": len(metrics)},
    )


def build_composite_summary(metrics: Sequence[TrendMetric]) -> Dict[str, Any]:
    if not metrics:
        return {
            "overall_direction": "stable",
            "overall_score": 0.0,
            "overall_confidence": 0.0,
            "risk_level": "low",
            "summary": "Trend input unavailable.",
        }

    weighted_score = 0.0
    total_weight = 0.0
    for metric in metrics:
        weight = 0.7 + 0.6 * metric.confidence
        weighted_score += metric.score * weight
        total_weight += weight
    overall_score = clamp(weighted_score / max(total_weight, 1e-9), -1.0, 1.0)
    overall_confidence = clamp(mean([m.confidence for m in metrics], 0.0), 0.0, 1.0)
    overall_direction = normalize_direction(0.0, overall_score)
    risk_proxy = clamp((mean([max(0.0, m.current) for m in metrics], 0.0) + max(0.0, overall_score)) / 2.0, 0.0, 1.0)
    risk_level = risk_level_from_score(risk_proxy)

    if overall_direction == "rising":
        summary = f"Observation pressure is rising with {risk_level} risk bias."
    elif overall_direction == "falling":
        summary = f"Observation pressure is easing, though {risk_level} risk remains in view."
    elif overall_direction == "accelerating":
        summary = f"Observation pressure is accelerating and deserves closer monitoring under a {risk_level} regime."
    else:
        summary = f"Observation pressure is broadly stable with a {risk_level} risk backdrop."

    return {
        "overall_direction": overall_direction,
        "overall_score": round(overall_score, 4),
        "overall_confidence": round(overall_confidence, 4),
        "risk_level": risk_level,
        "summary": summary,
    }


def build_watchpoints(metrics: Sequence[TrendMetric]) -> List[str]:
    out: List[str] = []
    for metric in metrics:
        if metric.key == "headline_intensity" and metric.direction in {"rising", "accelerating"}:
            out.append("Headline volume is climbing; monitor whether this broadens beyond isolated events.")
        if metric.key == "sentiment_trend" and metric.current < 0:
            out.append("Negative sentiment is outweighing positive sentiment; watch for persistence into the next run.")
        if metric.key == "risk_trend" and metric.direction in {"rising", "accelerating"}:
            out.append("Risk-related fields are strengthening; confirm whether this is reflected in next-day summaries.")
        if metric.key == "health_signals" and metric.current < 0:
            out.append("Health posture is deteriorating; verify whether pipeline quality issues are influencing the observation picture.")
    if not out:
        out.append("No single watchpoint dominates yet; monitor for confirmation in the next Morning Ritual run.")
    return list(dict.fromkeys(out))[:8]


def build_drivers(metrics: Sequence[TrendMetric]) -> List[str]:
    drivers: List[str] = []
    for metric in metrics:
        drivers.append(f"{metric.label}: {metric.direction} (score={metric.score:.2f}, confidence={metric.confidence:.2f})")
    return drivers[:10]


def build_payload(bundle: ObservationBundle, horizon_days: int, history_days: int) -> Dict[str, Any]:
    metric_builders = [
        build_sentiment_trend,
        build_risk_trend,
        build_headline_intensity_trend,
        build_health_trend,
    ]

    metrics: List[TrendMetric] = []
    for fn in metric_builders:
        metric = fn(bundle)
        if metric is not None:
            metrics.append(metric)

    confidence_metric = build_confidence_trend(metrics)
    if confidence_metric is not None:
        metrics.append(confidence_metric)

    summary = build_composite_summary(metrics)
    as_of = None
    for key in ("daily_summary", "sentiment", "health", "view_model", "prediction"):
        payload = bundle.sources.get(key)
        if payload:
            as_of = pick(payload, "as_of", "date", "generated_at")
            if as_of:
                break
    if as_of is None:
        as_of = utc_now_iso()

    return {
        "version": VERSION,
        "generated_at": utc_now_iso(),
        "as_of": as_of,
        "horizon_days": horizon_days,
        "history_window_days": history_days,
        "status": "ok" if metrics else "degraded",
        "summary": summary["summary"],
        "overall_direction": summary["overall_direction"],
        "overall_score": summary["overall_score"],
        "overall_confidence": summary["overall_confidence"],
        "risk_level": summary["risk_level"],
        "metrics": {metric.key: metric.to_dict() for metric in metrics},
        "trends": [metric.to_dict() for metric in metrics],
        "drivers": build_drivers(metrics),
        "watchpoints": build_watchpoints(metrics),
        "input_sources": {
            key: pick(value, "__source_path__", default=None)
            for key, value in bundle.sources.items()
        },
        "history_sources_used": [pick(item, "__history_path__", default=None) for item in bundle.history[:history_days]],
        "notes": [
            "Trend Engine reads analysis artifacts and lightweight history to infer directionality.",
            "Confidence expresses observation coherence, not certainty of future outcomes.",
            "Schema is tolerant so upstream analysis artifacts can evolve without breaking Signal Engine.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build analysis/prediction/trend_latest.json")
    parser.add_argument("--analysis-root", default="analysis", help="Analysis root directory")
    parser.add_argument("--output", default="analysis/prediction/trend_latest.json", help="Output JSON path")
    parser.add_argument("--horizon-days", type=int, default=DEFAULT_HORIZON_DAYS, help="Prediction horizon in days")
    parser.add_argument("--history-days", type=int, default=DEFAULT_HISTORY_DAYS, help="History window length")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analysis_root = Path(args.analysis_root)
    output_path = Path(args.output)

    bundle = ObservationBundle(analysis_root)
    bundle.history = read_history_window(analysis_root, max(1, args.history_days))
    bundle.load_defaults()

    payload = build_payload(bundle, horizon_days=max(1, args.horizon_days), history_days=max(1, args.history_days))
    save_json(output_path, payload)

    print(f"[trend_engine] wrote: {output_path}")
    print(f"[trend_engine] status: {payload.get('status')}")
    print(f"[trend_engine] metrics: {len(payload.get('trends', []))}")
    print(f"[trend_engine] overall_direction: {payload.get('overall_direction')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

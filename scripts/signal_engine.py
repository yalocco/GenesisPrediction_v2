#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def find_metric(source: Dict[str, Any], *keys: str, default: float = 0.0) -> float:
    if not isinstance(source, dict):
        return default

    for key in keys:
        if key in source:
            return to_float(source.get(key), default)

    containers = [
        source.get("metrics", {}),
        source.get("trends", {}),
        source.get("summary", {}),
        source.get("overview", {}),
    ]
    for container in containers:
        if not isinstance(container, dict):
            continue
        for key in keys:
            if key in container:
                value = container.get(key)

                if isinstance(value, dict):
                    if "current" in value:
                        return to_float(value.get("current"), default)
                    if "value" in value:
                        return to_float(value.get("value"), default)
                    if "score" in value:
                        return to_float(value.get("score"), default)

                return to_float(value, default)

    for list_key in ("metrics", "signals", "items"):
        items = source.get(list_key)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("key") or item.get("metric") or "").lower()
            for key in keys:
                if name == key.lower():
                    value = item.get("value", item.get("current", item.get("score")))
                    return to_float(value, default)

    return default


def find_direction(source: Dict[str, Any], *keys: str, default: str = "stable") -> str:
    if not isinstance(source, dict):
        return default

    candidates: List[Any] = []
    for key in keys:
        if key in source:
            candidates.append(source.get(key))

    for container_key in ("trends", "summary", "overview"):
        container = source.get(container_key)
        if isinstance(container, dict):
            for key in keys:
                if key in container:
                    candidates.append(container.get(key))

    for value in candidates:
        text = str(value).strip().lower()
        if text in {"rising", "up", "increase", "increasing", "accelerating"}:
            return "rising"
        if text in {"falling", "down", "decrease", "decreasing"}:
            return "falling"
        if text in {"stable", "flat", "neutral", "sideways"}:
            return "stable"

    return default


def signal_item(
    key: str,
    level: str,
    score: float,
    confidence: float,
    rationale: str,
    watchpoint: str,
    details: Dict[str, Any],
    tags: List[str],
) -> Dict[str, Any]:
    return {
        "key": key,
        "level": level,
        "score": round(score, 4),
        "confidence": round(confidence, 4),
        "rationale": rationale,
        "watchpoint": watchpoint,
        "details": details,
        "tags": unique_preserve_order([normalize_text(x) for x in tags if normalize_text(x)]),
    }


def classify_level(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def collect_trend_tags(trend: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    raw_tags = trend.get("trend_tags", [])
    if isinstance(raw_tags, list):
        tags.extend(normalize_text(x) for x in raw_tags if normalize_text(x))

    trends = trend.get("trends", [])
    if isinstance(trends, list):
        for item in trends:
            if not isinstance(item, dict):
                continue
            item_tags = item.get("tags", [])
            if isinstance(item_tags, list):
                tags.extend(normalize_text(x) for x in item_tags if normalize_text(x))
            key = normalize_text(item.get("key"))
            direction = normalize_text(item.get("direction"))
            if key and direction:
                tags.append(f"{key}_{direction}")

    return unique_preserve_order(tags)


def derive_historical_tags(
    trend_tags: List[str],
    overall_direction: str,
    risk_norm: float,
    intensity_norm: float,
    health_norm: float,
    confidence_norm: float,
    sentiment_norm: float,
) -> List[str]:
    tags: List[str] = []

    if risk_norm >= 0.68:
        tags.extend(["geopolitical_risk", "market_stress", "regime_shift_pressure"])
    elif risk_norm >= 0.48:
        tags.extend(["guarded_risk", "risk_pressure"])

    if intensity_norm >= 0.60:
        tags.extend(["headline_pressure", "event_density_rising"])

    if health_norm <= 0.35:
        tags.extend(["pipeline_stress", "health_deterioration"])

    if confidence_norm <= 0.45:
        tags.extend(["confidence_weak", "uncertainty_rising"])
    elif confidence_norm >= 0.70:
        tags.append("confidence_strong")

    if sentiment_norm <= 0.35:
        tags.extend(["negative_sentiment", "risk_off"])
    elif sentiment_norm >= 0.65:
        tags.extend(["positive_sentiment", "risk_on"])

    if overall_direction == "rising":
        tags.append("pressure_rising")
    elif overall_direction == "falling":
        tags.append("pressure_easing")

    if "geopolitical_risk" in trend_tags and intensity_norm >= 0.60:
        tags.extend(["military_escalation", "trade_fragmentation"])
    if "market_stress" in trend_tags or "risk_pressure" in trend_tags:
        tags.extend(["currency_instability", "banking_stress"])
    if "headline_pressure" in trend_tags and "negative_sentiment" in trend_tags:
        tags.append("social_unrest")
    if "event_density_rising" in trend_tags and "risk_pressure" in trend_tags:
        tags.append("systemic_stress")

    tags.extend(
        x for x in trend_tags
        if x in {
            "geopolitical_risk",
            "market_stress",
            "negative_sentiment",
            "pipeline_stress",
            "risk_pressure",
            "regime_shift_pressure",
            "headline_pressure",
        }
    )

    return unique_preserve_order(tags)


def build_signals(trend: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    overall_direction = find_direction(trend, "overall_direction")
    sentiment_score = find_metric(trend, "sentiment_score", "sentiment_trend_score", "sentiment", default=0.0)
    risk_score = find_metric(trend, "risk_score", "risk_trend_score", "risk", "risk_trend", default=0.0)
    intensity_score = find_metric(trend, "headline_intensity", "headline_intensity_score", "intensity_score", default=0.0)
    health_score = find_metric(trend, "health_score", "health_signal_score", "health", "health_signals", default=0.0)
    confidence_score = find_metric(trend, "confidence_score", "confidence_trend_score", "confidence", "confidence_trend", default=0.5)

    sentiment_norm = clamp((sentiment_score + 1.0) / 2.0, 0.0, 1.0) if sentiment_score < 0 or sentiment_score > 1 else clamp(sentiment_score, 0.0, 1.0)
    risk_norm = clamp(risk_score, 0.0, 1.0)
    intensity_norm = clamp(intensity_score, 0.0, 1.0)
    health_norm = clamp(health_score, 0.0, 1.0)
    confidence_norm = clamp(confidence_score, 0.0, 1.0)

    trend_tags = collect_trend_tags(trend)
    historical_tags = derive_historical_tags(
        trend_tags=trend_tags,
        overall_direction=overall_direction,
        risk_norm=risk_norm,
        intensity_norm=intensity_norm,
        health_norm=health_norm,
        confidence_norm=confidence_norm,
        sentiment_norm=sentiment_norm,
    )

    regime_shift = clamp((risk_norm * 0.45) + (intensity_norm * 0.35) + ((1.0 - confidence_norm) * 0.20), 0.0, 1.0)
    stress_build = clamp((risk_norm * 0.50) + ((1.0 - health_norm) * 0.25) + (intensity_norm * 0.25), 0.0, 1.0)
    stabilization = clamp(((1.0 - risk_norm) * 0.40) + (confidence_norm * 0.35) + ((1.0 - intensity_norm) * 0.25), 0.0, 1.0)
    opportunity = clamp((sentiment_norm * 0.45) + ((1.0 - risk_norm) * 0.30) + (confidence_norm * 0.25), 0.0, 1.0)

    signals = [
        signal_item(
            key="regime_shift_risk",
            level=classify_level(regime_shift),
            score=regime_shift,
            confidence=max(0.35, confidence_norm),
            rationale=f"Risk={risk_norm:.2f}, intensity={intensity_norm:.2f}, confidence_inverse={(1.0 - confidence_norm):.2f} suggest regime-shift pressure.",
            watchpoint="Monitor whether risk and headline intensity continue rising together for multiple days.",
            details={
                "overall_direction": overall_direction,
                "risk_score": round(risk_norm, 4),
                "headline_intensity": round(intensity_norm, 4),
                "confidence_inverse": round(1.0 - confidence_norm, 4),
            },
            tags=[
                "regime_shift_risk",
                classify_level(regime_shift),
                "regime_shift_pressure",
                "risk_pressure" if risk_norm >= 0.48 else "",
                "headline_pressure" if intensity_norm >= 0.60 else "",
                "military_escalation" if "geopolitical_risk" in historical_tags and intensity_norm >= 0.60 else "",
                "trade_fragmentation" if risk_norm >= 0.60 else "",
            ],
        ),
        signal_item(
            key="stress_building",
            level=classify_level(stress_build),
            score=stress_build,
            confidence=max(0.35, confidence_norm),
            rationale=f"Stress combines risk={risk_norm:.2f}, health_inverse={(1.0 - health_norm):.2f}, intensity={intensity_norm:.2f}.",
            watchpoint="Check health degradation, missing inputs, and rising volatility in the upstream observation layer.",
            details={
                "risk_score": round(risk_norm, 4),
                "health_inverse": round(1.0 - health_norm, 4),
                "headline_intensity": round(intensity_norm, 4),
            },
            tags=[
                "stress_building",
                classify_level(stress_build),
                "systemic_stress",
                "market_stress" if risk_norm >= 0.50 else "",
                "banking_stress" if risk_norm >= 0.60 else "",
                "currency_instability" if risk_norm >= 0.55 else "",
                "pipeline_stress" if health_norm <= 0.35 else "",
                "social_unrest" if sentiment_norm <= 0.35 and intensity_norm >= 0.50 else "",
            ],
        ),
        signal_item(
            key="stabilization_bias",
            level=classify_level(stabilization),
            score=stabilization,
            confidence=max(0.35, confidence_norm),
            rationale="Lower risk and lower intensity with stronger confidence point toward stabilization.",
            watchpoint="Invalidated if risk re-accelerates or confidence drops sharply.",
            details={
                "risk_inverse": round(1.0 - risk_norm, 4),
                "confidence_score": round(confidence_norm, 4),
                "intensity_inverse": round(1.0 - intensity_norm, 4),
            },
            tags=[
                "stabilization_bias",
                classify_level(stabilization),
                "stabilization",
                "confidence_strong" if confidence_norm >= 0.70 else "",
                "pressure_easing" if overall_direction == "falling" else "",
            ],
        ),
        signal_item(
            key="opportunity_window",
            level=classify_level(opportunity),
            score=opportunity,
            confidence=max(0.35, confidence_norm),
            rationale=f"Opportunity rises when sentiment={sentiment_norm:.2f}, confidence={confidence_norm:.2f}, and risk is contained.",
            watchpoint="Watch for sentiment reversals or renewed escalation in risk headlines.",
            details={
                "sentiment_score": round(sentiment_norm, 4),
                "risk_inverse": round(1.0 - risk_norm, 4),
                "confidence_score": round(confidence_norm, 4),
            },
            tags=[
                "opportunity_window",
                classify_level(opportunity),
                "risk_on" if sentiment_norm >= 0.65 else "",
                "constructive_bias" if opportunity >= 0.55 else "",
            ],
        ),
    ]

    top_signal = max(signals, key=lambda x: x["score"]) if signals else {}
    dominant_signals = [item["key"] for item in sorted(signals, key=lambda x: x["score"], reverse=True)[:2]]

    top_level_watchpoints = unique_preserve_order(
        [normalize_text(item.get("watchpoint")) for item in signals if item.get("watchpoint")]
        + [
            "escalating_risk_intensity_alignment" if regime_shift >= 0.60 else "",
            "health_degradation" if health_norm <= 0.35 else "",
            "confidence_breakdown" if confidence_norm <= 0.45 else "",
            "headline_pressure" if intensity_norm >= 0.60 else "",
        ]
    )
    top_level_watchpoints = [x for x in top_level_watchpoints if x][:10]

    signal_tags = unique_preserve_order(
        [tag for item in signals for tag in item.get("tags", [])]
        + trend_tags
        + historical_tags
    )

    early_warning_score = clamp(max(regime_shift, stress_build), 0.0, 1.0)
    early_warning_level = "warn" if early_warning_score >= 0.60 else "watch" if early_warning_score >= 0.40 else "normal"

    early_warning = {
        "status": "ok",
        "generated_at": utc_now_iso(),
        "warning_level": early_warning_level,
        "warning_score": round(early_warning_score, 4),
        "dominant_driver": "regime_shift_risk" if regime_shift >= stress_build else "stress_building",
        "watchpoints": top_level_watchpoints[:5],
    }

    extras = {
        "top_signal": top_signal.get("key", "none"),
        "dominant_signals": dominant_signals,
        "watchpoints": top_level_watchpoints,
        "signal_tags": signal_tags,
        "historical_tags": historical_tags,
        "trend_tags_used": trend_tags,
        "risk": "high" if max(regime_shift, stress_build) >= 0.75 else "guarded" if max(regime_shift, stress_build) >= 0.45 else "stable",
    }

    return signals, early_warning, extras


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate signal and early warning outputs from trend_latest.json")
    parser.add_argument("--analysis-root", default="analysis", help="Analysis root directory")
    parser.add_argument("--trend-input", default=None, help="Optional explicit trend input path")
    parser.add_argument("--signal-output", default=None, help="Optional explicit signal output path")
    parser.add_argument("--early-warning-output", default=None, help="Optional explicit early warning output path")
    args = parser.parse_args()

    analysis_root = Path(args.analysis_root)
    prediction_dir = analysis_root / "prediction"
    ensure_dir(prediction_dir)

    trend_input = Path(args.trend_input) if args.trend_input else prediction_dir / "trend_latest.json"
    signal_output = Path(args.signal_output) if args.signal_output else prediction_dir / "signal_latest.json"
    early_warning_output = Path(args.early_warning_output) if args.early_warning_output else prediction_dir / "early_warning_latest.json"

    trend = load_json(trend_input)
    signals, early_warning, extras = build_signals(trend)

    payload = {
        "status": "ok" if trend else "degraded",
        "generated_at": utc_now_iso(),
        "as_of": trend.get("as_of"),
        "source": str(trend_input).replace("\\", "/"),
        "signal_count": len(signals),
        "signals": signals,
        "signal_tags": extras["signal_tags"],
        "historical_tags": extras["historical_tags"],
        "trend_tags_used": extras["trend_tags_used"],
        "dominant_signals": extras["dominant_signals"],
        "watchpoints": extras["watchpoints"],
        "risk": extras["risk"],
        "summary": {
            "top_signal": extras["top_signal"],
            "overall_signal_bias": "risk_off" if any(s["key"] == "regime_shift_risk" and s["score"] >= 0.60 for s in signals) else "mixed",
        },
    }

    signal_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    early_warning_output.write_text(json.dumps(early_warning, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[signal_engine] wrote {signal_output}")
    print(f"[signal_engine] wrote {early_warning_output}")
    print(f"[signal_engine] signals={len(signals)}")
    print(f"[signal_engine] top_signal={payload['summary']['top_signal']}")
    print(f"[signal_engine] signal_tags={len(payload.get('signal_tags', []))}")


if __name__ == "__main__":
    main()
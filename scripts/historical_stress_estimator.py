#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def collect_tags(signal_data: Dict[str, Any], trend_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    for key in ("signal_tags", "historical_tags", "trend_tags_used", "watchpoints", "dominant_signals"):
        value = signal_data.get(key)
        if isinstance(value, list):
            tags.extend(normalize_text(x) for x in value if normalize_text(x))

    for key in ("trend_tags", "watchpoints", "drivers"):
        value = trend_data.get(key)
        if isinstance(value, list):
            tags.extend(normalize_text(x) for x in value if normalize_text(x))

    trends = trend_data.get("trends", [])
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

    return unique_preserve_order([x for x in tags if x])


def get_signal_score(signal_data: Dict[str, Any], key: str, default: float = 0.0) -> float:
    signals = signal_data.get("signals", [])
    if not isinstance(signals, list):
        return default
    for item in signals:
        if not isinstance(item, dict):
            continue
        if normalize_text(item.get("key")) == normalize_text(key):
            return clamp01(to_float(item.get("score"), default))
    return default


def get_trend_metric_current(trend_data: Dict[str, Any], key: str, default: float = 0.0) -> float:
    metrics = trend_data.get("metrics", {})
    if isinstance(metrics, dict):
        metric = metrics.get(key)
        if isinstance(metric, dict):
            if "current" in metric:
                return to_float(metric.get("current"), default)
            if "value" in metric:
                return to_float(metric.get("value"), default)
            if "score" in metric:
                return to_float(metric.get("score"), default)

    trends = trend_data.get("trends", [])
    if isinstance(trends, list):
        for item in trends:
            if not isinstance(item, dict):
                continue
            if normalize_text(item.get("key")) == normalize_text(key):
                if "current" in item:
                    return to_float(item.get("current"), default)
                if "value" in item:
                    return to_float(item.get("value"), default)
                if "score" in item:
                    return to_float(item.get("score"), default)

    return default


def derive_stress_vector(signal_data: Dict[str, Any], trend_data: Dict[str, Any]) -> Dict[str, float]:
    tags = set(collect_tags(signal_data, trend_data))

    regime_shift_score = get_signal_score(signal_data, "regime_shift_risk", 0.0)
    stress_build_score = get_signal_score(signal_data, "stress_building", 0.0)
    stabilization_score = get_signal_score(signal_data, "stabilization_bias", 0.0)

    risk_current = clamp01(get_trend_metric_current(trend_data, "risk_trend", 0.0))
    sentiment_current = get_trend_metric_current(trend_data, "sentiment_trend", 0.0)
    headline_current = clamp01(get_trend_metric_current(trend_data, "headline_intensity", 0.0))
    health_current = get_trend_metric_current(trend_data, "health_signals", 0.0)
    confidence_current = clamp01(get_trend_metric_current(trend_data, "confidence_trend", 0.5))

    # normalize trend-derived helpers
    sentiment_negative = clamp01(max(0.0, -sentiment_current))
    health_inverse = clamp01((1.0 - health_current) / 2.0 if health_current < 0 else 1.0 - clamp01(health_current))
    uncertainty = clamp01(1.0 - confidence_current)

    vector = {
        "food_stress": 0.0,
        "energy_stress": 0.0,
        "fiscal_stress": 0.0,
        "currency_stress": 0.0,
        "trade_stress": 0.0,
        "political_stress": 0.0,
        "military_stress": 0.0,
        "social_unrest_stress": 0.0,
    }

    def raise_to(key: str, value: float) -> None:
        vector[key] = max(vector[key], clamp01(value))

    # Base stress from signal/trend dynamics
    base_risk = max(regime_shift_score, stress_build_score, risk_current)
    base_systemic = max(stress_build_score, uncertainty)

    # Food stress
    if {"food_stress", "grain", "food", "famine", "drought"} & tags:
        raise_to("food_stress", 0.70)
    if {"negative_sentiment", "systemic_stress"} <= tags:
        raise_to("food_stress", 0.25)
    if "headline_pressure" in tags and "risk_pressure" in tags:
        raise_to("food_stress", 0.20)

    # Energy stress
    if {"energy", "oil", "gas", "power", "energy_shock"} & tags:
        raise_to("energy_stress", 0.75)
    if "military_escalation" in tags or "trade_fragmentation" in tags:
        raise_to("energy_stress", 0.35)

    # Fiscal stress
    if {"fiscal_stress", "debt", "bailout", "budget", "policy_liquidity"} & tags:
        raise_to("fiscal_stress", 0.70)
    if "banking_stress" in tags:
        raise_to("fiscal_stress", 0.45)
    raise_to("fiscal_stress", base_systemic * 0.35)

    # Currency stress
    if "currency_instability" in tags:
        raise_to("currency_stress", 0.80)
    if {"devaluation", "fx", "reserve", "capital_flight"} & tags:
        raise_to("currency_stress", 0.70)
    if "banking_stress" in tags:
        raise_to("currency_stress", 0.45)

    # Trade stress
    if "trade_fragmentation" in tags:
        raise_to("trade_stress", 0.80)
    if {"headline_pressure", "event_density_rising"} <= tags:
        raise_to("trade_stress", 0.40)
    if {"shipping", "port", "sanction", "trade_disruption"} & tags:
        raise_to("trade_stress", 0.75)

    # Political stress
    if {"regime_shift_pressure", "risk_pressure"} & tags:
        raise_to("political_stress", 0.65)
    if "guarded_risk" in tags:
        raise_to("political_stress", 0.45)
    if "pressure_easing" in tags and stabilization_score >= 0.70:
        raise_to("political_stress", 0.20)

    # Military stress
    if "military_escalation" in tags:
        raise_to("military_stress", 0.85)
    if {"geopolitical_risk", "trade_fragmentation"} & tags:
        raise_to("military_stress", 0.45)

    # Social unrest stress
    if "social_unrest" in tags:
        raise_to("social_unrest_stress", 0.80)
    if {"negative_sentiment", "risk_off"} & tags:
        raise_to("social_unrest_stress", 0.45)
    if "pipeline_stress" in tags:
        raise_to("social_unrest_stress", 0.20)
    raise_to("social_unrest_stress", sentiment_negative * 0.50)

    # Cross-domain boosts
    if "banking_stress" in tags and "currency_instability" in tags:
        raise_to("fiscal_stress", 0.60)
        raise_to("currency_stress", 0.85)
        raise_to("trade_stress", 0.35)

    if "headline_pressure" in tags and "risk_pressure" in tags:
        raise_to("political_stress", 0.70)
        raise_to("social_unrest_stress", 0.50)

    if "pipeline_stress" in tags:
        raise_to("fiscal_stress", 0.30)
        raise_to("political_stress", 0.30)

    # fallback from broad risk dynamics
    raise_to("political_stress", base_risk * 0.50)
    raise_to("currency_stress", base_systemic * 0.25)
    raise_to("trade_stress", headline_current * 0.30)

    return {k: round(clamp01(v), 4) for k, v in vector.items()}


def dominant_dimensions(vector: Dict[str, float], top_k: int = 3) -> List[str]:
    ranked = sorted(vector.items(), key=lambda kv: kv[1], reverse=True)
    return [k for k, v in ranked[:top_k] if v > 0]


def build_payload(signal_data: Dict[str, Any], trend_data: Dict[str, Any]) -> Dict[str, Any]:
    vector = derive_stress_vector(signal_data, trend_data)
    dominant = dominant_dimensions(vector, top_k=4)
    average_stress = round(sum(vector.values()) / len(vector), 4) if vector else 0.0
    peak_stress = round(max(vector.values()) if vector else 0.0, 4)

    return {
        "status": "ok",
        "generated_at": utc_now_iso(),
        "as_of": signal_data.get("as_of") or trend_data.get("as_of"),
        "source": {
            "signal": signal_data.get("source", "analysis/prediction/signal_latest.json"),
            "trend": "analysis/prediction/trend_latest.json",
        },
        "stress_vector": vector,
        "dominant_dimensions": dominant,
        "average_stress": average_stress,
        "peak_stress": peak_stress,
        "summary": (
            f"Dominant stress dimensions are {', '.join(dominant)}."
            if dominant
            else "No dominant stress dimension detected."
        ),
        "notes": [
            "This artifact estimates a normalized historical stress vector from signal and trend tags.",
            "Values are heuristic and intended for Historical Pattern matching, not direct UI calculation.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate historical stress vector from trend and signal outputs")
    parser.add_argument("--analysis-root", default="analysis", help="Analysis root directory")
    parser.add_argument("--signal-input", default=None, help="Optional signal_latest.json path")
    parser.add_argument("--trend-input", default=None, help="Optional trend_latest.json path")
    parser.add_argument("--output", default=None, help="Optional output path")
    args = parser.parse_args()

    analysis_root = Path(args.analysis_root)
    prediction_dir = analysis_root / "prediction"

    signal_input = Path(args.signal_input) if args.signal_input else prediction_dir / "signal_latest.json"
    trend_input = Path(args.trend_input) if args.trend_input else prediction_dir / "trend_latest.json"
    output = Path(args.output) if args.output else prediction_dir / "historical_stress_latest.json"

    signal_data = load_json(signal_input)
    trend_data = load_json(trend_input)

    payload = build_payload(signal_data, trend_data)
    write_json(output, payload)

    print(f"[historical_stress_estimator] wrote {output}")
    print(f"[historical_stress_estimator] dominant_dimensions={payload.get('dominant_dimensions')}")
    print(f"[historical_stress_estimator] peak_stress={payload.get('peak_stress')}")


if __name__ == "__main__":
    main()
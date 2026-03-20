#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"

TREND_LATEST_PATH = PREDICTION_DIR / "trend_latest.json"
SIGNAL_LATEST_PATH = PREDICTION_DIR / "signal_latest.json"
HISTORICAL_PATTERN_LATEST_PATH = PREDICTION_DIR / "historical_pattern_latest.json"
HISTORICAL_ANALOG_LATEST_PATH = PREDICTION_DIR / "historical_analog_latest.json"
SCENARIO_LATEST_PATH = PREDICTION_DIR / "scenario_latest.json"

PREDICTION_LATEST_PATH = PREDICTION_DIR / "prediction_latest.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def unique_preserve_order(items: List[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def extract_memory_summary(scenario_data: Dict[str, Any]) -> str:
    reference_memory = scenario_data.get("reference_memory", {})
    if not isinstance(reference_memory, dict):
        return ""
    return str(reference_memory.get("summary") or "").strip()


def extract_memory_status(scenario_data: Dict[str, Any]) -> str:
    reference_memory = scenario_data.get("reference_memory", {})
    if not isinstance(reference_memory, dict):
        return "unavailable"
    return str(reference_memory.get("status") or "unavailable").strip()


def extract_scenario_map(scenario_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    scenarios = scenario_data.get("scenarios", [])
    if not isinstance(scenarios, list):
        return out

    for item in scenarios:
        if not isinstance(item, dict):
            continue
        scenario_id = normalize_text(item.get("scenario_id"))
        if scenario_id:
            out[scenario_id] = item
    return out


def choose_primary_narrative(scenario_data: Dict[str, Any]) -> str:
    dominant = normalize_text(scenario_data.get("dominant_scenario"))
    scenario_map = extract_scenario_map(scenario_data)
    selected = scenario_map.get(dominant)
    if isinstance(selected, dict) and selected.get("narrative"):
        return str(selected.get("narrative"))
    summary = scenario_data.get("summary")
    if summary:
        return str(summary)
    return "No scenario narrative available."


def compute_historical_support_level(
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
) -> float:
    pattern_conf = safe_float(pattern_data.get("pattern_confidence"))
    analog_conf = safe_float(analog_data.get("analog_confidence"))
    support = 0.65 * pattern_conf + 0.35 * analog_conf
    return round(clamp01(support), 4)


def collect_signal_tags(signal_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    for key in ("signal_tags", "historical_tags", "trend_tags_used", "dominant_signals", "watchpoints"):
        value = signal_data.get(key)
        if isinstance(value, list):
            tags.extend(normalize_text(x) for x in value if normalize_text(x))

    signals = signal_data.get("signals", [])
    if isinstance(signals, list):
        for item in signals:
            if not isinstance(item, dict):
                continue
            key = normalize_text(item.get("key"))
            if key:
                tags.append(key)
            item_tags = item.get("tags", [])
            if isinstance(item_tags, list):
                tags.extend(normalize_text(x) for x in item_tags if normalize_text(x))

    return unique_preserve_order([x for x in tags if x])


def collect_trend_tags(trend_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    raw_tags = trend_data.get("trend_tags", [])
    if isinstance(raw_tags, list):
        tags.extend(normalize_text(x) for x in raw_tags if normalize_text(x))

    trends = trend_data.get("trends", [])
    if isinstance(trends, list):
        for item in trends:
            if not isinstance(item, dict):
                continue
            key = normalize_text(item.get("key"))
            direction = normalize_text(item.get("direction"))
            if key and direction:
                tags.append(f"{key}_{direction}")
            item_tags = item.get("tags", [])
            if isinstance(item_tags, list):
                tags.extend(normalize_text(x) for x in item_tags if normalize_text(x))

    return unique_preserve_order([x for x in tags if x])


def classify_prediction_direction(
    scenario_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
) -> str:
    dominant = normalize_text(scenario_data.get("dominant_scenario"))
    risk = normalize_text(scenario_data.get("risk"))
    dominant_pattern = normalize_text(pattern_data.get("dominant_pattern"))

    signal_tags = set(collect_signal_tags(signal_data))

    if dominant == "worst_case":
        return "deteriorating"
    if dominant == "best_case":
        return "stabilizing"

    stress_keywords = {
        "war",
        "military",
        "sanction",
        "debt",
        "bank",
        "currency",
        "drought",
        "flood",
        "pandemic",
        "trade",
        "unrest",
        "banking_stress",
        "currency_instability",
        "risk_pressure",
        "systemic_stress",
    }

    if risk in {"critical", "high", "guarded"} and (signal_tags & stress_keywords):
        return "guarded_deterioration"

    if dominant_pattern:
        return "historically_guarded"

    return "stable_to_guarded"


def build_prediction_statement(
    dominant_scenario: str,
    risk: str,
    direction: str,
    confidence: float,
    dominant_pattern: str,
    dominant_analog: str,
    memory_summary: str,
) -> str:
    sentence = (
        f"Primary outlook is {dominant_scenario} with {risk} risk and "
        f"{direction} directional bias at confidence {confidence:.2f}."
    )

    if dominant_pattern and dominant_analog:
        sentence += (
            f" Historical support is led by pattern {dominant_pattern} "
            f"and analog {dominant_analog}."
        )
    elif dominant_pattern:
        sentence += f" Historical support is led by pattern {dominant_pattern}."
    elif dominant_analog:
        sentence += f" Historical support is led by analog {dominant_analog}."

    if memory_summary:
        sentence += f" Memory context: {memory_summary}."

    return sentence


def build_action_bias(
    scenario_data: Dict[str, Any],
    expected_outcomes: List[str],
    historical_support_level: float,
) -> str:
    dominant = normalize_text(scenario_data.get("dominant_scenario"))
    risk = normalize_text(scenario_data.get("risk"))
    outcomes = set(normalize_text(x) for x in expected_outcomes)
    memory_summary = normalize_text(extract_memory_summary(scenario_data))

    # Memory is support-only, but crisis-pattern recall should harden bias.
    if "financial_crisis" in memory_summary or "banking_crisis" in memory_summary:
        return "defensive"

    if dominant == "worst_case":
        return "defensive"
    if dominant == "best_case" and risk in {"stable", "low"}:
        return "constructive"
    if {"currency_down", "currency_sharp_down", "trade_disruption", "energy_up", "commodity_up", "credit_spreads_up"} & outcomes:
        return "guarded"
    if historical_support_level >= 0.7:
        return "guarded"
    return "balanced"


def build_monitoring_priorities(
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
) -> List[str]:
    priorities: List[str] = []

    for item in scenario_data.get("watchpoints", [])[:6]:
        if item is not None:
            priorities.append(normalize_text(item))

    historical_context = scenario_data.get("historical_context", {})
    if isinstance(historical_context, dict):
        for item in historical_context.get("historical_watchpoints", [])[:6]:
            if item is not None:
                priorities.append(normalize_text(item))

    matched_patterns = pattern_data.get("matched_patterns", [])
    if isinstance(matched_patterns, list):
        for item in matched_patterns[:2]:
            if isinstance(item, dict):
                for wp in item.get("watchpoints", [])[:3]:
                    if wp is not None:
                        priorities.append(normalize_text(wp))

    top_analogs = analog_data.get("top_analogs", [])
    if isinstance(top_analogs, list):
        for item in top_analogs[:2]:
            if isinstance(item, dict):
                for wp in item.get("watchpoints", [])[:3]:
                    if wp is not None:
                        priorities.append(normalize_text(wp))
                for sim in item.get("similarities", [])[:2]:
                    if sim is not None:
                        priorities.append(normalize_text(sim))

    return unique_preserve_order([x for x in priorities if x])[:12]


def build_prediction_drivers(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
) -> List[str]:
    drivers: List[str] = []

    drivers.extend(collect_trend_tags(trend_data)[:5])
    drivers.extend(collect_signal_tags(signal_data)[:6])

    for item in scenario_data.get("key_drivers", [])[:6]:
        if item is not None:
            drivers.append(normalize_text(item))

    dominant_pattern = pattern_data.get("dominant_pattern")
    dominant_analog = analog_data.get("dominant_analog")
    if dominant_pattern:
        drivers.append(f"historical_pattern:{normalize_text(dominant_pattern)}")
    if dominant_analog:
        drivers.append(f"historical_analog:{normalize_text(dominant_analog)}")

    memory_summary = extract_memory_summary(scenario_data)
    if memory_summary:
        drivers.append(f"memory:{normalize_text(memory_summary)}")

    return unique_preserve_order([x for x in drivers if x])[:14]


def build_historical_context(
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
) -> Dict[str, Any]:
    support_level = compute_historical_support_level(pattern_data, analog_data)

    dominant_pattern = pattern_data.get("dominant_pattern")
    dominant_analog = analog_data.get("dominant_analog")

    summary_parts: List[str] = []

    if dominant_pattern:
        summary_parts.append(f"dominant pattern is {dominant_pattern}")
    if dominant_analog:
        summary_parts.append(f"dominant analog is {dominant_analog}")

    if support_level >= 0.75:
        summary_parts.append("historical support is strong")
    elif support_level >= 0.5:
        summary_parts.append("historical support is moderate")
    else:
        summary_parts.append("historical support is limited")

    summary = ". ".join(summary_parts).strip()
    if summary:
        summary += "."
    else:
        summary = "No historical context available."

    historical_context = scenario_data.get("historical_context", {})
    current_stress_vector = {}
    if isinstance(historical_context, dict):
        csv = historical_context.get("current_stress_vector", {})
        if isinstance(csv, dict):
            current_stress_vector = {str(k): round(clamp01(safe_float(v)), 4) for k, v in csv.items()}

    return {
        "dominant_pattern": dominant_pattern,
        "pattern_confidence": round(safe_float(pattern_data.get("pattern_confidence")), 4),
        "dominant_analog": dominant_analog,
        "analog_confidence": round(safe_float(analog_data.get("analog_confidence")), 4),
        "support_level": support_level,
        "current_stress_vector": current_stress_vector,
        "summary": summary,
    }


def calculate_prediction_confidence(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
) -> float:
    trend_conf = safe_float(trend_data.get("overall_confidence", trend_data.get("confidence", 0.0)))

    signal_conf = 0.0
    signals = signal_data.get("signals", [])
    if isinstance(signals, list) and signals:
        signal_conf = sum(
            safe_float(item.get("confidence", 0.0))
            for item in signals
            if isinstance(item, dict)
        ) / len(signals)

    scenario_conf = safe_float(scenario_data.get("confidence", 0.0))
    pattern_conf = safe_float(pattern_data.get("pattern_confidence", 0.0))
    analog_conf = safe_float(analog_data.get("analog_confidence", 0.0))

    confidence = (
        0.15 * trend_conf
        + 0.20 * signal_conf
        + 0.40 * scenario_conf
        + 0.15 * pattern_conf
        + 0.10 * analog_conf
    )

    # Mild support-only boost when memory recall is healthy and non-empty.
    memory_status = normalize_text(extract_memory_status(scenario_data))
    memory_summary = extract_memory_summary(scenario_data)
    if memory_status == "ok" and memory_summary:
        confidence += 0.05

    return round(clamp01(confidence), 4)


def build_summary(
    direction: str,
    dominant_scenario: str,
    risk: str,
    confidence: float,
    historical_context: Dict[str, Any],
    memory_summary: str,
) -> str:
    base = (
        f"Prediction is {direction}. "
        f"Dominant scenario is {dominant_scenario}. "
        f"Risk is {risk}. "
        f"Confidence is {confidence:.2f}."
    )

    historical_summary = historical_context.get("summary")
    if historical_summary:
        base += f" {historical_summary}"

    if memory_summary:
        base += f" Memory context: {memory_summary}"

    return base


def build_prediction_output(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
) -> Dict[str, Any]:
    as_of = (
        scenario_data.get("as_of")
        or signal_data.get("as_of")
        or trend_data.get("as_of")
        or pattern_data.get("as_of")
        or analog_data.get("as_of")
        or today_str()
    )

    dominant_scenario = normalize_text(scenario_data.get("dominant_scenario")) or "base_case"
    risk = normalize_text(scenario_data.get("risk")) or "guarded"
    memory_summary = extract_memory_summary(scenario_data)

    historical_context = build_historical_context(
        pattern_data=pattern_data,
        analog_data=analog_data,
        scenario_data=scenario_data,
    )

    direction = classify_prediction_direction(
        scenario_data=scenario_data,
        signal_data=signal_data,
        pattern_data=pattern_data,
    )

    confidence = calculate_prediction_confidence(
        trend_data=trend_data,
        signal_data=signal_data,
        scenario_data=scenario_data,
        pattern_data=pattern_data,
        analog_data=analog_data,
    )

    expected_outcomes = scenario_data.get("expected_outcomes", [])
    if not isinstance(expected_outcomes, list):
        expected_outcomes = []

    monitoring_priorities = build_monitoring_priorities(
        scenario_data=scenario_data,
        pattern_data=pattern_data,
        analog_data=analog_data,
    )

    action_bias = build_action_bias(
        scenario_data=scenario_data,
        expected_outcomes=expected_outcomes,
        historical_support_level=safe_float(historical_context.get("support_level")),
    )

    primary_narrative = choose_primary_narrative(scenario_data)

    prediction_statement = build_prediction_statement(
        dominant_scenario=dominant_scenario,
        risk=risk,
        direction=direction,
        confidence=confidence,
        dominant_pattern=str(historical_context.get("dominant_pattern") or ""),
        dominant_analog=str(historical_context.get("dominant_analog") or ""),
        memory_summary=memory_summary,
    )

    prediction_drivers = build_prediction_drivers(
        trend_data=trend_data,
        signal_data=signal_data,
        scenario_data=scenario_data,
        pattern_data=pattern_data,
        analog_data=analog_data,
    )

    summary = build_summary(
        direction=direction,
        dominant_scenario=dominant_scenario,
        risk=risk,
        confidence=confidence,
        historical_context=historical_context,
        memory_summary=memory_summary,
    )

    return {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "engine_version": "v3_memory_integrated",
        "direction": direction,
        "dominant_scenario": dominant_scenario,
        "risk": risk,
        "confidence": confidence,
        "action_bias": action_bias,
        "prediction_statement": prediction_statement,
        "primary_narrative": primary_narrative,
        "key_drivers": prediction_drivers,
        "monitoring_priorities": monitoring_priorities,
        "expected_outcomes": expected_outcomes[:10],
        "risk_flags": scenario_data.get("risk_flags", []),
        "historical_context": historical_context,
        "scenario_bias": scenario_data.get("scenario_bias", {}),
        "reference_memory": scenario_data.get("reference_memory", {}),
        "summary": summary,
    }


def save_history(prediction_output: Dict[str, Any]) -> None:
    as_of = str(prediction_output.get("as_of") or datetime.now().strftime("%Y-%m-%d"))
    history_dir = PREDICTION_DIR / "history" / as_of
    write_json(history_dir / "prediction.json", prediction_output)


def main() -> None:
    trend_data = load_json(TREND_LATEST_PATH)
    signal_data = load_json(SIGNAL_LATEST_PATH)
    scenario_data = load_json(SCENARIO_LATEST_PATH)
    pattern_data = load_json(HISTORICAL_PATTERN_LATEST_PATH)
    analog_data = load_json(HISTORICAL_ANALOG_LATEST_PATH)

    prediction_output = build_prediction_output(
        trend_data=trend_data,
        signal_data=signal_data,
        scenario_data=scenario_data,
        pattern_data=pattern_data,
        analog_data=analog_data,
    )

    write_json(PREDICTION_LATEST_PATH, prediction_output)
    save_history(prediction_output)

    print(f"[prediction_engine] wrote {PREDICTION_LATEST_PATH}")
    print(
        "[prediction_engine] dominant="
        f"{prediction_output.get('dominant_scenario')} "
        "risk="
        f"{prediction_output.get('risk')} "
        "confidence="
        f"{prediction_output.get('confidence')}"
    )


if __name__ == "__main__":
    main()
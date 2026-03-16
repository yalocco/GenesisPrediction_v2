#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"

TREND_LATEST_PATH = PREDICTION_DIR / "trend_latest.json"
SIGNAL_LATEST_PATH = PREDICTION_DIR / "signal_latest.json"
HISTORICAL_PATTERN_LATEST_PATH = PREDICTION_DIR / "historical_pattern_latest.json"
HISTORICAL_ANALOG_LATEST_PATH = PREDICTION_DIR / "historical_analog_latest.json"

SCENARIO_LATEST_PATH = PREDICTION_DIR / "scenario_latest.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


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


def collect_strings(obj: Any) -> List[str]:
    results: List[str] = []

    def walk(x: Any) -> None:
        if x is None:
            return
        if isinstance(x, str):
            s = normalize_text(x)
            if s:
                results.append(s)
            return
        if isinstance(x, list):
            for item in x:
                walk(item)
            return
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
            return

    walk(obj)
    return unique_preserve_order(results)


def extract_signal_tags(signal_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    candidate_keys = [
        "signal_tags",
        "historical_tags",
        "signals",
        "dominant_signals",
        "watchpoints",
        "tags",
    ]

    for key in candidate_keys:
        value = signal_data.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    tags.append(normalize_text(item))
                elif isinstance(item, dict):
                    for k in ("tag", "name", "signal", "label", "driver", "type", "key"):
                        if item.get(k):
                            tags.append(normalize_text(item.get(k)))
                    if isinstance(item.get("tags"), list):
                        tags.extend(normalize_text(x) for x in item.get("tags", []) if isinstance(x, str))
        elif isinstance(value, str):
            tags.append(normalize_text(value))

    if not tags:
        tags.extend(collect_strings(signal_data))

    return unique_preserve_order([t for t in tags if t])


def extract_trend_tags(trend_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    candidate_keys = [
        "trend_tags",
        "tags",
        "drivers",
        "dominant_trends",
        "regimes",
        "trend_summary",
    ]

    for key in candidate_keys:
        value = trend_data.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    tags.append(normalize_text(item))
                elif isinstance(item, dict):
                    for k in ("tag", "name", "trend", "label", "direction", "regime", "driver", "key"):
                        if item.get(k):
                            tags.append(normalize_text(item.get(k)))
                    if isinstance(item.get("tags"), list):
                        tags.extend(normalize_text(x) for x in item.get("tags", []) if isinstance(x, str))
        elif isinstance(value, str):
            tags.append(normalize_text(value))

    if not tags:
        tags.extend(collect_strings(trend_data))

    return unique_preserve_order([t for t in tags if t])


def extract_historical_watchpoints(pattern_data: Dict[str, Any], analog_data: Dict[str, Any]) -> List[str]:
    watchpoints: List[str] = []

    for item in pattern_data.get("matched_patterns", []) or []:
        if isinstance(item, dict):
            value = item.get("watchpoints", [])
            if isinstance(value, list):
                watchpoints.extend(str(x) for x in value if x is not None)

    for item in analog_data.get("top_analogs", []) or []:
        if isinstance(item, dict):
            value = item.get("watchpoints", [])
            if isinstance(value, list):
                watchpoints.extend(str(x) for x in value if x is not None)
            similarities = item.get("similarities", [])
            if isinstance(similarities, list):
                watchpoints.extend(str(x) for x in similarities if x is not None)

    return unique_preserve_order([normalize_text(x) for x in watchpoints if normalize_text(x)])


def extract_expected_outcomes(pattern_data: Dict[str, Any], analog_data: Dict[str, Any]) -> List[str]:
    outcomes: List[str] = []

    for item in pattern_data.get("matched_patterns", []) or []:
        if isinstance(item, dict):
            value = item.get("expected_outcomes", [])
            if isinstance(value, list):
                outcomes.extend(str(x) for x in value if x is not None)

    for item in analog_data.get("top_analogs", []) or []:
        if isinstance(item, dict):
            value = item.get("historical_outcomes", [])
            if isinstance(value, list):
                outcomes.extend(str(x) for x in value if x is not None)

    return unique_preserve_order([normalize_text(x) for x in outcomes if normalize_text(x)])


def get_current_stress_vector(historical_pattern_data: Dict[str, Any]) -> Dict[str, float]:
    vector = historical_pattern_data.get("current_stress_vector", {})
    if not isinstance(vector, dict):
        return {}
    return {str(k): clamp01(safe_float(v)) for k, v in vector.items()}


def stress_average(stress_vector: Dict[str, float]) -> float:
    if not stress_vector:
        return 0.0
    values = [clamp01(safe_float(v)) for v in stress_vector.values()]
    return sum(values) / len(values) if values else 0.0


def stress_peak(stress_vector: Dict[str, float]) -> float:
    if not stress_vector:
        return 0.0
    return max(clamp01(safe_float(v)) for v in stress_vector.values())


def build_risk_flags(
    signal_tags: List[str],
    trend_tags: List[str],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
    expected_outcomes: List[str],
    stress_vector: Dict[str, float],
) -> List[str]:
    flags: List[str] = []
    combined = set(signal_tags + trend_tags + expected_outcomes)

    keyword_map = {
        "war": "geopolitical escalation",
        "military": "military tension",
        "sanction": "sanctions fragmentation",
        "oil": "energy inflation",
        "energy": "energy stress",
        "debt": "debt fragility",
        "bank": "banking stress",
        "currency": "currency instability",
        "devaluation": "currency weakness",
        "trade": "trade disruption",
        "shipping": "supply chain disruption",
        "food": "food inflation risk",
        "grain": "grain stress",
        "drought": "agricultural shock",
        "flood": "infrastructure disruption",
        "pandemic": "health-system disruption",
        "protest": "social unrest",
        "unrest": "social unrest",
        "hegemon": "hegemonic transition",
        "empire": "order transition stress",
    }

    for token, label in keyword_map.items():
        if token in combined:
            flags.append(label)

    avg_stress = stress_average(stress_vector)
    peak_stress = stress_peak(stress_vector)

    if avg_stress >= 0.70:
        flags.append("broad civilizational stress")
    elif avg_stress >= 0.50:
        flags.append("multi-domain stress")

    if peak_stress >= 0.85:
        flags.append("acute stress concentration")

    if dominant_pattern:
        flags.append(f"historical pattern: {dominant_pattern}")
    if dominant_analog:
        flags.append(f"historical analog: {dominant_analog}")

    return unique_preserve_order(flags)


def build_key_drivers(
    signal_tags: List[str],
    trend_tags: List[str],
    dominant_pattern: Optional[str],
    expected_outcomes: List[str],
) -> List[str]:
    drivers = []
    drivers.extend(signal_tags[:6])
    drivers.extend(trend_tags[:4])

    if dominant_pattern:
        drivers.append(f"historical:{dominant_pattern}")

    for outcome in expected_outcomes[:4]:
        drivers.append(f"expected:{outcome}")

    return unique_preserve_order([normalize_text(x) for x in drivers if normalize_text(x)])


def derive_scenario_bias(
    historical_pattern_data: Dict[str, Any],
    historical_analog_data: Dict[str, Any],
) -> Dict[str, float]:
    best_case = 0.0
    base_case = 0.0
    worst_case = 0.0
    count = 0

    top_patterns = historical_pattern_data.get("matched_patterns", []) or []
    for item in top_patterns[:3]:
        if not isinstance(item, dict):
            continue
        bias = item.get("scenario_bias", {})
        if not isinstance(bias, dict):
            continue
        best_case += safe_float(bias.get("best_case"))
        base_case += safe_float(bias.get("base_case"))
        worst_case += safe_float(bias.get("worst_case"))
        count += 1

    top_analogs = historical_analog_data.get("top_analogs", []) or []
    for item in top_analogs[:2]:
        if not isinstance(item, dict):
            continue
        bias = item.get("scenario_bias", {})
        if not isinstance(bias, dict):
            continue
        best_case += safe_float(bias.get("best_case"))
        base_case += safe_float(bias.get("base_case"))
        worst_case += safe_float(bias.get("worst_case"))
        count += 1

    if count <= 0:
        return {
            "best_case": 0.25,
            "base_case": 0.5,
            "worst_case": 0.25,
        }

    best_case /= count
    base_case /= count
    worst_case /= count

    total = best_case + base_case + worst_case
    if total <= 0:
        return {
            "best_case": 0.25,
            "base_case": 0.5,
            "worst_case": 0.25,
        }

    return {
        "best_case": round(best_case / total, 4),
        "base_case": round(base_case / total, 4),
        "worst_case": round(worst_case / total, 4),
    }


def classify_risk_label(
    signal_data: Dict[str, Any],
    historical_pattern_data: Dict[str, Any],
    stress_vector: Dict[str, float],
) -> str:
    existing_risk = normalize_text(signal_data.get("risk") or signal_data.get("risk_level"))

    if existing_risk in {"high", "elevated", "guarded", "critical"}:
        if existing_risk == "critical":
            return "critical"
        if existing_risk == "high":
            return "high"
        return "guarded"

    pattern_confidence = safe_float(historical_pattern_data.get("pattern_confidence"))
    avg_stress = stress_average(stress_vector)
    peak_stress = stress_peak(stress_vector)

    if pattern_confidence >= 0.75 or peak_stress >= 0.90:
        return "high"
    if pattern_confidence >= 0.50 or avg_stress >= 0.50:
        return "guarded"
    return "stable"


def calculate_scenario_confidence(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    historical_pattern_data: Dict[str, Any],
    historical_analog_data: Dict[str, Any],
) -> float:
    base = 0.35

    trend_conf = safe_float(trend_data.get("confidence", trend_data.get("overall_confidence", 0.0)))
    signal_conf = 0.0
    signals = signal_data.get("signals", [])
    if isinstance(signals, list) and signals:
        signal_conf = sum(safe_float(item.get("confidence", 0.0)) for item in signals if isinstance(item, dict)) / len(signals)
    pattern_conf = safe_float(historical_pattern_data.get("pattern_confidence", 0.0))
    analog_conf = safe_float(historical_analog_data.get("analog_confidence", 0.0))

    confidence = (
        base
        + 0.20 * trend_conf
        + 0.25 * signal_conf
        + 0.15 * pattern_conf
        + 0.10 * analog_conf
    )

    return round(clamp01(confidence), 4)


def build_best_case(
    risk_label: str,
    expected_outcomes: List[str],
    watchpoints: List[str],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative = (
        "Escalation pressures stabilize, supply disruptions remain contained, "
        "and policy or market adaptation prevents broad spillover."
    )

    if risk_label == "stable":
        narrative = (
            "Current pressures remain limited and adaptive capacity is sufficient "
            "to prevent a major regime shift."
        )

    drivers = [
        "de-escalation",
        "policy stabilization",
        "supply adaptation",
        "confidence recovery",
    ]
    if dominant_pattern:
        drivers.append(f"containment_of:{dominant_pattern}")

    outcomes = []
    for item in expected_outcomes:
        if item.endswith("_up"):
            outcomes.append(item.replace("_up", "_moderates"))
        elif item.endswith("_down"):
            outcomes.append(item.replace("_down", "_stabilizes"))
        else:
            outcomes.append(item)

    return {
        "scenario_id": "best_case",
        "label": "Best Case",
        "probability_hint": "lower",
        "narrative": narrative,
        "drivers": unique_preserve_order(drivers),
        "expected_outcomes": unique_preserve_order(outcomes[:6]),
        "watchpoints": unique_preserve_order(watchpoints[:6]),
        "historical_support": {
            "dominant_pattern": dominant_pattern,
            "dominant_analog": dominant_analog,
            "stress_peak": round(stress_peak(stress_vector), 4),
        },
    }


def build_base_case(
    risk_label: str,
    expected_outcomes: List[str],
    watchpoints: List[str],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative = (
        "Current pressures persist in a guarded but manageable form, "
        "with continued volatility and selective downstream stress."
    )

    if risk_label == "high":
        narrative = (
            "The most likely path is continued deterioration without immediate collapse, "
            "producing a sustained guarded-risk regime."
        )

    drivers = [
        "persistent stress",
        "slow adjustment",
        "partial policy response",
        "selective spillover",
    ]
    if dominant_analog:
        drivers.append(f"historical_similarity:{dominant_analog}")

    return {
        "scenario_id": "base_case",
        "label": "Base Case",
        "probability_hint": "highest",
        "narrative": narrative,
        "drivers": unique_preserve_order(drivers),
        "expected_outcomes": unique_preserve_order(expected_outcomes[:6]),
        "watchpoints": unique_preserve_order(watchpoints[:8]),
        "historical_support": {
            "dominant_pattern": dominant_pattern,
            "dominant_analog": dominant_analog,
            "stress_average": round(stress_average(stress_vector), 4),
        },
    }


def build_worst_case(
    risk_label: str,
    expected_outcomes: List[str],
    watchpoints: List[str],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative = (
        "Current pressures intensify into a broader systemic regime, "
        "with cross-domain spillover into trade, currency, political, or social stability."
    )

    if risk_label == "stable":
        narrative = (
            "A low-probability but important adverse path remains: seemingly contained "
            "pressures could still cascade if watchpoints worsen rapidly."
        )

    intensified_outcomes = []
    for item in expected_outcomes:
        if item.endswith("_up"):
            intensified_outcomes.append(item.replace("_up", "_sharp_up"))
        elif item.endswith("_down"):
            intensified_outcomes.append(item.replace("_down", "_sharp_down"))
        else:
            intensified_outcomes.append(item)

    drivers = [
        "escalation",
        "confidence breakdown",
        "policy failure",
        "cross-domain contagion",
    ]
    if dominant_pattern:
        drivers.append(f"historical_escalation_path:{dominant_pattern}")

    return {
        "scenario_id": "worst_case",
        "label": "Worst Case",
        "probability_hint": "meaningful_tail_risk",
        "narrative": narrative,
        "drivers": unique_preserve_order(drivers),
        "expected_outcomes": unique_preserve_order(intensified_outcomes[:6]),
        "watchpoints": unique_preserve_order(watchpoints[:10]),
        "historical_support": {
            "dominant_pattern": dominant_pattern,
            "dominant_analog": dominant_analog,
            "stress_peak": round(stress_peak(stress_vector), 4),
            "stress_average": round(stress_average(stress_vector), 4),
        },
    }


def choose_dominant_scenario(
    scenario_bias: Dict[str, float],
    risk_label: str,
) -> str:
    best_case = safe_float(scenario_bias.get("best_case"))
    base_case = safe_float(scenario_bias.get("base_case"))
    worst_case = safe_float(scenario_bias.get("worst_case"))

    if risk_label == "high" and worst_case >= max(best_case, base_case) * 0.9:
        return "worst_case"

    if base_case >= best_case and base_case >= worst_case:
        return "base_case"
    if worst_case > best_case:
        return "worst_case"
    return "best_case"


def build_summary(
    dominant_scenario: str,
    risk_label: str,
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
    confidence: float,
) -> str:
    parts = [
        f"Dominant scenario is {dominant_scenario}",
        f"risk is {risk_label}",
        f"confidence is {confidence:.2f}",
    ]
    if dominant_pattern:
        parts.append(f"historical pattern is {dominant_pattern}")
    if dominant_analog:
        parts.append(f"historical analog is {dominant_analog}")
    return ". ".join(parts) + "."


def build_scenario_output(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    historical_pattern_data: Dict[str, Any],
    historical_analog_data: Dict[str, Any],
) -> Dict[str, Any]:
    as_of = (
        signal_data.get("as_of")
        or trend_data.get("as_of")
        or historical_pattern_data.get("as_of")
        or historical_analog_data.get("as_of")
        or today_str()
    )

    signal_tags = extract_signal_tags(signal_data)
    trend_tags = extract_trend_tags(trend_data)

    dominant_pattern = historical_pattern_data.get("dominant_pattern")
    dominant_analog = historical_analog_data.get("dominant_analog")

    expected_outcomes = extract_expected_outcomes(historical_pattern_data, historical_analog_data)
    watchpoints = extract_historical_watchpoints(historical_pattern_data, historical_analog_data)
    stress_vector = get_current_stress_vector(historical_pattern_data)

    scenario_bias = derive_scenario_bias(historical_pattern_data, historical_analog_data)
    risk_label = classify_risk_label(signal_data, historical_pattern_data, stress_vector)
    confidence = calculate_scenario_confidence(
        trend_data=trend_data,
        signal_data=signal_data,
        historical_pattern_data=historical_pattern_data,
        historical_analog_data=historical_analog_data,
    )

    scenarios = [
        build_best_case(
            risk_label=risk_label,
            expected_outcomes=expected_outcomes,
            watchpoints=watchpoints,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
        build_base_case(
            risk_label=risk_label,
            expected_outcomes=expected_outcomes,
            watchpoints=watchpoints,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
        build_worst_case(
            risk_label=risk_label,
            expected_outcomes=expected_outcomes,
            watchpoints=watchpoints,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
    ]

    dominant_scenario = choose_dominant_scenario(
        scenario_bias=scenario_bias,
        risk_label=risk_label,
    )

    key_drivers = build_key_drivers(
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        dominant_pattern=dominant_pattern,
        expected_outcomes=expected_outcomes,
    )

    risk_flags = build_risk_flags(
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
        expected_outcomes=expected_outcomes,
        stress_vector=stress_vector,
    )

    summary = build_summary(
        dominant_scenario=dominant_scenario,
        risk_label=risk_label,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
        confidence=confidence,
    )

    return {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "engine_version": "v2_historical",
        "dominant_scenario": dominant_scenario,
        "risk": risk_label,
        "confidence": confidence,
        "scenario_bias": scenario_bias,
        "key_drivers": key_drivers,
        "risk_flags": risk_flags,
        "watchpoints": watchpoints[:10],
        "expected_outcomes": expected_outcomes[:10],
        "historical_context": {
            "dominant_pattern": dominant_pattern,
            "pattern_confidence": round(safe_float(historical_pattern_data.get("pattern_confidence")), 4),
            "dominant_analog": dominant_analog,
            "analog_confidence": round(safe_float(historical_analog_data.get("analog_confidence")), 4),
            "current_stress_vector": {k: round(v, 4) for k, v in stress_vector.items()},
            "historical_watchpoints": watchpoints[:10],
        },
        "scenarios": scenarios,
        "summary": summary,
    }


def save_history(scenario_output: Dict[str, Any]) -> None:
    as_of = str(scenario_output.get("as_of") or today_str())
    history_dir = PREDICTION_DIR / "history" / as_of
    write_json(history_dir / "scenario.json", scenario_output)


def main() -> None:
    trend_data = load_json(TREND_LATEST_PATH, default={}) or {}
    signal_data = load_json(SIGNAL_LATEST_PATH, default={}) or {}
    historical_pattern_data = load_json(HISTORICAL_PATTERN_LATEST_PATH, default={}) or {}
    historical_analog_data = load_json(HISTORICAL_ANALOG_LATEST_PATH, default={}) or {}

    scenario_output = build_scenario_output(
        trend_data=trend_data,
        signal_data=signal_data,
        historical_pattern_data=historical_pattern_data,
        historical_analog_data=historical_analog_data,
    )

    write_json(SCENARIO_LATEST_PATH, scenario_output)
    save_history(scenario_output)

    print(f"[scenario_engine] wrote {SCENARIO_LATEST_PATH}")
    print(
        "[scenario_engine] dominant="
        f"{scenario_output.get('dominant_scenario')} "
        "risk="
        f"{scenario_output.get('risk')} "
        "confidence="
        f"{scenario_output.get('confidence')}"
    )


if __name__ == "__main__":
    main()
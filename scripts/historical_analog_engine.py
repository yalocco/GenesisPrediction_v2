from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"
HISTORICAL_DIR = ANALYSIS_DIR / "historical"
HISTORICAL_EVENTS_DIR = HISTORICAL_DIR / "events"

HISTORICAL_PATTERN_LATEST_PATH = PREDICTION_DIR / "historical_pattern_latest.json"
HISTORICAL_STRESS_LATEST_PATH = PREDICTION_DIR / "historical_stress_latest.json"
SIGNAL_LATEST_PATH = PREDICTION_DIR / "signal_latest.json"
TREND_LATEST_PATH = PREDICTION_DIR / "trend_latest.json"

HISTORICAL_ANALOG_LATEST_PATH = PREDICTION_DIR / "historical_analog_latest.json"


@dataclass
class EngineConfig:
    engine_version: str = "v3_similarity"
    top_k_analogs: int = 5
    history_enabled: bool = True
    clamp_scores: bool = True


CONFIG = EngineConfig()


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


def unique_preserve_order(items: Iterable[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def overlap_score(a: Iterable[str], b: Iterable[str]) -> float:
    sa = set(normalize_text(x) for x in a if normalize_text(x))
    sb = set(normalize_text(x) for x in b if normalize_text(x))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def cosine_similarity(v1: Dict[str, Any], v2: Dict[str, Any]) -> float:
    keys = sorted(set(v1.keys()) | set(v2.keys()))
    if not keys:
        return 0.0

    a = [safe_float(v1.get(k, 0.0)) for k in keys]
    b = [safe_float(v2.get(k, 0.0)) for k in keys]

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def vector_similarity(v1: Dict[str, Any], v2: Dict[str, Any]) -> float:
    cosine = cosine_similarity(v1, v2)

    keys = sorted(set(v1.keys()) | set(v2.keys()))
    if not keys:
        return 0.0

    total_abs_diff = 0.0
    for k in keys:
        total_abs_diff += abs(safe_float(v1.get(k, 0.0)) - safe_float(v2.get(k, 0.0)))
    manhattan_component = 1.0 - (total_abs_diff / float(len(keys)))

    blended = 0.7 * cosine + 0.3 * manhattan_component
    return clamp01(blended)


def collect_signal_tags(signal_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    for key in ("signal_tags", "historical_tags", "trend_tags_used", "watchpoints", "dominant_signals"):
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


def collect_pattern_context(pattern_data: Dict[str, Any]) -> Dict[str, Any]:
    matched_patterns = pattern_data.get("matched_patterns", [])
    if not isinstance(matched_patterns, list):
        matched_patterns = []

    dominant_pattern = normalize_text(pattern_data.get("dominant_pattern"))
    current_stress_vector = pattern_data.get("current_stress_vector", {})
    if not isinstance(current_stress_vector, dict):
        current_stress_vector = {}

    pattern_ids: List[str] = []
    expected_outcomes: List[str] = []
    watchpoints: List[str] = []

    for item in matched_patterns[:5]:
        if not isinstance(item, dict):
            continue
        pid = normalize_text(item.get("pattern_id"))
        if pid:
            pattern_ids.append(pid)

        eo = item.get("expected_outcomes", [])
        if isinstance(eo, list):
            expected_outcomes.extend(normalize_text(x) for x in eo if normalize_text(x))

        wp = item.get("watchpoints", [])
        if isinstance(wp, list):
            watchpoints.extend(normalize_text(x) for x in wp if normalize_text(x))

    if dominant_pattern and dominant_pattern not in pattern_ids:
        pattern_ids.insert(0, dominant_pattern)

    return {
        "dominant_pattern": dominant_pattern,
        "pattern_ids": unique_preserve_order(pattern_ids),
        "expected_outcomes": unique_preserve_order(expected_outcomes),
        "watchpoints": unique_preserve_order(watchpoints),
        "current_stress_vector": {str(k): round(clamp01(safe_float(v)), 4) for k, v in current_stress_vector.items()},
    }


def normalize_analog_event(event: Dict[str, Any]) -> Dict[str, Any]:
    tags: List[str] = []
    for key in (
        "tags",
        "cause_tags",
        "trigger_tags",
        "effect_tags",
        "outcome_tags",
        "watchpoints",
        "pattern_links",
    ):
        value = event.get(key, [])
        if isinstance(value, list):
            tags.extend(normalize_text(x) for x in value if normalize_text(x))

    return {
        "analog_id": event.get("analog_id") or event.get("event_id") or event.get("id") or "",
        "title": event.get("title") or event.get("name") or "Untitled analog",
        "period": event.get("period") or "",
        "category": event.get("category") or "general",
        "region": event.get("region") or "",
        "summary": event.get("summary") or "",
        "tags": unique_preserve_order(tags),
        "pattern_links": unique_preserve_order(
            normalize_text(x) for x in event.get("pattern_links", []) if normalize_text(x)
        ) if isinstance(event.get("pattern_links"), list) else [],
        "historical_outcomes": unique_preserve_order(
            normalize_text(x) for x in event.get("historical_outcomes", []) if normalize_text(x)
        ) if isinstance(event.get("historical_outcomes"), list) else [],
        "watchpoints": unique_preserve_order(
            normalize_text(x) for x in event.get("watchpoints", []) if normalize_text(x)
        ) if isinstance(event.get("watchpoints"), list) else [],
        "stress_vector": event.get("stress_vector", {}) if isinstance(event.get("stress_vector"), dict) else {},
        "scenario_bias": event.get("scenario_bias", {}) if isinstance(event.get("scenario_bias"), dict) else {},
        "confidence_weight": clamp01(safe_float(event.get("confidence_weight", 0.85), 0.85)),
    }


def load_event_library() -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []

    if HISTORICAL_EVENTS_DIR.exists() and HISTORICAL_EVENTS_DIR.is_dir():
        for path in sorted(HISTORICAL_EVENTS_DIR.glob("*.json")):
            payload = load_json(path, default={}) or {}
            if isinstance(payload, dict) and (payload.get("analog_id") or payload.get("title")):
                events.append(normalize_analog_event(payload))
            elif isinstance(payload, dict) and isinstance(payload.get("events"), list):
                for item in payload["events"]:
                    if isinstance(item, dict):
                        events.append(normalize_analog_event(item))

    return [e for e in events if e.get("analog_id")]


def fallback_events_from_pattern_output(pattern_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []

    matched_patterns = pattern_data.get("matched_patterns", [])
    if not isinstance(matched_patterns, list):
        return events

    for item in matched_patterns[:5]:
        if not isinstance(item, dict):
            continue
        analog_examples = item.get("analog_examples", [])
        if not isinstance(analog_examples, list):
            continue

        for analog_id in analog_examples:
            aid = normalize_text(analog_id)
            if not aid:
                continue

            events.append(
                {
                    "analog_id": aid,
                    "title": str(analog_id).replace("_", " ").title(),
                    "period": "",
                    "category": item.get("category", "general"),
                    "region": "",
                    "summary": item.get("summary", ""),
                    "tags": unique_preserve_order(
                        normalize_text(x)
                        for x in (
                            item.get("matched_signals", [])
                            + item.get("matched_trends", [])
                            + item.get("expected_outcomes", [])
                            + item.get("watchpoints", [])
                        )
                        if normalize_text(x)
                    ),
                    "pattern_links": [normalize_text(item.get("pattern_id"))] if item.get("pattern_id") else [],
                    "historical_outcomes": unique_preserve_order(
                        normalize_text(x) for x in item.get("expected_outcomes", []) if normalize_text(x)
                    ),
                    "watchpoints": unique_preserve_order(
                        normalize_text(x) for x in item.get("watchpoints", []) if normalize_text(x)
                    ),
                    "stress_vector": item.get("stress_profile", {}) if isinstance(item.get("stress_profile"), dict) else {},
                    "scenario_bias": item.get("scenario_bias", {}) if isinstance(item.get("scenario_bias"), dict) else {},
                    "confidence_weight": 0.75,
                }
            )

    dedup: Dict[str, Dict[str, Any]] = {}
    for event in events:
        analog_id = event["analog_id"]
        if analog_id not in dedup:
            dedup[analog_id] = event

    return list(dedup.values())


def compute_analog_match(
    event: Dict[str, Any],
    signal_tags: List[str],
    trend_tags: List[str],
    pattern_context: Dict[str, Any],
    stress_vector: Dict[str, float],
) -> Dict[str, Any]:
    analog_tags = event.get("tags", [])
    pattern_links = event.get("pattern_links", [])
    outcomes = event.get("historical_outcomes", [])
    analog_stress = event.get("stress_vector", {}) if isinstance(event.get("stress_vector"), dict) else {}

    signal_overlap = overlap_score(signal_tags, analog_tags)
    trend_overlap = overlap_score(trend_tags, analog_tags)
    pattern_overlap = overlap_score(pattern_context.get("pattern_ids", []), pattern_links)
    outcome_overlap = overlap_score(pattern_context.get("expected_outcomes", []), outcomes)
    watchpoint_overlap = overlap_score(pattern_context.get("watchpoints", []), event.get("watchpoints", []))
    stress_similarity = vector_similarity(stress_vector, analog_stress)

    similarity_score = (
        0.25 * signal_overlap
        + 0.15 * trend_overlap
        + 0.15 * pattern_overlap
        + 0.15 * outcome_overlap
        + 0.10 * watchpoint_overlap
        + 0.20 * stress_similarity
    )

    confidence_weight = clamp01(safe_float(event.get("confidence_weight", 0.85), 0.85))
    weighted_match_score = clamp01(similarity_score * confidence_weight)

    matched_tags = sorted(set(signal_tags + trend_tags) & set(analog_tags))
    pattern_matches = sorted(set(pattern_context.get("pattern_ids", [])) & set(pattern_links))
    outcome_matches = sorted(set(pattern_context.get("expected_outcomes", [])) & set(outcomes))

    similarities = unique_preserve_order(matched_tags + pattern_matches + outcome_matches)

    differences: List[str] = []
    if stress_similarity < 0.4:
        differences.append("stress_profile_divergence")
    if not pattern_matches:
        differences.append("pattern_link_gap")
    if not matched_tags:
        differences.append("tag_overlap_limited")

    return {
        "analog_id": event.get("analog_id"),
        "title": event.get("title"),
        "period": event.get("period", ""),
        "category": event.get("category", "general"),
        "region": event.get("region", ""),
        "similarity_score": round(clamp01(similarity_score), 4),
        "match_score": round(clamp01(similarity_score), 4),
        "weighted_match_score": round(weighted_match_score, 4),
        "similarities": similarities,
        "differences": differences,
        "historical_outcomes": outcomes,
        "watchpoints": event.get("watchpoints", []),
        "scenario_bias": event.get("scenario_bias", {}),
        "summary": event.get("summary", ""),
        "source_pattern_links": pattern_links,
        "stress_profile": {str(k): round(clamp01(safe_float(v)), 4) for k, v in analog_stress.items()},
        "diagnostics": {
            "signal_overlap": round(signal_overlap, 4),
            "trend_overlap": round(trend_overlap, 4),
            "pattern_overlap": round(pattern_overlap, 4),
            "outcome_overlap": round(outcome_overlap, 4),
            "watchpoint_overlap": round(watchpoint_overlap, 4),
            "stress_similarity": round(stress_similarity, 4),
            "confidence_weight": round(confidence_weight, 4),
        },
    }


def build_output(
    pattern_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    trend_data: Dict[str, Any],
    stress_data: Dict[str, Any],
    events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    signal_tags = collect_signal_tags(signal_data)
    trend_tags = collect_trend_tags(trend_data)
    pattern_context = collect_pattern_context(pattern_data)

    stress_vector = stress_data.get("stress_vector", {})
    if not isinstance(stress_vector, dict) or not stress_vector:
        stress_vector = pattern_context.get("current_stress_vector", {})
    if not isinstance(stress_vector, dict):
        stress_vector = {}

    candidates = [
        compute_analog_match(
            event=event,
            signal_tags=signal_tags,
            trend_tags=trend_tags,
            pattern_context=pattern_context,
            stress_vector=stress_vector,
        )
        for event in events
    ]

    candidates.sort(key=lambda x: x["weighted_match_score"], reverse=True)
    top_analogs = candidates[: CONFIG.top_k_analogs]

    dominant = top_analogs[0] if top_analogs else None
    dominant_analog = dominant["analog_id"] if dominant else None
    analog_confidence = dominant["weighted_match_score"] if dominant else 0.0

    summary = (
        f"Top historical analog is {dominant_analog} with weighted match {analog_confidence:.2f}."
        if dominant_analog
        else "No historical analog candidate available."
    )

    return {
        "as_of": pattern_data.get("as_of") or signal_data.get("as_of") or trend_data.get("as_of") or today_str(),
        "generated_at": utc_now_iso(),
        "engine_version": CONFIG.engine_version,
        "library_source": "analysis/historical/events" if HISTORICAL_EVENTS_DIR.exists() else "fallback_from_pattern_output",
        "dominant_analog": dominant_analog,
        "analog_confidence": round(analog_confidence, 4),
        "current_stress_vector": {str(k): round(clamp01(safe_float(v)), 4) for k, v in stress_vector.items()},
        "dominant_pattern_context": pattern_context.get("dominant_pattern"),
        "top_analogs": top_analogs,
        "summary": summary,
    }


def save_history(payload: Dict[str, Any]) -> None:
    if not CONFIG.history_enabled:
        return

    as_of = str(payload.get("as_of") or today_str())
    history_dir = PREDICTION_DIR / "history" / as_of
    write_json(history_dir / "historical_analog.json", payload)


def main() -> None:
    pattern_data = load_json(HISTORICAL_PATTERN_LATEST_PATH, default={}) or {}
    signal_data = load_json(SIGNAL_LATEST_PATH, default={}) or {}
    trend_data = load_json(TREND_LATEST_PATH, default={}) or {}
    stress_data = load_json(HISTORICAL_STRESS_LATEST_PATH, default={}) or {}

    events = load_event_library()
    if not events:
        events = fallback_events_from_pattern_output(pattern_data)

    payload = build_output(
        pattern_data=pattern_data,
        signal_data=signal_data,
        trend_data=trend_data,
        stress_data=stress_data,
        events=events,
    )

    write_json(HISTORICAL_ANALOG_LATEST_PATH, payload)
    save_history(payload)

    print(f"[historical_analog_engine] wrote {HISTORICAL_ANALOG_LATEST_PATH}")
    print(f"[historical_analog_engine] dominant_analog={payload.get('dominant_analog')}")
    print(f"[historical_analog_engine] analog_confidence={payload.get('analog_confidence')}")
    print(f"[historical_analog_engine] library_source={payload.get('library_source')}")


if __name__ == "__main__":
    main()
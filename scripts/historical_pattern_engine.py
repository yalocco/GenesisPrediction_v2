from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"
HISTORICAL_DIR = ANALYSIS_DIR / "historical"

TREND_LATEST_PATH = PREDICTION_DIR / "trend_latest.json"
SIGNAL_LATEST_PATH = PREDICTION_DIR / "signal_latest.json"
HISTORICAL_STRESS_LATEST_PATH = PREDICTION_DIR / "historical_stress_latest.json"

WORLD_POLITICS_DIR = ANALYSIS_DIR / "world_politics"
DAILY_SUMMARY_LATEST_PATH = WORLD_POLITICS_DIR / "daily_summary_latest.json"
SENTIMENT_LATEST_PATH = WORLD_POLITICS_DIR / "sentiment_latest.json"
VIEW_MODEL_LATEST_PATH = WORLD_POLITICS_DIR / "view_model_latest.json"

WAR_PATTERNS_PATH = HISTORICAL_DIR / "war_patterns.json"
FINANCIAL_PATTERNS_PATH = HISTORICAL_DIR / "financial_crisis_patterns.json"
EMPIRE_PATTERNS_PATH = HISTORICAL_DIR / "empire_decline_patterns.json"
DISASTER_PATTERNS_PATH = HISTORICAL_DIR / "disaster_patterns.json"

HISTORICAL_PATTERN_LATEST_PATH = PREDICTION_DIR / "historical_pattern_latest.json"
HISTORICAL_ANALOG_LATEST_PATH = PREDICTION_DIR / "historical_analog_latest.json"


@dataclass
class EngineConfig:
    engine_version: str = "v2_stress"
    top_k_patterns: int = 5
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
        if isinstance(x, (int, float, bool)):
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
        "signals",
        "signal_tags",
        "historical_tags",
        "tags",
        "drivers",
        "watchpoints",
        "dominant_signals",
        "active_signals",
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
                    for k in ("tag", "name", "signal", "type", "label", "driver", "key"):
                        if item.get(k):
                            tags.append(normalize_text(item.get(k)))
                    item_tags = item.get("tags")
                    if isinstance(item_tags, list):
                        tags.extend(normalize_text(x) for x in item_tags if normalize_text(x))
        elif isinstance(value, str):
            tags.append(normalize_text(value))

    return unique_preserve_order([t for t in tags if t])


def extract_trend_tags(trend_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    candidate_keys = [
        "trend_tags",
        "tags",
        "drivers",
        "regimes",
        "trend_summary",
        "dominant_trends",
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
                    for k in ("tag", "name", "trend", "direction", "label", "driver", "regime", "key"):
                        if item.get(k):
                            tags.append(normalize_text(item.get(k)))
                    item_tags = item.get("tags")
                    if isinstance(item_tags, list):
                        tags.extend(normalize_text(x) for x in item_tags if normalize_text(x))
        elif isinstance(value, str):
            tags.append(normalize_text(value))

    if not tags:
        tags.extend(collect_strings(trend_data))

    return unique_preserve_order([t for t in tags if t])


def extract_summary_keywords(daily_summary: Dict[str, Any]) -> List[str]:
    keywords: List[str] = []

    for key in ("topics", "keywords", "highlights", "summary_tags"):
        value = daily_summary.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    keywords.append(normalize_text(item))
                elif isinstance(item, dict):
                    for k in ("tag", "topic", "name", "title"):
                        if item.get(k):
                            keywords.append(normalize_text(item.get(k)))

    summary_text = " ".join(
        str(daily_summary.get(k, ""))
        for k in ("summary", "text_summary", "daily_summary")
        if daily_summary.get(k)
    ).lower()

    lexical_hints = [
        "war",
        "sanction",
        "oil",
        "energy",
        "inflation",
        "debt",
        "bank",
        "currency",
        "drought",
        "flood",
        "famine",
        "pandemic",
        "trade",
        "hegemon",
        "empire",
        "military",
        "food",
        "grain",
        "protest",
        "unrest",
    ]
    for word in lexical_hints:
        if word in summary_text:
            keywords.append(word)

    return unique_preserve_order([k for k in keywords if k])


def extract_current_stress_vector(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    daily_summary: Dict[str, Any],
) -> Dict[str, float]:
    base = {
        "food_stress": 0.0,
        "energy_stress": 0.0,
        "fiscal_stress": 0.0,
        "currency_stress": 0.0,
        "trade_stress": 0.0,
        "political_stress": 0.0,
        "military_stress": 0.0,
        "social_unrest_stress": 0.0,
    }

    tokens = set(
        extract_signal_tags(signal_data)
        + extract_trend_tags(trend_data)
        + extract_summary_keywords(daily_summary)
    )

    mapping = {
        "food_stress": {"food", "grain", "famine", "harvest", "drought"},
        "energy_stress": {"energy", "oil", "gas", "power", "energy_shock"},
        "fiscal_stress": {"debt", "deficit", "fiscal", "bailout", "budget", "policy_liquidity"},
        "currency_stress": {"currency", "fx", "devaluation", "reserve", "capital", "currency_instability"},
        "trade_stress": {"trade", "shipping", "port", "tariff", "sanction", "trade_fragmentation"},
        "political_stress": {"election", "political", "regime", "fragmentation", "governance", "risk_pressure", "regime_shift_pressure"},
        "military_stress": {"war", "military", "mobilization", "missile", "frontline", "military_escalation"},
        "social_unrest_stress": {"protest", "unrest", "riot", "migration", "instability", "social_unrest", "negative_sentiment"},
    }

    for stress_key, hints in mapping.items():
        overlap = len(tokens & hints)
        if overlap <= 0:
            base[stress_key] = 0.0
        elif overlap == 1:
            base[stress_key] = 0.4
        elif overlap == 2:
            base[stress_key] = 0.7
        else:
            base[stress_key] = 0.9

    return base


def extract_external_stress_vector(stress_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    if not isinstance(stress_data, dict):
        return None

    vector = stress_data.get("stress_vector")
    if not isinstance(vector, dict):
        return None

    normalized = {}
    for key, value in vector.items():
        normalized[str(key)] = round(clamp01(safe_float(value, 0.0)), 4)
    return normalized


def flatten_pattern_tags(pattern: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    for key in (
        "cause_tags",
        "trigger_tags",
        "event_chain",
        "impact_chain",
        "economic_outcomes",
        "political_outcomes",
        "civilization_outcomes",
        "watchpoints",
        "analog_examples",
    ):
        value = pattern.get(key, [])
        if isinstance(value, list):
            tags.extend(normalize_text(v) for v in value if isinstance(v, str))
        elif isinstance(value, str):
            tags.append(normalize_text(value))
    return unique_preserve_order([t for t in tags if t])


def load_pattern_library() -> List[Dict[str, Any]]:
    libraries = [
        load_json(WAR_PATTERNS_PATH, default={}),
        load_json(FINANCIAL_PATTERNS_PATH, default={}),
        load_json(EMPIRE_PATTERNS_PATH, default={}),
        load_json(DISASTER_PATTERNS_PATH, default={}),
    ]

    patterns: List[Dict[str, Any]] = []
    for lib in libraries:
        if not isinstance(lib, dict):
            continue
        items = lib.get("patterns", [])
        if not isinstance(items, list):
            continue
        for pattern in items:
            if isinstance(pattern, dict):
                patterns.append(pattern)

    return patterns


def overlap_score(a: Iterable[str], b: Iterable[str]) -> float:
    sa = set(normalize_text(x) for x in a if normalize_text(x))
    sb = set(normalize_text(x) for x in b if normalize_text(x))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def vector_similarity(v1: Dict[str, Any], v2: Dict[str, Any]) -> float:
    keys = sorted(set(v1.keys()) | set(v2.keys()))
    if not keys:
        return 0.0

    total = 0.0
    for k in keys:
        a = safe_float(v1.get(k, 0.0))
        b = safe_float(v2.get(k, 0.0))
        total += abs(a - b)

    max_total = float(len(keys))
    return 1.0 - (total / max_total if max_total > 0 else 0.0)


def category_match_score(current_tags: List[str], pattern_category: str) -> float:
    tokens = set(current_tags)
    category = normalize_text(pattern_category)

    category_hints = {
        "war": {"war", "military", "missile", "sanction", "frontline", "defense", "military_escalation"},
        "finance": {"bank", "debt", "currency", "liquidity", "credit", "default", "fx", "banking_stress", "currency_instability"},
        "empire": {"hegemon", "empire", "alliance", "bloc", "fragmentation", "legitimacy"},
        "disaster": {"drought", "flood", "famine", "pandemic", "earthquake", "food"},
    }

    hints = category_hints.get(category, set())
    if not hints:
        return 0.0

    overlap = len(tokens & hints)
    if overlap <= 0:
        return 0.0
    if overlap == 1:
        return 0.5
    return 1.0


def compute_pattern_match(
    pattern: Dict[str, Any],
    signal_tags: List[str],
    trend_tags: List[str],
    current_stress: Dict[str, float],
    summary_keywords: List[str],
) -> Dict[str, Any]:
    pattern_tags = flatten_pattern_tags(pattern)
    pattern_stress = pattern.get("stress_vector", {}) if isinstance(pattern.get("stress_vector"), dict) else {}

    signal_overlap = overlap_score(signal_tags, pattern_tags)
    trend_overlap = overlap_score(trend_tags, pattern_tags)
    stress_similarity = vector_similarity(current_stress, pattern_stress)
    category_score = category_match_score(signal_tags + trend_tags + summary_keywords, pattern.get("category", ""))
    outcome_overlap = overlap_score(summary_keywords, pattern.get("economic_outcomes", []))

    match_score = (
        0.30 * signal_overlap
        + 0.20 * trend_overlap
        + 0.20 * stress_similarity
        + 0.20 * category_score
        + 0.10 * outcome_overlap
    )

    confidence_weight = safe_float(pattern.get("confidence_weight", 1.0), 1.0)
    weighted_match_score = match_score * confidence_weight

    if CONFIG.clamp_scores:
        match_score = clamp01(match_score)
        weighted_match_score = clamp01(weighted_match_score)

    matched_signals = sorted(set(signal_tags) & set(pattern_tags))
    matched_trends = sorted(set(trend_tags) & set(pattern_tags))

    expected_outcomes = unique_preserve_order(pattern.get("economic_outcomes", []))
    watchpoints = unique_preserve_order(pattern.get("watchpoints", []))
    stress_profile = {
        k: round(safe_float(v), 4)
        for k, v in pattern_stress.items()
    }

    return {
        "pattern_id": pattern.get("pattern_id", ""),
        "name": pattern.get("name", ""),
        "category": pattern.get("category", ""),
        "match_score": round(match_score, 4),
        "weighted_match_score": round(weighted_match_score, 4),
        "matched_signals": matched_signals,
        "matched_trends": matched_trends,
        "watchpoints": watchpoints,
        "expected_outcomes": expected_outcomes,
        "stress_profile": stress_profile,
        "scenario_bias": pattern.get("scenario_bias", {}),
        "summary": pattern.get("summary", ""),
        "analog_examples": unique_preserve_order(pattern.get("analog_examples", [])),
    }


def build_historical_pattern_output(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    daily_summary: Dict[str, Any],
    stress_data: Dict[str, Any],
    patterns: List[Dict[str, Any]],
) -> Dict[str, Any]:
    signal_tags = extract_signal_tags(signal_data)
    trend_tags = extract_trend_tags(trend_data)
    summary_keywords = extract_summary_keywords(daily_summary)

    external_stress = extract_external_stress_vector(stress_data)
    if external_stress is not None:
        current_stress = external_stress
        stress_source = "historical_stress_latest.json"
    else:
        current_stress = extract_current_stress_vector(trend_data, signal_data, daily_summary)
        stress_source = "internal_heuristic"

    matched_patterns = [
        compute_pattern_match(
            pattern=pattern,
            signal_tags=signal_tags,
            trend_tags=trend_tags,
            current_stress=current_stress,
            summary_keywords=summary_keywords,
        )
        for pattern in patterns
    ]

    matched_patterns.sort(key=lambda x: x["weighted_match_score"], reverse=True)
    matched_patterns = matched_patterns[: CONFIG.top_k_patterns]

    dominant = matched_patterns[0] if matched_patterns else None
    dominant_pattern = dominant["pattern_id"] if dominant else None
    pattern_confidence = dominant["weighted_match_score"] if dominant else 0.0

    summary = (
        f"Top historical pattern is {dominant_pattern} with weighted match "
        f"{pattern_confidence:.2f}."
        if dominant_pattern
        else "No historical pattern match available."
    )

    return {
        "as_of": signal_data.get("as_of") or trend_data.get("as_of") or daily_summary.get("as_of") or today_str(),
        "generated_at": utc_now_iso(),
        "engine_version": CONFIG.engine_version,
        "dominant_pattern": dominant_pattern,
        "pattern_confidence": round(pattern_confidence, 4),
        "current_stress_vector": {k: round(v, 4) for k, v in current_stress.items()},
        "stress_source": stress_source,
        "signal_tags": signal_tags,
        "trend_tags": trend_tags,
        "summary_keywords": summary_keywords,
        "matched_patterns": matched_patterns,
        "summary": summary,
    }


def build_historical_analog_output(pattern_output: Dict[str, Any]) -> Dict[str, Any]:
    matched_patterns = pattern_output.get("matched_patterns", [])
    analogs: List[Dict[str, Any]] = []

    for matched in matched_patterns:
        analog_examples = matched.get("analog_examples", [])
        if not analog_examples:
            continue

        parent_score = safe_float(matched.get("weighted_match_score", matched.get("match_score", 0.0)))
        scenario_bias = matched.get("scenario_bias", {})

        for analog_id in analog_examples:
            analogs.append(
                {
                    "analog_id": analog_id,
                    "title": str(analog_id).replace("_", " ").title(),
                    "match_score": round(parent_score, 4),
                    "similarities": unique_preserve_order(
                        matched.get("matched_signals", []) + matched.get("matched_trends", [])
                    ),
                    "differences": [],
                    "historical_outcomes": matched.get("expected_outcomes", []),
                    "scenario_bias": scenario_bias,
                    "source_pattern_id": matched.get("pattern_id"),
                    "source_category": matched.get("category"),
                }
            )

    dedup: Dict[str, Dict[str, Any]] = {}
    for item in analogs:
        analog_id = item["analog_id"]
        current = dedup.get(analog_id)
        if current is None or safe_float(item.get("match_score")) > safe_float(current.get("match_score")):
            dedup[analog_id] = item

    top_analogs = sorted(
        dedup.values(),
        key=lambda x: safe_float(x.get("match_score", 0.0)),
        reverse=True,
    )[: CONFIG.top_k_analogs]

    dominant = top_analogs[0] if top_analogs else None
    dominant_analog = dominant["analog_id"] if dominant else None
    analog_confidence = safe_float(dominant.get("match_score", 0.0)) if dominant else 0.0

    summary = (
        f"Top historical analog is {dominant_analog} with match {analog_confidence:.2f}."
        if dominant_analog
        else "No historical analog candidate available."
    )

    return {
        "as_of": pattern_output.get("as_of", today_str()),
        "generated_at": utc_now_iso(),
        "engine_version": CONFIG.engine_version,
        "dominant_analog": dominant_analog,
        "analog_confidence": round(analog_confidence, 4),
        "top_analogs": top_analogs,
        "summary": summary,
    }


def build_outputs() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    trend_data = load_json(TREND_LATEST_PATH, default={}) or {}
    signal_data = load_json(SIGNAL_LATEST_PATH, default={}) or {}
    daily_summary = load_json(DAILY_SUMMARY_LATEST_PATH, default={}) or {}
    stress_data = load_json(HISTORICAL_STRESS_LATEST_PATH, default={}) or {}

    _ = load_json(SENTIMENT_LATEST_PATH, default={}) or {}
    _ = load_json(VIEW_MODEL_LATEST_PATH, default={}) or {}

    patterns = load_pattern_library()

    pattern_output = build_historical_pattern_output(
        trend_data=trend_data,
        signal_data=signal_data,
        daily_summary=daily_summary,
        stress_data=stress_data,
        patterns=patterns,
    )
    analog_output = build_historical_analog_output(pattern_output)

    return pattern_output, analog_output


def save_history(pattern_output: Dict[str, Any], analog_output: Dict[str, Any]) -> None:
    if not CONFIG.history_enabled:
        return

    as_of = str(pattern_output.get("as_of") or today_str())
    history_dir = PREDICTION_DIR / "history" / as_of

    write_json(history_dir / "historical_pattern.json", pattern_output)
    write_json(history_dir / "historical_analog.json", analog_output)


def main() -> None:
    pattern_output, analog_output = build_outputs()

    write_json(HISTORICAL_PATTERN_LATEST_PATH, pattern_output)
    write_json(HISTORICAL_ANALOG_LATEST_PATH, analog_output)
    save_history(pattern_output, analog_output)

    print(f"[historical_pattern_engine] wrote {HISTORICAL_PATTERN_LATEST_PATH}")
    print(f"[historical_pattern_engine] wrote {HISTORICAL_ANALOG_LATEST_PATH}")
    print(
        "[historical_pattern_engine] dominant_pattern="
        f"{pattern_output.get('dominant_pattern')} "
        "pattern_confidence="
        f"{pattern_output.get('pattern_confidence')}"
    )
    print(
        "[historical_pattern_engine] dominant_analog="
        f"{analog_output.get('dominant_analog')} "
        "analog_confidence="
        f"{analog_output.get('analog_confidence')}"
    )
    print(
        "[historical_pattern_engine] stress_source="
        f"{pattern_output.get('stress_source')}"
    )


if __name__ == "__main__":
    main()
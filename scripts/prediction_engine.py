#!/usr/bin/env python3
"""GenesisPrediction v2 - Prediction Engine

Builds prediction_latest.json from scenario_latest.json.

Design intent:
- analysis/ is the Single Source of Truth
- scripts generate artifacts only
- Prediction is the public-facing summary of Scenario, not a replacement for it
- Prediction must remain explainable with summary, drivers, watchpoints,
  confidence, invalidation_conditions, and scenario probabilities

This implementation is intentionally schema-tolerant because upstream Scenario
artifacts may evolve. It consumes stable scenario fields while keeping the
output contract predictable for UI and Morning Ritual integration.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


VERSION = "1.0"
DEFAULT_HORIZON_DAYS = 7


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def pick(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in d and d[key] is not None:
            return d[key]
    return default


def dedupe_keep_order(items: Iterable[str], limit: Optional[int] = None) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
        if limit is not None and len(out) >= limit:
            break
    return out


def to_title(text: str) -> str:
    return str(text or "").replace("_", " ").replace("-", " ").strip().title()


def normalize_risk_level(raw: Any, score: float) -> str:
    text = str(raw or "").strip().lower()
    if text in {"low", "guarded", "elevated", "high", "critical"}:
        return text
    if score >= 0.86:
        return "critical"
    if score >= 0.68:
        return "high"
    if score >= 0.48:
        return "elevated"
    if score >= 0.24:
        return "guarded"
    return "low"


def normalize_probability_map(payload: Dict[str, Any]) -> Dict[str, float]:
    probs = payload.get("probabilities") if isinstance(payload.get("probabilities"), dict) else {}
    best = clamp(safe_float(probs.get("best_case", 0.25), 0.25), 0.0, 1.0)
    base = clamp(safe_float(probs.get("base_case", 0.5), 0.5), 0.0, 1.0)
    worst = clamp(safe_float(probs.get("worst_case", 0.25), 0.25), 0.0, 1.0)

    total = max(best + base + worst, 1e-9)
    best_r = round(best / total, 4)
    base_r = round(base / total, 4)
    worst_r = round(1.0 - best_r - base_r, 4)
    if worst_r < 0:
        worst_r = 0.0
        base_r = round(1.0 - best_r, 4)

    return {
        "best_case": best_r,
        "base_case": base_r,
        "worst_case": worst_r,
    }


def iter_scenarios(payload: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any]]]:
    if isinstance(payload.get("scenarios"), list):
        for idx, item in enumerate(payload["scenarios"]):
            if isinstance(item, dict):
                scenario_id = str(pick(item, "scenario_id", "id", default=f"scenario_{idx}"))
                yield scenario_id, item

    for key in ("best_case", "base_case", "worst_case"):
        item = payload.get(key)
        if isinstance(item, dict):
            yield key, item


def build_scenario_index(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for scenario_id, item in iter_scenarios(payload):
        if scenario_id not in index:
            index[scenario_id] = item
    return index


def select_dominant_scenario(scenarios: Dict[str, Dict[str, Any]], probabilities: Dict[str, float], declared: str) -> Tuple[str, Dict[str, Any]]:
    if declared in scenarios:
        return declared, scenarios[declared]

    ranked = sorted(
        scenarios.items(),
        key=lambda kv: (
            safe_float(kv[1].get("probability", probabilities.get(kv[0], 0.0)), 0.0),
            safe_float(kv[1].get("confidence", 0.0), 0.0),
        ),
        reverse=True,
    )
    if ranked:
        return ranked[0][0], ranked[0][1]

    fallback = {
        "scenario_id": "base_case",
        "name": "Base Case",
        "probability": probabilities.get("base_case", 0.5),
        "confidence": 0.0,
        "regime": "Stable",
        "risk_level": "guarded",
        "risk_score": 0.0,
        "summary": "Scenario input unavailable.",
        "drivers": [],
        "watchpoints": [],
        "invalidation_conditions": [],
        "supporting_signals": [],
        "assumptions": [],
    }
    return "base_case", fallback


def build_overall_risk(scenarios: Dict[str, Dict[str, Any]], probabilities: Dict[str, float], fallback_score: float, fallback_level: str) -> Tuple[float, str]:
    weighted_score = 0.0
    total_weight = 0.0
    for scenario_id, item in scenarios.items():
        p = clamp(safe_float(item.get("probability", probabilities.get(scenario_id, 0.0)), probabilities.get(scenario_id, 0.0)), 0.0, 1.0)
        s = clamp(safe_float(item.get("risk_score", 0.0), 0.0), 0.0, 1.0)
        weighted_score += p * s
        total_weight += p

    if total_weight > 0:
        score = round(clamp(weighted_score / total_weight, 0.0, 1.0), 4)
    else:
        score = round(clamp(fallback_score, 0.0, 1.0), 4)

    level = normalize_risk_level(fallback_level, score)
    if scenarios:
        inferred = normalize_risk_level(None, score)
        if inferred != "low" or fallback_level in {"", "low"}:
            level = inferred
    return score, level


def build_prediction_summary(
    dominant_id: str,
    dominant: Dict[str, Any],
    overall_risk_level: str,
    overall_risk_score: float,
    horizon_days: int,
    probabilities: Dict[str, float],
    early_warning: Dict[str, Any],
) -> str:
    dominant_name = str(pick(dominant, "name", default=to_title(dominant_id)))
    dominant_probability = clamp(
        safe_float(dominant.get("probability", probabilities.get(dominant_id, 0.0)), probabilities.get(dominant_id, 0.0)),
        0.0,
        1.0,
    )
    dominant_regime = str(pick(dominant, "regime", default="Stable"))
    dominant_risk = normalize_risk_level(dominant.get("risk_level"), safe_float(dominant.get("risk_score", overall_risk_score), overall_risk_score))
    warning_level = str(pick(early_warning, "warning_level", default="quiet"))

    if dominant_id == "worst_case":
        return (
            f"Downside pressure is currently dominant: {dominant_name} leads at {dominant_probability:.0%}. "
            f"The {horizon_days}-day outlook is {overall_risk_level} risk under a {dominant_regime} regime, "
            f"with early warning at {warning_level}."
        )
    if dominant_id == "best_case":
        return (
            f"Stabilization remains plausible: {dominant_name} leads at {dominant_probability:.0%}. "
            f"The {horizon_days}-day outlook is {overall_risk_level} risk, but this path depends on current warnings failing to broaden."
        )
    return (
        f"Base case remains the working outlook at {dominant_probability:.0%}. "
        f"Overall risk is {overall_risk_level} ({overall_risk_score:.2f}) over the next {horizon_days} days, "
        f"while the {probabilities.get('worst_case', 0.0):.0%} worst-case branch keeps downside pressure visible."
    )


def collect_prediction_drivers(dominant: Dict[str, Any], scenarios: Dict[str, Dict[str, Any]], overall_risk_level: str) -> List[str]:
    drivers: List[str] = []
    dominant_drivers = dominant.get("drivers", []) if isinstance(dominant.get("drivers"), list) else []
    drivers.extend([str(x) for x in dominant_drivers])

    if overall_risk_level in {"high", "critical"}:
        drivers.append("Cross-scenario risk remains elevated enough that downside branches materially affect the public outlook.")
    elif overall_risk_level == "elevated":
        drivers.append("Risk is not extreme, but enough signals remain active to keep the outlook above guarded conditions.")
    else:
        drivers.append("Risk pressure is present but not yet dominant across the full scenario stack.")

    for key in ("base_case", "worst_case", "best_case"):
        if key in scenarios and scenarios[key] is not dominant:
            name = str(pick(scenarios[key], "name", default=to_title(key)))
            summary = str(pick(scenarios[key], "summary", default="")).strip()
            if summary:
                drivers.append(f"Alternative branch kept in view: {name} — {summary}")
                break

    return dedupe_keep_order(drivers, limit=8)


def collect_prediction_watchpoints(dominant: Dict[str, Any], scenarios: Dict[str, Dict[str, Any]], early_warning: Dict[str, Any]) -> List[str]:
    items: List[str] = []
    for key in ("watchpoints",):
        value = dominant.get(key)
        if isinstance(value, list):
            items.extend(str(x) for x in value)

    for scenario_key in ("worst_case", "base_case", "best_case"):
        scenario = scenarios.get(scenario_key)
        if not isinstance(scenario, dict) or scenario is dominant:
            continue
        value = scenario.get("watchpoints")
        if isinstance(value, list):
            items.extend(str(x) for x in value[:2])

    ew_headline = str(pick(early_warning, "headline", default="")).strip()
    ew_level = str(pick(early_warning, "warning_level", default="quiet")).strip()
    if ew_headline:
        items.append(f"Early warning: {ew_headline}")
    if ew_level and ew_level.lower() not in {"quiet", "low"}:
        items.append(f"Watch whether early warning level stays at {ew_level} or escalates further.")

    return dedupe_keep_order(items, limit=8)


def collect_invalidation_conditions(dominant: Dict[str, Any], scenarios: Dict[str, Dict[str, Any]]) -> List[str]:
    items: List[str] = []
    primary = dominant.get("invalidation_conditions")
    if isinstance(primary, list):
        items.extend(str(x) for x in primary)

    for scenario_key in ("base_case", "worst_case", "best_case"):
        scenario = scenarios.get(scenario_key)
        if not isinstance(scenario, dict) or scenario is dominant:
            continue
        value = scenario.get("invalidation_conditions")
        if isinstance(value, list):
            items.extend(str(x) for x in value[:2])

    return dedupe_keep_order(items, limit=6)


def build_signal_rollup(scenarios: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    counts = {
        "supporting_signal_count": 0,
        "high_or_critical_support_count": 0,
        "metrics": [],
        "signal_types": [],
    }
    metrics: List[str] = []
    signal_types: List[str] = []

    for scenario in scenarios.values():
        refs = scenario.get("supporting_signals") if isinstance(scenario.get("supporting_signals"), list) else []
        counts["supporting_signal_count"] += len(refs)
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            severity = str(ref.get("severity", "")).lower()
            if severity in {"high", "critical"}:
                counts["high_or_critical_support_count"] += 1
            metric = str(ref.get("metric", "")).strip()
            sig_type = str(ref.get("signal_type", "")).strip()
            if metric:
                metrics.append(metric)
            if sig_type:
                signal_types.append(sig_type)

    counts["metrics"] = dedupe_keep_order(metrics, limit=12)
    counts["signal_types"] = dedupe_keep_order(signal_types, limit=12)
    return counts


def build_prediction_payload(scenario_payload: Dict[str, Any], as_of: str, generated_at: str, horizon_days: int) -> Dict[str, Any]:
    probabilities = normalize_probability_map(scenario_payload)
    scenarios = build_scenario_index(scenario_payload)
    declared_dominant = str(pick(scenario_payload, "dominant_scenario", default="base_case"))
    dominant_id, dominant = select_dominant_scenario(scenarios, probabilities, declared_dominant)

    fallback_score = clamp(safe_float(pick(scenario_payload, "overall_risk_score", default=0.0), 0.0), 0.0, 1.0)
    fallback_level = str(pick(scenario_payload, "overall_risk_level", default="low"))
    overall_risk_score, overall_risk_level = build_overall_risk(scenarios, probabilities, fallback_score, fallback_level)

    scenario_confidence = clamp(safe_float(pick(scenario_payload, "scenario_confidence", "confidence", default=0.0), 0.0), 0.0, 1.0)
    dominant_confidence = clamp(safe_float(pick(dominant, "confidence", default=scenario_confidence), scenario_confidence), 0.0, 1.0)
    confidence = round(clamp((scenario_confidence * 0.6) + (dominant_confidence * 0.4), 0.0, 1.0), 4)

    regime = str(pick(dominant, "regime", default=pick(scenario_payload, "regime", default="Stable")))
    early_warning = scenario_payload.get("early_warning", {}) if isinstance(scenario_payload.get("early_warning"), dict) else {}

    summary = build_prediction_summary(
        dominant_id=dominant_id,
        dominant=dominant,
        overall_risk_level=overall_risk_level,
        overall_risk_score=overall_risk_score,
        horizon_days=horizon_days,
        probabilities=probabilities,
        early_warning=early_warning,
    )

    drivers = collect_prediction_drivers(dominant, scenarios, overall_risk_level)
    watchpoints = collect_prediction_watchpoints(dominant, scenarios, early_warning)
    invalidation_conditions = collect_invalidation_conditions(dominant, scenarios)
    signal_rollup = build_signal_rollup(scenarios)

    dominant_probability = round(
        clamp(safe_float(dominant.get("probability", probabilities.get(dominant_id, 0.0)), probabilities.get(dominant_id, 0.0)), 0.0, 1.0),
        4,
    )
    dominant_risk_score = round(clamp(safe_float(dominant.get("risk_score", overall_risk_score), overall_risk_score), 0.0, 1.0), 4)
    dominant_risk_level = normalize_risk_level(dominant.get("risk_level"), dominant_risk_score)

    output = {
        "version": VERSION,
        "generated_at": generated_at,
        "as_of": as_of,
        "horizon_days": horizon_days,
        "engine": "prediction_engine",
        "source": {
            "scenario_file": "analysis/prediction/scenario_latest.json",
            "scenario_count": len(scenarios),
        },
        "regime": regime,
        "overall_risk": overall_risk_level,
        "overall_risk_level": overall_risk_level,
        "overall_risk_score": overall_risk_score,
        "signal": dominant_risk_level,
        "confidence": confidence,
        "dominant_scenario": dominant_id,
        "dominant_scenario_name": str(pick(dominant, "name", default=to_title(dominant_id))),
        "dominant_probability": dominant_probability,
        "summary": summary,
        "scenario_probabilities": probabilities,
        "drivers": drivers,
        "watchpoints": watchpoints,
        "invalidation_conditions": invalidation_conditions,
        "early_warning": {
            "warning_level": str(pick(early_warning, "warning_level", default="quiet")),
            "warning_score": round(clamp(safe_float(pick(early_warning, "warning_score", default=0.0), 0.0), 0.0, 1.0), 4),
            "headline": str(pick(early_warning, "headline", default="No strong early warning cluster is active.")),
        },
        "dominant_branch": {
            "scenario_id": dominant_id,
            "name": str(pick(dominant, "name", default=to_title(dominant_id))),
            "regime": regime,
            "risk_level": dominant_risk_level,
            "risk_score": dominant_risk_score,
            "probability": dominant_probability,
            "confidence": round(dominant_confidence, 4),
            "summary": str(pick(dominant, "summary", default="")),
            "drivers": dominant.get("drivers", []) if isinstance(dominant.get("drivers"), list) else [],
            "watchpoints": dominant.get("watchpoints", []) if isinstance(dominant.get("watchpoints"), list) else [],
            "invalidation_conditions": dominant.get("invalidation_conditions", []) if isinstance(dominant.get("invalidation_conditions"), list) else [],
            "supporting_signals": dominant.get("supporting_signals", []) if isinstance(dominant.get("supporting_signals"), list) else [],
            "assumptions": dominant.get("assumptions", []) if isinstance(dominant.get("assumptions"), list) else [],
        },
        "scenario_summary": {
            "best_case": scenarios.get("best_case", {}),
            "base_case": scenarios.get("base_case", {}),
            "worst_case": scenarios.get("worst_case", {}),
        },
        "signal_rollup": signal_rollup,
        "ui": {
            "prediction_card": {
                "date": as_of,
                "regime": regime,
                "signal": dominant_risk_level,
                "confidence": confidence,
                "health": "OK" if scenarios else "DEGRADED",
            }
        },
        "notes": [
            "Prediction is a public-facing summary of the current scenario stack.",
            "Confidence expresses current alignment strength, not certainty of being correct.",
            "Scenario remains the branching layer; prediction should not recreate branch logic in UI.",
        ],
    }
    return output


def build_empty_payload(as_of: str, generated_at: str, horizon_days: int, reason: str) -> Dict[str, Any]:
    return {
        "version": VERSION,
        "generated_at": generated_at,
        "as_of": as_of,
        "horizon_days": horizon_days,
        "engine": "prediction_engine",
        "source": {
            "scenario_file": "analysis/prediction/scenario_latest.json",
            "scenario_count": 0,
        },
        "regime": "Stable",
        "overall_risk": "low",
        "overall_risk_level": "low",
        "overall_risk_score": 0.0,
        "signal": "guarded",
        "confidence": 0.0,
        "dominant_scenario": "base_case",
        "dominant_scenario_name": "Base Case",
        "dominant_probability": 0.5,
        "summary": reason,
        "scenario_probabilities": {
            "best_case": 0.25,
            "base_case": 0.5,
            "worst_case": 0.25,
        },
        "drivers": [],
        "watchpoints": [],
        "invalidation_conditions": [],
        "early_warning": {
            "warning_level": "quiet",
            "warning_score": 0.0,
            "headline": reason,
        },
        "dominant_branch": {
            "scenario_id": "base_case",
            "name": "Base Case",
            "regime": "Stable",
            "risk_level": "guarded",
            "risk_score": 0.0,
            "probability": 0.5,
            "confidence": 0.0,
            "summary": reason,
            "drivers": [],
            "watchpoints": [],
            "invalidation_conditions": [],
            "supporting_signals": [],
            "assumptions": [],
        },
        "scenario_summary": {
            "best_case": {},
            "base_case": {},
            "worst_case": {},
        },
        "signal_rollup": {
            "supporting_signal_count": 0,
            "high_or_critical_support_count": 0,
            "metrics": [],
            "signal_types": [],
        },
        "ui": {
            "prediction_card": {
                "date": as_of,
                "regime": "Stable",
                "signal": "guarded",
                "confidence": 0.0,
                "health": "DEGRADED",
            }
        },
        "notes": [reason],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build prediction_latest.json from scenario artifacts")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--input",
        default=None,
        help="Optional explicit scenario_latest.json path. Defaults to <root>/analysis/prediction/scenario_latest.json",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional explicit output directory. Defaults to <root>/analysis/prediction",
    )
    parser.add_argument("--horizon-days", type=int, default=DEFAULT_HORIZON_DAYS, help="Prediction horizon in days.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else root / "analysis" / "prediction"
    scenario_path = Path(args.input).resolve() if args.input else output_dir / "scenario_latest.json"

    generated_at = utc_now_iso()

    if not scenario_path.exists():
        payload = build_empty_payload(
            as_of=datetime.now().date().isoformat(),
            generated_at=generated_at,
            horizon_days=args.horizon_days,
            reason=f"scenario input not found: {scenario_path}",
        )
        save_json(output_dir / "prediction_latest.json", payload)
        print(f"[prediction_engine] input missing; wrote empty artifact to {output_dir}")
        return 0

    scenario_payload = load_json(scenario_path)
    as_of = str(pick(scenario_payload, "as_of", "date", default=datetime.now().date().isoformat()))
    horizon_days = int(safe_float(pick(scenario_payload, "horizon_days", default=args.horizon_days), args.horizon_days))

    scenarios = build_scenario_index(scenario_payload)
    if not scenarios:
        payload = build_empty_payload(
            as_of=as_of,
            generated_at=generated_at,
            horizon_days=horizon_days,
            reason="scenario input exists but no usable scenario records were found",
        )
    else:
        payload = build_prediction_payload(
            scenario_payload=scenario_payload,
            as_of=as_of,
            generated_at=generated_at,
            horizon_days=horizon_days,
        )

    save_json(output_dir / "prediction_latest.json", payload)
    print(f"[prediction_engine] wrote {output_dir / 'prediction_latest.json'}")
    print(
        f"[prediction_engine] dominant={payload.get('dominant_scenario', 'base_case')} "
        f"risk={payload.get('overall_risk_level', 'low')} confidence={payload.get('confidence', 0.0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

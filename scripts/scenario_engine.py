#!/usr/bin/env python3
"""GenesisPrediction v2 - Scenario Engine

Builds scenario_latest.json from signal_latest.json and early_warning_latest.json.

Design intent:
- analysis/ is the Single Source of Truth
- scripts generate artifacts only
- Scenario organizes multiple plausible futures, not a single forecast
- Scenario must be explainable with probabilities, drivers, watchpoints,
  invalidation_conditions, and confidence

This implementation is intentionally schema-tolerant because upstream Signal
artifacts may evolve. It consumes the stable parts of signal_latest.json while
being resilient to missing or partially changed fields.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


VERSION = "1.0"
DEFAULT_HORIZON_DAYS = 7


@dataclass
class NormalizedSignal:
    signal_id: str
    signal_type: str
    metric: str
    label: str
    direction: str
    severity: str
    severity_score: float
    confidence: float
    rationale: str
    watchpoint: str
    tags: List[str]
    details: Dict[str, Any]


@dataclass
class ScenarioBranch:
    scenario_id: str
    name: str
    horizon_days: int
    probability: float
    confidence: float
    regime: str
    risk_level: str
    risk_score: float
    summary: str
    drivers: List[str]
    watchpoints: List[str]
    invalidation_conditions: List[str]
    supporting_signals: List[Dict[str, Any]]
    assumptions: List[str]


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


def to_title(text: str) -> str:
    return str(text or "").replace("_", " ").replace("-", " ").strip().title()


def normalize_severity(raw: Any, score: float) -> str:
    text = str(raw or "").strip().lower()
    if text in {"low", "medium", "high", "critical"}:
        return text
    if score >= 0.9:
        return "critical"
    if score >= 0.72:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def normalize_direction(raw: Any) -> str:
    text = str(raw or "").strip().lower()
    if not text:
        return "stable"
    mapping = {
        "up": "rising",
        "uptrend": "rising",
        "increase": "rising",
        "rising": "rising",
        "down": "falling",
        "downtrend": "falling",
        "decrease": "falling",
        "falling": "falling",
        "flat": "stable",
        "stable": "stable",
        "reversal": "reversal",
        "reversing": "reversal",
        "accelerating": "accelerating",
    }
    return mapping.get(text, text)


def iter_signal_candidates(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    if isinstance(payload.get("signals"), list):
        for item in payload["signals"]:
            if isinstance(item, dict):
                yield item

    for bucket_name in ("items", "signal_list"):
        bucket = payload.get(bucket_name)
        if isinstance(bucket, list):
            for item in bucket:
                if isinstance(item, dict):
                    yield item


def normalize_signal(item: Dict[str, Any], idx: int) -> NormalizedSignal:
    signal_type = str(pick(item, "signal_type", "type", default="unknown"))
    metric = str(pick(item, "metric", "key", "name", default=f"metric_{idx}"))
    label = str(pick(item, "label", "title", default=metric))
    severity_score = clamp(safe_float(pick(item, "severity_score", "score", default=0.0)), 0.0, 1.0)
    confidence = clamp(safe_float(pick(item, "confidence", default=0.5), 0.5), 0.0, 1.0)
    severity = normalize_severity(pick(item, "severity"), severity_score)
    direction = normalize_direction(pick(item, "direction", default="stable"))
    rationale = str(pick(item, "rationale", default="No rationale provided."))
    watchpoint = str(pick(item, "watchpoint", default=f"Watch whether {label} changes materially on the next run."))
    tags = [str(x) for x in item.get("tags", []) if x not in (None, "")]
    details = item.get("details", {}) if isinstance(item.get("details"), dict) else {}
    signal_id = str(pick(item, "signal_id", default=f"{signal_type}:{metric}:{idx}"))

    return NormalizedSignal(
        signal_id=signal_id,
        signal_type=signal_type,
        metric=metric,
        label=label,
        direction=direction,
        severity=severity,
        severity_score=severity_score,
        confidence=confidence,
        rationale=rationale,
        watchpoint=watchpoint,
        tags=tags,
        details=details,
    )


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


def regime_from_risk(score: float, destabilizing_count: int) -> str:
    if score >= 0.86:
        return "Crisis"
    if score >= 0.68:
        return "Tension"
    if destabilizing_count >= 2 and score >= 0.42:
        return "Transition"
    return "Stable"


def summarize_signal_mix(signals: List[NormalizedSignal]) -> Dict[str, int]:
    summary: Dict[str, int] = {
        "total": len(signals),
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
        "destabilizing": 0,
        "stabilizing": 0,
    }
    for signal in signals:
        summary[signal.severity] = summary.get(signal.severity, 0) + 1
        if is_destabilizing(signal):
            summary["destabilizing"] += 1
        else:
            summary["stabilizing"] += 1
    return summary


def is_destabilizing(signal: NormalizedSignal) -> bool:
    destabilizing_types = {
        "anomaly",
        "regime_shift",
        "volatility_expansion",
        "acceleration",
        "reversal",
    }
    if signal.signal_type in destabilizing_types:
        return True
    if signal.direction in {"accelerating", "reversal"}:
        return True
    if signal.severity in {"high", "critical"} and signal.direction in {"rising", "falling"}:
        return True
    return False


def score_signals(signals: List[NormalizedSignal]) -> Tuple[float, float, float]:
    if not signals:
        return 0.0, 0.0, 0.0

    destabilizing = 0.0
    stabilizing = 0.0
    confidence_weight = 0.0

    for signal in signals:
        weight = signal.severity_score * (0.55 + 0.45 * signal.confidence)
        confidence_weight += signal.confidence
        if is_destabilizing(signal):
            destabilizing += weight
        else:
            stabilizing += weight * 0.7

    mean_confidence = clamp(confidence_weight / len(signals), 0.0, 1.0)
    raw_pressure = max(0.0, destabilizing - stabilizing)
    max_possible = max(1.0, len(signals) * 0.95)
    pressure_score = clamp(raw_pressure / max_possible, 0.0, 1.0)
    stabilization_score = clamp(stabilizing / max_possible, 0.0, 1.0)
    return pressure_score, stabilization_score, mean_confidence


def normalize_probabilities(best: float, base: float, worst: float) -> Tuple[float, float, float]:
    total = max(best + base + worst, 1e-9)
    best_n = best / total
    base_n = base / total
    worst_n = worst / total

    # round and force exact 1.0 total
    best_r = round(best_n, 4)
    base_r = round(base_n, 4)
    worst_r = round(1.0 - best_r - base_r, 4)
    if worst_r < 0:
        worst_r = 0.0
        base_r = round(1.0 - best_r, 4)
    return best_r, base_r, worst_r


def select_supporting_signals(signals: List[NormalizedSignal], predicate, limit: int = 5) -> List[NormalizedSignal]:
    matched = [s for s in signals if predicate(s)]
    matched.sort(key=lambda s: (s.severity_score, s.confidence), reverse=True)
    return matched[:limit]


def signals_to_refs(signals: List[NormalizedSignal]) -> List[Dict[str, Any]]:
    return [
        {
            "signal_id": s.signal_id,
            "signal_type": s.signal_type,
            "metric": s.metric,
            "severity": s.severity,
            "severity_score": round(s.severity_score, 4),
            "confidence": round(s.confidence, 4),
        }
        for s in signals
    ]


def build_best_case(
    signals: List[NormalizedSignal],
    horizon_days: int,
    probability: float,
    scenario_confidence: float,
    stabilization_score: float,
) -> ScenarioBranch:
    supporting = select_supporting_signals(
        signals,
        lambda s: (not is_destabilizing(s)) or s.signal_type == "reversal",
    )
    risk_score = clamp(0.12 + (0.38 * (1.0 - stabilization_score)), 0.0, 1.0)
    regime = regime_from_risk(risk_score, sum(1 for s in supporting if is_destabilizing(s)))
    drivers = [
        "Stress signals fail to broaden across multiple metrics.",
        "Recent anomalies normalize instead of compounding.",
        "Scenario pressure remains contained within the short horizon.",
    ]
    if supporting:
        drivers.extend([f"{to_title(s.label)} supports stabilization or reversal." for s in supporting[:2]])

    watchpoints = [
        "Watch whether high-severity signals decay on the next 1-2 runs.",
        "Watch whether anomaly and volatility signals lose intensity quickly.",
    ]
    if supporting:
        watchpoints.append(supporting[0].watchpoint)

    invalidation_conditions = [
        "A new cluster of high or critical destabilizing signals appears.",
        "Volatility expansion spreads across multiple metrics instead of fading.",
        "Early warning level rises to high or critical and persists.",
    ]

    assumptions = [
        "Current signal stress is temporary rather than structural.",
        "No major reinforcing shock emerges inside the horizon window.",
    ]

    return ScenarioBranch(
        scenario_id="best_case",
        name="Best Case",
        horizon_days=horizon_days,
        probability=round(probability, 4),
        confidence=round(clamp(scenario_confidence * 0.92, 0.0, 1.0), 4),
        regime=regime,
        risk_level=risk_level_from_score(risk_score),
        risk_score=round(risk_score, 4),
        summary="Signal stress fades, anomalies normalize, and near-term conditions stabilize faster than feared.",
        drivers=drivers[:5],
        watchpoints=watchpoints[:5],
        invalidation_conditions=invalidation_conditions,
        supporting_signals=signals_to_refs(supporting),
        assumptions=assumptions,
    )


def build_base_case(
    signals: List[NormalizedSignal],
    horizon_days: int,
    probability: float,
    scenario_confidence: float,
    pressure_score: float,
) -> ScenarioBranch:
    supporting = select_supporting_signals(signals, lambda s: True)
    destabilizing_count = sum(1 for s in supporting if is_destabilizing(s))
    risk_score = clamp(0.28 + (0.55 * pressure_score), 0.0, 1.0)
    regime = regime_from_risk(risk_score, destabilizing_count)

    drivers = [
        "The most likely path is continuation of the current signal mix.",
        "Pressure is meaningful but not yet decisive enough for a full breakdown case.",
        "Several signals remain active, but cross-metric confirmation is incomplete.",
    ]
    drivers.extend([f"{to_title(s.label)} remains an active driver through {s.signal_type}." for s in supporting[:2]])

    watchpoints = [
        "Watch whether medium signals upgrade into high-severity clusters.",
        "Watch whether acceleration persists into regime-shift confirmation.",
    ]
    if supporting:
        watchpoints.append(supporting[0].watchpoint)
        if len(supporting) > 1:
            watchpoints.append(supporting[1].watchpoint)

    invalidation_conditions = [
        "Several top signals normalize quickly, reducing scenario pressure.",
        "A destabilizing signal cluster broadens and forces the path toward worst case.",
        "Scenario confidence drops because signals diverge sharply across metrics.",
    ]

    assumptions = [
        "The current environment persists without a decisive external break.",
        "Observed signals remain directionally valid over the tactical horizon.",
    ]

    return ScenarioBranch(
        scenario_id="base_case",
        name="Base Case",
        horizon_days=horizon_days,
        probability=round(probability, 4),
        confidence=round(clamp(scenario_confidence, 0.0, 1.0), 4),
        regime=regime,
        risk_level=risk_level_from_score(risk_score),
        risk_score=round(risk_score, 4),
        summary="Current pressures continue unevenly: instability remains elevated, but the system does not fully break inside the horizon.",
        drivers=drivers[:5],
        watchpoints=watchpoints[:5],
        invalidation_conditions=invalidation_conditions,
        supporting_signals=signals_to_refs(supporting),
        assumptions=assumptions,
    )


def build_worst_case(
    signals: List[NormalizedSignal],
    horizon_days: int,
    probability: float,
    scenario_confidence: float,
    pressure_score: float,
) -> ScenarioBranch:
    supporting = select_supporting_signals(signals, is_destabilizing)
    destabilizing_count = sum(1 for s in supporting if is_destabilizing(s))
    risk_score = clamp(0.52 + (0.44 * pressure_score), 0.0, 1.0)
    regime = regime_from_risk(risk_score, destabilizing_count)

    drivers = [
        "Destabilizing signals reinforce each other instead of fading.",
        "Volatility, anomaly, and regime-shift conditions begin to cluster.",
        "The signal stack transitions from warning to active structural stress.",
    ]
    drivers.extend([f"{to_title(s.label)} increases downside risk through {s.signal_type}." for s in supporting[:2]])

    watchpoints = [
        "Watch for persistence of high or critical signals across consecutive runs.",
        "Watch for early warning concentration to remain elevated or worsen.",
    ]
    if supporting:
        watchpoints.append(supporting[0].watchpoint)
        if len(supporting) > 1:
            watchpoints.append(supporting[1].watchpoint)

    invalidation_conditions = [
        "Top destabilizing signals fade quickly instead of compounding.",
        "Expected regime shift fails to gain cross-metric confirmation.",
        "Scenario pressure falls back toward guarded levels.",
    ]

    assumptions = [
        "Signal pressure compounds rather than mean-reverting.",
        "The next observations validate stress broadening across metrics.",
    ]

    return ScenarioBranch(
        scenario_id="worst_case",
        name="Worst Case",
        horizon_days=horizon_days,
        probability=round(probability, 4),
        confidence=round(clamp(scenario_confidence * 1.04, 0.0, 1.0), 4),
        regime=regime,
        risk_level=risk_level_from_score(risk_score),
        risk_score=round(risk_score, 4),
        summary="Signal pressure compounds, cross-metric stress broadens, and the horizon shifts toward a sharper instability regime.",
        drivers=drivers[:5],
        watchpoints=watchpoints[:5],
        invalidation_conditions=invalidation_conditions,
        supporting_signals=signals_to_refs(supporting),
        assumptions=assumptions,
    )


def compute_probabilities(signals: List[NormalizedSignal], early_warning: Dict[str, Any]) -> Tuple[float, float, float, float, float, float]:
    pressure_score, stabilization_score, mean_confidence = score_signals(signals)
    warning_score = clamp(safe_float(pick(early_warning, "warning_score", default=0.0)), 0.0, 1.0)
    warning_level = str(pick(early_warning, "warning_level", default="quiet")).lower()

    level_boost = {
        "quiet": 0.0,
        "guarded": 0.04,
        "elevated": 0.09,
        "high": 0.16,
        "critical": 0.24,
    }.get(warning_level, 0.0)

    worst_raw = 0.18 + (0.62 * pressure_score) + (0.18 * warning_score) + level_boost
    best_raw = 0.18 + (0.48 * (1.0 - pressure_score)) + (0.22 * stabilization_score) - (0.12 * warning_score)
    base_raw = 0.36 + (0.25 * (1.0 - abs(0.5 - pressure_score))) + (0.10 * mean_confidence)

    best_p, base_p, worst_p = normalize_probabilities(
        clamp(best_raw, 0.05, 0.85),
        clamp(base_raw, 0.10, 0.90),
        clamp(worst_raw, 0.05, 0.90),
    )
    scenario_confidence = clamp((mean_confidence * 0.55) + (warning_score * 0.20) + (min(len(signals), 8) / 8.0 * 0.25), 0.0, 1.0)
    return best_p, base_p, worst_p, pressure_score, stabilization_score, scenario_confidence


def build_scenario_payload(signal_payload: Dict[str, Any], early_warning: Dict[str, Any], signals: List[NormalizedSignal], as_of: str, generated_at: str, horizon_days: int) -> Dict[str, Any]:
    best_p, base_p, worst_p, pressure_score, stabilization_score, scenario_confidence = compute_probabilities(signals, early_warning)

    best_case = build_best_case(signals, horizon_days, best_p, scenario_confidence, stabilization_score)
    base_case = build_base_case(signals, horizon_days, base_p, scenario_confidence, pressure_score)
    worst_case = build_worst_case(signals, horizon_days, worst_p, scenario_confidence, pressure_score)

    scenarios = [best_case, base_case, worst_case]
    dominant = max(scenarios, key=lambda s: s.probability)
    overall_risk_score = round(sum(s.probability * s.risk_score for s in scenarios), 4)
    overall_risk_level = risk_level_from_score(overall_risk_score)
    regime = dominant.regime if dominant.scenario_id != "base_case" else regime_from_risk(
        overall_risk_score,
        sum(1 for s in signals if is_destabilizing(s)),
    )

    mix_summary = summarize_signal_mix(signals)
    drivers = []
    watchpoints = []
    invalidation_conditions = []
    for branch in scenarios:
        drivers.extend(branch.drivers[:2])
        watchpoints.extend(branch.watchpoints[:2])
        invalidation_conditions.extend(branch.invalidation_conditions[:1])

    drivers = list(dict.fromkeys(drivers))[:8]
    watchpoints = list(dict.fromkeys(watchpoints))[:8]
    invalidation_conditions = list(dict.fromkeys(invalidation_conditions))[:6]

    summary = (
        f"Base case remains the most likely near-term path at {base_case.probability:.0%}, "
        f"with downside pressure kept visible by a {worst_case.probability:.0%} worst-case branch. "
        f"Overall risk is {overall_risk_level}."
    )
    if dominant.scenario_id == "worst_case":
        summary = (
            f"Worst case is now the dominant branch at {worst_case.probability:.0%}, "
            f"indicating concentrated signal stress and elevated downside risk over the next {horizon_days} days."
        )
    elif dominant.scenario_id == "best_case":
        summary = (
            f"Best case narrowly leads at {best_case.probability:.0%}, "
            f"suggesting stress could normalize if current warnings fail to broaden over the next {horizon_days} days."
        )

    return {
        "version": VERSION,
        "generated_at": generated_at,
        "as_of": as_of,
        "horizon_days": horizon_days,
        "engine": "scenario_engine",
        "source": {
            "signal_file": "analysis/prediction/signal_latest.json",
            "early_warning_file": "analysis/prediction/early_warning_latest.json",
            "signal_count": len(signals),
        },
        "regime": regime,
        "overall_risk_level": overall_risk_level,
        "overall_risk_score": overall_risk_score,
        "scenario_confidence": round(scenario_confidence, 4),
        "dominant_scenario": dominant.scenario_id,
        "dominant_probability": round(dominant.probability, 4),
        "summary": summary,
        "probabilities": {
            "best_case": round(best_case.probability, 4),
            "base_case": round(base_case.probability, 4),
            "worst_case": round(worst_case.probability, 4),
        },
        "best_case": asdict(best_case),
        "base_case": asdict(base_case),
        "worst_case": asdict(worst_case),
        "scenarios": [asdict(best_case), asdict(base_case), asdict(worst_case)],
        "drivers": drivers,
        "watchpoints": watchpoints,
        "invalidation_conditions": invalidation_conditions,
        "signal_mix_summary": mix_summary,
        "early_warning": {
            "warning_level": str(pick(early_warning, "warning_level", default="quiet")),
            "warning_score": round(clamp(safe_float(pick(early_warning, "warning_score", default=0.0)), 0.0, 1.0), 4),
            "headline": str(pick(early_warning, "headline", default="No strong early warning cluster is active.")),
        },
        "notes": [
            "Scenario organizes multiple plausible futures from the current signal stack.",
            "Probabilities are relative branch weights, not certainty claims.",
            "Prediction layer should consume this artifact without recreating signal logic.",
        ],
        "upstream_summary": signal_payload.get("signal_types_summary", {}),
    }


def build_empty_payload(as_of: str, generated_at: str, horizon_days: int, reason: str) -> Dict[str, Any]:
    empty_branch = ScenarioBranch(
        scenario_id="best_case",
        name="Best Case",
        horizon_days=horizon_days,
        probability=0.25,
        confidence=0.0,
        regime="Stable",
        risk_level="low",
        risk_score=0.0,
        summary="Scenario input unavailable.",
        drivers=[],
        watchpoints=[],
        invalidation_conditions=[],
        supporting_signals=[],
        assumptions=[],
    )
    base_branch = ScenarioBranch(
        scenario_id="base_case",
        name="Base Case",
        horizon_days=horizon_days,
        probability=0.5,
        confidence=0.0,
        regime="Stable",
        risk_level="guarded",
        risk_score=0.0,
        summary="Scenario input unavailable.",
        drivers=[],
        watchpoints=[],
        invalidation_conditions=[],
        supporting_signals=[],
        assumptions=[],
    )
    worst_branch = ScenarioBranch(
        scenario_id="worst_case",
        name="Worst Case",
        horizon_days=horizon_days,
        probability=0.25,
        confidence=0.0,
        regime="Stable",
        risk_level="low",
        risk_score=0.0,
        summary="Scenario input unavailable.",
        drivers=[],
        watchpoints=[],
        invalidation_conditions=[],
        supporting_signals=[],
        assumptions=[],
    )
    return {
        "version": VERSION,
        "generated_at": generated_at,
        "as_of": as_of,
        "horizon_days": horizon_days,
        "engine": "scenario_engine",
        "source": {
            "signal_file": "analysis/prediction/signal_latest.json",
            "early_warning_file": "analysis/prediction/early_warning_latest.json",
            "signal_count": 0,
        },
        "regime": "Stable",
        "overall_risk_level": "low",
        "overall_risk_score": 0.0,
        "scenario_confidence": 0.0,
        "dominant_scenario": "base_case",
        "dominant_probability": 0.5,
        "summary": reason,
        "probabilities": {
            "best_case": 0.25,
            "base_case": 0.5,
            "worst_case": 0.25,
        },
        "best_case": asdict(empty_branch),
        "base_case": asdict(base_branch),
        "worst_case": asdict(worst_branch),
        "scenarios": [asdict(empty_branch), asdict(base_branch), asdict(worst_branch)],
        "drivers": [],
        "watchpoints": [],
        "invalidation_conditions": [],
        "signal_mix_summary": {
            "total": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
            "destabilizing": 0,
            "stabilizing": 0,
        },
        "early_warning": {
            "warning_level": "quiet",
            "warning_score": 0.0,
            "headline": reason,
        },
        "notes": [reason],
        "upstream_summary": {},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build scenario_latest.json from signal artifacts")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--input",
        default=None,
        help="Optional explicit signal_latest.json path. Defaults to <root>/analysis/prediction/signal_latest.json",
    )
    parser.add_argument(
        "--early-warning-input",
        default=None,
        help="Optional explicit early_warning_latest.json path. Defaults to <root>/analysis/prediction/early_warning_latest.json",
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
    signal_path = Path(args.input).resolve() if args.input else output_dir / "signal_latest.json"
    early_warning_path = (
        Path(args.early_warning_input).resolve() if args.early_warning_input else output_dir / "early_warning_latest.json"
    )

    generated_at = utc_now_iso()

    if not signal_path.exists():
        payload = build_empty_payload(
            as_of=datetime.now().date().isoformat(),
            generated_at=generated_at,
            horizon_days=args.horizon_days,
            reason=f"signal input not found: {signal_path}",
        )
        save_json(output_dir / "scenario_latest.json", payload)
        print(f"[scenario_engine] input missing; wrote empty artifact to {output_dir}")
        return 0

    signal_payload = load_json(signal_path)
    as_of = str(pick(signal_payload, "as_of", "date", default=datetime.now().date().isoformat()))
    horizon_days = int(safe_float(pick(signal_payload, "horizon_days", default=args.horizon_days), args.horizon_days))

    early_warning: Dict[str, Any]
    if early_warning_path.exists():
        early_warning = load_json(early_warning_path)
    else:
        early_warning = {
            "warning_level": pick(signal_payload.get("early_warning", {}), "warning_level", default="quiet"),
            "warning_score": pick(signal_payload.get("early_warning", {}), "warning_score", default=0.0),
            "headline": pick(signal_payload.get("early_warning", {}), "headline", default="No strong early warning cluster is active."),
        }

    signals = [normalize_signal(item, idx) for idx, item in enumerate(iter_signal_candidates(signal_payload))]

    if not signals:
        payload = build_empty_payload(
            as_of=as_of,
            generated_at=generated_at,
            horizon_days=horizon_days,
            reason="signal input exists but no usable signal records were found",
        )
    else:
        payload = build_scenario_payload(
            signal_payload=signal_payload,
            early_warning=early_warning,
            signals=signals,
            as_of=as_of,
            generated_at=generated_at,
            horizon_days=horizon_days,
        )

    save_json(output_dir / "scenario_latest.json", payload)
    print(f"[scenario_engine] wrote {output_dir / 'scenario_latest.json'}")
    print(
        f"[scenario_engine] dominant={payload.get('dominant_scenario', 'base_case')} "
        f"risk={payload.get('overall_risk_level', 'low')} confidence={payload.get('scenario_confidence', 0.0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

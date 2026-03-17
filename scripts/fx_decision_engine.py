#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenesisPrediction v2
FX Decision Engine (Phase5-A)

Purpose
-------
Convert prediction outputs into actionable FX decision artifacts.

Design Principles
-----------------
- analysis/ is the Single Source of Truth
- scripts/ perform calculation only
- UI reads artifacts only
- v1 should remain rule-based and explainable
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_PREDICTION_PATH = Path("analysis/prediction/prediction_latest.json")
DEFAULT_FX_INPUTS_PATH = Path("analysis/fx/fx_inputs_latest.json")
DEFAULT_OUTPUT_DIR = Path("analysis/fx")

PAIR_ORDER = ["JPYTHB", "USDJPY", "USDTHB"]


@dataclass
class PairDecision:
    pair: str
    decision: str
    reason: str
    confidence: float
    prediction_bias: float
    fx_bias: float
    combined_score: float
    watchpoints: List[str]
    inputs: Dict[str, Any]


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing input: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize_text_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def lower_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip().lower()


def extract_prediction_fields(prediction: Dict[str, Any]) -> Dict[str, Any]:
    scenarios = prediction.get("scenarios", {})
    scenario_probabilities = prediction.get("scenario_probabilities", {})

    best_case = (
        prediction.get("best_case")
        or scenario_probabilities.get("best_case")
        or scenarios.get("best_case", {}).get("probability")
        or scenarios.get("best", {}).get("probability")
        or 0.0
    )
    base_case = (
        prediction.get("base_case")
        or scenario_probabilities.get("base_case")
        or scenarios.get("base_case", {}).get("probability")
        or scenarios.get("base", {}).get("probability")
        or 0.0
    )
    worst_case = (
        prediction.get("worst_case")
        or scenario_probabilities.get("worst_case")
        or scenarios.get("worst_case", {}).get("probability")
        or scenarios.get("worst", {}).get("probability")
        or 0.0
    )

    return {
        "as_of": str(prediction.get("as_of") or "").strip(),
        "overall_risk": lower_text(
            prediction.get("overall_risk")
            or prediction.get("risk")
            or prediction.get("risk_level"),
            default="unknown",
        ),
        "dominant_scenario": lower_text(
            prediction.get("dominant_scenario")
            or prediction.get("dominant")
            or "base_case"
        ),
        "confidence": clamp(safe_float(prediction.get("confidence"), 0.5), 0.0, 1.0),
        "watchpoints": normalize_text_list(prediction.get("watchpoints")),
        "drivers": normalize_text_list(prediction.get("drivers")),
        "best_case": clamp(safe_float(best_case, 0.0), 0.0, 1.0),
        "base_case": clamp(safe_float(base_case, 0.0), 0.0, 1.0),
        "worst_case": clamp(safe_float(worst_case, 0.0), 0.0, 1.0),
    }


def extract_pair_inputs(fx_inputs: Dict[str, Any], pair: str) -> Dict[str, Any]:
    pairs = fx_inputs.get("pairs", {})
    raw = pairs.get(pair, {})

    return {
        "rate": raw.get("rate"),
        "change_1d_pct": safe_float(raw.get("change_1d_pct"), 0.0),
        "change_7d_pct": safe_float(raw.get("change_7d_pct"), 0.0),
        "change_30d_pct": safe_float(raw.get("change_30d_pct"), 0.0),
        "volatility_7d": safe_float(raw.get("volatility_7d"), 0.0),
        "trend": lower_text(raw.get("trend"), default="stable") or "stable",
        "ma_gap_pct": safe_float(raw.get("ma_gap_pct"), 0.0),
    }


def score_prediction_bias(pred: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    notes: List[str] = []

    risk = pred["overall_risk"]
    dominant = pred["dominant_scenario"]
    confidence = float(pred["confidence"])
    worst_case = float(pred["worst_case"])
    best_case = float(pred["best_case"])
    watchpoints_text = " ".join(pred["watchpoints"]).lower()
    drivers_text = " ".join(pred["drivers"]).lower()

    if risk in {"crisis", "high", "elevated", "severe"}:
        score -= 0.35
        notes.append(f"prediction risk={risk}")
    elif risk in {"guarded", "moderate"}:
        score -= 0.10
        notes.append(f"prediction risk={risk}")
    elif risk in {"stable", "low"}:
        score += 0.10
        notes.append(f"prediction risk={risk}")
    else:
        notes.append(f"prediction risk={risk}")

    if dominant == "worst_case":
        score -= 0.30
        notes.append("dominant scenario=worst_case")
    elif dominant == "best_case":
        score += 0.20
        notes.append("dominant scenario=best_case")
    else:
        notes.append(f"dominant scenario={dominant}")

    confidence_adjustment = clamp((confidence - 0.50) * 0.40, -0.10, 0.10)
    score += confidence_adjustment
    notes.append(f"prediction confidence={confidence:.2f}")

    if worst_case >= 0.45:
        score -= 0.15
        notes.append("worst-case probability elevated")

    if best_case >= 0.45:
        score += 0.10
        notes.append("best-case probability supportive")

    danger_keywords = [
        "war",
        "conflict",
        "sanction",
        "intervention",
        "volatility",
        "shock",
        "crisis",
        "liquidity",
        "escalation",
        "military",
    ]

    if any(k in watchpoints_text for k in danger_keywords):
        score -= 0.10
        notes.append("watchpoints contain danger keywords")

    if any(k in drivers_text for k in danger_keywords):
        score -= 0.05
        notes.append("drivers contain danger keywords")

    return clamp(score, -0.70, 0.40), notes


def score_fx_bias(pair: str, fx: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    notes: List[str] = []

    change_7d = float(fx["change_7d_pct"])
    change_30d = float(fx["change_30d_pct"])
    vol_7d = float(fx["volatility_7d"])
    trend = fx["trend"]
    ma_gap_pct = float(fx["ma_gap_pct"])

    if vol_7d >= 2.0:
        score -= 0.35
        notes.append(f"very high volatility={vol_7d:.2f}")
    elif vol_7d >= 1.2:
        score -= 0.20
        notes.append(f"high volatility={vol_7d:.2f}")
    elif vol_7d >= 0.8:
        score -= 0.10
        notes.append(f"moderate volatility={vol_7d:.2f}")
    else:
        notes.append(f"volatility={vol_7d:.2f}")

    if pair == "JPYTHB":
        if change_7d >= 1.0:
            score += 0.30
            notes.append("JPYTHB improved over 7d")
        elif change_7d <= -1.0:
            score -= 0.25
            notes.append("JPYTHB deteriorated over 7d")

        if change_30d >= 2.0:
            score += 0.10
            notes.append("JPYTHB improved over 30d")
        elif change_30d <= -2.0:
            score -= 0.10
            notes.append("JPYTHB weakened over 30d")

        if trend == "up":
            score += 0.15
            notes.append("JPYTHB trend=up")
        elif trend == "down":
            score -= 0.15
            notes.append("JPYTHB trend=down")

        if ma_gap_pct >= 1.0:
            score += 0.05
            notes.append("JPYTHB above moving average")
        elif ma_gap_pct <= -1.0:
            score -= 0.05
            notes.append("JPYTHB below moving average")

    elif pair == "USDJPY":
        if abs(change_7d) >= 1.5:
            score -= 0.10
            notes.append("USDJPY moved strongly over 7d")

        if abs(change_30d) >= 3.0:
            score -= 0.05
            notes.append("USDJPY moved strongly over 30d")

        if trend in {"up", "down"} and vol_7d >= 0.8:
            score -= 0.05
            notes.append("USDJPY trend + volatility caution")

    elif pair == "USDTHB":
        if abs(change_7d) >= 1.0:
            score -= 0.05
            notes.append("USDTHB moved notably over 7d")

        if trend == "stable":
            score += 0.05
            notes.append("USDTHB trend=stable")

    return clamp(score, -0.60, 0.45), notes


def decision_from_score(score: float, pred_conf: float, vol_7d: float) -> str:
    if vol_7d >= 2.0:
        return "HOLD"
    if score >= 0.25:
        return "SEND"
    if score >= 0.05:
        return "SPLIT"
    if score <= -0.35:
        return "HOLD"
    if score <= -0.10:
        return "CAUTION"
    if pred_conf < 0.45:
        return "SPLIT"
    return "CAUTION"


def build_reason(pair: str, decision: str, pred_notes: List[str], fx_notes: List[str]) -> str:
    merged = pred_notes + fx_notes
    summary = "; ".join(merged[:6])
    if summary:
        return f"{pair}: {decision}. {summary}"
    return f"{pair}: {decision}."


def build_pair_decision(
    pair: str,
    prediction_fields: Dict[str, Any],
    fx_pair: Dict[str, Any],
) -> PairDecision:
    pred_bias, pred_notes = score_prediction_bias(prediction_fields)
    fx_bias, fx_notes = score_fx_bias(pair, fx_pair)

    combined = clamp(pred_bias + fx_bias, -1.0, 1.0)

    volatility_penalty = min(float(fx_pair["volatility_7d"]) * 0.08, 0.20)
    confidence = clamp(
        0.45
        + abs(combined) * 0.35
        + (float(prediction_fields["confidence"]) - 0.50) * 0.20
        - volatility_penalty,
        0.20,
        0.90,
    )

    decision = decision_from_score(
        score=combined,
        pred_conf=float(prediction_fields["confidence"]),
        vol_7d=float(fx_pair["volatility_7d"]),
    )

    watchpoints = list(prediction_fields["watchpoints"])

    if float(fx_pair["volatility_7d"]) >= 0.8:
        watchpoints.append("fx volatility expansion")

    if abs(float(fx_pair["change_7d_pct"])) >= 1.5:
        watchpoints.append("rapid 7d move")

    if abs(float(fx_pair["change_30d_pct"])) >= 3.0:
        watchpoints.append("large 30d move")

    dedup_watchpoints: List[str] = []
    seen = set()
    for item in watchpoints:
        key = str(item).strip().lower()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        dedup_watchpoints.append(str(item).strip())

    reason = build_reason(pair, decision, pred_notes, fx_notes)

    return PairDecision(
        pair=pair,
        decision=decision,
        reason=reason,
        confidence=round(confidence, 4),
        prediction_bias=round(pred_bias, 4),
        fx_bias=round(fx_bias, 4),
        combined_score=round(combined, 4),
        watchpoints=dedup_watchpoints,
        inputs={
            "prediction": {
                "overall_risk": prediction_fields["overall_risk"],
                "dominant_scenario": prediction_fields["dominant_scenario"],
                "prediction_confidence": prediction_fields["confidence"],
                "best_case": prediction_fields["best_case"],
                "base_case": prediction_fields["base_case"],
                "worst_case": prediction_fields["worst_case"],
            },
            "fx": fx_pair,
        },
    )


def pair_payload(as_of: str, engine_version: str, pd: PairDecision) -> Dict[str, Any]:
    mode = "defensive" if pd.decision in {"HOLD", "CAUTION"} else "adaptive"

    return {
        "as_of": as_of,
        "engine_version": engine_version,
        "pair": pd.pair,
        "decision": pd.decision,
        "status": pd.decision,
        "action": pd.decision,
        "recommendation": pd.decision,
        "reason": pd.reason,
        "confidence": pd.confidence,
        "watchpoints": pd.watchpoints,
        "inputs": pd.inputs,
        "scores": {
            "prediction_bias": pd.prediction_bias,
            "fx_bias": pd.fx_bias,
            "combined_score": pd.combined_score,
        },
        "policy": {
            "mode": mode,
            "split_allowed": True,
        },
    }


def aggregate_multi(
    as_of: str,
    engine_version: str,
    pair_results: List[PairDecision],
) -> Dict[str, Any]:
    if not pair_results:
        raise ValueError("pair_results is empty")

    primary = next((x for x in pair_results if x.pair == "JPYTHB"), pair_results[0])
    decisions = {x.pair: x.decision for x in pair_results}
    avg_score = sum(x.combined_score for x in pair_results) / len(pair_results)
    avg_confidence = sum(x.confidence for x in pair_results) / len(pair_results)

    if primary.decision == "HOLD":
        overall = "HOLD"
    elif primary.decision == "SEND" and avg_score >= 0.10:
        overall = "SEND"
    elif any(x.decision == "CAUTION" for x in pair_results):
        overall = "CAUTION"
    else:
        overall = "SPLIT"

    summary_parts = [f"{x.pair}={x.decision}" for x in pair_results]
    reason = (
        f"Primary pair {primary.pair} suggests {primary.decision}. "
        f"Cross-pair summary: {', '.join(summary_parts)}."
    )

    merged_watchpoints: List[str] = []
    seen = set()
    for result in pair_results:
        for item in result.watchpoints:
            key = str(item).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            merged_watchpoints.append(str(item).strip())

    mode = "defensive" if overall in {"HOLD", "CAUTION"} else "adaptive"

    return {
        "as_of": as_of,
        "engine_version": engine_version,
        "pair": "MULTI",
        "decision": overall,
        "status": overall,
        "action": overall,
        "recommendation": overall,
        "reason": reason,
        "confidence": round(avg_confidence, 4),
        "pairs": decisions,
        "scores": {
            "average_combined_score": round(avg_score, 4),
        },
        "watchpoints": merged_watchpoints,
        "policy": {
            "mode": mode,
            "split_allowed": True,
        },
    }


def parse_iso_date(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d")
    except ValueError:
        return None


def resolve_as_of(pred: Dict[str, Any], fx_inputs: Dict[str, Any]) -> str:
    pred_as_of = str(pred.get("as_of") or "").strip()
    fx_as_of = str(fx_inputs.get("as_of") or "").strip()

    pred_dt = parse_iso_date(pred_as_of)
    fx_dt = parse_iso_date(fx_as_of)

    if pred_dt and fx_dt:
        return pred_as_of if pred_dt >= fx_dt else fx_as_of
    if fx_as_of:
        return fx_as_of
    if pred_as_of:
        return pred_as_of
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="GenesisPrediction FX Decision Engine")
    parser.add_argument(
        "--prediction",
        type=Path,
        default=DEFAULT_PREDICTION_PATH,
        help="Path to prediction_latest.json",
    )
    parser.add_argument(
        "--fx-inputs",
        type=Path,
        default=DEFAULT_FX_INPUTS_PATH,
        help="Path to fx_inputs_latest.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for fx decision artifacts",
    )
    args = parser.parse_args()

    prediction = load_json(args.prediction)
    fx_inputs = load_json(args.fx_inputs)

    ensure_dir(args.output_dir)

    pred = extract_prediction_fields(prediction)
    as_of = resolve_as_of(pred, fx_inputs)
    engine_version = "fx_decision_engine_v1"

    pair_results: List[PairDecision] = []

    for pair in PAIR_ORDER:
        fx_pair = extract_pair_inputs(fx_inputs, pair)
        result = build_pair_decision(pair, pred, fx_pair)
        pair_results.append(result)

        payload = pair_payload(as_of, engine_version, result)
        write_json(args.output_dir / f"fx_decision_latest_{pair.lower()}.json", payload)

    multi_payload = aggregate_multi(as_of, engine_version, pair_results)

    write_json(args.output_dir / "fx_decision_latest_multi.json", multi_payload)
    write_json(args.output_dir / "fx_decision_latest.json", multi_payload)

    print(f"[fx_decision_engine] wrote {args.output_dir / 'fx_decision_latest.json'}")
    for pair in PAIR_ORDER:
        print(
            f"[fx_decision_engine] wrote "
            f"{args.output_dir / f'fx_decision_latest_{pair.lower()}.json'}"
        )
    print(f"[fx_decision_engine] wrote {args.output_dir / 'fx_decision_latest_multi.json'}")
    print(f"[fx_decision_engine] primary={multi_payload['decision']}")


if __name__ == "__main__":
    main()
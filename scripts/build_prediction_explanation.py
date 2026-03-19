#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_prediction_explanation.py

Purpose:
    Generate analysis/explanation/prediction_explanation_latest.json
    from prediction-layer artifacts.

Inputs:
    - analysis/prediction/prediction_latest.json
    - analysis/prediction/scenario_latest.json
    - analysis/prediction/signal_latest.json

Output:
    - analysis/explanation/prediction_explanation_latest.json

Design principles:
    - Explanation does not create new truth.
    - Explanation is structured, not free-form creative writing.
    - Missing inputs should produce an honest unavailable artifact.
    - UI reads this artifact only; UI must not synthesize explanations.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent

PREDICTION_PATH = REPO_ROOT / "analysis" / "prediction" / "prediction_latest.json"
SCENARIO_PATH = REPO_ROOT / "analysis" / "prediction" / "scenario_latest.json"
SIGNAL_PATH = REPO_ROOT / "analysis" / "prediction" / "signal_latest.json"

EXPLANATION_DIR = REPO_ROOT / "analysis" / "explanation"
OUTPUT_PATH = EXPLANATION_DIR / "prediction_explanation_latest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build prediction explanation artifact from prediction-layer outputs."
    )
    parser.add_argument(
        "--prediction",
        type=Path,
        default=PREDICTION_PATH,
        help="Path to prediction_latest.json",
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        default=SCENARIO_PATH,
        help="Path to scenario_latest.json",
    )
    parser.add_argument(
        "--signal",
        type=Path,
        default=SIGNAL_PATH,
        help="Path to signal_latest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Path to write prediction_explanation_latest.json",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON with indentation.",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def pick_first(mapping: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    if not isinstance(mapping, dict):
        return default
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def normalize_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if item is not None]
    return [value]


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned:
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def to_text_list(value: Any) -> list[str]:
    raw_items = normalize_list(value)
    result: list[str] = []

    for item in raw_items:
        if item is None:
            continue
        if isinstance(item, str):
            text = item.strip()
            if text:
                result.append(text)
            continue
        if isinstance(item, dict):
            # Pick common human-readable fields.
            text = (
                normalize_str(item.get("text"))
                or normalize_str(item.get("label"))
                or normalize_str(item.get("title"))
                or normalize_str(item.get("name"))
                or normalize_str(item.get("summary"))
                or normalize_str(item.get("description"))
                or normalize_str(item.get("reason"))
            )
            if text:
                result.append(text)
            continue
        result.append(str(item).strip())

    return dedupe_keep_order([x for x in result if x])


def extract_as_of(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
) -> str | None:
    return (
        normalize_str(pick_first(prediction, "as_of", "date"))
        or normalize_str(pick_first(scenario, "as_of", "date"))
        or normalize_str(pick_first(signal, "as_of", "date"))
    )


def extract_dominant_scenario(prediction: dict[str, Any] | None) -> str | None:
    value = normalize_str(
        pick_first(
            prediction,
            "dominant_scenario",
            "dominantScenario",
            "scenario",
            "regime",
        )
    )
    return value


def extract_confidence(prediction: dict[str, Any] | None) -> float | None:
    value = pick_first(prediction, "confidence", default=None)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except Exception:
            return None
    return None


def confidence_band(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.45:
        return "medium"
    return "low"


def extract_summary(prediction: dict[str, Any] | None) -> str | None:
    return normalize_str(
        pick_first(
            prediction,
            "summary",
            "headline_summary",
            "text_summary",
            "description",
        )
    )


def extract_drivers(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
    dominant_scenario: str | None,
    confidence: float | None,
) -> list[str]:
    collected: list[str] = []

    pred_drivers = to_text_list(pick_first(prediction, "drivers", default=[]))
    scen_drivers = to_text_list(pick_first(scenario, "drivers", default=[]))
    signal_drivers = to_text_list(pick_first(signal, "drivers", "signals", default=[]))

    collected.extend(pred_drivers)
    collected.extend(scen_drivers[:2])
    collected.extend(signal_drivers[:2])

    if dominant_scenario:
        collected.insert(0, f"dominant_scenario は現在 {dominant_scenario}")
    band = confidence_band(confidence)
    if band == "high":
        collected.append("現在の confidence は高めで、現時点の主枝は比較的強く支持されている")
    elif band == "medium":
        collected.append("現在の confidence は中程度で、強い断定には使えない")
    elif band == "low":
        collected.append("現在の confidence は低めで、主枝は暫定仮説として扱うべきである")
    else:
        collected.append("confidence 情報が十分でないため、主枝の強さは限定的に解釈すべきである")

    return dedupe_keep_order(collected)[:6]


def extract_watchpoints(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
) -> list[str]:
    collected: list[str] = []

    collected.extend(to_text_list(pick_first(prediction, "watchpoints", default=[])))
    collected.extend(to_text_list(pick_first(scenario, "watchpoints", default=[])))
    collected.extend(to_text_list(pick_first(signal, "watchpoints", default=[])))

    signal_count = pick_first(prediction, "signal_count", "signalCount", default=None)
    if isinstance(signal_count, (int, float)):
        collected.append(f"signal_count の増加")
    elif isinstance(signal_count, str) and signal_count.strip():
        collected.append("signal_count の増加")

    if not collected:
        collected = [
            "主要 driver の崩れ",
            "悪化側 signal の増加",
            "scenario balance の変化",
        ]

    return dedupe_keep_order(collected)[:6]


def extract_invalidation(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    dominant_scenario: str | None,
) -> list[str]:
    collected: list[str] = []

    collected.extend(
        to_text_list(
            pick_first(
                prediction,
                "invalidation",
                "invalidators",
                "invalidation_conditions",
                default=[],
            )
        )
    )
    collected.extend(
        to_text_list(
            pick_first(
                scenario,
                "invalidation",
                "invalidators",
                "invalidation_conditions",
                default=[],
            )
        )
    )

    if dominant_scenario:
        collected.insert(0, f"dominant_scenario が {dominant_scenario} から変化した場合")

    if not collected:
        collected = [
            "dominant_scenario が変化した場合",
            "confidence が大きく低下した場合",
            "watchpoints の複数が同時に悪化した場合",
        ]

    return dedupe_keep_order(collected)[:6]


def build_headline(
    dominant_scenario: str | None,
    watchpoints: list[str],
    confidence: float | None,
) -> str:
    dominant = dominant_scenario or "主枝不明"
    band = confidence_band(confidence)

    if dominant.lower() == "base_case":
        if watchpoints:
            return "現在は base_case 優勢だが、警戒すべき watchpoints が残る"
        return "現在は base_case 優勢で、主枝は比較的安定している"
    if dominant.lower() == "worst_case":
        return "現在は worst_case 側の圧力が強く、悪化分岐への警戒が必要"
    if dominant.lower() == "best_case":
        return "現在は best_case 側が主枝だが、過度な楽観は避けるべき状態"
    if band == "low":
        return f"現在の主枝は {dominant} だが、confidence が低く再評価余地が大きい"
    return f"現在の主枝は {dominant} で、追加の監視を要する状態"

def build_summary(
    prediction_summary: str | None,
    dominant_scenario: str | None,
    confidence: float | None,
    watchpoints: list[str],
) -> str:
    if prediction_summary:
        base = prediction_summary
    else:
        dominant = dominant_scenario or "現在の主枝"
        base = f"最新の prediction は現時点で {dominant} を主枝としている。"

    band = confidence_band(confidence)
    if band == "high":
        tail = "ただし、主枝が強く見える場合でも watchpoints の監視は継続すべきである。"
    elif band == "medium":
        tail = "ただし、signal と scenario の一部は再評価を必要とする可能性を残している。"
    elif band == "low":
        tail = "ただし、主枝の支持はまだ弱く、状況変化による見直し余地が大きい。"
    else:
        tail = "ただし、判断材料の解釈には慎重さが必要である。"

    if watchpoints:
        return f"{base} {tail}"
    return base


def build_why_it_matters(
    dominant_scenario: str | None,
    confidence: float | None,
) -> str:
    dominant = dominant_scenario or "dominant_scenario"
    band = confidence_band(confidence)

    if band == "high":
        return (
            f"{dominant} を断定未来として誤読せず、"
            "現在の主枝がどの条件で維持または変化するかを人間が理解するため。"
        )
    if band == "medium":
        return (
            f"{dominant} と confidence を断定未来として誤読せず、"
            "次に何を監視すべきかを人間が理解するため。"
        )
    return (
        f"{dominant} が暫定的な主枝にすぎないことを明確にし、"
        "過度な楽観や悲観を避けながら watchpoints を監視するため。"
    )


def build_ui_terms() -> list[dict[str, str]]:
    return [
        {
            "term": "confidence",
            "meaning": "現在の観測とシナリオ整合性の強さであり、的中率ではない",
        },
        {
            "term": "dominant_scenario",
            "meaning": "現時点で最も支持が強い主枝であり、唯一の未来ではない",
        },
        {
            "term": "watchpoints",
            "meaning": "今後シナリオを変えうる監視項目であり、結論そのものではない",
        },
    ]


def build_unavailable_artifact(
    prediction_path: Path,
    scenario_path: Path,
    signal_path: Path,
) -> dict[str, Any]:
    missing_inputs: list[str] = []
    if not prediction_path.exists():
        missing_inputs.append(str(prediction_path))
    if not scenario_path.exists():
        missing_inputs.append(str(scenario_path))
    if not signal_path.exists():
        missing_inputs.append(str(signal_path))

    artifact: dict[str, Any] = {
        "as_of": None,
        "subject": "prediction",
        "status": "unavailable",
        "headline": "prediction explanation unavailable",
        "summary": "必要な prediction-layer artifact が不足しているため、構造化 explanation を生成できなかった。",
        "why_it_matters": "UI が explanation を捏造せず、欠損を正直に表示するため。",
        "based_on": [
            str(prediction_path),
            str(scenario_path),
            str(signal_path),
        ],
        "drivers": [],
        "watchpoints": [],
        "invalidation": [],
        "must_not_mean": [
            "unavailable は安全を意味しない",
            "unavailable は prediction が存在しないことと同義ではない",
            "UI は unavailable 時に explanation を作文してはならない",
        ],
        "ui_terms": build_ui_terms(),
        "generated_at": utc_now_iso(),
    }
    if missing_inputs:
        artifact["missing_inputs"] = missing_inputs
    return artifact


def build_prediction_explanation(
    prediction: dict[str, Any],
    scenario: dict[str, Any],
    signal: dict[str, Any],
    prediction_path: Path,
    scenario_path: Path,
    signal_path: Path,
) -> dict[str, Any]:
    as_of = extract_as_of(prediction, scenario, signal)
    dominant_scenario = extract_dominant_scenario(prediction)
    confidence = extract_confidence(prediction)
    prediction_summary = extract_summary(prediction)

    drivers = extract_drivers(prediction, scenario, signal, dominant_scenario, confidence)
    watchpoints = extract_watchpoints(prediction, scenario, signal)
    invalidation = extract_invalidation(prediction, scenario, dominant_scenario)

    artifact: dict[str, Any] = {
        "as_of": as_of,
        "subject": "prediction",
        "status": "ok",
        "headline": build_headline(dominant_scenario, watchpoints, confidence),
        "summary": build_summary(prediction_summary, dominant_scenario, confidence, watchpoints),
        "why_it_matters": build_why_it_matters(dominant_scenario, confidence),
        "based_on": [
            str(prediction_path),
            str(scenario_path),
            str(signal_path),
        ],
        "drivers": drivers,
        "watchpoints": watchpoints,
        "invalidation": invalidation,
        "must_not_mean": [
            "prediction は確定未来ではない",
            "confidence は的中率ではない",
            "watchpoints は発生確定イベントではない",
        ],
        "ui_terms": build_ui_terms(),
        "generated_at": utc_now_iso(),
    }

    return artifact


def write_json(path: Path, data: dict[str, Any], pretty: bool) -> None:
    ensure_parent_dir(path)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2 if pretty else None,
            sort_keys=False,
        )
        f.write("\n")


def main() -> int:
    args = parse_args()

    prediction = read_json(args.prediction)
    scenario = read_json(args.scenario)
    signal = read_json(args.signal)

    if prediction is None or scenario is None or signal is None:
        artifact = build_unavailable_artifact(
            prediction_path=args.prediction,
            scenario_path=args.scenario,
            signal_path=args.signal,
        )
        write_json(args.output, artifact, pretty=args.pretty or True)
        print(f"[prediction_explanation] wrote {args.output}")
        print("[prediction_explanation] status=unavailable")
        return 0

    artifact = build_prediction_explanation(
        prediction=prediction,
        scenario=scenario,
        signal=signal,
        prediction_path=args.prediction,
        scenario_path=args.scenario,
        signal_path=args.signal,
    )
    write_json(args.output, artifact, pretty=args.pretty or True)

    print(f"[prediction_explanation] wrote {args.output}")
    print(
        "[prediction_explanation] "
        f"subject={artifact.get('subject')} "
        f"status={artifact.get('status')} "
        f"as_of={artifact.get('as_of')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
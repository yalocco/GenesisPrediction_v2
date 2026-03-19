#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_scenario_explanation.py

Purpose:
    Generate analysis/explanation/scenario_explanation_latest.json
    from prediction-layer artifacts.

Inputs:
    - analysis/prediction/scenario_latest.json
    - analysis/prediction/signal_latest.json
    - analysis/prediction/prediction_latest.json

Output:
    - analysis/explanation/scenario_explanation_latest.json

Design principles:
    - Explanation does not create new truth.
    - Scenario explanation describes branching structure, not final prediction.
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

SCENARIO_PATH = REPO_ROOT / "analysis" / "prediction" / "scenario_latest.json"
SIGNAL_PATH = REPO_ROOT / "analysis" / "prediction" / "signal_latest.json"
PREDICTION_PATH = REPO_ROOT / "analysis" / "prediction" / "prediction_latest.json"

EXPLANATION_DIR = REPO_ROOT / "analysis" / "explanation"
OUTPUT_PATH = EXPLANATION_DIR / "scenario_explanation_latest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build scenario explanation artifact from prediction-layer outputs."
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
        "--prediction",
        type=Path,
        default=PREDICTION_PATH,
        help="Path to prediction_latest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Path to write scenario_explanation_latest.json",
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
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


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
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
    prediction: dict[str, Any] | None,
) -> str | None:
    return (
        normalize_str(pick_first(scenario, "as_of", "date"))
        or normalize_str(pick_first(signal, "as_of", "date"))
        or normalize_str(pick_first(prediction, "as_of", "date"))
    )


def extract_dominant_scenario(
    scenario: dict[str, Any] | None,
    prediction: dict[str, Any] | None,
) -> str | None:
    return (
        normalize_str(pick_first(scenario, "dominant_scenario", "dominantScenario"))
        or normalize_str(pick_first(prediction, "dominant_scenario", "dominantScenario"))
    )


def get_probability_like(item: Any) -> float | None:
    if isinstance(item, (int, float)):
        return float(item)
    if isinstance(item, str):
        try:
            return float(item.strip())
        except Exception:
            return None
    if isinstance(item, dict):
        for key in ("probability", "weight", "score", "value"):
            value = item.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value.strip())
                except Exception:
                    pass
    return None


def extract_named_scenario_value(data: dict[str, Any] | None, name: str) -> float | str | None:
    if not isinstance(data, dict):
        return None

    direct = pick_first(data, name, default=None)
    if direct is not None:
        prob = get_probability_like(direct)
        return prob if prob is not None else normalize_str(direct)

    scenarios_obj = pick_first(data, "scenarios", default=None)
    if isinstance(scenarios_obj, dict):
        candidate = scenarios_obj.get(name)
        if candidate is not None:
            prob = get_probability_like(candidate)
            return prob if prob is not None else normalize_str(candidate)

    if isinstance(scenarios_obj, list):
        for item in scenarios_obj:
            if not isinstance(item, dict):
                continue
            item_name = normalize_str(item.get("name") or item.get("scenario"))
            if item_name == name:
                prob = get_probability_like(item)
                return prob if prob is not None else item_name

    return None


def format_branch_value(value: float | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        pct = float(value)
        if 0.0 <= pct <= 1.0:
            pct *= 100.0
        return f"{pct:.0f}%"
    return normalize_str(value)


def extract_branch_values(scenario: dict[str, Any] | None) -> dict[str, str | None]:
    return {
        "best_case": format_branch_value(extract_named_scenario_value(scenario, "best_case")),
        "base_case": format_branch_value(extract_named_scenario_value(scenario, "base_case")),
        "worst_case": format_branch_value(extract_named_scenario_value(scenario, "worst_case")),
    }


def build_balance_text(
    dominant: str | None,
    branches: dict[str, str | None],
    signal: dict[str, Any] | None,
) -> str:
    if dominant == "base_case":
        worst_exists = branches.get("worst_case") is not None
        best_exists = branches.get("best_case") is not None
        if worst_exists and best_exists:
            return "base優勢だが上下分岐の余地が残る状態"
        if worst_exists:
            return "base優勢だがworstが無視できない状態"
        if best_exists:
            return "base優勢で改善余地も残る状態"
        return "base優勢で分岐は比較的安定している状態"

    if dominant == "worst_case":
        return "worst優勢で悪化側への片寄りが強い状態"

    if dominant == "best_case":
        return "best優勢だが条件依存性が高い状態"

    signal_count = pick_first(signal, "signal_count", "count", default=None)
    if signal_count is not None:
        return "分岐の均衡が定まらず、signal 変化で主枝が動きうる状態"
    return "分岐構造は存在するが、均衡の読み取りには慎重さが必要な状態"


def extract_drivers(
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
    prediction: dict[str, Any] | None,
    dominant: str | None,
) -> list[str]:
    collected: list[str] = []

    scen_drivers = to_text_list(pick_first(scenario, "drivers", default=[]))
    signal_drivers = to_text_list(pick_first(signal, "drivers", "signals", default=[]))
    pred_drivers = to_text_list(pick_first(prediction, "drivers", default=[]))

    if dominant == "base_case":
        collected.append("base_case を支える主要 driver が現在も有効")
        collected.append("worst_case 側の trigger が完全には解消されていない")
        collected.append("best_case に移行するための強い signal は不足している")
    elif dominant == "worst_case":
        collected.append("悪化側の driver が現在の分岐を強く支えている")
        collected.append("改善側へ戻すための signal が不足している")
    elif dominant == "best_case":
        collected.append("改善側の driver が現時点では有効")
        collected.append("ただし下振れ側の再浮上条件は完全に消えていない")

    collected.extend(scen_drivers[:3])
    collected.extend(signal_drivers[:2])
    collected.extend(pred_drivers[:2])

    return dedupe_keep_order(collected)[:7]


def extract_watchpoints(
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
) -> list[str]:
    collected: list[str] = []

    collected.extend(to_text_list(pick_first(scenario, "watchpoints", default=[])))
    collected.extend(to_text_list(pick_first(signal, "watchpoints", default=[])))

    if not collected:
        collected = [
            "worst_case に接続する signal の増加",
            "driver の一部崩壊",
            "外部ショックの発生",
        ]

    return dedupe_keep_order(collected)[:6]


def extract_invalidation(
    scenario: dict[str, Any] | None,
    prediction: dict[str, Any] | None,
    dominant: str | None,
) -> list[str]:
    collected: list[str] = []

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

    if dominant:
        collected.insert(0, f"dominant scenario が {dominant} から変化した場合")

    if not collected:
        collected = [
            "dominant scenario が base_case から変化した場合",
            "worst_case 側の条件が明確に強化された場合",
            "best_case を支える新規 signal が成立した場合",
        ]

    return dedupe_keep_order(collected)[:6]


def build_headline(dominant: str | None, balance: str) -> str:
    if dominant == "base_case":
        return "複数シナリオが併存し、base_case を軸に上下分岐の余地が残る状態"
    if dominant == "worst_case":
        return "悪化側シナリオが主枝となり、worst_case 寄りの分岐構造が強まる状態"
    if dominant == "best_case":
        return "改善側シナリオが主枝だが、条件依存性が高く再悪化余地も残る状態"
    return f"複数シナリオが併存し、{balance}"


def build_summary(
    dominant: str | None,
    balance: str,
    branches: dict[str, str | None],
) -> str:
    dominant_text = dominant or "中心シナリオ不明"

    parts: list[str] = [
        f"現在の scenario 構造は {dominant_text} を中心に展開している。"
    ]

    branch_bits: list[str] = []
    if branches.get("best_case"):
        branch_bits.append(f"best_case={branches['best_case']}")
    if branches.get("base_case"):
        branch_bits.append(f"base_case={branches['base_case']}")
    if branches.get("worst_case"):
        branch_bits.append(f"worst_case={branches['worst_case']}")

    if branch_bits:
        parts.append("分岐バランスは " + " / ".join(branch_bits) + " である。")

    parts.append(f"全体としては {balance}。")
    return " ".join(parts)


def build_why_it_matters(dominant: str | None) -> str:
    if dominant == "worst_case":
        return (
            "悪化側を単なる恐怖ではなく分岐構造として理解することで、"
            "過剰反応ではなく監視と判断の優先順位を明確にできるため。"
        )
    if dominant == "best_case":
        return (
            "改善側の主枝を過度な楽観と混同せず、"
            "どの条件で維持・崩壊するかを理解するため。"
        )
    return (
        "単一の未来ではなく分岐構造として理解することで、"
        "過剰な楽観や悲観を避け、現実的な監視と判断が可能になるため。"
    )


def build_ui_terms() -> list[dict[str, str]]:
    return [
        {
            "term": "scenario",
            "meaning": "複数の未来分岐を構造として表現したものであり、単一の予測ではない",
        },
        {
            "term": "base_case",
            "meaning": "現時点で最も現実的と評価される主枝であり、固定された未来ではない",
        },
        {
            "term": "worst_case",
            "meaning": "回避すべきリスクシナリオであり、発生確定ではない",
        },
        {
            "term": "best_case",
            "meaning": "条件が整った場合に成立する改善シナリオであり、保証された結果ではない",
        },
    ]


def build_unavailable_artifact(
    scenario_path: Path,
    signal_path: Path,
    prediction_path: Path,
) -> dict[str, Any]:
    missing_inputs: list[str] = []
    if not scenario_path.exists():
        missing_inputs.append(str(scenario_path))
    if not signal_path.exists():
        missing_inputs.append(str(signal_path))
    if not prediction_path.exists():
        missing_inputs.append(str(prediction_path))

    artifact: dict[str, Any] = {
        "as_of": None,
        "subject": "scenario",
        "status": "unavailable",
        "headline": "scenario explanation unavailable",
        "summary": "必要な prediction-layer artifact が不足しているため、scenario explanation を生成できなかった。",
        "why_it_matters": "UI が scenario explanation を捏造せず、欠損を正直に表示するため。",
        "based_on": [
            str(scenario_path),
            str(signal_path),
            str(prediction_path),
        ],
        "scenario_structure": {
            "dominant": None,
            "alternatives": [],
            "balance": "unavailable",
        },
        "drivers": [],
        "watchpoints": [],
        "invalidation": [],
        "must_not_mean": [
            "unavailable は安全を意味しない",
            "base_case は安全を意味しない",
            "worst_case は確定未来ではない",
        ],
        "ui_terms": build_ui_terms(),
        "generated_at": utc_now_iso(),
    }
    if missing_inputs:
        artifact["missing_inputs"] = missing_inputs
    return artifact


def build_scenario_explanation(
    scenario: dict[str, Any],
    signal: dict[str, Any],
    prediction: dict[str, Any],
    scenario_path: Path,
    signal_path: Path,
    prediction_path: Path,
) -> dict[str, Any]:
    as_of = extract_as_of(scenario, signal, prediction)
    dominant = extract_dominant_scenario(scenario, prediction)
    branches = extract_branch_values(scenario)
    balance = build_balance_text(dominant, branches, signal)

    alternatives = [name for name in ("best_case", "base_case", "worst_case") if name != dominant]

    artifact: dict[str, Any] = {
        "as_of": as_of,
        "subject": "scenario",
        "status": "ok",
        "headline": build_headline(dominant, balance),
        "summary": build_summary(dominant, balance, branches),
        "why_it_matters": build_why_it_matters(dominant),
        "based_on": [
            str(scenario_path),
            str(signal_path),
            str(prediction_path),
        ],
        "scenario_structure": {
            "dominant": dominant,
            "alternatives": alternatives,
            "balance": balance,
        },
        "drivers": extract_drivers(scenario, signal, prediction, dominant),
        "watchpoints": extract_watchpoints(scenario, signal),
        "invalidation": extract_invalidation(scenario, prediction, dominant),
        "must_not_mean": [
            "base_case は安全を意味しない",
            "worst_case は確定未来ではない",
            "best_case は期待ではなく条件付き分岐である",
        ],
        "ui_terms": build_ui_terms(),
        "generated_at": utc_now_iso(),
    }

    return artifact


def main() -> int:
    args = parse_args()

    scenario = read_json(args.scenario)
    signal = read_json(args.signal)
    prediction = read_json(args.prediction)

    if scenario is None or signal is None or prediction is None:
        artifact = build_unavailable_artifact(
            scenario_path=args.scenario,
            signal_path=args.signal,
            prediction_path=args.prediction,
        )
        write_json(args.output, artifact, pretty=args.pretty or True)
        print(f"[scenario_explanation] wrote {args.output}")
        print("[scenario_explanation] status=unavailable")
        return 0

    artifact = build_scenario_explanation(
        scenario=scenario,
        signal=signal,
        prediction=prediction,
        scenario_path=args.scenario,
        signal_path=args.signal,
        prediction_path=args.prediction,
    )
    write_json(args.output, artifact, pretty=args.pretty or True)

    print(f"[scenario_explanation] wrote {args.output}")
    print(
        "[scenario_explanation] "
        f"subject={artifact.get('subject')} "
        f"status={artifact.get('status')} "
        f"as_of={artifact.get('as_of')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
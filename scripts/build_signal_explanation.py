#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_signal_explanation.py

Purpose:
    Generate analysis/explanation/signal_explanation_latest.json
    from prediction-layer artifacts.

Inputs:
    - analysis/prediction/signal_latest.json
    - analysis/prediction/scenario_latest.json
    - analysis/prediction/prediction_latest.json

Output:
    - analysis/explanation/signal_explanation_latest.json

Design principles:
    - Explanation does not create new truth.
    - Signal explanation describes what is currently active in the signal layer.
    - Missing inputs should produce an honest unavailable artifact.
    - UI reads this artifact only; UI must not synthesize explanations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent

SIGNAL_PATH = REPO_ROOT / "analysis" / "prediction" / "signal_latest.json"
SCENARIO_PATH = REPO_ROOT / "analysis" / "prediction" / "scenario_latest.json"
PREDICTION_PATH = REPO_ROOT / "analysis" / "prediction" / "prediction_latest.json"

EXPLANATION_DIR = REPO_ROOT / "analysis" / "explanation"
OUTPUT_PATH = EXPLANATION_DIR / "signal_explanation_latest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build signal explanation artifact from prediction-layer outputs."
    )
    parser.add_argument(
        "--signal",
        type=Path,
        default=SIGNAL_PATH,
        help="Path to signal_latest.json",
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        default=SCENARIO_PATH,
        help="Path to scenario_latest.json",
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
        help="Path to write signal_explanation_latest.json",
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


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sentence(text: str) -> str:
    s = compact_spaces(text)
    if not s:
        return ""
    if s.endswith(("。", "．", ".", "!", "！", "?", "？")):
        return s
    return s + "。"


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
        cleaned = compact_spaces(item)
        if not cleaned:
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def dedupe_dict_list(items: list[dict[str, Any]], key_fields: list[str]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []

    for item in items:
        parts = [str(item.get(field, "")).strip() for field in key_fields]
        key = " | ".join(parts).strip()
        if not key:
            key = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)

    return result


def to_text_list(value: Any) -> list[str]:
    raw_items = normalize_list(value)
    result: list[str] = []

    for item in raw_items:
        if item is None:
            continue
        if isinstance(item, str):
            text = compact_spaces(item)
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
                or normalize_str(item.get("meaning"))
            )
            if text:
                result.append(compact_spaces(text))
            continue
        result.append(compact_spaces(str(item)))

    return dedupe_keep_order([x for x in result if x])


def clamp_confidence(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        num = float(value)
    elif isinstance(value, str):
        try:
            num = float(value.strip())
        except Exception:
            return None
    else:
        return None

    if num < 0.0:
        return 0.0
    if num > 1.0:
        return 1.0
    return num


def extract_as_of(
    signal: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    prediction: dict[str, Any] | None,
) -> str | None:
    return (
        normalize_str(pick_first(signal, "as_of", "date"))
        or normalize_str(pick_first(scenario, "as_of", "date"))
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


def extract_confidence(
    signal: dict[str, Any] | None,
    prediction: dict[str, Any] | None,
) -> float | None:
    direct = clamp_confidence(pick_first(signal, "confidence", default=None))
    if direct is not None:
        return direct
    return clamp_confidence(pick_first(prediction, "confidence", default=None))


def confidence_band(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.45:
        return "medium"
    return "low"


def extract_signal_count(signal: dict[str, Any] | None) -> int | None:
    for value in (
        pick_first(signal, "signal_count", default=None),
        pick_first(signal, "count", default=None),
    ):
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value.strip()))
            except Exception:
                pass

    signals = pick_first(signal, "signals", default=None)
    if isinstance(signals, list):
        return len(signals)

    drivers = pick_first(signal, "drivers", default=None)
    if isinstance(drivers, list):
        return len(drivers)

    return None


def normalize_signal_item(item: Any) -> dict[str, str] | None:
    if item is None:
        return None

    if isinstance(item, str):
        text = compact_spaces(item)
        if not text:
            return None
        return {
            "signal": text,
            "meaning": sentence(f"{text} が現在の signal layer で有効とみなされている"),
        }

    if isinstance(item, dict):
        signal_name = (
            normalize_str(item.get("signal"))
            or normalize_str(item.get("name"))
            or normalize_str(item.get("title"))
            or normalize_str(item.get("label"))
            or normalize_str(item.get("type"))
            or normalize_str(item.get("category"))
        )
        meaning = (
            normalize_str(item.get("meaning"))
            or normalize_str(item.get("summary"))
            or normalize_str(item.get("description"))
            or normalize_str(item.get("reason"))
            or normalize_str(item.get("detail"))
        )

        if not signal_name:
            return None
        if not meaning:
            meaning = f"{signal_name} が現在の変化方向を示す signal として扱われている。"

        return {
            "signal": compact_spaces(signal_name),
            "meaning": sentence(meaning),
        }

    text = compact_spaces(str(item))
    if not text:
        return None

    return {
        "signal": text,
        "meaning": sentence(f"{text} が現在の signal として記録されている"),
    }


def extract_signal_items(signal: dict[str, Any] | None) -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []

    for raw in normalize_list(pick_first(signal, "signals", default=[])):
        item = normalize_signal_item(raw)
        if item:
            collected.append(item)

    for raw in normalize_list(pick_first(signal, "drivers", default=[])):
        item = normalize_signal_item(raw)
        if item:
            collected.append(item)

    return dedupe_dict_list(collected, ["signal", "meaning"])[:6]


def classify_signal_mix(items: list[dict[str, str]]) -> str:
    if not items:
        return "quiet"

    texts = " ".join(
        f"{item.get('signal', '')} {item.get('meaning', '')}".lower()
        for item in items
    )

    down_hits = sum(token in texts for token in [
        "risk", "stress", "tight", "contraction", "down", "weak",
        "warn", "fragile", "volatility", "crisis", "deterior"
    ])
    up_hits = sum(token in texts for token in [
        "improv", "recover", "best", "up", "support",
        "stabil", "positive", "relief"
    ])

    if down_hits > 0 and up_hits > 0:
        return "mixed"
    if down_hits > 0:
        return "risk-biased"
    if up_hits > 0:
        return "supportive"
    return "mixed"


def extract_watchpoints(
    signal: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
) -> list[str]:
    collected: list[str] = []
    collected.extend(to_text_list(pick_first(signal, "watchpoints", default=[])))
    collected.extend(to_text_list(pick_first(scenario, "watchpoints", default=[])))

    if not collected:
        collected = [
            "signal count の増減",
            "新規 regime shift signal の出現",
            "既存 signal の急速な消失または悪化",
        ]

    return dedupe_keep_order(collected)[:6]


def extract_invalidation(
    signal: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
) -> list[str]:
    collected: list[str] = []

    collected.extend(
        to_text_list(
            pick_first(
                signal,
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

    if not collected:
        collected = [
            "主要 signal が複数同時に消失した場合",
            "逆方向の signal が明確に優勢化した場合",
            "scenario balance が signal 解釈と矛盾し始めた場合",
        ]

    return dedupe_keep_order(collected)[:6]


def build_headline(
    signal_count: int | None,
    mix: str,
    dominant_scenario: str | None,
) -> str:
    dominant = dominant_scenario or "current branch"

    if signal_count is None or signal_count == 0:
        return "signal layer は静かで、強い方向確定を示す材料はまだ少ない"

    if mix == "risk-biased":
        return f"複数 signal が悪化側に偏り、{dominant} を不安定化させる圧力が見える"
    if mix == "supportive":
        return f"改善・支持系 signal が優勢だが、{dominant} を固定視するにはまだ早い"
    return f"複数 signal が同時に点灯し、{dominant} を支えつつも方向感はまだ限定的"


def build_summary(
    signal_count: int | None,
    mix: str,
    dominant_scenario: str | None,
    confidence: float | None,
) -> str:
    dominant = dominant_scenario or "current scenario"
    conf_text = "unknown" if confidence is None else f"{confidence:.2f}"

    if signal_count is None:
        return sentence(
            f"signal layer は有効な兆候を持っているが、件数は明確でない。"
            f" 現時点では {dominant} を支える signal 群が存在する一方で、confidence は {conf_text} に留まり、"
            "一方向への収束を断定できる段階ではない"
        )

    return sentence(
        f"現在の signal layer では {signal_count} 件前後の有効 signal が観測されている。"
        f" 構成は {mix} 寄りで、現時点では {dominant} を支える材料があるものの、confidence は {conf_text} であり、"
        "まだ単線的な方向確定とは読まない方が安全である"
    )


def build_why_it_matters(mix: str) -> str:
    if mix == "risk-biased":
        return sentence(
            "signal は最初に変化を知らせる層なので、ここで悪化バイアスが強いことは scenario や prediction が後追いで重くなる前兆になりうる"
        )
    if mix == "supportive":
        return sentence(
            "改善側 signal が立っていても、それをそのまま安心材料と誤読しないために signal layer を構造として読む必要がある"
        )
    return sentence(
        "signal layer を見ることで、scenario や prediction に先行して何が動き始めているかを把握できるため"
    )


def build_interpretation(
    mix: str,
    dominant_scenario: str | None,
    items: list[dict[str, str]],
) -> str:
    dominant = dominant_scenario or "current scenario"
    first_signal = items[0]["signal"] if items else "主要 signal"

    if mix == "risk-biased":
        return sentence(
            f"これは悪化圧力の初期段階を示す可能性がある。"
            f" ただし signal はまだ予測そのものではなく、{first_signal} のような兆候が {dominant} をどちらへ押すかを読む段階である"
        )
    if mix == "supportive":
        return sentence(
            f"これは改善・支持の兆候が見えている局面だが、まだ土台固めの途中と読むべきである。"
            f" {first_signal} のような signal が続くかどうかが、楽観へ進めるかの分かれ目になる"
        )
    return sentence(
        f"これは signal が一方向に収束したというより、複数の兆候が同時に動いている局面を意味する。"
        f" したがって {dominant} を前提にしつつも、{first_signal} のような先行兆候を優先監視するのが自然である"
    )


def build_signal_state(
    signal_count: int | None,
    mix: str,
    confidence: float | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "count": signal_count,
        "dominant_type": mix,
        "strength": confidence_band(confidence),
    }
    if confidence is not None:
        state["confidence"] = confidence
    return state


def build_implications(
    mix: str,
    dominant_scenario: str | None,
    watchpoints: list[str],
) -> list[str]:
    dominant = dominant_scenario or "current scenario"
    first_watch = watchpoints[0] if watchpoints else "主要 watchpoint"

    if mix == "risk-biased":
        items = [
            f"現在の signal 構成は {dominant} を悪化側へ寄せる圧力として働きうる",
            f"{first_watch} の悪化は scenario balance を一段下へ動かす可能性がある",
            "prediction 側の guarded read が重くなる前段階として読むべきである",
        ]
    elif mix == "supportive":
        items = [
            f"現在の signal 構成は {dominant} を支える補助材料になりうる",
            f"{first_watch} が維持されれば best/base 側の整合が強まりうる",
            "ただし支持系 signal だけで安全宣言してはならない",
        ]
    else:
        items = [
            f"現在の signal 構成は {dominant} を支えつつも、方向感そのものはまだ流動的である",
            f"{first_watch} の変化が次の scenario shift を早める可能性がある",
            "signal layer は判断確定ではなく、先行兆候の監視レイヤとして読むべきである",
        ]

    return dedupe_keep_order(items)[:5]


def build_ui_terms() -> list[dict[str, str]]:
    return [
        {
            "term": "signal",
            "meaning": "変化の兆候であり、まだ最終判断そのものではない",
        },
        {
            "term": "signal_count",
            "meaning": "現在有効とみなされる signal の件数であり、重要度の総和ではない",
        },
        {
            "term": "dominant_type",
            "meaning": "signal 構成が全体としてどちら寄りかを示す読みであり、確定方向ではない",
        },
        {
            "term": "strength",
            "meaning": "signal 層の整合度の読みであり、的中率や成功保証ではない",
        },
    ]


def build_unavailable_artifact(
    signal_path: Path,
    scenario_path: Path,
    prediction_path: Path,
) -> dict[str, Any]:
    missing_inputs: list[str] = []
    if not signal_path.exists():
        missing_inputs.append(str(signal_path))
    if not scenario_path.exists():
        missing_inputs.append(str(scenario_path))
    if not prediction_path.exists():
        missing_inputs.append(str(prediction_path))

    artifact: dict[str, Any] = {
        "as_of": None,
        "subject": "signal",
        "status": "unavailable",
        "headline": "signal explanation unavailable",
        "summary": "必要な prediction-layer artifact が不足しているため、signal explanation を生成できなかった。",
        "interpretation": "UI が signal explanation を捏造せず、欠損を正直に表示するため unavailable を返す。",
        "why_it_matters": "UI が signal explanation を捏造せず、欠損を正直に表示するため。",
        "based_on": [
            str(signal_path),
            str(scenario_path),
            str(prediction_path),
        ],
        "signal_state": {
            "count": None,
            "dominant_type": "unavailable",
            "strength": "unknown",
        },
        "signals": [],
        "watchpoints": [],
        "implications": [],
        "invalidation": [],
        "must_not_mean": [
            "unavailable は安全を意味しない",
            "signal は最終判断ではない",
            "UI は signal explanation を作文してはならない",
        ],
        "ui_terms": build_ui_terms(),
        "generated_at": utc_now_iso(),
    }
    if missing_inputs:
        artifact["missing_inputs"] = missing_inputs
    return artifact


def build_signal_explanation(
    signal: dict[str, Any],
    scenario: dict[str, Any],
    prediction: dict[str, Any],
    signal_path: Path,
    scenario_path: Path,
    prediction_path: Path,
) -> dict[str, Any]:
    as_of = extract_as_of(signal, scenario, prediction)
    dominant_scenario = extract_dominant_scenario(scenario, prediction)
    confidence = extract_confidence(signal, prediction)
    signal_count = extract_signal_count(signal)
    signal_items = extract_signal_items(signal)
    mix = classify_signal_mix(signal_items)
    watchpoints = extract_watchpoints(signal, scenario)

    artifact: dict[str, Any] = {
        "as_of": as_of,
        "subject": "signal",
        "status": "ok",
        "headline": build_headline(signal_count, mix, dominant_scenario),
        "summary": build_summary(signal_count, mix, dominant_scenario, confidence),
        "interpretation": build_interpretation(mix, dominant_scenario, signal_items),
        "why_it_matters": build_why_it_matters(mix),
        "based_on": [
            str(signal_path),
            str(scenario_path),
            str(prediction_path),
        ],
        "signal_state": build_signal_state(signal_count, mix, confidence),
        "signals": signal_items,
        "watchpoints": watchpoints,
        "implications": build_implications(mix, dominant_scenario, watchpoints),
        "invalidation": extract_invalidation(signal, scenario),
        "must_not_mean": [
            "signal は prediction そのものではない",
            "signal_count は危険度の合計ではない",
            "dominant_type は単線的な未来確定を意味しない",
        ],
        "ui_terms": build_ui_terms(),
        "generated_at": utc_now_iso(),
    }

    return artifact


def main() -> int:
    args = parse_args()

    signal = read_json(args.signal)
    scenario = read_json(args.scenario)
    prediction = read_json(args.prediction)

    if signal is None or scenario is None or prediction is None:
        artifact = build_unavailable_artifact(
            signal_path=args.signal,
            scenario_path=args.scenario,
            prediction_path=args.prediction,
        )
        write_json(args.output, artifact, pretty=args.pretty or True)
        print(f"[signal_explanation] wrote {args.output}")
        print("[signal_explanation] status=unavailable")
        return 0

    artifact = build_signal_explanation(
        signal=signal,
        scenario=scenario,
        prediction=prediction,
        signal_path=args.signal,
        scenario_path=args.scenario,
        prediction_path=args.prediction,
    )
    write_json(args.output, artifact, pretty=args.pretty or True)

    print(f"[signal_explanation] wrote {args.output}")
    print(
        "[signal_explanation] "
        f"subject={artifact.get('subject')} "
        f"status={artifact.get('status')} "
        f"as_of={artifact.get('as_of')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
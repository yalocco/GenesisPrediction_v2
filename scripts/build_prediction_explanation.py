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
    - analysis/prediction/historical_pattern_latest.json   (optional)
    - analysis/prediction/historical_analog_latest.json    (optional)
    - analysis/prediction/reference_memory_latest.json     (optional)

Output:
    - analysis/explanation/prediction_explanation_latest.json

Design principles:
    - Explanation does not create new truth.
    - Explanation is structured and analysis-side, not UI-side generation.
    - Missing inputs should produce an honest unavailable artifact.
    - UI reads this artifact only; UI must not synthesize explanations.
    - SSOT = analysis
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

PREDICTION_PATH = REPO_ROOT / "analysis" / "prediction" / "prediction_latest.json"
SCENARIO_PATH = REPO_ROOT / "analysis" / "prediction" / "scenario_latest.json"
SIGNAL_PATH = REPO_ROOT / "analysis" / "prediction" / "signal_latest.json"
HISTORICAL_PATTERN_PATH = REPO_ROOT / "analysis" / "prediction" / "historical_pattern_latest.json"
HISTORICAL_ANALOG_PATH = REPO_ROOT / "analysis" / "prediction" / "historical_analog_latest.json"
REFERENCE_MEMORY_PATH = REPO_ROOT / "analysis" / "prediction" / "reference_memory_latest.json"

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
        "--historical-pattern",
        type=Path,
        default=HISTORICAL_PATTERN_PATH,
        help="Path to historical_pattern_latest.json",
    )
    parser.add_argument(
        "--historical-analog",
        type=Path,
        default=HISTORICAL_ANALOG_PATH,
        help="Path to historical_analog_latest.json",
    )
    parser.add_argument(
        "--reference-memory",
        type=Path,
        default=REFERENCE_MEMORY_PATH,
        help="Path to reference_memory_latest.json",
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


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sentence(text: str) -> str:
    s = compact_spaces(text)
    if not s:
        return ""
    if s.endswith(("。", "．", ".", "!", "！", "?", "？")):
        return s
    return s + "。"


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
        parts: list[str] = []
        for field in key_fields:
            parts.append(str(item.get(field, "")).strip())
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


def safe_title(text: Any) -> str | None:
    s = normalize_str(text)
    if not s:
        return None
    return compact_spaces(s.replace("_", " ").replace("-", " "))


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


def extract_dominant_scenario(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
) -> str | None:
    value = normalize_str(
        pick_first(
            prediction,
            "dominant_scenario",
            "dominantScenario",
            "scenario",
            "regime",
        )
    )
    if value:
        return value

    scenario_direct = normalize_str(
        pick_first(
            scenario,
            "dominant_scenario",
            "dominantScenario",
            "scenario",
        )
    )
    if scenario_direct:
        return scenario_direct

    scenarios = pick_first(scenario, "scenarios", default=[])
    if isinstance(scenarios, list):
        best_name: str | None = None
        best_score = -1.0
        for item in scenarios:
            if not isinstance(item, dict):
                continue
            name = (
                normalize_str(item.get("name"))
                or normalize_str(item.get("scenario"))
                or normalize_str(item.get("label"))
            )
            score = clamp_confidence(item.get("probability", item.get("confidence")))
            if name and score is not None and score > best_score:
                best_name = name
                best_score = score
        if best_name:
            return best_name

    return None


def extract_confidence(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
) -> float | None:
    direct = clamp_confidence(pick_first(prediction, "confidence", default=None))
    if direct is not None:
        return direct

    scenario_conf = clamp_confidence(pick_first(scenario, "confidence", default=None))
    if scenario_conf is not None:
        return scenario_conf

    scenarios = pick_first(scenario, "scenarios", default=[])
    if isinstance(scenarios, list):
        best_score = -1.0
        for item in scenarios:
            if not isinstance(item, dict):
                continue
            score = clamp_confidence(item.get("probability", item.get("confidence")))
            if score is not None and score > best_score:
                best_score = score
        if best_score >= 0.0:
            return best_score

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
            "prediction_statement",
            "primary_narrative",
        )
    )


def extract_risk(prediction: dict[str, Any] | None) -> str | None:
    return normalize_str(
        pick_first(
            prediction,
            "overall_risk",
            "risk_level",
            "overall_risk_level",
            "global_risk",
            "risk",
            "warning_level",
        )
    )


def format_confidence_text(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    return f"{confidence:.2f}"


def normalize_driver_struct(item: Any) -> dict[str, str] | None:
    if item is None:
        return None

    if isinstance(item, str):
        text = safe_title(item)
        if not text:
            return None
        return {
            "driver": text,
            "why": sentence(f"{text} が現在の予測判断に影響している"),
            "impact": sentence(f"{text} が継続すると現在の見立てが維持されやすい"),
        }

    if isinstance(item, dict):
        driver = (
            normalize_str(item.get("driver"))
            or normalize_str(item.get("name"))
            or normalize_str(item.get("title"))
            or normalize_str(item.get("label"))
            or normalize_str(item.get("signal"))
            or normalize_str(item.get("pattern"))
        )
        why = (
            normalize_str(item.get("why"))
            or normalize_str(item.get("reason"))
            or normalize_str(item.get("summary"))
            or normalize_str(item.get("description"))
        )
        impact = (
            normalize_str(item.get("impact"))
            or normalize_str(item.get("meaning"))
            or normalize_str(item.get("path"))
            or normalize_str(item.get("effect"))
        )

        if not driver:
            return None
        if not why:
            why = f"{driver} が現在のシナリオ整合に寄与している。"
        if not impact:
            impact = f"{driver} が続くと現行の予測方向が維持されやすい。"

        return {
            "driver": compact_spaces(driver),
            "why": sentence(why),
            "impact": sentence(impact),
        }

    text = safe_title(str(item))
    if not text:
        return None

    return {
        "driver": text,
        "why": sentence(f"{text} が判断材料として扱われている"),
        "impact": sentence(f"{text} の変化は予測更新要因になりうる"),
    }


def enrich_driver_structs(
    drivers: list[dict[str, str]],
    dominant_scenario: str | None,
    confidence: float | None,
    risk_value: str | None,
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    dominant = dominant_scenario or "current scenario"
    band = confidence_band(confidence)
    risk_text = risk_value or "unknown risk"

    for item in drivers:
        driver = item.get("driver", "")
        why = item.get("why", "")
        impact = item.get("impact", "")

        if driver.lower() == "dominant scenario alignment":
            why = sentence(
                f"現時点の主枝は {dominant} と判定されており、説明全体の重心はこの主枝に従っている。"
                f" つまり現局面は単なるラベル列ではなく、複数観測が {dominant} 側へ傾いているという意味を持つ"
            )
            impact = sentence(
                f"主枝が変化すると summary / watchpoints / implications の意味づけもまとめて変わる。"
                f" そのため {dominant} の維持可否は explanation 全体の基準線になる"
            )
        elif driver.lower() == "confidence support":
            why = sentence(
                "現在の confidence は比較的高めで、主枝を支える材料が複数そろっていることを示す。"
                " これは断定の免罪符ではないが、少なくとも現時点では主枝が安定して支持されていることを意味する"
            )
            impact = sentence(
                "主枝は短期的には維持されやすい。"
                " ただし高 confidence でも watchpoints が崩れれば評価は更新されうる"
            )
        elif driver.lower() == "moderate confidence":
            why = sentence(
                "現在の confidence は中程度で、主枝は一定の整合を持つが、まだ強い断定には至らない。"
                " これは『崩れてはいないが、安心し切るほどでもない』中間局面を示唆する"
            )
            impact = sentence(
                "小さくない環境変化が入ると主枝の再評価が起こりうる。"
                " 現局面では結果そのものより、次に何が崩れるかを見る必要がある"
            )
        elif driver.lower() == "fragile confidence":
            why = sentence(
                "現在の confidence は低めで、主枝は暫定仮説に近い。"
                " 見た目の安定があっても、基礎の支持はまだ薄い可能性がある"
            )
            impact = sentence(
                "小さな条件変化でも予測方向が動きやすい。"
                " 現局面では結論固定より watchpoints 優先で読むべきである"
            )
        elif driver.lower() == "limited confidence visibility":
            why = sentence(
                "confidence 情報が十分でないため、主枝の強さを過大評価すべきではない。"
                " ここでは明示的な数値より構造的な整合を見る必要がある"
            )
            impact = sentence(
                "判断時には watchpoints と invalidation をより重視する必要がある。"
                " 数字不足を UI 側で補完してはならない"
            )
        else:
            if band == "high":
                why = sentence(
                    f"{driver} は現在の主枝 {dominant} を比較的強く支える材料の一つである。"
                    " 複数条件が同方向を向いているため、現時点ではこの driver を軽視しにくい"
                )
            elif band == "medium":
                why = sentence(
                    f"{driver} は現在の主枝 {dominant} を支える主要材料の一つである。"
                    " ただし confidence は中程度で、これだけで断定できるほど強い支えではない"
                )
            elif band == "low":
                why = sentence(
                    f"{driver} は現在の主枝 {dominant} を支えているが、その支えはまだ暫定的に読むべきである。"
                    " ほかの条件が逆転すると、ここもすぐに意味を変えうる"
                )
            else:
                why = sentence(
                    f"{driver} は現在の主枝 {dominant} と整合する材料として扱われている。"
                    " ただし強さの評価には慎重さが必要である"
                )

            impact = sentence(
                f"{driver} が崩れると、現在の {risk_text} 局面は一段不安定に読まれやすくなる。"
                " 逆にこの支えが続く限り、直ちに全体像が反転するとは限らない"
            )

        result.append(
            {
                "driver": driver,
                "why": why,
                "impact": impact,
            }
        )

    return dedupe_dict_list(result, ["driver", "why", "impact"])


def extract_drivers(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
    dominant_scenario: str | None,
    confidence: float | None,
    risk_value: str | None,
) -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []

    for raw in normalize_list(pick_first(prediction, "drivers", default=[])):
        item = normalize_driver_struct(raw)
        if item:
            collected.append(item)

    scenario_drivers = normalize_list(pick_first(scenario, "drivers", default=[]))
    for raw in scenario_drivers[:3]:
        item = normalize_driver_struct(raw)
        if item:
            collected.append(item)

    signal_drivers = normalize_list(pick_first(signal, "drivers", "signals", default=[]))
    for raw in signal_drivers[:3]:
        item = normalize_driver_struct(raw)
        if item:
            collected.append(item)

    if dominant_scenario:
        collected.insert(
            0,
            {
                "driver": "dominant scenario alignment",
                "why": sentence(f"現時点の主枝は {dominant_scenario} と判定されている"),
                "impact": sentence("主枝が変化すると explanation 全体の意味づけも見直し対象になる"),
            },
        )

    band = confidence_band(confidence)
    if band == "high":
        collected.append(
            {
                "driver": "confidence support",
                "why": sentence("現在の confidence は高めで、主枝は比較的強く支持されている"),
                "impact": sentence("短期的には現行シナリオが維持されやすい"),
            }
        )
    elif band == "medium":
        collected.append(
            {
                "driver": "moderate confidence",
                "why": sentence("現在の confidence は中程度で、強い断定には使えない"),
                "impact": sentence("追加変化が入ると主枝の再評価が起こりうる"),
            }
        )
    elif band == "low":
        collected.append(
            {
                "driver": "fragile confidence",
                "why": sentence("現在の confidence は低めで、主枝は暫定仮説として扱うべきである"),
                "impact": sentence("小さな環境変化でも予測方向が動きやすい"),
            }
        )
    else:
        collected.append(
            {
                "driver": "limited confidence visibility",
                "why": sentence("confidence 情報が十分でないため、主枝の強さは限定的に解釈すべきである"),
                "impact": sentence("判断時には watch と invalidation をより重視する必要がある"),
            }
        )

    collected = dedupe_dict_list(collected, ["driver", "why", "impact"])[:6]
    return enrich_driver_structs(collected, dominant_scenario, confidence, risk_value)[:6]


def normalize_monitor_struct(item: Any) -> dict[str, str] | None:
    if item is None:
        return None

    if isinstance(item, str):
        text = safe_title(item)
        if not text:
            return None
        return {
            "item": text,
            "trigger": sentence("方向感が明確に変化・加速・悪化した場合"),
            "meaning": sentence(f"{text} は現行シナリオの維持または崩れを判断する監視点"),
        }

    if isinstance(item, dict):
        monitor_item = (
            normalize_str(item.get("item"))
            or normalize_str(item.get("watchpoint"))
            or normalize_str(item.get("name"))
            or normalize_str(item.get("title"))
            or normalize_str(item.get("label"))
            or normalize_str(item.get("signal"))
        )
        trigger = (
            normalize_str(item.get("trigger"))
            or normalize_str(item.get("condition"))
            or normalize_str(item.get("threshold"))
            or normalize_str(item.get("when"))
        )
        meaning = (
            normalize_str(item.get("meaning"))
            or normalize_str(item.get("why"))
            or normalize_str(item.get("reason"))
            or normalize_str(item.get("summary"))
            or normalize_str(item.get("description"))
        )

        if not monitor_item:
            return None
        if not trigger:
            trigger = "方向感が明確に変わった場合"
        if not meaning:
            meaning = f"{monitor_item} は現行予測の継続または見直しを判断するための監視点。"

        return {
            "item": compact_spaces(monitor_item),
            "trigger": sentence(trigger),
            "meaning": sentence(meaning),
        }

    text = safe_title(str(item))
    if not text:
        return None

    return {
        "item": text,
        "trigger": sentence("有意な変化が観測された場合"),
        "meaning": sentence(f"{text} は見立て確認の材料"),
    }


def enrich_monitor_structs(
    monitor: list[dict[str, str]],
    dominant_scenario: str | None,
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    dominant = dominant_scenario or "current scenario"

    for item in monitor:
        monitor_item = item.get("item", "")
        trigger = item.get("trigger", "")
        meaning = item.get("meaning", "")

        enriched_meaning = sentence(
            f"{meaning.rstrip('。')}。"
            f" これは単なる観察項目ではなく、主枝 {dominant} が維持されるのか、"
            "あるいは見直しへ向かうのかを判定するための分岐トリガーとして重要である"
        )

        result.append(
            {
                "item": monitor_item,
                "trigger": sentence(trigger),
                "meaning": enriched_meaning,
            }
        )

    return dedupe_dict_list(result, ["item", "trigger", "meaning"])


def extract_monitor(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
    dominant_scenario: str | None,
) -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []

    for raw in normalize_list(pick_first(prediction, "watchpoints", default=[])):
        item = normalize_monitor_struct(raw)
        if item:
            collected.append(item)

    for raw in normalize_list(pick_first(scenario, "watchpoints", default=[])):
        item = normalize_monitor_struct(raw)
        if item:
            collected.append(item)

    for raw in normalize_list(pick_first(signal, "watchpoints", default=[])):
        item = normalize_monitor_struct(raw)
        if item:
            collected.append(item)

    signal_count = pick_first(prediction, "signal_count", "signalCount", default=None)
    if isinstance(signal_count, (int, float)) or (
        isinstance(signal_count, str) and signal_count.strip()
    ):
        collected.append(
            {
                "item": "signal_count",
                "trigger": sentence("増加または悪化側への偏りが強まった場合"),
                "meaning": sentence("現在の scenario balance が変化する前兆になりうる"),
            }
        )

    if not collected:
        collected = [
            {
                "item": "主要 driver の崩れ",
                "trigger": sentence("driver が逆向きに転じた場合"),
                "meaning": sentence("現行の予測理由そのものが弱まる"),
            },
            {
                "item": "悪化側 signal の増加",
                "trigger": sentence("複数 signal が同時に悪化へ傾いた場合"),
                "meaning": sentence("下振れシナリオの重みが増す可能性がある"),
            },
            {
                "item": "scenario balance の変化",
                "trigger": sentence("best/base/worst の比重が変わった場合"),
                "meaning": sentence("主枝更新の直接要因になる"),
            },
        ]

    collected = dedupe_dict_list(collected, ["item", "trigger", "meaning"])[:6]
    return enrich_monitor_structs(collected, dominant_scenario)[:6]


def extract_watchpoints_from_monitor(monitor: list[dict[str, str]]) -> list[str]:
    return dedupe_keep_order([item["item"] for item in monitor if item.get("item")])[:6]


def domin_scenario_text(value: str) -> str:
    return compact_spaces(value)


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
        collected.insert(
            0,
            f"dominant_scenario が {domin_scenario_text(dominant_scenario)} から変化した場合"
        )

    if not collected:
        collected = [
            "dominant_scenario が変化した場合",
            "confidence が大きく低下した場合",
            "watchpoints の複数が同時に悪化した場合",
        ]

    return dedupe_keep_order(collected)[:6]


def normalize_historical_struct(item: Any) -> dict[str, Any] | None:
    if item is None or not isinstance(item, dict):
        return None

    pattern = (
        normalize_str(item.get("pattern"))
        or normalize_str(item.get("name"))
        or normalize_str(item.get("title"))
        or normalize_str(item.get("pattern_id"))
        or normalize_str(item.get("analog_id"))
    )
    similarity = (
        normalize_str(item.get("similarity"))
        or normalize_str(item.get("summary"))
        or normalize_str(item.get("reason"))
    )
    difference = (
        normalize_str(item.get("difference"))
        or normalize_str(item.get("notes"))
        or normalize_str(item.get("warning"))
    )

    if not similarity:
        matched_signals = to_text_list(item.get("matched_signals"))
        if matched_signals:
            similarity = "matched_signals: " + ", ".join(matched_signals[:4])

    if not difference:
        difference = "現在局面は過去と完全一致ではなく、政策速度・規模・構成の差がある。"

    if not pattern and not similarity:
        return None

    if not pattern:
        pattern = "historical reference"
    if not similarity:
        similarity = "現在構造との共通点が示唆されている。"

    payload: dict[str, Any] = {
        "pattern": compact_spaces(pattern),
        "similarity": sentence(similarity),
        "difference": sentence(difference),
    }

    score = clamp_confidence(
        item.get("match_score", item.get("pattern_confidence", item.get("analog_confidence")))
    )
    if score is not None:
        payload["confidence"] = score

    return payload


def enrich_historical_structs(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    for item in items:
        pattern = item.get("pattern")
        similarity = sentence(
            f"{str(item.get('similarity', '')).rstrip('。')}。"
            " つまり今回は、過去の同型ストレスと部分的に似た圧力配置を持っている可能性がある"
        )
        difference = sentence(
            f"{str(item.get('difference', '')).rstrip('。')}。"
            " したがってこれは再演予言ではなく、比較によって現在の脆さと政策余地を測るための参照として使うべきである"
        )

        enriched = dict(item)
        enriched["pattern"] = pattern
        enriched["similarity"] = similarity
        enriched["difference"] = difference
        result.append(enriched)

    return dedupe_dict_list(result, ["pattern", "similarity", "difference"])


def extract_historical(
    historical_pattern: dict[str, Any] | None,
    historical_analog: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []

    if historical_pattern:
        for raw in normalize_list(
            pick_first(historical_pattern, "matched_patterns", "patterns", default=[])
        )[:3]:
            item = normalize_historical_struct(raw)
            if item:
                collected.append(item)

    if historical_analog:
        for raw in normalize_list(
            pick_first(historical_analog, "top_analogs", "analogs", default=[])
        )[:3]:
            item = normalize_historical_struct(raw)
            if item:
                collected.append(item)

    collected = dedupe_dict_list(collected, ["pattern", "similarity", "difference"])[:4]
    return enrich_historical_structs(collected)[:4]


def normalize_implication_struct(item: Any, fallback_confidence: float | None) -> dict[str, Any] | None:
    if item is None:
        return None

    if isinstance(item, str):
        text = safe_title(item)
        if not text:
            return None
        payload: dict[str, Any] = {
            "outcome": text,
            "path": sentence(f"{text} が現行シナリオの downstream effect として想定される"),
        }
        if fallback_confidence is not None:
            payload["confidence"] = fallback_confidence
        return payload

    if isinstance(item, dict):
        outcome = (
            normalize_str(item.get("outcome"))
            or normalize_str(item.get("name"))
            or normalize_str(item.get("title"))
            or normalize_str(item.get("label"))
            or normalize_str(item.get("event"))
        )
        path = (
            normalize_str(item.get("path"))
            or normalize_str(item.get("reason"))
            or normalize_str(item.get("summary"))
            or normalize_str(item.get("description"))
            or normalize_str(item.get("impact"))
            or normalize_str(item.get("effect"))
        )
        confidence = clamp_confidence(
            item.get("confidence", item.get("probability", fallback_confidence))
        )

        if not outcome:
            return None
        if not path:
            path = f"{outcome} は現行シナリオが続いた場合の派生結果として想定される。"

        payload = {
            "outcome": compact_spaces(outcome),
            "path": sentence(path),
        }
        if confidence is not None:
            payload["confidence"] = confidence
        return payload

    text = safe_title(str(item))
    if not text:
        return None
    payload = {
        "outcome": text,
        "path": sentence(f"{text} が想定帰結として扱われている"),
    }
    if fallback_confidence is not None:
        payload["confidence"] = fallback_confidence
    return payload


def enrich_implication_structs(
    implications: list[dict[str, Any]],
    dominant_scenario: str | None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    dominant = dominant_scenario or "current scenario"

    for item in implications:
        outcome = item.get("outcome")
        path = sentence(
            f"{str(item.get('path', '')).rstrip('。')}。"
            f" 言い換えると、主枝 {dominant} が続く場合に下流で起こりやすい変化を示している"
        )
        enriched = dict(item)
        enriched["outcome"] = outcome
        enriched["path"] = path
        result.append(enriched)

    return dedupe_dict_list(result, ["outcome", "path"])


def extract_implications(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    confidence: float | None,
    dominant_scenario: str | None,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []

    for raw in normalize_list(
        pick_first(prediction, "expected_outcomes", "implications", default=[])
    ):
        item = normalize_implication_struct(raw, confidence)
        if item:
            collected.append(item)

    for raw in normalize_list(
        pick_first(scenario, "expected_outcomes", "implications", default=[])
    )[:3]:
        item = normalize_implication_struct(raw, confidence)
        if item:
            collected.append(item)

    if not collected and confidence is not None:
        collected.append(
            {
                "outcome": "scenario persistence",
                "path": sentence("明確な反証条件が出ない限り、現行主枝がしばらく維持される可能性がある"),
                "confidence": confidence,
            }
        )

    collected = dedupe_dict_list(collected, ["outcome", "path"])[:6]
    return enrich_implication_structs(collected, dominant_scenario)[:6]


def extract_risks(
    prediction: dict[str, Any] | None,
    dominant_scenario: str | None,
    confidence: float | None,
    historical: list[dict[str, Any]],
) -> list[str]:
    collected: list[str] = []

    risk_level = normalize_str(
        pick_first(
            prediction,
            "overall_risk",
            "risk_level",
            "global_risk",
            "risk",
        )
    )
    if risk_level:
        collected.append(f"overall_risk は現在 {risk_level}")

    band = confidence_band(confidence)
    if band == "low":
        collected.append("confidence が低いため、現行主枝への過信は危険")
    elif band == "medium":
        collected.append("confidence は中程度であり、単線的な断定判断は危険")

    if dominant_scenario:
        collected.append(f"dominant_scenario {domin_scenario_text(dominant_scenario)} の固定視は危険")

    if historical:
        first_pattern = historical[0].get("pattern")
        if first_pattern:
            collected.append(f"歴史比較 {first_pattern} を単純再現と誤解するのは危険")

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


def build_decision_line(
    dominant_scenario: str | None,
    risk_value: str | None,
    confidence: float | None,
) -> str:
    dominant = (dominant_scenario or "").lower()
    risk = (risk_value or "").lower()
    band = confidence_band(confidence)

    if dominant == "worst_case" or "critical" in risk or "high" in risk:
        return "Defensive bias should remain strong. Aggressive expansion is not yet justified."
    if dominant == "base_case" and band == "high":
        return "Base-case remains the main branch. Maintain discipline, but do not mistake stability for certainty."
    if dominant == "base_case":
        return "Maintain guarded positioning. Do not mistake temporary stability for full safety."
    if dominant == "best_case":
        return "Positive branch is visible, but the system still calls for measured optimism rather than full risk-on behavior."
    return "Current read supports caution with flexibility. Watch for branch change before making larger directional commitments."


def build_summary(
    prediction_summary: str | None,
    dominant_scenario: str | None,
    confidence: float | None,
    watchpoints: list[str],
    risk_value: str | None,
) -> str:
    dominant = dominant_scenario or "現在の主枝"
    conf_text = format_confidence_text(confidence)
    risk_text = risk_value or "unknown"
    first_watch = watchpoints[0] if watchpoints else "主要 watchpoint"

    if prediction_summary:
        base = prediction_summary.rstrip("。")
        return sentence(
            f"{base}。現時点では主枝は {dominant} にあり、confidence は {conf_text}、overall_risk は {risk_text} と読まれる。"
            f" ただし安定宣言にはまだ早く、次に確認すべき焦点は {first_watch} である"
        )

    return sentence(
        f"最新の prediction は現時点で {dominant} を主枝としている。"
        f" confidence は {conf_text}、overall_risk は {risk_text} と読まれる。"
        f" ただしこれは単純な安心局面を意味せず、{first_watch} の推移次第で見立ては再評価されうる"
    )


def build_interpretation(
    dominant_scenario: str | None,
    confidence: float | None,
    risk_value: str | None,
    drivers: list[dict[str, str]],
    monitor: list[dict[str, str]],
) -> str:
    dominant = dominant_scenario or "current scenario"
    band = confidence_band(confidence)
    risk_text = risk_value or "unknown risk"
    first_driver = drivers[0]["driver"] if drivers else "主要 driver"
    first_monitor = monitor[0]["item"] if monitor else "主要 monitor"

    if band == "high":
        return sentence(
            f"これは {dominant} がかなり強く支持されている局面として読める。"
            f" ただし {risk_text} リスクが残る以上、{first_driver} が支え続けるか、そして {first_monitor} が崩れないかを確認しながら進むべきである"
        )

    if band == "medium":
        return sentence(
            f"これは『崩れてはいないが、安心して拡大へ踏み出せるほどでもない』中間局面として読むのが近い。"
            f" 現在の主枝 {dominant} は一定の整合を持つが、{first_driver} の支えと {first_monitor} の推移を失えば重心はすぐに動きうる"
        )

    if band == "low":
        return sentence(
            f"これは主枝 {dominant} が仮置きされている段階に近く、見立ての安定性はまだ弱い。"
            f" したがって判断は結論より過程を重視し、{first_driver} と {first_monitor} の変化を優先的に追うべきである"
        )

    return sentence(
        "これは現時点で最も整合的な仮説を示しているが、強い断定よりも経過観察を前提に読むべき局面である"
    )


def build_why_it_matters(
    dominant_scenario: str | None,
    confidence: float | None,
    risk_value: str | None,
) -> str:
    dominant = dominant_scenario or "dominant_scenario"
    band = confidence_band(confidence)
    risk_text = risk_value or "unknown risk"

    if band == "high":
        return sentence(
            f"{dominant} を断定未来として誤読せず、強い整合がどの条件で維持されるかを把握するために重要である。"
            f" 特に {risk_text} が残る限り、高 confidence でも過信防止が必要になる"
        )
    if band == "medium":
        return sentence(
            f"{dominant} と confidence を『そこそこ有力だが未確定』な読みとして扱い、"
            "次に何を見れば判断が一段深まるかを明確にするために重要である"
        )
    return sentence(
        f"{dominant} が暫定主枝にすぎないことを明確にし、"
        "過度な楽観や悲観を避けながら watchpoints を監視するために重要である"
    )


def build_narrative_flow(
    headline: str,
    summary: str,
    interpretation: str,
    decision_line: str,
) -> list[str]:
    return [
        sentence(headline),
        sentence(summary),
        sentence(interpretation),
        sentence(decision_line),
    ]


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
        {
            "term": "monitor",
            "meaning": "watchpoints を item / trigger / meaning に構造化した判断支援フィールド",
        },
        {
            "term": "historical",
            "meaning": "過去との比較材料であり、歴史の再演確定を意味しない",
        },
        {
            "term": "interpretation",
            "meaning": "prediction を人間がどう読むべきかを示す中間説明であり、新しい真実ではない",
        },
        {
            "term": "decision_line",
            "meaning": "現局面をどう扱うべきかを一行で示す運用的要約であり、命令ではない",
        },
    ]


def build_must_not_mean() -> list[str]:
    return [
        "prediction は確定未来ではない",
        "confidence は的中率ではない",
        "watchpoints は発生確定イベントではない",
        "historical は歴史の再演確定を意味しない",
        "decision_line は投資助言や命令ではない",
        "interpretation は UI の感想ではなく analysis artifact の説明である",
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
        "decision_line": "Explanation unavailable. Do not infer structured meaning from missing artifacts.",
        "summary": "必要な prediction-layer artifact が不足しているため、構造化 explanation を生成できなかった。",
        "interpretation": "UI が explanation を捏造せず、欠損を正直に表示するため、ここでは unavailable を返す。",
        "why_it_matters": "UI が explanation を捏造せず、欠損を正直に表示するため。",
        "narrative_flow": [
            "prediction explanation unavailable。",
            "必要 artifact が不足している。",
            "structured explanation は生成されていない。",
        ],
        "based_on": [
            str(prediction_path),
            str(scenario_path),
            str(signal_path),
        ],
        "drivers": [],
        "monitor": [],
        "watchpoints": [],
        "historical": [],
        "implications": [],
        "risks": [],
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
    historical_pattern: dict[str, Any] | None,
    historical_analog: dict[str, Any] | None,
    reference_memory: dict[str, Any] | None,
    prediction_path: Path,
    scenario_path: Path,
    signal_path: Path,
    historical_pattern_path: Path,
    historical_analog_path: Path,
    reference_memory_path: Path,
) -> dict[str, Any]:
    as_of = extract_as_of(prediction, scenario, signal)
    dominant_scenario = extract_dominant_scenario(prediction, scenario)
    confidence = extract_confidence(prediction, scenario)
    prediction_summary = extract_summary(prediction)
    risk_value = extract_risk(prediction)

    drivers = extract_drivers(
        prediction,
        scenario,
        signal,
        dominant_scenario,
        confidence,
        risk_value,
    )
    monitor = extract_monitor(
        prediction,
        scenario,
        signal,
        dominant_scenario,
    )
    watchpoints = extract_watchpoints_from_monitor(monitor)
    historical = extract_historical(historical_pattern, historical_analog)
    implications = extract_implications(
        prediction,
        scenario,
        confidence,
        dominant_scenario,
    )
    risks = extract_risks(prediction, dominant_scenario, confidence, historical)
    invalidation = extract_invalidation(prediction, scenario, dominant_scenario)

    headline = build_headline(dominant_scenario, watchpoints, confidence)
    decision_line = build_decision_line(dominant_scenario, risk_value, confidence)
    summary = build_summary(
        prediction_summary,
        dominant_scenario,
        confidence,
        watchpoints,
        risk_value,
    )
    interpretation = build_interpretation(
        dominant_scenario,
        confidence,
        risk_value,
        drivers,
        monitor,
    )
    why_it_matters = build_why_it_matters(
        dominant_scenario,
        confidence,
        risk_value,
    )
    narrative_flow = build_narrative_flow(
        headline,
        summary,
        interpretation,
        decision_line,
    )

    based_on: list[str] = [
        str(prediction_path),
        str(scenario_path),
        str(signal_path),
    ]
    if historical_pattern_path.exists():
        based_on.append(str(historical_pattern_path))
    if historical_analog_path.exists():
        based_on.append(str(historical_analog_path))
    if reference_memory_path.exists():
        based_on.append(str(reference_memory_path))

    artifact: dict[str, Any] = {
        "as_of": as_of,
        "subject": "prediction",
        "status": "ok",
        "headline": headline,
        "decision_line": decision_line,
        "summary": summary,
        "interpretation": interpretation,
        "why_it_matters": why_it_matters,
        "narrative_flow": narrative_flow,
        "based_on": based_on,
        "context": {
            "dominant_scenario": dominant_scenario,
            "confidence": confidence,
            "overall_risk": risk_value,
        },
        "drivers": drivers,
        "monitor": monitor,
        "watchpoints": watchpoints,
        "historical": historical,
        "implications": implications,
        "risks": risks,
        "invalidation": invalidation,
        "must_not_mean": build_must_not_mean(),
        "ui_terms": build_ui_terms(),
        "generated_at": utc_now_iso(),
    }

    if reference_memory is not None:
        memory_refs = to_text_list(
            pick_first(
                reference_memory,
                "reference_memory",
                "memories",
                "historical_patterns",
                default=[],
            )
        )
        if memory_refs:
            artifact["reference_memory"] = memory_refs[:6]

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
    historical_pattern = read_json(args.historical_pattern)
    historical_analog = read_json(args.historical_analog)
    reference_memory = read_json(args.reference_memory)

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
        historical_pattern=historical_pattern,
        historical_analog=historical_analog,
        reference_memory=reference_memory,
        prediction_path=args.prediction,
        scenario_path=args.scenario,
        signal_path=args.signal,
        historical_pattern_path=args.historical_pattern,
        historical_analog_path=args.historical_analog,
        reference_memory_path=args.reference_memory,
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
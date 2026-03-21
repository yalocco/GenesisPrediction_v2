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
    - SSOT = analysis
    - Multilingual fields are generated in analysis, never UI.
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

SCENARIO_PATH = REPO_ROOT / "analysis" / "prediction" / "scenario_latest.json"
SIGNAL_PATH = REPO_ROOT / "analysis" / "prediction" / "signal_latest.json"
PREDICTION_PATH = REPO_ROOT / "analysis" / "prediction" / "prediction_latest.json"

EXPLANATION_DIR = REPO_ROOT / "analysis" / "explanation"
OUTPUT_PATH = EXPLANATION_DIR / "scenario_explanation_latest.json"

LANG_DEFAULT = "en"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]

SCENARIO_LABELS = {
    "best_case": {"ja": "best_case", "en": "best_case", "th": "best_case"},
    "base_case": {"ja": "base_case", "en": "base_case", "th": "base_case"},
    "worst_case": {"ja": "worst_case", "en": "worst_case", "th": "worst_case"},
    "unknown": {"ja": "unknown", "en": "unknown", "th": "unknown"},
}

KEY_LABELS = {
    "base_case を支える主要 driver が現在も有効": {
        "ja": "base_case を支える主要 driver が現在も有効",
        "en": "The main drivers supporting base_case remain active.",
        "th": "แรงขับหลักที่สนับสนุน base_case ยังทำงานอยู่",
    },
    "worst_case 側の trigger が完全には解消されていない": {
        "ja": "worst_case 側の trigger が完全には解消されていない",
        "en": "Worst-case triggers have not been fully cleared.",
        "th": "ตัวกระตุ้นฝั่ง worst_case ยังไม่ถูกคลี่คลายหมด",
    },
    "best_case に移行するための強い signal は不足している": {
        "ja": "best_case に移行するための強い signal は不足している",
        "en": "There is not yet a strong enough signal to move toward best_case.",
        "th": "ยังไม่มีสัญญาณที่แรงพอจะขยับไปสู่ best_case",
    },
    "悪化側の driver が現在の分岐を強く支えている": {
        "ja": "悪化側の driver が現在の分岐を強く支えている",
        "en": "Deterioration-side drivers are strongly supporting the current branch structure.",
        "th": "แรงขับฝั่งเสื่อมลงกำลังสนับสนุนโครงสร้างแขนงปัจจุบันอย่างชัดเจน",
    },
    "改善側へ戻すための signal が不足している": {
        "ja": "改善側へ戻すための signal が不足している",
        "en": "Signals needed to move back toward improvement are insufficient.",
        "th": "สัญญาณที่จะพากลับไปสู่ฝั่งดีขึ้นยังไม่เพียงพอ",
    },
    "改善側の driver が現時点では有効": {
        "ja": "改善側の driver が現時点では有効",
        "en": "Improvement-side drivers are currently active.",
        "th": "แรงขับฝั่งดีขึ้นยังทำงานอยู่ในขณะนี้",
    },
    "ただし下振れ側の再浮上条件は完全に消えていない": {
        "ja": "ただし下振れ側の再浮上条件は完全に消えていない",
        "en": "However, the conditions for downside re-emergence have not disappeared.",
        "th": "อย่างไรก็ดี เงื่อนไขที่ทำให้ฝั่งแย่ลงกลับมานั้นยังไม่หายไปทั้งหมด",
    },
    "worst_case に接続する signal の増加": {
        "ja": "worst_case に接続する signal の増加",
        "en": "An increase in signals connected to worst_case.",
        "th": "การเพิ่มขึ้นของสัญญาณที่เชื่อมไปสู่ worst_case",
    },
    "driver の一部崩壊": {
        "ja": "driver の一部崩壊",
        "en": "Partial collapse of current drivers.",
        "th": "การพังลงบางส่วนของ driver ปัจจุบัน",
    },
    "外部ショックの発生": {
        "ja": "外部ショックの発生",
        "en": "The occurrence of an external shock.",
        "th": "การเกิดช็อกจากภายนอก",
    },
    "dominant scenario が base_case から変化した場合": {
        "ja": "dominant scenario が base_case から変化した場合",
        "en": "If the dominant scenario shifts away from base_case.",
        "th": "หาก dominant scenario เปลี่ยนออกจาก base_case",
    },
    "worst_case 側の条件が明確に強化された場合": {
        "ja": "worst_case 側の条件が明確に強化された場合",
        "en": "If worst-case conditions are clearly reinforced.",
        "th": "หากเงื่อนไขฝั่ง worst_case แข็งแรงขึ้นอย่างชัดเจน",
    },
    "best_case を支える新規 signal が成立した場合": {
        "ja": "best_case を支える新規 signal が成立した場合",
        "en": "If new signals supporting best_case are established.",
        "th": "หากเกิดสัญญาณใหม่ที่สนับสนุน best_case",
    },
    "base_case は安全を意味しない": {
        "ja": "base_case は安全を意味しない",
        "en": "base_case does not mean safety.",
        "th": "base_case ไม่ได้หมายถึงความปลอดภัย",
    },
    "worst_case は確定未来ではない": {
        "ja": "worst_case は確定未来ではない",
        "en": "worst_case is not a predetermined future.",
        "th": "worst_case ไม่ใช่อนาคตที่กำหนดไว้แน่นอน",
    },
    "best_case は期待ではなく条件付き分岐である": {
        "ja": "best_case は期待ではなく条件付き分岐である",
        "en": "best_case is a conditional branch, not a wish.",
        "th": "best_case เป็นแขนงตามเงื่อนไข ไม่ใช่ความคาดหวัง",
    },
}

UI_TERM_MEANINGS = {
    "scenario": {
        "ja": "複数の未来分岐を構造として表現したものであり、単一の予測ではない",
        "en": "A structure that represents multiple future branches, not a single forecast.",
        "th": "โครงสร้างที่แสดงหลายแขนงของอนาคต ไม่ใช่การคาดการณ์เพียงเส้นเดียว",
    },
    "base_case": {
        "ja": "現時点で最も現実的と評価される主枝であり、固定された未来ではない",
        "en": "The main branch judged most realistic at the moment, not a fixed future.",
        "th": "แขนงหลักที่ถูกมองว่าสมจริงที่สุด ณ ตอนนี้ ไม่ใช่อนาคตที่ตายตัว",
    },
    "worst_case": {
        "ja": "回避すべきリスクシナリオであり、発生確定ではない",
        "en": "A risk scenario to avoid, not a confirmed outcome.",
        "th": "ฉากทัศน์ความเสี่ยงที่ควรหลีกเลี่ยง ไม่ใช่ผลลัพธ์ที่ยืนยันแล้ว",
    },
    "best_case": {
        "ja": "条件が整った場合に成立する改善シナリオであり、保証された結果ではない",
        "en": "An improvement scenario that holds if conditions align, not a guaranteed result.",
        "th": "ฉากทัศน์ที่ดีขึ้นซึ่งเกิดได้เมื่อเงื่อนไขลงตัว ไม่ใช่ผลลัพธ์ที่รับประกัน",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build scenario explanation artifact from prediction-layer outputs."
    )
    parser.add_argument("--scenario", type=Path, default=SCENARIO_PATH, help="Path to scenario_latest.json")
    parser.add_argument("--signal", type=Path, default=SIGNAL_PATH, help="Path to signal_latest.json")
    parser.add_argument("--prediction", type=Path, default=PREDICTION_PATH, help="Path to prediction_latest.json")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Path to write scenario_explanation_latest.json")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output JSON with indentation.")
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


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def sentence(text: str) -> str:
    s = compact_spaces(text)
    if not s:
        return ""
    if s.endswith(("。", "．", ".", "!", "！", "?", "？")):
        return s
    return s + "。"


def sentence_lang(text: str, lang: str) -> str:
    s = compact_spaces(text)
    if not s:
        return ""
    if lang == "ja":
        if s.endswith(("。", "．", "!", "！", "?", "？")):
            return s
        return s + "。"
    if s.endswith((".", "!", "?")):
        return s
    return s + "."


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = compact_spaces(item)
        if not cleaned or cleaned in seen:
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
            )
            if text:
                result.append(compact_spaces(text))
            continue
        result.append(compact_spaces(str(item)))

    return dedupe_keep_order([x for x in result if x])


def translate_key_generic(text: str) -> dict[str, str]:
    key = compact_spaces(text)
    if key in KEY_LABELS:
        return KEY_LABELS[key]
    return {
        "ja": key,
        "en": key,
        "th": key,
    }


def wrap_i18n(ja: str, en: str | None = None, th: str | None = None) -> dict[str, str]:
    return {
        "ja": compact_spaces(ja),
        "en": compact_spaces(en or ja),
        "th": compact_spaces(th or ja),
    }


def list_i18n_from_strings(items: list[str]) -> dict[str, list[str]]:
    out = {"ja": [], "en": [], "th": []}
    for item in items:
        row = translate_key_generic(item)
        out["ja"].append(row["ja"])
        out["en"].append(row["en"])
        out["th"].append(row["th"])
    return out


def ui_terms_with_i18n(terms: list[dict[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in terms:
        term = item.get("term", "")
        meaning = item.get("meaning", "")
        result.append(
            {
                "term": term,
                "meaning": meaning,
                "meaning_i18n": UI_TERM_MEANINGS.get(term, wrap_i18n(meaning)),
            }
        )
    return result


def label_for_scenario(value: str | None) -> dict[str, str]:
    if not value:
        return SCENARIO_LABELS["unknown"]
    return SCENARIO_LABELS.get(value.lower(), {"ja": value, "en": value, "th": value})


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
            return "base remains dominant, but room for both upside and downside branches still remains"
        if worst_exists:
            return "base remains dominant, but the worst_case side cannot be ignored"
        if best_exists:
            return "base remains dominant, with room for improvement still open"
        return "base remains dominant and the branching structure is relatively stable"

    if dominant == "worst_case":
        return "worst_case is dominant and the structure is strongly tilted toward deterioration"

    if dominant == "best_case":
        return "best_case is dominant, but the structure remains highly condition-dependent"

    signal_count = pick_first(signal, "signal_count", "count", default=None)
    if signal_count is not None:
        return "branch balance is not fixed, and the dominant branch can still move as signals change"
    return "a branching structure exists, but its balance still requires cautious reading"


def build_balance_text_i18n(
    dominant: str | None,
    branches: dict[str, str | None],
    signal: dict[str, Any] | None,
) -> dict[str, str]:
    if dominant == "base_case":
        worst_exists = branches.get("worst_case") is not None
        best_exists = branches.get("best_case") is not None
        if worst_exists and best_exists:
            return wrap_i18n(
                "base優勢だが上下分岐の余地が残る状態",
                "base remains dominant, but room for both upside and downside branches still remains.",
                "base ยังคงเป็นแกนหลัก แต่ยังมีพื้นที่ให้แตกแขนงได้ทั้งขึ้นและลง",
            )
        if worst_exists:
            return wrap_i18n(
                "base優勢だがworstが無視できない状態",
                "base remains dominant, but the worst_case side cannot be ignored.",
                "base ยังเป็นแกนหลัก แต่ฝั่ง worst_case ยังไม่อาจมองข้ามได้",
            )
        if best_exists:
            return wrap_i18n(
                "base優勢で改善余地も残る状態",
                "base remains dominant, with room for improvement still open.",
                "base ยังเป็นแกนหลัก และยังมีช่องให้ดีขึ้นได้",
            )
        return wrap_i18n(
            "base優勢で分岐は比較的安定している状態",
            "base remains dominant and the branching structure is relatively stable.",
            "base ยังเป็นแกนหลัก และโครงสร้างการแตกแขนงค่อนข้างทรงตัว",
        )

    if dominant == "worst_case":
        return wrap_i18n(
            "worst優勢で悪化側への片寄りが強い状態",
            "worst_case is dominant and the structure is strongly tilted toward deterioration.",
            "worst_case เป็นแกนหลักและโครงสร้างเอนเอียงไปทางเสื่อมลงอย่างชัดเจน",
        )

    if dominant == "best_case":
        return wrap_i18n(
            "best優勢だが条件依存性が高い状態",
            "best_case is dominant, but the structure remains highly condition-dependent.",
            "best_case เป็นแกนหลัก แต่ยังขึ้นอยู่กับเงื่อนไขอย่างมาก",
        )

    signal_count = pick_first(signal, "signal_count", "count", default=None)
    if signal_count is not None:
        return wrap_i18n(
            "分岐の均衡が定まらず、signal 変化で主枝が動きうる状態",
            "Branch balance is not fixed, and the dominant branch can still move as signals change.",
            "สมดุลของแขนงยังไม่ตายตัว และแขนงหลักยังเปลี่ยนได้เมื่อสัญญาณเปลี่ยน",
        )

    return wrap_i18n(
        "分岐構造は存在するが、均衡の読み取りには慎重さが必要な状態",
        "A branching structure exists, but its balance still requires cautious reading.",
        "มีโครงสร้างการแตกแขนงอยู่ แต่ยังต้องอ่านสมดุลอย่างระมัดระวัง",
    )


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
        return "Multiple scenarios coexist, with base_case at the center and room still left for both upside and downside branching."
    if dominant == "worst_case":
        return "A deterioration-side scenario has become dominant, and the branching structure is strengthening toward worst_case."
    if dominant == "best_case":
        return "An improvement-side scenario is dominant, but it remains highly condition-dependent and downside reversion risk still remains."
    return f"Multiple scenarios coexist, and {balance}."


def build_headline_i18n(dominant: str | None, balance_i18n: dict[str, str]) -> dict[str, str]:
    if dominant == "base_case":
        return wrap_i18n(
            "複数シナリオが併存し、base_case を軸に上下分岐の余地が残る状態",
            "Multiple scenarios coexist, with base_case at the center and room still left for both upside and downside branching.",
            "มีหลาย scenario อยู่ร่วมกัน โดยมี base_case เป็นแกนกลาง และยังมีพื้นที่ให้แตกแขนงได้ทั้งขึ้นและลง",
        )
    if dominant == "worst_case":
        return wrap_i18n(
            "悪化側シナリオが主枝となり、worst_case 寄りの分岐構造が強まる状態",
            "A deterioration-side scenario has become dominant, and the branching structure is strengthening toward worst_case.",
            "scenario ฝั่งเสื่อมลงกลายเป็นแกนหลัก และโครงสร้างการแตกแขนงกำลังเอนเข้าหา worst_case มากขึ้น",
        )
    if dominant == "best_case":
        return wrap_i18n(
            "改善側シナリオが主枝だが、条件依存性が高く再悪化余地も残る状態",
            "An improvement-side scenario is dominant, but it remains highly condition-dependent and downside reversion risk still remains.",
            "scenario ฝั่งดีขึ้นเป็นแกนหลัก แต่ยังขึ้นอยู่กับเงื่อนไขสูง และยังมีความเสี่ยงกลับไปแย่ลงอีก",
        )
    return wrap_i18n(
        f"複数シナリオが併存し、{balance_i18n['ja']}",
        f"Multiple scenarios coexist, and {balance_i18n['en']}",
        f"มีหลาย scenario อยู่ร่วมกัน และ {balance_i18n['th']}",
    )


def build_summary(
    dominant: str | None,
    balance: str,
    branches: dict[str, str | None],
) -> str:
    dominant_text = dominant or "unknown"

    parts: list[str] = [f"The current scenario structure is centered on {dominant_text}."]

    branch_bits: list[str] = []
    if branches.get("best_case"):
        branch_bits.append(f"best_case {branches['best_case']}")
    if branches.get("base_case"):
        branch_bits.append(f"base_case {branches['base_case']}")
    if branches.get("worst_case"):
        branch_bits.append(f"worst_case {branches['worst_case']}")

    if branch_bits:
        parts.append("Branch balance is " + " / ".join(branch_bits) + ".")

    parts.append(f"Overall, {balance}.")
    return " ".join(parts)


def build_summary_i18n(
    dominant: str | None,
    balance_i18n: dict[str, str],
    branches: dict[str, str | None],
) -> dict[str, str]:
    dominant_label = label_for_scenario(dominant)

    branch_bits: list[str] = []
    if branches.get("best_case"):
        branch_bits.append(f"best_case {branches['best_case']}")
    if branches.get("base_case"):
        branch_bits.append(f"base_case {branches['base_case']}")
    if branches.get("worst_case"):
        branch_bits.append(f"worst_case {branches['worst_case']}")
    branch_text = " / ".join(branch_bits) if branch_bits else "branch balance unavailable"

    return wrap_i18n(
        f"現在の scenario 構造は {dominant_label['ja']} を中心に展開している。分岐バランスは {branch_text}。全体としては {balance_i18n['ja']}。",
        f"The current scenario structure is centered on {dominant_label['en']}. Branch balance is {branch_text}. Overall, {balance_i18n['en']}.",
        f"โครงสร้าง scenario ปัจจุบันมีศูนย์กลางอยู่ที่ {dominant_label['th']} สมดุลของแขนงคือ {branch_text} โดยรวมแล้ว {balance_i18n['th']}",
    )


def build_why_it_matters(dominant: str | None) -> str:
    if dominant == "worst_case":
        return (
            "This matters because reading the deterioration side as branching structure rather than raw fear helps clarify monitoring and decision priorities without overreaction."
        )
    if dominant == "best_case":
        return (
            "This matters because the improvement-side branch should not be confused with optimism, and the conditions for sustaining or breaking it must be understood."
        )
    return (
        "This matters because understanding the outlook as branching structure rather than a single future helps avoid excess optimism or pessimism and supports realistic monitoring and decisions."
    )


def build_why_it_matters_i18n(dominant: str | None) -> dict[str, str]:
    if dominant == "worst_case":
        return wrap_i18n(
            "悪化側を単なる恐怖ではなく分岐構造として理解することで、過剰反応ではなく監視と判断の優先順位を明確にできるため。",
            "This matters because reading the deterioration side as branching structure rather than raw fear helps clarify monitoring and decision priorities without overreaction.",
            "สิ่งนี้สำคัญเพราะการมองฝั่งเสื่อมลงเป็นโครงสร้างการแตกแขนง ไม่ใช่แค่ความกลัว จะช่วยจัดลำดับการเฝ้าดูและการตัดสินใจโดยไม่ตอบสนองเกินเหตุ",
        )
    if dominant == "best_case":
        return wrap_i18n(
            "改善側の主枝を過度な楽観と混同せず、どの条件で維持・崩壊するかを理解するため。",
            "This matters because the improvement-side branch should not be confused with optimism, and the conditions for sustaining or breaking it must be understood.",
            "สิ่งนี้สำคัญเพราะไม่ควรสับสนแขนงฝั่งดีขึ้นกับความมองโลกในแง่ดี และต้องเข้าใจเงื่อนไขที่ทำให้มันอยู่ต่อหรือพังลง",
        )
    return wrap_i18n(
        "単一の未来ではなく分岐構造として理解することで、過剰な楽観や悲観を避け、現実的な監視と判断が可能になるため。",
        "This matters because understanding the outlook as branching structure rather than a single future helps avoid excess optimism or pessimism and supports realistic monitoring and decisions.",
        "สิ่งนี้สำคัญเพราะการเข้าใจภาพอนาคตเป็นโครงสร้างการแตกแขนง ไม่ใช่อนาคตเส้นเดียว จะช่วยหลีกเลี่ยงความมองบวกหรือลบเกินไป และทำให้เฝ้าดูพร้อมตัดสินใจได้อย่างสมจริง",
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

    headline_i18n = wrap_i18n(
        "scenario explanation unavailable",
        "scenario explanation unavailable",
        "scenario explanation unavailable",
    )
    summary_i18n = wrap_i18n(
        "必要な prediction-layer artifact が不足しているため、scenario explanation を生成できなかった。",
        "Scenario explanation could not be generated because required prediction-layer artifacts are missing.",
        "ไม่สามารถสร้าง scenario explanation ได้ เพราะ prediction-layer artifacts ที่จำเป็นขาดหายไป",
    )
    why_i18n = wrap_i18n(
        "UI が scenario explanation を捏造せず、欠損を正直に表示するため。",
        "So that UI does not fabricate scenario explanation and shows missing state honestly.",
        "เพื่อให้ UI ไม่แต่ง scenario explanation ขึ้นเอง และแสดงสถานะที่ขาดหายอย่างตรงไปตรงมา",
    )

    artifact: dict[str, Any] = {
        "as_of": None,
        "subject": "scenario",
        "status": "unavailable",
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "headline": headline_i18n["en"],
        "headline_i18n": headline_i18n,
        "summary": summary_i18n["en"],
        "summary_i18n": summary_i18n,
        "why_it_matters": why_i18n["en"],
        "why_it_matters_i18n": why_i18n,
        "based_on": [str(scenario_path), str(signal_path), str(prediction_path)],
        "scenario_structure": {
            "dominant": None,
            "alternatives": [],
            "balance": "unavailable",
        },
        "scenario_structure_i18n": {
            "dominant": label_for_scenario(None),
            "alternatives": [],
            "balance": wrap_i18n("unavailable", "unavailable", "unavailable"),
        },
        "drivers": [],
        "drivers_i18n": {"ja": [], "en": [], "th": []},
        "watchpoints": [],
        "watchpoints_i18n": {"ja": [], "en": [], "th": []},
        "invalidation": [],
        "invalidation_i18n": {"ja": [], "en": [], "th": []},
        "must_not_mean": [
            "unavailable does not mean safe.",
            "base_case does not mean safety.",
            "worst_case is not a predetermined future.",
        ],
        "must_not_mean_i18n": {
            "ja": [
                "unavailable は安全を意味しない",
                "base_case は安全を意味しない",
                "worst_case は確定未来ではない",
            ],
            "en": [
                "unavailable does not mean safe.",
                "base_case does not mean safety.",
                "worst_case is not a predetermined future.",
            ],
            "th": [
                "unavailable ไม่ได้หมายถึงความปลอดภัย",
                "base_case ไม่ได้หมายถึงความปลอดภัย",
                "worst_case ไม่ใช่อนาคตที่กำหนดไว้แน่นอน",
            ],
        },
        "ui_terms": ui_terms_with_i18n(build_ui_terms()),
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
    balance_i18n = build_balance_text_i18n(dominant, branches, signal)

    alternatives = [name for name in ("best_case", "base_case", "worst_case") if name != dominant]

    headline_i18n = build_headline_i18n(dominant, balance_i18n)
    summary_i18n = build_summary_i18n(dominant, balance_i18n, branches)
    why_i18n = build_why_it_matters_i18n(dominant)

    drivers = extract_drivers(scenario, signal, prediction, dominant)
    watchpoints = extract_watchpoints(scenario, signal)
    invalidation = extract_invalidation(scenario, prediction, dominant)

    artifact: dict[str, Any] = {
        "as_of": as_of,
        "subject": "scenario",
        "status": "ok",
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "headline": headline_i18n["en"],
        "headline_i18n": headline_i18n,
        "summary": summary_i18n["en"],
        "summary_i18n": summary_i18n,
        "why_it_matters": why_i18n["en"],
        "why_it_matters_i18n": why_i18n,
        "based_on": [str(scenario_path), str(signal_path), str(prediction_path)],
        "scenario_structure": {
            "dominant": dominant,
            "alternatives": alternatives,
            "balance": balance,
        },
        "scenario_structure_i18n": {
            "dominant": label_for_scenario(dominant),
            "alternatives": [label_for_scenario(name) for name in alternatives],
            "balance": balance_i18n,
        },
        "drivers": list_i18n_from_strings(drivers)["en"],
        "drivers_i18n": list_i18n_from_strings(drivers),
        "watchpoints": list_i18n_from_strings(watchpoints)["en"],
        "watchpoints_i18n": list_i18n_from_strings(watchpoints),
        "invalidation": list_i18n_from_strings(invalidation)["en"],
        "invalidation_i18n": list_i18n_from_strings(invalidation),
        "must_not_mean": [
            "base_case does not mean safety.",
            "worst_case is not a predetermined future.",
            "best_case is a conditional branch, not a wish.",
        ],
        "must_not_mean_i18n": {
            "ja": [
                "base_case は安全を意味しない",
                "worst_case は確定未来ではない",
                "best_case は期待ではなく条件付き分岐である",
            ],
            "en": [
                "base_case does not mean safety.",
                "worst_case is not a predetermined future.",
                "best_case is a conditional branch, not a wish.",
            ],
            "th": [
                "base_case ไม่ได้หมายถึงความปลอดภัย",
                "worst_case ไม่ใช่อนาคตที่กำหนดไว้แน่นอน",
                "best_case เป็นแขนงตามเงื่อนไข ไม่ใช่ความคาดหวัง",
            ],
        },
        "ui_terms": ui_terms_with_i18n(build_ui_terms()),
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
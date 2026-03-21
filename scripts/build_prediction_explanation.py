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

PREDICTION_PATH = REPO_ROOT / "analysis" / "prediction" / "prediction_latest.json"
SCENARIO_PATH = REPO_ROOT / "analysis" / "prediction" / "scenario_latest.json"
SIGNAL_PATH = REPO_ROOT / "analysis" / "prediction" / "signal_latest.json"
HISTORICAL_PATTERN_PATH = REPO_ROOT / "analysis" / "prediction" / "historical_pattern_latest.json"
HISTORICAL_ANALOG_PATH = REPO_ROOT / "analysis" / "prediction" / "historical_analog_latest.json"
REFERENCE_MEMORY_PATH = REPO_ROOT / "analysis" / "prediction" / "reference_memory_latest.json"

EXPLANATION_DIR = REPO_ROOT / "analysis" / "explanation"
OUTPUT_PATH = EXPLANATION_DIR / "prediction_explanation_latest.json"

LANG_DEFAULT = "ja"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]

SCENARIO_LABELS = {
    "best_case": {"ja": "最良シナリオ", "en": "best_case", "th": "กรณีดีที่สุด"},
    "base_case": {"ja": "基本シナリオ", "en": "base_case", "th": "กรณีฐาน"},
    "worst_case": {"ja": "最悪シナリオ", "en": "worst_case", "th": "กรณีเลวร้ายที่สุด"},
}

RISK_LABELS = {
    "guarded": {"ja": "警戒", "en": "guarded", "th": "เฝ้าระวัง"},
    "stable": {"ja": "安定", "en": "stable", "th": "ทรงตัว"},
    "elevated": {"ja": "警戒", "en": "elevated", "th": "ยกระดับ"},
    "high": {"ja": "高い", "en": "high", "th": "สูง"},
    "critical": {"ja": "危機", "en": "critical", "th": "วิกฤต"},
    "low": {"ja": "低い", "en": "low", "th": "ต่ำ"},
    "warn": {"ja": "警戒", "en": "warn", "th": "เตือน"},
    "unknown": {"ja": "不明", "en": "unknown", "th": "ไม่ทราบ"},
}

CONFIDENCE_BAND_LABELS = {
    "high": {"ja": "高め", "en": "high", "th": "ค่อนข้างสูง"},
    "medium": {"ja": "中程度", "en": "moderate", "th": "ปานกลาง"},
    "low": {"ja": "低め", "en": "low", "th": "ต่ำ"},
    "unknown": {"ja": "不明", "en": "unknown", "th": "ไม่ทราบ"},
}

KEY_LABELS = {
    "dominant scenario alignment": {
        "ja": "主枝整合",
        "en": "dominant scenario alignment",
        "th": "ความสอดคล้องของแขนงหลัก",
    },
    "confidence support": {
        "ja": "信頼度の支え",
        "en": "confidence support",
        "th": "แรงหนุนของ confidence",
    },
    "moderate confidence": {
        "ja": "中程度の信頼度",
        "en": "moderate confidence",
        "th": "confidence ระดับปานกลาง",
    },
    "fragile confidence": {
        "ja": "脆弱な信頼度",
        "en": "fragile confidence",
        "th": "confidence ที่เปราะบาง",
    },
    "limited confidence visibility": {
        "ja": "信頼度可視性の不足",
        "en": "limited confidence visibility",
        "th": "การมองเห็น confidence ที่จำกัด",
    },
    "signal count": {
        "ja": "signal 数",
        "en": "signal count",
        "th": "จำนวน signal",
    },
    "signal_count": {
        "ja": "signal 数",
        "en": "signal_count",
        "th": "จำนวน signal",
    },
    "bank funding stress": {
        "ja": "銀行資金調達ストレス",
        "en": "bank funding stress",
        "th": "ความตึงตัวของเงินทุนธนาคาร",
    },
    "credit spread widening": {
        "ja": "信用スプレッド拡大",
        "en": "credit spread widening",
        "th": "ส่วนต่างเครดิตขยายกว้างขึ้น",
    },
    "loan loss increase": {
        "ja": "貸倒増加",
        "en": "loan loss increase",
        "th": "หนี้เสียเพิ่มขึ้น",
    },
    "housing or equity drawdown": {
        "ja": "住宅・株式の下落",
        "en": "housing or equity drawdown",
        "th": "การปรับลดลงของที่อยู่อาศัยหรือหุ้น",
    },
    "policy emergency liquidity": {
        "ja": "緊急流動性政策",
        "en": "policy emergency liquidity",
        "th": "มาตรการสภาพคล่องฉุกเฉินของนโยบาย",
    },
    "fx reserve drop": {
        "ja": "外貨準備低下",
        "en": "fx reserve drop",
        "th": "เงินสำรองระหว่างประเทศลดลง",
    },
    "forward market stress": {
        "ja": "先物市場ストレス",
        "en": "forward market stress",
        "th": "ความตึงเครียดในตลาดล่วงหน้า",
    },
    "sovereign spread widening": {
        "ja": "国債スプレッド拡大",
        "en": "sovereign spread widening",
        "th": "ส่วนต่างพันธบัตรรัฐบาลขยายกว้างขึ้น",
    },
    "capital outflow": {
        "ja": "資本流出",
        "en": "capital outflow",
        "th": "เงินทุนไหลออก",
    },
    "banking stress": {
        "ja": "銀行システムストレス",
        "en": "banking stress",
        "th": "ความตึงเครียดในระบบธนาคาร",
    },
    "currency instability": {
        "ja": "通貨不安定",
        "en": "currency instability",
        "th": "ความไม่เสถียรของค่าเงิน",
    },
    "interbank spread surge": {
        "ja": "短期市場スプレッド急拡大",
        "en": "interbank spread surge",
        "th": "ส่วนต่างตลาดเงินระหว่างธนาคารพุ่งสูง",
    },
    "equities down": {
        "ja": "株式下落",
        "en": "equities down",
        "th": "หุ้นปรับตัวลง",
    },
    "credit spreads up": {
        "ja": "信用スプレッド上昇",
        "en": "credit spreads up",
        "th": "ส่วนต่างเครดิตเพิ่มขึ้น",
    },
    "growth down": {
        "ja": "成長減速",
        "en": "growth down",
        "th": "การเติบโตชะลอลง",
    },
    "unemployment up": {
        "ja": "失業率上昇",
        "en": "unemployment up",
        "th": "การว่างงานเพิ่มขึ้น",
    },
    "safe haven up": {
        "ja": "安全資産選好",
        "en": "safe haven up",
        "th": "ความต้องการสินทรัพย์ปลอดภัยเพิ่มขึ้น",
    },
    "currency down": {
        "ja": "通貨下落",
        "en": "currency down",
        "th": "ค่าเงินอ่อนลง",
    },
    "inflation up": {
        "ja": "インフレ上昇",
        "en": "inflation up",
        "th": "เงินเฟ้อเพิ่มขึ้น",
    },
    "rates up": {
        "ja": "金利上昇",
        "en": "rates up",
        "th": "อัตราดอกเบี้ยเพิ่มขึ้น",
    },
    "default risk up": {
        "ja": "デフォルトリスク上昇",
        "en": "default risk up",
        "th": "ความเสี่ยงผิดนัดชำระเพิ่มขึ้น",
    },
    "volatility up": {
        "ja": "変動率上昇",
        "en": "volatility up",
        "th": "ความผันผวนเพิ่มขึ้น",
    },
    "overall direction falling": {
        "ja": "全体方向の下向き",
        "en": "overall direction falling",
        "th": "ทิศทางโดยรวมกำลังอ่อนลง",
    },
    "risk level critical": {
        "ja": "リスク水準は危機寄り",
        "en": "risk level critical",
        "th": "ระดับความเสี่ยงอยู่ฝั่งวิกฤต",
    },
    "risk pressure": {
        "ja": "リスク圧力",
        "en": "risk pressure",
        "th": "แรงกดดันด้านความเสี่ยง",
    },
    "regime shift pressure": {
        "ja": "レジーム転換圧力",
        "en": "regime shift pressure",
        "th": "แรงกดดันต่อการเปลี่ยนระบอบ",
    },
    "pressure easing": {
        "ja": "圧力緩和",
        "en": "pressure easing",
        "th": "แรงกดดันเริ่มผ่อนลง",
    },
    "debt bubble banking crisis": {
        "ja": "債務バブルと銀行危機",
        "en": "debt bubble banking crisis",
        "th": "ฟองสบู่หนี้และวิกฤตธนาคาร",
    },
    "pandemic > labor disruption > supply stress > state burden": {
        "ja": "パンデミック > 労働混乱 > 供給ストレス > 国家負担",
        "en": "Pandemic > Labor Disruption > Supply Stress > State Burden",
        "th": "โรคระบาด > ความปั่นป่วนด้านแรงงาน > แรงกดดันอุปทาน > ภาระของรัฐ",
    },
    "war > resource drain > fiscal stress > currency weakness": {
        "ja": "戦争 > 資源流出 > 財政ストレス > 通貨弱体化",
        "en": "War > Resource Drain > Fiscal Stress > Currency Weakness",
        "th": "สงคราม > ทรัพยากรถูกดูดออก > แรงกดดันทางการคลัง > ค่าเงินอ่อนตัว",
    },
    "debt bubble > banking stress > credit contraction": {
        "ja": "債務バブル > 銀行ストレス > 信用収縮",
        "en": "Debt Bubble > Banking Stress > Credit Contraction",
        "th": "ฟองสบู่หนี้ > ความตึงเครียดธนาคาร > การหดตัวของเครดิต",
    },
    "currency crisis > capital flight > import shock": {
        "ja": "通貨危機 > 資本流出 > 輸入ショック",
        "en": "Currency Crisis > Capital Flight > Import Shock",
        "th": "วิกฤตค่าเงิน > เงินทุนไหลออก > ช็อกราคานำเข้า",
    },
    "liquidity freeze > market stress > policy backstop": {
        "ja": "流動性凍結 > 市場ストレス > 政策下支え",
        "en": "Liquidity Freeze > Market Stress > Policy Backstop",
        "th": "สภาพคล่องแข็งตัว > ความตึงเครียดตลาด > มาตรการพยุงจากนโยบาย",
    },
    "2008 global financial crisis": {
        "ja": "2008年世界金融危機",
        "en": "2008 Global Financial Crisis",
        "th": "วิกฤตการเงินโลกปี 2008",
    },
}

UI_TERM_MEANINGS = {
    "confidence": {
        "ja": "現在の観測とシナリオ整合性の強さであり、的中率ではない",
        "en": "It measures the strength of alignment between current observation and scenario, not hit rate.",
        "th": "เป็นความแข็งแรงของความสอดคล้องระหว่างการสังเกตปัจจุบันกับ scenario ไม่ใช่อัตราทำนายถูก",
    },
    "dominant_scenario": {
        "ja": "現時点で最も支持が強い主枝であり、唯一の未来ではない",
        "en": "It is the currently strongest branch, not the only possible future.",
        "th": "เป็นแขนงหลักที่ได้รับการสนับสนุนมากที่สุดในขณะนี้ ไม่ใช่อนาคตที่เป็นไปได้เพียงทางเดียว",
    },
    "watchpoints": {
        "ja": "今後シナリオを変えうる監視項目であり、結論そのものではない",
        "en": "They are monitoring points that can change branch balance, not conclusions themselves.",
        "th": "เป็นจุดเฝ้าระวังที่อาจเปลี่ยนสมดุลของแขนง ไม่ใช่ข้อสรุปในตัวมันเอง",
    },
    "monitor": {
        "ja": "watchpoints を item / trigger / meaning に構造化した判断支援フィールド",
        "en": "A decision-support field that structures watchpoints into item / trigger / meaning.",
        "th": "ฟิลด์ช่วยตัดสินใจที่จัดโครงสร้าง watchpoints เป็น item / trigger / meaning",
    },
    "historical": {
        "ja": "過去との比較材料であり、歴史の再演確定を意味しない",
        "en": "Historical comparison material, not proof of exact replay.",
        "th": "เป็นวัสดุเปรียบเทียบทางประวัติศาสตร์ ไม่ได้หมายถึงการเกิดซ้ำแบบเดิมอย่างแน่นอน",
    },
    "interpretation": {
        "ja": "prediction を人間がどう読むべきかを示す中間説明であり、新しい真実ではない",
        "en": "A human-readable reading aid for prediction, not a new layer of truth.",
        "th": "คำอธิบายช่วยอ่าน prediction สำหรับมนุษย์ ไม่ใช่ความจริงชั้นใหม่",
    },
    "decision_line": {
        "ja": "現局面をどう扱うべきかを一行で示す運用的要約であり、命令ではない",
        "en": "An operational one-line summary of how to treat the current phase, not an order.",
        "th": "สรุปเชิงปฏิบัติหนึ่งบรรทัดสำหรับการรับมือกับช่วงปัจจุบัน ไม่ใช่คำสั่ง",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build prediction explanation artifact from prediction-layer outputs."
    )
    parser.add_argument("--prediction", type=Path, default=PREDICTION_PATH)
    parser.add_argument("--scenario", type=Path, default=SCENARIO_PATH)
    parser.add_argument("--signal", type=Path, default=SIGNAL_PATH)
    parser.add_argument("--historical-pattern", type=Path, default=HISTORICAL_PATTERN_PATH)
    parser.add_argument("--historical-analog", type=Path, default=HISTORICAL_ANALOG_PATH)
    parser.add_argument("--reference-memory", type=Path, default=REFERENCE_MEMORY_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--pretty", action="store_true")
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
    return max(0.0, min(1.0, num))


def safe_title(text: Any) -> str | None:
    s = normalize_str(text)
    if not s:
        return None
    return compact_spaces(s.replace("_", " ").replace("-", " "))


def canonical_key(text: str) -> str:
    s = compact_spaces(str(text or ""))
    if not s:
        return ""
    s = s.lower()
    s = s.replace("→", ">")
    s = re.sub(r"\s*>\s*", " > ", s)
    s = s.replace("_", " ")
    s = s.replace("-", " ")
    s = compact_spaces(s)
    return s


def split_arrow_phrase(text: str) -> list[str]:
    normalized = compact_spaces(str(text).replace("→", ">"))
    if ">" not in normalized:
        return [compact_spaces(normalized)]
    return [compact_spaces(part) for part in re.split(r"\s*>\s*", normalized) if compact_spaces(part)]


def translate_key_generic(text: str) -> dict[str, str]:
    raw = compact_spaces(text)
    if not raw:
        return {"ja": "", "en": "", "th": ""}

    key = canonical_key(raw)
    if key in KEY_LABELS:
        return KEY_LABELS[key]

    if ">" in raw or ">" in key:
        parts = split_arrow_phrase(raw)
        translated_parts = [translate_key_generic(part) for part in parts]
        return {
            "ja": " > ".join([p["ja"] for p in translated_parts if p["ja"]]),
            "en": " > ".join([p["en"] for p in translated_parts if p["en"]]),
            "th": " > ".join([p["th"] for p in translated_parts if p["th"]]),
        }

    readable = compact_spaces(raw.replace("_", " ").replace("-", " "))
    return {"ja": readable, "en": readable, "th": readable}


def label_for_scenario(value: str | None) -> dict[str, str]:
    if not value:
        return {"ja": "不明", "en": "unknown", "th": "ไม่ทราบ"}
    return SCENARIO_LABELS.get(value.lower(), {"ja": value, "en": value, "th": value})


def label_for_risk(value: str | None) -> dict[str, str]:
    if not value:
        return RISK_LABELS["unknown"]
    return RISK_LABELS.get(value.lower(), {"ja": value, "en": value, "th": value})


def label_for_confidence_band(value: str) -> dict[str, str]:
    return CONFIDENCE_BAND_LABELS.get(value, CONFIDENCE_BAND_LABELS["unknown"])


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
        pick_first(prediction, "dominant_scenario", "dominantScenario", "scenario", "regime")
    )
    if value:
        return value

    scenario_direct = normalize_str(
        pick_first(scenario, "dominant_scenario", "dominantScenario", "scenario")
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
                or normalize_str(item.get("scenario_id"))
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


def format_confidence_text_i18n(confidence: float | None) -> dict[str, str]:
    text = format_confidence_text(confidence)
    return {"ja": text, "en": text, "th": text}


def normalize_driver_struct(item: Any) -> dict[str, str] | None:
    if item is None:
        return None

    if isinstance(item, str):
        text = safe_title(item)
        if not text:
            return None
        return {"driver": text}

    if isinstance(item, dict):
        driver = (
            normalize_str(item.get("driver"))
            or normalize_str(item.get("name"))
            or normalize_str(item.get("title"))
            or normalize_str(item.get("label"))
            or normalize_str(item.get("signal"))
            or normalize_str(item.get("pattern"))
        )
        if not driver:
            return None
        return {"driver": compact_spaces(driver)}

    text = safe_title(str(item))
    if not text:
        return None
    return {"driver": text}


def extract_drivers(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
    dominant_scenario: str | None,
    confidence: float | None,
    risk_value: str | None,
) -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []

    for raw in normalize_list(pick_first(prediction, "drivers", "key_drivers", default=[])):
        item = normalize_driver_struct(raw)
        if item:
            collected.append(item)

    for raw in normalize_list(pick_first(scenario, "drivers", "key_drivers", default=[]))[:3]:
        item = normalize_driver_struct(raw)
        if item:
            collected.append(item)

    for raw in normalize_list(pick_first(signal, "drivers", "signals", default=[]))[:3]:
        item = normalize_driver_struct(raw)
        if item:
            collected.append(item)

    if dominant_scenario:
        collected.insert(0, {"driver": "dominant scenario alignment"})

    band = confidence_band(confidence)
    if band == "high":
        collected.append({"driver": "confidence support"})
    elif band == "medium":
        collected.append({"driver": "moderate confidence"})
    elif band == "low":
        collected.append({"driver": "fragile confidence"})
    else:
        collected.append({"driver": "limited confidence visibility"})

    collected = dedupe_dict_list(collected, ["driver"])[:6]
    return collected


def normalize_monitor_struct(item: Any) -> dict[str, str] | None:
    if item is None:
        return None

    if isinstance(item, str):
        text = safe_title(item)
        if not text:
            return None
        return {"item": text}

    if isinstance(item, dict):
        monitor_item = (
            normalize_str(item.get("item"))
            or normalize_str(item.get("watchpoint"))
            or normalize_str(item.get("name"))
            or normalize_str(item.get("title"))
            or normalize_str(item.get("label"))
            or normalize_str(item.get("signal"))
        )
        if not monitor_item:
            return None
        return {"item": compact_spaces(monitor_item)}

    text = safe_title(str(item))
    if not text:
        return None
    return {"item": text}


def extract_monitor(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
) -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []

    for raw in normalize_list(pick_first(prediction, "watchpoints", "monitoring_priorities", default=[])):
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
    if isinstance(signal_count, (int, float)) or (isinstance(signal_count, str) and signal_count.strip()):
        collected.append({"item": "signal_count"})

    if not collected:
        collected = [
            {"item": "主要 driver の崩れ"},
            {"item": "悪化側 signal の増加"},
            {"item": "scenario balance の変化"},
        ]

    return dedupe_dict_list(collected, ["item"])[:6]


def extract_watchpoints_from_monitor(monitor: list[dict[str, str]]) -> list[str]:
    return dedupe_keep_order([item["item"] for item in monitor if item.get("item")])[:6]


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

    if not pattern:
        pattern = "historical reference"

    score = clamp_confidence(
        item.get("match_score", item.get("pattern_confidence", item.get("analog_confidence")))
    )

    payload: dict[str, Any] = {"pattern": compact_spaces(pattern)}
    if score is not None:
        payload["confidence"] = score
    return payload


def extract_historical(
    historical_pattern: dict[str, Any] | None,
    historical_analog: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []

    if historical_pattern:
        for raw in normalize_list(pick_first(historical_pattern, "matched_patterns", "patterns", default=[]))[:3]:
            item = normalize_historical_struct(raw)
            if item:
                collected.append(item)

    if historical_analog:
        for raw in normalize_list(pick_first(historical_analog, "top_analogs", "analogs", default=[]))[:3]:
            item = normalize_historical_struct(raw)
            if item:
                collected.append(item)

    return dedupe_dict_list(collected, ["pattern"])[:4]


def normalize_implication_struct(item: Any, fallback_confidence: float | None) -> dict[str, Any] | None:
    if item is None:
        return None

    if isinstance(item, str):
        text = safe_title(item)
        if not text:
            return None
        payload: dict[str, Any] = {"outcome": text}
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
        confidence = clamp_confidence(item.get("confidence", item.get("probability", fallback_confidence)))
        if not outcome:
            return None
        payload = {"outcome": compact_spaces(outcome)}
        if confidence is not None:
            payload["confidence"] = confidence
        return payload

    text = safe_title(str(item))
    if not text:
        return None
    payload = {"outcome": text}
    if fallback_confidence is not None:
        payload["confidence"] = fallback_confidence
    return payload


def extract_implications(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    confidence: float | None,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []

    for raw in normalize_list(pick_first(prediction, "expected_outcomes", "implications", default=[])):
        item = normalize_implication_struct(raw, confidence)
        if item:
            collected.append(item)

    for raw in normalize_list(pick_first(scenario, "expected_outcomes", "implications", default=[]))[:3]:
        item = normalize_implication_struct(raw, confidence)
        if item:
            collected.append(item)

    if not collected and confidence is not None:
        collected.append({"outcome": "scenario persistence", "confidence": confidence})

    return dedupe_dict_list(collected, ["outcome"])[:6]


def extract_risks(
    prediction: dict[str, Any] | None,
    dominant_scenario: str | None,
    confidence: float | None,
    historical: list[dict[str, Any]],
) -> list[str]:
    collected: list[str] = []

    risk_level = normalize_str(
        pick_first(prediction, "overall_risk", "risk_level", "global_risk", "risk")
    )
    if risk_level:
        collected.append("overall_risk_current")

    band = confidence_band(confidence)
    if band == "low":
        collected.append("low_confidence_overread_risk")
    elif band == "medium":
        collected.append("moderate_confidence_overread_risk")

    if dominant_scenario:
        collected.append("dominant_scenario_fixation_risk")

    if historical:
        collected.append("historical_replay_misread_risk")

    return dedupe_keep_order(collected)[:6]


def extract_invalidation(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    dominant_scenario: str | None,
) -> list[str]:
    collected: list[str] = []

    raw_pred = to_text_list(
        pick_first(
            prediction,
            "invalidation",
            "invalidators",
            "invalidation_conditions",
            default=[],
        )
    )
    raw_scn = to_text_list(
        pick_first(
            scenario,
            "invalidation",
            "invalidators",
            "invalidation_conditions",
            default=[],
        )
    )

    if dominant_scenario:
        collected.append("dominant_scenario_change")

    if raw_pred or raw_scn:
        collected.append("custom_invalidation_present")
    else:
        collected.extend([
            "confidence_large_drop",
            "multiple_watchpoints_deteriorate",
        ])

    return dedupe_keep_order(collected)[:6]


def driver_text_triplet_i18n(
    driver_key: str,
    dominant_scenario: str | None,
    confidence: float | None,
    risk_value: str | None,
) -> dict[str, dict[str, str]]:
    label = translate_key_generic(driver_key)
    scenario = label_for_scenario(dominant_scenario)
    risk = label_for_risk(risk_value)
    band = confidence_band(confidence)
    band_label = label_for_confidence_band(band)

    lowered = canonical_key(driver_key)

    if lowered == "dominant scenario alignment":
        return {
            "ja": {
                "driver": label["ja"],
                "why": sentence_lang(
                    f"現時点では {scenario['ja']} が主枝として最も整合的に支持されており、説明全体の重心はこの主枝に従っている", "ja"
                ),
                "impact": sentence_lang(
                    "主枝が変化すると summary / monitor / implications の意味づけもまとめて見直し対象になる", "ja"
                ),
            },
            "en": {
                "driver": label["en"],
                "why": sentence_lang(
                    f"The current center of gravity is aligned with {scenario['en']}, so the explanation is anchored to that branch", "en"
                ),
                "impact": sentence_lang(
                    "If the dominant branch changes, the meaning of summary / monitor / implications changes with it", "en"
                ),
            },
            "th": {
                "driver": label["th"],
                "why": sentence_lang(
                    f"ขณะนี้ {scenario['th']} ได้รับการสนับสนุนอย่างสอดคล้องมากที่สุด จึงเป็นแกนหลักของคำอธิบายทั้งหมด", "th"
                ),
                "impact": sentence_lang(
                    "หากแขนงหลักเปลี่ยน ความหมายของ summary / monitor / implications ก็ต้องถูกทบทวนพร้อมกัน", "th"
                ),
            },
        }

    if lowered == "confidence support":
        return {
            "ja": {
                "driver": label["ja"],
                "why": sentence_lang(
                    f"confidence は {band_label['ja']} で、主枝を支える材料が比較的そろっている", "ja"
                ),
                "impact": sentence_lang(
                    "短期的には現行シナリオが維持されやすいが、watchpoints を無視してよい意味ではない", "ja"
                ),
            },
            "en": {
                "driver": label["en"],
                "why": sentence_lang(
                    f"Confidence is {band_label['en']}, so the current branch has relatively solid support", "en"
                ),
                "impact": sentence_lang(
                    "That supports short-term persistence, but it does not justify ignoring watchpoints", "en"
                ),
            },
            "th": {
                "driver": label["th"],
                "why": sentence_lang(
                    f"confidence อยู่ในระดับ {band_label['th']} จึงมีแรงสนับสนุนต่อแขนงปัจจุบันค่อนข้างพอสมควร", "th"
                ),
                "impact": sentence_lang(
                    "สิ่งนี้ช่วยให้แขนงปัจจุบันคงอยู่ในระยะสั้นได้ง่ายขึ้น แต่ไม่ได้แปลว่าสามารถละเลย watchpoints ได้", "th"
                ),
            },
        }

    if lowered == "moderate confidence":
        return {
            "ja": {
                "driver": label["ja"],
                "why": sentence_lang(
                    "confidence は中程度で、主枝は保たれているが強い断定に使えるほどではない", "ja"
                ),
                "impact": sentence_lang(
                    "追加の変化が入ると主枝再評価が起こりうるため、安定を確実性と誤読してはならない", "ja"
                ),
            },
            "en": {
                "driver": label["en"],
                "why": sentence_lang(
                    "Confidence is moderate: the branch is intact, but not strong enough for hard certainty", "en"
                ),
                "impact": sentence_lang(
                    "Additional change can trigger reassessment, so stability should not be misread as certainty", "en"
                ),
            },
            "th": {
                "driver": label["th"],
                "why": sentence_lang(
                    "confidence อยู่ในระดับปานกลาง หมายถึงแขนงยังไม่พัง แต่ยังไม่แข็งแรงพอสำหรับข้อสรุปแบบหนักแน่น", "th"
                ),
                "impact": sentence_lang(
                    "หากมีการเปลี่ยนแปลงเพิ่ม อาจเกิดการประเมินแขนงใหม่ได้ จึงไม่ควรตีความเสถียรภาพว่าเป็นความแน่นอน", "th"
                ),
            },
        }

    if lowered == "fragile confidence":
        return {
            "ja": {
                "driver": label["ja"],
                "why": sentence_lang(
                    "confidence は低めで、主枝は暫定仮説として扱うべきである", "ja"
                ),
                "impact": sentence_lang(
                    "小さな環境変化でも重心が動きやすいため、結論固定より経過観察を優先すべきである", "ja"
                ),
            },
            "en": {
                "driver": label["en"],
                "why": sentence_lang(
                    "Confidence is fragile, so the current branch should be treated as provisional", "en"
                ),
                "impact": sentence_lang(
                    "Even small environmental changes can move the balance, so process monitoring matters more than fixed conclusions", "en"
                ),
            },
            "th": {
                "driver": label["th"],
                "why": sentence_lang(
                    "confidence ค่อนข้างเปราะบาง จึงควรมองแขนงปัจจุบันว่าเป็นสมมติฐานชั่วคราว", "th"
                ),
                "impact": sentence_lang(
                    "การเปลี่ยนแปลงเล็กน้อยก็อาจขยับสมดุลได้ ดังนั้นควรให้น้ำหนักกับการติดตามต่อมากกว่าการยึดข้อสรุปตายตัว", "th"
                ),
            },
        }

    if lowered == "limited confidence visibility":
        return {
            "ja": {
                "driver": label["ja"],
                "why": sentence_lang(
                    "confidence 情報が十分でないため、主枝の強さを過大評価すべきではない", "ja"
                ),
                "impact": sentence_lang(
                    "判断時には invalidation と watchpoints をより重視する必要がある", "ja"
                ),
            },
            "en": {
                "driver": label["en"],
                "why": sentence_lang(
                    "Confidence visibility is limited, so branch strength should not be overstated", "en"
                ),
                "impact": sentence_lang(
                    "That makes invalidation and watchpoints more important in the current read", "en"
                ),
            },
            "th": {
                "driver": label["th"],
                "why": sentence_lang(
                    "ข้อมูล confidence มีจำกัด จึงไม่ควรประเมินความแข็งแรงของแขนงหลักสูงเกินจริง", "th"
                ),
                "impact": sentence_lang(
                    "ทำให้ invalidation และ watchpoints มีความสำคัญมากขึ้นในการอ่านสถานะปัจจุบัน", "th"
                ),
            },
        }

    return {
        "ja": {
            "driver": label["ja"],
            "why": sentence_lang(
                f"{label['ja']} は現在の {scenario['ja']} と整合する主要材料の一つであり、局面の重心を支えている", "ja"
            ),
            "impact": sentence_lang(
                f"{label['ja']} が崩れると {risk['ja']} 局面は一段不安定に読まれやすくなる", "ja"
            ),
        },
        "en": {
            "driver": label["en"],
            "why": sentence_lang(
                f"{label['en']} is one of the main factors supporting the current {scenario['en']} branch", "en"
            ),
            "impact": sentence_lang(
                f"If {label['en']} weakens, the current {risk['en']} phase becomes easier to read as unstable", "en"
            ),
        },
        "th": {
            "driver": label["th"],
            "why": sentence_lang(
                f"{label['th']} เป็นหนึ่งในปัจจัยหลักที่ช่วยพยุงแขนง {scenario['th']} ในปัจจุบัน", "th"
            ),
            "impact": sentence_lang(
                f"หาก {label['th']} อ่อนลง ภาวะความเสี่ยงแบบ {risk['th']} จะถูกอ่านว่าไม่มั่นคงมากขึ้น", "th"
            ),
        },
    }


def monitor_text_triplet_i18n(
    item_key: str,
    dominant_scenario: str | None,
) -> dict[str, dict[str, str]]:
    label = translate_key_generic(item_key)
    scenario = label_for_scenario(dominant_scenario)

    return {
        "ja": {
            "item": label["ja"],
            "trigger": sentence_lang("方向感が明確に変化・加速・悪化した場合", "ja"),
            "meaning": sentence_lang(
                f"{label['ja']} は {scenario['ja']} が維持されるのか、見直しへ向かうのかを判定するための分岐トリガーである", "ja"
            ),
        },
        "en": {
            "item": label["en"],
            "trigger": sentence_lang("When direction clearly changes, accelerates, or deteriorates", "en"),
            "meaning": sentence_lang(
                f"{label['en']} is a branch trigger used to judge whether {scenario['en']} remains valid or needs reassessment", "en"
            ),
        },
        "th": {
            "item": label["th"],
            "trigger": sentence_lang("เมื่อทิศทางเปลี่ยน เร่งตัว หรือแย่ลงอย่างชัดเจน", "th"),
            "meaning": sentence_lang(
                f"{label['th']} เป็นตัวกระตุ้นการแตกแขนงที่ใช้ตัดสินว่า {scenario['th']} ยังใช้ได้หรือควรถูกประเมินใหม่", "th"
            ),
        },
    }


def historical_row_i18n(item: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pattern_label = translate_key_generic(str(item.get("pattern", "")))
    confidence = clamp_confidence(item.get("confidence"))
    conf_text = format_confidence_text(confidence)

    return {
        "ja": {
            "pattern": pattern_label["ja"],
            "similarity": sentence_lang(
                f"{pattern_label['ja']} は現在の圧力配置と部分的に似た比較対象として扱われる", "ja"
            ),
            "difference": sentence_lang(
                "これは再演予言ではなく、現在の脆さと政策余地を測るための比較材料である", "ja"
            ),
            **({"confidence": confidence, "confidence_text": conf_text} if confidence is not None else {}),
        },
        "en": {
            "pattern": pattern_label["en"],
            "similarity": sentence_lang(
                f"{pattern_label['en']} is used as a partial comparison for the current pressure mix", "en"
            ),
            "difference": sentence_lang(
                "This is comparison material, not a claim of exact historical replay", "en"
            ),
            **({"confidence": confidence, "confidence_text": conf_text} if confidence is not None else {}),
        },
        "th": {
            "pattern": pattern_label["th"],
            "similarity": sentence_lang(
                f"{pattern_label['th']} ถูกใช้เป็นตัวเปรียบเทียบบางส่วนกับแรงกดดันในปัจจุบัน", "th"
            ),
            "difference": sentence_lang(
                "นี่คือวัสดุเปรียบเทียบ ไม่ใช่การยืนยันว่าจะเกิดซ้ำทางประวัติศาสตร์แบบตรงตัว", "th"
            ),
            **({"confidence": confidence, "confidence_text": conf_text} if confidence is not None else {}),
        },
    }


def implication_row_i18n(
    item: dict[str, Any],
    dominant_scenario: str | None,
) -> dict[str, dict[str, Any]]:
    outcome_label = translate_key_generic(str(item.get("outcome", "")))
    confidence = clamp_confidence(item.get("confidence"))
    conf_text = format_confidence_text(confidence)
    scenario = label_for_scenario(dominant_scenario)

    return {
        "ja": {
            "outcome": outcome_label["ja"],
            "path": sentence_lang(
                f"{scenario['ja']} が続く場合、{outcome_label['ja']} は下流で起こりやすい派生結果として読むべきである", "ja"
            ),
            **({"confidence": confidence, "confidence_text": conf_text} if confidence is not None else {}),
        },
        "en": {
            "outcome": outcome_label["en"],
            "path": sentence_lang(
                f"If {scenario['en']} persists, {outcome_label['en']} becomes a more plausible downstream outcome", "en"
            ),
            **({"confidence": confidence, "confidence_text": conf_text} if confidence is not None else {}),
        },
        "th": {
            "outcome": outcome_label["th"],
            "path": sentence_lang(
                f"หาก {scenario['th']} ดำเนินต่อไป {outcome_label['th']} จะมีความเป็นไปได้มากขึ้นในฐานะผลลัพธ์ปลายน้ำ", "th"
            ),
            **({"confidence": confidence, "confidence_text": conf_text} if confidence is not None else {}),
        },
    }


def risks_i18n_from_context(
    risk_value: str | None,
    dominant_scenario: str | None,
    confidence: float | None,
    historical: list[dict[str, Any]],
) -> dict[str, list[str]]:
    out = {"ja": [], "en": [], "th": []}
    risk = label_for_risk(risk_value)
    scenario = label_for_scenario(dominant_scenario)
    band = confidence_band(confidence)

    if risk_value:
        out["ja"].append(sentence_lang(f"overall_risk は現在 {risk['ja']} である", "ja"))
        out["en"].append(sentence_lang(f"overall_risk is currently {risk['en']}", "en"))
        out["th"].append(sentence_lang(f"overall_risk อยู่ในระดับ {risk['th']} ในขณะนี้", "th"))

    if band == "low":
        out["ja"].append(sentence_lang("confidence が低いため、現行主枝への過信は危険である", "ja"))
        out["en"].append(sentence_lang("Confidence is low, so over-reading the current branch is dangerous", "en"))
        out["th"].append(sentence_lang("confidence ต่ำ จึงอันตรายหากอ่านแขนงปัจจุบันอย่างมั่นใจเกินไป", "th"))
    elif band == "medium":
        out["ja"].append(sentence_lang("confidence は中程度であり、単線的な断定判断は危険である", "ja"))
        out["en"].append(sentence_lang("Confidence is moderate, so linear certainty is still risky", "en"))
        out["th"].append(sentence_lang("confidence อยู่ในระดับปานกลาง จึงยังเสี่ยงหากตัดสินแบบเส้นตรงเกินไป", "th"))

    if dominant_scenario:
        out["ja"].append(sentence_lang(f"{scenario['ja']} の固定視は危険である", "ja"))
        out["en"].append(sentence_lang(f"Fixating on {scenario['en']} as permanent is risky", "en"))
        out["th"].append(sentence_lang(f"การยึด {scenario['th']} ว่าจะคงอยู่ถาวรเป็นความเสี่ยง", "th"))

    if historical:
        pattern_label = translate_key_generic(str(historical[0].get("pattern", "")))
        out["ja"].append(sentence_lang(f"{pattern_label['ja']} を単純再現と誤解するのは危険である", "ja"))
        out["en"].append(sentence_lang(f"It is risky to misread {pattern_label['en']} as an exact replay", "en"))
        out["th"].append(sentence_lang(f"การอ่าน {pattern_label['th']} ว่าเป็นการเกิดซ้ำแบบตรงตัวเป็นความเสี่ยง", "th"))

    return out


def invalidation_i18n_from_context(
    dominant_scenario: str | None,
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
) -> dict[str, list[str]]:
    out = {"ja": [], "en": [], "th": []}
    scenario_label = label_for_scenario(dominant_scenario)

    if dominant_scenario:
        out["ja"].append(sentence_lang(f"{scenario_label['ja']} から主枝が変化した場合", "ja"))
        out["en"].append(sentence_lang(f"When the dominant branch changes away from {scenario_label['en']}", "en"))
        out["th"].append(sentence_lang(f"เมื่อแขนงหลักเปลี่ยนออกจาก {scenario_label['th']}", "th"))

    raw_pred = to_text_list(
        pick_first(prediction, "invalidation", "invalidators", "invalidation_conditions", default=[])
    )
    raw_scn = to_text_list(
        pick_first(scenario, "invalidation", "invalidators", "invalidation_conditions", default=[])
    )
    if raw_pred or raw_scn:
        out["ja"].append(sentence_lang("既存の invalidation 条件に抵触した場合", "ja"))
        out["en"].append(sentence_lang("When an existing invalidation condition is triggered", "en"))
        out["th"].append(sentence_lang("เมื่อเข้าเงื่อนไข invalidation ที่มีอยู่เดิม", "th"))
    else:
        out["ja"].append(sentence_lang("confidence が大きく低下した場合", "ja"))
        out["en"].append(sentence_lang("When confidence drops materially", "en"))
        out["th"].append(sentence_lang("เมื่อ confidence ลดลงอย่างมีนัยสำคัญ", "th"))

        out["ja"].append(sentence_lang("watchpoints の複数が同時に悪化した場合", "ja"))
        out["en"].append(sentence_lang("When multiple watchpoints deteriorate at the same time", "en"))
        out["th"].append(sentence_lang("เมื่อ watchpoints หลายรายการแย่ลงพร้อมกัน", "th"))

    return out


def must_not_mean_i18n() -> dict[str, list[str]]:
    return {
        "ja": [
            "prediction は確定未来ではない",
            "confidence は的中率ではない",
            "watchpoints は発生確定イベントではない",
            "historical は歴史の再演確定を意味しない",
            "decision_line は投資助言や命令ではない",
            "interpretation は UI の感想ではなく analysis artifact の説明である",
        ],
        "en": [
            "prediction is not a guaranteed future",
            "confidence is not hit rate",
            "watchpoints are not confirmed events",
            "historical does not mean an exact replay of history",
            "decision_line is not investment advice or an order",
            "interpretation is an analysis-side explanation, not a UI opinion",
        ],
        "th": [
            "prediction ไม่ใช่อนาคตที่แน่นอน",
            "confidence ไม่ใช่อัตราทำนายถูก",
            "watchpoints ไม่ใช่เหตุการณ์ที่ยืนยันแล้ว",
            "historical ไม่ได้หมายถึงการเกิดซ้ำของประวัติศาสตร์แบบตรงตัว",
            "decision_line ไม่ใช่คำแนะนำการลงทุนหรือคำสั่ง",
            "interpretation เป็นคำอธิบายจากฝั่ง analysis ไม่ใช่ความเห็นของ UI",
        ],
    }


def ui_terms_with_i18n(terms: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in terms:
        term = str(item.get("term", "")).strip()
        row = dict(item)
        row["meaning_i18n"] = UI_TERM_MEANINGS.get(
            term,
            {
                "ja": str(item.get("meaning", "")),
                "en": str(item.get("meaning", "")),
                "th": str(item.get("meaning", "")),
            },
        )
        out.append(row)
    return out


def i18n_for_headline(
    dominant_scenario: str | None,
    watchpoints: list[str],
    confidence: float | None,
) -> dict[str, str]:
    scenario = label_for_scenario(dominant_scenario)
    band = confidence_band(confidence)

    if (dominant_scenario or "").lower() == "base_case":
        if watchpoints:
            return {
                "ja": f"現在は {scenario['ja']} 優勢だが、警戒すべき watchpoints が残る",
                "en": f"{scenario['en']} remains dominant for now, but important watchpoints remain active",
                "th": f"ขณะนี้ {scenario['th']} ยังเป็นแกนหลัก แต่ยังมี watchpoints สำคัญที่ต้องเฝ้าระวัง",
            }
        return {
            "ja": f"現在は {scenario['ja']} 優勢で、主枝は比較的安定している",
            "en": f"{scenario['en']} remains dominant and the main branch is relatively stable",
            "th": f"ขณะนี้ {scenario['th']} ยังเป็นแกนหลัก และแขนงหลักค่อนข้างทรงตัว",
        }

    if (dominant_scenario or "").lower() == "worst_case":
        return {
            "ja": "現在は worst_case 側の圧力が強く、悪化分岐への警戒が必要",
            "en": "Pressure is leaning toward worst_case, so deterioration branches require close attention",
            "th": "แรงกดดันกำลังเอนเอียงไปทาง worst_case จึงต้องเฝ้าระวังแขนงการเสื่อมลงอย่างใกล้ชิด",
        }

    if (dominant_scenario or "").lower() == "best_case":
        return {
            "ja": "現在は best_case 側が主枝だが、過度な楽観は避けるべき状態",
            "en": "The best_case branch is visible, but excessive optimism is still unwarranted",
            "th": "แม้จะเห็นแขนง best_case แต่ยังไม่ควรมองโลกในแง่ดีเกินไป",
        }

    if band == "low":
        return {
            "ja": f"現在の主枝は {scenario['ja']} だが、confidence が低く再評価余地が大きい",
            "en": f"The current main branch is {scenario['en']}, but confidence is low and reassessment risk remains large",
            "th": f"แขนงหลักปัจจุบันคือ {scenario['th']} แต่ confidence ต่ำและยังมีโอกาสต้องประเมินใหม่สูง",
        }

    return {
        "ja": f"現在の主枝は {scenario['ja']} で、追加の監視を要する状態",
        "en": f"The current main branch is {scenario['en']}, and additional monitoring is required",
        "th": f"แขนงหลักปัจจุบันคือ {scenario['th']} และยังต้องติดตามเพิ่มเติม",
    }


def i18n_for_decision_line(
    dominant_scenario: str | None,
    risk_value: str | None,
    confidence: float | None,
) -> dict[str, str]:
    dominant = (dominant_scenario or "").lower()
    risk_text = (risk_value or "").lower()

    if dominant == "worst_case" or "critical" in risk_text or "high" in risk_text:
        return {
            "ja": "防御寄りの姿勢を強く維持すべき局面であり、積極拡大型の行動はまだ正当化されない。",
            "en": "Defensive bias should remain strong. Aggressive expansion is not yet justified.",
            "th": "ควรรักษาอคติเชิงป้องกันอย่างเข้มแข็ง และยังไม่เหมาะกับการขยายเชิงรุก",
        }

    if dominant == "base_case" and confidence_band(confidence) == "high":
        return {
            "ja": "base_case が主枝として維持されている。規律は保つべきだが、安定を確実性と誤解してはならない。",
            "en": "Base-case remains the main branch. Maintain discipline, but do not mistake stability for certainty.",
            "th": "base_case ยังเป็นแขนงหลัก ควรรักษาวินัย แต่ไม่ควรตีความเสถียรภาพว่าเป็นความแน่นอน",
        }

    if dominant == "base_case":
        return {
            "ja": "慎重な姿勢を維持し、一時的な安定を全面安全と誤読しないこと。",
            "en": "Maintain guarded positioning. Do not mistake temporary stability for full safety.",
            "th": "คงท่าทีระมัดระวังไว้ และอย่าตีความเสถียรภาพชั่วคราวว่าเป็นความปลอดภัยเต็มรูปแบบ",
        }

    if dominant == "best_case":
        return {
            "ja": "前向きな分岐は見えるが、全面的な risk-on 行動よりも節度ある楽観に留めるべき局面である。",
            "en": "Positive branch is visible, but the system still calls for measured optimism rather than full risk-on behavior.",
            "th": "แม้จะเห็นแขนงเชิงบวก แต่ควรรักษาความมองบวกอย่างมีวินัยมากกว่าการเปิดรับความเสี่ยงเต็มรูปแบบ",
        }

    return {
        "ja": "現時点では慎重さを残しつつ柔軟に構えるべきであり、より大きな方向判断は branch 変化確認後に行うべきである。",
        "en": "Current read supports caution with flexibility. Watch for branch change before making larger directional commitments.",
        "th": "ภาพอ่านปัจจุบันสนับสนุนความระมัดระวังแบบยืดหยุ่น และควรรอการเปลี่ยน branch ก่อนตัดสินใจเชิงทิศทางที่ใหญ่ขึ้น",
    }


def i18n_for_summary(
    dominant_scenario: str | None,
    confidence: float | None,
    watchpoints: list[str],
    risk_value: str | None,
    historical: list[dict[str, Any]],
) -> dict[str, str]:
    scenario = label_for_scenario(dominant_scenario)
    risk = label_for_risk(risk_value)
    conf = format_confidence_text(confidence)
    first_watch = translate_key_generic(watchpoints[0]) if watchpoints else {
        "ja": "主要 watchpoint",
        "en": "key watchpoint",
        "th": "watchpoint หลัก",
    }
    pattern_ja = translate_key_generic(str(historical[0].get("pattern")))["ja"] if historical else "履歴参照なし"
    pattern_en = translate_key_generic(str(historical[0].get("pattern")))["en"] if historical else "no historical reference"
    pattern_th = translate_key_generic(str(historical[0].get("pattern")))["th"] if historical else "ไม่มีการอ้างอิงทางประวัติศาสตร์"

    return {
        "ja": sentence(
            f"Prediction は {scenario['ja']} 優勢で、overall_risk は {risk['ja']}。"
            f" Confidence は {conf}。"
            f" 次に確認すべき焦点は {first_watch['ja']} である。"
            f" 歴史参照の中心は {pattern_ja} である"
        ),
        "en": sentence_lang(
            f"Prediction is centered on {scenario['en']}, with overall_risk at {risk['en']}. "
            f"Confidence is {conf}. "
            f"The next focal point is {first_watch['en']}. "
            f"The main historical reference is {pattern_en}",
            "en",
        ),
        "th": sentence_lang(
            f"Prediction มีศูนย์กลางอยู่ที่ {scenario['th']} โดย overall_risk อยู่ในระดับ {risk['th']}. "
            f"Confidence อยู่ที่ {conf}. "
            f"จุดถัดไปที่ต้องติดตามคือ {first_watch['th']}. "
            f"บริบทประวัติศาสตร์หลักคือ {pattern_th}",
            "th",
        ),
    }


def i18n_for_interpretation(
    dominant_scenario: str | None,
    confidence: float | None,
    risk_value: str | None,
    drivers: list[dict[str, str]],
    monitor: list[dict[str, str]],
) -> dict[str, str]:
    scenario = label_for_scenario(dominant_scenario)
    risk = label_for_risk(risk_value)
    band = confidence_band(confidence)
    first_driver = translate_key_generic(drivers[0]["driver"]) if drivers else {
        "ja": "主要 driver",
        "en": "main driver",
        "th": "driver หลัก",
    }
    first_monitor = translate_key_generic(monitor[0]["item"]) if monitor else {
        "ja": "主要 monitor",
        "en": "main monitor",
        "th": "monitor หลัก",
    }

    if band == "high":
        return {
            "ja": sentence(
                f"これは {scenario['ja']} がかなり強く支持されている局面として読める。"
                f" ただし {risk['ja']} リスクが残る以上、{first_driver['ja']} と {first_monitor['ja']} の確認が必要である"
            ),
            "en": sentence_lang(
                f"This can be read as a phase where {scenario['en']} is strongly supported. "
                f"Even so, as long as {risk['en']} risk remains, {first_driver['en']} and {first_monitor['en']} still need close confirmation",
                "en",
            ),
            "th": sentence_lang(
                f"นี่เป็นช่วงที่ {scenario['th']} ได้รับการสนับสนุนค่อนข้างแรง "
                f"อย่างไรก็ดี ตราบใดที่ความเสี่ยง {risk['th']} ยังอยู่ ยังต้องติดตาม {first_driver['th']} และ {first_monitor['th']} อย่างใกล้ชิด",
                "th",
            ),
        }

    if band == "medium":
        return {
            "ja": sentence(
                f"これは『崩れてはいないが、安心して拡大へ踏み出せるほどでもない』中間局面として読むのが近い。"
                f" 現在の主枝 {scenario['ja']} は一定の整合を持つが、{first_driver['ja']} と {first_monitor['ja']} を失えば重心はすぐに動きうる"
            ),
            "en": sentence_lang(
                f"This reads like an intermediate phase: not broken, but not safe enough for confident expansion. "
                f"The current main branch {scenario['en']} has some alignment, but the center of gravity can shift quickly if {first_driver['en']} or {first_monitor['en']} weakens",
                "en",
            ),
            "th": sentence_lang(
                f"นี่ใกล้เคียงกับช่วงกลาง: ยังไม่พัง แต่ยังไม่ปลอดภัยพอสำหรับการขยายตัวอย่างมั่นใจ "
                f"แขนงหลักปัจจุบัน {scenario['th']} มีความสอดคล้องอยู่บ้าง แต่จุดศูนย์กลางสามารถเปลี่ยนได้เร็วหาก {first_driver['th']} หรือ {first_monitor['th']} อ่อนลง",
                "th",
            ),
        }

    if band == "low":
        return {
            "ja": sentence(
                f"これは主枝 {scenario['ja']} が仮置きされている段階に近く、見立ての安定性はまだ弱い。"
                f" 結論より過程を重視し、{first_driver['ja']} と {first_monitor['ja']} の変化を優先して追うべきである"
            ),
            "en": sentence_lang(
                f"This is closer to a provisional phase where {scenario['en']} is only tentatively centered and stability remains weak. "
                f"The process matters more than the conclusion, and changes in {first_driver['en']} and {first_monitor['en']} should be tracked first",
                "en",
            ),
            "th": sentence_lang(
                f"นี่ใกล้เคียงกับช่วงชั่วคราวที่ {scenario['th']} ยังเป็นเพียงศูนย์กลางแบบไม่มั่นคง "
                f"ควรให้น้ำหนักกับกระบวนการมากกว่าข้อสรุป และติดตามการเปลี่ยนแปลงของ {first_driver['th']} กับ {first_monitor['th']} ก่อน",
                "th",
            ),
        }

    return {
        "ja": "これは現時点で最も整合的な仮説を示しているが、強い断定よりも経過観察を前提に読むべき局面である。",
        "en": "This shows the most coherent current hypothesis, but it should be read as an observation-led phase rather than a strong conclusion.",
        "th": "นี่แสดงสมมติฐานที่สอดคล้องที่สุดในปัจจุบัน แต่ควรอ่านในฐานะช่วงที่ต้องติดตามต่อ มากกว่าข้อสรุปที่หนักแน่น",
    }


def i18n_for_why_it_matters(
    dominant_scenario: str | None,
    confidence: float | None,
    risk_value: str | None,
) -> dict[str, str]:
    scenario = label_for_scenario(dominant_scenario)
    risk = label_for_risk(risk_value)
    band = confidence_band(confidence)

    if band == "high":
        return {
            "ja": sentence(
                f"{scenario['ja']} を断定未来として誤読せず、強い整合がどの条件で維持されるかを把握するために重要である。"
                f" 特に {risk['ja']} が残る限り、高 confidence でも過信防止が必要になる"
            ),
            "en": sentence_lang(
                f"This matters because {scenario['en']} should not be misread as a guaranteed future. "
                f"As long as {risk['en']} remains, even high confidence still requires overconfidence control",
                "en",
            ),
            "th": sentence_lang(
                f"สิ่งนี้สำคัญเพราะไม่ควรอ่าน {scenario['th']} ว่าเป็นอนาคตที่แน่นอน "
                f"ตราบใดที่ความเสี่ยง {risk['th']} ยังอยู่ แม้ confidence สูงก็ยังต้องป้องกันการมั่นใจเกินไป",
                "th",
            ),
        }

    if band == "medium":
        return {
            "ja": sentence(
                f"{scenario['ja']} と confidence を『そこそこ有力だが未確定』な読みとして扱い、"
                "次に何を見れば判断が一段深まるかを明確にするために重要である"
            ),
            "en": sentence_lang(
                f"This matters because {scenario['en']} and confidence should be read as fairly strong but still not final, "
                "and the next observation points need to be explicit",
                "en",
            ),
            "th": sentence_lang(
                f"สิ่งนี้สำคัญเพราะ {scenario['th']} และ confidence ควรถูกอ่านว่าแข็งแรงพอสมควรแต่ยังไม่สิ้นสุด "
                "และจำเป็นต้องทำให้ชัดว่าอะไรคือจุดสังเกตถัดไป",
                "th",
            ),
        }

    return {
        "ja": sentence(
            f"{scenario['ja']} が暫定主枝にすぎないことを明確にし、"
            "過度な楽観や悲観を避けながら watchpoints を監視するために重要である"
        ),
        "en": sentence_lang(
            f"This matters because {scenario['en']} is only a provisional main branch, "
            "and watchpoints must be monitored without falling into premature optimism or pessimism",
            "en",
        ),
        "th": sentence_lang(
            f"สิ่งนี้สำคัญเพราะ {scenario['th']} เป็นเพียงแขนงหลักชั่วคราว "
            "และต้องเฝ้าดู watchpoints โดยไม่เอนเอียงไปทางมองบวกหรือลบเร็วเกินไป",
            "th",
        ),
    }


def i18n_for_narrative_flow(
    headline_i18n: dict[str, str],
    summary_i18n: dict[str, str],
    interpretation_i18n: dict[str, str],
    decision_line_i18n: dict[str, str],
) -> dict[str, list[str]]:
    return {
        "ja": [
            sentence(headline_i18n["ja"]),
            sentence(summary_i18n["ja"]),
            sentence(interpretation_i18n["ja"]),
            sentence(decision_line_i18n["ja"]),
        ],
        "en": [
            sentence_lang(headline_i18n["en"], "en"),
            sentence_lang(summary_i18n["en"], "en"),
            sentence_lang(interpretation_i18n["en"], "en"),
            sentence_lang(decision_line_i18n["en"], "en"),
        ],
        "th": [
            sentence_lang(headline_i18n["th"], "th"),
            sentence_lang(summary_i18n["th"], "th"),
            sentence_lang(interpretation_i18n["th"], "th"),
            sentence_lang(decision_line_i18n["th"], "th"),
        ],
    }


def build_ui_terms() -> list[dict[str, str]]:
    return [
        {"term": "confidence", "meaning": "現在の観測とシナリオ整合性の強さであり、的中率ではない"},
        {"term": "dominant_scenario", "meaning": "現時点で最も支持が強い主枝であり、唯一の未来ではない"},
        {"term": "watchpoints", "meaning": "今後シナリオを変えうる監視項目であり、結論そのものではない"},
        {"term": "monitor", "meaning": "watchpoints を item / trigger / meaning に構造化した判断支援フィールド"},
        {"term": "historical", "meaning": "過去との比較材料であり、歴史の再演確定を意味しない"},
        {"term": "interpretation", "meaning": "prediction を人間がどう読むべきかを示す中間説明であり、新しい真実ではない"},
        {"term": "decision_line", "meaning": "現局面をどう扱うべきかを一行で示す運用的要約であり、命令ではない"},
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

    headline_i18n = {
        "ja": "prediction explanation unavailable",
        "en": "prediction explanation unavailable",
        "th": "prediction explanation unavailable",
    }
    decision_line_i18n = {
        "ja": "Explanation unavailable. Do not infer structured meaning from missing artifacts.",
        "en": "Explanation unavailable. Do not infer structured meaning from missing artifacts.",
        "th": "Explanation unavailable. Do not infer structured meaning from missing artifacts.",
    }
    summary_i18n = {
        "ja": "必要な prediction-layer artifact が不足しているため、構造化 explanation を生成できなかった。",
        "en": "Structured explanation could not be generated because required prediction-layer artifacts are missing.",
        "th": "ไม่สามารถสร้าง structured explanation ได้ เนื่องจาก prediction-layer artifacts ที่จำเป็นขาดหายไป",
    }
    interpretation_i18n = {
        "ja": "UI が explanation を捏造せず、欠損を正直に表示するため、ここでは unavailable を返す。",
        "en": "UI must not fabricate explanations, so unavailable is returned honestly here.",
        "th": "UI ต้องไม่แต่งคำอธิบายขึ้นเอง จึงส่งคืนสถานะ unavailable อย่างตรงไปตรงมา",
    }
    why_i18n = {
        "ja": "UI が explanation を捏造せず、欠損を正直に表示するため。",
        "en": "So that UI does not fabricate explanations and shows missing state honestly.",
        "th": "เพื่อให้ UI ไม่แต่งคำอธิบายขึ้นเอง และแสดงสถานะขาดหายอย่างตรงไปตรงมา",
    }
    narrative_flow_i18n = i18n_for_narrative_flow(
        headline_i18n,
        summary_i18n,
        interpretation_i18n,
        decision_line_i18n,
    )

    artifact: dict[str, Any] = {
        "as_of": None,
        "subject": "prediction",
        "status": "unavailable",
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "headline": headline_i18n["ja"],
        "headline_i18n": headline_i18n,
        "decision_line": decision_line_i18n["ja"],
        "decision_line_i18n": decision_line_i18n,
        "summary": summary_i18n["ja"],
        "summary_i18n": summary_i18n,
        "interpretation": interpretation_i18n["ja"],
        "interpretation_i18n": interpretation_i18n,
        "why_it_matters": why_i18n["ja"],
        "why_it_matters_i18n": why_i18n,
        "narrative_flow": narrative_flow_i18n["ja"],
        "narrative_flow_i18n": narrative_flow_i18n,
        "based_on": [str(prediction_path), str(scenario_path), str(signal_path)],
        "drivers": [],
        "drivers_i18n": {"ja": [], "en": [], "th": []},
        "monitor": [],
        "monitor_i18n": {"ja": [], "en": [], "th": []},
        "watchpoints": [],
        "watchpoints_i18n": {"ja": [], "en": [], "th": []},
        "historical": [],
        "historical_i18n": {"ja": [], "en": [], "th": []},
        "implications": [],
        "implications_i18n": {"ja": [], "en": [], "th": []},
        "risks": [],
        "risks_i18n": {"ja": [], "en": [], "th": []},
        "invalidation": [],
        "invalidation_i18n": {"ja": [], "en": [], "th": []},
        "must_not_mean": [
            "unavailable は安全を意味しない",
            "unavailable は prediction が存在しないことと同義ではない",
            "UI は unavailable 時に explanation を作文してはならない",
        ],
        "must_not_mean_i18n": {
            "ja": [
                "unavailable は安全を意味しない",
                "unavailable は prediction が存在しないことと同義ではない",
                "UI は unavailable 時に explanation を作文してはならない",
            ],
            "en": [
                "unavailable does not mean safe",
                "unavailable is not the same as prediction not existing",
                "UI must not compose explanations when unavailable",
            ],
            "th": [
                "unavailable ไม่ได้หมายถึงความปลอดภัย",
                "unavailable ไม่ได้แปลว่า prediction ไม่มีอยู่",
                "UI ต้องไม่แต่ง explanation เมื่อ unavailable",
            ],
        },
        "ui_terms": ui_terms_with_i18n(build_ui_terms()),
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
    )
    watchpoints = extract_watchpoints_from_monitor(monitor)
    historical = extract_historical(historical_pattern, historical_analog)
    implications = extract_implications(
        prediction,
        scenario,
        confidence,
    )
    risks = extract_risks(prediction, dominant_scenario, confidence, historical)
    invalidation = extract_invalidation(prediction, scenario, dominant_scenario)

    headline_i18n = i18n_for_headline(dominant_scenario, watchpoints, confidence)
    decision_line_i18n = i18n_for_decision_line(dominant_scenario, risk_value, confidence)
    summary_i18n = i18n_for_summary(
        dominant_scenario,
        confidence,
        watchpoints,
        risk_value,
        historical,
    )
    interpretation_i18n = i18n_for_interpretation(
        dominant_scenario,
        confidence,
        risk_value,
        drivers,
        monitor,
    )
    why_it_matters_i18n = i18n_for_why_it_matters(
        dominant_scenario,
        confidence,
        risk_value,
    )
    narrative_flow_i18n = i18n_for_narrative_flow(
        headline_i18n,
        summary_i18n,
        interpretation_i18n,
        decision_line_i18n,
    )

    drivers_i18n = {"ja": [], "en": [], "th": []}
    drivers_base: list[dict[str, str]] = []
    for row in drivers:
        rendered = driver_text_triplet_i18n(
            row.get("driver", ""),
            dominant_scenario,
            confidence,
            risk_value,
        )
        drivers_i18n["ja"].append(rendered["ja"])
        drivers_i18n["en"].append(rendered["en"])
        drivers_i18n["th"].append(rendered["th"])
        drivers_base.append(rendered["ja"])

    monitor_i18n = {"ja": [], "en": [], "th": []}
    monitor_base: list[dict[str, str]] = []
    for row in monitor:
        rendered = monitor_text_triplet_i18n(
            row.get("item", ""),
            dominant_scenario,
        )
        monitor_i18n["ja"].append(rendered["ja"])
        monitor_i18n["en"].append(rendered["en"])
        monitor_i18n["th"].append(rendered["th"])
        monitor_base.append(rendered["ja"])

    historical_i18n = {"ja": [], "en": [], "th": []}
    historical_base: list[dict[str, Any]] = []
    for row in historical:
        rendered = historical_row_i18n(row)
        historical_i18n["ja"].append(rendered["ja"])
        historical_i18n["en"].append(rendered["en"])
        historical_i18n["th"].append(rendered["th"])
        historical_base.append(rendered["ja"])

    implications_i18n = {"ja": [], "en": [], "th": []}
    implications_base: list[dict[str, Any]] = []
    for row in implications:
        rendered = implication_row_i18n(row, dominant_scenario)
        implications_i18n["ja"].append(rendered["ja"])
        implications_i18n["en"].append(rendered["en"])
        implications_i18n["th"].append(rendered["th"])
        implications_base.append(rendered["ja"])

    risks_i18n = risks_i18n_from_context(
        risk_value=risk_value,
        dominant_scenario=dominant_scenario,
        confidence=confidence,
        historical=historical,
    )
    invalidation_i18n = invalidation_i18n_from_context(
        dominant_scenario=dominant_scenario,
        prediction=prediction,
        scenario=scenario,
    )
    must_not_mean_all_i18n = must_not_mean_i18n()

    watchpoints_i18n = {
        "ja": [translate_key_generic(x)["ja"] for x in watchpoints],
        "en": [translate_key_generic(x)["en"] for x in watchpoints],
        "th": [translate_key_generic(x)["th"] for x in watchpoints],
    }

    based_on: list[str] = [str(prediction_path), str(scenario_path), str(signal_path)]
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
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "headline": headline_i18n["ja"],
        "headline_i18n": headline_i18n,
        "decision_line": decision_line_i18n["ja"],
        "decision_line_i18n": decision_line_i18n,
        "summary": summary_i18n["ja"],
        "summary_i18n": summary_i18n,
        "interpretation": interpretation_i18n["ja"],
        "interpretation_i18n": interpretation_i18n,
        "why_it_matters": why_it_matters_i18n["ja"],
        "why_it_matters_i18n": why_it_matters_i18n,
        "narrative_flow": narrative_flow_i18n["ja"],
        "narrative_flow_i18n": narrative_flow_i18n,
        "based_on": based_on,
        "context": {
            "dominant_scenario": dominant_scenario,
            "confidence": confidence,
            "overall_risk": risk_value,
        },
        "context_i18n": {
            "dominant_scenario": label_for_scenario(dominant_scenario),
            "overall_risk": label_for_risk(risk_value),
            "confidence": format_confidence_text_i18n(confidence),
        },
        "drivers": drivers_base,
        "drivers_i18n": drivers_i18n,
        "monitor": monitor_base,
        "monitor_i18n": monitor_i18n,
        "watchpoints": watchpoints_i18n["ja"],
        "watchpoints_i18n": watchpoints_i18n,
        "historical": historical_base,
        "historical_i18n": historical_i18n,
        "implications": implications_base,
        "implications_i18n": implications_i18n,
        "risks": risks_i18n["ja"],
        "risks_i18n": risks_i18n,
        "invalidation": invalidation_i18n["ja"],
        "invalidation_i18n": invalidation_i18n,
        "must_not_mean": must_not_mean_all_i18n["ja"],
        "must_not_mean_i18n": must_not_mean_all_i18n,
        "ui_terms": ui_terms_with_i18n(build_ui_terms()),
        "generated_at": utc_now_iso(),
    }

    if reference_memory is not None:
        memory_refs = to_text_list(
            pick_first(
                reference_memory,
                "reference_memory",
                "memories",
                "historical_patterns",
                "similar_cases",
                default=[],
            )
        )
        if memory_refs:
            translated_refs = [translate_key_generic(x) for x in memory_refs[:6]]
            artifact["reference_memory"] = [x["ja"] for x in translated_refs]
            artifact["reference_memory_i18n"] = {
                "ja": [x["ja"] for x in translated_refs],
                "en": [x["en"] for x in translated_refs],
                "th": [x["th"] for x in translated_refs],
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
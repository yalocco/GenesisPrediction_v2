#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from i18n_translate import (
    translate_reference_memory_summary as shared_translate_reference_memory_summary,
    translate_status as shared_translate_status,
)


ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"

TREND_LATEST_PATH = PREDICTION_DIR / "trend_latest.json"
SIGNAL_LATEST_PATH = PREDICTION_DIR / "signal_latest.json"
HISTORICAL_PATTERN_LATEST_PATH = PREDICTION_DIR / "historical_pattern_latest.json"
HISTORICAL_ANALOG_LATEST_PATH = PREDICTION_DIR / "historical_analog_latest.json"
SCENARIO_LATEST_PATH = PREDICTION_DIR / "scenario_latest.json"
REFERENCE_MEMORY_LATEST_PATH = PREDICTION_DIR / "reference_memory_latest.json"

PREDICTION_LATEST_PATH = PREDICTION_DIR / "prediction_latest.json"

LANG_DEFAULT = "ja"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]

DIRECTION_LABELS = {
    "deteriorating": {
        "en": "deteriorating",
        "ja": "悪化方向",
        "th": "แนวโน้มแย่ลง",
    },
    "stabilizing": {
        "en": "stabilizing",
        "ja": "安定化方向",
        "th": "แนวโน้มทรงตัวดีขึ้น",
    },
    "guarded_deterioration": {
        "en": "guarded deterioration",
        "ja": "警戒を伴う悪化方向",
        "th": "แนวโน้มแย่ลงแบบต้องเฝ้าระวัง",
    },
    "historically_guarded": {
        "en": "historically guarded",
        "ja": "歴史的には警戒優勢",
        "th": "ในเชิงประวัติศาสตร์ควรระวัง",
    },
    "stable_to_guarded": {
        "en": "stable to guarded",
        "ja": "安定〜警戒",
        "th": "ทรงตัวถึงเฝ้าระวัง",
    },
}

SCENARIO_LABELS = {
    "best_case": {
        "en": "best_case",
        "ja": "最良シナリオ",
        "th": "กรณีดีที่สุด",
    },
    "base_case": {
        "en": "base_case",
        "ja": "基本シナリオ",
        "th": "กรณีฐาน",
    },
    "worst_case": {
        "en": "worst_case",
        "ja": "最悪シナリオ",
        "th": "กรณีเลวร้ายที่สุด",
    },
}

RISK_LABELS = {
    "low": {
        "en": "low",
        "ja": "低",
        "th": "ต่ำ",
    },
    "stable": {
        "en": "stable",
        "ja": "安定",
        "th": "ทรงตัว",
    },
    "guarded": {
        "en": "guarded",
        "ja": "警戒",
        "th": "เฝ้าระวัง",
    },
    "high": {
        "en": "high",
        "ja": "高",
        "th": "สูง",
    },
    "critical": {
        "en": "critical",
        "ja": "重大",
        "th": "วิกฤต",
    },
}

ACTION_BIAS_LABELS = {
    "defensive": {
        "en": "defensive",
        "ja": "防御寄り",
        "th": "เชิงป้องกัน",
    },
    "constructive": {
        "en": "constructive",
        "ja": "前向き",
        "th": "เชิงบวก",
    },
    "guarded": {
        "en": "guarded",
        "ja": "警戒寄り",
        "th": "ระมัดระวัง",
    },
    "balanced": {
        "en": "balanced",
        "ja": "中立",
        "th": "สมดุล",
    },
}

OUTCOME_LABELS = {
    "currency_down": {
        "en": "currency weakness",
        "ja": "通貨下落",
        "th": "ค่าเงินอ่อนตัว",
    },
    "currency_sharp_down": {
        "en": "sharp currency weakness",
        "ja": "急激な通貨下落",
        "th": "ค่าเงินอ่อนตัวรุนแรง",
    },
    "trade_disruption": {
        "en": "trade disruption",
        "ja": "貿易混乱",
        "th": "การค้าสะดุด",
    },
    "energy_up": {
        "en": "energy prices rise",
        "ja": "エネルギー価格上昇",
        "th": "ราคาพลังงานปรับขึ้น",
    },
    "commodity_up": {
        "en": "commodity prices rise",
        "ja": "商品価格上昇",
        "th": "ราคาสินค้าโภคภัณฑ์ปรับขึ้น",
    },
    "credit_spreads_up": {
        "en": "credit spreads widen",
        "ja": "信用スプレッド拡大",
        "th": "ส่วนต่างเครดิตกว้างขึ้น",
    },
    "inflation_up": {
        "en": "inflation rises",
        "ja": "インフレ上昇",
        "th": "เงินเฟ้อปรับขึ้น",
    },
    "growth_down": {
        "en": "growth slows",
        "ja": "成長鈍化",
        "th": "การเติบโตชะลอลง",
    },
    "volatility_up": {
        "en": "volatility rises",
        "ja": "ボラティリティ上昇",
        "th": "ความผันผวนเพิ่มขึ้น",
    },
    "liquidity_down": {
        "en": "liquidity weakens",
        "ja": "流動性低下",
        "th": "สภาพคล่องอ่อนตัว",
    },
}

GENERIC_TEXT_MAP = {
    "No scenario narrative available.": {
        "en": "No scenario narrative available.",
        "ja": "利用可能なシナリオ説明はありません。",
        "th": "ไม่มีคำอธิบายสถานการณ์ที่พร้อมใช้งาน",
    },
    "No historical context available.": {
        "en": "No historical context available.",
        "ja": "利用可能な歴史的文脈はありません。",
        "th": "ไม่มีบริบททางประวัติศาสตร์ที่พร้อมใช้งาน",
    },
}

HISTORICAL_SUPPORT_PHRASES = {
    "strong": {
        "en": "historical support is strong",
        "ja": "歴史的裏付けは強い",
        "th": "แรงสนับสนุนจากประวัติศาสตร์อยู่ในระดับสูง",
    },
    "moderate": {
        "en": "historical support is moderate",
        "ja": "歴史的裏付けは中程度",
        "th": "แรงสนับสนุนจากประวัติศาสตร์อยู่ในระดับปานกลาง",
    },
    "limited": {
        "en": "historical support is limited",
        "ja": "歴史的裏付けは限定的",
        "th": "แรงสนับสนุนจากประวัติศาสตร์มีจำกัด",
    },
}

LABEL_REGISTRY = {
    "debt_bubble_banking_crisis": {
        "en": "debt bubble and banking crisis",
        "ja": "債務バブルと銀行危機",
        "th": "ฟองสบู่หนี้และวิกฤตธนาคาร",
    },
    "financial_crisis": {
        "en": "financial crisis",
        "ja": "金融危機",
        "th": "วิกฤตการเงิน",
    },
    "banking_crisis": {
        "en": "banking crisis",
        "ja": "銀行危機",
        "th": "วิกฤตธนาคาร",
    },
    "banking_stress": {
        "en": "banking stress",
        "ja": "銀行ストレス",
        "th": "แรงกดดันในภาคธนาคาร",
    },
    "currency_instability": {
        "en": "currency instability",
        "ja": "通貨不安定",
        "th": "ความไม่เสถียรของค่าเงิน",
    },
    "risk_pressure": {
        "en": "risk pressure",
        "ja": "リスク圧力",
        "th": "แรงกดดันด้านความเสี่ยง",
    },
    "systemic_stress": {
        "en": "systemic stress",
        "ja": "システム全体ストレス",
        "th": "แรงกดดันเชิงระบบ",
    },
    "trade_fragmentation": {
        "en": "trade fragmentation",
        "ja": "貿易分断",
        "th": "การแตกตัวของการค้า",
    },
    "geopolitical_escalation": {
        "en": "geopolitical escalation",
        "ja": "地政学的緊張の激化",
        "th": "ความตึงเครียดทางภูมิรัฐศาสตร์ที่ยกระดับ",
    },
    "sovereign_debt_stress": {
        "en": "sovereign debt stress",
        "ja": "政府債務ストレス",
        "th": "แรงกดดันจากหนี้ภาครัฐ",
    },
    "energy_supply_shock": {
        "en": "energy supply shock",
        "ja": "エネルギー供給ショック",
        "th": "แรงกระแทกด้านอุปทานพลังงาน",
    },
    "inflation_shock": {
        "en": "inflation shock",
        "ja": "インフレショック",
        "th": "แรงกระแทกจากเงินเฟ้อ",
    },
    "disaster_supply_shock": {
        "en": "disaster-driven supply shock",
        "ja": "災害起因の供給ショック",
        "th": "แรงกระแทกด้านอุปทานจากภัยพิบัติ",
    },
    "empire_decline": {
        "en": "imperial decline",
        "ja": "帝国衰退",
        "th": "การเสื่อมถอยของจักรวรรดิ",
    },
    "war": {
        "en": "war",
        "ja": "戦争",
        "th": "สงคราม",
    },
    "military": {
        "en": "military tension",
        "ja": "軍事緊張",
        "th": "ความตึงเครียดทางทหาร",
    },
    "sanction": {
        "en": "sanctions",
        "ja": "制裁",
        "th": "มาตรการคว่ำบาตร",
    },
    "debt": {
        "en": "debt stress",
        "ja": "債務ストレス",
        "th": "แรงกดดันด้านหนี้",
    },
    "bank": {
        "en": "bank stress",
        "ja": "銀行ストレス",
        "th": "แรงกดดันในภาคธนาคาร",
    },
    "currency": {
        "en": "currency stress",
        "ja": "通貨ストレス",
        "th": "แรงกดดันด้านค่าเงิน",
    },
    "drought": {
        "en": "drought",
        "ja": "干ばつ",
        "th": "ภัยแล้ง",
    },
    "flood": {
        "en": "flood",
        "ja": "洪水",
        "th": "น้ำท่วม",
    },
    "pandemic": {
        "en": "pandemic",
        "ja": "パンデミック",
        "th": "โรคระบาดใหญ่",
    },
    "trade": {
        "en": "trade stress",
        "ja": "貿易ストレス",
        "th": "แรงกดดันด้านการค้า",
    },
    "unrest": {
        "en": "civil unrest",
        "ja": "社会不安",
        "th": "ความไม่สงบในสังคม",
    },
    "historical_pattern": {
        "en": "historical pattern",
        "ja": "歴史パターン",
        "th": "รูปแบบทางประวัติศาสตร์",
    },
    "historical_analog": {
        "en": "historical analog",
        "ja": "歴史アナログ",
        "th": "กรณีเทียบเคียงทางประวัติศาสตร์",
    },
    "memory": {
        "en": "memory context",
        "ja": "記憶参照",
        "th": "บริบทจากหน่วยความจำ",
    },
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def unique_preserve_order(items: List[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, (dict, list)) else str(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def ensure_lang_map(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, str] = {}
    for lang in SUPPORTED_LANGUAGES:
        text = value.get(lang)
        if text is None:
            continue
        text_str = str(text).strip()
        if text_str:
            out[lang] = text_str
    return out


def ensure_lang_list_map(value: Any) -> Dict[str, List[str]]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, List[str]] = {}
    for lang in SUPPORTED_LANGUAGES:
        items = value.get(lang)
        if not isinstance(items, list):
            continue
        out[lang] = [str(x).strip() for x in items if str(x).strip()]
    return out


def finalize_text_i18n(base_en: str, partial: Dict[str, str]) -> Dict[str, str]:
    en_text = str(partial.get("en") or base_en or "").strip()
    ja_text = str(partial.get("ja") or en_text).strip()
    th_text = str(partial.get("th") or en_text).strip()
    return {
        "en": en_text,
        "ja": ja_text,
        "th": th_text,
    }


def finalize_list_i18n(base_en_list: List[str], partial: Dict[str, List[str]]) -> Dict[str, List[str]]:
    en_list = partial.get("en") or list(base_en_list)
    ja_list = partial.get("ja") or list(en_list)
    th_list = partial.get("th") or list(en_list)
    return {
        "en": en_list,
        "ja": ja_list,
        "th": th_list,
    }


def prettify_label_en(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""

    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        prefix_label = LABEL_REGISTRY.get(normalize_text(prefix), {}).get("en", prefix.replace("_", " ").strip())
        rest_label = prettify_label_en(rest)
        return f"{prefix_label}: {rest_label}" if rest_label else prefix_label

    pretty = raw.replace("_", " ").replace("-", " ").strip()
    pretty = " ".join(pretty.split())
    if not pretty:
        return raw
    return pretty


def labelize_i18n(value: Any) -> Dict[str, str]:
    raw = str(value or "").strip()
    if not raw:
        return {"en": "", "ja": "", "th": ""}

    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        prefix_i18n = labelize_i18n(prefix)
        rest_i18n = labelize_i18n(rest)
        return {
            "en": f"{prefix_i18n['en']}: {rest_i18n['en']}" if rest_i18n["en"] else prefix_i18n["en"],
            "ja": f"{prefix_i18n['ja']}: {rest_i18n['ja']}" if rest_i18n["ja"] else prefix_i18n["ja"],
            "th": f"{prefix_i18n['th']}: {rest_i18n['th']}" if rest_i18n["th"] else prefix_i18n["th"],
        }

    mapped = LABEL_REGISTRY.get(normalize_text(raw))
    if mapped:
        return finalize_text_i18n(str(mapped.get("en") or raw), mapped)

    pretty_en = prettify_label_en(raw)
    return {
        "en": pretty_en,
        "ja": pretty_en,
        "th": pretty_en,
    }


def labelize(value: Any, lang: str = LANG_DEFAULT) -> str:
    return labelize_i18n(value).get(lang, str(value or "").strip())


def labelize_list(items: List[Any], lang: str = LANG_DEFAULT) -> List[str]:
    return [labelize(item, lang=lang) for item in items if str(item or "").strip()]


def label_from_map(value: str, mapping: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    key = normalize_text(value)
    mapped = mapping.get(key)
    if mapped:
        return finalize_text_i18n(str(mapped.get("en") or key), mapped)
    base = str(value or "").strip()
    return {
        "en": base,
        "ja": base,
        "th": base,
    }


def translate_generic_text(text: str) -> Dict[str, str]:
    base = str(text or "").strip()
    if not base:
        return {"en": "", "ja": "", "th": ""}
    mapped = GENERIC_TEXT_MAP.get(base)
    if mapped:
        return finalize_text_i18n(base, mapped)
    return {
        "en": base,
        "ja": base,
        "th": base,
    }


def extract_reference_memory_from_scenario(scenario_data: Dict[str, Any]) -> Dict[str, Any]:
    reference_memory = scenario_data.get("reference_memory", {})
    return reference_memory if isinstance(reference_memory, dict) else {}


def merge_reference_memory(
    scenario_reference_memory: Dict[str, Any],
    direct_reference_memory: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(scenario_reference_memory, dict):
        scenario_reference_memory = {}
    if not isinstance(direct_reference_memory, dict):
        direct_reference_memory = {}

    if scenario_reference_memory.get("status") == "ok":
        return scenario_reference_memory

    if direct_reference_memory.get("status") == "ok":
        return direct_reference_memory

    merged = dict(direct_reference_memory)
    merged.update(scenario_reference_memory)

    if not merged:
        return {
            "status": "unavailable",
            "summary": "",
            "decision_refs": [],
            "similar_cases": [],
            "historical_patterns": [],
            "historical_analogs": [],
        }

    if "summary" not in merged and "recall_summary" in merged:
        merged["summary"] = merged.get("recall_summary")

    return merged


def extract_memory_summary(reference_memory: Dict[str, Any]) -> str:
    if not isinstance(reference_memory, dict):
        return ""
    return str(reference_memory.get("summary") or reference_memory.get("recall_summary") or "").strip()


def extract_memory_status(reference_memory: Dict[str, Any]) -> str:
    if not isinstance(reference_memory, dict):
        return "unavailable"
    return str(reference_memory.get("status") or "unavailable").strip()


def extract_scenario_map(scenario_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    scenarios = scenario_data.get("scenarios", [])
    if not isinstance(scenarios, list):
        return out

    for item in scenarios:
        if not isinstance(item, dict):
            continue
        scenario_id = normalize_text(item.get("scenario_id"))
        if scenario_id:
            out[scenario_id] = item
    return out


def choose_primary_narrative(scenario_data: Dict[str, Any]) -> str:
    dominant = normalize_text(scenario_data.get("dominant_scenario"))
    scenario_map = extract_scenario_map(scenario_data)
    selected = scenario_map.get(dominant)
    if isinstance(selected, dict) and selected.get("narrative"):
        return str(selected.get("narrative"))
    summary = scenario_data.get("summary")
    if summary:
        return str(summary)
    return "No scenario narrative available."


def choose_primary_narrative_i18n(scenario_data: Dict[str, Any], primary_narrative: str) -> Dict[str, str]:
    dominant = normalize_text(scenario_data.get("dominant_scenario"))
    scenario_map = extract_scenario_map(scenario_data)
    selected = scenario_map.get(dominant)

    if isinstance(selected, dict):
        selected_i18n = ensure_lang_map(selected.get("narrative_i18n"))
        if selected_i18n:
            return finalize_text_i18n(primary_narrative, selected_i18n)

    summary_i18n = ensure_lang_map(scenario_data.get("summary_i18n"))
    if summary_i18n and primary_narrative == str(scenario_data.get("summary") or "").strip():
        return finalize_text_i18n(primary_narrative, summary_i18n)

    return translate_generic_text(primary_narrative)


def compute_historical_support_level(
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
) -> float:
    pattern_conf = safe_float(pattern_data.get("pattern_confidence"))
    analog_conf = safe_float(analog_data.get("analog_confidence"))
    support = 0.65 * pattern_conf + 0.35 * analog_conf
    return round(clamp01(support), 4)


def collect_signal_tags(signal_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    for key in ("signal_tags", "historical_tags", "trend_tags_used", "dominant_signals", "watchpoints"):
        value = signal_data.get(key)
        if isinstance(value, list):
            tags.extend(normalize_text(x) for x in value if normalize_text(x))

    signals = signal_data.get("signals", [])
    if isinstance(signals, list):
        for item in signals:
            if not isinstance(item, dict):
                continue
            key = normalize_text(item.get("key"))
            if key:
                tags.append(key)
            item_tags = item.get("tags", [])
            if isinstance(item_tags, list):
                tags.extend(normalize_text(x) for x in item_tags if normalize_text(x))

    return unique_preserve_order([x for x in tags if x])


def collect_trend_tags(trend_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    raw_tags = trend_data.get("trend_tags", [])
    if isinstance(raw_tags, list):
        tags.extend(normalize_text(x) for x in raw_tags if normalize_text(x))

    trends = trend_data.get("trends", [])
    if isinstance(trends, list):
        for item in trends:
            if not isinstance(item, dict):
                continue
            key = normalize_text(item.get("key"))
            direction = normalize_text(item.get("direction"))
            if key and direction:
                tags.append(f"{key}_{direction}")
            item_tags = item.get("tags", [])
            if isinstance(item_tags, list):
                tags.extend(normalize_text(x) for x in item_tags if normalize_text(x))

    return unique_preserve_order([x for x in tags if x])


def classify_prediction_direction(
    scenario_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
) -> str:
    dominant = normalize_text(scenario_data.get("dominant_scenario"))
    risk = normalize_text(scenario_data.get("risk"))
    dominant_pattern = normalize_text(pattern_data.get("dominant_pattern"))

    signal_tags = set(collect_signal_tags(signal_data))

    if dominant == "worst_case":
        return "deteriorating"
    if dominant == "best_case":
        return "stabilizing"

    stress_keywords = {
        "war",
        "military",
        "sanction",
        "debt",
        "bank",
        "currency",
        "drought",
        "flood",
        "pandemic",
        "trade",
        "unrest",
        "banking_stress",
        "currency_instability",
        "risk_pressure",
        "systemic_stress",
    }

    if risk in {"critical", "high", "guarded"} and (signal_tags & stress_keywords):
        return "guarded_deterioration"

    if dominant_pattern:
        return "historically_guarded"

    return "stable_to_guarded"


def build_prediction_statement(
    dominant_scenario: str,
    risk: str,
    direction: str,
    confidence: float,
    dominant_pattern: str,
    dominant_analog: str,
    memory_summary: str,
) -> str:
    dominant_pattern_label = labelize(dominant_pattern, lang="en")
    dominant_analog_label = labelize(dominant_analog, lang="en")

    sentence = (
        f"Primary outlook is {dominant_scenario} with {risk} risk and "
        f"{direction} directional bias at confidence {confidence:.2f}."
    )

    if dominant_pattern_label and dominant_analog_label:
        sentence += (
            f" Historical support is led by pattern {dominant_pattern_label} "
            f"and analog {dominant_analog_label}."
        )
    elif dominant_pattern_label:
        sentence += f" Historical support is led by pattern {dominant_pattern_label}."
    elif dominant_analog_label:
        sentence += f" Historical support is led by analog {dominant_analog_label}."

    if memory_summary:
        sentence += f" Memory context: {memory_summary}."

    return sentence


def build_prediction_statement_i18n(
    dominant_scenario: str,
    risk: str,
    direction: str,
    confidence: float,
    dominant_pattern: str,
    dominant_analog: str,
    memory_summary: str,
    prediction_statement_en: str,
) -> Dict[str, str]:
    scenario_labels = label_from_map(dominant_scenario, SCENARIO_LABELS)
    risk_labels = label_from_map(risk, RISK_LABELS)
    direction_labels = label_from_map(direction, DIRECTION_LABELS)
    dominant_pattern_labels = labelize_i18n(dominant_pattern)
    dominant_analog_labels = labelize_i18n(dominant_analog)

    en = (
        f"Primary outlook is {scenario_labels['en']} with {risk_labels['en']} risk and "
        f"{direction_labels['en']} directional bias at confidence {confidence:.2f}."
    )
    ja = (
        f"主要見通しは {scenario_labels['ja']}。"
        f"リスクは {risk_labels['ja']}、方向性は {direction_labels['ja']}、"
        f"信頼度は {confidence:.2f}。"
    )
    th = (
        f"มุมมองหลักคือ {scenario_labels['th']} "
        f"โดยมีระดับความเสี่ยง {risk_labels['th']} "
        f"และทิศทาง {direction_labels['th']} "
        f"ที่ความเชื่อมั่น {confidence:.2f}."
    )

    if dominant_pattern_labels["en"] and dominant_analog_labels["en"]:
        en += (
            f" Historical support is led by pattern {dominant_pattern_labels['en']} "
            f"and analog {dominant_analog_labels['en']}."
        )
        ja += (
            f" 歴史的裏付けはパターン {dominant_pattern_labels['ja']} "
            f"とアナログ {dominant_analog_labels['ja']} が主導している。"
        )
        th += (
            f" แรงสนับสนุนทางประวัติศาสตร์นำโดย pattern {dominant_pattern_labels['th']} "
            f"และ analog {dominant_analog_labels['th']}."
        )
    elif dominant_pattern_labels["en"]:
        en += f" Historical support is led by pattern {dominant_pattern_labels['en']}."
        ja += f" 歴史的裏付けはパターン {dominant_pattern_labels['ja']} が主導している。"
        th += f" แรงสนับสนุนทางประวัติศาสตร์นำโดย pattern {dominant_pattern_labels['th']}."
    elif dominant_analog_labels["en"]:
        en += f" Historical support is led by analog {dominant_analog_labels['en']}."
        ja += f" 歴史的裏付けはアナログ {dominant_analog_labels['ja']} が主導している。"
        th += f" แรงสนับสนุนทางประวัติศาสตร์นำโดย analog {dominant_analog_labels['th']}."

    if memory_summary:
        en += f" Memory context: {memory_summary}."
        ja += f" 記憶参照文脈: {memory_summary}。"
        th += f" บริบทจากหน่วยความจำ: {memory_summary}."

    return finalize_text_i18n(
        prediction_statement_en,
        {
            "en": en,
            "ja": ja,
            "th": th,
        },
    )


def build_action_bias(
    dominant_scenario: str,
    risk: str,
    expected_outcomes: List[str],
    historical_support_level: float,
    reference_memory: Dict[str, Any],
) -> str:
    outcomes = set(normalize_text(x) for x in expected_outcomes)
    memory_summary = normalize_text(extract_memory_summary(reference_memory))

    if "financial_crisis" in memory_summary or "banking_crisis" in memory_summary:
        return "defensive"

    if dominant_scenario == "worst_case":
        return "defensive"
    if dominant_scenario == "best_case" and risk in {"stable", "low"}:
        return "constructive"
    if {"currency_down", "currency_sharp_down", "trade_disruption", "energy_up", "commodity_up", "credit_spreads_up"} & outcomes:
        return "guarded"
    if historical_support_level >= 0.7:
        return "guarded"
    return "balanced"


def build_monitoring_priorities(
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
    reference_memory: Dict[str, Any],
) -> List[str]:
    priorities: List[str] = []

    for item in scenario_data.get("watchpoints", [])[:6]:
        if item is not None:
            priorities.append(normalize_text(item))

    historical_context = scenario_data.get("historical_context", {})
    if isinstance(historical_context, dict):
        for item in historical_context.get("historical_watchpoints", [])[:6]:
            if item is not None:
                priorities.append(normalize_text(item))

    matched_patterns = pattern_data.get("matched_patterns", [])
    if isinstance(matched_patterns, list):
        for item in matched_patterns[:2]:
            if isinstance(item, dict):
                for wp in item.get("watchpoints", [])[:3]:
                    if wp is not None:
                        priorities.append(normalize_text(wp))

    top_analogs = analog_data.get("top_analogs", [])
    if isinstance(top_analogs, list):
        for item in top_analogs[:2]:
            if isinstance(item, dict):
                for wp in item.get("watchpoints", [])[:3]:
                    if wp is not None:
                        priorities.append(normalize_text(wp))
                for sim in item.get("similarities", [])[:2]:
                    if sim is not None:
                        priorities.append(normalize_text(sim))

    for bucket_name in ("historical_patterns", "historical_analogs", "similar_cases"):
        for item in reference_memory.get(bucket_name, [])[:2]:
            if not isinstance(item, dict):
                continue
            for tag in item.get("tags", [])[:3]:
                if tag is not None:
                    priorities.append(normalize_text(tag))

    return unique_preserve_order([x for x in priorities if x])[:12]


def build_prediction_drivers(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
    reference_memory: Dict[str, Any],
) -> List[str]:
    drivers: List[str] = []

    drivers.extend(collect_trend_tags(trend_data)[:5])
    drivers.extend(collect_signal_tags(signal_data)[:6])

    for item in scenario_data.get("key_drivers", [])[:6]:
        if item is not None:
            drivers.append(normalize_text(item))

    dominant_pattern = pattern_data.get("dominant_pattern")
    dominant_analog = analog_data.get("dominant_analog")
    if dominant_pattern:
        drivers.append(f"historical_pattern:{normalize_text(dominant_pattern)}")
    if dominant_analog:
        drivers.append(f"historical_analog:{normalize_text(dominant_analog)}")

    for item in reference_memory.get("historical_patterns", [])[:2]:
        if isinstance(item, dict) and item.get("title"):
            drivers.append(f"memory_pattern:{normalize_text(item.get('title'))}")

    for item in reference_memory.get("historical_analogs", [])[:2]:
        if isinstance(item, dict) and item.get("title"):
            drivers.append(f"memory_analog:{normalize_text(item.get('title'))}")

    for item in reference_memory.get("similar_cases", [])[:2]:
        if isinstance(item, dict) and item.get("title"):
            drivers.append(f"memory_case:{normalize_text(item.get('title'))}")

    memory_summary = extract_memory_summary(reference_memory)
    if memory_summary:
        drivers.append(f"memory:{normalize_text(memory_summary)}")

    return unique_preserve_order([x for x in drivers if x])[:14]


def build_historical_context(
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
) -> Dict[str, Any]:
    support_level = compute_historical_support_level(pattern_data, analog_data)

    dominant_pattern = pattern_data.get("dominant_pattern")
    dominant_analog = analog_data.get("dominant_analog")
    dominant_pattern_label_en = labelize(dominant_pattern, lang="en")
    dominant_analog_label_en = labelize(dominant_analog, lang="en")
    dominant_pattern_i18n = labelize_i18n(dominant_pattern)
    dominant_analog_i18n = labelize_i18n(dominant_analog)

    summary_parts: List[str] = []

    if dominant_pattern_label_en:
        summary_parts.append(f"dominant pattern is {dominant_pattern_label_en}")
    if dominant_analog_label_en:
        summary_parts.append(f"dominant analog is {dominant_analog_label_en}")

    support_strength = "limited"
    if support_level >= 0.75:
        support_strength = "strong"
    elif support_level >= 0.5:
        support_strength = "moderate"

    summary_parts.append(HISTORICAL_SUPPORT_PHRASES[support_strength]["en"])

    summary = ". ".join(summary_parts).strip()
    if summary:
        summary += "."
    else:
        summary = "No historical context available."

    historical_context = scenario_data.get("historical_context", {})
    current_stress_vector = {}
    if isinstance(historical_context, dict):
        csv = historical_context.get("current_stress_vector", {})
        if isinstance(csv, dict):
            current_stress_vector = {str(k): round(clamp01(safe_float(v)), 4) for k, v in csv.items()}

    if summary == "No historical context available.":
        summary_i18n = translate_generic_text(summary)
    else:
        en_parts: List[str] = []
        ja_parts: List[str] = []
        th_parts: List[str] = []

        if dominant_pattern_label_en:
            en_parts.append(f"dominant pattern is {dominant_pattern_label_en}")
            ja_parts.append(f"主要パターンは {dominant_pattern_i18n['ja']}")
            th_parts.append(f"pattern หลักคือ {dominant_pattern_i18n['th']}")

        if dominant_analog_label_en:
            en_parts.append(f"dominant analog is {dominant_analog_label_en}")
            ja_parts.append(f"主要アナログは {dominant_analog_i18n['ja']}")
            th_parts.append(f"analog หลักคือ {dominant_analog_i18n['th']}")

        en_parts.append(HISTORICAL_SUPPORT_PHRASES[support_strength]["en"])
        ja_parts.append(HISTORICAL_SUPPORT_PHRASES[support_strength]["ja"])
        th_parts.append(HISTORICAL_SUPPORT_PHRASES[support_strength]["th"])

        summary_i18n = {
            "en": ". ".join(en_parts).strip() + ".",
            "ja": "。".join(ja_parts).strip() + "。",
            "th": ". ".join(th_parts).strip() + ".",
        }

    return {
        "dominant_pattern": labelize(dominant_pattern, lang=LANG_DEFAULT),
        "dominant_pattern_id": dominant_pattern,
        "dominant_pattern_i18n": dominant_pattern_i18n,
        "pattern_confidence": round(safe_float(pattern_data.get("pattern_confidence")), 4),
        "dominant_analog": labelize(dominant_analog, lang=LANG_DEFAULT),
        "dominant_analog_id": dominant_analog,
        "dominant_analog_i18n": dominant_analog_i18n,
        "analog_confidence": round(safe_float(analog_data.get("analog_confidence")), 4),
        "support_level": support_level,
        "current_stress_vector": current_stress_vector,
        "summary": summary,
        "summary_i18n": summary_i18n,
    }


def calculate_prediction_confidence(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
    reference_memory: Dict[str, Any],
) -> float:
    trend_conf = safe_float(trend_data.get("overall_confidence", trend_data.get("confidence", 0.0)))

    signal_conf = 0.0
    signals = signal_data.get("signals", [])
    if isinstance(signals, list) and signals:
        signal_conf = sum(
            safe_float(item.get("confidence", 0.0))
            for item in signals
            if isinstance(item, dict)
        ) / len(signals)

    scenario_conf = safe_float(scenario_data.get("confidence", 0.0))
    pattern_conf = safe_float(pattern_data.get("pattern_confidence", 0.0))
    analog_conf = safe_float(analog_data.get("analog_confidence", 0.0))

    confidence = (
        0.15 * trend_conf
        + 0.20 * signal_conf
        + 0.40 * scenario_conf
        + 0.15 * pattern_conf
        + 0.10 * analog_conf
    )

    memory_status = normalize_text(extract_memory_status(reference_memory))
    memory_summary = extract_memory_summary(reference_memory)
    if memory_status == "ok" and memory_summary:
        confidence += 0.05

    return round(clamp01(confidence), 4)


def build_summary(
    direction: str,
    dominant_scenario: str,
    risk: str,
    confidence: float,
    historical_context: Dict[str, Any],
    memory_summary: str,
) -> str:
    base = (
        f"Prediction is {direction}. "
        f"Dominant scenario is {dominant_scenario}. "
        f"Risk is {risk}. "
        f"Confidence is {confidence:.2f}."
    )

    historical_summary = historical_context.get("summary")
    if historical_summary:
        base += f" {historical_summary}"

    if memory_summary:
        base += f" Memory context: {memory_summary}"

    return base


def build_summary_i18n(
    direction: str,
    dominant_scenario: str,
    risk: str,
    confidence: float,
    historical_context: Dict[str, Any],
    memory_summary: str,
    summary_en: str,
) -> Dict[str, str]:
    direction_labels = label_from_map(direction, DIRECTION_LABELS)
    scenario_labels = label_from_map(dominant_scenario, SCENARIO_LABELS)
    risk_labels = label_from_map(risk, RISK_LABELS)
    historical_summary_i18n = ensure_lang_map(historical_context.get("summary_i18n"))

    en = (
        f"Prediction is {direction_labels['en']}. "
        f"Dominant scenario is {scenario_labels['en']}. "
        f"Risk is {risk_labels['en']}. "
        f"Confidence is {confidence:.2f}."
    )
    ja = (
        f"予測は {direction_labels['ja']}。"
        f"主要シナリオは {scenario_labels['ja']}。"
        f"リスクは {risk_labels['ja']}。"
        f"信頼度は {confidence:.2f}。"
    )
    th = (
        f"การคาดการณ์อยู่ในทิศทาง {direction_labels['th']}. "
        f"สถานการณ์หลักคือ {scenario_labels['th']}. "
        f"ความเสี่ยงอยู่ในระดับ {risk_labels['th']}. "
        f"ความเชื่อมั่นอยู่ที่ {confidence:.2f}."
    )

    if historical_summary_i18n:
        en += f" {historical_summary_i18n.get('en', '')}".rstrip()
        ja += f" {historical_summary_i18n.get('ja', '')}".rstrip()
        th += f" {historical_summary_i18n.get('th', '')}".rstrip()

    if memory_summary:
        en += f" Memory context: {memory_summary}"
        ja += f" 記憶参照文脈: {memory_summary}"
        th += f" บริบทจากหน่วยความจำ: {memory_summary}"

    return finalize_text_i18n(
        summary_en,
        {
            "en": en.strip(),
            "ja": ja.strip(),
            "th": th.strip(),
        },
    )


def translate_expected_outcome_item(item: Any) -> Dict[str, str]:
    text = str(item or "").strip()
    key = normalize_text(text)
    if key in OUTCOME_LABELS:
        return finalize_text_i18n(text, OUTCOME_LABELS[key])

    pretty_en = text.replace("_", " ")
    if pretty_en:
        pretty_en = pretty_en[0].upper() + pretty_en[1:]
    else:
        pretty_en = ""

    return {
        "en": pretty_en or text,
        "ja": text,
        "th": text,
    }


def build_expected_outcomes_i18n(
    scenario_data: Dict[str, Any],
    expected_outcomes: List[str],
) -> Dict[str, List[str]]:
    direct_i18n = ensure_lang_list_map(scenario_data.get("expected_outcomes_i18n"))
    if direct_i18n:
        return finalize_list_i18n(expected_outcomes, direct_i18n)

    en_list: List[str] = []
    ja_list: List[str] = []
    th_list: List[str] = []

    for item in expected_outcomes:
        translated = translate_expected_outcome_item(item)
        en_list.append(translated["en"])
        ja_list.append(translated["ja"])
        th_list.append(translated["th"])

    return {
        "en": en_list,
        "ja": ja_list,
        "th": th_list,
    }


def build_reference_memory_output(reference_memory: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(reference_memory, dict):
        return {
            "status": "unavailable",
            "summary": "",
            "query_context": {},
        }

    return {
        "status": reference_memory.get("status", "unavailable"),
        "summary": extract_memory_summary(reference_memory),
        "query_context": reference_memory.get("query_context", {}),
    }


def build_prediction_output(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
    reference_memory_data: Dict[str, Any],
) -> Dict[str, Any]:
    as_of = (
        scenario_data.get("as_of")
        or signal_data.get("as_of")
        or trend_data.get("as_of")
        or pattern_data.get("as_of")
        or analog_data.get("as_of")
        or today_str()
    )

    dominant_scenario = normalize_text(scenario_data.get("dominant_scenario")) or "base_case"
    risk = normalize_text(scenario_data.get("risk")) or "guarded"
    memory_summary = extract_memory_summary(reference_memory_data)

    historical_context = build_historical_context(
        pattern_data=pattern_data,
        analog_data=analog_data,
        scenario_data=scenario_data,
    )

    direction = classify_prediction_direction(
        scenario_data=scenario_data,
        signal_data=signal_data,
        pattern_data=pattern_data,
    )

    confidence = calculate_prediction_confidence(
        trend_data=trend_data,
        signal_data=signal_data,
        scenario_data=scenario_data,
        pattern_data=pattern_data,
        analog_data=analog_data,
        reference_memory=reference_memory_data,
    )

    expected_outcomes = scenario_data.get("expected_outcomes", [])
    if not isinstance(expected_outcomes, list):
        expected_outcomes = []
    expected_outcomes = [str(x).strip() for x in expected_outcomes if str(x).strip()][:10]

    monitoring_priorities = build_monitoring_priorities(
        scenario_data=scenario_data,
        pattern_data=pattern_data,
        analog_data=analog_data,
        reference_memory=reference_memory_data,
    )

    action_bias = build_action_bias(
        dominant_scenario=dominant_scenario,
        risk=risk,
        expected_outcomes=expected_outcomes,
        historical_support_level=safe_float(historical_context.get("support_level")),
        reference_memory=reference_memory_data,
    )

    primary_narrative = choose_primary_narrative(scenario_data)

    prediction_statement = build_prediction_statement(
        dominant_scenario=dominant_scenario,
        risk=risk,
        direction=direction,
        confidence=confidence,
        dominant_pattern=str(historical_context.get("dominant_pattern_id") or ""),
        dominant_analog=str(historical_context.get("dominant_analog_id") or ""),
        memory_summary=memory_summary,
    )

    prediction_statement_i18n = build_prediction_statement_i18n(
        dominant_scenario=dominant_scenario,
        risk=risk,
        direction=direction,
        confidence=confidence,
        dominant_pattern=str(historical_context.get("dominant_pattern_id") or ""),
        dominant_analog=str(historical_context.get("dominant_analog_id") or ""),
        memory_summary=memory_summary,
        prediction_statement_en=prediction_statement,
    )

    primary_narrative_i18n = choose_primary_narrative_i18n(
        scenario_data=scenario_data,
        primary_narrative=primary_narrative,
    )

    expected_outcomes_i18n = build_expected_outcomes_i18n(
        scenario_data=scenario_data,
        expected_outcomes=expected_outcomes,
    )

    prediction_drivers = build_prediction_drivers(
        trend_data=trend_data,
        signal_data=signal_data,
        scenario_data=scenario_data,
        pattern_data=pattern_data,
        analog_data=analog_data,
        reference_memory=reference_memory_data,
    )

    summary = build_summary(
        direction=direction,
        dominant_scenario=dominant_scenario,
        risk=risk,
        confidence=confidence,
        historical_context=historical_context,
        memory_summary=memory_summary,
    )

    summary_i18n = build_summary_i18n(
        direction=direction,
        dominant_scenario=dominant_scenario,
        risk=risk,
        confidence=confidence,
        historical_context=historical_context,
        memory_summary=memory_summary,
        summary_en=summary,
    )

    risk_flags_raw = scenario_data.get("risk_flags", [])
    if not isinstance(risk_flags_raw, list):
        risk_flags_raw = []

    output = {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "engine_version": "v3_vector_memory_integrated_i18n_phase4_data_i18n",
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "direction": direction,
        "dominant_scenario": dominant_scenario,
        "dominant_scenario_i18n": label_from_map(dominant_scenario, SCENARIO_LABELS),
        "risk": risk,
        "overall_risk": risk,
        "overall_risk_i18n": label_from_map(risk, RISK_LABELS),
        "confidence": confidence,
        "action_bias": action_bias,
        "action_bias_i18n": label_from_map(action_bias, ACTION_BIAS_LABELS),
        "prediction_statement": prediction_statement,
        "prediction_statement_i18n": prediction_statement_i18n,
        "primary_narrative": primary_narrative,
        "primary_narrative_i18n": primary_narrative_i18n,
        "key_drivers": prediction_drivers,
        "monitoring_priorities": monitoring_priorities,
        "expected_outcomes": expected_outcomes,
        "expected_outcomes_i18n": expected_outcomes_i18n,
        "risk_flags": risk_flags_raw,
        "historical_context": historical_context,
        "scenario_bias": scenario_data.get("scenario_bias", {}),
        "reference_memory": build_reference_memory_output(reference_memory_data),
        "summary": summary,
        "summary_i18n": summary_i18n,
    }

    output["key_drivers_ids"] = list(output.get("key_drivers", []))
    output["monitoring_priorities_ids"] = list(output.get("monitoring_priorities", []))
    output["risk_flags_ids"] = list(output.get("risk_flags", []))

    output["key_drivers"] = labelize_list(output.get("key_drivers", []), lang="en")
    output["monitoring_priorities"] = labelize_list(output.get("monitoring_priorities", []), lang="en")
    output["risk_flags"] = labelize_list(output.get("risk_flags", []), lang="en")

    output["key_drivers_i18n"] = finalize_list_i18n(
        output.get("key_drivers", []),
        {
            "en": [labelize(item, "en") for item in output.get("key_drivers_ids", [])],
            "ja": [labelize(item, "ja") for item in output.get("key_drivers_ids", [])],
            "th": [labelize(item, "th") for item in output.get("key_drivers_ids", [])],
        },
    )
    output["monitoring_priorities_i18n"] = finalize_list_i18n(
        output.get("monitoring_priorities", []),
        {
            "en": [labelize(item, "en") for item in output.get("monitoring_priorities_ids", [])],
            "ja": [labelize(item, "ja") for item in output.get("monitoring_priorities_ids", [])],
            "th": [labelize(item, "th") for item in output.get("monitoring_priorities_ids", [])],
        },
    )
    output["risk_flags_i18n"] = finalize_list_i18n(
        output.get("risk_flags", []),
        {
            "en": [labelize(item, "en") for item in output.get("risk_flags_ids", [])],
            "ja": [labelize(item, "ja") for item in output.get("risk_flags_ids", [])],
            "th": [labelize(item, "th") for item in output.get("risk_flags_ids", [])],
        },
    )

    # Backward-compatible aliases for Prediction History consumers.
    output["drivers"] = list(output.get("key_drivers", []))
    output["drivers_i18n"] = list(output.get("key_drivers_i18n", []))
    output["watchpoints"] = list(output.get("monitoring_priorities", []))
    output["watchpoints_i18n"] = list(output.get("monitoring_priorities_i18n", []))
    output["invalidation_conditions"] = list(output.get("risk_flags", []))
    output["invalidation_conditions_i18n"] = list(output.get("risk_flags_i18n", []))

    return output


def save_history(prediction_output: Dict[str, Any]) -> None:
    as_of = str(prediction_output.get("as_of") or datetime.now().strftime("%Y-%m-%d"))
    history_dir = PREDICTION_DIR / "history" / as_of
    write_json(history_dir / "prediction.json", prediction_output)


def main() -> None:
    trend_data = load_json(TREND_LATEST_PATH)
    signal_data = load_json(SIGNAL_LATEST_PATH)
    scenario_data = load_json(SCENARIO_LATEST_PATH)
    pattern_data = load_json(HISTORICAL_PATTERN_LATEST_PATH)
    analog_data = load_json(HISTORICAL_ANALOG_LATEST_PATH)
    direct_reference_memory = load_json(REFERENCE_MEMORY_LATEST_PATH)

    scenario_reference_memory = extract_reference_memory_from_scenario(scenario_data)
    reference_memory_data = merge_reference_memory(
        scenario_reference_memory=scenario_reference_memory,
        direct_reference_memory=direct_reference_memory,
    )

    prediction_output = build_prediction_output(
        trend_data=trend_data,
        signal_data=signal_data,
        scenario_data=scenario_data,
        pattern_data=pattern_data,
        analog_data=analog_data,
        reference_memory_data=reference_memory_data,
    )

    write_json(PREDICTION_LATEST_PATH, prediction_output)
    save_history(prediction_output)

    print(f"[prediction_engine] wrote {PREDICTION_LATEST_PATH}")
    print(
        "[prediction_engine] dominant="
        f"{prediction_output.get('dominant_scenario')} "
        "risk="
        f"{prediction_output.get('risk')} "
        "confidence="
        f"{prediction_output.get('confidence')}"
    )
    print(
        "[prediction_engine] reference_memory="
        f"{prediction_output.get('reference_memory', {}).get('status')} "
        f"summary={prediction_output.get('reference_memory', {}).get('summary')}"
    )


if __name__ == "__main__":
    main()
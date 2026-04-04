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
SENTIMENT_LATEST_PATH = ROOT / "data" / "world_politics" / "analysis" / "sentiment_latest.json"

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


GENERIC_SEMANTIC_TAGS = {
    "",
    "general",
    "medium",
    "low",
    "high",
    "critical",
    "derived",
    "risk",
    "news",
    "headline",
    "intensity",
    "health",
    "confidence",
    "sentiment",
}

LOW_SIGNAL_NOISE_TAGS = {
    "overall_direction_falling",
    "risk_level_critical",
    "risk_trend_low",
    "sentiment_trend_falling",
    "pipeline_stress",
    "pipeline_health",
    "health_signals_accelerating",
    "confidence_moderate",
    "confidence_trend_stable",
}

SEMANTIC_CATEGORY_LABELS = {
    "themes": {
        "en": "themes",
        "ja": "テーマ",
        "th": "ธีม",
    },
    "signals": {
        "en": "signals",
        "ja": "シグナル",
        "th": "สัญญาณ",
    },
    "risk_drivers": {
        "en": "risk drivers",
        "ja": "リスク要因",
        "th": "ปัจจัยเสี่ยง",
    },
    "impacts": {
        "en": "impact paths",
        "ja": "波及経路",
        "th": "เส้นทางผลกระทบ",
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


PREDICTION_DRIVER_NOISE = {
    "guarded",
    "stable",
    "high",
    "critical",
    "low",
    "balanced",
    "defensive",
    "constructive",
    "health_degradation",
    "health deterioration",
    "stabilization",
    "pressure_easing",
    "pressure easing",
    "event_density_high",
    "event_density_rising",
    "headline_surge",
    "headline_intensity_accelerating",
    "risk_level_critical",
    "overall_direction_falling",
    "overall direction falling",
}

PREDICTION_MONITORING_NOISE = {
    "banking_stress",
    "banking stress",
}


def normalize_token_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    return unique_preserve_order([normalize_text(x) for x in values if normalize_text(x)])


def filter_prediction_driver_tokens(values: List[str]) -> List[str]:
    allowed: List[str] = []
    for raw in values or []:
        token = normalize_text(raw)
        if not token or token in PREDICTION_DRIVER_NOISE:
            continue
        if is_generic_semantic_tag(token) or is_low_signal_noise_tag(token):
            continue
        allowed.append(token)
    return unique_preserve_order(allowed)


def get_scenario_watchpoint_roles(scenario_data: Dict[str, Any]) -> Dict[str, List[str]]:
    roles = scenario_data.get("watchpoint_roles", {})
    if not isinstance(roles, dict):
        return {"escalation": [], "persistence": [], "stabilization": []}
    return {
        "escalation": normalize_token_list(roles.get("escalation")),
        "persistence": normalize_token_list(roles.get("persistence")),
        "stabilization": normalize_token_list(roles.get("stabilization")),
    }


def get_structured_drivers(scenario_data: Dict[str, Any]) -> Dict[str, List[str]]:
    structured = scenario_data.get("structured_drivers", {})
    if not isinstance(structured, dict):
        return {
            "core_drivers": [],
            "pressure_modifiers": [],
            "trend_context": [],
            "downstream_risks": [],
        }
    return {
        "core_drivers": normalize_token_list(structured.get("core_drivers")),
        "pressure_modifiers": normalize_token_list(structured.get("pressure_modifiers")),
        "trend_context": normalize_token_list(structured.get("trend_context")),
        "downstream_risks": normalize_token_list(structured.get("downstream_risks")),
    }


def render_label_list(values: List[str], lang: str = "en", limit: int = 3) -> str:
    items = [labelize(x, lang=lang) for x in values[:limit] if str(x).strip()]
    if not items:
        return ""
    if lang == "ja":
        return "・".join(items)
    return ", ".join(items)


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




def is_generic_semantic_tag(value: Any) -> bool:
    tag = normalize_text(value)
    return (not tag) or tag in GENERIC_SEMANTIC_TAGS


def is_low_signal_noise_tag(value: Any) -> bool:
    tag = normalize_text(value)
    return tag in LOW_SIGNAL_NOISE_TAGS


def pick_sentiment_today(sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
    today = sentiment_data.get("today", {})
    return today if isinstance(today, dict) else {}


def extract_semantic_ids(today: Dict[str, Any], field_name: str) -> List[str]:
    raw = today.get(field_name, [])
    if not isinstance(raw, list):
        return []
    items: List[str] = []
    for item in raw:
        tag = normalize_text(item)
        if is_generic_semantic_tag(tag):
            continue
        items.append(tag)
    return unique_preserve_order(items)


def extract_semantic_i18n(today: Dict[str, Any], field_name: str, fallback_ids: List[str]) -> Dict[str, List[str]]:
    raw = ensure_lang_list_map(today.get(field_name))
    source_key = field_name.replace("_i18n", "")
    source_ids = today.get(source_key, [])
    if raw and isinstance(source_ids, list):
        aligned = {"en": [], "ja": [], "th": []}
        for idx, raw_id in enumerate(source_ids):
            normalized_id = normalize_text(raw_id)
            if normalized_id not in fallback_ids:
                continue
            aligned["en"].append(labelize(raw_id, lang="en"))
            aligned["ja"].append((raw.get("ja") or [])[idx] if idx < len(raw.get("ja") or []) else labelize(raw_id, lang="ja"))
            aligned["th"].append((raw.get("th") or [])[idx] if idx < len(raw.get("th") or []) else labelize(raw_id, lang="th"))
        if aligned["en"]:
            return aligned
    return {
        "en": [labelize(x, lang="en") for x in fallback_ids],
        "ja": [labelize(x, lang="ja") for x in fallback_ids],
        "th": [labelize(x, lang="th") for x in fallback_ids],
    }


def collect_sentiment_semantic_context(sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
    today = pick_sentiment_today(sentiment_data)

    theme_ids = extract_semantic_ids(today, "top_theme_tags")[:3]
    signal_ids = extract_semantic_ids(today, "top_signal_tags")[:3]
    risk_driver_ids = extract_semantic_ids(today, "top_risk_drivers")[:3]
    impact_ids = extract_semantic_ids(today, "top_impact_tags")[:3]

    return {
        "themes": {
            "ids": theme_ids,
            "i18n": extract_semantic_i18n(today, "top_theme_tags_i18n", theme_ids),
        },
        "signals": {
            "ids": signal_ids,
            "i18n": extract_semantic_i18n(today, "top_signal_tags_i18n", signal_ids),
        },
        "risk_drivers": {
            "ids": risk_driver_ids,
            "i18n": extract_semantic_i18n(today, "top_risk_drivers_i18n", risk_driver_ids),
        },
        "impacts": {
            "ids": impact_ids,
            "i18n": extract_semantic_i18n(today, "top_impact_tags_i18n", impact_ids),
        },
        "sentiment_label": normalize_text(today.get("sentiment_label") or today.get("sentiment")),
        "mixed_share": round(
            safe_float((today.get("label_counts") or {}).get("mixed", 0.0))
            / max(safe_float(today.get("articles", 0.0), 1.0), 1.0),
            4,
        ) if isinstance(today.get("label_counts"), dict) else 0.0,
    }


def build_semantic_summary_lines(semantic_context: Dict[str, Any]) -> Dict[str, str]:
    themes = semantic_context.get("themes", {})
    signals = semantic_context.get("signals", {})
    risk_drivers = semantic_context.get("risk_drivers", {})
    impacts = semantic_context.get("impacts", {})

    theme_i18n = ensure_lang_list_map(themes.get("i18n"))
    signal_i18n = ensure_lang_list_map(signals.get("i18n"))
    risk_driver_i18n = ensure_lang_list_map(risk_drivers.get("i18n"))
    impact_i18n = ensure_lang_list_map(impacts.get("i18n"))

    clauses = {"en": "", "ja": "", "th": ""}

    if theme_i18n.get("en"):
        clauses["en"] += " Semantic backdrop is centered on " + ", ".join(theme_i18n["en"][:2]) + "."
        clauses["ja"] += " 意味的な地合いは " + "・".join(theme_i18n["ja"][:2]) + " を中心に形成されている。"
        clauses["th"] += " ภาพรวมเชิงความหมายกำลังขับเคลื่อนด้วย " + " และ ".join(theme_i18n["th"][:2]) + "."

    if signal_i18n.get("en"):
        clauses["en"] += " Active signals are led by " + ", ".join(signal_i18n["en"][:2]) + "."
        clauses["ja"] += " 主なアクティブシグナルは " + "・".join(signal_i18n["ja"][:2]) + " である。"
        clauses["th"] += " สัญญาณที่เด่นที่สุดคือ " + " และ ".join(signal_i18n["th"][:2]) + "."

    if risk_driver_i18n.get("en"):
        clauses["en"] += " Main risk drivers are " + ", ".join(risk_driver_i18n["en"][:2]) + "."
        clauses["ja"] += " 主なリスク要因は " + "・".join(risk_driver_i18n["ja"][:2]) + " である。"
        clauses["th"] += " ปัจจัยเสี่ยงหลักคือ " + " และ ".join(risk_driver_i18n["th"][:2]) + "."

    if impact_i18n.get("en"):
        clauses["en"] += " Likely transmission runs through " + ", ".join(impact_i18n["en"][:2]) + "."
        clauses["ja"] += " 波及経路としては " + "・".join(impact_i18n["ja"][:2]) + " が意識される。"
        clauses["th"] += " เส้นทางผลกระทบที่น่าจับตาคือ " + " และ ".join(impact_i18n["th"][:2]) + "."

    return {lang: text.strip() for lang, text in clauses.items()}



def build_primary_narrative(
    scenario_data: Dict[str, Any],
    semantic_context: Dict[str, Any],
) -> str:
    dominant = normalize_text(scenario_data.get("dominant_scenario")) or "base_case"
    risk = normalize_text(scenario_data.get("risk")) or "guarded"

    structured = get_structured_drivers(scenario_data)
    roles = get_scenario_watchpoint_roles(scenario_data)
    scenario_bias = collect_scenario_probabilities(scenario_data)

    core_drivers = filter_prediction_driver_tokens(structured.get("core_drivers", []))[:3]
    modifiers = filter_prediction_driver_tokens(structured.get("pressure_modifiers", []))[:2]
    propagation = normalize_token_list(scenario_data.get("expected_outcomes"))[:3]
    escalation = roles.get("escalation", [])[:3]

    dominant_label = labelize(dominant, lang="en")
    risk_label = labelize(risk, lang="en")
    driver_text = render_label_list(core_drivers, lang="en", limit=3)
    modifier_text = render_label_list(modifiers, lang="en", limit=2)
    propagation_text = render_label_list(propagation, lang="en", limit=3)
    escalation_text = render_label_list(escalation, lang="en", limit=3)

    base = f"{dominant_label} remains the lead operating path under {risk_label} conditions."

    base_prob = safe_float(scenario_bias.get("base_case"))
    worst_prob = safe_float(scenario_bias.get("worst_case"))
    best_prob = safe_float(scenario_bias.get("best_case"))
    if base_prob or worst_prob or best_prob:
        if worst_prob >= max(0.25, base_prob - 0.10):
            base += (
                f" The branch balance still carries material tail risk "
                f"(base {base_prob:.2f} vs worst {worst_prob:.2f}; best {best_prob:.2f})."
            )
        else:
            base += (
                f" Scenario balance still favors the base path "
                f"(base {base_prob:.2f}; worst {worst_prob:.2f}; best {best_prob:.2f})."
            )

    if driver_text:
        base += f" Core pressure is concentrated in {driver_text}."
    if modifier_text:
        base += f" Modifiers such as {modifier_text} are preventing a clean normalization."
    if propagation_text:
        base += f" The most likely transmission path runs through {propagation_text}."
    if escalation_text:
        base += f" A worse turn becomes more likely if {escalation_text} deteriorate together."

    semantic_drivers = filter_prediction_driver_tokens(normalize_token_list((semantic_context.get("risk_drivers") or {}).get("ids")))[:2]
    semantic_impacts = normalize_token_list((semantic_context.get("impacts") or {}).get("ids"))[:2]
    if semantic_drivers:
        base += f" Outside the scenario core, semantic pressure is also building in {render_label_list(semantic_drivers, 'en', 2)}."
    if semantic_impacts:
        base += f" That keeps spillover risk focused on {render_label_list(semantic_impacts, 'en', 2)}."

    historical_context = scenario_data.get("historical_context", {})
    if isinstance(historical_context, dict):
        pattern = historical_context.get("dominant_pattern")
        analog = historical_context.get("dominant_analog")
        pattern_label = labelize(pattern, lang="en")
        analog_label = labelize(analog, lang="en")
        if pattern_label or analog_label:
            if pattern_label and analog_label:
                base += f" Historically, the structure is closest to {pattern_label} and resembles {analog_label}."
            elif pattern_label:
                base += f" Historically, the structure is closest to {pattern_label}."
            else:
                base += f" Historically, the structure resembles {analog_label}."

    return base.strip()

def build_primary_narrative_i18n(
    scenario_data: Dict[str, Any],
    primary_narrative: str,
    semantic_context: Dict[str, Any],
) -> Dict[str, str]:
    dominant = normalize_text(scenario_data.get("dominant_scenario")) or "base_case"
    risk = normalize_text(scenario_data.get("risk")) or "guarded"

    structured = get_structured_drivers(scenario_data)
    roles = get_scenario_watchpoint_roles(scenario_data)

    core_drivers = filter_prediction_driver_tokens(structured.get("core_drivers", []))[:3]
    modifiers = filter_prediction_driver_tokens(structured.get("pressure_modifiers", []))[:2]
    propagation = normalize_token_list(scenario_data.get("expected_outcomes"))[:3]
    escalation = roles.get("escalation", [])[:3]

    dominant_i18n = label_from_map(dominant, SCENARIO_LABELS)
    risk_i18n = label_from_map(risk, RISK_LABELS)

    en = f"{labelize(dominant, 'en')} remains the working path under {labelize(risk, 'en')} conditions."
    ja = f"{dominant_i18n['ja']} が引き続き主経路であり、条件は {risk_i18n['ja']} にある。"
    th = f"{dominant_i18n['th']} ยังคงเป็นเส้นทางหลักภายใต้ภาวะ {risk_i18n['th']}."

    if core_drivers:
        en += f" Core pressure is still concentrated in {render_label_list(core_drivers, 'en', 3)}."
        ja += f" 中核圧力はなお {render_label_list(core_drivers, 'ja', 3)} に集中している。"
        th += f" แรงกดดันหลักยังกระจุกอยู่ที่ {render_label_list(core_drivers, 'th', 3)}."
    if modifiers:
        en += f" Modifiers such as {render_label_list(modifiers, 'en', 2)} keep normalization incomplete."
        ja += f" {render_label_list(modifiers, 'ja', 2)} のような修飾要因が正常化を不完全なままにしている。"
        th += f" ตัวเสริมอย่าง {render_label_list(modifiers, 'th', 2)} ทำให้การกลับสู่ภาวะปกติยังไม่สมบูรณ์."
    if propagation:
        en += f" The main downside propagation runs through {render_label_list(propagation, 'en', 3)}."
        ja += f" 主な下方波及経路は {render_label_list(propagation, 'ja', 3)} である。"
        th += f" การลุกลามขาลงหลักเกิดผ่าน {render_label_list(propagation, 'th', 3)}."
    if escalation:
        en += f" A worse turn is most likely if {render_label_list(escalation, 'en', 3)} deteriorate together."
        ja += f" {render_label_list(escalation, 'ja', 3)} が同時に悪化すると、さらに悪い分岐へ移りやすい。"
        th += f" หาก {render_label_list(escalation, 'th', 3)} แย่ลงพร้อมกัน โอกาสเข้าสู่กรณีที่แย่กว่าจะสูงขึ้น."

    historical_context = scenario_data.get("historical_context", {})
    if isinstance(historical_context, dict):
        pattern = historical_context.get("dominant_pattern")
        analog = historical_context.get("dominant_analog")
        pattern_i18n = labelize_i18n(pattern)
        analog_i18n = labelize_i18n(analog)
        if pattern_i18n.get("en") or analog_i18n.get("en"):
            if pattern_i18n.get("en") and analog_i18n.get("en"):
                en += f" Historically, the structure is closest to {pattern_i18n['en']} and resembles {analog_i18n['en']}."
                ja += f" 歴史的には {pattern_i18n['ja']} に最も近く、{analog_i18n['ja']} に似た輪郭を持つ。"
                th += f" ในเชิงประวัติศาสตร์ โครงสร้างนี้ใกล้กับ {pattern_i18n['th']} และคล้าย {analog_i18n['th']}."
            elif pattern_i18n.get("en"):
                en += f" Historically, the structure is closest to {pattern_i18n['en']}."
                ja += f" 歴史的には {pattern_i18n['ja']} に最も近い。"
                th += f" ในเชิงประวัติศาสตร์ โครงสร้างนี้ใกล้กับ {pattern_i18n['th']} มากที่สุด."
            else:
                en += f" Historically, the structure resembles {analog_i18n['en']}."
                ja += f" 歴史的には {analog_i18n['ja']} に似た輪郭を持つ。"
                th += f" ในเชิงประวัติศาสตร์ โครงสร้างนี้คล้าย {analog_i18n['th']}."

    return finalize_text_i18n(primary_narrative, {"en": en, "ja": ja, "th": th})


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
    semantic_context: Dict[str, Any],
    scenario_probabilities: Dict[str, float],
) -> str:
    dominant_pattern_label = labelize(dominant_pattern, lang="en")
    dominant_analog_label = labelize(dominant_analog, lang="en")
    semantic_lines = build_semantic_summary_lines(semantic_context)

    base_prob = safe_float(scenario_probabilities.get("base_case"))
    worst_prob = safe_float(scenario_probabilities.get("worst_case"))
    best_prob = safe_float(scenario_probabilities.get("best_case"))

    sentence = (
        f"Primary outlook remains {labelize(dominant_scenario, lang='en')} "
        f"with {labelize(risk, lang='en')} risk and "
        f"{labelize(direction, lang='en')} directional bias at confidence {confidence:.2f}."
    )

    if base_prob or worst_prob or best_prob:
        if worst_prob >= max(0.25, base_prob - 0.10):
            sentence += (
                f" Downside remains live because worst-case weight ({worst_prob:.2f}) "
                f"is still close to the base path ({base_prob:.2f}), while upside stays capped at {best_prob:.2f}."
            )
        else:
            sentence += (
                f" Scenario balance still favors the base path ({base_prob:.2f}) "
                f"over worst-case ({worst_prob:.2f}) and best-case ({best_prob:.2f})."
            )

    semantic_en = semantic_lines.get("en", "").strip()
    if semantic_en:
        sentence += f" {semantic_en}"

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
    semantic_context: Dict[str, Any],
    scenario_probabilities: Dict[str, float],
) -> Dict[str, str]:
    scenario_labels = label_from_map(dominant_scenario, SCENARIO_LABELS)
    risk_labels = label_from_map(risk, RISK_LABELS)
    direction_labels = label_from_map(direction, DIRECTION_LABELS)
    dominant_pattern_labels = labelize_i18n(dominant_pattern)
    dominant_analog_labels = labelize_i18n(dominant_analog)
    semantic_lines = build_semantic_summary_lines(semantic_context)

    base_prob = safe_float(scenario_probabilities.get("base_case"))
    worst_prob = safe_float(scenario_probabilities.get("worst_case"))
    best_prob = safe_float(scenario_probabilities.get("best_case"))

    en = (
        f"Primary outlook remains {scenario_labels['en']} with {risk_labels['en']} risk and "
        f"{direction_labels['en']} directional bias at confidence {confidence:.2f}."
    )
    ja = (
        f"主要見通しは {scenario_labels['ja']} を維持している。"
        f"リスクは {risk_labels['ja']}、方向性は {direction_labels['ja']}、"
        f"信頼度は {confidence:.2f}。"
    )
    th = (
        f"มุมมองหลักยังคงเป็น {scenario_labels['th']} "
        f"โดยมีระดับความเสี่ยง {risk_labels['th']} และทิศทาง {direction_labels['th']} "
        f"ที่ความเชื่อมั่น {confidence:.2f}."
    )

    if base_prob or worst_prob or best_prob:
        if worst_prob >= max(0.25, base_prob - 0.10):
            en += (
                f" Downside remains live because worst-case weight ({worst_prob:.2f}) "
                f"is still close to the base path ({base_prob:.2f}), while upside stays capped at {best_prob:.2f}."
            )
            ja += (
                f" 最悪ケース比重 {worst_prob:.2f} が基本経路 {base_prob:.2f} にまだ近く、"
                f"上振れ余地は {best_prob:.2f} にとどまるため、下方尾部リスクはなお生きている。"
            )
            th += (
                f" น้ำหนักกรณีเลวร้าย {worst_prob:.2f} ยังใกล้กับกรณีฐาน {base_prob:.2f} "
                f"ขณะที่โอกาสขาขึ้นถูกจำกัดที่ {best_prob:.2f} จึงยังต้องเฝ้าระวังความเสี่ยงด้านลบ."
            )
        else:
            en += (
                f" Scenario balance still favors the base path ({base_prob:.2f}) "
                f"over worst-case ({worst_prob:.2f}) and best-case ({best_prob:.2f})."
            )
            ja += (
                f" シナリオ配分は、最悪ケース {worst_prob:.2f} と最良ケース {best_prob:.2f} を上回り、"
                f"基本経路 {base_prob:.2f} を優位としている。"
            )
            th += (
                f" สมดุลของสถานการณ์ยังให้น้ำหนักกรณีฐาน {base_prob:.2f} สูงกว่า "
                f"กรณีเลวร้าย {worst_prob:.2f} และกรณีดีที่สุด {best_prob:.2f}."
            )

    if semantic_lines.get("en"):
        en += f" {semantic_lines['en']}"
        ja += f" {semantic_lines['ja']}"
        th += f" {semantic_lines['th']}"

    if dominant_pattern_labels.get("en") and dominant_analog_labels.get("en"):
        en += (
            f" Historical support is led by pattern {dominant_pattern_labels['en']} "
            f"and analog {dominant_analog_labels['en']}."
        )
        ja += f" 歴史的裏付けは {dominant_pattern_labels['ja']} と {dominant_analog_labels['ja']} が主導している。"
        th += f" แรงหนุนจากประวัติศาสตร์นำโดยรูปแบบ {dominant_pattern_labels['th']} และกรณีเทียบเคียง {dominant_analog_labels['th']}."
    elif dominant_pattern_labels.get("en"):
        en += f" Historical support is led by pattern {dominant_pattern_labels['en']}."
        ja += f" 歴史的裏付けは {dominant_pattern_labels['ja']} が主導している。"
        th += f" แรงหนุนจากประวัติศาสตร์นำโดยรูปแบบ {dominant_pattern_labels['th']}."
    elif dominant_analog_labels.get("en"):
        en += f" Historical support is led by analog {dominant_analog_labels['en']}."
        ja += f" 歴史的裏付けは {dominant_analog_labels['ja']} が主導している。"
        th += f" แรงหนุนจากประวัติศาสตร์นำโดยกรณีเทียบเคียง {dominant_analog_labels['th']}."

    if memory_summary:
        en += f" Memory context: {memory_summary}."
        ja += f" 記憶参照文脈: {memory_summary}。"
        th += f" บริบทจากหน่วยความจำ: {memory_summary}."

    return finalize_text_i18n(prediction_statement_en, {
        "en": en.strip(),
        "ja": ja.strip(),
        "th": th.strip(),
    })

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
    roles = get_scenario_watchpoint_roles(scenario_data)
    priorities: List[str] = []

    priorities.extend(roles.get("escalation", [])[:4])
    priorities.extend(roles.get("persistence", [])[:3])
    priorities.extend(roles.get("stabilization", [])[:2])

    for item in normalize_token_list(scenario_data.get("watchpoints"))[:6]:
        priorities.append(item)

    historical_context = scenario_data.get("historical_context", {})
    if isinstance(historical_context, dict):
        priorities.extend(normalize_token_list(historical_context.get("historical_watchpoints"))[:4])

    matched_patterns = pattern_data.get("matched_patterns", [])
    if isinstance(matched_patterns, list):
        for item in matched_patterns[:1]:
            if isinstance(item, dict):
                priorities.extend(normalize_token_list(item.get("watchpoints"))[:2])

    top_analogs = analog_data.get("top_analogs", [])
    if isinstance(top_analogs, list):
        for item in top_analogs[:1]:
            if isinstance(item, dict):
                priorities.extend(normalize_token_list(item.get("watchpoints"))[:2])

    cleaned = []
    for token in unique_preserve_order([x for x in priorities if x]):
        if token in PREDICTION_MONITORING_NOISE:
            continue
        cleaned.append(token)
    return cleaned[:8]



def build_prediction_drivers(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
    reference_memory: Dict[str, Any],
    semantic_context: Dict[str, Any],
) -> List[str]:
    structured = get_structured_drivers(scenario_data)
    drivers: List[str] = []

    drivers.extend(filter_prediction_driver_tokens(structured.get("core_drivers", []))[:3])
    drivers.extend(filter_prediction_driver_tokens(structured.get("pressure_modifiers", []))[:2])

    risk_driver_ids = normalize_token_list((semantic_context.get("risk_drivers") or {}).get("ids"))
    for token in filter_prediction_driver_tokens(risk_driver_ids):
        if token not in drivers:
            drivers.append(token)
        if len(drivers) >= 6:
            break

    if len(drivers) < 4:
        for token in filter_prediction_driver_tokens(normalize_token_list(scenario_data.get("key_drivers"))):
            if token not in drivers:
                drivers.append(token)
            if len(drivers) >= 6:
                break

    return unique_preserve_order(drivers)[:6]


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
    semantic_context: Dict[str, Any],
) -> str:
    base = (
        f"Prediction remains {labelize(dominant_scenario, lang='en')} under "
        f"{labelize(risk, lang='en')} risk with a {labelize(direction, lang='en')} bias "
        f"at confidence {confidence:.2f}."
    )

    semantic_en = build_semantic_summary_lines(semantic_context).get("en", "").strip()
    if semantic_en:
        base += f" {semantic_en}"

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
    semantic_context: Dict[str, Any],
) -> Dict[str, str]:
    direction_labels = label_from_map(direction, DIRECTION_LABELS)
    scenario_labels = label_from_map(dominant_scenario, SCENARIO_LABELS)
    risk_labels = label_from_map(risk, RISK_LABELS)
    historical_summary_i18n = ensure_lang_map(historical_context.get("summary_i18n"))
    semantic_lines = build_semantic_summary_lines(semantic_context)

    en = (
        f"Prediction remains {scenario_labels['en']} under {risk_labels['en']} risk "
        f"with a {direction_labels['en']} bias at confidence {confidence:.2f}."
    )
    ja = (
        f"予測は {scenario_labels['ja']} を維持している。"
        f"リスクは {risk_labels['ja']}、方向性は {direction_labels['ja']}、"
        f"信頼度は {confidence:.2f}。"
    )
    th = (
        f"การคาดการณ์ยังคงเป็น {scenario_labels['th']} "
        f"ภายใต้ความเสี่ยงระดับ {risk_labels['th']} "
        f"พร้อมทิศทาง {direction_labels['th']} "
        f"ที่ความเชื่อมั่น {confidence:.2f}."
    )

    if semantic_lines.get("en"):
        en += f" {semantic_lines['en']}".rstrip()
        ja += f" {semantic_lines['ja']}".rstrip()
        th += f" {semantic_lines['th']}".rstrip()

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


def collect_scenario_probabilities(scenario_data: Dict[str, Any]) -> Dict[str, float]:
    scenario_bias = scenario_data.get("scenario_bias", {})
    out = {
        "best_case": 0.0,
        "base_case": 0.0,
        "worst_case": 0.0,
    }

    if isinstance(scenario_bias, dict):
        for key in list(out.keys()):
            out[key] = round(clamp01(safe_float(scenario_bias.get(key))), 4)

    scenarios = scenario_data.get("scenarios", [])
    if isinstance(scenarios, list):
        for item in scenarios:
            if not isinstance(item, dict):
                continue
            scenario_id = normalize_text(item.get("scenario_id"))
            if scenario_id not in out:
                continue
            value = item.get("probability")
            if value is None:
                value = item.get("weight")
            if value is None:
                continue
            out[scenario_id] = round(clamp01(safe_float(value)), 4)

    total = sum(out.values())
    if total > 1.25:
        return {k: round(v / total, 4) for k, v in out.items()}
    return out


def classify_scenario_balance(scenario_probabilities: Dict[str, float]) -> str:
    base_prob = safe_float(scenario_probabilities.get("base_case"))
    worst_prob = safe_float(scenario_probabilities.get("worst_case"))
    best_prob = safe_float(scenario_probabilities.get("best_case"))

    if worst_prob >= max(0.35, base_prob):
        return "downside_pressure"
    if worst_prob >= max(0.25, base_prob - 0.10):
        return "material_tail_risk"
    if base_prob >= max(0.45, worst_prob + 0.12) and best_prob <= 0.25:
        return "base_case_control"
    if best_prob >= max(0.30, worst_prob + 0.08):
        return "constructive_optional"
    return "balanced_range"


def build_driver_structure(
    scenario_data: Dict[str, Any],
    semantic_context: Dict[str, Any],
    prediction_drivers: List[str],
    historical_context: Dict[str, Any],
) -> Dict[str, List[str]]:
    structured = get_structured_drivers(scenario_data)
    risk_driver_ids = filter_prediction_driver_tokens(normalize_token_list((semantic_context.get("risk_drivers") or {}).get("ids")))[:3]
    impact_ids = normalize_token_list((semantic_context.get("impacts") or {}).get("ids"))[:3]

    historical: List[str] = []
    pattern_id = normalize_text(historical_context.get("dominant_pattern_id") or historical_context.get("dominant_pattern"))
    analog_id = normalize_text(historical_context.get("dominant_analog_id") or historical_context.get("dominant_analog"))
    if pattern_id:
        historical.append(pattern_id)
    if analog_id:
        historical.append(analog_id)

    return {
        "core": unique_preserve_order(filter_prediction_driver_tokens(structured.get("core_drivers", []))[:4]),
        "modifiers": unique_preserve_order(filter_prediction_driver_tokens(structured.get("pressure_modifiers", []))[:3]),
        "semantic": unique_preserve_order(risk_driver_ids[:3]),
        "transmission": unique_preserve_order(impact_ids[:3]),
        "historical": unique_preserve_order(historical[:2]),
        "flat": unique_preserve_order([normalize_text(x) for x in prediction_drivers if normalize_text(x)])[:6],
    }


def build_driver_structure_i18n(driver_structure: Dict[str, List[str]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, values in driver_structure.items():
        out[key] = {
            "en": [labelize(item, "en") for item in values],
            "ja": [labelize(item, "ja") for item in values],
            "th": [labelize(item, "th") for item in values],
        }
    return out


DECISION_POSTURE_LABELS = {
    "protect_capital_now": {
        "en": "protect capital now",
        "ja": "資本保全を最優先",
        "th": "ปกป้องเงินทุนเป็นอันดับแรก",
    },
    "operate_defensively": {
        "en": "operate defensively",
        "ja": "防御姿勢で運用",
        "th": "ดำเนินการแบบตั้งรับ",
    },
    "base_case_with_tail_hedge": {
        "en": "base case with tail hedge",
        "ja": "基本線維持＋尾部ヘッジ",
        "th": "ยึดกรณีฐานพร้อมป้องกันความเสี่ยงปลายหาง",
    },
    "selective_reengagement": {
        "en": "selective re-engagement",
        "ja": "限定的な再関与",
        "th": "กลับเข้าดำเนินการอย่างเลือกสรร",
    },
    "wait_for_resolution": {
        "en": "wait for resolution",
        "ja": "解像度待ち",
        "th": "รอความชัดเจนเพิ่มเติม",
    },
    "monitor_and_adapt": {
        "en": "monitor and adapt",
        "ja": "監視しつつ調整",
        "th": "ติดตามและปรับตัว",
    },
}


SCENARIO_BALANCE_LABELS = {
    "downside_pressure": {
        "en": "downside pressure",
        "ja": "下方圧力優勢",
        "th": "แรงกดดันด้านลบเด่น",
    },
    "material_tail_risk": {
        "en": "material tail risk",
        "ja": "無視できない尾部リスク",
        "th": "มีความเสี่ยงปลายหางอย่างมีนัยสำคัญ",
    },
    "base_case_control": {
        "en": "base-case control",
        "ja": "基本ケース優位",
        "th": "กรณีฐานยังควบคุมภาพรวม",
    },
    "constructive_optional": {
        "en": "constructive optionality",
        "ja": "建設的な上振れ余地",
        "th": "มีทางเลือกเชิงบวก",
    },
    "balanced_range": {
        "en": "balanced range",
        "ja": "均衡レンジ",
        "th": "สมดุลในกรอบ",
    },
}


def build_decision_posture(
    dominant_scenario: str,
    risk: str,
    direction: str,
    confidence: float,
    scenario_balance: str,
    action_bias: str,
) -> str:
    if dominant_scenario == "worst_case" or risk in {"critical", "high"}:
        return "protect_capital_now"
    if action_bias == "defensive" and scenario_balance in {"downside_pressure", "material_tail_risk"}:
        return "operate_defensively"
    if scenario_balance == "material_tail_risk":
        return "base_case_with_tail_hedge"
    if scenario_balance == "base_case_control" and confidence >= 0.68 and direction in {"stabilizing", "stable_to_guarded"}:
        return "selective_reengagement"
    if confidence < 0.45:
        return "wait_for_resolution"
    return "monitor_and_adapt"


def build_decision_summary(
    posture: str,
    dominant_scenario: str,
    scenario_balance: str,
    scenario_probabilities: Dict[str, float],
    monitoring_priorities: List[str],
    expected_outcomes: List[str],
) -> str:
    posture_label = label_from_map(posture, DECISION_POSTURE_LABELS)["en"]
    dominant_label = label_from_map(dominant_scenario, SCENARIO_LABELS)["en"]
    balance_label = label_from_map(scenario_balance, SCENARIO_BALANCE_LABELS)["en"]

    base_prob = safe_float(scenario_probabilities.get("base_case"))
    worst_prob = safe_float(scenario_probabilities.get("worst_case"))
    best_prob = safe_float(scenario_probabilities.get("best_case"))

    summary = (
        f"Decision posture: {posture_label}. Operate on {dominant_label} as the active plan, "
        f"but treat the branch mix as {balance_label} (best {best_prob:.2f} / base {base_prob:.2f} / worst {worst_prob:.2f})."
    )
    if monitoring_priorities:
        summary += f" Escalate if {render_label_list(monitoring_priorities, 'en', 3)} worsen together."
    if expected_outcomes:
        summary += f" Expected spillover is most visible through {render_label_list(expected_outcomes, 'en', 3)}."
    return summary.strip()


def build_decision_summary_i18n(
    posture: str,
    dominant_scenario: str,
    scenario_balance: str,
    scenario_probabilities: Dict[str, float],
    monitoring_priorities: List[str],
    expected_outcomes: List[str],
    decision_summary_en: str,
) -> Dict[str, str]:
    posture_labels = label_from_map(posture, DECISION_POSTURE_LABELS)
    dominant_labels = label_from_map(dominant_scenario, SCENARIO_LABELS)
    balance_labels = label_from_map(scenario_balance, SCENARIO_BALANCE_LABELS)

    base_prob = safe_float(scenario_probabilities.get("base_case"))
    worst_prob = safe_float(scenario_probabilities.get("worst_case"))
    best_prob = safe_float(scenario_probabilities.get("best_case"))

    en = (
        f"Decision posture: {posture_labels['en']}. Operate on {dominant_labels['en']} as the active plan, "
        f"but treat the branch mix as {balance_labels['en']} (best {best_prob:.2f} / base {base_prob:.2f} / worst {worst_prob:.2f})."
    )
    ja = (
        f"意思決定姿勢は「{posture_labels['ja']}」。運用上の主計画は {dominant_labels['ja']} とするが、"
        f"分岐バランスは「{balance_labels['ja']}」として扱う（最良 {best_prob:.2f} / 基本 {base_prob:.2f} / 最悪 {worst_prob:.2f}）。"
    )
    th = (
        f"ท่าทีการตัดสินใจคือ {posture_labels['th']} โดยใช้ {dominant_labels['th']} เป็นแผนหลัก "
        f"แต่ต้องมองสมดุลของสถานการณ์ว่าเป็น {balance_labels['th']} (ดีที่สุด {best_prob:.2f} / ฐาน {base_prob:.2f} / แย่ที่สุด {worst_prob:.2f})."
    )

    if monitoring_priorities:
        en += f" Escalate if {render_label_list(monitoring_priorities, 'en', 3)} worsen together."
        ja += f" {render_label_list(monitoring_priorities, 'ja', 3)} が同時に悪化したら防御を強める。"
        th += f" หาก {render_label_list(monitoring_priorities, 'th', 3)} แย่ลงพร้อมกัน ให้เพิ่มระดับการป้องกัน."
    if expected_outcomes:
        en += f" Expected spillover is most visible through {render_label_list(expected_outcomes, 'en', 3)}."
        ja += f" 想定される波及は主に {render_label_list(expected_outcomes, 'ja', 3)} に表れる。"
        th += f" ผลกระทบต่อเนื่องที่คาดว่าจะเห็นชัดคือ {render_label_list(expected_outcomes, 'th', 3)}."

    return finalize_text_i18n(decision_summary_en, {
        "en": en.strip(),
        "ja": ja.strip(),
        "th": th.strip(),
    })


def build_decision_guardrails(scenario_data: Dict[str, Any], monitoring_priorities: List[str]) -> Dict[str, List[str]]:
    roles = get_scenario_watchpoint_roles(scenario_data)
    return {
        "escalation": unique_preserve_order(roles.get("escalation", []) + monitoring_priorities[:2])[:4],
        "persistence": unique_preserve_order(roles.get("persistence", []))[:3],
        "stabilization": unique_preserve_order(roles.get("stabilization", []))[:3],
    }


def build_decision_guardrails_i18n(guardrails: Dict[str, List[str]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, values in guardrails.items():
        out[key] = {
            "en": [labelize(item, "en") for item in values],
            "ja": [labelize(item, "ja") for item in values],
            "th": [labelize(item, "th") for item in values],
        }
    return out


def build_decision_actions(
    posture: str,
    scenario_balance: str,
    decision_guardrails: Dict[str, List[str]],
    monitoring_priorities: List[str],
) -> Dict[str, List[str]]:
    escalation = unique_preserve_order(decision_guardrails.get("escalation", []) + monitoring_priorities[:2])[:3]
    stabilization = unique_preserve_order(decision_guardrails.get("stabilization", []))[:2]

    base_case: List[str] = ["maintain_core_positioning"]
    if scenario_balance in {"downside_pressure", "material_tail_risk"}:
        base_case.append("keep_tail_hedge_active")
    else:
        base_case.append("avoid_overreaction")
    if escalation:
        base_case.append(f"monitor::{escalation[0]}")

    worst_case: List[str] = [
        "reduce_exposure",
        "raise_defensive_buffer",
    ]
    if escalation:
        worst_case.append(f"escalate_on::{escalation[0]}")

    best_case: List[str] = ["selective_reengagement"]
    if stabilization:
        best_case.append(f"add_risk_only_if::{stabilization[0]}")
    else:
        best_case.append("add_risk_selectively")
    best_case.append("prefer_high_conviction_only")

    if posture == "protect_capital_now":
        worst_case = unique_preserve_order(["protect_capital_now"] + worst_case)[:4]
    elif posture == "selective_reengagement":
        best_case = unique_preserve_order(["lean_into_stabilization"] + best_case)[:4]

    return {
        "base_case": unique_preserve_order(base_case)[:4],
        "worst_case": unique_preserve_order(worst_case)[:4],
        "best_case": unique_preserve_order(best_case)[:4],
    }


def build_decision_actions_i18n(actions: Dict[str, List[str]]) -> Dict[str, Any]:
    ACTION_TEXT = {
        "maintain_core_positioning": {
            "en": "maintain core positioning",
            "ja": "中核ポジションを維持する",
            "th": "คงสถานะหลักไว้",
        },
        "keep_tail_hedge_active": {
            "en": "keep tail hedge active",
            "ja": "尾部ヘッジを維持する",
            "th": "คงการป้องกันความเสี่ยงปลายหางไว้",
        },
        "avoid_overreaction": {
            "en": "avoid overreaction",
            "ja": "過剰反応を避ける",
            "th": "หลีกเลี่ยงการตอบสนองเกินเหตุ",
        },
        "reduce_exposure": {
            "en": "reduce exposure",
            "ja": "エクスポージャーを落とす",
            "th": "ลดการเปิดรับความเสี่ยง",
        },
        "raise_defensive_buffer": {
            "en": "raise defensive buffer",
            "ja": "防御バッファを厚くする",
            "th": "เพิ่มกันชนเชิงป้องกัน",
        },
        "protect_capital_now": {
            "en": "protect capital now",
            "ja": "今は資本保全を優先する",
            "th": "ให้ความสำคัญกับการปกป้องเงินทุนทันที",
        },
        "selective_reengagement": {
            "en": "re-engage selectively",
            "ja": "限定的に再関与する",
            "th": "กลับเข้าดำเนินการอย่างเลือกสรร",
        },
        "lean_into_stabilization": {
            "en": "lean into stabilization gradually",
            "ja": "安定化を確認しながら段階的に寄せる",
            "th": "ค่อย ๆ เพิ่มน้ำหนักเมื่อการทรงตัวชัดเจน",
        },
        "add_risk_selectively": {
            "en": "add risk selectively",
            "ja": "リスク追加は選択的に行う",
            "th": "เพิ่มความเสี่ยงอย่างเลือกสรร",
        },
        "prefer_high_conviction_only": {
            "en": "prefer high-conviction only",
            "ja": "高確度領域に限定する",
            "th": "จำกัดเฉพาะจุดที่มีความเชื่อมั่นสูง",
        },
    }

    def render_token(token: str, lang: str) -> str:
        token = normalize_text(token)
        if token.startswith("monitor::"):
            target = token.split("::", 1)[1]
            target_label = labelize(target, lang)
            if lang == "ja":
                return f"{target_label} を重点監視する"
            if lang == "th":
                return f"ติดตาม {target_label} อย่างใกล้ชิด"
            return f"monitor {target_label} closely"
        if token.startswith("escalate_on::"):
            target = token.split("::", 1)[1]
            target_label = labelize(target, lang)
            if lang == "ja":
                return f"{target_label} が悪化したら防御を強める"
            if lang == "th":
                return f"เพิ่มการป้องกันหาก {target_label} แย่ลง"
            return f"escalate defense if {target_label} worsens"
        if token.startswith("add_risk_only_if::"):
            target = token.split("::", 1)[1]
            target_label = labelize(target, lang)
            if lang == "ja":
                return f"{target_label} を確認できる場合にのみリスクを増やす"
            if lang == "th":
                return f"เพิ่มความเสี่ยงเฉพาะเมื่อเห็น {target_label}"
            return f"add risk only if {target_label} appears"
        labels = ACTION_TEXT.get(token)
        if labels:
            return labels.get(lang) or labels.get("en") or token
        return labelize(token, lang)

    out: Dict[str, Any] = {}
    for scenario_id, items in actions.items():
        out[scenario_id] = {
            "en": [render_token(item, "en") for item in items],
            "ja": [render_token(item, "ja") for item in items],
            "th": [render_token(item, "th") for item in items],
        }
    return out


def build_prediction_output(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    scenario_data: Dict[str, Any],
    pattern_data: Dict[str, Any],
    analog_data: Dict[str, Any],
    reference_memory_data: Dict[str, Any],
    sentiment_data: Dict[str, Any],
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
    semantic_context = collect_sentiment_semantic_context(sentiment_data)
    scenario_probabilities = collect_scenario_probabilities(scenario_data)
    scenario_balance = classify_scenario_balance(scenario_probabilities)

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

    decision_posture = build_decision_posture(
        dominant_scenario=dominant_scenario,
        risk=risk,
        direction=direction,
        confidence=confidence,
        scenario_balance=scenario_balance,
        action_bias=action_bias,
    )

    primary_narrative = build_primary_narrative(
        scenario_data=scenario_data,
        semantic_context=semantic_context,
    )

    prediction_statement = build_prediction_statement(
        dominant_scenario=dominant_scenario,
        risk=risk,
        direction=direction,
        confidence=confidence,
        dominant_pattern=str(historical_context.get("dominant_pattern_id") or ""),
        dominant_analog=str(historical_context.get("dominant_analog_id") or ""),
        memory_summary=memory_summary,
        semantic_context=semantic_context,
        scenario_probabilities=scenario_probabilities,
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
        semantic_context=semantic_context,
        scenario_probabilities=scenario_probabilities,
    )

    primary_narrative_i18n = build_primary_narrative_i18n(
        scenario_data=scenario_data,
        primary_narrative=primary_narrative,
        semantic_context=semantic_context,
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
        semantic_context=semantic_context,
    )

    driver_structure = build_driver_structure(
        scenario_data=scenario_data,
        semantic_context=semantic_context,
        prediction_drivers=prediction_drivers,
        historical_context=historical_context,
    )
    driver_structure_i18n = build_driver_structure_i18n(driver_structure)

    decision_summary = build_decision_summary(
        posture=decision_posture,
        dominant_scenario=dominant_scenario,
        scenario_balance=scenario_balance,
        scenario_probabilities=scenario_probabilities,
        monitoring_priorities=monitoring_priorities,
        expected_outcomes=expected_outcomes,
    )
    decision_summary_i18n = build_decision_summary_i18n(
        posture=decision_posture,
        dominant_scenario=dominant_scenario,
        scenario_balance=scenario_balance,
        scenario_probabilities=scenario_probabilities,
        monitoring_priorities=monitoring_priorities,
        expected_outcomes=expected_outcomes,
        decision_summary_en=decision_summary,
    )
    decision_guardrails = build_decision_guardrails(
        scenario_data=scenario_data,
        monitoring_priorities=monitoring_priorities,
    )
    decision_guardrails_i18n = build_decision_guardrails_i18n(decision_guardrails)
    decision_actions = build_decision_actions(
        posture=decision_posture,
        scenario_balance=scenario_balance,
        decision_guardrails=decision_guardrails,
        monitoring_priorities=monitoring_priorities,
    )
    decision_actions_i18n = build_decision_actions_i18n(decision_actions)

    summary = build_summary(
        direction=direction,
        dominant_scenario=dominant_scenario,
        risk=risk,
        confidence=confidence,
        historical_context=historical_context,
        memory_summary=memory_summary,
        semantic_context=semantic_context,
    )

    summary_i18n = build_summary_i18n(
        direction=direction,
        dominant_scenario=dominant_scenario,
        risk=risk,
        confidence=confidence,
        historical_context=historical_context,
        memory_summary=memory_summary,
        summary_en=summary,
        semantic_context=semantic_context,
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
        "scenario_probabilities": scenario_probabilities,
        "scenario_balance": scenario_balance,
        "scenario_balance_i18n": label_from_map(scenario_balance, SCENARIO_BALANCE_LABELS),
        "action_bias": action_bias,
        "action_bias_i18n": label_from_map(action_bias, ACTION_BIAS_LABELS),
        "decision_posture": decision_posture,
        "decision_posture_i18n": label_from_map(decision_posture, DECISION_POSTURE_LABELS),
        "prediction_statement": prediction_statement,
        "prediction_statement_i18n": prediction_statement_i18n,
        "primary_narrative": primary_narrative,
        "primary_narrative_i18n": primary_narrative_i18n,
        "key_drivers": prediction_drivers,
        "driver_structure": driver_structure,
        "driver_structure_i18n": driver_structure_i18n,
        "monitoring_priorities": monitoring_priorities,
        "decision_summary": decision_summary,
        "decision_summary_i18n": decision_summary_i18n,
        "decision_guardrails": decision_guardrails,
        "decision_guardrails_i18n": decision_guardrails_i18n,
        "decision_actions": decision_actions,
        "decision_actions_i18n": decision_actions_i18n,
        "expected_outcomes": expected_outcomes,
        "expected_outcomes_i18n": expected_outcomes_i18n,
        "risk_flags": risk_flags_raw,
        "historical_context": historical_context,
        "semantic_context": semantic_context,
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
    output["drivers_i18n"] = dict(output.get("key_drivers_i18n", {}))
    output["watchpoints"] = list(output.get("monitoring_priorities", []))
    output["watchpoints_i18n"] = dict(output.get("monitoring_priorities_i18n", {}))
    output["invalidation_conditions"] = list(output.get("risk_flags", []))
    output["invalidation_conditions_i18n"] = dict(output.get("risk_flags_i18n", {}))

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
    sentiment_data = load_json(SENTIMENT_LATEST_PATH)
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
        sentiment_data=sentiment_data,
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
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from vector_recall import (
        DEFAULT_COLLECTION,
        DEFAULT_URL,
        build_client,
        search_similar,
    )
except Exception:
    DEFAULT_COLLECTION = "genesis_reference_memory"
    DEFAULT_URL = "http://localhost:6333"
    build_client = None
    search_similar = None


ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"

TREND_LATEST_PATH = PREDICTION_DIR / "trend_latest.json"
SIGNAL_LATEST_PATH = PREDICTION_DIR / "signal_latest.json"
HISTORICAL_PATTERN_LATEST_PATH = PREDICTION_DIR / "historical_pattern_latest.json"
HISTORICAL_ANALOG_LATEST_PATH = PREDICTION_DIR / "historical_analog_latest.json"
REFERENCE_MEMORY_PATH = PREDICTION_DIR / "reference_memory_latest.json"

SCENARIO_LATEST_PATH = PREDICTION_DIR / "scenario_latest.json"

LANG_DEFAULT = "ja"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]
ENGINE_VERSION = "v3_with_vector_memory_i18n_phase3"
REFERENCE_MEMORY_ENGINE_VERSION = "v2"
DEFAULT_RECALL_LIMIT = 3

SCENARIO_LABELS = {
    "best_case": {
        "en": "Best Case",
        "ja": "最良シナリオ",
        "th": "กรณีดีที่สุด",
    },
    "base_case": {
        "en": "Base Case",
        "ja": "基本シナリオ",
        "th": "กรณีฐาน",
    },
    "worst_case": {
        "en": "Worst Case",
        "ja": "最悪シナリオ",
        "th": "กรณีเลวร้ายที่สุด",
    },
}

RISK_LABELS = {
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

WATCHPOINT_LABELS = {
    "bank_funding_stress": {
        "en": "bank funding stress",
        "ja": "銀行の資金調達ストレス",
        "th": "ความตึงตัวของเงินทุนธนาคาร",
    },
    "credit_spread_widening": {
        "en": "credit spread widening",
        "ja": "信用スプレッド拡大",
        "th": "ส่วนต่างเครดิตขยายกว้าง",
    },
    "loan_loss_increase": {
        "en": "loan loss increase",
        "ja": "貸倒増加",
        "th": "หนี้เสียเพิ่มขึ้น",
    },
    "housing_or_equity_drawdown": {
        "en": "housing or equity drawdown",
        "ja": "住宅・株式価格の下落",
        "th": "ราคาที่อยู่อาศัยหรือหุ้นปรับลดลง",
    },
    "policy_emergency_liquidity": {
        "en": "policy emergency liquidity",
        "ja": "緊急流動性政策",
        "th": "มาตรการสภาพคล่องฉุกเฉิน",
    },
    "fx_reserve_drop": {
        "en": "FX reserve drop",
        "ja": "外貨準備低下",
        "th": "ทุนสำรองระหว่างประเทศลดลง",
    },
    "forward_market_stress": {
        "en": "forward market stress",
        "ja": "先物市場ストレス",
        "th": "ความตึงเครียดในตลาดล่วงหน้า",
    },
    "sovereign_spread_widening": {
        "en": "sovereign spread widening",
        "ja": "国債スプレッド拡大",
        "th": "ส่วนต่างพันธบัตรรัฐบาลขยายกว้าง",
    },
    "import_price_surge": {
        "en": "import price surge",
        "ja": "輸入価格急騰",
        "th": "ราคานำเข้าพุ่งสูง",
    },
    "capital_control_discussion": {
        "en": "capital control discussion",
        "ja": "資本規制議論",
        "th": "การถกเถียงเรื่องควบคุมเงินทุน",
    },
    "repo_stress": {
        "en": "repo stress",
        "ja": "レポ市場ストレス",
        "th": "ความตึงเครียดในตลาดรีโป",
    },
    "interbank_spread_surge": {
        "en": "interbank spread surge",
        "ja": "短期市場スプレッド急拡大",
        "th": "ส่วนต่างตลาดเงินระหว่างธนาคารพุ่งสูง",
    },
    "money_market_dislocation": {
        "en": "money market dislocation",
        "ja": "短期金融市場の混乱",
        "th": "ความผิดปกติในตลาดเงิน",
    },
    "emergency_swap_lines": {
        "en": "emergency swap lines",
        "ja": "緊急スワップライン",
        "th": "วงเงินสว็อปฉุกเฉิน",
    },
    "forced_asset_sales": {
        "en": "forced asset sales",
        "ja": "資産の投げ売り",
        "th": "การขายสินทรัพย์แบบถูกบีบ",
    },
    "capital_outflow": {
        "en": "capital outflow",
        "ja": "資本流出",
        "th": "เงินทุนไหลออก",
    },
    "banking_stress": {
        "en": "banking stress",
        "ja": "銀行ストレス",
        "th": "ความตึงเครียดในระบบธนาคาร",
    },
    "currency_instability": {
        "en": "currency instability",
        "ja": "通貨不安定",
        "th": "ความไม่เสถียรของค่าเงิน",
    },
}

OUTCOME_LABELS = {
    "equities_down": {
        "en": "equities down",
        "ja": "株式下落",
        "th": "หุ้นปรับตัวลง",
    },
    "credit_spreads_up": {
        "en": "credit spreads up",
        "ja": "信用スプレッド拡大",
        "th": "ส่วนต่างเครดิตเพิ่มขึ้น",
    },
    "growth_down": {
        "en": "growth down",
        "ja": "成長減速",
        "th": "การเติบโตชะลอลง",
    },
    "unemployment_up": {
        "en": "unemployment up",
        "ja": "失業率上昇",
        "th": "การว่างงานเพิ่มขึ้น",
    },
    "safe_haven_up": {
        "en": "safe haven up",
        "ja": "安全資産選好",
        "th": "ความต้องการสินทรัพย์ปลอดภัยเพิ่มขึ้น",
    },
    "currency_down": {
        "en": "currency down",
        "ja": "通貨下落",
        "th": "ค่าเงินอ่อนตัว",
    },
    "inflation_up": {
        "en": "inflation up",
        "ja": "インフレ上昇",
        "th": "เงินเฟ้อเพิ่มขึ้น",
    },
    "rates_up": {
        "en": "rates up",
        "ja": "金利上昇",
        "th": "อัตราดอกเบี้ยเพิ่มขึ้น",
    },
    "default_risk_up": {
        "en": "default risk up",
        "ja": "デフォルトリスク上昇",
        "th": "ความเสี่ยงผิดนัดชำระเพิ่มขึ้น",
    },
    "volatility_up": {
        "en": "volatility up",
        "ja": "変動率上昇",
        "th": "ความผันผวนเพิ่มขึ้น",
    },
    "equities_stabilizes": {
        "en": "equities stabilize",
        "ja": "株式安定化",
        "th": "หุ้นเริ่มทรงตัว",
    },
    "credit_spreads_moderates": {
        "en": "credit spreads moderate",
        "ja": "信用スプレッド縮小",
        "th": "ส่วนต่างเครดิตเริ่มผ่อนคลาย",
    },
    "growth_stabilizes": {
        "en": "growth stabilizes",
        "ja": "成長安定化",
        "th": "การเติบโตเริ่มทรงตัว",
    },
    "unemployment_moderates": {
        "en": "unemployment moderates",
        "ja": "失業率悪化が和らぐ",
        "th": "การว่างงานเริ่มผ่อนคลาย",
    },
    "safe_haven_moderates": {
        "en": "safe haven demand moderates",
        "ja": "安全資産偏重が和らぐ",
        "th": "แรงซื้อสินทรัพย์ปลอดภัยเริ่มผ่อนคลาย",
    },
    "currency_stabilizes": {
        "en": "currency stabilizes",
        "ja": "通貨安定化",
        "th": "ค่าเงินเริ่มทรงตัว",
    },
    "currency_sharp_down": {
        "en": "sharp currency weakness",
        "ja": "急激な通貨下落",
        "th": "ค่าเงินอ่อนตัวรุนแรง",
    },
    "equities_sharp_down": {
        "en": "sharp equities decline",
        "ja": "急激な株式下落",
        "th": "หุ้นร่วงแรง",
    },
    "growth_sharp_down": {
        "en": "sharp growth slowdown",
        "ja": "急激な成長悪化",
        "th": "การเติบโตทรุดตัวแรง",
    },
}

DRIVER_LABELS = {
    "de-escalation": {
        "en": "de-escalation",
        "ja": "緊張緩和",
        "th": "การคลี่คลาย",
    },
    "policy stabilization": {
        "en": "policy stabilization",
        "ja": "政策安定化",
        "th": "นโยบายช่วยพยุงเสถียรภาพ",
    },
    "supply adaptation": {
        "en": "supply adaptation",
        "ja": "供給適応",
        "th": "การปรับตัวด้านอุปทาน",
    },
    "confidence recovery": {
        "en": "confidence recovery",
        "ja": "信認回復",
        "th": "ความเชื่อมั่นฟื้นตัว",
    },
    "persistent stress": {
        "en": "persistent stress",
        "ja": "ストレス持続",
        "th": "แรงกดดันยังคงอยู่",
    },
    "slow adjustment": {
        "en": "slow adjustment",
        "ja": "緩慢な調整",
        "th": "การปรับตัวอย่างช้า ๆ",
    },
    "partial policy response": {
        "en": "partial policy response",
        "ja": "部分的政策対応",
        "th": "มาตรการตอบสนองเพียงบางส่วน",
    },
    "selective spillover": {
        "en": "selective spillover",
        "ja": "選択的波及",
        "th": "ผลกระทบลุกลามแบบจำกัดวง",
    },
    "escalation": {
        "en": "escalation",
        "ja": "エスカレーション",
        "th": "การยกระดับ",
    },
    "confidence breakdown": {
        "en": "confidence breakdown",
        "ja": "信認崩れ",
        "th": "ความเชื่อมั่นพังลง",
    },
    "policy failure": {
        "en": "policy failure",
        "ja": "政策失敗",
        "th": "นโยบายล้มเหลว",
    },
    "cross-domain contagion": {
        "en": "cross-domain contagion",
        "ja": "領域横断の波及",
        "th": "การลุกลามข้ามภาคส่วน",
    },
}

PHRASE_I18N = {
    "geopolitical escalation": {
        "en": "geopolitical escalation",
        "ja": "地政学的エスカレーション",
        "th": "การยกระดับทางภูมิรัฐศาสตร์",
    },
    "military tension": {
        "en": "military tension",
        "ja": "軍事緊張",
        "th": "ความตึงเครียดทางทหาร",
    },
    "sanctions fragmentation": {
        "en": "sanctions fragmentation",
        "ja": "制裁分断",
        "th": "การแบ่งแยกจากมาตรการคว่ำบาตร",
    },
    "energy inflation": {
        "en": "energy inflation",
        "ja": "エネルギーインフレ",
        "th": "เงินเฟ้อด้านพลังงาน",
    },
    "energy stress": {
        "en": "energy stress",
        "ja": "エネルギーストレス",
        "th": "แรงกดดันด้านพลังงาน",
    },
    "debt fragility": {
        "en": "debt fragility",
        "ja": "債務脆弱性",
        "th": "ความเปราะบางของหนี้",
    },
    "banking stress": {
        "en": "banking stress",
        "ja": "銀行ストレス",
        "th": "ความตึงเครียดในระบบธนาคาร",
    },
    "currency weakness": {
        "en": "currency weakness",
        "ja": "通貨弱含み",
        "th": "ค่าเงินอ่อนตัว",
    },
    "trade disruption": {
        "en": "trade disruption",
        "ja": "貿易混乱",
        "th": "การค้าสะดุด",
    },
    "supply chain disruption": {
        "en": "supply chain disruption",
        "ja": "供給網混乱",
        "th": "ห่วงโซ่อุปทานสะดุด",
    },
    "food inflation risk": {
        "en": "food inflation risk",
        "ja": "食料インフレリスク",
        "th": "ความเสี่ยงเงินเฟ้ออาหาร",
    },
    "grain stress": {
        "en": "grain stress",
        "ja": "穀物ストレス",
        "th": "แรงกดดันด้านธัญพืช",
    },
    "agricultural shock": {
        "en": "agricultural shock",
        "ja": "農業ショック",
        "th": "ช็อกภาคเกษตร",
    },
    "infrastructure disruption": {
        "en": "infrastructure disruption",
        "ja": "インフラ混乱",
        "th": "โครงสร้างพื้นฐานสะดุด",
    },
    "health-system disruption": {
        "en": "health-system disruption",
        "ja": "医療体制混乱",
        "th": "ระบบสาธารณสุขสะดุด",
    },
    "social unrest": {
        "en": "social unrest",
        "ja": "社会不安",
        "th": "ความไม่สงบทางสังคม",
    },
    "hegemonic transition": {
        "en": "hegemonic transition",
        "ja": "覇権移行",
        "th": "การเปลี่ยนผ่านมหาอำนาจนำ",
    },
    "order transition stress": {
        "en": "order transition stress",
        "ja": "秩序移行ストレス",
        "th": "แรงกดดันจากการเปลี่ยนระเบียบโลก",
    },
    "broad civilizational stress": {
        "en": "broad civilizational stress",
        "ja": "広域文明ストレス",
        "th": "แรงกดดันเชิงอารยธรรมในวงกว้าง",
    },
    "multi-domain stress": {
        "en": "multi-domain stress",
        "ja": "多領域ストレス",
        "th": "แรงกดดันหลายมิติ",
    },
    "acute stress concentration": {
        "en": "acute stress concentration",
        "ja": "急性ストレス集中",
        "th": "แรงกดดันเฉียบพลันกระจุกตัว",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build scenario_latest.json with vector-memory-backed reference recall."
    )
    parser.add_argument("--qdrant-url", default=DEFAULT_URL, help="Qdrant URL")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Qdrant collection name")
    parser.add_argument("--recall-limit", type=int, default=DEFAULT_RECALL_LIMIT, help="Vector recall result limit")
    parser.add_argument(
        "--skip-recall",
        action="store_true",
        help="Skip live vector recall and use existing reference_memory_latest.json if present",
    )
    return parser.parse_args()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def unique_preserve_order(items: List[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for item in items:
        key = (
            json.dumps(item, ensure_ascii=False, sort_keys=True)
            if isinstance(item, (dict, list))
            else str(item)
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def collect_strings(obj: Any) -> List[str]:
    results: List[str] = []

    def walk(x: Any) -> None:
        if x is None:
            return
        if isinstance(x, str):
            s = normalize_text(x)
            if s:
                results.append(s)
            return
        if isinstance(x, list):
            for item in x:
                walk(item)
            return
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
            return

    walk(obj)
    return unique_preserve_order(results)


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


def finalize_text_i18n(base_en: str, partial: Dict[str, str]) -> Dict[str, str]:
    en_text = str(partial.get("en") or base_en or "").strip()
    ja_text = str(partial.get("ja") or en_text).strip()
    th_text = str(partial.get("th") or en_text).strip()
    return {
        "en": en_text,
        "ja": ja_text,
        "th": th_text,
    }


def label_from_map(value: str, mapping: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    key = normalize_text(value)
    mapped = mapping.get(key)
    if mapped:
        return finalize_text_i18n(str(mapped.get("en") or value or ""), mapped)
    base = str(value or "").strip()
    return {
        "en": base,
        "ja": base,
        "th": base,
    }


def item_i18n(value: Any, mapping: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    key = normalize_text(value)
    if key in mapping:
        return finalize_text_i18n(str(mapping[key].get("en") or value or ""), mapping[key])

    base = str(value or "").strip()
    if ":" in base:
        prefix, suffix = base.split(":", 1)
        translated_prefix = item_i18n(prefix, DRIVER_LABELS)
        suffix_clean = suffix.strip()
        return {
            "en": f"{translated_prefix['en']}: {suffix_clean}",
            "ja": f"{translated_prefix['ja']}: {suffix_clean}",
            "th": f"{translated_prefix['th']}: {suffix_clean}",
        }

    phrase = PHRASE_I18N.get(base)
    if phrase:
        return finalize_text_i18n(str(phrase.get("en") or base), phrase)

    pretty_en = base.replace("_", " ").strip()
    if pretty_en:
        pretty_en = pretty_en[0].upper() + pretty_en[1:]

    return {
        "en": pretty_en or base,
        "ja": base,
        "th": base,
    }


def list_i18n(values: List[Any], mapping: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
    en_list: List[str] = []
    ja_list: List[str] = []
    th_list: List[str] = []

    for value in values:
        translated = item_i18n(value, mapping)
        if translated["en"]:
            en_list.append(translated["en"])
        if translated["ja"]:
            ja_list.append(translated["ja"])
        if translated["th"]:
            th_list.append(translated["th"])

    return {
        "en": en_list,
        "ja": ja_list,
        "th": th_list,
    }


def load_reference_memory() -> Dict[str, Any]:
    data = load_json(REFERENCE_MEMORY_PATH, default={}) or {}
    return data if isinstance(data, dict) else {}


def extract_signal_tags(signal_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    candidate_keys = [
        "signal_tags",
        "historical_tags",
        "signals",
        "dominant_signals",
        "watchpoints",
        "tags",
    ]

    for key in candidate_keys:
        value = signal_data.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    tags.append(normalize_text(item))
                elif isinstance(item, dict):
                    for k in ("tag", "name", "signal", "label", "driver", "type", "key"):
                        if item.get(k):
                            tags.append(normalize_text(item.get(k)))
                    if isinstance(item.get("tags"), list):
                        tags.extend(normalize_text(x) for x in item.get("tags", []) if isinstance(x, str))
        elif isinstance(value, str):
            tags.append(normalize_text(value))

    if not tags:
        tags.extend(collect_strings(signal_data))

    return unique_preserve_order([t for t in tags if t])


def extract_trend_tags(trend_data: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    candidate_keys = [
        "trend_tags",
        "tags",
        "drivers",
        "dominant_trends",
        "regimes",
        "trend_summary",
    ]

    for key in candidate_keys:
        value = trend_data.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    tags.append(normalize_text(item))
                elif isinstance(item, dict):
                    for k in ("tag", "name", "trend", "label", "direction", "regime", "driver", "key"):
                        if item.get(k):
                            tags.append(normalize_text(item.get(k)))
                    if isinstance(item.get("tags"), list):
                        tags.extend(normalize_text(x) for x in item.get("tags", []) if isinstance(x, str))
        elif isinstance(value, str):
            tags.append(normalize_text(value))

    if not tags:
        tags.extend(collect_strings(trend_data))

    return unique_preserve_order([t for t in tags if t])


def extract_reference_watchpoints(reference_memory: Dict[str, Any]) -> List[str]:
    watchpoints: List[str] = []

    for bucket_name in ("historical_patterns", "historical_analogs", "similar_cases"):
        for item in reference_memory.get(bucket_name, []) or []:
            if not isinstance(item, dict):
                continue
            tags = item.get("tags", [])
            if isinstance(tags, list):
                watchpoints.extend(str(x) for x in tags if x is not None)

    return unique_preserve_order([normalize_text(x) for x in watchpoints if normalize_text(x)])


def extract_reference_drivers(reference_memory: Dict[str, Any]) -> List[str]:
    drivers: List[str] = []

    for item in reference_memory.get("historical_patterns", []) or []:
        if isinstance(item, dict) and item.get("title"):
            drivers.append(f"pattern:{normalize_text(item.get('title'))}")

    for item in reference_memory.get("historical_analogs", []) or []:
        if isinstance(item, dict) and item.get("title"):
            drivers.append(f"analog:{normalize_text(item.get('title'))}")

    for item in reference_memory.get("similar_cases", []) or []:
        if isinstance(item, dict) and item.get("title"):
            drivers.append(f"similar_case:{normalize_text(item.get('title'))}")

    return unique_preserve_order([x for x in drivers if x])


def extract_historical_watchpoints(pattern_data: Dict[str, Any], analog_data: Dict[str, Any]) -> List[str]:
    watchpoints: List[str] = []

    for item in pattern_data.get("matched_patterns", []) or []:
        if isinstance(item, dict):
            value = item.get("watchpoints", [])
            if isinstance(value, list):
                watchpoints.extend(str(x) for x in value if x is not None)

    for item in analog_data.get("top_analogs", []) or []:
        if isinstance(item, dict):
            value = item.get("watchpoints", [])
            if isinstance(value, list):
                watchpoints.extend(str(x) for x in value if x is not None)
            similarities = item.get("similarities", [])
            if isinstance(similarities, list):
                watchpoints.extend(str(x) for x in similarities if x is not None)

    return unique_preserve_order([normalize_text(x) for x in watchpoints if normalize_text(x)])


def extract_expected_outcomes(pattern_data: Dict[str, Any], analog_data: Dict[str, Any]) -> List[str]:
    outcomes: List[str] = []

    for item in pattern_data.get("matched_patterns", []) or []:
        if isinstance(item, dict):
            value = item.get("expected_outcomes", [])
            if isinstance(value, list):
                outcomes.extend(str(x) for x in value if x is not None)

    for item in analog_data.get("top_analogs", []) or []:
        if isinstance(item, dict):
            value = item.get("historical_outcomes", [])
            if isinstance(value, list):
                outcomes.extend(str(x) for x in value if x is not None)

    return unique_preserve_order([normalize_text(x) for x in outcomes if normalize_text(x)])


def get_current_stress_vector(historical_pattern_data: Dict[str, Any]) -> Dict[str, float]:
    vector = historical_pattern_data.get("current_stress_vector", {})
    if not isinstance(vector, dict):
        return {}
    return {str(k): clamp01(safe_float(v)) for k, v in vector.items()}


def stress_average(stress_vector: Dict[str, float]) -> float:
    if not stress_vector:
        return 0.0
    values = [clamp01(safe_float(v)) for v in stress_vector.values()]
    return sum(values) / len(values) if values else 0.0


def stress_peak(stress_vector: Dict[str, float]) -> float:
    if not stress_vector:
        return 0.0
    return max(clamp01(safe_float(v)) for v in stress_vector.values())


def build_risk_flags(
    signal_tags: List[str],
    trend_tags: List[str],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
    expected_outcomes: List[str],
    stress_vector: Dict[str, float],
) -> List[str]:
    flags: List[str] = []
    combined = set(signal_tags + trend_tags + expected_outcomes)

    keyword_map = {
        "war": "geopolitical escalation",
        "military": "military tension",
        "sanction": "sanctions fragmentation",
        "oil": "energy inflation",
        "energy": "energy stress",
        "debt": "debt fragility",
        "bank": "banking stress",
        "currency": "currency weakness",
        "devaluation": "currency weakness",
        "trade": "trade disruption",
        "shipping": "supply chain disruption",
        "food": "food inflation risk",
        "grain": "grain stress",
        "drought": "agricultural shock",
        "flood": "infrastructure disruption",
        "pandemic": "health-system disruption",
        "protest": "social unrest",
        "unrest": "social unrest",
        "hegemon": "hegemonic transition",
        "empire": "order transition stress",
    }

    for token, label in keyword_map.items():
        if token in combined:
            flags.append(label)

    avg_stress = stress_average(stress_vector)
    peak_stress = stress_peak(stress_vector)

    if avg_stress >= 0.70:
        flags.append("broad civilizational stress")
    elif avg_stress >= 0.50:
        flags.append("multi-domain stress")

    if peak_stress >= 0.85:
        flags.append("acute stress concentration")

    if dominant_pattern:
        flags.append(f"historical pattern: {dominant_pattern}")
    if dominant_analog:
        flags.append(f"historical analog: {dominant_analog}")

    return unique_preserve_order(flags)


def build_key_drivers(
    signal_tags: List[str],
    trend_tags: List[str],
    dominant_pattern: Optional[str],
    expected_outcomes: List[str],
) -> List[str]:
    drivers = []
    drivers.extend(signal_tags[:6])
    drivers.extend(trend_tags[:4])

    if dominant_pattern:
        drivers.append(f"historical:{dominant_pattern}")

    for outcome in expected_outcomes[:4]:
        drivers.append(f"expected:{outcome}")

    return unique_preserve_order([normalize_text(x) for x in drivers if normalize_text(x)])


def derive_scenario_bias(
    historical_pattern_data: Dict[str, Any],
    historical_analog_data: Dict[str, Any],
) -> Dict[str, float]:
    best_case = 0.0
    base_case = 0.0
    worst_case = 0.0
    count = 0

    top_patterns = historical_pattern_data.get("matched_patterns", []) or []
    for item in top_patterns[:3]:
        if not isinstance(item, dict):
            continue
        bias = item.get("scenario_bias", {})
        if not isinstance(bias, dict):
            continue
        best_case += safe_float(bias.get("best_case"))
        base_case += safe_float(bias.get("base_case"))
        worst_case += safe_float(bias.get("worst_case"))
        count += 1

    top_analogs = historical_analog_data.get("top_analogs", []) or []
    for item in top_analogs[:2]:
        if not isinstance(item, dict):
            continue
        bias = item.get("scenario_bias", {})
        if not isinstance(bias, dict):
            continue
        best_case += safe_float(bias.get("best_case"))
        base_case += safe_float(bias.get("base_case"))
        worst_case += safe_float(bias.get("worst_case"))
        count += 1

    if count <= 0:
        return {
            "best_case": 0.25,
            "base_case": 0.5,
            "worst_case": 0.25,
        }

    best_case /= count
    base_case /= count
    worst_case /= count

    total = best_case + base_case + worst_case
    if total <= 0:
        return {
            "best_case": 0.25,
            "base_case": 0.5,
            "worst_case": 0.25,
        }

    return {
        "best_case": round(best_case / total, 4),
        "base_case": round(base_case / total, 4),
        "worst_case": round(worst_case / total, 4),
    }


def classify_risk_label(
    signal_data: Dict[str, Any],
    historical_pattern_data: Dict[str, Any],
    stress_vector: Dict[str, float],
) -> str:
    existing_risk = normalize_text(signal_data.get("risk") or signal_data.get("risk_level"))

    if existing_risk in {"high", "elevated", "guarded", "critical"}:
        if existing_risk == "critical":
            return "critical"
        if existing_risk == "high":
            return "high"
        return "guarded"

    pattern_confidence = safe_float(historical_pattern_data.get("pattern_confidence"))
    avg_stress = stress_average(stress_vector)
    peak_stress = stress_peak(stress_vector)

    if pattern_confidence >= 0.75 or peak_stress >= 0.90:
        return "high"
    if pattern_confidence >= 0.50 or avg_stress >= 0.50:
        return "guarded"
    return "stable"


def calculate_scenario_confidence(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    historical_pattern_data: Dict[str, Any],
    historical_analog_data: Dict[str, Any],
    reference_memory_data: Optional[Dict[str, Any]] = None,
) -> float:
    base = 0.35

    trend_conf = safe_float(trend_data.get("confidence", trend_data.get("overall_confidence", 0.0)))
    signal_conf = 0.0
    signals = signal_data.get("signals", [])
    if isinstance(signals, list) and signals:
        signal_conf = (
            sum(safe_float(item.get("confidence", 0.0)) for item in signals if isinstance(item, dict))
            / len(signals)
        )
    pattern_conf = safe_float(historical_pattern_data.get("pattern_confidence", 0.0))
    analog_conf = safe_float(historical_analog_data.get("analog_confidence", 0.0))

    confidence = (
        base
        + 0.20 * trend_conf
        + 0.25 * signal_conf
        + 0.15 * pattern_conf
        + 0.10 * analog_conf
    )

    ref = reference_memory_data or {}
    if ref.get("status") == "ok":
        similar_case_count = len(ref.get("similar_cases", []) or [])
        historical_pattern_count = len(ref.get("historical_patterns", []) or [])
        historical_analog_count = len(ref.get("historical_analogs", []) or [])
        decision_ref_count = len(ref.get("decision_refs", []) or [])

        confidence += min(0.02, 0.01 * similar_case_count)
        confidence += min(0.015, 0.005 * historical_pattern_count)
        confidence += min(0.015, 0.005 * historical_analog_count)
        confidence += min(0.01, 0.003 * decision_ref_count)

    return round(clamp01(confidence), 4)


def build_best_case_narrative_i18n(risk_label: str) -> Dict[str, str]:
    if risk_label == "stable":
        return {
            "en": (
                "Current pressures remain limited and adaptive capacity is sufficient "
                "to prevent a major regime shift."
            ),
            "ja": (
                "現在の圧力は限定的で、適応余地もまだあり、大きなレジーム転換を回避できる可能性が高い。"
            ),
            "th": (
                "แรงกดดันปัจจุบันยังอยู่ในวงจำกัด และระบบยังมีความสามารถในการปรับตัวเพียงพอ "
                "ที่จะหลีกเลี่ยงการเปลี่ยนระบอบครั้งใหญ่"
            ),
        }
    return {
        "en": (
            "Escalation pressures stabilize, supply disruptions remain contained, "
            "and policy or market adaptation prevents broad spillover."
        ),
        "ja": (
            "エスカレーション圧力が落ち着き、供給混乱も封じ込められ、政策または市場の適応によって広範な波及が防がれる。"
        ),
        "th": (
            "แรงกดดันการยกระดับเริ่มทรงตัว ความปั่นป่วนด้านอุปทานยังถูกจำกัดไว้ "
            "และการปรับตัวของนโยบายหรือของตลาดช่วยป้องกันการลุกลามในวงกว้าง"
        ),
    }


def build_base_case_narrative_i18n(risk_label: str) -> Dict[str, str]:
    if risk_label == "high":
        return {
            "en": (
                "The most likely path is continued deterioration without immediate collapse, "
                "producing a sustained guarded-risk regime."
            ),
            "ja": (
                "最も起こりやすい道筋は、直ちに崩壊はしないものの悪化が続き、警戒リスクが長引く展開である。"
            ),
            "th": (
                "เส้นทางที่เป็นไปได้มากที่สุดคือการเสื่อมลงต่อเนื่องโดยยังไม่พังทลายในทันที "
                "ทำให้ระบอบความเสี่ยงแบบเฝ้าระวังคงอยู่นาน"
            ),
        }
    return {
        "en": (
            "Current pressures persist in a guarded but manageable form, "
            "with continued volatility and selective downstream stress."
        ),
        "ja": (
            "現在の圧力は、警戒を要するものの管理可能な形で持続し、変動と選択的な下流ストレスが続く。"
        ),
        "th": (
            "แรงกดดันปัจจุบันยังคงอยู่ในลักษณะที่ต้องเฝ้าระวังแต่ยังพอจัดการได้ "
            "โดยความผันผวนและแรงกดดันปลายน้ำบางส่วนยังดำเนินต่อไป"
        ),
    }


def build_worst_case_narrative_i18n(risk_label: str) -> Dict[str, str]:
    if risk_label == "stable":
        return {
            "en": (
                "A low-probability but important adverse path remains: seemingly contained "
                "pressures could still cascade if watchpoints worsen rapidly."
            ),
            "ja": (
                "確率は低いが重要な悪化シナリオは残る。いまは抑え込まれて見える圧力でも、監視点が急悪化すれば連鎖的に波及しうる。"
            ),
            "th": (
                "ยังมีเส้นทางเชิงลบที่มีโอกาสต่ำแต่สำคัญอยู่ แม้แรงกดดันจะดูถูกควบคุมได้ในตอนนี้ "
                "แต่ก็อาจลุกลามเป็นลูกโซ่หากจุดเฝ้าระวังแย่ลงอย่างรวดเร็ว"
            ),
        }
    return {
        "en": (
            "Current pressures intensify into a broader systemic regime, "
            "with cross-domain spillover into trade, currency, political, or social stability."
        ),
        "ja": (
            "現在の圧力がより広いシステム局面へと強まり、貿易・通貨・政治・社会安定へ横断的に波及する。"
        ),
        "th": (
            "แรงกดดันปัจจุบันทวีความรุนแรงจนกลายเป็นภาวะเชิงระบบที่กว้างขึ้น "
            "และลุกลามข้ามมิติไปยังการค้า ค่าเงิน การเมือง และเสถียรภาพทางสังคม"
        ),
    }


def build_best_case(
    risk_label: str,
    expected_outcomes: List[str],
    watchpoints: List[str],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative_i18n = build_best_case_narrative_i18n(risk_label)
    narrative = narrative_i18n["en"]

    drivers = [
        "de-escalation",
        "policy stabilization",
        "supply adaptation",
        "confidence recovery",
    ]
    if dominant_pattern:
        drivers.append(f"containment_of:{dominant_pattern}")

    outcomes = []
    for item in expected_outcomes:
        if item.endswith("_up"):
            outcomes.append(item.replace("_up", "_moderates"))
        elif item.endswith("_down"):
            outcomes.append(item.replace("_down", "_stabilizes"))
        else:
            outcomes.append(item)

    outcomes = unique_preserve_order(outcomes[:6])
    watchpoints = unique_preserve_order(watchpoints[:6])

    return {
        "scenario_id": "best_case",
        "label": "Best Case",
        "label_i18n": label_from_map("best_case", SCENARIO_LABELS),
        "probability_hint": "lower",
        "narrative": narrative,
        "narrative_i18n": narrative_i18n,
        "drivers": unique_preserve_order(drivers),
        "drivers_i18n": list_i18n(unique_preserve_order(drivers), DRIVER_LABELS),
        "expected_outcomes": outcomes,
        "expected_outcomes_i18n": list_i18n(outcomes, OUTCOME_LABELS),
        "watchpoints": watchpoints,
        "watchpoints_i18n": list_i18n(watchpoints, WATCHPOINT_LABELS),
        "historical_support": {
            "dominant_pattern": dominant_pattern,
            "dominant_analog": dominant_analog,
            "stress_peak": round(stress_peak(stress_vector), 4),
        },
    }


def build_base_case(
    risk_label: str,
    expected_outcomes: List[str],
    watchpoints: List[str],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative_i18n = build_base_case_narrative_i18n(risk_label)
    narrative = narrative_i18n["en"]

    drivers = [
        "persistent stress",
        "slow adjustment",
        "partial policy response",
        "selective spillover",
    ]
    if dominant_analog:
        drivers.append(f"historical_similarity:{dominant_analog}")

    expected_outcomes = unique_preserve_order(expected_outcomes[:6])
    watchpoints = unique_preserve_order(watchpoints[:8])

    return {
        "scenario_id": "base_case",
        "label": "Base Case",
        "label_i18n": label_from_map("base_case", SCENARIO_LABELS),
        "probability_hint": "highest",
        "narrative": narrative,
        "narrative_i18n": narrative_i18n,
        "drivers": unique_preserve_order(drivers),
        "drivers_i18n": list_i18n(unique_preserve_order(drivers), DRIVER_LABELS),
        "expected_outcomes": expected_outcomes,
        "expected_outcomes_i18n": list_i18n(expected_outcomes, OUTCOME_LABELS),
        "watchpoints": watchpoints,
        "watchpoints_i18n": list_i18n(watchpoints, WATCHPOINT_LABELS),
        "historical_support": {
            "dominant_pattern": dominant_pattern,
            "dominant_analog": dominant_analog,
            "stress_average": round(stress_average(stress_vector), 4),
        },
    }


def build_worst_case(
    risk_label: str,
    expected_outcomes: List[str],
    watchpoints: List[str],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative_i18n = build_worst_case_narrative_i18n(risk_label)
    narrative = narrative_i18n["en"]

    intensified_outcomes = []
    for item in expected_outcomes:
        if item.endswith("_up"):
            intensified_outcomes.append(item.replace("_up", "_sharp_up"))
        elif item.endswith("_down"):
            intensified_outcomes.append(item.replace("_down", "_sharp_down"))
        else:
            intensified_outcomes.append(item)

    drivers = [
        "escalation",
        "confidence breakdown",
        "policy failure",
        "cross-domain contagion",
    ]
    if dominant_pattern:
        drivers.append(f"historical_escalation_path:{dominant_pattern}")

    intensified_outcomes = unique_preserve_order(intensified_outcomes[:6])
    watchpoints = unique_preserve_order(watchpoints[:10])

    return {
        "scenario_id": "worst_case",
        "label": "Worst Case",
        "label_i18n": label_from_map("worst_case", SCENARIO_LABELS),
        "probability_hint": "meaningful_tail_risk",
        "narrative": narrative,
        "narrative_i18n": narrative_i18n,
        "drivers": unique_preserve_order(drivers),
        "drivers_i18n": list_i18n(unique_preserve_order(drivers), DRIVER_LABELS),
        "expected_outcomes": intensified_outcomes,
        "expected_outcomes_i18n": list_i18n(intensified_outcomes, OUTCOME_LABELS),
        "watchpoints": watchpoints,
        "watchpoints_i18n": list_i18n(watchpoints, WATCHPOINT_LABELS),
        "historical_support": {
            "dominant_pattern": dominant_pattern,
            "dominant_analog": dominant_analog,
            "stress_peak": round(stress_peak(stress_vector), 4),
            "stress_average": round(stress_average(stress_vector), 4),
        },
    }


def choose_dominant_scenario(
    scenario_bias: Dict[str, float],
    risk_label: str,
) -> str:
    best_case = safe_float(scenario_bias.get("best_case"))
    base_case = safe_float(scenario_bias.get("base_case"))
    worst_case = safe_float(scenario_bias.get("worst_case"))

    if risk_label == "high" and worst_case >= max(best_case, base_case) * 0.9:
        return "worst_case"

    if base_case >= best_case and base_case >= worst_case:
        return "base_case"
    if worst_case > best_case:
        return "worst_case"
    return "best_case"


def build_summary(
    dominant_scenario: str,
    risk_label: str,
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
    confidence: float,
) -> str:
    parts = [
        f"Dominant scenario is {dominant_scenario}",
        f"risk is {risk_label}",
        f"confidence is {confidence:.2f}",
    ]
    if dominant_pattern:
        parts.append(f"historical pattern is {dominant_pattern}")
    if dominant_analog:
        parts.append(f"historical analog is {dominant_analog}")
    return ". ".join(parts) + "."


def build_summary_i18n(
    dominant_scenario: str,
    risk_label: str,
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
    confidence: float,
    summary_en: str,
) -> Dict[str, str]:
    scenario_label = label_from_map(dominant_scenario, SCENARIO_LABELS)
    risk_label_i18n = label_from_map(risk_label, RISK_LABELS)

    en_parts = [
        f"Dominant scenario is {scenario_label['en']}",
        f"risk is {risk_label_i18n['en']}",
        f"confidence is {confidence:.2f}",
    ]
    ja_parts = [
        f"主要シナリオは {scenario_label['ja']}",
        f"リスクは {risk_label_i18n['ja']}",
        f"信頼度は {confidence:.2f}",
    ]
    th_parts = [
        f"สถานการณ์หลักคือ {scenario_label['th']}",
        f"ความเสี่ยงอยู่ที่ {risk_label_i18n['th']}",
        f"ความเชื่อมั่นอยู่ที่ {confidence:.2f}",
    ]

    if dominant_pattern:
        en_parts.append(f"historical pattern is {dominant_pattern}")
        ja_parts.append(f"歴史パターンは {dominant_pattern}")
        th_parts.append(f"historical pattern คือ {dominant_pattern}")

    if dominant_analog:
        en_parts.append(f"historical analog is {dominant_analog}")
        ja_parts.append(f"歴史アナログは {dominant_analog}")
        th_parts.append(f"historical analog คือ {dominant_analog}")

    return finalize_text_i18n(
        summary_en,
        {
            "en": ". ".join(en_parts) + ".",
            "ja": "。".join(ja_parts) + "。",
            "th": ". ".join(th_parts) + ".",
        },
    )


def compact_recall_items(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in (items or [])[:limit]:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "score": item.get("score"),
                "memory_type": item.get("memory_type"),
                "as_of": item.get("as_of"),
                "title": item.get("title"),
                "title_i18n": ensure_lang_map(item.get("title_i18n")),
                "summary": item.get("summary"),
                "summary_i18n": ensure_lang_map(item.get("summary_i18n")),
                "source_path": item.get("source_path"),
                "tags": item.get("tags") if isinstance(item.get("tags"), list) else [],
            }
        )
    return out


def readable_token(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace("_", " ").replace(":", " ").replace(">", " ").strip()


def build_reference_query(
    signal_tags: List[str],
    trend_tags: List[str],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
    expected_outcomes: List[str],
    watchpoints: Optional[List[str]] = None,
) -> str:
    parts: List[str] = []

    parts.extend([
        "base_case",
        "guarded",
        "watchpoints",
        "financial stress",
        "bank funding stress",
        "credit contraction",
    ])

    if watchpoints:
        for item in watchpoints[:8]:
            norm = normalize_text(item)
            if norm:
                parts.append(norm)
                parts.append(readable_token(norm))

    for item in signal_tags[:8]:
        norm = normalize_text(item)
        if norm:
            parts.append(norm)
            parts.append(readable_token(norm))

    for item in trend_tags[:6]:
        norm = normalize_text(item)
        if norm:
            parts.append(norm)
            parts.append(readable_token(norm))

    for item in expected_outcomes[:6]:
        norm = normalize_text(item)
        if norm:
            parts.append(norm)
            parts.append(readable_token(norm))

    if dominant_pattern:
        parts.append(str(dominant_pattern).strip())
        parts.append(readable_token(dominant_pattern))
    if dominant_analog:
        parts.append(str(dominant_analog).strip())
        parts.append(readable_token(dominant_analog))

    normalized = [str(x).strip() for x in parts if str(x).strip()]
    return " ".join(unique_preserve_order(normalized)[:32]).strip() or "global risk scenario watchpoints bank funding stress"


def search_recall_bucket(
    *,
    client: Any,
    collection: str,
    query: str,
    limit: int,
    memory_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if search_similar is None:
        return []

    try:
        return compact_recall_items(
            search_similar(
                client=client,
                collection=collection,
                query=query,
                limit=limit,
                memory_type=memory_type,
            ),
            limit,
        )
    except Exception:
        return []


def build_reference_memory_artifact(
    *,
    as_of: str,
    qdrant_url: str,
    collection: str,
    recall_limit: int,
    signal_tags: List[str],
    trend_tags: List[str],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
    expected_outcomes: List[str],
    watchpoints: List[str],
) -> Dict[str, Any]:
    artifact: Dict[str, Any] = {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "engine_version": REFERENCE_MEMORY_ENGINE_VERSION,
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "query_context": {
            "source": "scenario_engine",
            "tags": unique_preserve_order((signal_tags or [])[:8] + (trend_tags or [])[:4]),
            "notes": "",
            "decision_query": "",
            "general_query": "",
        },
        "decision_refs": [],
        "similar_cases": [],
        "historical_patterns": [],
        "historical_analogs": [],
        "recall_summary": "",
        "status": "unavailable",
    }

    general_query = build_reference_query(
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
        expected_outcomes=expected_outcomes,
        watchpoints=watchpoints,
    )
    decision_query = "decision log analysis SST UI read-only complete file vector memory reference only"

    artifact["query_context"]["notes"] = general_query
    artifact["query_context"]["decision_query"] = decision_query
    artifact["query_context"]["general_query"] = general_query

    if build_client is None or search_similar is None:
        artifact["recall_summary"] = "vector_recall import unavailable"
        return artifact

    try:
        client = build_client(qdrant_url)

        decision_refs = search_recall_bucket(
            client=client,
            collection=collection,
            query=decision_query,
            limit=recall_limit,
            memory_type="decision_log",
        )

        similar_cases = search_recall_bucket(
            client=client,
            collection=collection,
            query=general_query,
            limit=recall_limit,
            memory_type="scenario_snapshot",
        )

        if not similar_cases:
            similar_cases = search_recall_bucket(
                client=client,
                collection=collection,
                query=general_query,
                limit=recall_limit,
                memory_type="prediction_snapshot",
            )

        historical_patterns = search_recall_bucket(
            client=client,
            collection=collection,
            query=general_query,
            limit=recall_limit,
            memory_type="historical_pattern",
        )

        historical_analogs = search_recall_bucket(
            client=client,
            collection=collection,
            query=general_query,
            limit=recall_limit,
            memory_type="historical_analog",
        )

        generic_fallback = search_recall_bucket(
            client=client,
            collection=collection,
            query=general_query,
            limit=max(recall_limit * 3, 6),
            memory_type=None,
        )

        if not similar_cases:
            similar_cases = [x for x in generic_fallback if x.get("memory_type") in {"scenario_snapshot", "prediction_snapshot"}][:recall_limit]

        if not historical_patterns:
            historical_patterns = [x for x in generic_fallback if x.get("memory_type") == "historical_pattern"][:recall_limit]

        if not historical_analogs:
            historical_analogs = [x for x in generic_fallback if x.get("memory_type") == "historical_analog"][:recall_limit]

        if not decision_refs:
            decision_refs = [x for x in generic_fallback if x.get("memory_type") == "decision_log"][:recall_limit]

        artifact["decision_refs"] = decision_refs
        artifact["similar_cases"] = similar_cases
        artifact["historical_patterns"] = historical_patterns
        artifact["historical_analogs"] = historical_analogs
        artifact["status"] = "ok"

        summary_parts: List[str] = []
        if decision_refs:
            summary_parts.append(f"decision_refs={len(decision_refs)}")
        if similar_cases:
            summary_parts.append(f"similar_cases={len(similar_cases)}")
        if historical_patterns:
            summary_parts.append(f"historical_patterns={len(historical_patterns)}")
        if historical_analogs:
            summary_parts.append(f"historical_analogs={len(historical_analogs)}")

        artifact["recall_summary"] = ", ".join(summary_parts) if summary_parts else "no recall hits"
        return artifact

    except Exception as exc:
        artifact["status"] = "unavailable"
        artifact["recall_summary"] = f"vector recall unavailable: {exc}"
        return artifact


def save_reference_memory_history(reference_memory_output: Dict[str, Any]) -> None:
    as_of = str(reference_memory_output.get("as_of") or today_str())
    history_dir = PREDICTION_DIR / "history" / as_of
    write_json(history_dir / "reference_memory.json", reference_memory_output)


def build_scenario_output(
    trend_data: Dict[str, Any],
    signal_data: Dict[str, Any],
    historical_pattern_data: Dict[str, Any],
    historical_analog_data: Dict[str, Any],
    reference_memory_data: Dict[str, Any],
) -> Dict[str, Any]:
    as_of = (
        signal_data.get("as_of")
        or trend_data.get("as_of")
        or historical_pattern_data.get("as_of")
        or historical_analog_data.get("as_of")
        or today_str()
    )

    signal_tags = extract_signal_tags(signal_data)
    trend_tags = extract_trend_tags(trend_data)

    dominant_pattern = historical_pattern_data.get("dominant_pattern")
    dominant_analog = historical_analog_data.get("dominant_analog")

    expected_outcomes = extract_expected_outcomes(historical_pattern_data, historical_analog_data)

    watchpoints = extract_historical_watchpoints(historical_pattern_data, historical_analog_data)
    reference_watchpoints = extract_reference_watchpoints(reference_memory_data)
    watchpoints = unique_preserve_order(watchpoints + reference_watchpoints)

    stress_vector = get_current_stress_vector(historical_pattern_data)

    scenario_bias = derive_scenario_bias(historical_pattern_data, historical_analog_data)
    risk_label = classify_risk_label(signal_data, historical_pattern_data, stress_vector)
    confidence = calculate_scenario_confidence(
        trend_data=trend_data,
        signal_data=signal_data,
        historical_pattern_data=historical_pattern_data,
        historical_analog_data=historical_analog_data,
        reference_memory_data=reference_memory_data,
    )

    scenarios = [
        build_best_case(
            risk_label=risk_label,
            expected_outcomes=expected_outcomes,
            watchpoints=watchpoints,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
        build_base_case(
            risk_label=risk_label,
            expected_outcomes=expected_outcomes,
            watchpoints=watchpoints,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
        build_worst_case(
            risk_label=risk_label,
            expected_outcomes=expected_outcomes,
            watchpoints=watchpoints,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
    ]

    dominant_scenario = choose_dominant_scenario(
        scenario_bias=scenario_bias,
        risk_label=risk_label,
    )

    key_drivers = build_key_drivers(
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        dominant_pattern=dominant_pattern,
        expected_outcomes=expected_outcomes,
    )
    key_drivers = unique_preserve_order(key_drivers + extract_reference_drivers(reference_memory_data))

    risk_flags = build_risk_flags(
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
        expected_outcomes=expected_outcomes,
        stress_vector=stress_vector,
    )

    summary = build_summary(
        dominant_scenario=dominant_scenario,
        risk_label=risk_label,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
        confidence=confidence,
    )
    summary_i18n = build_summary_i18n(
        dominant_scenario=dominant_scenario,
        risk_label=risk_label,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
        confidence=confidence,
        summary_en=summary,
    )

    return {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "engine_version": ENGINE_VERSION,
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "dominant_scenario": dominant_scenario,
        "dominant_scenario_i18n": label_from_map(dominant_scenario, SCENARIO_LABELS),
        "risk": risk_label,
        "risk_i18n": label_from_map(risk_label, RISK_LABELS),
        "confidence": confidence,
        "scenario_bias": scenario_bias,
        "key_drivers": key_drivers,
        "key_drivers_i18n": list_i18n(key_drivers, DRIVER_LABELS),
        "risk_flags": risk_flags,
        "risk_flags_i18n": list_i18n(risk_flags, PHRASE_I18N),
        "watchpoints": watchpoints[:12],
        "watchpoints_i18n": list_i18n(watchpoints[:12], WATCHPOINT_LABELS),
        "expected_outcomes": expected_outcomes[:10],
        "expected_outcomes_i18n": list_i18n(expected_outcomes[:10], OUTCOME_LABELS),
        "historical_context": {
            "dominant_pattern": dominant_pattern,
            "pattern_confidence": round(safe_float(historical_pattern_data.get("pattern_confidence")), 4),
            "dominant_analog": dominant_analog,
            "analog_confidence": round(safe_float(historical_analog_data.get("analog_confidence")), 4),
            "current_stress_vector": {k: round(v, 4) for k, v in stress_vector.items()},
            "historical_watchpoints": watchpoints[:10],
            "historical_watchpoints_i18n": list_i18n(watchpoints[:10], WATCHPOINT_LABELS),
        },
        "reference_memory": {
            "status": reference_memory_data.get("status", "unavailable"),
            "summary": reference_memory_data.get("recall_summary"),
            "decision_ref_count": len(reference_memory_data.get("decision_refs", []) or []),
            "similar_case_count": len(reference_memory_data.get("similar_cases", []) or []),
            "historical_pattern_count": len(reference_memory_data.get("historical_patterns", []) or []),
            "historical_analog_count": len(reference_memory_data.get("historical_analogs", []) or []),
            "query_context": reference_memory_data.get("query_context", {}),
        },
        "scenarios": scenarios,
        "summary": summary,
        "summary_i18n": summary_i18n,
    }


def save_history(scenario_output: Dict[str, Any]) -> None:
    as_of = str(scenario_output.get("as_of") or today_str())
    history_dir = PREDICTION_DIR / "history" / as_of
    write_json(history_dir / "scenario.json", scenario_output)


def main() -> None:
    args = parse_args()

    trend_data = load_json(TREND_LATEST_PATH, default={}) or {}
    signal_data = load_json(SIGNAL_LATEST_PATH, default={}) or {}
    historical_pattern_data = load_json(HISTORICAL_PATTERN_LATEST_PATH, default={}) or {}
    historical_analog_data = load_json(HISTORICAL_ANALOG_LATEST_PATH, default={}) or {}

    as_of = (
        signal_data.get("as_of")
        or trend_data.get("as_of")
        or historical_pattern_data.get("as_of")
        or historical_analog_data.get("as_of")
        or today_str()
    )

    signal_tags = extract_signal_tags(signal_data)
    trend_tags = extract_trend_tags(trend_data)
    dominant_pattern = historical_pattern_data.get("dominant_pattern")
    dominant_analog = historical_analog_data.get("dominant_analog")
    expected_outcomes = extract_expected_outcomes(historical_pattern_data, historical_analog_data)
    watchpoints = extract_historical_watchpoints(historical_pattern_data, historical_analog_data)

    if args.skip_recall:
        reference_memory_data = load_reference_memory()
        if not reference_memory_data:
            reference_memory_data = {
                "as_of": as_of,
                "generated_at": utc_now_iso(),
                "engine_version": REFERENCE_MEMORY_ENGINE_VERSION,
                "lang_default": LANG_DEFAULT,
                "languages": SUPPORTED_LANGUAGES,
                "query_context": {
                    "source": "scenario_engine",
                    "tags": [],
                    "notes": "skip_recall=true",
                    "decision_query": "",
                    "general_query": "",
                },
                "decision_refs": [],
                "similar_cases": [],
                "historical_patterns": [],
                "historical_analogs": [],
                "recall_summary": "skip_recall=true and no existing reference memory artifact",
                "status": "unavailable",
            }
    else:
        reference_memory_data = build_reference_memory_artifact(
            as_of=as_of,
            qdrant_url=args.qdrant_url,
            collection=args.collection,
            recall_limit=max(1, int(args.recall_limit)),
            signal_tags=signal_tags,
            trend_tags=trend_tags,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
            expected_outcomes=expected_outcomes,
            watchpoints=watchpoints,
        )

    scenario_output = build_scenario_output(
        trend_data=trend_data,
        signal_data=signal_data,
        historical_pattern_data=historical_pattern_data,
        historical_analog_data=historical_analog_data,
        reference_memory_data=reference_memory_data,
    )

    write_json(REFERENCE_MEMORY_PATH, reference_memory_data)
    save_reference_memory_history(reference_memory_data)

    write_json(SCENARIO_LATEST_PATH, scenario_output)
    save_history(scenario_output)

    print(f"[scenario_engine] wrote {SCENARIO_LATEST_PATH}")
    print(f"[scenario_engine] wrote {REFERENCE_MEMORY_PATH}")
    print(
        "[scenario_engine] dominant="
        f"{scenario_output.get('dominant_scenario')} "
        "risk="
        f"{scenario_output.get('risk')} "
        "confidence="
        f"{scenario_output.get('confidence')}"
    )
    print(
        "[scenario_engine] reference_memory="
        f"{reference_memory_data.get('status')} "
        f"summary={reference_memory_data.get('recall_summary')}"
    )


if __name__ == "__main__":
    main()
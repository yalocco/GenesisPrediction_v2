#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from i18n_translate import (
    translate_reference_memory_summary as shared_translate_reference_memory_summary,
    translate_status as shared_translate_status,
)

try:
    from vector_recall import (
        DEFAULT_COLLECTION,
        DEFAULT_URL,
        build_client,
        recall_for_scenario_context,
    )
except Exception:
    DEFAULT_COLLECTION = "genesis_reference_memory"
    DEFAULT_URL = "http://localhost:6333"
    build_client = None
    recall_for_scenario_context = None

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
ENGINE_VERSION = "v3_with_vector_memory_i18n_phase4_data_i18n"
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


SIGNAL_CATEGORY_LABELS = {
    "pressure signals": {
        "en": "pressure signals",
        "ja": "圧力シグナル",
        "th": "สัญญาณแรงกดดัน",
    },
    "headline intensity signals": {
        "en": "headline intensity signals",
        "ja": "ヘッドライン強度シグナル",
        "th": "สัญญาณความเข้มของพาดหัวข่าว",
    },
    "confidence signals": {
        "en": "confidence signals",
        "ja": "信認シグナル",
        "th": "สัญญาณความเชื่อมั่น",
    },
    "stabilization signals": {
        "en": "stabilization signals",
        "ja": "安定化シグナル",
        "th": "สัญญาณการทรงตัว",
    },
    "system stress signals": {
        "en": "system stress signals",
        "ja": "システムストレスシグナル",
        "th": "สัญญาณความตึงเครียดเชิงระบบ",
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



def canonicalize_driver_token(value: Any) -> str:
    token = normalize_text(value)
    if not token:
        return ""

    invalid_final_drivers = {
        "guarded",
        "health_degradation",
        "stabilization",
        "opportunity_window",
        "base_case",
        "best_case",
        "worst_case",
        "基本シナリオ",
        "最良シナリオ",
        "最悪シナリオ",
        "กรณีฐาน",
        "กรณีดีที่สุด",
        "กรณีเลวร้ายที่สุด",
    }

    if token.startswith("expected:"):
        token = token.split(":", 1)[1].strip()
    if token.startswith("historical:"):
        token = token.split(":", 1)[1].strip()
    if token.startswith("pattern:"):
        token = token.split(":", 1)[1].strip()
    if token.startswith("analog:"):
        token = token.split(":", 1)[1].strip()
    if token.startswith("similar_case:"):
        token = token.split(":", 1)[1].strip()

    noise_tokens = {
        "",
        "low",
        "medium",
        "high",
        "critical",
        "derived",
        "confidence_moderate",
        "confidence_trend_stable",
        "pipeline_health",
        "health",
        "news",
        "headline",
        "intensity",
        "sentiment",
        "sentiment_balance",
        "negative_leaning",
        "negative_sentiment",
        "risk",
        "guarded_risk",
        "risk_pressure",
        "pipeline_stress",
        "health_deterioration",
        "health_signals_accelerating",
        "stabilization_bias",
        "opportunity_window",
        "pressure_easing",
        "risk_off",
        "event_density_high",
        "event_density_rising",
        "headline_surge",
        "headline_intensity_accelerating",
        "mobility_restrictions",
        "supply_delay_reacceleration",
        "fiscal_support_reexpansion",
        "crop_yield_decline",
        "reservoir_shortage",
        "grain_import_surge",
        "food_price_spike",
        "subsidy_stress",
        "fiscal_spending_up",
        "credit_spreads_up",
        "credit_spreads_sharp_up",
        "safe_haven_sharp_up",
        "unemployment_sharp_up",
        "sentiment_trend_falling",
        "risk_trend_accelerating",
        "risk_trend_guarded",
    }
    if token in noise_tokens:
        return ""
    if token in invalid_final_drivers:
        return ""
    if token.startswith("monitor ") or token.startswith("check ") or token.startswith("invalidated if") or token.startswith("watch for "):
        return ""

    replacements = {
        "bank funding stress": "banking stress",
        "bank_funding_stress": "banking stress",
        "bank stress": "banking stress",
        "repo stress": "banking stress",
        "interbank spread surge": "banking stress",
        "money market dislocation": "banking stress",
        "forced asset sales": "banking stress",
        "loan loss increase": "banking stress",
        "credit spread widening": "credit spread widening",
        "sovereign spread widening": "credit spread widening",
        "fx reserve drop": "currency instability",
        "forward market stress": "currency instability",
        "capital outflow": "currency instability",
        "currency weakness": "currency instability",
        "currency down": "currency instability",
        "currency sharp down": "currency instability",
        "sanctions fragmentation": "trade disruption",
        "trade disruption": "trade disruption",
        "supply chain disruption": "trade disruption",
        "import price surge": "energy stress",
        "energy inflation": "energy stress",
        "food inflation risk": "grain stress",
        "agricultural shock": "grain stress",
        "social unrest": "social unrest",
        "policy emergency liquidity": "policy stabilization",
        "emergency swap lines": "policy stabilization",
        "policy failure": "policy failure",
        "confidence breakdown": "confidence breakdown",
        "cross domain contagion": "cross-domain contagion",
        "cross-domain contagion": "cross-domain contagion",
        "overall direction falling": "downtrend pressure",
        "overall direction rising": "uptrend pressure",
        "overall_direction_falling": "downtrend pressure",
        "overall_direction_rising": "uptrend pressure",
        "regime shift risk": "regime shift pressure",
        "regime_shift_risk": "regime shift pressure",
        "regime shift pressure": "regime shift pressure",
        "regime_shift_pressure": "regime shift pressure",
        "stress building": "stress building",
        "stress_building": "stress building",
        "systemic stress": "systemic stress",
        "systemic_stress": "systemic stress",
        "headline pressure": "headline pressure",
        "headline_pressure": "headline pressure",
        "risk level critical": "critical risk regime",
        "risk_level_critical": "critical risk regime",
        "volatility expansion": "volatility expansion",
        "volatility_expansion": "volatility expansion",
        "confidence falling": "confidence erosion",
        "confidence_falling": "confidence erosion",
        "confidence down": "confidence erosion",
        "equities down": "equities down",
        "equities sharp down": "equities sharp down",
        "growth down": "growth down",
        "growth sharp down": "growth sharp down",
        "unemployment up": "unemployment up",
        "default risk up": "default risk up",
        "safe haven up": "safe haven up",
        "inflation up": "inflation up",
        "rates up": "rates up",
    }
    if token in replacements:
        token = replacements[token]
        if token in invalid_final_drivers:
            return ""
        return token

    keyword_map = [
        (("bank", "repo", "interbank", "money market", "loan loss"), "banking stress"),
        (("currency", "fx", "capital outflow", "devaluation", "reserve"), "currency instability"),
        (("sanction", "trade", "shipping", "supply chain"), "trade disruption"),
        (("energy", "oil", "gas", "import price"), "energy stress"),
        (("food", "grain", "agricultural"), "grain stress"),
        (("military", "war", "conflict"), "military tension"),
        (("policy failure",), "policy failure"),
        (("policy", "swap lines", "liquidity"), "policy stabilization"),
        (("confidence",), "confidence erosion"),
        (("social unrest", "protest", "unrest"), "social unrest"),
        (("contagion", "spillover"), "cross-domain contagion"),
        (("headline",), "headline pressure"),
        (("regime",), "regime shift pressure"),
        (("stress",), "stress building"),
        (("volatility",), "volatility expansion"),
        (("falling", "decline", "downtrend"), "downtrend pressure"),
    ]
    for keywords, mapped in keyword_map:
        if any(keyword in token for keyword in keywords):
            if mapped in invalid_final_drivers:
                return ""
            return mapped

    if token in invalid_final_drivers:
        return ""
    return token


def driver_priority(value: str) -> int:
    token = normalize_text(value)
    priorities = {
        "banking stress": 100,
        "currency instability": 96,
        "military tension": 95,
        "energy stress": 94,
        "trade disruption": 93,
        "grain stress": 92,
        "social unrest": 90,
        "policy failure": 88,
        "confidence breakdown": 87,
        "confidence erosion": 86,
        "cross-domain contagion": 85,
        "credit spread widening": 84,
        "default risk up": 83,
        "regime shift pressure": 82,
        "systemic stress": 81,
        "stress building": 80,
        "headline pressure": 79,
        "volatility expansion": 78,
        "critical risk regime": 77,
        "downtrend pressure": 76,
        "uptrend pressure": 60,
        "policy stabilization": 58,
        "equities down": 40,
        "growth down": 39,
        "unemployment up": 38,
        "safe haven up": 37,
        "inflation up": 36,
        "rates up": 35,
    }
    return priorities.get(token, 10)


def build_structured_drivers(
    signal_tags: List[str],
    trend_tags: List[str],
    expected_outcomes: List[str],
    reference_memory_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, List[str]]:
    core_drivers: List[str] = []
    pressure_modifiers: List[str] = []
    trend_context: List[str] = []
    downstream_risks: List[str] = []

    modifier_tokens = {
        "regime shift pressure",
        "stress building",
        "systemic stress",
        "headline pressure",
        "critical risk regime",
        "volatility expansion",
        "confidence erosion",
        "confidence breakdown",
        "cross-domain contagion",
    }
    trend_tokens = {
        "downtrend pressure",
        "uptrend pressure",
    }
    downstream_tokens = {
        "equities down",
        "equities sharp down",
        "growth down",
        "growth sharp down",
        "unemployment up",
        "default risk up",
        "safe haven up",
        "inflation up",
        "rates up",
        "credit spread widening",
    }
    invalid_final_tokens = {
        "regime shift pressure",
        "stress building",
        "systemic stress",
        "headline pressure",
        "critical risk regime",
        "volatility expansion",
        "confidence erosion",
        "confidence breakdown",
        "cross-domain contagion",
        "downtrend pressure",
        "uptrend pressure",
    }

    for raw in list(signal_tags or []) + list(trend_tags or []):
        token = canonicalize_driver_token(raw)
        if not token or token in invalid_final_tokens:
            continue
        if token in trend_tokens:
            trend_context.append(token)
        elif token in modifier_tokens:
            if token not in invalid_final_tokens:
                pressure_modifiers.append(token)
        elif token in downstream_tokens:
            downstream_risks.append(token)
        else:
            core_drivers.append(token)

    for raw in expected_outcomes or []:
        token = canonicalize_driver_token(raw)
        if not token:
            continue
        downstream_risks.append(token)

    for raw in extract_reference_drivers(reference_memory_data or {}):
        token = canonicalize_driver_token(raw)
        if not token or token in invalid_final_tokens:
            continue
        if token in modifier_tokens:
            if token not in invalid_final_tokens:
                pressure_modifiers.append(token)
        elif token in trend_tokens:
            trend_context.append(token)
        elif token in downstream_tokens:
            downstream_risks.append(token)
        else:
            core_drivers.append(token)

    core_drivers = [
        item for item in unique_preserve_order(core_drivers)
        if normalize_text(item) not in invalid_final_tokens
    ]
    pressure_modifiers = [
        item for item in unique_preserve_order(pressure_modifiers)
        if normalize_text(item) not in invalid_final_tokens
    ]
    trend_context = [
        item for item in unique_preserve_order(trend_context)
        if normalize_text(item) not in invalid_final_tokens
    ]
    downstream_risks = unique_preserve_order(downstream_risks)

    core_drivers = sorted(
        unique_preserve_order(core_drivers),
        key=lambda x: (-driver_priority(x), x),
    )[:6]
    pressure_modifiers = sorted(
        unique_preserve_order(pressure_modifiers),
        key=lambda x: (-driver_priority(x), x),
    )[:4]
    trend_context = sorted(
        unique_preserve_order(trend_context),
        key=lambda x: (-driver_priority(x), x),
    )[:3]
    downstream_risks = sorted(
        unique_preserve_order(downstream_risks),
        key=lambda x: (-driver_priority(x), x),
    )[:8]

    return {
        "core_drivers": core_drivers,
        "pressure_modifiers": pressure_modifiers,
        "trend_context": trend_context,
        "downstream_risks": downstream_risks,
    }



def build_key_drivers(
    signal_tags: List[str],
    trend_tags: List[str],
    dominant_pattern: Optional[str],
    expected_outcomes: List[str],
    reference_memory_data: Optional[Dict[str, Any]] = None,
) -> List[str]:
    structured = build_structured_drivers(
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        expected_outcomes=expected_outcomes,
        reference_memory_data=reference_memory_data,
    )

    core = list(structured.get("core_drivers", []))

    drivers: List[str] = []
    for item in core:
        token = normalize_text(item)
        if not token:
            continue
        if token not in drivers:
            drivers.append(token)
        if len(drivers) >= 5:
            break

    return unique_preserve_order([normalize_text(x) for x in drivers if normalize_text(x)])[:5]




def classify_watchpoint_roles(watchpoints: List[str]) -> Dict[str, List[str]]:
    stabilization: List[str] = []
    persistence: List[str] = []
    escalation: List[str] = []

    escalation_keywords = (
        "stress",
        "widening",
        "loss",
        "drawdown",
        "drop",
        "surge",
        "outflow",
        "forced",
        "emergency",
        "instability",
    )
    stabilization_keywords = (
        "stabilize",
        "moderate",
        "contain",
        "recovery",
        "easing",
        "improve",
    )

    for item in watchpoints or []:
        token = normalize_text(item)
        if not token:
            continue
        if any(key in token for key in stabilization_keywords):
            stabilization.append(token)
        elif any(key in token for key in escalation_keywords):
            escalation.append(token)
        else:
            persistence.append(token)

    if not stabilization:
        stabilization = unique_preserve_order((watchpoints or [])[:3])
    if not persistence:
        persistence = unique_preserve_order((watchpoints or [])[1:5] or (watchpoints or [])[:4])
    if not escalation:
        escalation = unique_preserve_order((watchpoints or [])[:5])

    return {
        "stabilization": unique_preserve_order(stabilization)[:5],
        "persistence": unique_preserve_order(persistence)[:6],
        "escalation": unique_preserve_order(escalation)[:6],
    }


def merge_term_labels() -> Dict[str, Dict[str, str]]:
    merged: Dict[str, Dict[str, str]] = {}
    for mapping in (DRIVER_LABELS, WATCHPOINT_LABELS, OUTCOME_LABELS, PHRASE_I18N):
        merged.update(mapping)
    return merged


TERM_LABELS = merge_term_labels()


def render_term_i18n(value: Any) -> Dict[str, str]:
    translated = item_i18n(value, TERM_LABELS)
    return finalize_text_i18n(str(translated.get("en") or value or ""), translated)


def join_term_texts(values: List[str], limit: int = 5) -> Dict[str, str]:
    items = unique_preserve_order([normalize_text(x) for x in values if normalize_text(x)])[:limit]
    if not items:
        return {"en": "", "ja": "", "th": ""}

    translated = [render_term_i18n(item) for item in items]
    return {
        "en": ", ".join(item["en"] for item in translated if item.get("en")),
        "ja": "、".join(item["ja"] for item in translated if item.get("ja")),
        "th": ", ".join(item["th"] for item in translated if item.get("th")),
    }


def build_memory_background_i18n(
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, str]:
    pattern = str(dominant_pattern or "").strip()
    analog = str(dominant_analog or "").strip()

    if pattern and analog:
        return {
            "en": f"Historical context remains closest to {pattern}, with an analog profile resembling {analog}.",
            "ja": f"歴史的背景は {pattern} に最も近く、アナログ事例としては {analog} に似た輪郭を示す。",
            "th": f"บริบททางประวัติศาสตร์ใกล้เคียงกับ {pattern} มากที่สุด และรูปแบบเชิงเทียบคล้ายกับ {analog}",
        }
    if pattern:
        return {
            "en": f"Historical context remains closest to {pattern}.",
            "ja": f"歴史的背景は {pattern} に最も近い。",
            "th": f"บริบททางประวัติศาสตร์ใกล้เคียงกับ {pattern} มากที่สุด",
        }
    if analog:
        return {
            "en": f"The closest analog profile remains {analog}.",
            "ja": f"最も近いアナログ事例は {analog} である。",
            "th": f"กรณีเทียบเคียงที่ใกล้ที่สุดยังคงเป็น {analog}",
        }
    return {"en": "", "ja": "", "th": ""}



def summarize_signal_tags_i18n(signal_tags: List[str]) -> Dict[str, str]:
    categories: List[str] = []
    tokens = [normalize_text(x) for x in (signal_tags or []) if normalize_text(x)]

    def has_any(*needles: str) -> bool:
        return any(any(needle in token for needle in needles) for token in tokens)

    if has_any("regime", "risk", "stress_building", "systemic_stress", "pipeline_stress"):
        categories.append("pressure signals")
    if has_any("headline", "event_density", "headline_intensity"):
        categories.append("headline intensity signals")
    if has_any("confidence"):
        categories.append("confidence signals")
    if has_any("stabilization", "pressure_easing", "opportunity_window"):
        categories.append("stabilization signals")
    if has_any("bank", "currency", "social_unrest", "health_degradation"):
        categories.append("system stress signals")

    categories = unique_preserve_order(categories)[:3]
    if not categories:
        categories = ["pressure signals"]

    translated = [label_from_map(category, SIGNAL_CATEGORY_LABELS) for category in categories]
    return {
        "en": ", ".join(item["en"] for item in translated if item.get("en")),
        "ja": "、".join(item["ja"] for item in translated if item.get("ja")),
        "th": ", ".join(item["th"] for item in translated if item.get("th")),
    }


def build_scenario_narrative_i18n(
    scenario_id: str,
    risk_label: str,
    signal_tags: List[str],
    trend_tags: List[str],
    structured_drivers: Dict[str, List[str]],
    expected_outcomes: List[str],
    watchpoint_roles: Dict[str, List[str]],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, str]:
    core_text = join_term_texts(structured_drivers.get("core_drivers", []), limit=4)
    modifier_text = join_term_texts(structured_drivers.get("pressure_modifiers", []), limit=3)
    trend_text = join_term_texts(structured_drivers.get("trend_context", []) or trend_tags, limit=3)
    signal_text = summarize_signal_tags_i18n(signal_tags)
    outcome_text = join_term_texts(expected_outcomes, limit=4)
    memory_text = build_memory_background_i18n(dominant_pattern, dominant_analog)
    risk_text = label_from_map(risk_label, RISK_LABELS)

    if scenario_id == "best_case":
        watch_text = join_term_texts(watchpoint_roles.get("stabilization", []), limit=4)
        en = (
            f"The current flow remains inside a {risk_text['en']} regime instead of breaking into a wider shock. "
            f"Trend pressure around {trend_text['en'] or 'contained volatility'} starts to cool, and signals led by "
            f"{signal_text['en'] or 'stabilization signals'} stop reinforcing one another. "
            f"As core drivers such as {core_text['en'] or 'policy stabilization'} ease, modifiers like "
            f"{modifier_text['en'] or 'headline pressure'} lose force, so propagation into "
            f"{outcome_text['en'] or 'broader downstream stress'} stays limited. "
            f"This branch gains support if watchpoints such as {watch_text['en'] or 'funding and spread conditions'} stabilize rather than worsen. "
            f"{memory_text['en']}".strip()
        )
        ja = (
            f"現在の流れは、より大きなショックへ崩れるのではなく {risk_text['ja']} 局面の内側にとどまる。"
            f"{trend_text['ja'] or '抑制された変動'} をめぐる圧力が冷え始め、"
            f"{signal_text['ja'] or '安定化シグナル'} に代表される兆候同士の相互増幅も止まる。"
            f"{core_text['ja'] or '政策安定化'} のような主要ドライバーが和らぐにつれて、"
            f"{modifier_text['ja'] or 'ヘッドライン圧力'} のような修飾要因も弱まり、"
            f"{outcome_text['ja'] or '広範な下流ストレス'} への波及は限定される。"
            f"{watch_text['ja'] or '資金調達やスプレッド環境'} のような監視点が悪化ではなく安定へ向かえば、この分岐の支持が強まる。"
            f"{memory_text['ja']}".strip()
        )
        th = (
            f"ทิศทางปัจจุบันยังคงอยู่ภายในระบอบความเสี่ยงแบบ {risk_text['th']} แทนที่จะลุกลามเป็นช็อกวงกว้าง. "
            f"แรงกดดันเชิงแนวโน้มรอบ {trend_text['th'] or 'ความผันผวนที่ถูกกดไว้'} เริ่มเย็นลง "
            f"และสัญญาณที่นำโดย {signal_text['th'] or 'สัญญาณการทรงตัว'} หยุดหนุนกันเอง. "
            f"เมื่อปัจจัยขับเคลื่อนหลักอย่าง {core_text['th'] or 'การพยุงเชิงนโยบาย'} ผ่อนแรงลง "
            f"แรงเสริมอย่าง {modifier_text['th'] or 'แรงกดดันจากข่าว'} ก็อ่อนลงตาม "
            f"จึงทำให้การลุกลามไปสู่ {outcome_text['th'] or 'แรงกดดันปลายน้ำในวงกว้าง'} ยังถูกจำกัด. "
            f"สาขานี้จะมีน้ำหนักมากขึ้นหากจุดเฝ้าระวังอย่าง {watch_text['th'] or 'ภาวะเงินทุนและสเปรด'} ทรงตัวแทนที่จะแย่ลง. "
            f"{memory_text['th']}".strip()
        )
        return finalize_text_i18n(en, {"en": en, "ja": ja, "th": th})

    if scenario_id == "worst_case":
        watch_text = join_term_texts(watchpoint_roles.get("escalation", []), limit=5)
        en = (
            f"The current flow shifts from a {risk_text['en']} regime toward a broader break in stability. "
            f"Trend pressure around {trend_text['en'] or 'accelerating downside conditions'} worsens further, and signals led by "
            f"{signal_text['en'] or 'stress escalation'} begin to reinforce one another across domains. "
            f"Core drivers such as {core_text['en'] or 'systemic stress'} combine with modifiers like "
            f"{modifier_text['en'] or 'confidence erosion'}, which raises the chance that stress propagates into "
            f"{outcome_text['en'] or 'system-wide damage'}. "
            f"This branch becomes more likely if watchpoints such as {watch_text['en'] or 'funding, spreads, and liquidity conditions'} deteriorate together instead of remaining isolated. "
            f"{memory_text['en']}".strip()
        )
        ja = (
            f"現在の流れは {risk_text['ja']} 局面から、より広い安定破壊へ移り始める。"
            f"{trend_text['ja'] or '下方加速条件'} をめぐる圧力はさらに悪化し、"
            f"{signal_text['ja'] or 'ストレス拡大'} に代表される兆候が領域横断で相互増幅し始める。"
            f"{core_text['ja'] or 'システムストレス'} のような主要ドライバーが、"
            f"{modifier_text['ja'] or '信認侵食'} のような修飾要因と結びつくことで、"
            f"ストレスが {outcome_text['ja'] or 'システム全体の損傷'} へ伝播する確率が高まる。"
            f"{watch_text['ja'] or '資金調達・スプレッド・流動性条件'} のような監視点が、個別ではなく同時に悪化し始めれば、この分岐がより有力になる。"
            f"{memory_text['ja']}".strip()
        )
        th = (
            f"ทิศทางปัจจุบันกำลังเปลี่ยนจากระบอบความเสี่ยงแบบ {risk_text['th']} ไปสู่ความเสียหายด้านเสถียรภาพในวงกว้าง. "
            f"แรงกดดันเชิงแนวโน้มรอบ {trend_text['th'] or 'เงื่อนไขขาลงที่เร่งขึ้น'} แย่ลงต่อเนื่อง "
            f"และสัญญาณที่นำโดย {signal_text['th'] or 'การยกระดับของความตึงเครียด'} เริ่มหนุนกันข้ามภาคส่วน. "
            f"ตัวขับเคลื่อนหลักอย่าง {core_text['th'] or 'แรงกดดันเชิงระบบ'} รวมตัวกับแรงเสริมอย่าง "
            f"{modifier_text['th'] or 'การกัดกร่อนความเชื่อมั่น'} ทำให้โอกาสที่แรงกดดันจะลามไปสู่ "
            f"{outcome_text['th'] or 'ความเสียหายทั้งระบบ'} สูงขึ้น. "
            f"สาขานี้จะมีโอกาสมากขึ้นหากจุดเฝ้าระวังอย่าง {watch_text['th'] or 'เงินทุน สเปรด และสภาพคล่อง'} แย่ลงพร้อมกันแทนที่จะแยกกันเกิด. "
            f"{memory_text['th']}".strip()
        )
        return finalize_text_i18n(en, {"en": en, "ja": ja, "th": th})

    watch_text = join_term_texts(watchpoint_roles.get("persistence", []), limit=4)
    en = (
        f"The most likely path keeps the system inside a {risk_text['en']} regime rather than resolving it quickly. "
        f"Trend pressure around {trend_text['en'] or 'persistent volatility'} continues, and signals led by "
        f"{signal_text['en'] or 'persistent stress'} remain active without yet turning into full disorder. "
        f"Core drivers such as {core_text['en'] or 'banking stress'} stay in place, while modifiers like "
        f"{modifier_text['en'] or 'headline pressure'} keep normalization incomplete, so the main propagation remains "
        f"{outcome_text['en'] or 'selective downstream weakness'}. "
        f"This base path holds as long as watchpoints such as {watch_text['en'] or 'funding and spread stress'} stay elevated but do not deteriorate in sync. "
        f"{memory_text['en']}".strip()
    )
    ja = (
        f"最も起こりやすい道筋は、システムが急速に解消するのではなく {risk_text['ja']} 局面の内側にとどまる展開である。"
        f"{trend_text['ja'] or '持続的な変動'} をめぐる圧力は続き、"
        f"{signal_text['ja'] or 'ストレス持続'} に代表される兆候も、全面的な無秩序へはまだ転化しないまま残る。"
        f"{core_text['ja'] or '銀行ストレス'} のような主要ドライバーが居座り、"
        f"{modifier_text['ja'] or 'ヘッドライン圧力'} のような修飾要因が正常化を不完全なままにするため、"
        f"主な伝播先は {outcome_text['ja'] or '選択的な下流悪化'} にとどまる。"
        f"{watch_text['ja'] or '資金調達やスプレッド圧力'} のような監視点が高止まりしても、同時悪化に至らない限り、この base 経路が維持されやすい。"
        f"{memory_text['ja']}".strip()
    )
    th = (
        f"เส้นทางที่เป็นไปได้มากที่สุดคือระบบยังคงอยู่ภายในระบอบความเสี่ยงแบบ {risk_text['th']} แทนที่จะคลี่คลายอย่างรวดเร็ว. "
        f"แรงกดดันเชิงแนวโน้มรอบ {trend_text['th'] or 'ความผันผวนที่ยืดเยื้อ'} ยังคงดำเนินต่อไป "
        f"และสัญญาณที่นำโดย {signal_text['th'] or 'แรงกดดันที่คงอยู่'} ยังทำงานอยู่โดยยังไม่เปลี่ยนเป็นภาวะไร้ระเบียบเต็มรูปแบบ. "
        f"ตัวขับเคลื่อนหลักอย่าง {core_text['th'] or 'ความตึงเครียดภาคธนาคาร'} ยังไม่หายไป "
        f"ขณะที่แรงเสริมอย่าง {modifier_text['th'] or 'แรงกดดันจากข่าว'} ทำให้การกลับสู่ภาวะปกติไม่สมบูรณ์ "
        f"ดังนั้นการลุกลามหลักจึงยังอยู่ที่ {outcome_text['th'] or 'ความอ่อนแอปลายน้ำแบบเลือกจุด'}. "
        f"ตราบใดที่จุดเฝ้าระวังอย่าง {watch_text['th'] or 'แรงกดดันด้านเงินทุนและสเปรด'} ยังสูงแต่ไม่แย่ลงพร้อมกัน "
        f"เส้นทางฐานนี้ก็ยังมีแนวโน้มคงอยู่. "
        f"{memory_text['th']}".strip()
    )
    return finalize_text_i18n(en, {"en": en, "ja": ja, "th": th})




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
    signal_tags: List[str],
    trend_tags: List[str],
    structured_drivers: Dict[str, List[str]],
    expected_outcomes: List[str],
    watchpoint_roles: Dict[str, List[str]],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative_i18n = build_scenario_narrative_i18n(
        scenario_id="best_case",
        risk_label=risk_label,
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        structured_drivers=structured_drivers,
        expected_outcomes=expected_outcomes,
        watchpoint_roles=watchpoint_roles,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
    )
    narrative = narrative_i18n["en"]

    drivers = unique_preserve_order(
        structured_drivers.get("core_drivers", [])[:5]
        + structured_drivers.get("pressure_modifiers", [])[:1]
    )[:6]

    outcomes = []
    for item in expected_outcomes:
        normalized = normalize_text(item)
        if normalized.endswith("_up"):
            outcomes.append(normalized.replace("_up", "_moderates"))
        elif normalized.endswith("_down"):
            outcomes.append(normalized.replace("_down", "_stabilizes"))
        else:
            outcomes.append(normalized)

    outcomes = unique_preserve_order(outcomes[:6])
    scenario_watchpoints = unique_preserve_order(
        watchpoint_roles.get("stabilization", [])[:3]
        + watchpoint_roles.get("persistence", [])[:2]
    )[:6]

    return {
        "scenario_id": "best_case",
        "label": "Best Case",
        "label_i18n": label_from_map("best_case", SCENARIO_LABELS),
        "probability_hint": "lower",
        "narrative": narrative,
        "narrative_i18n": narrative_i18n,
        "drivers": drivers,
        "drivers_i18n": list_i18n(drivers, DRIVER_LABELS),
        "expected_outcomes": outcomes,
        "expected_outcomes_i18n": list_i18n(outcomes, OUTCOME_LABELS),
        "watchpoints": scenario_watchpoints,
        "watchpoints_i18n": list_i18n(scenario_watchpoints, WATCHPOINT_LABELS),
        "watchpoint_roles": {
            "stabilization": watchpoint_roles.get("stabilization", [])[:5],
            "persistence": watchpoint_roles.get("persistence", [])[:3],
            "escalation": watchpoint_roles.get("escalation", [])[:2],
        },
        "historical_support": {
            "dominant_pattern": dominant_pattern,
            "dominant_analog": dominant_analog,
            "stress_peak": round(stress_peak(stress_vector), 4),
        },
    }


def build_base_case(
    risk_label: str,
    signal_tags: List[str],
    trend_tags: List[str],
    structured_drivers: Dict[str, List[str]],
    expected_outcomes: List[str],
    watchpoint_roles: Dict[str, List[str]],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative_i18n = build_scenario_narrative_i18n(
        scenario_id="base_case",
        risk_label=risk_label,
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        structured_drivers=structured_drivers,
        expected_outcomes=expected_outcomes,
        watchpoint_roles=watchpoint_roles,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
    )
    narrative = narrative_i18n["en"]

    drivers = unique_preserve_order(
        structured_drivers.get("core_drivers", [])[:5]
        + structured_drivers.get("pressure_modifiers", [])[:2]
    )[:6]

    expected_outcomes = unique_preserve_order([normalize_text(x) for x in expected_outcomes[:6]])
    scenario_watchpoints = unique_preserve_order(
        watchpoint_roles.get("persistence", [])[:4]
        + watchpoint_roles.get("escalation", [])[:2]
    )[:8]

    return {
        "scenario_id": "base_case",
        "label": "Base Case",
        "label_i18n": label_from_map("base_case", SCENARIO_LABELS),
        "probability_hint": "highest",
        "narrative": narrative,
        "narrative_i18n": narrative_i18n,
        "drivers": drivers,
        "drivers_i18n": list_i18n(drivers, DRIVER_LABELS),
        "expected_outcomes": expected_outcomes,
        "expected_outcomes_i18n": list_i18n(expected_outcomes, OUTCOME_LABELS),
        "watchpoints": scenario_watchpoints,
        "watchpoints_i18n": list_i18n(scenario_watchpoints, WATCHPOINT_LABELS),
        "watchpoint_roles": {
            "stabilization": watchpoint_roles.get("stabilization", [])[:2],
            "persistence": watchpoint_roles.get("persistence", [])[:6],
            "escalation": watchpoint_roles.get("escalation", [])[:4],
        },
        "historical_support": {
            "dominant_pattern": dominant_pattern,
            "dominant_analog": dominant_analog,
            "stress_average": round(stress_average(stress_vector), 4),
        },
    }


def build_worst_case(
    risk_label: str,
    signal_tags: List[str],
    trend_tags: List[str],
    structured_drivers: Dict[str, List[str]],
    expected_outcomes: List[str],
    watchpoint_roles: Dict[str, List[str]],
    stress_vector: Dict[str, float],
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
) -> Dict[str, Any]:
    narrative_i18n = build_scenario_narrative_i18n(
        scenario_id="worst_case",
        risk_label=risk_label,
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        structured_drivers=structured_drivers,
        expected_outcomes=expected_outcomes,
        watchpoint_roles=watchpoint_roles,
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
    )
    narrative = narrative_i18n["en"]

    intensified_outcomes = []
    for item in expected_outcomes:
        normalized = normalize_text(item)
        if normalized.endswith("_up"):
            intensified_outcomes.append(normalized.replace("_up", "_sharp_up"))
        elif normalized.endswith("_down"):
            intensified_outcomes.append(normalized.replace("_down", "_sharp_down"))
        else:
            intensified_outcomes.append(normalized)

    drivers = unique_preserve_order(
        structured_drivers.get("core_drivers", [])[:5]
        + structured_drivers.get("pressure_modifiers", [])[:2]
    )[:7]

    intensified_outcomes = unique_preserve_order(intensified_outcomes[:6])
    scenario_watchpoints = unique_preserve_order(
        watchpoint_roles.get("escalation", [])[:6]
        + watchpoint_roles.get("persistence", [])[:2]
    )[:10]

    return {
        "scenario_id": "worst_case",
        "label": "Worst Case",
        "label_i18n": label_from_map("worst_case", SCENARIO_LABELS),
        "probability_hint": "meaningful_tail_risk",
        "narrative": narrative,
        "narrative_i18n": narrative_i18n,
        "drivers": drivers,
        "drivers_i18n": list_i18n(drivers, DRIVER_LABELS),
        "expected_outcomes": intensified_outcomes,
        "expected_outcomes_i18n": list_i18n(intensified_outcomes, OUTCOME_LABELS),
        "watchpoints": scenario_watchpoints,
        "watchpoints_i18n": list_i18n(scenario_watchpoints, WATCHPOINT_LABELS),
        "watchpoint_roles": {
            "stabilization": watchpoint_roles.get("stabilization", [])[:1],
            "persistence": watchpoint_roles.get("persistence", [])[:3],
            "escalation": watchpoint_roles.get("escalation", [])[:6],
        },
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


def filter_recall_noise_tags(values: List[str]) -> List[str]:
    noise = {
        "low",
        "medium",
        "high",
        "critical",
        "stable",
        "guarded",
        "ok",
        "warn",
        "ng",
        "unknown",
        "none",
    }
    out: List[str] = []
    for raw in values or []:
        value = normalize_text(raw)
        if not value or value in noise:
            continue
        out.append(value)
    return unique_preserve_order(out)


def build_focus_terms(
    dominant_pattern: Optional[str],
    dominant_analog: Optional[str],
    drivers: List[str],
    watchpoints: List[str],
) -> List[str]:
    terms: List[str] = []

    if dominant_pattern:
        terms.append(normalize_text(dominant_pattern))
        terms.append(readable_token(dominant_pattern))
    if dominant_analog:
        terms.append(normalize_text(dominant_analog))
        terms.append(readable_token(dominant_analog))

    for item in drivers[:4]:
        norm = normalize_text(item)
        if norm:
            terms.append(norm)
            terms.append(readable_token(norm))

    for item in watchpoints[:4]:
        norm = normalize_text(item)
        if norm:
            terms.append(norm)
            terms.append(readable_token(norm))

    return unique_preserve_order([x for x in terms if str(x).strip()])


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
    filtered_signal_tags = filter_recall_noise_tags(signal_tags)
    filtered_trend_tags = filter_recall_noise_tags(trend_tags)
    filtered_watchpoints = filter_recall_noise_tags(watchpoints)
    filtered_outcomes = filter_recall_noise_tags(expected_outcomes)

    focus_terms = build_focus_terms(
        dominant_pattern=dominant_pattern,
        dominant_analog=dominant_analog,
        drivers=filtered_outcomes,
        watchpoints=filtered_watchpoints,
    )

    artifact: Dict[str, Any] = {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "engine_version": REFERENCE_MEMORY_ENGINE_VERSION,
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "query_context": {
            "source": "scenario_engine",
            "tags": unique_preserve_order(filtered_signal_tags[:6] + filtered_trend_tags[:4]),
            "notes": "signal-driven + history-informed recall for scenario support",
        },
        "decision_refs": [],
        "similar_cases": [],
        "historical_patterns": [],
        "historical_analogs": [],
        "explanations": [],
        "recall_summary": "",
        "status": "unavailable",
    }

    if build_client is None or recall_for_scenario_context is None:
        artifact["recall_summary"] = "vector_recall import unavailable"
        return artifact

    try:
        client = build_client(qdrant_url)

        trend_direction_terms = unique_preserve_order(
            [readable_token(x) for x in filtered_trend_tags[:3] if readable_token(x)]
            + [readable_token(x) for x in focus_terms[:4] if readable_token(x)]
        )
        trend_direction = " ".join([x for x in trend_direction_terms if x]).strip()

        primary_result = recall_for_scenario_context(
            client=client,
            collection=collection,
            signal_tags=filtered_signal_tags[:6],
            trend_direction=trend_direction,
            drivers=focus_terms[:5] or filtered_outcomes[:5],
            watchpoints=filtered_watchpoints[:6],
            overall_risk="guarded",
            dominant_scenario="base_case",
            as_of=as_of,
            limit=max(1, int(recall_limit)),
        )

        result = primary_result if isinstance(primary_result, dict) else {}

        no_hits = (
            not result
            or result.get("status") == "no_results"
            or not any(
                result.get(key)
                for key in (
                    "decision_refs",
                    "similar_cases",
                    "historical_patterns",
                    "historical_analogs",
                )
            )
        )

        if no_hits:
            relaxed_signal_tags = unique_preserve_order(
                filtered_signal_tags[:3]
                + ([normalize_text(dominant_pattern)] if dominant_pattern else [])
                + ([normalize_text(dominant_analog)] if dominant_analog else [])
            )
            relaxed_drivers = focus_terms[:6] or filtered_outcomes[:4]
            relaxed_watchpoints = filtered_watchpoints[:4]

            relaxed_result = recall_for_scenario_context(
                client=client,
                collection=collection,
                signal_tags=relaxed_signal_tags,
                trend_direction=" ".join(
                    readable_token(x) for x in relaxed_drivers[:4] if readable_token(x)
                ).strip(),
                drivers=relaxed_drivers,
                watchpoints=relaxed_watchpoints,
                overall_risk="guarded",
                dominant_scenario="base_case",
                as_of=as_of,
                limit=max(1, int(recall_limit)),
            )
            if isinstance(relaxed_result, dict):
                result = relaxed_result

        if not isinstance(result, dict):
            artifact["recall_summary"] = "vector recall returned invalid result"
            return artifact

        artifact["generated_at"] = utc_now_iso()
        artifact["query_context"] = result.get("query_context", artifact["query_context"])
        artifact["decision_refs"] = result.get("decision_refs", []) or []
        artifact["similar_cases"] = result.get("similar_cases", []) or []
        artifact["historical_patterns"] = result.get("historical_patterns", []) or []
        artifact["historical_analogs"] = result.get("historical_analogs", []) or []
        artifact["explanations"] = result.get("explanations", []) or []
        artifact["recall_summary"] = result.get("recall_summary", "") or "no recall hits"
        artifact["status"] = result.get("status", "ok")

        artifact["query_context"]["filtered_signal_tags"] = filtered_signal_tags
        artifact["query_context"]["filtered_trend_tags"] = filtered_trend_tags
        artifact["query_context"]["filtered_watchpoints"] = filtered_watchpoints
        artifact["query_context"]["focus_terms"] = focus_terms

        if dominant_pattern and not artifact["query_context"].get("dominant_pattern"):
            artifact["query_context"]["dominant_pattern"] = dominant_pattern
        if dominant_analog and not artifact["query_context"].get("dominant_analog"):
            artifact["query_context"]["dominant_analog"] = dominant_analog

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
    structured_drivers = build_structured_drivers(
        signal_tags=signal_tags,
        trend_tags=trend_tags,
        expected_outcomes=expected_outcomes,
        reference_memory_data=reference_memory_data,
    )
    watchpoint_roles = classify_watchpoint_roles(watchpoints)
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
            signal_tags=signal_tags,
            trend_tags=trend_tags,
            structured_drivers=structured_drivers,
            expected_outcomes=expected_outcomes,
            watchpoint_roles=watchpoint_roles,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
        build_base_case(
            risk_label=risk_label,
            signal_tags=signal_tags,
            trend_tags=trend_tags,
            structured_drivers=structured_drivers,
            expected_outcomes=expected_outcomes,
            watchpoint_roles=watchpoint_roles,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
        build_worst_case(
            risk_label=risk_label,
            signal_tags=signal_tags,
            trend_tags=trend_tags,
            structured_drivers=structured_drivers,
            expected_outcomes=expected_outcomes,
            watchpoint_roles=watchpoint_roles,
            stress_vector=stress_vector,
            dominant_pattern=dominant_pattern,
            dominant_analog=dominant_analog,
        ),
    ]

    dominant_scenario = choose_dominant_scenario(
        scenario_bias=scenario_bias,
        risk_label=risk_label,
    )

    key_drivers = unique_preserve_order(structured_drivers.get("core_drivers", []))[:5]

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
        "structured_drivers": structured_drivers,
        "structured_drivers_i18n": {
            "core_drivers": list_i18n(structured_drivers.get("core_drivers", []), DRIVER_LABELS),
            "pressure_modifiers": list_i18n(structured_drivers.get("pressure_modifiers", []), DRIVER_LABELS),
            "trend_context": list_i18n(structured_drivers.get("trend_context", []), DRIVER_LABELS),
            "downstream_risks": list_i18n(structured_drivers.get("downstream_risks", []), OUTCOME_LABELS),
        },
        "risk_flags": risk_flags,
        "risk_flags_i18n": list_i18n(risk_flags, PHRASE_I18N),
        "watchpoints": watchpoints[:12],
        "watchpoints_i18n": list_i18n(watchpoints[:12], WATCHPOINT_LABELS),
        "watchpoint_roles": {
            "stabilization": watchpoint_roles.get("stabilization", [])[:5],
            "persistence": watchpoint_roles.get("persistence", [])[:6],
            "escalation": watchpoint_roles.get("escalation", [])[:6],
        },
        "watchpoint_roles_i18n": {
            "stabilization": list_i18n(watchpoint_roles.get("stabilization", [])[:5], WATCHPOINT_LABELS),
            "persistence": list_i18n(watchpoint_roles.get("persistence", [])[:6], WATCHPOINT_LABELS),
            "escalation": list_i18n(watchpoint_roles.get("escalation", [])[:6], WATCHPOINT_LABELS),
        },
        "expected_outcomes": structured_drivers.get("downstream_risks", [])[:10] or expected_outcomes[:10],
        "expected_outcomes_i18n": list_i18n(structured_drivers.get("downstream_risks", [])[:10] or expected_outcomes[:10], OUTCOME_LABELS),
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
            "status_i18n": shared_translate_status(reference_memory_data.get("status", "unavailable")),
            "summary": reference_memory_data.get("recall_summary"),
            "summary_i18n": shared_translate_reference_memory_summary(reference_memory_data.get("recall_summary")),
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
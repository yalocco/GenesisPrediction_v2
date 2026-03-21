#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenesisPrediction v2
FX Decision Engine (Phase5-A i18n Phase1)

Purpose
-------
Convert prediction outputs into actionable FX decision artifacts.

Design Principles
-----------------
- analysis/ is the Single Source of Truth
- scripts/ perform calculation only
- UI reads artifacts only
- v1 should remain rule-based and explainable
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_PREDICTION_PATH = Path("analysis/prediction/prediction_latest.json")
DEFAULT_FX_INPUTS_PATH = Path("analysis/fx/fx_inputs_latest.json")
DEFAULT_OUTPUT_DIR = Path("analysis/fx")

PAIR_ORDER = ["JPYTHB", "USDJPY", "USDTHB"]

LANG_DEFAULT = "ja"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]


DECISION_LABELS = {
    "SEND": {
        "en": "SEND",
        "ja": "送金実行",
        "th": "ส่งเงิน",
    },
    "SPLIT": {
        "en": "SPLIT",
        "ja": "分割送金",
        "th": "ทยอยส่ง",
    },
    "CAUTION": {
        "en": "CAUTION",
        "ja": "注意",
        "th": "ระวัง",
    },
    "HOLD": {
        "en": "HOLD",
        "ja": "保留",
        "th": "ชะลอ",
    },
}

PAIR_LABELS = {
    "JPYTHB": {
        "en": "JPYTHB",
        "ja": "JPYTHB",
        "th": "JPYTHB",
    },
    "USDJPY": {
        "en": "USDJPY",
        "ja": "USDJPY",
        "th": "USDJPY",
    },
    "USDTHB": {
        "en": "USDTHB",
        "ja": "USDTHB",
        "th": "USDTHB",
    },
    "MULTI": {
        "en": "MULTI",
        "ja": "総合判定",
        "th": "การตัดสินใจรวม",
    },
}

WATCHPOINT_TRANSLATIONS = {
    "fx volatility expansion": {
        "en": "fx volatility expansion",
        "ja": "為替ボラティリティ拡大",
        "th": "ความผันผวนค่าเงินขยายตัว",
    },
    "rapid 7d move": {
        "en": "rapid 7d move",
        "ja": "7日で急変動",
        "th": "เคลื่อนไหวเร็วในรอบ 7 วัน",
    },
    "large 30d move": {
        "en": "large 30d move",
        "ja": "30日で大幅変動",
        "th": "เคลื่อนไหวขนาดใหญ่ในรอบ 30 วัน",
    },
}

NOTE_TRANSLATIONS = {
    "worst-case probability elevated": {
        "en": "worst-case probability elevated",
        "ja": "最悪シナリオ確率が高め",
        "th": "ความน่าจะเป็นกรณีเลวร้ายอยู่ในระดับสูง",
    },
    "best-case probability supportive": {
        "en": "best-case probability supportive",
        "ja": "最良シナリオ確率が支援的",
        "th": "ความน่าจะเป็นกรณีดีที่สุดช่วยหนุน",
    },
    "watchpoints contain danger keywords": {
        "en": "watchpoints contain danger keywords",
        "ja": "監視項目に危険キーワードを含む",
        "th": "จุดเฝ้าระวังมีคำสำคัญด้านความเสี่ยง",
    },
    "drivers contain danger keywords": {
        "en": "drivers contain danger keywords",
        "ja": "ドライバーに危険キーワードを含む",
        "th": "ตัวขับเคลื่อนมีคำสำคัญด้านความเสี่ยง",
    },
    "JPYTHB improved over 7d": {
        "en": "JPYTHB improved over 7d",
        "ja": "JPYTHB は7日で改善",
        "th": "JPYTHB ปรับดีขึ้นในรอบ 7 วัน",
    },
    "JPYTHB deteriorated over 7d": {
        "en": "JPYTHB deteriorated over 7d",
        "ja": "JPYTHB は7日で悪化",
        "th": "JPYTHB แย่ลงในรอบ 7 วัน",
    },
    "JPYTHB improved over 30d": {
        "en": "JPYTHB improved over 30d",
        "ja": "JPYTHB は30日で改善",
        "th": "JPYTHB ปรับดีขึ้นในรอบ 30 วัน",
    },
    "JPYTHB weakened over 30d": {
        "en": "JPYTHB weakened over 30d",
        "ja": "JPYTHB は30日で弱含み",
        "th": "JPYTHB อ่อนลงในรอบ 30 วัน",
    },
    "JPYTHB trend=up": {
        "en": "JPYTHB trend=up",
        "ja": "JPYTHB トレンド=上向き",
        "th": "JPYTHB แนวโน้ม=ขึ้น",
    },
    "JPYTHB trend=down": {
        "en": "JPYTHB trend=down",
        "ja": "JPYTHB トレンド=下向き",
        "th": "JPYTHB แนวโน้ม=ลง",
    },
    "JPYTHB above moving average": {
        "en": "JPYTHB above moving average",
        "ja": "JPYTHB は移動平均より上",
        "th": "JPYTHB อยู่เหนือค่าเฉลี่ยเคลื่อนที่",
    },
    "JPYTHB below moving average": {
        "en": "JPYTHB below moving average",
        "ja": "JPYTHB は移動平均より下",
        "th": "JPYTHB อยู่ต่ำกว่าค่าเฉลี่ยเคลื่อนที่",
    },
    "USDJPY moved strongly over 7d": {
        "en": "USDJPY moved strongly over 7d",
        "ja": "USDJPY は7日で大きく変動",
        "th": "USDJPY เคลื่อนไหวแรงในรอบ 7 วัน",
    },
    "USDJPY moved strongly over 30d": {
        "en": "USDJPY moved strongly over 30d",
        "ja": "USDJPY は30日で大きく変動",
        "th": "USDJPY เคลื่อนไหวแรงในรอบ 30 วัน",
    },
    "USDJPY trend + volatility caution": {
        "en": "USDJPY trend + volatility caution",
        "ja": "USDJPY はトレンドと変動率の両面で注意",
        "th": "USDJPY ต้องระวังทั้งแนวโน้มและความผันผวน",
    },
    "USDTHB moved notably over 7d": {
        "en": "USDTHB moved notably over 7d",
        "ja": "USDTHB は7日で目立つ変動",
        "th": "USDTHB เคลื่อนไหวเด่นในรอบ 7 วัน",
    },
    "USDTHB trend=stable": {
        "en": "USDTHB trend=stable",
        "ja": "USDTHB トレンド=安定",
        "th": "USDTHB แนวโน้ม=ทรงตัว",
    },
}


@dataclass
class PairDecision:
    pair: str
    decision: str
    reason: str
    reason_i18n: Dict[str, str]
    confidence: float
    prediction_bias: float
    fx_bias: float
    combined_score: float
    watchpoints: List[str]
    watchpoints_i18n: Dict[str, List[str]]
    inputs: Dict[str, Any]


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing input: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize_text_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def lower_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip().lower()


def normalize_lang_map(value: Any) -> Dict[str, str]:
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


def normalize_lang_list_map(value: Any) -> Dict[str, List[str]]:
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


def label_from_map(value: str, mapping: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    key = str(value or "").strip()
    mapped = mapping.get(key)
    if mapped:
        return finalize_text_i18n(str(mapped.get("en") or key), mapped)
    return {
        "en": key,
        "ja": key,
        "th": key,
    }


def extract_prediction_fields(prediction: Dict[str, Any]) -> Dict[str, Any]:
    scenarios = prediction.get("scenarios", {})
    scenario_probabilities = prediction.get("scenario_probabilities", {})

    best_case = (
        prediction.get("best_case")
        or scenario_probabilities.get("best_case")
        or scenarios.get("best_case", {}).get("probability")
        or scenarios.get("best", {}).get("probability")
        or 0.0
    )
    base_case = (
        prediction.get("base_case")
        or scenario_probabilities.get("base_case")
        or scenarios.get("base_case", {}).get("probability")
        or scenarios.get("base", {}).get("probability")
        or 0.0
    )
    worst_case = (
        prediction.get("worst_case")
        or scenario_probabilities.get("worst_case")
        or scenarios.get("worst_case", {}).get("probability")
        or scenarios.get("worst", {}).get("probability")
        or 0.0
    )

    return {
        "as_of": str(prediction.get("as_of") or "").strip(),
        "overall_risk": lower_text(
            prediction.get("overall_risk")
            or prediction.get("risk")
            or prediction.get("risk_level"),
            default="unknown",
        ),
        "dominant_scenario": lower_text(
            prediction.get("dominant_scenario")
            or prediction.get("dominant")
            or "base_case"
        ),
        "confidence": clamp(safe_float(prediction.get("confidence"), 0.5), 0.0, 1.0),
        "watchpoints": normalize_text_list(
            prediction.get("watchpoints")
            or prediction.get("monitoring_priorities")
        ),
        "watchpoints_i18n": normalize_lang_list_map(prediction.get("watchpoints_i18n")),
        "drivers": normalize_text_list(
            prediction.get("drivers")
            or prediction.get("key_drivers")
        ),
        "best_case": clamp(safe_float(best_case, 0.0), 0.0, 1.0),
        "base_case": clamp(safe_float(base_case, 0.0), 0.0, 1.0),
        "worst_case": clamp(safe_float(worst_case, 0.0), 0.0, 1.0),
        "prediction_statement": str(prediction.get("prediction_statement") or "").strip(),
        "prediction_statement_i18n": normalize_lang_map(prediction.get("prediction_statement_i18n")),
        "primary_narrative": str(prediction.get("primary_narrative") or "").strip(),
        "primary_narrative_i18n": normalize_lang_map(prediction.get("primary_narrative_i18n")),
        "summary": str(prediction.get("summary") or "").strip(),
        "summary_i18n": normalize_lang_map(prediction.get("summary_i18n")),
        "lang_default": str(prediction.get("lang_default") or LANG_DEFAULT).strip() or LANG_DEFAULT,
        "languages": prediction.get("languages") if isinstance(prediction.get("languages"), list) else list(SUPPORTED_LANGUAGES),
    }


def extract_pair_inputs(fx_inputs: Dict[str, Any], pair: str) -> Dict[str, Any]:
    pairs = fx_inputs.get("pairs", {})
    raw = pairs.get(pair, {})

    return {
        "rate": raw.get("rate"),
        "change_1d_pct": safe_float(raw.get("change_1d_pct"), 0.0),
        "change_7d_pct": safe_float(raw.get("change_7d_pct"), 0.0),
        "change_30d_pct": safe_float(raw.get("change_30d_pct"), 0.0),
        "volatility_7d": safe_float(raw.get("volatility_7d"), 0.0),
        "trend": lower_text(raw.get("trend"), default="stable") or "stable",
        "ma_gap_pct": safe_float(raw.get("ma_gap_pct"), 0.0),
    }


def score_prediction_bias(pred: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    notes: List[str] = []

    risk = pred["overall_risk"]
    dominant = pred["dominant_scenario"]
    confidence = float(pred["confidence"])
    worst_case = float(pred["worst_case"])
    best_case = float(pred["best_case"])
    watchpoints_text = " ".join(pred["watchpoints"]).lower()
    drivers_text = " ".join(pred["drivers"]).lower()

    if risk in {"crisis", "high", "elevated", "severe"}:
        score -= 0.35
        notes.append(f"prediction risk={risk}")
    elif risk in {"guarded", "moderate"}:
        score -= 0.10
        notes.append(f"prediction risk={risk}")
    elif risk in {"stable", "low"}:
        score += 0.10
        notes.append(f"prediction risk={risk}")
    else:
        notes.append(f"prediction risk={risk}")

    if dominant == "worst_case":
        score -= 0.30
        notes.append("dominant scenario=worst_case")
    elif dominant == "best_case":
        score += 0.20
        notes.append("dominant scenario=best_case")
    else:
        notes.append(f"dominant scenario={dominant}")

    confidence_adjustment = clamp((confidence - 0.50) * 0.40, -0.10, 0.10)
    score += confidence_adjustment
    notes.append(f"prediction confidence={confidence:.2f}")

    if worst_case >= 0.45:
        score -= 0.15
        notes.append("worst-case probability elevated")

    if best_case >= 0.45:
        score += 0.10
        notes.append("best-case probability supportive")

    danger_keywords = [
        "war",
        "conflict",
        "sanction",
        "intervention",
        "volatility",
        "shock",
        "crisis",
        "liquidity",
        "escalation",
        "military",
    ]

    if any(k in watchpoints_text for k in danger_keywords):
        score -= 0.10
        notes.append("watchpoints contain danger keywords")

    if any(k in drivers_text for k in danger_keywords):
        score -= 0.05
        notes.append("drivers contain danger keywords")

    return clamp(score, -0.70, 0.40), notes


def score_fx_bias(pair: str, fx: Dict[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    notes: List[str] = []

    change_7d = float(fx["change_7d_pct"])
    change_30d = float(fx["change_30d_pct"])
    vol_7d = float(fx["volatility_7d"])
    trend = fx["trend"]
    ma_gap_pct = float(fx["ma_gap_pct"])

    if vol_7d >= 2.0:
        score -= 0.35
        notes.append(f"very high volatility={vol_7d:.2f}")
    elif vol_7d >= 1.2:
        score -= 0.20
        notes.append(f"high volatility={vol_7d:.2f}")
    elif vol_7d >= 0.8:
        score -= 0.10
        notes.append(f"moderate volatility={vol_7d:.2f}")
    else:
        notes.append(f"volatility={vol_7d:.2f}")

    if pair == "JPYTHB":
        if change_7d >= 1.0:
            score += 0.30
            notes.append("JPYTHB improved over 7d")
        elif change_7d <= -1.0:
            score -= 0.25
            notes.append("JPYTHB deteriorated over 7d")

        if change_30d >= 2.0:
            score += 0.10
            notes.append("JPYTHB improved over 30d")
        elif change_30d <= -2.0:
            score -= 0.10
            notes.append("JPYTHB weakened over 30d")

        if trend == "up":
            score += 0.15
            notes.append("JPYTHB trend=up")
        elif trend == "down":
            score -= 0.15
            notes.append("JPYTHB trend=down")

        if ma_gap_pct >= 1.0:
            score += 0.05
            notes.append("JPYTHB above moving average")
        elif ma_gap_pct <= -1.0:
            score -= 0.05
            notes.append("JPYTHB below moving average")

    elif pair == "USDJPY":
        if abs(change_7d) >= 1.5:
            score -= 0.10
            notes.append("USDJPY moved strongly over 7d")

        if abs(change_30d) >= 3.0:
            score -= 0.05
            notes.append("USDJPY moved strongly over 30d")

        if trend in {"up", "down"} and vol_7d >= 0.8:
            score -= 0.05
            notes.append("USDJPY trend + volatility caution")

    elif pair == "USDTHB":
        if abs(change_7d) >= 1.0:
            score -= 0.05
            notes.append("USDTHB moved notably over 7d")

        if trend == "stable":
            score += 0.05
            notes.append("USDTHB trend=stable")

    return clamp(score, -0.60, 0.45), notes


def decision_from_score(score: float, pred_conf: float, vol_7d: float) -> str:
    if vol_7d >= 2.0:
        return "HOLD"
    if score >= 0.25:
        return "SEND"
    if score >= 0.05:
        return "SPLIT"
    if score <= -0.35:
        return "HOLD"
    if score <= -0.10:
        return "CAUTION"
    if pred_conf < 0.45:
        return "SPLIT"
    return "CAUTION"


def translate_dynamic_note(note: str) -> Dict[str, str]:
    base = str(note or "").strip()
    if not base:
        return {"en": "", "ja": "", "th": ""}

    mapped = NOTE_TRANSLATIONS.get(base)
    if mapped:
        return finalize_text_i18n(base, mapped)

    if base.startswith("prediction risk="):
        value = base.split("=", 1)[1].strip()
        return {
            "en": f"prediction risk={value}",
            "ja": f"予測リスク={value}",
            "th": f"ความเสี่ยงจากการคาดการณ์={value}",
        }

    if base.startswith("dominant scenario="):
        value = base.split("=", 1)[1].strip()
        return {
            "en": f"dominant scenario={value}",
            "ja": f"主要シナリオ={value}",
            "th": f"สถานการณ์หลัก={value}",
        }

    if base.startswith("prediction confidence="):
        value = base.split("=", 1)[1].strip()
        return {
            "en": f"prediction confidence={value}",
            "ja": f"予測信頼度={value}",
            "th": f"ความเชื่อมั่นการคาดการณ์={value}",
        }

    if base.startswith("very high volatility="):
        value = base.split("=", 1)[1].strip()
        return {
            "en": f"very high volatility={value}",
            "ja": f"非常に高いボラティリティ={value}",
            "th": f"ความผันผวนสูงมาก={value}",
        }

    if base.startswith("high volatility="):
        value = base.split("=", 1)[1].strip()
        return {
            "en": f"high volatility={value}",
            "ja": f"高いボラティリティ={value}",
            "th": f"ความผันผวนสูง={value}",
        }

    if base.startswith("moderate volatility="):
        value = base.split("=", 1)[1].strip()
        return {
            "en": f"moderate volatility={value}",
            "ja": f"中程度のボラティリティ={value}",
            "th": f"ความผันผวนปานกลาง={value}",
        }

    if base.startswith("volatility="):
        value = base.split("=", 1)[1].strip()
        return {
            "en": f"volatility={value}",
            "ja": f"ボラティリティ={value}",
            "th": f"ความผันผวน={value}",
        }

    return {
        "en": base,
        "ja": base,
        "th": base,
    }


def build_reason(pair: str, decision: str, pred_notes: List[str], fx_notes: List[str]) -> str:
    merged = pred_notes + fx_notes
    summary = "; ".join(merged[:6])
    if summary:
        return f"{pair}: {decision}. {summary}"
    return f"{pair}: {decision}."


def build_reason_i18n(pair: str, decision: str, pred_notes: List[str], fx_notes: List[str]) -> Dict[str, str]:
    merged = pred_notes + fx_notes
    translated = [translate_dynamic_note(x) for x in merged[:6] if str(x).strip()]
    pair_labels = label_from_map(pair, PAIR_LABELS)
    decision_labels = label_from_map(decision, DECISION_LABELS)

    if translated:
        en_summary = "; ".join(x["en"] for x in translated if x["en"])
        ja_summary = "；".join(x["ja"] for x in translated if x["ja"])
        th_summary = "; ".join(x["th"] for x in translated if x["th"])

        en = f"{pair_labels['en']}: {decision_labels['en']}. {en_summary}"
        ja = f"{pair_labels['ja']}: {decision_labels['ja']}。{ja_summary}"
        th = f"{pair_labels['th']}: {decision_labels['th']}. {th_summary}"
    else:
        en = f"{pair_labels['en']}: {decision_labels['en']}."
        ja = f"{pair_labels['ja']}: {decision_labels['ja']}。"
        th = f"{pair_labels['th']}: {decision_labels['th']}."

    return {
        "en": en,
        "ja": ja,
        "th": th,
    }


def translate_watchpoint_item(item: str, prediction_watchpoints_i18n: Dict[str, List[str]], index: int) -> Dict[str, str]:
    base = str(item or "").strip()
    if not base:
        return {"en": "", "ja": "", "th": ""}

    pred_en = prediction_watchpoints_i18n.get("en", [])
    pred_ja = prediction_watchpoints_i18n.get("ja", [])
    pred_th = prediction_watchpoints_i18n.get("th", [])
    if index < len(pred_en) or index < len(pred_ja) or index < len(pred_th):
        return {
            "en": pred_en[index] if index < len(pred_en) else base,
            "ja": pred_ja[index] if index < len(pred_ja) else base,
            "th": pred_th[index] if index < len(pred_th) else base,
        }

    mapped = WATCHPOINT_TRANSLATIONS.get(base)
    if mapped:
        return finalize_text_i18n(base, mapped)

    return {
        "en": base,
        "ja": base,
        "th": base,
    }


def build_watchpoints_i18n(
    watchpoints: List[str],
    prediction_watchpoints_i18n: Dict[str, List[str]],
    prediction_watchpoints_count: int,
) -> Dict[str, List[str]]:
    en_list: List[str] = []
    ja_list: List[str] = []
    th_list: List[str] = []

    for idx, item in enumerate(watchpoints):
        source_index = idx if idx < prediction_watchpoints_count else 999999
        translated = translate_watchpoint_item(item, prediction_watchpoints_i18n, source_index)
        en_list.append(translated["en"])
        ja_list.append(translated["ja"])
        th_list.append(translated["th"])

    return {
        "en": en_list,
        "ja": ja_list,
        "th": th_list,
    }


def build_pair_decision(
    pair: str,
    prediction_fields: Dict[str, Any],
    fx_pair: Dict[str, Any],
) -> PairDecision:
    pred_bias, pred_notes = score_prediction_bias(prediction_fields)
    fx_bias, fx_notes = score_fx_bias(pair, fx_pair)

    combined = clamp(pred_bias + fx_bias, -1.0, 1.0)

    volatility_penalty = min(float(fx_pair["volatility_7d"]) * 0.08, 0.20)
    confidence = clamp(
        0.45
        + abs(combined) * 0.35
        + (float(prediction_fields["confidence"]) - 0.50) * 0.20
        - volatility_penalty,
        0.20,
        0.90,
    )

    decision = decision_from_score(
        score=combined,
        pred_conf=float(prediction_fields["confidence"]),
        vol_7d=float(fx_pair["volatility_7d"]),
    )

    watchpoints = list(prediction_fields["watchpoints"])
    prediction_watchpoints_count = len(watchpoints)

    if float(fx_pair["volatility_7d"]) >= 0.8:
        watchpoints.append("fx volatility expansion")

    if abs(float(fx_pair["change_7d_pct"])) >= 1.5:
        watchpoints.append("rapid 7d move")

    if abs(float(fx_pair["change_30d_pct"])) >= 3.0:
        watchpoints.append("large 30d move")

    dedup_watchpoints: List[str] = []
    dedup_indexes: List[int] = []
    seen = set()
    for idx, item in enumerate(watchpoints):
        key = str(item).strip().lower()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        dedup_watchpoints.append(str(item).strip())
        dedup_indexes.append(idx)

    remapped_prediction_i18n = {"en": [], "ja": [], "th": []}
    original_i18n = prediction_fields["watchpoints_i18n"]
    for idx in dedup_indexes:
        if idx < prediction_watchpoints_count:
            for lang in SUPPORTED_LANGUAGES:
                items = original_i18n.get(lang, [])
                remapped_prediction_i18n[lang].append(items[idx] if idx < len(items) else "")

    reason = build_reason(pair, decision, pred_notes, fx_notes)
    reason_i18n = build_reason_i18n(pair, decision, pred_notes, fx_notes)
    watchpoints_i18n = build_watchpoints_i18n(
        watchpoints=dedup_watchpoints,
        prediction_watchpoints_i18n=remapped_prediction_i18n,
        prediction_watchpoints_count=min(prediction_watchpoints_count, len(remapped_prediction_i18n["en"]) or prediction_watchpoints_count),
    )

    return PairDecision(
        pair=pair,
        decision=decision,
        reason=reason,
        reason_i18n=reason_i18n,
        confidence=round(confidence, 4),
        prediction_bias=round(pred_bias, 4),
        fx_bias=round(fx_bias, 4),
        combined_score=round(combined, 4),
        watchpoints=dedup_watchpoints,
        watchpoints_i18n=watchpoints_i18n,
        inputs={
            "prediction": {
                "overall_risk": prediction_fields["overall_risk"],
                "dominant_scenario": prediction_fields["dominant_scenario"],
                "prediction_confidence": prediction_fields["confidence"],
                "best_case": prediction_fields["best_case"],
                "base_case": prediction_fields["base_case"],
                "worst_case": prediction_fields["worst_case"],
                "prediction_statement": prediction_fields["prediction_statement"],
                "prediction_statement_i18n": prediction_fields["prediction_statement_i18n"],
                "primary_narrative": prediction_fields["primary_narrative"],
                "primary_narrative_i18n": prediction_fields["primary_narrative_i18n"],
                "summary": prediction_fields["summary"],
                "summary_i18n": prediction_fields["summary_i18n"],
            },
            "fx": fx_pair,
        },
    )


def pair_payload(as_of: str, engine_version: str, pd: PairDecision) -> Dict[str, Any]:
    mode = "defensive" if pd.decision in {"HOLD", "CAUTION"} else "adaptive"

    return {
        "as_of": as_of,
        "engine_version": engine_version,
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "pair": pd.pair,
        "pair_i18n": label_from_map(pd.pair, PAIR_LABELS),
        "decision": pd.decision,
        "decision_i18n": label_from_map(pd.decision, DECISION_LABELS),
        "status": pd.decision,
        "status_i18n": label_from_map(pd.decision, DECISION_LABELS),
        "action": pd.decision,
        "action_i18n": label_from_map(pd.decision, DECISION_LABELS),
        "recommendation": pd.decision,
        "recommendation_i18n": label_from_map(pd.decision, DECISION_LABELS),
        "reason": pd.reason,
        "reason_i18n": pd.reason_i18n,
        "confidence": pd.confidence,
        "watchpoints": pd.watchpoints,
        "watchpoints_i18n": pd.watchpoints_i18n,
        "inputs": pd.inputs,
        "scores": {
            "prediction_bias": pd.prediction_bias,
            "fx_bias": pd.fx_bias,
            "combined_score": pd.combined_score,
        },
        "policy": {
            "mode": mode,
            "split_allowed": True,
        },
    }


def aggregate_multi(
    as_of: str,
    engine_version: str,
    pair_results: List[PairDecision],
) -> Dict[str, Any]:
    if not pair_results:
        raise ValueError("pair_results is empty")

    primary = next((x for x in pair_results if x.pair == "JPYTHB"), pair_results[0])
    decisions = {x.pair: x.decision for x in pair_results}
    decisions_i18n = {x.pair: label_from_map(x.decision, DECISION_LABELS) for x in pair_results}
    avg_score = sum(x.combined_score for x in pair_results) / len(pair_results)
    avg_confidence = sum(x.confidence for x in pair_results) / len(pair_results)

    if primary.decision == "HOLD":
        overall = "HOLD"
    elif primary.decision == "SEND" and avg_score >= 0.10:
        overall = "SEND"
    elif any(x.decision == "CAUTION" for x in pair_results):
        overall = "CAUTION"
    else:
        overall = "SPLIT"

    summary_parts = [f"{x.pair}={x.decision}" for x in pair_results]
    reason = (
        f"Primary pair {primary.pair} suggests {primary.decision}. "
        f"Cross-pair summary: {', '.join(summary_parts)}."
    )

    pair_labels_primary = label_from_map(primary.pair, PAIR_LABELS)
    overall_labels = label_from_map(overall, DECISION_LABELS)
    ja_summary_parts = [
        f"{label_from_map(x.pair, PAIR_LABELS)['ja']}={label_from_map(x.decision, DECISION_LABELS)['ja']}"
        for x in pair_results
    ]
    th_summary_parts = [
        f"{label_from_map(x.pair, PAIR_LABELS)['th']}={label_from_map(x.decision, DECISION_LABELS)['th']}"
        for x in pair_results
    ]
    reason_i18n = {
        "en": reason,
        "ja": f"主対象ペア {pair_labels_primary['ja']} は {label_from_map(primary.decision, DECISION_LABELS)['ja']} を示唆。クロスペア要約: {', '.join(ja_summary_parts)}。",
        "th": f"คู่หลัก {pair_labels_primary['th']} ชี้ไปที่ {label_from_map(primary.decision, DECISION_LABELS)['th']}. สรุปข้ามคู่เงิน: {', '.join(th_summary_parts)}.",
    }

    merged_watchpoints: List[str] = []
    merged_watchpoints_i18n = {"en": [], "ja": [], "th": []}
    seen = set()
    for result in pair_results:
        en_items = result.watchpoints_i18n.get("en", [])
        ja_items = result.watchpoints_i18n.get("ja", [])
        th_items = result.watchpoints_i18n.get("th", [])
        for idx, item in enumerate(result.watchpoints):
            key = str(item).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            merged_watchpoints.append(str(item).strip())
            merged_watchpoints_i18n["en"].append(en_items[idx] if idx < len(en_items) else str(item).strip())
            merged_watchpoints_i18n["ja"].append(ja_items[idx] if idx < len(ja_items) else str(item).strip())
            merged_watchpoints_i18n["th"].append(th_items[idx] if idx < len(th_items) else str(item).strip())

    mode = "defensive" if overall in {"HOLD", "CAUTION"} else "adaptive"

    return {
        "as_of": as_of,
        "engine_version": engine_version,
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "pair": "MULTI",
        "pair_i18n": label_from_map("MULTI", PAIR_LABELS),
        "decision": overall,
        "decision_i18n": overall_labels,
        "status": overall,
        "status_i18n": overall_labels,
        "action": overall,
        "action_i18n": overall_labels,
        "recommendation": overall,
        "recommendation_i18n": overall_labels,
        "reason": reason,
        "reason_i18n": reason_i18n,
        "confidence": round(avg_confidence, 4),
        "pairs": decisions,
        "pairs_i18n": decisions_i18n,
        "scores": {
            "average_combined_score": round(avg_score, 4),
        },
        "watchpoints": merged_watchpoints,
        "watchpoints_i18n": merged_watchpoints_i18n,
        "policy": {
            "mode": mode,
            "split_allowed": True,
        },
    }


def parse_iso_date(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d")
    except ValueError:
        return None


def resolve_as_of(pred: Dict[str, Any], fx_inputs: Dict[str, Any]) -> str:
    pred_as_of = str(pred.get("as_of") or "").strip()
    fx_as_of = str(fx_inputs.get("as_of") or "").strip()

    pred_dt = parse_iso_date(pred_as_of)
    fx_dt = parse_iso_date(fx_as_of)

    if pred_dt and fx_dt:
        return pred_as_of if pred_dt >= fx_dt else fx_as_of
    if fx_as_of:
        return fx_as_of
    if pred_as_of:
        return pred_as_of
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="GenesisPrediction FX Decision Engine")
    parser.add_argument(
        "--prediction",
        type=Path,
        default=DEFAULT_PREDICTION_PATH,
        help="Path to prediction_latest.json",
    )
    parser.add_argument(
        "--fx-inputs",
        type=Path,
        default=DEFAULT_FX_INPUTS_PATH,
        help="Path to fx_inputs_latest.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for fx decision artifacts",
    )
    args = parser.parse_args()

    prediction = load_json(args.prediction)
    fx_inputs = load_json(args.fx_inputs)

    ensure_dir(args.output_dir)

    pred = extract_prediction_fields(prediction)
    as_of = resolve_as_of(pred, fx_inputs)
    engine_version = "fx_decision_engine_v1_i18n_phase1"

    pair_results: List[PairDecision] = []

    for pair in PAIR_ORDER:
        fx_pair = extract_pair_inputs(fx_inputs, pair)
        result = build_pair_decision(pair, pred, fx_pair)
        pair_results.append(result)

        payload = pair_payload(as_of, engine_version, result)
        write_json(args.output_dir / f"fx_decision_latest_{pair.lower()}.json", payload)

    multi_payload = aggregate_multi(as_of, engine_version, pair_results)

    write_json(args.output_dir / "fx_decision_latest_multi.json", multi_payload)
    write_json(args.output_dir / "fx_decision_latest.json", multi_payload)

    print(f"[fx_decision_engine] wrote {args.output_dir / 'fx_decision_latest.json'}")
    for pair in PAIR_ORDER:
        print(
            f"[fx_decision_engine] wrote "
            f"{args.output_dir / f'fx_decision_latest_{pair.lower()}.json'}"
        )
    print(f"[fx_decision_engine] wrote {args.output_dir / 'fx_decision_latest_multi.json'}")
    print(f"[fx_decision_engine] primary={multi_payload['decision']}")


if __name__ == "__main__":
    main()
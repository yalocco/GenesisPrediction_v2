#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
build_explanation_multilang.py

GenesisPrediction Prediction Layer
Explanation / Multi-language builder

Purpose:
- Generate multilingual explanation artifacts from structured prediction/scenario data
- Preserve current single-language fields for existing UI compatibility
- Add *_i18n fields deterministically
- Keep UI selector-only and analysis-generated translation model
- Avoid exact-match-only translation failure
- Humanize drivers / watchpoints / must_not_mean for EN / JA / TH

Inputs:
- analysis/prediction/prediction_latest.json
- analysis/prediction/scenario_latest.json

Outputs:
- analysis/explanation/prediction_explanation_latest.json
- analysis/explanation/scenario_explanation_latest.json
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"
EXPLANATION_DIR = ANALYSIS_DIR / "explanation"

PREDICTION_LATEST = PREDICTION_DIR / "prediction_latest.json"
SCENARIO_LATEST = PREDICTION_DIR / "scenario_latest.json"

PREDICTION_EXPLANATION_LATEST = EXPLANATION_DIR / "prediction_explanation_latest.json"
SCENARIO_EXPLANATION_LATEST = EXPLANATION_DIR / "scenario_explanation_latest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="as_of override (YYYY-MM-DD)")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def limit_list(value: Any, max_items: int = 3) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        s = normalize_text(item)
        if s:
            out.append(s)
    return out[:max_items]


def to_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    s = normalize_text(value)
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default


def fmt_confidence(value: Any) -> str:
    return f"{to_float(value, 0.0):.2f}"


def fmt_pct(value: Any) -> str:
    v = to_float(value, 0.0)
    if v <= 1.0:
        v *= 100.0
    return f"{v:.0f}%"


def pick_first(*values: Any, default: str = "") -> str:
    for value in values:
        s = normalize_text(value)
        if s:
            return s
    return default


RISK_LABELS = {
    "guarded": {"ja": "guarded", "en": "guarded", "th": "guarded"},
    "stable": {"ja": "安定", "en": "stable", "th": "ทรงตัว"},
    "elevated": {"ja": "警戒", "en": "elevated", "th": "ยกระดับ"},
    "high": {"ja": "高い", "en": "high", "th": "สูง"},
    "critical": {"ja": "危機", "en": "critical", "th": "วิกฤต"},
    "low": {"ja": "低い", "en": "low", "th": "ต่ำ"},
    "warn": {"ja": "警戒", "en": "warn", "th": "เตือน"},
}

SCENARIO_LABELS = {
    "best_case": {"ja": "best_case", "en": "best_case", "th": "best_case"},
    "base_case": {"ja": "base_case", "en": "base_case", "th": "base_case"},
    "worst_case": {"ja": "worst_case", "en": "worst_case", "th": "worst_case"},
}

KEY_LABELS = {
    "overall_direction_falling": {
        "ja": "全体方向が下向き",
        "en": "overall direction is falling",
        "th": "ทิศทางโดยรวมกำลังอ่อนลง",
    },
    "risk_level_critical": {
        "ja": "リスク水準が高止まり",
        "en": "risk level remains highly stressed",
        "th": "ระดับความเสี่ยงยังคงตึงตัวสูง",
    },
    "risk_pressure": {
        "ja": "リスク圧力が残存",
        "en": "risk pressure remains active",
        "th": "แรงกดดันด้านความเสี่ยงยังคงอยู่",
    },
    "regime_shift_pressure": {
        "ja": "レジーム転換圧力",
        "en": "regime-shift pressure is present",
        "th": "มีแรงกดดันต่อการเปลี่ยนระบอบ",
    },
    "pressure_easing": {
        "ja": "一部で圧力緩和の兆し",
        "en": "some easing pressure is visible",
        "th": "เริ่มมีสัญญาณผ่อนแรงบางส่วน",
    },
    "regime_shift_risk": {
        "ja": "レジーム変化リスク",
        "en": "risk of regime change remains",
        "th": "ความเสี่ยงของการเปลี่ยนระบอบยังคงอยู่",
    },
    "headline_pressure": {
        "ja": "ヘッドライン圧力",
        "en": "headline pressure remains elevated",
        "th": "แรงกดดันจากข่าวพาดหัว仍อยู่ในระดับสูง",
    },
    "stress_building": {
        "ja": "ストレス蓄積",
        "en": "stress is still building",
        "th": "ความตึงเครียดยังคงสะสม",
    },
    "bank_funding_stress": {
        "ja": "銀行資金調達ストレス",
        "en": "bank funding stress",
        "th": "ความตึงตัวของเงินทุนธนาคาร",
    },
    "credit_spread_widening": {
        "ja": "信用スプレッド拡大",
        "en": "credit spread widening",
        "th": "ส่วนต่างเครดิตขยายกว้างขึ้น",
    },
    "loan_loss_increase": {
        "ja": "貸倒増加",
        "en": "loan loss increase",
        "th": "หนี้เสียเพิ่มขึ้น",
    },
    "housing_or_equity_drawdown": {
        "ja": "住宅・株式の下落",
        "en": "housing or equity drawdown",
        "th": "การปรับลดลงของที่อยู่อาศัยหรือหุ้น",
    },
    "policy_emergency_liquidity": {
        "ja": "緊急流動性政策",
        "en": "policy emergency liquidity support",
        "th": "มาตรการสภาพคล่องฉุกเฉินของนโยบาย",
    },
    "fx_reserve_drop": {
        "ja": "外貨準備低下",
        "en": "foreign reserve decline",
        "th": "เงินสำรองระหว่างประเทศลดลง",
    },
    "forward_market_stress": {
        "ja": "先物市場ストレス",
        "en": "forward market stress",
        "th": "ความตึงเครียดในตลาดล่วงหน้า",
    },
    "sovereign_spread_widening": {
        "ja": "国債スプレッド拡大",
        "en": "sovereign spread widening",
        "th": "ส่วนต่างพันธบัตรรัฐบาลขยายกว้างขึ้น",
    },
    "capital_outflow": {
        "ja": "資本流出",
        "en": "capital outflow",
        "th": "เงินทุนไหลออก",
    },
    "banking_stress": {
        "ja": "銀行システムストレス",
        "en": "banking stress",
        "th": "ความตึงเครียดในระบบธนาคาร",
    },
    "currency_instability": {
        "ja": "通貨不安定",
        "en": "currency instability",
        "th": "ความไม่เสถียรของค่าเงิน",
    },
    "interbank_spread_surge": {
        "ja": "短期市場スプレッド急拡大",
        "en": "interbank spread surge",
        "th": "ส่วนต่างตลาดเงินระหว่างธนาคารพุ่งสูง",
    },
    "equities_down": {
        "ja": "株式下落",
        "en": "equities down",
        "th": "หุ้นปรับตัวลง",
    },
    "credit_spreads_up": {
        "ja": "信用スプレッド上昇",
        "en": "credit spreads up",
        "th": "ส่วนต่างเครดิตเพิ่มขึ้น",
    },
    "growth_down": {
        "ja": "成長減速",
        "en": "growth down",
        "th": "การเติบโตชะลอลง",
    },
    "unemployment_up": {
        "ja": "失業率上昇",
        "en": "unemployment up",
        "th": "การว่างงานเพิ่มขึ้น",
    },
    "safe_haven_up": {
        "ja": "安全資産選好",
        "en": "safe haven demand rises",
        "th": "ความต้องการสินทรัพย์ปลอดภัยเพิ่มขึ้น",
    },
    "currency_down": {
        "ja": "通貨下落",
        "en": "currency down",
        "th": "ค่าเงินอ่อนลง",
    },
    "inflation_up": {
        "ja": "インフレ上昇",
        "en": "inflation up",
        "th": "เงินเฟ้อเพิ่มขึ้น",
    },
    "rates_up": {
        "ja": "金利上昇",
        "en": "rates up",
        "th": "อัตราดอกเบี้ยเพิ่มขึ้น",
    },
    "default_risk_up": {
        "ja": "デフォルトリスク上昇",
        "en": "default risk up",
        "th": "ความเสี่ยงผิดนัดชำระเพิ่มขึ้น",
    },
    "volatility_up": {
        "ja": "変動率上昇",
        "en": "volatility up",
        "th": "ความผันผวนเพิ่มขึ้น",
    },
}

UI_TERM_MEANINGS = {
    "confidence": {
        "ja": "現在の観測とシナリオ整合性の強さであり、的中率ではない。",
        "en": "It measures the strength of alignment between current observation and scenario, not hit rate.",
        "th": "เป็นความแข็งแรงของความสอดคล้องระหว่างการสังเกตปัจจุบันกับ scenario ไม่ใช่อัตราทำนายถูก",
    },
    "dominant_scenario": {
        "ja": "現時点で最も支持が強い主枝であり、唯一の未来ではない。",
        "en": "It is the currently strongest branch, not the only possible future.",
        "th": "เป็นแขนงหลักที่ได้รับการสนับสนุนมากที่สุดในขณะนี้ ไม่ใช่อนาคตที่เป็นไปได้เพียงทางเดียว",
    },
    "watchpoints": {
        "ja": "今後シナリオを変えうる監視項目であり、結論そのものではない。",
        "en": "They are monitoring points that can change branch balance, not conclusions themselves.",
        "th": "เป็นจุดเฝ้าระวังที่อาจเปลี่ยนสมดุลของแขนง ไม่ใช่ข้อสรุปในตัวมันเอง",
    },
    "scenario": {
        "ja": "複数の未来分岐を整理した構造であり、単線予測ではない。",
        "en": "It is a structured set of multiple future branches, not a single prediction.",
        "th": "เป็นโครงสร้างของหลายแขนงอนาคต ไม่ใช่การคาดการณ์เพียงหนึ่งเดียว",
    },
    "base_case": {
        "ja": "現在の中心枝であり、固定未来ではない。",
        "en": "It is the current central branch, not a fixed future.",
        "th": "เป็นแขนงศูนย์กลางในปัจจุบัน ไม่ใช่อนาคตที่ตายตัว",
    },
}


def translate_key_generic(key: str) -> dict[str, str]:
    k = normalize_text(key).lower()
    if k in KEY_LABELS:
        return KEY_LABELS[k]

    readable = k.replace("_", " ").strip()
    if not readable:
        readable = "unknown"

    return {
        "ja": readable,
        "en": readable,
        "th": readable,
    }


def label_for_risk(risk: str) -> dict[str, str]:
    return RISK_LABELS.get(risk.lower(), {"ja": risk, "en": risk, "th": risk})


def label_for_scenario(scenario_name: str) -> dict[str, str]:
    return SCENARIO_LABELS.get(
        scenario_name.lower(),
        {"ja": scenario_name, "en": scenario_name, "th": scenario_name},
    )


def list_i18n_from_keys(items: list[str]) -> dict[str, list[str]]:
    out = {"ja": [], "en": [], "th": []}
    for item in items:
        row = translate_key_generic(item)
        out["ja"].append(row["ja"])
        out["en"].append(row["en"])
        out["th"].append(row["th"])
    return out


def term_meaning_i18n(term: str) -> dict[str, str]:
    t = normalize_text(term)
    return UI_TERM_MEANINGS.get(
        t,
        {"ja": t, "en": t, "th": t},
    )


def build_prediction_i18n(
    prediction: dict[str, Any],
    scenario: dict[str, Any],
    as_of: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    dominant = pick_first(
        prediction.get("dominant_scenario"),
        scenario.get("dominant"),
        scenario.get("dominant_scenario"),
        default="base_case",
    )
    risk = pick_first(prediction.get("risk"), prediction.get("overall_risk"), default="guarded")
    confidence = fmt_confidence(prediction.get("confidence", 0.0))

    scenario_label = label_for_scenario(dominant)
    risk_label = label_for_risk(risk)

    key_drivers = limit_list(prediction.get("key_drivers") or prediction.get("drivers") or [], max_items=3)
    watchpoints = limit_list(
        prediction.get("monitoring_priorities")
        or prediction.get("watchpoints")
        or scenario.get("watchpoints")
        or [],
        max_items=3,
    )
    expected_outcomes = limit_list(prediction.get("expected_outcomes") or [], max_items=3)
    risk_flags = limit_list(prediction.get("risk_flags") or [], max_items=3)

    pattern = pick_first(
        prediction.get("historical_context", {}).get("dominant_pattern")
        if isinstance(prediction.get("historical_context"), dict) else "",
        default="historical pattern unavailable",
    )
    analog = pick_first(
        prediction.get("historical_context", {}).get("dominant_analog")
        if isinstance(prediction.get("historical_context"), dict) else "",
        default="historical analog unavailable",
    )
    support = fmt_confidence(
        prediction.get("historical_context", {}).get("support_level")
        if isinstance(prediction.get("historical_context"), dict) else 0.0
    )

    headline_i18n = {
        "ja": f"現在の中心は {scenario_label['ja']} で、リスクは {risk_label['ja']}。重要な監視項目はまだ残っている。",
        "en": f"The current center is {scenario_label['en']}, with {risk_label['en']} risk. Important watchpoints still remain.",
        "th": f"ศูนย์กลางปัจจุบันคือ {scenario_label['th']} และความเสี่ยงอยู่ในระดับ {risk_label['th']} โดยยังมีจุดเฝ้าระวังสำคัญคงอยู่",
    }

    summary_i18n = {
        "ja": (
            f"Prediction は {dominant} 優勢で、risk は {risk_label['ja']}。"
            f"Confidence は {confidence}。"
            f"主要な歴史文脈は {pattern} / {analog} で、support は {support}。"
        ),
        "en": (
            f"Prediction is centered on {dominant}, with {risk_label['en']} risk. "
            f"Confidence is {confidence}. "
            f"The main historical context is {pattern} / {analog}, with support at {support}."
        ),
        "th": (
            f"Prediction มีศูนย์กลางอยู่ที่ {dominant} โดย risk อยู่ในระดับ {risk_label['th']} "
            f"และ Confidence อยู่ที่ {confidence} "
            f"บริบททางประวัติศาสตร์หลักคือ {pattern} / {analog} โดยมี support ที่ {support}"
        ),
    }

    why_i18n = {
        "ja": "confidence を的中率と誤解せず、watchpoints を発生確定イベントと取り違えないための補助説明である。",
        "en": "This is a supporting explanation so confidence is not mistaken for hit rate and watchpoints are not mistaken for confirmed events.",
        "th": "นี่คือคำอธิบายเสริมเพื่อไม่ให้เข้าใจผิดว่า confidence คืออัตราทำนายถูก และ watchpoints คือเหตุการณ์ที่ยืนยันแล้ว",
    }

    invalidation_i18n = {
        "ja": [
            f"dominant_scenario が {scenario_label['ja']} から離れた場合は再評価する。"
        ],
        "en": [
            f"Reassess if the dominant_scenario moves away from {scenario_label['en']}."
        ],
        "th": [
            f"ประเมินใหม่หาก dominant_scenario เปลี่ยนออกจาก {scenario_label['th']}"
        ],
    }

    must_not_mean_i18n = {
        "ja": [
            "prediction は確定未来ではない。",
            "confidence は的中率ではない。",
            "watchpoints は発生確定イベントではない。",
        ],
        "en": [
            "prediction is not a guaranteed future.",
            "confidence is not hit rate.",
            "watchpoints are not confirmed events.",
        ],
        "th": [
            "prediction ไม่ใช่อนาคตที่แน่นอน",
            "confidence ไม่ใช่อัตราทำนายถูก",
            "watchpoints ไม่ใช่เหตุการณ์ที่ยืนยันแล้ว",
        ],
    }

    drivers_i18n = list_i18n_from_keys(key_drivers)
    watchpoints_i18n = list_i18n_from_keys(watchpoints)
    expected_outcomes_i18n = list_i18n_from_keys(expected_outcomes)
    risk_flags_i18n = list_i18n_from_keys(risk_flags)

    ui_terms = [
        {"term": "confidence", "meaning_i18n": term_meaning_i18n("confidence")},
        {"term": "dominant_scenario", "meaning_i18n": term_meaning_i18n("dominant_scenario")},
        {"term": "watchpoints", "meaning_i18n": term_meaning_i18n("watchpoints")},
    ]

    doc = {
        "as_of": as_of,
        "subject": "prediction",
        "status": "ok",
        "lang_default": "ja",
        "languages": ["en", "ja", "th"],
        "headline": headline_i18n["ja"],
        "summary": summary_i18n["ja"],
        "why_it_matters": why_i18n["ja"],
        "drivers": drivers_i18n["ja"],
        "watchpoints": watchpoints_i18n["ja"],
        "invalidation": invalidation_i18n["ja"],
        "must_not_mean": must_not_mean_i18n["ja"],
        "headline_i18n": headline_i18n,
        "summary_i18n": summary_i18n,
        "why_it_matters_i18n": why_i18n,
        "drivers_i18n": drivers_i18n,
        "watchpoints_i18n": watchpoints_i18n,
        "expected_outcomes_i18n": expected_outcomes_i18n,
        "risk_flags_i18n": risk_flags_i18n,
        "invalidation_i18n": invalidation_i18n,
        "must_not_mean_i18n": must_not_mean_i18n,
        "based_on": [
            str(PREDICTION_LATEST),
            str(SCENARIO_LATEST),
        ],
        "ui_terms": ui_terms,
        "generated_at": utc_now_iso(),
    }

    return doc, {
        "dominant": dominant,
        "risk": risk,
        "confidence": confidence,
        "scenario_label": scenario_label,
    }


def build_scenario_i18n(
    prediction: dict[str, Any],
    scenario: dict[str, Any],
    as_of: str,
) -> dict[str, Any]:
    dominant = pick_first(
        scenario.get("dominant"),
        scenario.get("dominant_scenario"),
        prediction.get("dominant_scenario"),
        default="base_case",
    )
    scenario_label = label_for_scenario(dominant)

    best = fmt_pct(scenario.get("best_case") or scenario.get("best") or 0.15)
    base = fmt_pct(scenario.get("base_case") or scenario.get("base") or 0.44)
    worst = fmt_pct(scenario.get("worst_case") or scenario.get("worst") or 0.41)
    scenario_conf = fmt_confidence(scenario.get("confidence") or scenario.get("scenario_confidence") or 0.73)

    watchpoints = limit_list(
        scenario.get("watchpoints")
        or prediction.get("monitoring_priorities")
        or prediction.get("watchpoints")
        or [],
        max_items=3,
    )

    headline_i18n = {
        "ja": f"複数シナリオが併存し、現在の中心は {scenario_label['ja']} にある。",
        "en": f"Multiple scenarios coexist, and the current center is {scenario_label['en']}.",
        "th": f"มีหลาย scenario อยู่ร่วมกัน และศูนย์กลางปัจจุบันอยู่ที่ {scenario_label['th']}",
    }

    summary_i18n = {
        "ja": f"現在の scenario balance は best {best} / base {base} / worst {worst} で、scenario confidence は {scenario_conf}。",
        "en": f"The current scenario balance is best {best} / base {base} / worst {worst}, and scenario confidence is {scenario_conf}.",
        "th": f"สมดุล scenario ปัจจุบันคือ best {best} / base {base} / worst {worst} และ scenario confidence อยู่ที่ {scenario_conf}",
    }

    why_i18n = {
        "ja": "見通しを単線予測として誤読させず、分岐条件に注意を向けるため。",
        "en": "This helps prevent a single-line reading of the outlook and keeps attention on branch conditions.",
        "th": "เพื่อไม่ให้มองภาพคาดการณ์แบบเส้นเดียว และเพื่อให้ความสนใจไปที่เงื่อนไขการแตกแขนง",
    }

    drivers_i18n = {
        "ja": [
            f"{scenario_label['ja']} が現在の中心枝である。",
            f"worst_case 側も {worst} あり、無視できない。",
            "best_case 側へ進むには追加の緩和シグナルが必要。",
        ],
        "en": [
            f"{scenario_label['en']} is the current central branch.",
            f"The worst_case side is also {worst}, so it cannot be ignored.",
            "A stronger easing signal is needed to move toward best_case.",
        ],
        "th": [
            f"{scenario_label['th']} เป็นแขนงศูนย์กลางในปัจจุบัน",
            f"ฝั่ง worst_case ก็อยู่ที่ {worst} และไม่อาจมองข้ามได้",
            "การจะขยับไปสู่ best_case ต้องมีสัญญาณผ่อนคลายที่แรงกว่านี้",
        ],
    }

    watchpoints_i18n = list_i18n_from_keys(watchpoints)

    invalidation_i18n = {
        "ja": [f"branch balance が {scenario_label['ja']} を支えなくなった場合は再評価する。"],
        "en": [f"Reassess if branch balance no longer supports {scenario_label['en']}."],
        "th": [f"ประเมินใหม่หาก branch balance ไม่สนับสนุน {scenario_label['th']} อีกต่อไป"],
    }

    must_not_mean_i18n = {
        "ja": [
            "base_case は安全を意味しない。",
            "worst_case は確定未来ではない。",
            "best_case は条件付きであり保証ではない。",
        ],
        "en": [
            "base_case does not mean safety.",
            "worst_case is not a predetermined future.",
            "best_case is conditional and not guaranteed.",
        ],
        "th": [
            "base_case ไม่ได้หมายถึงความปลอดภัย",
            "worst_case ไม่ใช่อนาคตที่กำหนดไว้แน่นอน",
            "best_case เป็นเงื่อนไขเฉพาะ ไม่ใช่สิ่งที่รับประกัน",
        ],
    }

    doc = {
        "as_of": as_of,
        "subject": "scenario",
        "status": "ok",
        "lang_default": "ja",
        "languages": ["en", "ja", "th"],
        "headline": headline_i18n["ja"],
        "summary": summary_i18n["ja"],
        "why_it_matters": why_i18n["ja"],
        "drivers": drivers_i18n["ja"],
        "watchpoints": watchpoints_i18n["ja"],
        "invalidation": invalidation_i18n["ja"],
        "must_not_mean": must_not_mean_i18n["ja"],
        "headline_i18n": headline_i18n,
        "summary_i18n": summary_i18n,
        "why_it_matters_i18n": why_i18n,
        "drivers_i18n": drivers_i18n,
        "watchpoints_i18n": watchpoints_i18n,
        "invalidation_i18n": invalidation_i18n,
        "must_not_mean_i18n": must_not_mean_i18n,
        "scenario_structure": {
            "dominant": dominant,
            "alternatives": ["best_case", "worst_case"],
            "balance": f"best {best} / base {base} / worst {worst}",
        },
        "based_on": [
            str(SCENARIO_LATEST),
            str(PREDICTION_LATEST),
        ],
        "ui_terms": [
            {"term": "scenario", "meaning_i18n": term_meaning_i18n("scenario")},
            {"term": "base_case", "meaning_i18n": term_meaning_i18n("base_case")},
        ],
        "generated_at": utc_now_iso(),
    }
    return doc


def main() -> int:
    args = parse_args()

    prediction = load_json(PREDICTION_LATEST) or {}
    scenario = load_json(SCENARIO_LATEST) or {}

    as_of = args.date or normalize_text(prediction.get("as_of")) or normalize_text(scenario.get("as_of"))
    if not as_of:
        as_of = datetime.now().strftime("%Y-%m-%d")

    prediction_doc, _ = build_prediction_i18n(prediction, scenario, as_of)
    scenario_doc = build_scenario_i18n(prediction, scenario, as_of)

    prediction_doc["generated_at"] = utc_now_iso()
    scenario_doc["generated_at"] = utc_now_iso()

    write_json(PREDICTION_EXPLANATION_LATEST, prediction_doc)
    write_json(SCENARIO_EXPLANATION_LATEST, scenario_doc)

    print(f"[OK] wrote {PREDICTION_EXPLANATION_LATEST}")
    print(f"[OK] wrote {SCENARIO_EXPLANATION_LATEST}")
    print("[OK] multilingual explanation meaning layer finalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
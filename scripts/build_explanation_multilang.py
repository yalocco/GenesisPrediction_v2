#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
build_explanation_multilang.py

GenesisPrediction Prediction Layer Phase4
Explanation / Multi-language builder (finalized meaning layer)

Purpose:
- Generate multilingual shadow fields for explanation artifacts
- Preserve current single-language fields for existing UI compatibility
- Add *_i18n fields deterministically
- Keep UI selector-only and analysis-generated translation model
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
    return ""


def limit_list(value: Any, max_items: int = 3) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            s = item.strip()
            if s:
                out.append(s)
    return out[:max_items]


WATCHPOINT_LABELS = {
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
}

WATCHPOINT_MEANING = {
    "bank_funding_stress": {
        "ja": "銀行の資金繰り圧力が強まる兆候",
        "en": "signs that bank funding pressure is intensifying",
        "th": "สัญญาณว่าความกดดันด้านเงินทุนของธนาคารกำลังรุนแรงขึ้น",
    },
    "credit_spread_widening": {
        "ja": "信用不安の広がりを示すスプレッド拡大",
        "en": "widening spreads that signal rising credit stress",
        "th": "ส่วนต่างที่กว้างขึ้นซึ่งบ่งชี้ว่าความตึงเครียดด้านเครดิตเพิ่มขึ้น",
    },
    "loan_loss_increase": {
        "ja": "貸倒損失の増加傾向",
        "en": "an increase in expected or realized loan losses",
        "th": "แนวโน้มหนี้เสียหรือความสูญเสียจากสินเชื่อที่เพิ่มขึ้น",
    },
    "housing_or_equity_drawdown": {
        "ja": "住宅または株式価格の下落圧力",
        "en": "downward pressure in housing or equity prices",
        "th": "แรงกดดันขาลงในราคาที่อยู่อาศัยหรือหุ้น",
    },
    "policy_emergency_liquidity": {
        "ja": "当局による緊急流動性支援の必要性",
        "en": "a need for emergency liquidity support by policymakers",
        "th": "ความจำเป็นในการอัดฉีดสภาพคล่องฉุกเฉินโดยภาครัฐหรือธนาคารกลาง",
    },
    "fx_reserve_drop": {
        "ja": "外貨準備の減少圧力",
        "en": "pressure from declining foreign reserves",
        "th": "แรงกดดันจากเงินสำรองระหว่างประเทศที่ลดลง",
    },
}


JA_TO_EN_EXACT = {
    "現在は base_case 優勢だが、重要な watchpoints はまだ残っている。":
        "base_case remains dominant for now, but important watchpoints are still active.",
    "Prediction は historically_guarded 寄りで、risk は 安定。Confidence は 0.60。歴史文脈は 債務バブル・銀行危機型 と 1997年アジア通貨危機 が中心。":
        "Prediction leans historically_guarded, risk is stable, and confidence is 0.60. The main historical context is a debt-bubble banking-crisis pattern with the 1997 Asian financial crisis as the closest analog.",
    "confidence を的中率と誤解せず、watchpoints を発生確定イベントと取り違えないための補助説明である。":
        "This is a supporting explanation so confidence is not mistaken for hit rate and watchpoints are not mistaken for confirmed events.",
    "The current dominant branch is base_case.":
        "The current dominant branch is base_case.",
    "Risk is not in rapid expansion and remains stable.":
        "Risk is not in rapid expansion and remains stable.",
    "Historical support is centered on the debt-bubble banking-crisis pattern / the 1997 Asian financial crisis (33%).":
        "Historical support is centered on the debt-bubble banking-crisis pattern / the 1997 Asian financial crisis (33%).",
    "Prediction is not a guaranteed future.":
        "Prediction is not a guaranteed future.",
    "Confidence is not hit rate.":
        "Confidence is not hit rate.",
    "Watchpoints are not confirmed events.":
        "Watchpoints are not confirmed events.",
    "It measures the strength of alignment between current observation and scenario, not hit rate.":
        "It measures the strength of alignment between current observation and scenario, not hit rate.",
    "It is the currently strongest branch, not the only possible future.":
        "It is the currently strongest branch, not the only possible future.",
    "They are monitoring points that can change branch balance, not conclusions themselves.":
        "They are monitoring points that can change branch balance, not conclusions themselves.",
    "複数シナリオが併存し、現在のバランス中心は base_case にある。":
        "Multiple scenarios coexist, and the current balance is centered on base_case.",
    "現在の scenario balance は best 15% / base 44% / worst 41% で、scenario confidence は 0.73。":
        "The current scenario balance is best 15% / base 44% / worst 41%, and scenario confidence is 0.73.",
    "見通しを単線予測として誤読させず、分岐条件に注意を向けるため。":
        "This helps prevent a single-line reading of the outlook and keeps attention on branch conditions.",
    "base_case currently has the largest branch weight.":
        "base_case currently has the largest branch weight.",
    "The worst_case side is also 41%, so it cannot be ignored.":
        "The worst_case side is also 41%, so it cannot be ignored.",
    "A stronger easing signal is needed to move toward best_case.":
        "A stronger easing signal is needed to move toward best_case.",
    "base_case does not mean safety.":
        "base_case does not mean safety.",
    "worst_case is not a predetermined future.":
        "worst_case is not a predetermined future.",
    "best_case is conditional and not guaranteed.":
        "best_case is conditional and not guaranteed.",
    "It is a structured set of multiple future branches, not a single prediction.":
        "It is a structured set of multiple future branches, not a single prediction.",
    "It is the current central branch, not a fixed future.":
        "It is the current central branch, not a fixed future.",
    "Reassess if dominant_scenario moves away from base_case.":
        "Reassess if dominant_scenario moves away from base_case.",
    "Reassess if branch balance no longer supports base_case.":
        "Reassess if branch balance no longer supports base_case.",
}

JA_TO_TH_EXACT = {
    "現在は base_case 優勢だが、重要な watchpoints はまだ残っている。":
        "ขณะนี้ base_case ยังเป็นแกนหลัก แต่ยังมี watchpoints สำคัญที่ต้องเฝ้าระวัง",
    "Prediction は historically_guarded 寄りで、risk は 安定。Confidence は 0.60。歴史文脈は 債務バブル・銀行危機型 と 1997年アジア通貨危機 が中心。":
        "Prediction เอนเอียงไปทาง historically_guarded โดย risk ยังทรงตัว และ Confidence อยู่ที่ 0.60 บริบททางประวัติศาสตร์หลักคือรูปแบบฟองสบู่หนี้/วิกฤตธนาคาร และวิกฤตการเงินเอเชียปี 1997",
    "confidence を的中率と誤解せず、watchpoints を発生確定イベントと取り違えないための補助説明である。":
        "นี่คือคำอธิบายเสริมเพื่อไม่ให้เข้าใจผิดว่า confidence คืออัตราทำนายถูก และ watchpoints คือเหตุการณ์ที่ยืนยันแล้ว",
    "The current dominant branch is base_case.":
        "แนวโน้มหลักปัจจุบันคือ base_case",
    "Risk is not in rapid expansion and remains stable.":
        "risk ไม่ได้ขยายตัวอย่างรวดเร็วและยังคงอยู่ในภาวะทรงตัว",
    "Historical support is centered on the debt-bubble banking-crisis pattern / the 1997 Asian financial crisis (33%).":
        "บริบททางประวัติศาสตร์หลักคือรูปแบบฟองสบู่หนี้/วิกฤตธนาคาร และวิกฤตการเงินเอเชียปี 1997 (33%)",
    "Prediction is not a guaranteed future.":
        "prediction ไม่ใช่อนาคตที่แน่นอน",
    "Confidence is not hit rate.":
        "confidence ไม่ใช่อัตราทำนายถูก",
    "Watchpoints are not confirmed events.":
        "watchpoints ไม่ใช่เหตุการณ์ที่ยืนยันแล้ว",
    "It measures the strength of alignment between current observation and scenario, not hit rate.":
        "เป็นความแข็งแรงของความสอดคล้องระหว่างการสังเกตปัจจุบันกับ scenario ไม่ใช่อัตราทำนายถูก",
    "It is the currently strongest branch, not the only possible future.":
        "เป็นแขนงหลักที่ได้รับการสนับสนุนมากที่สุดในขณะนี้ ไม่ใช่อนาคตที่เป็นไปได้เพียงทางเดียว",
    "They are monitoring points that can change branch balance, not conclusions themselves.":
        "เป็นจุดเฝ้าระวังที่อาจเปลี่ยนสมดุลของแขนง ไม่ใช่ข้อสรุปในตัวมันเอง",
    "複数シナリオが併存し、現在のバランス中心は base_case にある。":
        "มีหลาย scenario อยู่ร่วมกัน และดุลปัจจุบันมีศูนย์กลางอยู่ที่ base_case",
    "現在の scenario balance は best 15% / base 44% / worst 41% で、scenario confidence は 0.73。":
        "สมดุล scenario ปัจจุบันคือ best 15% / base 44% / worst 41% และ scenario confidence อยู่ที่ 0.73",
    "見通しを単線予測として誤読させず、分岐条件に注意を向けるため。":
        "เพื่อไม่ให้มองภาพคาดการณ์แบบเส้นเดียว และเพื่อให้ความสนใจไปที่เงื่อนไขการแตกแขนง",
    "base_case currently has the largest branch weight.":
        "base_case มี branch weight มากที่สุดในขณะนี้",
    "The worst_case side is also 41%, so it cannot be ignored.":
        "ฝั่ง worst_case ก็อยู่ที่ 41% และไม่อาจมองข้ามได้",
    "A stronger easing signal is needed to move toward best_case.":
        "การจะขยับไปสู่ best_case ต้องมีสัญญาณผ่อนคลายที่แรงกว่านี้",
    "base_case does not mean safety.":
        "base_case ไม่ได้หมายถึงความปลอดภัย",
    "worst_case is not a predetermined future.":
        "worst_case ไม่ใช่อนาคตที่กำหนดไว้แน่นอน",
    "best_case is conditional and not guaranteed.":
        "best_case เป็นเงื่อนไขเฉพาะ ไม่ใช่สิ่งที่รับประกัน",
    "It is a structured set of multiple future branches, not a single prediction.":
        "เป็นโครงสร้างของหลายแขนงอนาคต ไม่ใช่การคาดการณ์เพียงหนึ่งเดียว",
    "It is the current central branch, not a fixed future.":
        "เป็นแขนงศูนย์กลางในปัจจุบัน ไม่ใช่อนาคตที่ตายตัว",
    "Reassess if dominant_scenario moves away from base_case.":
        "หาก dominant_scenario เปลี่ยนออกจาก base_case ต้องประเมินใหม่",
    "Reassess if branch balance no longer supports base_case.":
        "หาก branch balance ไม่สนับสนุน base_case อีกต่อไป ต้องประเมินใหม่",
}


def translate_text_en(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""
    return JA_TO_EN_EXACT.get(text, text)


def translate_text_th(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""
    return JA_TO_TH_EXACT.get(text, text)


def to_i18n_text(ja_text: str) -> dict[str, str]:
    ja = normalize_text(ja_text)
    return {
        "en": translate_text_en(ja),
        "ja": ja,
        "th": translate_text_th(ja),
    }


def to_i18n_list_from_ja(items: list[str]) -> dict[str, list[str]]:
    ja_items = [normalize_text(x) for x in items if normalize_text(x)]
    return {
        "en": [translate_text_en(x) for x in ja_items],
        "ja": ja_items,
        "th": [translate_text_th(x) for x in ja_items],
    }


def watchpoint_display(key: str) -> dict[str, str]:
    normalized = normalize_text(key)
    return WATCHPOINT_LABELS.get(
        normalized,
        {"ja": normalized, "en": normalized, "th": normalized}
    )


def watchpoint_meaning_line(key: str) -> dict[str, str]:
    normalized = normalize_text(key)
    label = watchpoint_display(normalized)
    meaning = WATCHPOINT_MEANING.get(normalized)

    if meaning is None:
        return label

    return {
        "ja": f"{label['ja']}（{meaning['ja']}）",
        "en": f"{label['en']} ({meaning['en']})",
        "th": f"{label['th']} ({meaning['th']})",
    }


def watchpoints_to_i18n(items: list[str]) -> dict[str, list[str]]:
    ja_list, en_list, th_list = [], [], []
    for item in items:
        row = watchpoint_meaning_line(item)
        ja_list.append(row["ja"])
        en_list.append(row["en"])
        th_list.append(row["th"])
    return {"en": en_list, "ja": ja_list, "th": th_list}


def ensure_term_meaning_i18n(doc: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(doc)
    terms = out.get("ui_terms")
    if not isinstance(terms, list):
        return out

    new_terms = []
    for item in terms:
        if not isinstance(item, dict):
            continue
        copied = deepcopy(item)
        meaning = normalize_text(copied.get("meaning"))
        copied["meaning_i18n"] = to_i18n_text(meaning)
        new_terms.append(copied)
    out["ui_terms"] = new_terms
    return out


def build_prediction_doc(prediction: dict[str, Any], scenario: dict[str, Any], as_of: str) -> dict[str, Any]:
    watchpoints_raw = limit_list(
        prediction.get("watchpoints") or scenario.get("watchpoints") or [],
        max_items=3,
    )

    return {
        "as_of": as_of,
        "subject": "prediction",
        "status": "ok",
        "lang_default": "ja",
        "languages": ["en", "ja", "th"],
        "headline": "現在は base_case 優勢だが、重要な watchpoints はまだ残っている。",
        "summary": "Prediction は historically_guarded 寄りで、risk は 安定。Confidence は 0.60。歴史文脈は 債務バブル・銀行危機型 と 1997年アジア通貨危機 が中心。",
        "why_it_matters": "confidence を的中率と誤解せず、watchpoints を発生確定イベントと取り違えないための補助説明である。",
        "drivers": [
            "The current dominant branch is base_case.",
            "Risk is not in rapid expansion and remains stable.",
            "Historical support is centered on the debt-bubble banking-crisis pattern / the 1997 Asian financial crisis (33%).",
        ],
        "watchpoints": watchpoints_raw,
        "invalidation": [
            "Reassess if dominant_scenario moves away from base_case."
        ],
        "must_not_mean": [
            "Prediction is not a guaranteed future.",
            "Confidence is not hit rate.",
            "Watchpoints are not confirmed events.",
        ],
        "based_on": [
            str(PREDICTION_LATEST),
            str(SCENARIO_LATEST),
        ],
        "ui_terms": [
            {
                "term": "confidence",
                "meaning": "It measures the strength of alignment between current observation and scenario, not hit rate.",
            },
            {
                "term": "dominant_scenario",
                "meaning": "It is the currently strongest branch, not the only possible future.",
            },
            {
                "term": "watchpoints",
                "meaning": "They are monitoring points that can change branch balance, not conclusions themselves.",
            },
        ],
        "generated_at": utc_now_iso(),
    }


def build_scenario_doc(prediction: dict[str, Any], scenario: dict[str, Any], as_of: str) -> dict[str, Any]:
    watchpoints_raw = limit_list(
        scenario.get("watchpoints") or prediction.get("watchpoints") or [],
        max_items=3,
    )

    dominant = normalize_text(
        scenario.get("dominant")
        or scenario.get("dominant_scenario")
        or prediction.get("dominant_scenario")
        or "base_case"
    ) or "base_case"

    return {
        "as_of": as_of,
        "subject": "scenario",
        "status": "ok",
        "lang_default": "ja",
        "languages": ["en", "ja", "th"],
        "headline": "複数シナリオが併存し、現在のバランス中心は base_case にある。",
        "summary": "現在の scenario balance は best 15% / base 44% / worst 41% で、scenario confidence は 0.73。",
        "why_it_matters": "見通しを単線予測として誤読させず、分岐条件に注意を向けるため。",
        "drivers": [
            "base_case currently has the largest branch weight.",
            "The worst_case side is also 41%, so it cannot be ignored.",
            "A stronger easing signal is needed to move toward best_case.",
        ],
        "watchpoints": watchpoints_raw,
        "invalidation": [
            "Reassess if branch balance no longer supports base_case."
        ],
        "must_not_mean": [
            "base_case does not mean safety.",
            "worst_case is not a predetermined future.",
            "best_case is conditional and not guaranteed.",
        ],
        "scenario_structure": {
            "dominant": dominant,
            "alternatives": ["best_case", "worst_case"],
            "balance": "best 15% / base 44% / worst 41%",
        },
        "based_on": [
            str(SCENARIO_LATEST),
            str(PREDICTION_LATEST),
        ],
        "ui_terms": [
            {
                "term": "scenario",
                "meaning": "It is a structured set of multiple future branches, not a single prediction.",
            },
            {
                "term": "base_case",
                "meaning": "It is the current central branch, not a fixed future.",
            },
        ],
        "generated_at": utc_now_iso(),
    }


def attach_i18n(doc: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(doc)

    out["headline_i18n"] = to_i18n_text(out.get("headline", ""))
    out["summary_i18n"] = to_i18n_text(out.get("summary", ""))
    out["why_it_matters_i18n"] = to_i18n_text(out.get("why_it_matters", ""))

    drivers = limit_list(out.get("drivers", []), max_items=3)
    out["drivers_i18n"] = to_i18n_list_from_ja(drivers)

    raw_watchpoints = limit_list(out.get("watchpoints", []), max_items=3)
    out["watchpoints_i18n"] = watchpoints_to_i18n(raw_watchpoints)
    out["watchpoints"] = out["watchpoints_i18n"]["ja"]

    invalidation = limit_list(out.get("invalidation", []), max_items=3)
    out["invalidation_i18n"] = to_i18n_list_from_ja(invalidation)

    must_not_mean = limit_list(out.get("must_not_mean", []), max_items=3)
    out["must_not_mean_i18n"] = to_i18n_list_from_ja(must_not_mean)

    out = ensure_term_meaning_i18n(out)
    return out


def main() -> int:
    args = parse_args()

    prediction = load_json(PREDICTION_LATEST) or {}
    scenario = load_json(SCENARIO_LATEST) or {}

    as_of = args.date or normalize_text(prediction.get("as_of")) or normalize_text(scenario.get("as_of"))
    if not as_of:
        as_of = datetime.now().strftime("%Y-%m-%d")

    prediction_doc = attach_i18n(build_prediction_doc(prediction, scenario, as_of))
    scenario_doc = attach_i18n(build_scenario_doc(prediction, scenario, as_of))

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenesisPrediction v2
Prediction History Index Builder

Purpose:
- Read prediction history snapshots
- Build a lightweight prediction_history_index.json
- Provide a stable UI-friendly history source
- Materialize history i18n fields on the analysis side

Input:
- analysis/prediction/history/YYYY-MM-DD/prediction.json

Primary Output:
- data/prediction/prediction_history_index.json

Compatibility Output:
- analysis/prediction/prediction_history_index.json
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"
HISTORY_DIR = PREDICTION_DIR / "history"
DATA_PREDICTION_DIR = ROOT / "data" / "prediction"
DATA_INDEX_PATH = DATA_PREDICTION_DIR / "prediction_history_index.json"
ANALYSIS_INDEX_PATH = PREDICTION_DIR / "prediction_history_index.json"

LANG_DEFAULT = "en"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]

RISK_LABELS: Dict[str, Dict[str, str]] = {
    "low": {"en": "Low", "ja": "低", "th": "ต่ำ"},
    "guarded": {"en": "Guarded", "ja": "警戒", "th": "เฝ้าระวัง"},
    "moderate": {"en": "Moderate", "ja": "中", "th": "ปานกลาง"},
    "high": {"en": "High", "ja": "高", "th": "สูง"},
    "critical": {"en": "Critical", "ja": "危機", "th": "วิกฤต"},
    "unknown": {"en": "Unknown", "ja": "不明", "th": "ไม่ทราบ"},
}

SCENARIO_LABELS: Dict[str, Dict[str, str]] = {
    "best_case": {"en": "Best Case", "ja": "最良シナリオ", "th": "กรณีดีที่สุด"},
    "base_case": {"en": "Base Case", "ja": "基本シナリオ", "th": "กรณีฐาน"},
    "worst_case": {"en": "Worst Case", "ja": "最悪シナリオ", "th": "กรณีเลวร้ายที่สุด"},
    "unknown": {"en": "Unknown", "ja": "不明", "th": "ไม่ทราบ"},
}

GENERIC_LABELS: Dict[str, Dict[str, str]] = {
    "headline risk pressure": {
        "en": "headline risk pressure",
        "ja": "見出しリスク圧力",
        "th": "แรงกดดันความเสี่ยงจากพาดหัวข่าว",
    },
    "summary risk score": {
        "en": "summary risk score",
        "ja": "要約リスクスコア",
        "th": "คะแนนความเสี่ยงจากสรุป",
    },
    "uncertainty": {
        "en": "uncertainty",
        "ja": "不確実性",
        "th": "ความไม่แน่นอน",
    },
    "no strong risk headline pressure detected": {
        "en": "no strong risk headline pressure detected",
        "ja": "強いリスク見出し圧力はまだ検出されていません",
        "th": "ยังไม่ตรวจพบแรงกดดันความเสี่ยงจากพาดหัวข่าวที่รุนแรง",
    },
    "uncertainty elevated": {
        "en": "uncertainty elevated",
        "ja": "不確実性が高まっています",
        "th": "ความไม่แน่นอนอยู่ในระดับสูง",
    },
    "summary risk score elevated": {
        "en": "summary risk score elevated",
        "ja": "要約リスクスコアが上昇しています",
        "th": "คะแนนความเสี่ยงจากสรุปอยู่ในระดับสูง",
    },
    "adverse signals fade": {
        "en": "adverse signals fade",
        "ja": "悪化シグナルが後退する",
        "th": "สัญญาณเชิงลบอ่อนลง",
    },
    "volatility compresses": {
        "en": "volatility compresses",
        "ja": "ボラティリティが縮小する",
        "th": "ความผันผวนลดลง",
    },
    "clear improvement signals dominate": {
        "en": "clear improvement signals dominate",
        "ja": "明確な改善シグナルが優勢になる",
        "th": "สัญญาณการฟื้นตัวที่ชัดเจนกลายเป็นแรงหลัก",
    },
    "major escalation breaks out": {
        "en": "major escalation breaks out",
        "ja": "大きなエスカレーションが発生する",
        "th": "เกิดการยกระดับครั้งใหญ่",
    },
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or isinstance(value, bool):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def ensure_lang_map(value: Any, fallback_en: str = "") -> Dict[str, str]:
    fb = clean_text(fallback_en)
    if isinstance(value, dict):
        return {
            "en": clean_text(value.get("en") or fb),
            "ja": clean_text(value.get("ja") or value.get("en") or fb),
            "th": clean_text(value.get("th") or value.get("en") or fb),
        }
    return {"en": fb, "ja": fb, "th": fb}


def ensure_lang_list(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []
    out: List[Dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            out.append(ensure_lang_map(item, item.get("en", "")))
        else:
            text = clean_text(item)
            out.append({"en": text, "ja": text, "th": text})
    return out


def labelize_text(text: Any) -> Dict[str, str]:
    raw = clean_text(text)
    if not raw:
        return {"en": "", "ja": "", "th": ""}
    mapped = GENERIC_LABELS.get(raw) or GENERIC_LABELS.get(raw.lower())
    if mapped:
        return ensure_lang_map(mapped, raw)
    return {"en": raw, "ja": raw, "th": raw}


def labelize_list(values: Any) -> List[Dict[str, str]]:
    if isinstance(values, list):
        return [
            labelize_text(v) if not isinstance(v, dict) else ensure_lang_map(v, v.get("en", ""))
            for v in values
        ]
    return []


def scenario_label_map(value: Any) -> Dict[str, str]:
    raw = clean_text(value).lower()
    mapped = SCENARIO_LABELS.get(raw) or SCENARIO_LABELS["unknown"]
    return ensure_lang_map(mapped, clean_text(value))


def risk_label_map(value: Any) -> Dict[str, str]:
    raw = clean_text(value).lower()
    mapped = RISK_LABELS.get(raw) or RISK_LABELS["unknown"]
    return ensure_lang_map(mapped, clean_text(value))


def first_non_empty(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def normalize_entry(date_str: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    probs = payload.get("scenario_probabilities", {})
    meta = payload.get("meta", {}) if isinstance(payload.get("meta"), dict) else {}

    overall_risk = first_non_empty(
        payload.get("overall_risk"),
        payload.get("risk"),
        payload.get("risk_level"),
        "unknown",
    )
    dominant_scenario = first_non_empty(
        payload.get("dominant_scenario"),
        payload.get("scenario"),
        "unknown",
    )
    summary = first_non_empty(
        payload.get("summary"),
        payload.get("prediction_statement"),
        payload.get("primary_narrative"),
    )

    watchpoints = payload.get("watchpoints")
    if not isinstance(watchpoints, list) or not watchpoints:
        watchpoints = payload.get("monitoring_priorities", []) if isinstance(payload.get("monitoring_priorities"), list) else []

    drivers = payload.get("drivers")
    if not isinstance(drivers, list) or not drivers:
        drivers = payload.get("key_drivers", []) if isinstance(payload.get("key_drivers"), list) else []

    invalidation_conditions = payload.get("invalidation_conditions")
    if not isinstance(invalidation_conditions, list):
        invalidation_conditions = payload.get("invalidation", []) if isinstance(payload.get("invalidation"), list) else []

    summary_i18n = ensure_lang_map(payload.get("summary_i18n"), summary)
    dominant_scenario_i18n = ensure_lang_map(payload.get("dominant_scenario_i18n"), dominant_scenario)
    if not dominant_scenario_i18n.get("en"):
        dominant_scenario_i18n = scenario_label_map(dominant_scenario)

    overall_risk_i18n = ensure_lang_map(payload.get("overall_risk_i18n"), overall_risk)
    if not overall_risk_i18n.get("en"):
        overall_risk_i18n = risk_label_map(overall_risk)

    drivers_i18n = ensure_lang_list(payload.get("drivers_i18n"))
    if not drivers_i18n:
        drivers_i18n = ensure_lang_list(payload.get("key_drivers_i18n"))
    if not drivers_i18n:
        drivers_i18n = labelize_list(drivers)

    watchpoints_i18n = ensure_lang_list(payload.get("watchpoints_i18n"))
    if not watchpoints_i18n:
        watchpoints_i18n = ensure_lang_list(payload.get("monitoring_priorities_i18n"))
    if not watchpoints_i18n:
        watchpoints_i18n = labelize_list(watchpoints)

    invalidation_i18n = ensure_lang_list(payload.get("invalidation_conditions_i18n"))
    if not invalidation_i18n:
        invalidation_i18n = ensure_lang_list(payload.get("invalidation_i18n"))
    if not invalidation_i18n:
        invalidation_i18n = labelize_list(invalidation_conditions)

    return {
        "date": date_str,
        "as_of": first_non_empty(payload.get("as_of"), date_str),
        "generated_at": payload.get("generated_at"),
        "lang_default": clean_text(payload.get("lang_default") or LANG_DEFAULT),
        "languages": payload.get("languages") if isinstance(payload.get("languages"), list) else SUPPORTED_LANGUAGES,
        "horizon": first_non_empty(payload.get("horizon"), payload.get("horizon_days"), "7d"),
        "overall_risk": overall_risk,
        "confidence": round(safe_float(payload.get("confidence")), 4),
        "dominant_scenario": dominant_scenario,
        "best_case": round(safe_float(probs.get("best_case") or payload.get("best_case")), 4),
        "base_case": round(safe_float(probs.get("base_case") or payload.get("base_case")), 4),
        "worst_case": round(safe_float(probs.get("worst_case") or payload.get("worst_case")), 4),
        "summary": summary,
        "watchpoints": watchpoints if isinstance(watchpoints, list) else [],
        "drivers": drivers if isinstance(drivers, list) else [],
        "invalidation_conditions": invalidation_conditions if isinstance(invalidation_conditions, list) else [],
        "signal_count": int(safe_float(meta.get("signal_count") or payload.get("signal_count"), 0)),
        "summary_i18n": summary_i18n,
        "dominant_scenario_i18n": dominant_scenario_i18n,
        "overall_risk_i18n": overall_risk_i18n,
        "drivers_i18n": drivers_i18n,
        "watchpoints_i18n": watchpoints_i18n,
        "invalidation_conditions_i18n": invalidation_i18n,
    }


def list_history_dates() -> List[Path]:
    if not HISTORY_DIR.exists():
        return []
    return sorted(
        [p for p in HISTORY_DIR.iterdir() if p.is_dir() and p.name and len(p.name) == 10],
        key=lambda p: p.name,
    )


def build_index(limit: Optional[int] = None) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    date_dirs = list_history_dates()

    for date_dir in date_dirs:
        prediction_path = date_dir / "prediction.json"
        if not prediction_path.exists():
            continue

        try:
            payload = load_json(prediction_path)
        except Exception:
            continue

        if not isinstance(payload, dict):
            continue

        rows.append(normalize_entry(date_dir.name, payload))

    if limit is not None and limit > 0:
        rows = rows[-limit:]

    latest = rows[-1] if rows else None

    return {
        "generated_at": utc_now_iso(),
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "root": str(HISTORY_DIR.relative_to(ROOT)).replace("\\", "/"),
        "count": len(rows),
        "latest_date": latest["date"] if latest else None,
        "items": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build prediction history index.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Keep only the latest N history rows in the index",
    )
    return parser.parse_args()


def write_all_outputs(payload: Dict[str, Any]) -> None:
    write_json(DATA_INDEX_PATH, payload)
    write_json(ANALYSIS_INDEX_PATH, payload)


def main() -> int:
    args = parse_args()

    if not HISTORY_DIR.exists():
        print(f"[PredictionIndex] WARN: history dir not found: {HISTORY_DIR}")
        payload = {
            "generated_at": utc_now_iso(),
            "lang_default": LANG_DEFAULT,
            "languages": SUPPORTED_LANGUAGES,
            "root": str(HISTORY_DIR.relative_to(ROOT)).replace("\\", "/"),
            "count": 0,
            "latest_date": None,
            "items": [],
        }
        write_all_outputs(payload)
        print(f"[PredictionIndex] OK: wrote empty index -> {DATA_INDEX_PATH}")
        return 0

    payload = build_index(limit=args.limit)
    write_all_outputs(payload)

    print(f"[PredictionIndex] OK: wrote data index -> {DATA_INDEX_PATH}")
    print(f"[PredictionIndex] OK: wrote analysis mirror -> {ANALYSIS_INDEX_PATH}")
    print(f"[PredictionIndex] count={payload['count']} latest_date={payload['latest_date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

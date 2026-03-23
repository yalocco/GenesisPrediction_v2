#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Dict, List

SUPPORTED_LANGUAGES = ["en", "ja", "th"]
LANG_DEFAULT_EN = "en"

REFERENCE_MEMORY_STATUS_I18N = {
    "ok": {"en": "ok", "ja": "正常", "th": "ปกติ"},
    "partial": {"en": "partial", "ja": "部分", "th": "บางส่วน"},
    "unavailable": {"en": "unavailable", "ja": "利用不可", "th": "ไม่พร้อมใช้งาน"},
    "missing": {"en": "missing", "ja": "欠落", "th": "ขาดหาย"},
    "error": {"en": "error", "ja": "エラー", "th": "ข้อผิดพลาด"},
    "unknown": {"en": "unknown", "ja": "不明", "th": "ไม่ทราบ"},
}

GENERIC_TEXT_MAP = {
    "": {"en": "", "ja": "", "th": ""},
    "No reference memory summary available.": {
        "en": "No reference memory summary available.",
        "ja": "参照メモリ要約は利用できません。",
        "th": "ไม่มีสรุป reference memory ที่พร้อมใช้งาน",
    },
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


def normalize_str(value: Any) -> str:
    return str(value or "").strip()


def ensure_lang_map(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, str] = {}
    for lang in SUPPORTED_LANGUAGES:
        text = normalize_str(value.get(lang))
        if text:
            out[lang] = text
    return out


def ensure_lang_list_map(value: Any) -> Dict[str, List[str]]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, List[str]] = {}
    for lang in SUPPORTED_LANGUAGES:
        items = value.get(lang)
        if isinstance(items, list):
            vals = [normalize_str(x) for x in items if normalize_str(x)]
            if vals:
                out[lang] = vals
    return out


def finalize_text_i18n(base_en: str, partial: Dict[str, str] | None = None) -> Dict[str, str]:
    partial = partial or {}
    en_text = normalize_str((partial or {}).get("en") or base_en)
    ja_text = normalize_str((partial or {}).get("ja") or en_text)
    th_text = normalize_str((partial or {}).get("th") or en_text)
    return {"en": en_text, "ja": ja_text, "th": th_text}


def finalize_list_i18n(base_en_list: List[str], partial: Dict[str, List[str]] | None = None) -> Dict[str, List[str]]:
    partial = partial or {}
    en_list = partial.get("en") or [normalize_str(x) for x in base_en_list if normalize_str(x)]
    ja_list = partial.get("ja") or list(en_list)
    th_list = partial.get("th") or list(en_list)
    return {"en": en_list, "ja": ja_list, "th": th_list}


def translate_generic_text(text: str) -> Dict[str, str]:
    base = normalize_str(text)
    mapped = GENERIC_TEXT_MAP.get(base)
    if mapped:
        return finalize_text_i18n(base, mapped)
    return {"en": base, "ja": base, "th": base}


def translate_status(value: Any) -> Dict[str, str]:
    key = normalize_str(value).lower() or "unknown"
    mapped = REFERENCE_MEMORY_STATUS_I18N.get(key)
    if mapped:
        return finalize_text_i18n(mapped.get("en", key), mapped)
    return finalize_text_i18n(key, {"en": key})


def translate_reference_memory_summary(summary: Any, existing_i18n: Any = None) -> Dict[str, str]:
    existing = ensure_lang_map(existing_i18n)
    base = normalize_str(summary)
    if existing:
        return finalize_text_i18n(base, existing)
    if not base:
        return translate_generic_text("No reference memory summary available.")
    return translate_generic_text(base)

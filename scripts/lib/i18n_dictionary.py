"""
i18n_dictionary.py

Dictionary-based multilingual support for GenesisPrediction
SSOT: configs/i18n_dictionary.json

Principles:
- English is the source of truth
- UI does NOT translate
- Analysis layer injects *_i18n fields
- Fallback is handled here
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


# --------------------------------------------------
# Load dictionary
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
DICT_PATH = ROOT / "configs" / "i18n_dictionary.json"

_dictionary: Dict[str, Dict[str, Any]] = {}
_flat_index: Dict[str, Dict[str, str]] = {}
_category_index: Dict[str, Dict[str, Dict[str, str]]] = {}


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_lang_entry(value: Any) -> bool:
    return isinstance(value, dict) and any(lang in value for lang in ("en", "ja", "th"))


def _rebuild_indexes() -> None:
    global _flat_index, _category_index

    flat_index: Dict[str, Dict[str, str]] = {}
    category_index: Dict[str, Dict[str, Dict[str, str]]] = {}

    for category, entries in _dictionary.items():
        if not isinstance(entries, dict):
            continue
        if str(category).startswith("_"):
            continue

        bucket: Dict[str, Dict[str, str]] = {}

        for raw_key, raw_value in entries.items():
            if not _is_lang_entry(raw_value):
                continue

            normalized_entry = {
                "en": str(raw_value.get("en", raw_key)).strip(),
                "ja": str(raw_value.get("ja", raw_value.get("en", raw_key))).strip(),
                "th": str(raw_value.get("th", raw_value.get("en", raw_key))).strip(),
            }

            raw_key_norm = _normalize_key(raw_key)
            en_key_norm = _normalize_key(normalized_entry["en"])

            if raw_key_norm:
                bucket[raw_key_norm] = normalized_entry
                flat_index[raw_key_norm] = normalized_entry

            if en_key_norm:
                bucket[en_key_norm] = normalized_entry
                flat_index[en_key_norm] = normalized_entry

        if bucket:
            category_index[_normalize_key(category)] = bucket

    _flat_index = flat_index
    _category_index = category_index


def _load_dictionary() -> None:
    global _dictionary
    if not DICT_PATH.exists():
        _dictionary = {}
        _rebuild_indexes()
        return

    try:
        with open(DICT_PATH, "r", encoding="utf-8") as f:
            _dictionary = json.load(f)
    except Exception:
        _dictionary = {}

    _rebuild_indexes()


_load_dictionary()


# --------------------------------------------------
# Core translate function
# --------------------------------------------------

def get_dictionary_entry(text: Any, category: str | None = None) -> Dict[str, str] | None:
    key = _normalize_key(text)
    if not key:
        return None

    if category:
        bucket = _category_index.get(_normalize_key(category), {})
        entry = bucket.get(key)
        if entry:
            return dict(entry)

    entry = _flat_index.get(key)
    if entry:
        return dict(entry)

    return None


def translate(text: Any, category: str | None = None) -> Dict[str, str]:
    """
    Convert text into i18n structure

    Returns:
        {
            "en": "...",
            "ja": "...",
            "th": "..."
        }
    """

    base_text = str(text or "").strip()
    if not base_text:
        return {"en": "", "ja": "", "th": ""}

    entry = get_dictionary_entry(base_text, category=category)

    if entry:
        return {
            "en": str(entry.get("en") or base_text),
            "ja": str(entry.get("ja") or entry.get("en") or base_text),
            "th": str(entry.get("th") or entry.get("en") or base_text),
        }

    # fallback (no dictionary match)
    return {
        "en": base_text,
        "ja": base_text,
        "th": base_text,
    }


# --------------------------------------------------
# Batch helper
# --------------------------------------------------

def translate_list(items: Iterable[Any], category: str | None = None) -> list[Dict[str, str]]:
    return [translate(x, category=category) for x in items if str(x or "").strip()]


def translate_lang_list(items: Iterable[Any], category: str | None = None) -> Dict[str, list[str]]:
    out = {"en": [], "ja": [], "th": []}
    for item in items:
        entry = translate(item, category=category)
        if entry["en"] or entry["ja"] or entry["th"]:
            out["en"].append(entry["en"])
            out["ja"].append(entry["ja"])
            out["th"].append(entry["th"])
    return out


# --------------------------------------------------
# Inject helper (important)
# --------------------------------------------------

def inject_i18n(obj: Dict[str, Any], fields: list[str], category_map: Dict[str, str] | None = None):
    """
    Add *_i18n fields to dict

    Example:
        inject_i18n(news, ["title", "source"])

    Result:
        title_i18n, source_i18n added
    """

    category_map = category_map or {}

    for field in fields:
        value = obj.get(field)
        category = category_map.get(field)

        if isinstance(value, str):
            obj[f"{field}_i18n"] = translate(value, category=category)

        elif isinstance(value, list):
            obj[f"{field}_i18n"] = translate_lang_list(value, category=category)

    return obj


# --------------------------------------------------
# Reload (for dev)
# --------------------------------------------------

def reload_dictionary():
    _load_dictionary()

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

DEFAULT_OLLAMA_URL = os.environ.get("GENESIS_OLLAMA_URL", "http://localhost:11435")
DEFAULT_MODEL = os.environ.get("GENESIS_TRANSLATION_MODEL", "gemma3:4b")
DEFAULT_TIMEOUT = int(os.environ.get("GENESIS_TRANSLATION_TIMEOUT", "60"))

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class TranslationConfig:
    ollama_url: str = DEFAULT_OLLAMA_URL
    model: str = DEFAULT_MODEL
    timeout: int = DEFAULT_TIMEOUT


class TranslationError(RuntimeError):
    pass


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _clean_json_response(text: str) -> Dict[str, str]:
    raw = _normalize_text(text)
    if not raw:
        raise TranslationError("empty translation response")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = _JSON_BLOCK_RE.search(raw)
        if not match:
            raise TranslationError("no JSON object found in response")
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise TranslationError("translation response is not a JSON object")

    return {
        "ja": _normalize_text(parsed.get("ja")),
        "th": _normalize_text(parsed.get("th")),
    }


def _build_prompt(text: str) -> str:
    return (
        "You are a precise translation engine for GenesisPrediction.\n"
        "Translate the English text into Japanese and Thai.\n"
        "Rules:\n"
        "- Preserve meaning exactly.\n"
        "- Do not summarize.\n"
        "- Do not add explanations.\n"
        "- Keep names, organizations, and URLs unchanged when appropriate.\n"
        "- Return JSON only. No markdown. No code fences.\n"
        'Output format: {"ja":"...","th":"..."}\n\n'
        f"Text:\n{text}"
    )


def translate_text_block(
    text: str,
    *,
    config: Optional[TranslationConfig] = None,
    session: Optional[requests.Session] = None,
) -> Dict[str, str]:
    value = _normalize_text(text)
    if not value:
        return {"en": "", "ja": "", "th": ""}

    cfg = config or TranslationConfig()
    payload = {
        "model": cfg.model,
        "prompt": _build_prompt(value),
        "stream": False,
        "options": {
            "temperature": 0,
        },
    }

    client = session or requests.Session()
    response = client.post(
        f"{cfg.ollama_url.rstrip('/')}/api/generate",
        json=payload,
        timeout=cfg.timeout,
    )
    response.raise_for_status()
    body = response.json()

    result = _clean_json_response(_normalize_text(body.get("response")))
    return {
        "en": value,
        "ja": result.get("ja") or value,
        "th": result.get("th") or value,
    }


from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict

import requests

CACHE_FILE = Path("data/translation_cache_sentiment_refine.json")

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
READ_MORE_RE = re.compile(r"\bRead More:?\b.*$", re.IGNORECASE)
WS_RE = re.compile(r"\s+")
# Keep ASCII, Japanese, Thai, and common punctuation. Remove odd mixed-script artifacts.
SANITIZE_RE = re.compile(r"[^0-9A-Za-z\u3040-\u30FF\u3400-\u9FFF\u0E00-\u0E7F\s.,!?;:()'\"“”‘’/\-–—%&+#]+")

PROPER_NOUN_MAP: Dict[str, str] = {
    "Peter Thiel": "Peter Thiel",
    "Fox News": "Fox News",
    "New York Magazine": "New York Magazine",
    "Shan State": "Shan State",
    "Salween River": "Salween River",
    "Daredevil: Born Again": "Daredevil: Born Again",
    "The Kingpin": "The Kingpin",
    "Prime Video": "Prime Video",
    "Disney+": "Disney+",
    "Marvel": "Marvel",
    "Thai": "Thai",
    "Iran": "Iran",
    "Israel": "Israel",
    "Trump": "Trump",
}

def load_cache() -> Dict[str, Dict[str, str]]:
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}

def save_cache(cache: Dict[str, Dict[str, str]]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def clean_text(text: str, limit: int = 260) -> str:
    text = text or ""
    text = text.replace("\u00a0", " ")
    text = URL_RE.sub("", text)
    text = READ_MORE_RE.sub("", text)
    text = WS_RE.sub(" ", text).strip(" -–—")
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in [". ", "! ", "? ", "; ", ", "]:
        idx = cut.rfind(sep)
        if idx >= 140:
            return cut[:idx + 1].strip()
    idx = cut.rfind(" ")
    if idx >= 140:
        return cut[:idx].strip()
    return cut.strip()

def sanitize_output(text: str) -> str:
    text = text or ""
    text = SANITIZE_RE.sub("", text)
    text = WS_RE.sub(" ", text).strip()
    return text

def restore_proper_nouns(text: str) -> str:
    out = text
    for noun in PROPER_NOUN_MAP:
        # leave exact protected terms as-is when already present
        out = out.replace(noun.lower(), noun)
    return out

def build_prompt(text: str) -> str:
    protected_terms = ", ".join(PROPER_NOUN_MAP.keys())
    return f"""Translate the following English news snippet into Japanese and Thai.

Rules:
- Keep proper nouns, person names, organization names, place names, product names, and media titles unchanged when appropriate.
- Do not translate source names or brand names into different words.
- Return STRICT JSON only.
- Keep the translation concise and natural.
- If the text is truncated, translate only the visible text without inventing missing parts.
- Protected terms that should remain unchanged when they appear: {protected_terms}

Text:
{text}

Output JSON:
{{"ja":"...", "th":"..."}}
"""

def call_ollama(text: str, model: str, ollama_url: str, timeout: int) -> Dict[str, str] | None:
    try:
        response = requests.post(
            f"{ollama_url.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": build_prompt(text),
                "stream": False,
                "format": "json",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        raw = payload.get("response", "")
        if not raw:
            return None
        data = json.loads(raw)
        ja = sanitize_output(str(data.get("ja", "")).strip())
        th = sanitize_output(str(data.get("th", "")).strip())
        if not ja or not th:
            return None
        return {"ja": restore_proper_nouns(ja), "th": restore_proper_nouns(th)}
    except Exception:
        return None

def refine_block(
    original_en: str,
    current_block: Dict[str, Any],
    cache: Dict[str, Dict[str, str]],
    model: str,
    ollama_url: str,
    timeout: int,
) -> Dict[str, str]:
    cleaned = clean_text(original_en)
    if not cleaned:
        return {"en": "", "ja": "", "th": ""}

    cache_key = f"description::{cleaned}"
    cached = cache.get(cache_key)
    if isinstance(cached, dict):
        return {
            "en": cleaned,
            "ja": str(cached.get("ja", cleaned)),
            "th": str(cached.get("th", cleaned)),
        }

    current_ja = str((current_block or {}).get("ja", "")).strip()
    current_th = str((current_block or {}).get("th", "")).strip()

    # If current values are already translated and look usable, normalize them and cache.
    if current_ja and current_th and current_ja != original_en and current_th != original_en:
        out = {
            "en": cleaned,
            "ja": sanitize_output(current_ja),
            "th": sanitize_output(current_th),
        }
        cache[cache_key] = {"ja": out["ja"], "th": out["th"]}
        return out

    translated = call_ollama(cleaned, model=model, ollama_url=ollama_url, timeout=timeout)
    if translated is None:
        out = {"en": cleaned, "ja": cleaned, "th": cleaned}
    else:
        out = {"en": cleaned, "ja": translated["ja"], "th": translated["th"]}

    cache[cache_key] = {"ja": out["ja"], "th": out["th"]}
    return out

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True)
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--ollama-url", default="http://localhost:11435")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    infile = Path(args.infile)
    outfile = Path(args.outfile)

    data = json.loads(infile.read_text(encoding="utf-8"))
    cache = load_cache()

    count = 0
    for item in data.get("items", []):
        description = str(item.get("description", "")).strip()
        block = item.get("description_i18n")
        item["description_i18n"] = refine_block(
            description,
            block if isinstance(block, dict) else {},
            cache,
            model=args.model,
            ollama_url=args.ollama_url,
            timeout=args.timeout,
        )
        count += 1

    save_cache(cache)
    outfile.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] refined description_i18n for {count} items")
    print(f"[OK] wrote: {outfile}")
    print(f"[OK] cache: {CACHE_FILE}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

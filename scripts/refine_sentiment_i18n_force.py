
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Any

import requests

CACHE_FILE = Path("data/translation_cache_sentiment_refine_force.json")

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
READ_MORE_RE = re.compile(r"\bRead More:?\b.*$", re.IGNORECASE)
WS_RE = re.compile(r"\s+")
# Remove odd artifacts but keep ASCII/Japanese/Thai/common punctuation.
SANITIZE_RE = re.compile(r"[^0-9A-Za-z\u3040-\u30FF\u3400-\u9FFF\u0E00-\u0E7F\s.,!?;:()'\"“”‘’/\-–—%&+#]+")

PROPER_NOUNS = [
    "Peter Thiel", "Paolo Benanti", "Fox News", "Hakeem Jeffries",
    "New York Magazine", "Salween River", "Shan State", "Sai De Moine",
    "Prime Video", "Invincible", "HBO Max", "Filip", "Poland",
    "Daredevil: Born Again", "Thunderbolts", "MCU", "Disney+",
    "Marvel", "Kingpin", "CounterPunch", "Rebecca Karl",
    "Nikita Bier", "CNBC", "TSA", "ICE", "UNHRC", "AIPAC",
    "Jennifer Aniston", "Rachel Green", "Friends", "Jim Curtis",
    "Imran Khan", "Sulaiman", "Kasim", "Pakistan",
]

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

def clean_text(text: str, limit: int = 320) -> str:
    text = text or ""
    text = text.replace("\u00a0", " ")
    text = URL_RE.sub("", text)
    text = READ_MORE_RE.sub("", text)
    text = WS_RE.sub(" ", text).strip(" -–—")
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in [". ", "! ", "? ", "; "]:
        idx = cut.rfind(sep)
        if idx >= 150:
            return cut[:idx + 1].strip()
    idx = cut.rfind(" ")
    if idx >= 150:
        return cut[:idx].strip()
    return cut.strip()

def sanitize_output(text: str) -> str:
    text = text or ""
    text = SANITIZE_RE.sub("", text)
    text = WS_RE.sub(" ", text).strip()
    return text

def restore_proper_nouns(text: str) -> str:
    out = text
    for noun in PROPER_NOUNS:
        lower = noun.lower()
        out = re.sub(re.escape(lower), noun, out, flags=re.IGNORECASE)
    return out

def has_english_words(text: str) -> bool:
    # Allow protected proper nouns; detect broad English leakage.
    ascii_words = re.findall(r"\b[A-Za-z]{3,}\b", text or "")
    for word in ascii_words:
        if any(word.lower() in noun.lower() for noun in PROPER_NOUNS):
            continue
        return True
    return False

def build_prompt(text: str) -> str:
    protected = ", ".join(PROPER_NOUNS)
    return f"""Translate the following English news snippet into Japanese and Thai.

Rules:
- Preserve these proper nouns exactly when they appear: {protected}
- Preserve person names, organization names, place names, show/movie titles, brand names, and acronyms exactly.
- Do not leave stray English words except protected proper nouns.
- Use natural complete sentences.
- If the text is truncated, translate only the visible text and do not invent missing parts.
- Return STRICT JSON only.

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
        ja = restore_proper_nouns(sanitize_output(str(data.get("ja", "")).strip()))
        th = restore_proper_nouns(sanitize_output(str(data.get("th", "")).strip()))
        if not ja or not th:
            return None
        return {"ja": ja, "th": th}
    except Exception:
        return None

def refine_block(
    original_en: str,
    cache: Dict[str, Dict[str, str]],
    model: str,
    ollama_url: str,
    timeout: int,
    force: bool,
) -> Dict[str, str]:
    cleaned = clean_text(original_en)
    if not cleaned:
        return {"en": "", "ja": "", "th": ""}

    key = f"description::{cleaned}"
    if not force:
        cached = cache.get(key)
        if isinstance(cached, dict):
            return {"en": cleaned, "ja": str(cached.get("ja", cleaned)), "th": str(cached.get("th", cleaned))}

    translated = call_ollama(cleaned, model=model, ollama_url=ollama_url, timeout=timeout)
    if translated is None:
        out = {"en": cleaned, "ja": cleaned, "th": cleaned}
    else:
        # second pass fallback if broad English leakage remains
        ja = translated["ja"]
        th = translated["th"]
        if has_english_words(ja) or has_english_words(th):
            translated2 = call_ollama(cleaned, model=model, ollama_url=ollama_url, timeout=timeout)
            if translated2 is not None:
                ja, th = translated2["ja"], translated2["th"]
        out = {"en": cleaned, "ja": ja, "th": th}

    cache[key] = {"ja": out["ja"], "th": out["th"]}
    return out

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True)
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--ollama-url", default="http://localhost:11435")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--force", action="store_true", help="Re-translate all descriptions even if already present or cached")
    args = parser.parse_args()

    infile = Path(args.infile)
    outfile = Path(args.outfile)
    data = json.loads(infile.read_text(encoding="utf-8"))
    cache = load_cache()

    count = 0
    for item in data.get("items", []):
        description = str(item.get("description", "")).strip()
        if not description:
            continue
        item["description_i18n"] = refine_block(
            description,
            cache=cache,
            model=args.model,
            ollama_url=args.ollama_url,
            timeout=args.timeout,
            force=args.force,
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

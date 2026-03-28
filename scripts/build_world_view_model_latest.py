# scripts/build_world_view_model_latest.py
# Build /data/world_politics/analysis/view_model_latest.json for GUI pages.
#
# Purpose:
# - Provide a stable read-only ViewModel for GUI pages.
# - Join daily article cards with summary / sentiment / health.
# - Expose top-level fields expected by UI.
# - Emit *_i18n shadow fields for migration-safe multilingual rendering.
#
# Important:
# - This builder MUST NOT invent analysis.
# - UI must read *_i18n only; translation belongs here in scripts / analysis.
# - Article translation is optional and only runs when explicitly enabled.
# - Existing upstream *_i18n is reused only when it contains real non-English content.
# - Translation failures are surfaced in logs and meta instead of being silently hidden.

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except Exception:
    requests = None

try:
    from i18n_dictionary import translate as dict_translate
    from i18n_dictionary import translate_lang_list as dict_translate_lang_list
except Exception:
    dict_translate = None
    dict_translate_lang_list = None


ROOT = Path(__file__).resolve().parents[1]
DATA_WORLD = ROOT / "data" / "world_politics"
ANALYSIS = DATA_WORLD / "analysis"

LATEST_JSON = ANALYSIS / "latest.json"
SENT_LATEST_JSON = ANALYSIS / "sentiment_latest.json"
SUMMARY_LATEST_JSON = ANALYSIS / "daily_summary_latest.json"
HEALTH_LATEST_JSON = ANALYSIS / "health_latest.json"
OUT_JSON = ANALYSIS / "view_model_latest.json"

LANG_DEFAULT = "en"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]

TEXT_I18N = {
    "global_risk": {
        "LOW": {"en": "LOW", "ja": "低", "th": "ต่ำ"},
        "MEDIUM": {"en": "MEDIUM", "ja": "中", "th": "กลาง"},
        "HIGH": {"en": "HIGH", "ja": "高", "th": "สูง"},
    },
    "section_title": {
        "world_politics": {"en": "World Politics", "ja": "世界政治", "th": "การเมืองโลก"},
    },
}

_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
_RAW_URL_RE = re.compile(r"https?://\S+")
_WS_RE = re.compile(r"[ \t]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jst_now_iso() -> str:
    jst = timezone(timedelta(hours=9))
    return datetime.now(tz=jst).isoformat(timespec="seconds")


def _pick_date(*docs: dict) -> str:
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        for key in ("base_date", "date", "as_of"):
            value = doc.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:10]
        meta = doc.get("meta")
        if isinstance(meta, dict):
            for key in ("as_of", "date", "generated_at"):
                value = meta.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()[:10]
    return "latest"


def _resolve_source_file(latest_doc: dict, fallback_date: str) -> Path:
    sf = latest_doc.get("source_file")
    if isinstance(sf, str) and sf.strip():
        sf = sf.strip()
        prefix = "/data/world_politics/"
        if sf.startswith(prefix):
            return DATA_WORLD / sf[len(prefix):]
        return DATA_WORLD / Path(sf).name

    d = latest_doc.get("date")
    if isinstance(d, str) and d.strip():
        return DATA_WORLD / f"{d.strip()[:10]}.json"

    return DATA_WORLD / f"{fallback_date}.json"


def _as_str(x: Any) -> str:
    return "" if x is None else str(x)


def _normalize_url(value: Any) -> str:
    return _as_str(value).strip()


def _normalized_key(value: Any) -> str:
    return " ".join(_as_str(value).lower().split())


def _clean_text(value: Any) -> str:
    text = _as_str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return ""
    text = _MARKDOWN_LINK_RE.sub(r"\1", text)
    text = _RAW_URL_RE.sub("", text)
    text = _WS_RE.sub(" ", text)
    text = "\n".join(part.strip() for part in text.split("\n"))
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip(" \n\t\"'")


def _finalize_text_i18n(base_text: str, partial: dict[str, str] | None = None) -> dict[str, str]:
    partial = partial or {}
    en_text = _clean_text(partial.get("en") or base_text or "")
    ja_text = _clean_text(partial.get("ja") or en_text)
    th_text = _clean_text(partial.get("th") or en_text)
    return {"en": en_text, "ja": ja_text, "th": th_text}


def _finalize_list_i18n(base_list: list[str], resolver: dict[str, dict[str, str]] | None = None) -> dict[str, list[str]]:
    cleaned_base = [_clean_text(x) for x in base_list if _clean_text(x)]
    if not resolver:
        return {"en": list(cleaned_base), "ja": list(cleaned_base), "th": list(cleaned_base)}
    out = {"en": [], "ja": [], "th": []}
    for item in cleaned_base:
        mapping = resolver.get(item) or {}
        out["en"].append(_clean_text(mapping.get("en") or item))
        out["ja"].append(_clean_text(mapping.get("ja") or mapping.get("en") or item))
        out["th"].append(_clean_text(mapping.get("th") or mapping.get("en") or item))
    return out


def _dict_text_i18n(base_text: str, category: str | None = None) -> dict[str, str]:
    text = _clean_text(base_text)
    if not text:
        return {"en": "", "ja": "", "th": ""}

    if dict_translate is not None:
        try:
            return _finalize_text_i18n(text, dict_translate(text, category=category))
        except Exception:
            pass

    return _finalize_text_i18n(text)


def _dict_list_i18n(base_list: list[str], category: str | None = None) -> dict[str, list[str]]:
    items = [_clean_text(x) for x in base_list if _clean_text(x)]
    if not items:
        return {"en": [], "ja": [], "th": []}

    if dict_translate_lang_list is not None:
        try:
            out = dict_translate_lang_list(items, category=category)
            return {
                "en": [_clean_text(x) for x in out.get("en", items)],
                "ja": [_clean_text(x) for x in out.get("ja", items)],
                "th": [_clean_text(x) for x in out.get("th", items)],
            }
        except Exception:
            pass

    return _finalize_list_i18n(items)


def _parse_source_name(value: Any) -> str:
    if isinstance(value, dict):
        return _as_str(value.get("name") or value.get("id") or "")
    return _as_str(value)


def _has_real_translation(block: dict[str, str] | None) -> bool:
    if not isinstance(block, dict):
        return False
    en = _normalized_key(_clean_text(block.get("en")))
    ja = _normalized_key(_clean_text(block.get("ja")))
    th = _normalized_key(_clean_text(block.get("th")))
    return bool((ja and ja != en) or (th and th != en))


class ArticleTranslator:
    def __init__(
        self,
        enabled: bool = False,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
        verbose: bool = False,
    ) -> None:
        self.enabled = enabled and requests is not None
        self.model = (model or "").strip()
        self.base_url = (base_url or "http://127.0.0.1:11434").rstrip("/")
        self.timeout = timeout
        self.verbose = verbose
        self.cache: dict[tuple[str, str], str] = {}
        self.stats = {
            "requested": 0,
            "succeeded": 0,
            "failed": 0,
            "reused_upstream": 0,
            "fallback_english": 0,
        }

    def available(self) -> bool:
        return bool(self.enabled and self.model and requests is not None)

    def translate_map(
        self,
        text: str,
        *,
        category: str | None = None,
        existing: dict[str, str] | None = None,
        force_translate: bool = False,
    ) -> dict[str, str]:
        base = _clean_text(text)
        result = _finalize_text_i18n(base, existing)
        if not base:
            return result

        if _has_real_translation(existing):
            self.stats["reused_upstream"] += 1
            return _finalize_text_i18n(base, existing)

        if not self.available():
            self.stats["fallback_english"] += 1
            if category:
                return _dict_text_i18n(base, category=category)
            return result

        if not force_translate and _has_real_translation(result):
            self.stats["reused_upstream"] += 1
            return result

        ja = self._translate_one(base, "ja")
        th = self._translate_one(base, "th")

        if ja:
            result["ja"] = ja
        if th:
            result["th"] = th

        if _has_real_translation(result):
            self.stats["succeeded"] += 1
        else:
            self.stats["failed"] += 1
            self.stats["fallback_english"] += 1
            if self.verbose:
                print(f"[WARN] translation fallback to EN: {base[:90]}", file=sys.stderr)

        return _finalize_text_i18n(base, result)

    def translate_list(
        self,
        items: list[str],
        *,
        category: str | None = None,
        force_translate: bool = False,
    ) -> dict[str, list[str]]:
        cleaned = [_clean_text(x) for x in items if _clean_text(x)]
        if not cleaned:
            return {"en": [], "ja": [], "th": []}

        if not self.available():
            if category:
                return _dict_list_i18n(cleaned, category=category)
            return {"en": list(cleaned), "ja": list(cleaned), "th": list(cleaned)}

        return {
            "en": list(cleaned),
            "ja": [self.translate_map(item, category=category, force_translate=force_translate)["ja"] for item in cleaned],
            "th": [self.translate_map(item, category=category, force_translate=force_translate)["th"] for item in cleaned],
        }

    def _translate_one(self, text: str, target_lang: str) -> str:
        self.stats["requested"] += 1
        key = (target_lang, hashlib.sha1(text.encode("utf-8")).hexdigest())
        if key in self.cache:
            return self.cache[key]

        language_name = {"ja": "Japanese", "th": "Thai"}.get(target_lang, target_lang)
        prompt = (
            f"Translate the following news text into {language_name}.\n"
            "Rules:\n"
            "- Return only the translation.\n"
            "- Keep names, organizations, tickers, URLs, and numbers accurate.\n"
            "- Do not add explanations, notes, URLs, markdown, or any extra content.\n"
            "- Output ONLY the translated text.\n"
            "- Preserve concise news style.\n"
            "- Do not leave the answer in English unless the text is only a proper noun or brand.\n\n"
            f"Text:\n{text}"
        )

        translated = ""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            translated = _clean_text(data.get("response"))
        except Exception as exc:
            if self.verbose:
                print(f"[WARN] translation request failed ({target_lang}): {exc}", file=sys.stderr)
            translated = ""

        if _normalized_key(translated) == _normalized_key(text):
            translated = ""

        self.cache[key] = translated
        return translated


def _build_sentiment_lookup(sent: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    by_url: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    items = sent.get("items") if isinstance(sent, dict) else []
    if not isinstance(items, list):
        return by_url, by_title

    for item in items:
        if not isinstance(item, dict):
            continue
        url = _normalize_url(item.get("url") or item.get("link"))
        if url:
            by_url[url] = item

        title = _normalized_key(item.get("title") or item.get("headline"))
        if title and title not in by_title:
            by_title[title] = item

    return by_url, by_title


def _pick_upstream_i18n(sent_item: dict | None, *field_names: str) -> dict[str, str] | None:
    if not isinstance(sent_item, dict):
        return None
    for name in field_names:
        value = sent_item.get(name)
        if isinstance(value, dict) and _has_real_translation(value):
            return value
    return None


def _wrap_article_text_i18n(
    text: Any,
    *,
    category: str | None = None,
    upstream_i18n: dict[str, str] | None = None,
    translator: ArticleTranslator | None = None,
    force_translate: bool = False,
) -> dict[str, str]:
    base = _clean_text(text)
    if translator is not None:
        return translator.translate_map(base, category=category, existing=upstream_i18n, force_translate=force_translate)
    if upstream_i18n:
        return _finalize_text_i18n(base, upstream_i18n)
    return _dict_text_i18n(base, category=category)


def _extract_articles_from_daily(
    daily_doc: Any,
    *,
    sentiment_lookup_by_url: dict[str, dict] | None = None,
    sentiment_lookup_by_title: dict[str, dict] | None = None,
    translator: ArticleTranslator | None = None,
    force_translate_articles: bool = False,
) -> list[dict]:
    if isinstance(daily_doc, list):
        items = daily_doc
    elif isinstance(daily_doc, dict):
        items = daily_doc.get("items") or daily_doc.get("articles") or daily_doc.get("data") or daily_doc.get("news") or []
    else:
        items = []

    if not isinstance(items, list):
        return []

    sentiment_lookup_by_url = sentiment_lookup_by_url or {}
    sentiment_lookup_by_title = sentiment_lookup_by_title or {}
    out: list[dict] = []

    for a in items:
        if not isinstance(a, dict):
            continue

        title_text = _clean_text(a.get("title") or a.get("headline") or "")
        url_text = _clean_text(a.get("url") or a.get("link") or "")
        summary_text = _clean_text(a.get("summary") or a.get("description") or a.get("excerpt") or "")
        source_text = _clean_text(_parse_source_name(a.get("source")) or _as_str(a.get("domain")))
        published_at = _clean_text(a.get("published_at") or a.get("publishedAt") or a.get("published") or a.get("date") or "")

        image = a.get("urlToImage") or a.get("image") or a.get("thumbnail") or a.get("thumb") or a.get("og_image")
        if not (isinstance(image, str) and image.strip()):
            image = None

        tags = [_clean_text(x) for x in (a.get("tags") if isinstance(a.get("tags"), list) else []) if _clean_text(x)]

        sent_item = sentiment_lookup_by_url.get(url_text) or sentiment_lookup_by_title.get(_normalized_key(title_text))
        title_i18n = _wrap_article_text_i18n(
            title_text,
            upstream_i18n=_pick_upstream_i18n(sent_item, "title_i18n"),
            translator=translator,
            force_translate=force_translate_articles,
        )
        summary_i18n = _wrap_article_text_i18n(
            summary_text,
            upstream_i18n=_pick_upstream_i18n(sent_item, "summary_i18n", "description_i18n"),
            translator=translator,
            force_translate=force_translate_articles,
        )
        source_i18n = _wrap_article_text_i18n(
            source_text,
            category="sources",
            upstream_i18n=_pick_upstream_i18n(sent_item, "source_i18n"),
            translator=None,
            force_translate=False,
        )

        out.append(
            {
                "title": title_text,
                "title_i18n": title_i18n,
                "summary": summary_text,
                "summary_i18n": summary_i18n,
                "source": source_text,
                "source_i18n": source_i18n,
                "url": url_text,
                "image": image,
                "published_at": published_at,
                "tags": tags,
            }
        )

    return out


def _extract_today(sent: dict, cards_count: int) -> dict:
    today = sent.get("today")
    if isinstance(today, dict) and today:
        return today
    items = sent.get("items")
    if isinstance(items, list):
        return {"articles": len(items)}
    return {"articles": cards_count}


def _extract_sentiment_block(sent: dict) -> dict:
    block = sent.get("sentiment")
    if isinstance(block, dict):
        return {
            "risk": round(float(block.get("risk", 0.0) or 0.0), 6),
            "positive": round(float(block.get("positive", 0.0) or 0.0), 6),
            "uncertainty": round(float(block.get("uncertainty", 0.0) or 0.0), 6),
        }
    return {"risk": 0.0, "positive": 0.0, "uncertainty": 0.0}


def _extract_health_block(health: dict) -> dict:
    if not isinstance(health, dict):
        return {"ok": 0, "warn": 0, "ng": 0}
    summary = health.get("summary")
    if isinstance(summary, dict):
        return {
            "ok": int(summary.get("ok", 0) or 0),
            "warn": int(summary.get("warn", 0) or 0),
            "ng": int(summary.get("ng", 0) or 0),
        }
    return {
        "ok": int(health.get("ok", 0) or 0),
        "warn": int(health.get("warn", 0) or 0),
        "ng": int(health.get("ng", 0) or 0),
    }


def _risk_label(risk_value: float) -> str:
    if risk_value < 0.10:
        return "LOW"
    if risk_value < 0.30:
        return "MEDIUM"
    return "HIGH"


def _collect_summary_text(summary_doc: dict) -> str:
    if not isinstance(summary_doc, dict):
        return ""
    candidates = [
        summary_doc.get("summary"),
        summary_doc.get("text_summary"),
        summary_doc.get("daily_summary"),
        summary_doc.get("yesterday_summary_text"),
        summary_doc.get("daily_summary_text"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return _clean_text(value)
    lines = summary_doc.get("lines")
    if isinstance(lines, list):
        text = " ".join(_clean_text(x) for x in lines if _clean_text(x))
        if text.strip():
            return _clean_text(text)
    return ""


def _collect_topics(summary_doc: dict) -> list[str]:
    if not isinstance(summary_doc, dict):
        return []
    topics = summary_doc.get("topics")
    if isinstance(topics, list):
        return [_clean_text(x) for x in topics if _clean_text(x)]
    return []


def _match_keywords(texts: list[str], keywords: list[str]) -> list[str]:
    joined = " \n ".join(t.lower() for t in texts if isinstance(t, str) and t.strip())
    return [kw for kw in keywords if kw in joined]


def _build_signal_lists(cards: list[dict], summary_doc: dict) -> tuple[list[str], list[str]]:
    texts = []
    for c in cards:
        texts.append(_as_str(c.get("title")))
        texts.append(_as_str(c.get("summary")))
        texts.append(" ".join(_as_str(x) for x in c.get("tags", [])))

    summary_text = _collect_summary_text(summary_doc)
    if summary_text:
        texts.append(summary_text)
    texts.extend(_collect_topics(summary_doc))

    economic_rules: list[tuple[str, list[str]]] = [
        ("Energy price volatility", ["oil", "gas", "energy", "barrel", "fuel"]),
        ("Inflation / rates pressure", ["inflation", "interest", "rates", "fed", "boj", "ecb", "yield"]),
        ("Trade / supply chain stress", ["tariff", "trade", "shipping", "supply chain", "export", "import", "sanction"]),
        ("Market instability", ["market", "stocks", "equity", "bond", "liquidity", "bank"]),
    ]
    geopolitical_rules: list[tuple[str, list[str]]] = [
        ("Middle East tension", ["iran", "israel", "gaza", "hormuz", "middle east"]),
        ("Ukraine / Russia conflict pressure", ["ukraine", "russia", "moscow", "kyiv"]),
        ("US political uncertainty", ["trump", "white house", "congress", "election", "biden"]),
        ("China / Taiwan strategic pressure", ["china", "taiwan", "beijing", "south china sea"]),
    ]

    economic_signals = [label for label, kws in economic_rules if _match_keywords(texts, kws)][:6]
    geopolitical_signals = [label for label, kws in geopolitical_rules if _match_keywords(texts, kws)][:6]
    return economic_signals, geopolitical_signals


def _translate_meta_text(
    text: str,
    *,
    category: str | None,
    translator: ArticleTranslator,
    force_translate: bool,
) -> dict[str, str]:
    if translator.available():
        return translator.translate_map(text, category=category, force_translate=force_translate)
    return _dict_text_i18n(text, category=category)


def _translate_meta_list(
    items: list[str],
    *,
    category: str | None,
    translator: ArticleTranslator,
    force_translate: bool,
) -> dict[str, list[str]]:
    if translator.available():
        return translator.translate_list(items, category=category, force_translate=force_translate)
    return _dict_list_i18n(items, category=category)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--translate-articles", action="store_true", help="Enable local article translation for title/summary fields.")
    parser.add_argument("--force-translate-articles", action="store_true", help="Force translation even when upstream *_i18n exists but is only EN copy.")
    parser.add_argument("--translate-meta", action="store_true", help="Translate daily summary and signal label *_i18n via the same local translation pipeline.")
    parser.add_argument("--ollama-model", default=os.getenv("GP_I18N_OLLAMA_MODEL", "").strip())
    parser.add_argument("--ollama-base-url", default=os.getenv("GP_I18N_OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    parser.add_argument("--ollama-timeout", type=int, default=int(os.getenv("GP_I18N_OLLAMA_TIMEOUT", "60")))
    parser.add_argument("--verbose-translation", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if not LATEST_JSON.exists():
        raise FileNotFoundError(f"missing: {LATEST_JSON}")

    latest_doc = _load_json(LATEST_JSON)
    sent = _load_json(SENT_LATEST_JSON) if SENT_LATEST_JSON.exists() else {}
    summary_doc = _load_json(SUMMARY_LATEST_JSON) if SUMMARY_LATEST_JSON.exists() else {}
    health_doc = _load_json(HEALTH_LATEST_JSON) if HEALTH_LATEST_JSON.exists() else {}

    date = _pick_date(sent, summary_doc, latest_doc)
    daily_path = _resolve_source_file(latest_doc, fallback_date=date)
    if not daily_path.exists():
        fallback = DATA_WORLD / f"{date}.json"
        if fallback.exists():
            daily_path = fallback
        else:
            raise FileNotFoundError(f"daily source not found: {daily_path} (and fallback {fallback})")

    daily_doc = _load_json(daily_path)
    sentiment_lookup_by_url, sentiment_lookup_by_title = _build_sentiment_lookup(sent)
    translator = ArticleTranslator(
        enabled=args.translate_articles or args.translate_meta,
        model=args.ollama_model,
        base_url=args.ollama_base_url,
        timeout=args.ollama_timeout,
        verbose=args.verbose_translation,
    )
    cards = _extract_articles_from_daily(
        daily_doc,
        sentiment_lookup_by_url=sentiment_lookup_by_url,
        sentiment_lookup_by_title=sentiment_lookup_by_title,
        translator=translator if args.translate_articles else None,
        force_translate_articles=args.force_translate_articles,
    )

    today = _extract_today(sent, cards_count=len(cards))
    sentiment_block = _extract_sentiment_block(sent)
    health_block = _extract_health_block(health_doc)
    global_risk = _risk_label(sentiment_block["risk"])
    economic_signals, geopolitical_signals = _build_signal_lists(cards, summary_doc)
    daily_summary_text = _collect_summary_text(summary_doc)

    section_title_i18n = _finalize_text_i18n("World Politics", TEXT_I18N["section_title"]["world_politics"])
    global_risk_i18n = _dict_text_i18n(global_risk, category="risk_levels")

    if args.translate_meta:
        daily_summary_i18n = _translate_meta_text(
            daily_summary_text,
            category=None,
            translator=translator,
            force_translate=True,
        )
        economic_signals_i18n = _translate_meta_list(
            economic_signals,
            category=None,
            translator=translator,
            force_translate=True,
        )
        geopolitical_signals_i18n = _translate_meta_list(
            geopolitical_signals,
            category=None,
            translator=translator,
            force_translate=True,
        )
    else:
        daily_summary_i18n = _dict_text_i18n(daily_summary_text)
        economic_signals_i18n = _dict_list_i18n(economic_signals, category="economic_signals")
        geopolitical_signals_i18n = _dict_list_i18n(geopolitical_signals, category="geopolitical_signals")

    vm = {
        "version": "v2",
        "date": date,
        "as_of": date,
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "global_risk": global_risk,
        "global_risk_i18n": global_risk_i18n,
        "daily_summary": daily_summary_text,
        "daily_summary_i18n": daily_summary_i18n,
        "events_count": len(cards),
        "sentiment": sentiment_block,
        "health": health_block,
        "economic_signals": economic_signals,
        "economic_signals_i18n": economic_signals_i18n,
        "geopolitical_signals": geopolitical_signals,
        "geopolitical_signals_i18n": geopolitical_signals_i18n,
        "sections": [
            {
                "id": "world_politics",
                "title": section_title_i18n["en"],
                "title_i18n": section_title_i18n,
                "status": "ok",
                "cards": cards,
                "notes": f"generated_from={daily_path.as_posix()}",
            }
        ],
        "meta": {
            "as_of": date,
            "generated_at": _jst_now_iso(),
            "schema": "view_model_latest.v2",
            "generator": "world_view_model_builder",
            "source": str(daily_path),
            "notes": "rebuilt from *_latest.json (daily_summary/sentiment/health); article *_i18n may call local translation when enabled; meta *_i18n may also use the same translator when --translate-meta is enabled",
            "article_translation": {
                "enabled": bool(args.translate_articles),
                "forced": bool(args.force_translate_articles),
                "meta_enabled": bool(args.translate_meta),
                "ollama_model": args.ollama_model if (args.translate_articles or args.translate_meta) else "",
                "ollama_base_url": args.ollama_base_url if (args.translate_articles or args.translate_meta) else "",
                "provider_available": translator.available(),
                "stats": translator.stats,
            },
        },
        "today": today,
        "sources": {
            "latest": str(LATEST_JSON),
            "daily_summary_latest": str(SUMMARY_LATEST_JSON) if SUMMARY_LATEST_JSON.exists() else "",
            "sentiment_latest": str(SENT_LATEST_JSON) if SENT_LATEST_JSON.exists() else "",
            "health_latest": str(HEALTH_LATEST_JSON) if HEALTH_LATEST_JSON.exists() else "",
            "daily_source": str(daily_path),
        },
    }

    OUT_JSON.write_text(json.dumps(vm, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[OK] wrote: {OUT_JSON} "
        f"(cards={len(cards)}, date={date}, risk={global_risk}, source={daily_path}, "
        f"translate_articles={args.translate_articles}, force_translate_articles={args.force_translate_articles}, "
        f"translate_meta={args.translate_meta}, provider_available={translator.available()}, stats={translator.stats})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

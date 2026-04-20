# scripts/build_world_view_model_latest.py
# Build /data/world_politics/analysis/view_model_latest.json for GUI pages.
#
# Purpose:
# - Provide a stable read-only ViewModel for GUI pages.
# - Join daily article cards with summary / sentiment / health.
# - Expose top-level fields expected by UI.
# - Emit *_i18n shadow fields for migration-safe multilingual rendering.
#
# Quality improvements in this revision:
# - Avoid count/text contradictions such as "Observed 0 events" when articles exist.
# - Materialize a structured summary before generating human-readable summary text.
# - Reject malformed upstream summary payloads (article dumps / JSON-like blobs).
# - Enrich article cards with per-article sentiment metrics when matching data exists.
# - Use stronger URL/title normalization for matching and duplicate control.
# - Keep all inference rule-based and inspectable; do not invent unsupported facts.

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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

_THEME_RULES: list[tuple[str, list[str]]] = [
    ("middle_east_tension", ["iran", "israel", "gaza", "middle east", "hormuz", "tehran"]),
    ("ukraine_russia_conflict", ["ukraine", "russia", "moscow", "kyiv", "putin"]),
    ("china_taiwan_pressure", ["china", "taiwan", "beijing", "south china sea", "pla"]),
    ("energy_price_stress", ["oil", "gas", "energy", "fuel", "barrel", "lng"]),
    ("inflation_rates_pressure", ["inflation", "interest rate", "rates", "yield", "fed", "ecb", "boj"]),
    ("trade_supply_chain_stress", ["tariff", "sanction", "shipping", "supply chain", "export", "import", "trade"]),
    ("market_instability", ["market", "stocks", "equity", "bond", "liquidity", "bank", "credit"]),
    ("policy_uncertainty", ["policy", "white house", "congress", "election", "cabinet", "regulation"]),
    ("food_fertilizer_stress", ["fertilizer", "grain", "food", "harvest", "crop", "agriculture"]),
]

_LABEL_RULES: list[tuple[str, list[str]]] = [
    ("geopolitics", ["war", "military", "missile", "strike", "security", "nuclear", "conflict"]),
    ("policy", ["policy", "government", "court", "law", "bill", "congress", "election"]),
    ("economy", ["inflation", "rate", "market", "bank", "economy", "debt", "credit"]),
    ("energy", ["oil", "gas", "energy", "fuel", "electricity"]),
    ("food", ["fertilizer", "food", "grain", "agriculture", "crop"]),
]

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "at", "by", "from",
    "is", "are", "was", "were", "be", "as", "that", "this", "it", "its", "their", "his", "her",
    "about", "after", "before", "into", "over", "under", "amid", "amidst",
}

_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
_RAW_URL_RE = re.compile(r"https?://\S+")
_WS_RE = re.compile(r"[ \t]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
_JSONISH_SUMMARY_RE = re.compile(r'"\s*summary\s*"\s*:', re.IGNORECASE)
_BULLETISH_RE = re.compile(r"^\s*[-*•]\s+", re.MULTILINE)


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


def _normalized_key(value: Any) -> str:
    return " ".join(_clean_text(value).lower().split())


def _canonical_title(value: Any) -> str:
    text = _normalized_key(value)
    if not text:
        return ""
    text = text.replace("’", "'")
    text = _NON_WORD_RE.sub(" ", text)
    tokens = [t for t in text.split() if t and t not in _STOPWORDS]
    return " ".join(tokens)


def _normalize_url(value: Any) -> str:
    raw = _clean_text(value)
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except Exception:
        return raw.strip()
    if not parts.scheme or not parts.netloc:
        return raw.strip()
    query_pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    netloc = parts.netloc.lower()
    path = re.sub(r"/+", "/", parts.path or "/").rstrip("/")
    cleaned = urlunsplit((parts.scheme.lower(), netloc, path, urlencode(query_pairs), ""))
    return cleaned


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


def _looks_like_article_dump(text: str, event_count_hint: int = 0) -> bool:
    cleaned = _clean_text(text)
    if not cleaned:
        return False

    lowered = cleaned.lower()
    line_count = cleaned.count("\n") + 1
    summary_key_hits = len(_JSONISH_SUMMARY_RE.findall(cleaned))
    bullet_hits = len(_BULLETISH_RE.findall(cleaned))
    pipe_hits = cleaned.count("|")

    heuristics = [
        summary_key_hits >= 3,
        line_count >= 12 and summary_key_hits >= 1,
        len(cleaned) >= 1600,
        bullet_hits >= 6,
        pipe_hits >= max(6, event_count_hint // 4 if event_count_hint else 6),
        cleaned.startswith("{") and '"summary"' in lowered,
        cleaned.startswith("[") and '"summary"' in lowered,
        "representative headlines" not in lowered and summary_key_hits >= 2,
    ]
    return any(heuristics)


def _sanitize_upstream_summary(text: str, event_count_hint: int = 0) -> str:
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    if _looks_like_article_dump(cleaned, event_count_hint=event_count_hint):
        return ""
    if len(cleaned) > 800:
        return cleaned[:797].rstrip() + "..."
    return cleaned


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


def _build_sentiment_lookup(sent: dict) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    by_url: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    by_title_soft: dict[str, dict] = {}
    items = sent.get("items") if isinstance(sent, dict) else []
    if not isinstance(items, list):
        return by_url, by_title, by_title_soft

    for item in items:
        if not isinstance(item, dict):
            continue
        url = _normalize_url(item.get("url") or item.get("link"))
        if url and url not in by_url:
            by_url[url] = item

        title = _normalized_key(item.get("title") or item.get("headline"))
        if title and title not in by_title:
            by_title[title] = item

        title_soft = _canonical_title(item.get("title") or item.get("headline"))
        if title_soft and title_soft not in by_title_soft:
            by_title_soft[title_soft] = item

    return by_url, by_title, by_title_soft


def _find_sentiment_match(
    *,
    title_text: str,
    url_text: str,
    sentiment_lookup_by_url: dict[str, dict],
    sentiment_lookup_by_title: dict[str, dict],
    sentiment_lookup_by_title_soft: dict[str, dict],
) -> dict | None:
    url_key = _normalize_url(url_text)
    if url_key and url_key in sentiment_lookup_by_url:
        return sentiment_lookup_by_url[url_key]

    title_key = _normalized_key(title_text)
    if title_key and title_key in sentiment_lookup_by_title:
        return sentiment_lookup_by_title[title_key]

    title_soft = _canonical_title(title_text)
    if title_soft and title_soft in sentiment_lookup_by_title_soft:
        return sentiment_lookup_by_title_soft[title_soft]

    return None


def _extract_sentiment_metrics(sent_item: dict | None) -> dict[str, Any]:
    if not isinstance(sent_item, dict):
        return {
            "risk": 0.0,
            "positive": 0.0,
            "uncertainty": 0.0,
            "net": 0.0,
            "score": 0.0,
            "sentiment": "unknown",
            "sentiment_i18n": _dict_text_i18n("unknown", category="sentiment_labels"),
            "sentiment_label": "unknown",
            "sentiment_label_i18n": _dict_text_i18n("unknown", category="sentiment_labels"),
            "method": "unmatched",
            "method_i18n": _dict_text_i18n("unmatched"),
        }
    sentiment = _clean_text(sent_item.get("sentiment") or sent_item.get("sentiment_label") or "unknown") or "unknown"
    sentiment_label = _clean_text(sent_item.get("sentiment_label") or sentiment) or "unknown"
    return {
        "risk": round(float(sent_item.get("risk", 0.0) or 0.0), 6),
        "positive": round(float(sent_item.get("positive", 0.0) or 0.0), 6),
        "uncertainty": round(float(sent_item.get("uncertainty", 0.0) or 0.0), 6),
        "net": round(float(sent_item.get("net", sent_item.get("score", 0.0)) or 0.0), 6),
        "score": round(float(sent_item.get("score", sent_item.get("net", 0.0)) or 0.0), 6),
        "sentiment": sentiment,
        "sentiment_i18n": _finalize_text_i18n(sentiment, sent_item.get("sentiment_i18n") if isinstance(sent_item.get("sentiment_i18n"), dict) else None),
        "sentiment_label": sentiment_label,
        "sentiment_label_i18n": _finalize_text_i18n(sentiment_label, sent_item.get("sentiment_label_i18n") if isinstance(sent_item.get("sentiment_label_i18n"), dict) else None),
        "method": _clean_text(sent_item.get("method") or "rule_based") or "rule_based",
        "method_i18n": _finalize_text_i18n(_clean_text(sent_item.get("method") or "rule_based") or "rule_based", sent_item.get("method_i18n") if isinstance(sent_item.get("method_i18n"), dict) else None),
    }


def _infer_card_label(title: str, summary: str, tags: list[str]) -> str:
    joined = " ".join([_normalized_key(title), _normalized_key(summary), " ".join(_normalized_key(x) for x in tags)])
    for label, keywords in _LABEL_RULES:
        if any(kw in joined for kw in keywords):
            return label
    return "general"


def _extract_theme_hits(texts: list[str], explicit_topics: list[str]) -> list[str]:
    joined = " \n ".join(t.lower() for t in texts if isinstance(t, str) and t.strip())
    hits: list[str] = []
    for topic in explicit_topics:
        cleaned = _clean_text(topic)
        if cleaned and cleaned.lower() not in {h.lower() for h in hits}:
            hits.append(cleaned)
    for theme_id, keywords in _THEME_RULES:
        if any(kw in joined for kw in keywords):
            hits.append(theme_id)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in hits:
        key = _normalized_key(item)
        if key and key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def _extract_articles_from_daily(
    daily_doc: Any,
    *,
    sentiment_lookup_by_url: dict[str, dict] | None = None,
    sentiment_lookup_by_title: dict[str, dict] | None = None,
    sentiment_lookup_by_title_soft: dict[str, dict] | None = None,
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
    sentiment_lookup_by_title_soft = sentiment_lookup_by_title_soft or {}

    out: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()

    for a in items:
        if not isinstance(a, dict):
            continue

        title_text = _clean_text(a.get("title") or a.get("headline") or "")
        raw_url = a.get("url") or a.get("link")
        url_text = _as_str(raw_url).strip()

        if not url_text:
            continue

        summary_text = _clean_text(a.get("summary") or a.get("description") or a.get("excerpt") or a.get("content") or "")
        source_text = _clean_text(_parse_source_name(a.get("source")) or _as_str(a.get("domain")))
        published_at = _clean_text(a.get("published_at") or a.get("publishedAt") or a.get("published") or a.get("date") or "")

        image = a.get("urlToImage") or a.get("image") or a.get("thumbnail") or a.get("thumb") or a.get("og_image")
        if not (isinstance(image, str) and image.strip()):
            image = None

        tags = [_clean_text(x) for x in (a.get("tags") if isinstance(a.get("tags"), list) else []) if _clean_text(x)]

        dedupe_key = (_normalize_url(url_text), _canonical_title(title_text))
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        sent_item = _find_sentiment_match(
            title_text=title_text,
            url_text=url_text,
            sentiment_lookup_by_url=sentiment_lookup_by_url,
            sentiment_lookup_by_title=sentiment_lookup_by_title,
            sentiment_lookup_by_title_soft=sentiment_lookup_by_title_soft,
        )
        sent_metrics = _extract_sentiment_metrics(sent_item)

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

        label = _infer_card_label(title_text, summary_text, tags)
        label_i18n = _dict_text_i18n(label, category="labels")

        card = {
            "title": title_text,
            "title_i18n": title_i18n,
            "summary": summary_text,
            "summary_raw": summary_text,
            "summary_i18n": summary_i18n,
            "source": source_text,
            "source_i18n": source_i18n,
            "url": url_text,
            "image": image,
            "publishedAt": published_at,
            "published_at": published_at,
            "tags": tags,
            "category": "world_politics",
            "category_i18n": _finalize_text_i18n("World Politics", TEXT_I18N["section_title"]["world_politics"]),
            "label": label,
            "label_i18n": label_i18n,
            **sent_metrics,
            "relevance": round(max(float(sent_metrics["risk"]), abs(float(sent_metrics["score"]))), 6),
            "matched_sentiment": bool(sent_item),
        }
        out.append(card)

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
    today = sent.get("today") if isinstance(sent, dict) else None
    if isinstance(today, dict) and today:
        return {
            "risk": round(float(today.get("risk", 0.0) or 0.0), 6),
            "positive": round(float(today.get("positive", 0.0) or 0.0), 6),
            "uncertainty": round(float(today.get("uncertainty", 0.0) or 0.0), 6),
            "score": round(float(today.get("score", today.get("net", 0.0)) or 0.0), 6),
            "net": round(float(today.get("net", today.get("score", 0.0)) or 0.0), 6),
            "sentiment": _clean_text(today.get("sentiment") or today.get("sentiment_label") or "unknown") or "unknown",
            "sentiment_label": _clean_text(today.get("sentiment_label") or today.get("sentiment") or "unknown") or "unknown",
            "label_counts": today.get("label_counts") if isinstance(today.get("label_counts"), dict) else {},
        }
    block = sent.get("sentiment") if isinstance(sent, dict) else None
    if isinstance(block, dict):
        return {
            "risk": round(float(block.get("risk", 0.0) or 0.0), 6),
            "positive": round(float(block.get("positive", 0.0) or 0.0), 6),
            "uncertainty": round(float(block.get("uncertainty", 0.0) or 0.0), 6),
            "score": round(float(block.get("score", block.get("net", 0.0)) or 0.0), 6),
            "net": round(float(block.get("net", block.get("score", 0.0)) or 0.0), 6),
            "sentiment": _clean_text(block.get("sentiment") or block.get("sentiment_label") or "unknown") or "unknown",
            "sentiment_label": _clean_text(block.get("sentiment_label") or block.get("sentiment") or "unknown") or "unknown",
            "label_counts": block.get("label_counts") if isinstance(block.get("label_counts"), dict) else {},
        }
    return {
        "risk": 0.0,
        "positive": 0.0,
        "uncertainty": 0.0,
        "score": 0.0,
        "net": 0.0,
        "sentiment": "unknown",
        "sentiment_label": "unknown",
        "label_counts": {},
    }


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


def _human_theme_label(theme_id: str) -> str:
    mapping = {
        "middle_east_tension": "Middle East tension",
        "ukraine_russia_conflict": "Ukraine / Russia conflict pressure",
        "china_taiwan_pressure": "China / Taiwan strategic pressure",
        "energy_price_stress": "Energy price volatility",
        "inflation_rates_pressure": "Inflation / rates pressure",
        "trade_supply_chain_stress": "Trade / supply chain stress",
        "market_instability": "Market instability",
        "policy_uncertainty": "Policy uncertainty",
        "food_fertilizer_stress": "Food / fertilizer stress",
    }
    return mapping.get(theme_id, theme_id.replace("_", " ").strip())


def _build_signal_lists(cards: list[dict], summary_doc: dict) -> tuple[list[str], list[str], list[str]]:
    texts: list[str] = []
    for c in cards:
        texts.append(_as_str(c.get("title")))
        texts.append(_as_str(c.get("summary")))
        texts.append(" ".join(_as_str(x) for x in c.get("tags", [])))

    summary_text = _collect_summary_text(summary_doc)
    if summary_text:
        texts.append(summary_text)
    topics = _collect_topics(summary_doc)
    texts.extend(topics)

    hits = _extract_theme_hits(texts, topics)
    human_hits = [_human_theme_label(x) for x in hits]

    economic_ids = {"energy_price_stress", "inflation_rates_pressure", "trade_supply_chain_stress", "market_instability", "food_fertilizer_stress"}
    geopolitical_ids = {"middle_east_tension", "ukraine_russia_conflict", "china_taiwan_pressure", "policy_uncertainty"}

    economic = [_human_theme_label(x) for x in hits if x in economic_ids][:6]
    geopolitical = [_human_theme_label(x) for x in hits if x in geopolitical_ids][:6]
    return economic, geopolitical, human_hits[:8]


def _signal_density(n_signals: int) -> str:
    if n_signals <= 1:
        return "low"
    if n_signals <= 3:
        return "medium"
    return "high"


def _quality_flags(cards: list[dict], sentiment_block: dict, summary_text: str) -> list[str]:
    flags: list[str] = []
    if not cards:
        flags.append("no_cards")
    if cards and sum(1 for c in cards if c.get("matched_sentiment")) == 0:
        flags.append("no_per_article_sentiment_matches")
    if cards and sum(1 for c in cards if c.get("matched_sentiment")) < max(3, len(cards) // 4):
        flags.append("low_sentiment_match_ratio")
    if not summary_text:
        flags.append("missing_upstream_summary")
    if float(sentiment_block.get("uncertainty", 0.0) or 0.0) >= 0.30:
        flags.append("elevated_uncertainty")
    return flags


def _build_summary_structured(
    *,
    cards: list[dict],
    summary_doc: dict,
    sentiment_block: dict,
    latest_doc: dict,
    economic_signals: list[str],
    geopolitical_signals: list[str],
    all_signals: list[str],
) -> dict[str, Any]:
    _ = _sanitize_upstream_summary(
        _collect_summary_text(summary_doc),
        event_count_hint=len(cards),
    )
    matched_sentiment = sum(1 for c in cards if c.get("matched_sentiment"))
    label_counts = Counter(_clean_text(c.get("sentiment_label") or "unknown") or "unknown" for c in cards)
    dominant_label = label_counts.most_common(1)[0][0] if label_counts else _clean_text(sentiment_block.get("sentiment_label") or "unknown") or "unknown"
    top_headlines = [c.get("title") for c in sorted(cards, key=lambda c: (float(c.get("risk", 0.0) or 0.0), abs(float(c.get("score", 0.0) or 0.0))), reverse=True) if _clean_text(c.get("title"))][:3]

    new_url_count = 0
    for key in ("new_url_count", "n_new_urls"):
        value = latest_doc.get(key)
        if isinstance(value, int):
            new_url_count = value
            break
        meta = latest_doc.get("meta")
        if isinstance(meta, dict) and isinstance(meta.get(key), int):
            new_url_count = meta.get(key)
            break

    return {
        "event_count": len(cards),
        "matched_sentiment_count": matched_sentiment,
        "dominant_sentiment": dominant_label,
        "risk_level": _risk_label(float(sentiment_block.get("risk", 0.0) or 0.0)),
        "risk_value": round(float(sentiment_block.get("risk", 0.0) or 0.0), 6),
        "uncertainty": round(float(sentiment_block.get("uncertainty", 0.0) or 0.0), 6),
        "score": round(float(sentiment_block.get("score", sentiment_block.get("net", 0.0)) or 0.0), 6),
        "signal_density": _signal_density(len(all_signals)),
        "economic_signals": economic_signals,
        "geopolitical_signals": geopolitical_signals,
        "theme_hits": all_signals,
        "anchor_topics": _collect_topics(summary_doc),
        "upstream_summary": "",
        "top_headlines": top_headlines,
        "new_url_count": int(new_url_count or 0),
        "quality_flags": _quality_flags(cards, sentiment_block, ""),
    }


def _build_summary_text(structured: dict[str, Any]) -> str:
    event_count = int(structured.get("event_count", 0) or 0)
    dominant_sentiment = _clean_text(structured.get("dominant_sentiment") or "unknown") or "unknown"
    risk_level = _clean_text(structured.get("risk_level") or "LOW") or "LOW"
    signal_density = _clean_text(structured.get("signal_density") or "low") or "low"
    themes = [x for x in structured.get("theme_hits", []) if _clean_text(x)]
    top_headlines = [x for x in structured.get("top_headlines", []) if _clean_text(x)]
    new_url_count = int(structured.get("new_url_count", 0) or 0)
    upstream_summary = _clean_text(structured.get("upstream_summary"))

    if event_count <= 0:
        if upstream_summary:
            return upstream_summary
        return "No observable world politics events were materialized for this run."

    parts = [
        f"Observed {event_count} world politics items.",
        f"Current tone is {dominant_sentiment} with {risk_level.lower()} headline risk and {signal_density} signal density.",
    ]
    if themes:
        parts.append(f"Dominant themes: {', '.join(themes[:3])}.")
    if top_headlines:
        parts.append(f"Representative headlines ({len(top_headlines[:3])}): {' | '.join(top_headlines[:3])}.")
    if new_url_count > 0:
        parts.append(f"New URLs detected: {new_url_count}.")
    elif event_count > 0:
        parts.append("No new URLs detected in latest deduplicated intake.")
    return " ".join(parts)


def _build_summary_structured_i18n(structured: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in structured.items():
        if key == "upstream_summary":
            out[key] = {"en": "", "ja": "", "th": ""}
            continue

        if isinstance(value, str):
            if not value.strip():
                out[key] = {"en": "", "ja": "", "th": ""}
            else:
                out[key] = _dict_text_i18n(value)
        elif isinstance(value, list):
            out[key] = _dict_list_i18n([_as_str(x) for x in value])
        else:
            out[key] = value
    return out


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
    sentiment_lookup_by_url, sentiment_lookup_by_title, sentiment_lookup_by_title_soft = _build_sentiment_lookup(sent)
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
        sentiment_lookup_by_title_soft=sentiment_lookup_by_title_soft,
        translator=translator if args.translate_articles else None,
        force_translate_articles=args.force_translate_articles,
    )

    today = _extract_today(sent, cards_count=len(cards))
    sentiment_block = _extract_sentiment_block(sent)
    health_block = _extract_health_block(health_doc)
    global_risk = _risk_label(float(sentiment_block["risk"] or 0.0))
    economic_signals, geopolitical_signals, theme_hits = _build_signal_lists(cards, summary_doc)
    summary_structured = _build_summary_structured(
        cards=cards,
        summary_doc=summary_doc,
        sentiment_block=sentiment_block,
        latest_doc=latest_doc,
        economic_signals=economic_signals,
        geopolitical_signals=geopolitical_signals,
        all_signals=theme_hits,
    )
    daily_summary_text = _build_summary_text(summary_structured)

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
        theme_hits_i18n = _translate_meta_list(
            theme_hits,
            category=None,
            translator=translator,
            force_translate=True,
        )
    else:
        daily_summary_i18n = _dict_text_i18n(daily_summary_text)
        economic_signals_i18n = _dict_list_i18n(economic_signals, category="economic_signals")
        geopolitical_signals_i18n = _dict_list_i18n(geopolitical_signals, category="geopolitical_signals")
        theme_hits_i18n = _dict_list_i18n(theme_hits)

    summary_structured_i18n = _build_summary_structured_i18n(summary_structured)

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
        "summary": daily_summary_text,
        "summary_i18n": daily_summary_i18n,
        "summary_structured": summary_structured,
        "summary_structured_i18n": summary_structured_i18n,
        "events_count": len(cards),
        "sentiment": sentiment_block,
        "health": health_block,
        "economic_signals": economic_signals,
        "economic_signals_i18n": economic_signals_i18n,
        "geopolitical_signals": geopolitical_signals,
        "geopolitical_signals_i18n": geopolitical_signals_i18n,
        "theme_hits": theme_hits,
        "theme_hits_i18n": theme_hits_i18n,
        "cards": cards,
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
            "n_events": len(cards),
            "digest_card_count": len(cards),
            "matched_sentiment_count": summary_structured["matched_sentiment_count"],
            "signal_count": len(theme_hits),
            "quality_flags": summary_structured["quality_flags"],
            "notes": "rebuilt from *_latest.json (daily_summary/sentiment/health); article *_i18n may call local translation when enabled; upstream_summary is intentionally blank and empty strings bypass i18n conversion to prevent malformed summary payload leakage into structured view model",
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

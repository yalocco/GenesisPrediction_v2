
# scripts/build_world_view_model_latest.py
# Build /data/world_politics/analysis/view_model_latest.json for GUI pages.
#
# Purpose:
# - Provide a stable read-only ViewModel for index / overlay / digest / sentiment.
# - Join daily article cards with summary / sentiment / health.
# - Expose top-level fields expected by UI.
# - Emit *_i18n shadow fields for migration-safe multilingual rendering.
#
# Important:
# - This builder MUST NOT invent analysis.
# - It may localize fixed/generated labels it owns.
# - It may wrap article text in *_i18n with English fallback only.
# - True article translation still belongs to the upstream analysis / translation pipeline.

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

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
    "signal_label": {
        "Energy price volatility": {"en": "Energy price volatility", "ja": "エネルギー価格の変動", "th": "ความผันผวนของราคา ऊर्जा"},
        "Inflation / rates pressure": {"en": "Inflation / rates pressure", "ja": "インフレ・金利圧力", "th": "แรงกดดันด้านเงินเฟ้อและดอกเบี้ย"},
        "Trade / supply chain stress": {"en": "Trade / supply chain stress", "ja": "貿易・サプライチェーンの緊張", "th": "ความตึงเครียดด้านการค้าและซัพพลายเชน"},
        "Market instability": {"en": "Market instability", "ja": "市場の不安定化", "th": "ความไม่เสถียรของตลาด"},
        "Middle East tension": {"en": "Middle East tension", "ja": "中東情勢の緊張", "th": "ความตึงเครียดในตะวันออกกลาง"},
        "Ukraine / Russia conflict pressure": {"en": "Ukraine / Russia conflict pressure", "ja": "ウクライナ・ロシア紛争圧力", "th": "แรงกดดันจากความขัดแย้งยูเครน/รัสเซีย"},
        "US political uncertainty": {"en": "US political uncertainty", "ja": "米国政治の不確実性", "th": "ความไม่แน่นอนทางการเมืองของสหรัฐฯ"},
        "China / Taiwan strategic pressure": {"en": "China / Taiwan strategic pressure", "ja": "中国・台湾の戦略的圧力", "th": "แรงกดดันเชิงยุทธศาสตร์จีน/ไต้หวัน"},
    },
}


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


def _dict_text_i18n(base_text: str, category: str | None = None) -> dict[str, str]:
    text = _as_str(base_text).strip()
    if not text:
        return {"en": "", "ja": "", "th": ""}

    if dict_translate is not None:
        try:
            return _finalize_text_i18n(text, dict_translate(text, category=category))
        except Exception:
            pass

    return _finalize_text_i18n(text)


def _dict_list_i18n(base_list: list[str], category: str | None = None) -> dict[str, list[str]]:
    items = [_as_str(x).strip() for x in base_list if _as_str(x).strip()]
    if not items:
        return {"en": [], "ja": [], "th": []}

    if dict_translate_lang_list is not None:
        try:
            return dict_translate_lang_list(items, category=category)
        except Exception:
            pass

    return _finalize_list_i18n(items)


def _finalize_text_i18n(base_text: str, partial: dict[str, str] | None = None) -> dict[str, str]:
    partial = partial or {}
    en_text = str(partial.get("en") or base_text or "").strip()
    ja_text = str(partial.get("ja") or en_text).strip()
    th_text = str(partial.get("th") or en_text).strip()
    return {"en": en_text, "ja": ja_text, "th": th_text}


def _finalize_list_i18n(base_list: list[str], resolver: dict[str, dict[str, str]] | None = None) -> dict[str, list[str]]:
    if not resolver:
        return {
            "en": list(base_list),
            "ja": list(base_list),
            "th": list(base_list),
        }
    out = {"en": [], "ja": [], "th": []}
    for item in base_list:
        mapping = resolver.get(item) or {}
        out["en"].append(str(mapping.get("en") or item))
        out["ja"].append(str(mapping.get("ja") or mapping.get("en") or item))
        out["th"].append(str(mapping.get("th") or mapping.get("en") or item))
    return out


def _parse_source_name(value: Any) -> str:
    if isinstance(value, dict):
        return _as_str(value.get("name") or value.get("id") or "")
    return _as_str(value)


def _wrap_article_text_i18n(text: Any, category: str | None = None) -> dict[str, str]:
    base = _as_str(text).strip()
    return _dict_text_i18n(base, category=category)


def _extract_articles_from_daily(daily_doc: Any) -> list[dict]:
    if isinstance(daily_doc, list):
        items = daily_doc
    elif isinstance(daily_doc, dict):
        items = (
            daily_doc.get("items")
            or daily_doc.get("articles")
            or daily_doc.get("data")
            or daily_doc.get("news")
            or []
        )
    else:
        items = []

    if not isinstance(items, list):
        return []

    out: list[dict] = []
    for a in items:
        if not isinstance(a, dict):
            continue

        title = a.get("title") or a.get("headline") or ""
        url = a.get("url") or a.get("link") or ""
        summary = a.get("summary") or a.get("description") or a.get("excerpt") or ""
        source = _parse_source_name(a.get("source")) or _as_str(a.get("domain"))
        published_at = (
            a.get("published_at")
            or a.get("publishedAt")
            or a.get("published")
            or a.get("date")
            or ""
        )

        image = (
            a.get("urlToImage")
            or a.get("image")
            or a.get("thumbnail")
            or a.get("thumb")
            or a.get("og_image")
        )
        if not (isinstance(image, str) and image.strip()):
            image = None

        tags = a.get("tags")
        if not isinstance(tags, list):
            tags = []

        title_text = _as_str(title).strip()
        summary_text = _as_str(summary).strip()
        source_text = _as_str(source).strip()

        out.append(
            {
                "title": title_text,
                "title_i18n": _wrap_article_text_i18n(title_text),
                "summary": summary_text,
                "summary_i18n": _wrap_article_text_i18n(summary_text),
                "source": source_text,
                "source_i18n": _dict_text_i18n(source_text),
                "url": _as_str(url),
                "image": image,
                "published_at": _as_str(published_at),
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
        risk = float(block.get("risk", 0.0) or 0.0)
        positive = float(block.get("positive", 0.0) or 0.0)
        uncertainty = float(block.get("uncertainty", 0.0) or 0.0)
        return {
            "risk": round(risk, 6),
            "positive": round(positive, 6),
            "uncertainty": round(uncertainty, 6),
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
            return value.strip()

    lines = summary_doc.get("lines")
    if isinstance(lines, list):
        text = " ".join(_as_str(x) for x in lines if _as_str(x).strip())
        if text.strip():
            return text.strip()

    return ""


def _collect_topics(summary_doc: dict) -> list[str]:
    if not isinstance(summary_doc, dict):
        return []

    topics = summary_doc.get("topics")
    if isinstance(topics, list):
        return [_as_str(x).strip() for x in topics if _as_str(x).strip()]

    return []


def _match_keywords(texts: list[str], keywords: list[str]) -> list[str]:
    joined = " \n ".join(t.lower() for t in texts if isinstance(t, str) and t.strip())
    matched: list[str] = []
    for kw in keywords:
        if kw in joined:
            matched.append(kw)
    return matched


def _build_signal_lists(cards: list[dict], summary_doc: dict) -> tuple[list[str], list[str]]:
    texts = []
    for c in cards:
        texts.append(_as_str(c.get("title")))
        texts.append(_as_str(c.get("summary")))
        texts.append(" ".join(_as_str(x) for x in c.get("tags", [])))

    summary_text = _collect_summary_text(summary_doc)
    if summary_text:
        texts.append(summary_text)

    topics = _collect_topics(summary_doc)
    texts.extend(topics)

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

    economic_signals: list[str] = []
    geopolitical_signals: list[str] = []

    for label, kws in economic_rules:
        if _match_keywords(texts, kws):
            economic_signals.append(label)

    for label, kws in geopolitical_rules:
        if _match_keywords(texts, kws):
            geopolitical_signals.append(label)

    return economic_signals[:6], geopolitical_signals[:6]


def main() -> int:
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
            raise FileNotFoundError(
                f"daily source not found: {daily_path} (and fallback {fallback})"
            )

    daily_doc = _load_json(daily_path)
    cards = _extract_articles_from_daily(daily_doc)

    today = _extract_today(sent, cards_count=len(cards))
    sentiment_block = _extract_sentiment_block(sent)
    health_block = _extract_health_block(health_doc)

    global_risk = _risk_label(sentiment_block["risk"])
    economic_signals, geopolitical_signals = _build_signal_lists(cards, summary_doc)
    daily_summary_text = _collect_summary_text(summary_doc)

    section_title_i18n = _finalize_text_i18n("World Politics", TEXT_I18N["section_title"]["world_politics"])
    global_risk_i18n = _dict_text_i18n(global_risk, category="risk_levels")

    vm = {
        "version": "v2",
        "date": date,
        "as_of": date,
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
        "global_risk": global_risk,
        "global_risk_i18n": global_risk_i18n,
        "daily_summary": daily_summary_text,
        "daily_summary_i18n": _dict_text_i18n(daily_summary_text),
        "events_count": len(cards),
        "sentiment": sentiment_block,
        "health": health_block,
        "economic_signals": economic_signals,
        "economic_signals_i18n": _dict_list_i18n(economic_signals, category="economic_signals"),
        "geopolitical_signals": geopolitical_signals,
        "geopolitical_signals_i18n": _dict_list_i18n(geopolitical_signals, category="geopolitical_signals"),
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
            "notes": "rebuilt from *_latest.json (daily_summary/sentiment/health); *_i18n added with English fallback for untranslated article text",
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
        f"(cards={len(cards)}, date={date}, risk={global_risk}, source={daily_path})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

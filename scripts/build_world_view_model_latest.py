# scripts/build_world_view_model_latest.py
# Build /data/world_politics/analysis/view_model_latest.json for GUI pages.
#
# Purpose:
# - Provide a stable read-only ViewModel for index / overlay / digest / sentiment.
# - Join daily article cards with summary / sentiment / health.
# - Expose top-level fields expected by UI:
#     global_risk
#     economic_signals
#     geopolitical_signals
#
# Inputs:
# - data/world_politics/analysis/latest.json
# - data/world_politics/analysis/sentiment_latest.json
# - data/world_politics/analysis/daily_summary_latest.json
# - data/world_politics/analysis/health_latest.json
# - data/world_politics/YYYY-MM-DD.json
#
# Output:
# - data/world_politics/analysis/view_model_latest.json

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_WORLD = ROOT / "data" / "world_politics"
ANALYSIS = DATA_WORLD / "analysis"

LATEST_JSON = ANALYSIS / "latest.json"
SENT_LATEST_JSON = ANALYSIS / "sentiment_latest.json"
SUMMARY_LATEST_JSON = ANALYSIS / "daily_summary_latest.json"
HEALTH_LATEST_JSON = ANALYSIS / "health_latest.json"
OUT_JSON = ANALYSIS / "view_model_latest.json"


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
    """
    latest.json usually has:
      "source_file": "/data/world_politics/2026-02-14.json"
    We map that to repo-local:
      <repo>/data/world_politics/2026-02-14.json
    """
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


def _parse_source_name(value: Any) -> str:
    if isinstance(value, dict):
        return _as_str(value.get("name") or value.get("id") or "")
    return _as_str(value)


def _extract_articles_from_daily(daily_doc: Any) -> list[dict]:
    """
    Support common daily shapes:
      - {"items":[...]} or {"articles":[...]} or list itself
    """
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

        out.append(
            {
                "title": _as_str(title),
                "summary": _as_str(summary),
                "source": _as_str(source),
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

    vm = {
        "version": "v2",
        "date": date,
        "as_of": date,
        "global_risk": global_risk,
        "daily_summary": daily_summary_text,
        "events_count": len(cards),
        "sentiment": sentiment_block,
        "health": health_block,
        "economic_signals": economic_signals,
        "geopolitical_signals": geopolitical_signals,
        "sections": [
            {
                "id": "world_politics",
                "title": "World Politics",
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
            "notes": "rebuilt from *_latest.json (daily_summary/sentiment/health)",
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
# scripts/publish_daily_news_latest.py
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "world_politics"
ANALYSIS_DIR = RAW_DIR / "analysis"


def _as_str(value: Any) -> str:
    return "" if value is None else str(value)


def _pick_latest_article(obj: dict[str, Any]) -> dict[str, Any]:
    articles = obj.get("articles")
    if not isinstance(articles, list) or not articles:
        return {}

    valid_articles = [a for a in articles if isinstance(a, dict)]
    if not valid_articles:
        return {}

    def published_at(article: dict[str, Any]) -> str:
        value = article.get("publishedAt") or article.get("published_at") or ""
        return _as_str(value)

    return max(valid_articles, key=published_at)


def _build_pointer_doc(date: str, obj: dict[str, Any]) -> dict[str, Any]:
    articles = obj.get("articles")
    count = len(articles) if isinstance(articles, list) else 0
    latest_article = _pick_latest_article(obj)

    latest = {
        "title": _as_str(latest_article.get("title")),
        "url": _as_str(latest_article.get("url")),
        "published_at": _as_str(latest_article.get("publishedAt") or latest_article.get("published_at")),
        "sentiment_label": _as_str(latest_article.get("sentiment_label")),
        "sentiment_score": latest_article.get("sentiment_score", 0.0),
        "topic": _as_str(latest_article.get("topic", "other")) or "other",
    }

    return {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": f"/data/world_politics/{date}.json",
        "count": count,
        "latest": latest,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    src = RAW_DIR / f"{args.date}.json"
    if not src.exists():
        raise SystemExit(f"[ERR] missing raw news: {src}")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    dst_latest = ANALYSIS_DIR / "daily_news_latest.json"
    dst_dated = ANALYSIS_DIR / f"daily_news_{args.date}.json"
    dst_pointer = ANALYSIS_DIR / "latest.json"

    # 読めることを保証してからコピー（壊れたJSONをlatestにしない）
    obj = json.loads(src.read_text(encoding="utf-8"))
    txt = json.dumps(obj, ensure_ascii=False, indent=2)

    pointer_doc = _build_pointer_doc(args.date, obj)
    pointer_txt = json.dumps(pointer_doc, ensure_ascii=False, indent=2)

    dst_latest.write_text(txt, encoding="utf-8")
    dst_dated.write_text(txt, encoding="utf-8")
    dst_pointer.write_text(pointer_txt, encoding="utf-8")

    print("[OK] published daily_news_latest")
    print(f"  src : {src}")
    print(f"  latest: {dst_latest}")
    print(f"  dated : {dst_dated}")
    print(f"  pointer: {dst_pointer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

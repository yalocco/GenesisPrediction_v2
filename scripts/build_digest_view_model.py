#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def extract_summary_text(summary_json: Dict[str, Any], daily_summary_json: Dict[str, Any]) -> Optional[str]:
    """
    Prefer the analyzer's summary.json text.
    Fall back to daily_summary_latest.json only if it already contains a real summary-like field.
    """
    candidates: List[Any] = [
        summary_json.get("summary"),
        summary_json.get("text"),
        summary_json.get("daily_summary"),
        summary_json.get("body"),
        summary_json.get("content"),
    ]

    overview = summary_json.get("overview")
    if isinstance(overview, dict):
        candidates.extend([
            overview.get("summary"),
            overview.get("text"),
            overview.get("body"),
        ])

    daily_candidates: List[Any] = [
        daily_summary_json.get("summary"),
        daily_summary_json.get("text"),
        daily_summary_json.get("daily_summary"),
        daily_summary_json.get("summary_text"),
        daily_summary_json.get("body"),
        daily_summary_json.get("content"),
    ]

    yesterday_summary = daily_summary_json.get("yesterday_summary")
    if isinstance(yesterday_summary, dict):
        daily_candidates.extend([
            yesterday_summary.get("summary"),
            yesterday_summary.get("text"),
            yesterday_summary.get("body"),
        ])

    return first_non_empty(*(candidates + daily_candidates))


def extract_titles(news_json: Dict[str, Any], daily_summary_json: Dict[str, Any]) -> List[str]:
    titles: List[str] = []

    for key in ("events", "items", "articles", "news"):
        items = news_json.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    title = first_non_empty(
                        item.get("title"),
                        item.get("headline"),
                        item.get("name"),
                    )
                    if title:
                        titles.append(title)

    yesterday_summary = daily_summary_json.get("yesterday_summary")
    if isinstance(yesterday_summary, dict):
        ys_titles = yesterday_summary.get("titles")
        if isinstance(ys_titles, list):
            for title in ys_titles:
                if isinstance(title, str) and title.strip():
                    titles.append(title.strip())

    seen = set()
    unique_titles: List[str] = []
    for title in titles:
        if title not in seen:
            seen.add(title)
            unique_titles.append(title)
    return unique_titles


def extract_highlights(summary_json: Dict[str, Any], daily_summary_json: Dict[str, Any], titles: List[str]) -> List[str]:
    highlights: List[str] = []

    for key in ("highlights", "bullets", "key_points"):
        value = summary_json.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    highlights.append(item.strip())

    anchors = daily_summary_json.get("anchors")
    if isinstance(anchors, list):
        anchor_line = ", ".join(str(x).strip() for x in anchors if str(x).strip())
        if anchor_line:
            highlights.append(f"Anchors: {anchor_line}")

    if not highlights:
        highlights.extend(titles[:5])

    return highlights[:8]


def build_payload(
    date_value: str,
    summary_text: Optional[str],
    titles: List[str],
    highlights: List[str],
    daily_summary_json: Dict[str, Any],
) -> Dict[str, Any]:
    new_urls = daily_summary_json.get("new_urls")
    if not isinstance(new_urls, list):
        new_urls = []

    n_events = daily_summary_json.get("n_events")
    if not isinstance(n_events, int):
        n_events = len(titles)

    return {
        "status": "ok",
        "generated_at": now_iso(),
        "date": date_value,
        "summary": summary_text or "",
        "summary_available": bool(summary_text),
        "highlights": highlights,
        "articles": titles[:12],
        "meta": {
            "n_events": n_events,
            "new_url_count": len(new_urls),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build digest view model.")
    parser.add_argument("--date", required=True, help="Target local date YYYY-MM-DD")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    analysis_dir = root / "data" / "world_politics" / "analysis"
    digest_dir = root / "data" / "digest"
    digest_view_dir = digest_dir / "view"

    daily_news_path = analysis_dir / f"daily_news_{args.date}.json"
    daily_summary_latest_path = analysis_dir / "daily_summary_latest.json"
    summary_json_path = analysis_dir / "summary.json"

    daily_news_json = load_json(daily_news_path)
    daily_summary_json = load_json(daily_summary_latest_path)
    summary_json = load_json(summary_json_path)

    summary_text = extract_summary_text(summary_json, daily_summary_json)
    titles = extract_titles(daily_news_json, daily_summary_json)
    highlights = extract_highlights(summary_json, daily_summary_json, titles)

    payload = build_payload(
        date_value=args.date,
        summary_text=summary_text,
        titles=titles,
        highlights=highlights,
        daily_summary_json=daily_summary_json,
    )

    dated_path = digest_view_dir / f"{args.date}.json"
    latest_path_a = digest_dir / "view_model_latest.json"
    latest_path_b = digest_view_dir / "view_model_latest.json"

    write_json(dated_path, payload)
    write_json(latest_path_a, payload)
    write_json(latest_path_b, payload)

    print(f"[OK] wrote dated : {dated_path.as_posix()}")
    print(f"[OK] wrote latest: {latest_path_a.as_posix()}")
    print(f"[OK] wrote latest: {latest_path_b.as_posix()}")

    if payload["summary_available"]:
        print("[OK] summary loaded")
    else:
        print("[WARN] summary missing (summary.json / daily_summary_latest.json text not found)")


if __name__ == "__main__":
    main()

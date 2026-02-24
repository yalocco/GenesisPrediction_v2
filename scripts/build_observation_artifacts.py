#!/usr/bin/env python3
"""
Build observation artifacts expected by Data Health:

- data/world_politics/analysis/observation_YYYY-MM-DD.md
- data/world_politics/analysis/observation_YYYY-MM-DD.json
- data/world_politics/analysis/observation_latest.md

This is a derived artifact generator (safe for SST).
It does NOT modify upstream raw inputs.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"


def _validate_date(s: str) -> str:
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError as e:
        raise SystemExit(f"[ERROR] invalid --date '{s}' (expected YYYY-MM-DD)") from e
    return s


def _load_json_if_exists(p: Path) -> Dict[str, Any]:
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            v = json.load(f)
        return v if isinstance(v, dict) else {"_value": v}
    except Exception:
        return {"_read_error": str(p)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, type=_validate_date, help="YYYY-MM-DD")
    args = ap.parse_args()

    date = args.date

    daily_summary = _load_json_if_exists(ANALYSIS_DIR / "daily_summary_latest.json")
    sentiment_latest = _load_json_if_exists(ANALYSIS_DIR / "sentiment_latest.json")

    def pick(obj: Dict[str, Any], keys: list[str]) -> Any:
        cur: Any = obj
        for k in keys:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                return None
        return cur

    risk = pick(sentiment_latest, ["metrics", "risk"]) or pick(sentiment_latest, ["risk"])
    positive = pick(sentiment_latest, ["metrics", "positive"]) or pick(sentiment_latest, ["positive"])
    uncertainty = pick(sentiment_latest, ["metrics", "uncertainty"]) or pick(sentiment_latest, ["uncertainty"])

    headline = pick(daily_summary, ["headline"]) or pick(daily_summary, ["title"]) or pick(daily_summary, ["summary", "title"])
    bullets = pick(daily_summary, ["bullets"]) or pick(daily_summary, ["points"]) or pick(daily_summary, ["summary", "bullets"])

    lines: list[str] = []
    lines.append(f"# Observation {date}")
    lines.append("")
    if headline:
        lines.append("## Headline")
        lines.append(f"- {headline}")
        lines.append("")
    if bullets and isinstance(bullets, list):
        lines.append("## Key points")
        for b in bullets[:10]:
            lines.append(f"- {str(b)}")
        lines.append("")
    lines.append("## Sentiment (latest)")
    lines.append(f"- risk: {risk if risk is not None else 'n/a'}")
    lines.append(f"- positive: {positive if positive is not None else 'n/a'}")
    lines.append(f"- uncertainty: {uncertainty if uncertainty is not None else 'n/a'}")
    lines.append("")
    lines.append("## Links (local artifacts)")
    lines.append(f"- daily_news: daily_news_{date}.html")
    lines.append(f"- fx overlay (legacy): fx_overlay_{date}.png")
    lines.append("")

    md_text = "\n".join(lines)

    md_dated = ANALYSIS_DIR / f"observation_{date}.md"
    json_dated = ANALYSIS_DIR / f"observation_{date}.json"
    md_latest = ANALYSIS_DIR / "observation_latest.md"

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    md_dated.write_text(md_text, encoding="utf-8")
    md_latest.write_text(md_text, encoding="utf-8")

    payload: Dict[str, Any] = {
        "date": date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "artifacts": {
            "daily_news_html": f"daily_news_{date}.html",
            "fx_overlay_legacy_png": f"fx_overlay_{date}.png",
            "observation_md": md_dated.name,
            "observation_latest_md": md_latest.name,
        },
        "sentiment": {
            "risk": risk,
            "positive": positive,
            "uncertainty": uncertainty,
        },
    }

    with json_dated.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("[OK] built observation artifacts")
    print(f"  md_dated : {md_dated}")
    print(f"  json     : {json_dated}")
    print(f"  md_latest: {md_latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
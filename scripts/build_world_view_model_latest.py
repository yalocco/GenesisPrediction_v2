# scripts/build_world_view_model_latest.py
# Build /data/world_politics/analysis/view_model_latest.json for GUI/Sentiment join.
#
# Key point:
# - analysis/latest.json contains only ONE "latest" item, not a list.
# - It provides "source_file" which points to the daily full list (e.g. /data/world_politics/2026-02-14.json).
#
# Inputs:
# - data/world_politics/analysis/latest.json  (to locate daily source_file)
# - data/world_politics/analysis/sentiment_latest.json (for date alignment + today summary)
# - data/world_politics/YYYY-MM-DD.json (daily full list)
#
# Output:
# - data/world_politics/analysis/view_model_latest.json

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_WORLD = ROOT / "data" / "world_politics"
ANALYSIS = DATA_WORLD / "analysis"

LATEST_JSON = ANALYSIS / "latest.json"
SENT_LATEST_JSON = ANALYSIS / "sentiment_latest.json"
OUT_JSON = ANALYSIS / "view_model_latest.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jst_now_iso() -> str:
    jst = timezone(timedelta(hours=9))
    return datetime.now(tz=jst).isoformat(timespec="seconds")


def _pick_date(sent: dict) -> str:
    for k in ("base_date", "date"):
        v = sent.get(k)
        if isinstance(v, str) and v:
            return v
    return "latest"


def _resolve_source_file(latest_doc: dict) -> Path:
    """
    latest.json has:
      "source_file": "/data/world_politics/2026-02-14.json"
    We map that to repo-local:
      <repo>/data/world_politics/2026-02-14.json
    """
    sf = latest_doc.get("source_file")
    if not isinstance(sf, str) or not sf:
        # fallback: use date in latest.json
        d = latest_doc.get("date")
        if isinstance(d, str) and d:
            return DATA_WORLD / f"{d}.json"
        raise ValueError("latest.json has no source_file and no usable date")

    # Normalize linux-like absolute path
    # Expected prefix: /data/world_politics/
    prefix = "/data/world_politics/"
    if sf.startswith(prefix):
        name = sf[len(prefix):]
        return DATA_WORLD / name

    # If it points elsewhere, take basename as fallback
    return DATA_WORLD / Path(sf).name


def _as_str(x) -> str:
    return "" if x is None else str(x)


def _extract_articles_from_daily(daily_doc: Any) -> list[dict]:
    """
    Support common daily shapes:
      - {"items":[...]} or {"articles":[...]} or list itself
    Each article may have:
      title, description/summary, source, url, urlToImage/image/thumbnail, published_at, topic, sentiment_score/label
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

        # Source can be a string or dict
        source = ""
        src = a.get("source")
        if isinstance(src, dict):
            source = src.get("name") or src.get("id") or ""
        else:
            source = a.get("source") or a.get("domain") or ""

        # image candidates
        image = (
            a.get("urlToImage")
            or a.get("image")
            or a.get("thumbnail")
            or a.get("thumb")
            or a.get("og_image")
        )
        if not (isinstance(image, str) and image.strip()):
            image = None

        out.append(
            {
                "title": _as_str(title),
                "summary": _as_str(summary),
                "source": _as_str(source),
                "url": _as_str(url),
                "image": image,
                "tags": a.get("tags") if isinstance(a.get("tags"), list) else [],
            }
        )

    return out


def main() -> int:
    if not LATEST_JSON.exists():
        raise FileNotFoundError(f"missing: {LATEST_JSON}")

    latest_doc = _load_json(LATEST_JSON)
    sent = _load_json(SENT_LATEST_JSON) if SENT_LATEST_JSON.exists() else {}

    date = _pick_date(sent)

    daily_path = _resolve_source_file(latest_doc)
    if not daily_path.exists():
        # last-resort fallback: try date-based
        fallback = DATA_WORLD / f"{date}.json"
        if fallback.exists():
            daily_path = fallback
        else:
            raise FileNotFoundError(f"daily source not found: {daily_path} (and fallback {fallback})")

    daily_doc = _load_json(daily_path)
    cards = _extract_articles_from_daily(daily_doc)

    # today summary: prefer sentiment_latest.json.today if available
    today = sent.get("today") if isinstance(sent.get("today"), dict) else {}
    if not today:
        today = {"articles": len(cards)}

    vm = {
        "version": "v1",
        "date": date,
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
            "generated_at": _jst_now_iso(),
            "generator": "world_view_model_builder",
            "source": str(daily_path),
        },
        "today": today,
    }

    OUT_JSON.write_text(json.dumps(vm, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote: {OUT_JSON} (cards={len(cards)}, date={date}, source={daily_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# scripts/build_world_view_model_latest.py
# Build /data/world_politics/analysis/view_model_latest.json for GUI/Sentiment join.
#
# Inputs (preferred):
# - data/world_politics/analysis/latest.json
# - data/world_politics/analysis/sentiment_latest.json (for date alignment + today summary)
#
# Output:
# - data/world_politics/analysis/view_model_latest.json

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "world_politics" / "analysis"

LATEST_JSON = ANALYSIS / "latest.json"
SENT_LATEST_JSON = ANALYSIS / "sentiment_latest.json"
OUT_JSON = ANALYSIS / "view_model_latest.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_date(sent: dict) -> str:
    # Prefer sentiment_latest.json date / base_date to keep join consistent
    for k in ("base_date", "date"):
        v = sent.get(k)
        if isinstance(v, str) and v:
            return v
    return "latest"


def _as_str(x) -> str:
    return "" if x is None else str(x)


def _extract_articles(latest: dict) -> list[dict]:
    """
    Support several common shapes:
      - {"items":[...]} or {"articles":[...]} or list itself
    Each article may have: title, description/summary, source, url, urlToImage/image
    """
    if isinstance(latest, list):
        items = latest
    else:
        items = (
            latest.get("items")
            or latest.get("articles")
            or latest.get("data")
            or []
        )
    if not isinstance(items, list):
        return []

    out: list[dict] = []
    for a in items:
        if not isinstance(a, dict):
            continue

        title = a.get("title") or a.get("headline") or ""
        url = a.get("url") or a.get("link") or ""
        source = ""
        src = a.get("source")
        if isinstance(src, dict):
            source = src.get("name") or src.get("id") or ""
        else:
            source = a.get("source") or a.get("domain") or ""

        summary = a.get("summary") or a.get("description") or a.get("excerpt") or ""

        # image candidates (keep as URL string if present, else null)
        image = (
            a.get("urlToImage")
            or a.get("image")
            or a.get("thumbnail")
            or a.get("thumb")
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

    latest = _load_json(LATEST_JSON)
    sent = _load_json(SENT_LATEST_JSON) if SENT_LATEST_JSON.exists() else {}

    date = _pick_date(sent)
    cards = _extract_articles(latest)

    # today summary: prefer sentiment_latest.json.today if available
    today = sent.get("today") if isinstance(sent.get("today"), dict) else {}
    # fallback: basic counts
    if not today:
        today = {"articles": len(cards)}

    # generated_at in JST
    jst = timezone(timedelta(hours=9))
    generated_at = datetime.now(tz=jst).isoformat(timespec="seconds")

    vm = {
        "version": "v1",
        "date": date,
        "sections": [
            {
                "id": "world_politics",
                "title": "World Politics",
                "status": "ok",
                "cards": cards,
                "notes": "generated_from=analysis/latest.json",
            }
        ],
        "meta": {
            "generated_at": generated_at,
            "generator": "world_view_model_builder",
            "source": "analysis/latest.json",
        },
        "today": today,
    }

    OUT_JSON.write_text(json.dumps(vm, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote: {OUT_JSON} (cards={len(cards)}, date={date})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

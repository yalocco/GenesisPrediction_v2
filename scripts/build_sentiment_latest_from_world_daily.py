# scripts/build_sentiment_latest_from_world_daily.py
# Build analysis/sentiment_latest.json (and sentiment_<date>.json) from the world daily source file.
#
# Why:
# - Your sentiment_<date>.json currently has stale items (URLs from old days), so join becomes all-missing.
# - This script reconstructs sentiment items directly from data/world_politics/<date>.json,
#   using sentiment_score if present, and deriving risk/positive/uncertainty.
#
# Usage:
#   .\.venv\Scripts\python.exe scripts\build_sentiment_latest_from_world_daily.py --date 2026-02-14

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_WORLD = ROOT / "data" / "world_politics"
ANALYSIS = DATA_WORLD / "analysis"

OUT_LATEST = ANALYSIS / "sentiment_latest.json"


def jst_iso() -> str:
    jst = timezone(timedelta(hours=9))
    return datetime.now(tz=jst).isoformat(timespec="seconds")


def load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def backup(path: Path) -> None:
    if not path.exists():
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.with_suffix(path.suffix + f".bak_{ts}")
    shutil.copy2(path, bak)


def get_items_from_daily(daily: Any) -> list[dict]:
    # Support common shapes: list, {"items":[...]}, {"articles":[...]}
    if isinstance(daily, list):
        items = daily
    elif isinstance(daily, dict):
        items = daily.get("items") or daily.get("articles") or daily.get("data") or daily.get("news") or []
    else:
        items = []
    if not isinstance(items, list):
        return []
    out: list[dict] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        out.append(a)
    return out


def parse_source(a: dict) -> str:
    s = a.get("source")
    if isinstance(s, dict):
        return str(s.get("name") or s.get("id") or "")
    return str(a.get("source") or a.get("domain") or "")


def guess_uncertainty(label: str, net: float) -> float:
    # Very simple, safe heuristic:
    # - neutral tends to be more uncertain
    # - strong magnitude tends to be less uncertain
    label = (label or "").lower().strip()
    mag = abs(net)
    base = 0.25
    if label == "neutral":
        base = 0.35
    elif label in ("positive", "negative"):
        base = 0.22
    # reduce uncertainty when |net| is large
    u = base - min(0.12, mag * 0.15)
    if u < 0.05:
        u = 0.05
    if u > 0.6:
        u = 0.6
    return float(u)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    date = args.date
    daily_path = DATA_WORLD / f"{date}.json"
    if not daily_path.exists():
        print(f"[ERR] daily not found: {daily_path}")
        return 2

    daily_doc = load_json(daily_path)
    src_items = get_items_from_daily(daily_doc)
    if not src_items:
        print(f"[ERR] no items found in: {daily_path}")
        return 2

    items: list[dict] = []
    sum_risk = 0.0
    sum_pos = 0.0
    sum_unc = 0.0

    for a in src_items:
        url = str(a.get("url") or a.get("link") or "").strip()
        title = str(a.get("title") or a.get("headline") or "").strip()
        source = parse_source(a).strip()

        # net score
        score = a.get("sentiment_score")
        try:
            net = float(score) if score is not None else 0.0
        except Exception:
            net = 0.0

        # label (optional)
        label = str(a.get("sentiment_label") or a.get("label") or "").strip()

        risk = max(0.0, -net)
        positive = max(0.0, net)
        uncertainty = guess_uncertainty(label, net)

        sum_risk += risk
        sum_pos += positive
        sum_unc += uncertainty

        items.append(
            {
                "url": url,
                "title": title,
                "source": source,
                "sentiment_label": label or None,
                "net": net,
                "risk": risk,
                "positive": positive,
                "uncertainty": uncertainty,
            }
        )

    n = len(items)
    today = {
        "articles": n,
        "risk": (sum_risk / n) if n else 0.0,
        "positive": (sum_pos / n) if n else 0.0,
        "uncertainty": (sum_unc / n) if n else 0.0,
        "net": ((sum_pos - sum_risk) / n) if n else 0.0,
    }

    out = {
        "date": date,
        "base": date,
        "base_date": date,
        "generated_at": jst_iso(),
        "source_file": str(daily_path),
        "items": items,
        "today": today,
        "summary": {
            "fallback_background_items": 0,
            "note": "rebuilt from world daily file (safe restore)",
        },
    }

    dated_out = ANALYSIS / f"sentiment_{date}.json"

    # backups
    backup(OUT_LATEST)
    backup(dated_out)

    OUT_LATEST.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    dated_out.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] wrote: {OUT_LATEST} ({OUT_LATEST.stat().st_size} bytes)")
    print(f"[OK] wrote: {dated_out} ({dated_out.stat().st_size} bytes)")
    print(f"[INFO] items={n}  today.net={today['net']:.6f}  today.risk={today['risk']:.6f}  today.pos={today['positive']:.6f}  today.unc={today['uncertainty']:.6f}")
    print("[INFO] sample urls:")
    for it in items[:5]:
        print("  -", it["url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

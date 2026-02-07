# scripts/rebuild_sentiment_timeseries_full.py
"""
Rebuild data/world_politics/analysis/sentiment_timeseries.csv
from existing sentiment_YYYY-MM-DD.json files.

Robust extractor:
- Supports summary at:
    obj.today
    obj.summary
    obj.sentiment.today / obj.sentiment.summary
    obj.meta.today / obj.meta.summary (just in case)
- If no summary, aggregates from per-item list:
    keys candidates: items, articles, rows, sentiments, data
  For each item, uses risk/positive/uncertainty/net if present.
  Aggregation: mean of available fields across items.
"""

from __future__ import annotations

from pathlib import Path
import csv
import json
import re
from typing import Any, Dict, Iterable, Optional, Tuple, List

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "world_politics" / "analysis"
OUT = ANALYSIS / "sentiment_timeseries.csv"

PAT = re.compile(r"^sentiment_(\d{4}-\d{2}-\d{2})\.json$")


def _to_int(v: Any, default: int = 0) -> int:
    try:
        if v is None:
            return default
        return int(v)
    except Exception:
        return default


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _get_dict(obj: Any, *keys: str) -> Optional[dict]:
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur if isinstance(cur, dict) else None


def _pick_summary_dict(obj: dict) -> Optional[dict]:
    # Common places
    for path in [
        ("today",),
        ("summary",),
        ("sentiment", "today"),
        ("sentiment", "summary"),
        ("meta", "today"),
        ("meta", "summary"),
    ]:
        d = _get_dict(obj, *path)
        if isinstance(d, dict):
            return d
    return None


def _find_item_list(obj: dict) -> Optional[List[Any]]:
    # Candidates where per-article sentiment rows might live
    for k in ("items", "articles", "rows", "sentiments", "data"):
        v = obj.get(k)
        if isinstance(v, list) and v:
            return v
    # Sometimes nested under "today" etc.
    for path in [("today",), ("sentiment", "today"), ("summary",), ("sentiment", "summary")]:
        d = _get_dict(obj, *path)
        if isinstance(d, dict):
            for k in ("items", "articles", "rows", "sentiments", "data"):
                v = d.get(k)
                if isinstance(v, list) and v:
                    return v
    return None


def _extract_from_summary_dict(d: dict) -> Dict[str, Any]:
    return {
        "articles": _to_int(d.get("articles"), 0),
        "risk": _to_float(d.get("risk"), 0.0),
        "positive": _to_float(d.get("positive"), 0.0),
        "uncertainty": _to_float(d.get("uncertainty"), 0.0),
    }


def _extract_from_items(items: List[Any]) -> Optional[Dict[str, Any]]:
    # Accept only dict items
    rows = [x for x in items if isinstance(x, dict)]
    if not rows:
        return None

    # Some datasets store per-article under "sentiment" inside each row
    def pick_val(r: dict, name: str) -> Any:
        if name in r:
            return r.get(name)
        s = r.get("sentiment")
        if isinstance(s, dict) and name in s:
            return s.get(name)
        return None

    risks: List[float] = []
    poss: List[float] = []
    uncs: List[float] = []

    for r in rows:
        rv = pick_val(r, "risk")
        pv = pick_val(r, "positive")
        uv = pick_val(r, "uncertainty")

        # Fallback: if only net exists, derive risk/positive
        if rv is None and pv is None:
            net = pick_val(r, "net")
            if net is not None:
                netf = _to_float(net, None)  # type: ignore[arg-type]
                if netf is not None:
                    rv = max(0.0, -netf)
                    pv = max(0.0, netf)

        if rv is not None:
            risks.append(_to_float(rv, 0.0))
        if pv is not None:
            poss.append(_to_float(pv, 0.0))
        if uv is not None:
            uncs.append(_to_float(uv, 0.0))

    if not (risks or poss or uncs):
        return None

    def mean(xs: List[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "articles": len(rows),
        "risk": mean(risks),
        "positive": mean(poss),
        "uncertainty": mean(uncs),
    }


def extract_summary(obj: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(obj, dict):
        return None

    # 1) Summary dict
    sd = _pick_summary_dict(obj)
    if isinstance(sd, dict) and any(k in sd for k in ("articles", "risk", "positive", "uncertainty")):
        return _extract_from_summary_dict(sd)

    # 2) Top-level summary
    if any(k in obj for k in ("articles", "risk", "positive", "uncertainty")):
        return _extract_from_summary_dict(obj)

    # 3) Aggregate from items list
    items = _find_item_list(obj)
    if items:
        return _extract_from_items(items)

    return None


def main() -> int:
    if not ANALYSIS.exists():
        print(f"[FATAL] analysis dir not found: {ANALYSIS}")
        return 2

    rows_out = []
    seen = 0
    used = 0
    skipped = 0

    for p in sorted(ANALYSIS.glob("sentiment_*.json")):
        m = PAT.match(p.name)
        if not m:
            continue

        date = m.group(1)
        seen += 1

        try:
            raw = p.read_text(encoding="utf-8")
            obj = json.loads(raw)
        except Exception:
            skipped += 1
            continue

        s = extract_summary(obj)
        if s is None:
            skipped += 1
            continue

        rows_out.append(
            {
                "date": date,
                "articles": int(s["articles"]),
                "risk": f"{float(s['risk']):.6f}",
                "positive": f"{float(s['positive']):.6f}",
                "uncertainty": f"{float(s['uncertainty']):.6f}",
            }
        )
        used += 1

    rows_out.sort(key=lambda r: r["date"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["date", "articles", "risk", "positive", "uncertainty"]
        )
        w.writeheader()
        w.writerows(rows_out)

    print(f"[OK] rebuilt sentiment_timeseries.csv: {OUT}")
    print(f"[OK] files seen={seen} used={used} skipped={skipped}")
    if rows_out:
        print(f"[OK] range: {rows_out[0]['date']} .. {rows_out[-1]['date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

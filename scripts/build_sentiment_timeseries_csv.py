# scripts/build_sentiment_timeseries_csv.py
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


SENT_LATEST = Path("data/world_politics/analysis/sentiment_latest.json")
OUT_CSV = Path("data/world_politics/analysis/sentiment_timeseries.csv")


def _num(v: Any, default: float = 0.0) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except Exception:
            return float(default)
    return float(default)


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _read_existing(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        return []
    rows: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if row.get("date"):
                rows.append(row)
    return rows


def _write(csv_path: Path, rows: List[Dict[str, str]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["date", "articles", "risk", "positive", "uncertainty"]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    date = args.date

    if not SENT_LATEST.exists():
        raise SystemExit(f"[ERR] missing sentiment_latest: {SENT_LATEST}")

    sent = _load_json(SENT_LATEST)
    today = sent.get("today", {})
    if not isinstance(today, dict):
        today = {}

    # Prefer canonical keys; fallback to *Score aliases
    articles = today.get("articles", 0)
    try:
        articles_i = int(articles)
    except Exception:
        articles_i = 0

    risk = today.get("risk", today.get("riskScore", 0.0))
    pos = today.get("positive", today.get("posScore", 0.0))
    unc = today.get("uncertainty", today.get("uncScore", 0.0))

    new_row = {
        "date": date,
        "articles": str(articles_i),
        "risk": f"{_num(risk, 0.0):.6f}",
        "positive": f"{_num(pos, 0.0):.6f}",
        "uncertainty": f"{_num(unc, 0.0):.6f}",
    }

    rows = _read_existing(OUT_CSV)

    # replace or append
    by_date = {r["date"]: r for r in rows if "date" in r}
    by_date[date] = new_row

    merged = list(by_date.values())
    merged.sort(key=lambda r: r["date"])

    _write(OUT_CSV, merged)

    if not args.quiet:
        print(f"[OK] wrote: {OUT_CSV}")
        print(f"  row: {new_row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

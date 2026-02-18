# scripts/rebuild_sentiment_timeseries_csv.py
# Rebuild sentiment_timeseries.csv from analysis/sentiment_YYYY-MM-DD.json files.
#
# Why:
# - sentiment_timeseries.csv can become short/flat if generated from sentiment_latest only,
#   or if the builder stops appending correctly.
# - This script is a safe "one-shot repair" that does NOT touch sentiment generation.
#
# Output:
#   data/world_politics/analysis/sentiment_timeseries.csv
# Columns (avg per article, same scale as sentiment_latest.json top-level):
#   date,articles,risk,positive,uncertainty
#
# Run:
#   .\.venv\Scripts\python.exe scripts\rebuild_sentiment_timeseries_csv.py
#   (optional) --out <path> --include-missing-days
#
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "world_politics" / "analysis"
DEFAULT_OUT = ANALYSIS / "sentiment_timeseries.csv"

RE_DATED = re.compile(r"^sentiment_(\d{4}-\d{2}-\d{2})\.json$")


@dataclass(frozen=True)
class Row:
    d: str
    articles: int
    risk: float
    positive: float
    uncertainty: float


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _to_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return obj


def _extract_summary(obj: Dict[str, Any]) -> Tuple[int, float, float, float]:
    """
    Prefer top-level summary if present:
      articles, risk, positive, uncertainty
    Fallback: compute averages from items if needed.
    """
    # (A) Top-level fields (most common after normalize)
    articles = _to_int(obj.get("articles"), default=-1)
    risk = obj.get("risk")
    positive = obj.get("positive")
    uncertainty = obj.get("uncertainty")

    if articles >= 0 and risk is not None and positive is not None and uncertainty is not None:
        return (
            articles,
            _to_float(risk, 0.0),
            _to_float(positive, 0.0),
            _to_float(uncertainty, 0.0),
        )

    # (B) Fallback: derive from items
    items = obj.get("items", [])
    if not isinstance(items, list):
        items = []

    n = len(items)
    if n == 0:
        return (0, 0.0, 0.0, 0.0)

    # try multiple key variants
    def pick(it: Dict[str, Any], *keys: str) -> Optional[float]:
        for k in keys:
            if k in it:
                v = it.get(k)
                try:
                    return float(v)
                except Exception:
                    continue
        # nested "sentiment" or "sent"
        for nest_key in ("sentiment", "sent"):
            nest = it.get(nest_key)
            if isinstance(nest, dict):
                for k in keys:
                    if k in nest:
                        v = nest.get(k)
                        try:
                            return float(v)
                        except Exception:
                            continue
        return None

    sum_r = 0.0
    sum_p = 0.0
    sum_u = 0.0
    for it in items:
        if not isinstance(it, dict):
            continue
        r = pick(it, "risk", "risk_score", "riskScore", "risk_score_avg")
        p = pick(it, "positive", "pos", "pos_score", "posScore", "positive_score", "positiveScore")
        u = pick(it, "uncertainty", "unc", "unc_score", "uncScore", "uncertainty_score", "uncertaintyScore")

        sum_r += (r if r is not None else 0.0)
        sum_p += (p if p is not None else 0.0)
        sum_u += (u if u is not None else 0.0)

    # convert to per-article averages (same as normalized top-level convention)
    return (n, sum_r / n, sum_p / n, sum_u / n)


def _list_dated_sentiments() -> List[Tuple[str, Path]]:
    out: List[Tuple[str, Path]] = []
    for p in ANALYSIS.glob("sentiment_*.json"):
        m = RE_DATED.match(p.name)
        if not m:
            continue
        ds = m.group(1)
        out.append((ds, p))
    out.sort(key=lambda t: t[0])
    return out


def _daterange(d0: date, d1: date) -> List[str]:
    cur = d0
    res: List[str] = []
    while cur <= d1:
        res.append(cur.isoformat())
        cur += timedelta(days=1)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output CSV path")
    ap.add_argument(
        "--include-missing-days",
        action="store_true",
        help="Fill missing dates between min/max with zeros (articles=0).",
    )
    args = ap.parse_args()

    pairs = _list_dated_sentiments()
    if not pairs:
        raise SystemExit(f"[ERR] no dated sentiments found under: {ANALYSIS} (sentiment_YYYY-MM-DD.json)")

    rows_by_date: Dict[str, Row] = {}
    for ds, path in pairs:
        try:
            obj = _read_json(path)
            articles, risk, positive, uncertainty = _extract_summary(obj)
            rows_by_date[ds] = Row(ds, articles, risk, positive, uncertainty)
        except Exception as e:
            print(f"[WARN] skip {path.name}: {e}")

    if not rows_by_date:
        raise SystemExit("[ERR] could not extract any rows from dated sentiments")

    dates = sorted(rows_by_date.keys())
    if args.include_missing_days:
        d0 = date.fromisoformat(dates[0])
        d1 = date.fromisoformat(dates[-1])
        dates = _daterange(d0, d1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "articles", "risk", "positive", "uncertainty"])
        for ds in dates:
            r = rows_by_date.get(ds)
            if r is None:
                w.writerow([ds, 0, 0.0, 0.0, 0.0])
            else:
                w.writerow([r.d, r.articles, f"{r.risk:.6f}", f"{r.positive:.6f}", f"{r.uncertainty:.6f}"])

    print("[OK] rebuilt sentiment_timeseries.csv")
    print(f"  out: {out_path}")
    print(f"  rows: {sum(1 for _ in dates)} (dated_files={len(rows_by_date)})")


if __name__ == "__main__":
    main()

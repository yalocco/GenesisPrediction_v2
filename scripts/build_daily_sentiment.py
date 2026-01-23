#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_daily_sentiment.py

GenesisPrediction v2 - Sentiment Builder (Spec v1)

- News/events を辞書ベースでスコア化（risk / positive / uncertainty）
- 日次の詳細JSONと、GUI用の時系列CSVを生成

Outputs:
  data/world_politics/analysis/sentiment_YYYY-MM-DD.json
  data/world_politics/analysis/sentiment_timeseries.csv

Usage:
  python scripts/build_daily_sentiment.py --date 2026-01-23
  python scripts/build_daily_sentiment.py --date 2026-01-23 --input path/to/file
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ----------------------------
# Keyword sets (Spec v1)
# ----------------------------

RISK_WORDS = {
    "war", "attack", "missile", "strike", "bomb", "explosion", "terror", "terrorist",
    "sanction", "sanctions", "crisis", "conflict", "clash", "invasion", "incursion",
    "recession", "collapse", "default", "bankrupt", "bankruptcy", "inflation",
    "riot", "coup", "assassination", "hostage", "killed", "dead", "casualties",
    "nuclear", "threat", "emergency", "outbreak", "pandemic",
}

POSITIVE_WORDS = {
    "agreement", "deal", "recovery", "growth", "cooperation", "stabilize", "stabilized",
    "peace", "ceasefire", "truce", "aid", "support", "improve", "improved", "improving",
    "rebound", "success", "progress", "breakthrough", "rescue",
}

UNCERTAINTY_WORDS = {
    "may", "might", "could", "unclear", "uncertain", "likely", "unlikely", "possible",
    "possibility", "reportedly", "allegedly", "rumor", "rumour", "suspected",
    "expected", "estimate", "estimated",
}

TOKEN_RE = re.compile(r"[A-Za-z]+")


@dataclass
class ArticleScore:
    idx: int
    source: str
    title: str
    text_len: int
    token_count: int
    risk_hits: int
    positive_hits: int
    uncertainty_hits: int
    risk_score: float
    positive_score: float
    uncertainty_score: float


# ----------------------------
# Helpers
# ----------------------------

def iso_date(s: str) -> str:
    # Accept YYYY-MM-DD
    dt = datetime.strptime(s, "%Y-%m-%d")
    return dt.strftime("%Y-%m-%d")


def tokenize(text: str) -> List[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text or "")]


def safe_mean(xs: List[float]) -> float:
    return float(sum(xs) / len(xs)) if xs else 0.0


def safe_std(xs: List[float]) -> float:
    if len(xs) < 2:
        return 0.0
    return float(statistics.pstdev(xs))


def percentile(xs: List[float], p: float) -> float:
    if not xs:
        return 0.0
    xs2 = sorted(xs)
    if p <= 0:
        return float(xs2[0])
    if p >= 100:
        return float(xs2[-1])
    k = (len(xs2) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(xs2[int(k)])
    d0 = xs2[f] * (c - k)
    d1 = xs2[c] * (k - f)
    return float(d0 + d1)


def find_default_input(date: str) -> Path:
    """
    Try to auto-detect available input files for the date.
    Priority: daily_news JSON > events JSONL > other JSON candidates.
    """
    candidates = [
        # Common patterns (adjustable)
        Path(f"data/world_politics/analysis/daily_news_{date}.json"),
        Path(f"data/world_politics/daily_news_{date}.json"),
        Path(f"data/world_politics/analysis/events_{date}.jsonl"),
        Path(f"data/world_politics/events_{date}.jsonl"),
        # Sometimes analysis might store jsonl digest of items
        Path(f"data/world_politics/analysis/daily_news_{date}.jsonl"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "No input file found for the date. Tried:\n  - "
        + "\n  - ".join(str(x) for x in candidates)
        + "\nHint: pass --input <path> explicitly."
    )


def load_items(path: Path) -> List[Dict[str, Any]]:
    """
    Load items from:
      - JSON array
      - JSON object with a list field (articles/items/events)
      - JSONL (one JSON per line)
    Returns: list[dict]
    """
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        items: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))
        return items

    if suffix == ".json":
        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)]
        if isinstance(obj, dict):
            for k in ("articles", "items", "events", "data"):
                v = obj.get(k)
                if isinstance(v, list):
                    return [x for x in v if isinstance(x, dict)]
            # If it's a single item dict, wrap it
            return [obj]
        return []

    raise ValueError(f"Unsupported input type: {path}")


def pick_text_fields(item: Dict[str, Any]) -> Tuple[str, str]:
    """
    Return (title, body) best-effort from typical keys.
    """
    title = (
        item.get("title")
        or item.get("headline")
        or item.get("name")
        or ""
    )
    body = (
        item.get("content")
        or item.get("summary")
        or item.get("description")
        or item.get("text")
        or ""
    )
    return str(title), str(body)


def pick_source(item: Dict[str, Any]) -> str:
    s = item.get("source") or item.get("publisher") or item.get("domain") or ""
    if isinstance(s, dict):
        return str(s.get("name") or s.get("id") or "")
    return str(s)


def score_item(i: int, item: Dict[str, Any]) -> ArticleScore:
    title, body = pick_text_fields(item)
    source = pick_source(item) or "unknown"
    text = f"{title}\n{body}".strip()
    tokens = tokenize(text)
    token_count = max(1, len(tokens))

    risk_hits = sum(1 for t in tokens if t in RISK_WORDS)
    positive_hits = sum(1 for t in tokens if t in POSITIVE_WORDS)
    uncertainty_hits = sum(1 for t in tokens if t in UNCERTAINTY_WORDS)

    risk_score = risk_hits / token_count
    positive_score = positive_hits / token_count
    uncertainty_score = uncertainty_hits / token_count

    return ArticleScore(
        idx=i,
        source=source,
        title=title[:240],
        text_len=len(text),
        token_count=token_count,
        risk_hits=risk_hits,
        positive_hits=positive_hits,
        uncertainty_hits=uncertainty_hits,
        risk_score=float(risk_score),
        positive_score=float(positive_score),
        uncertainty_score=float(uncertainty_score),
    )


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_daily_json(out_path: Path, payload: Dict[str, Any]) -> None:
    ensure_parent(out_path)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_timeseries_row(csv_path: Path, row: Dict[str, Any]) -> None:
    """
    Upsert by 'date' column.
    """
    ensure_parent(csv_path)

    fieldnames = ["date", "risk", "positive", "uncertainty", "articles"]
    rows: List[Dict[str, str]] = []

    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            # Accept older/extra columns but preserve only known ones
            for r in reader:
                if not r:
                    continue
                rows.append({
                    "date": r.get("date", "").strip(),
                    "risk": r.get("risk", "").strip(),
                    "positive": r.get("positive", "").strip(),
                    "uncertainty": r.get("uncertainty", "").strip(),
                    "articles": r.get("articles", "").strip(),
                })

    # Remove existing same date
    rows = [r for r in rows if r.get("date") != row["date"]]

    # Append new row
    rows.append({
        "date": str(row["date"]),
        "risk": f"{row['risk']:.8f}",
        "positive": f"{row['positive']:.8f}",
        "uncertainty": f"{row['uncertainty']:.8f}",
        "articles": str(int(row["articles"])),
    })

    # Sort by date
    rows.sort(key=lambda r: r.get("date", ""))

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--input", default="", help="Optional explicit input file path (json/jsonl)")
    ap.add_argument("--max_items", type=int, default=0, help="Optional limit for scoring (0 = no limit)")
    args = ap.parse_args()

    date = iso_date(args.date)

    in_path = Path(args.input) if args.input else find_default_input(date)
    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {in_path}")

    items = load_items(in_path)
    if args.max_items and args.max_items > 0:
        items = items[: args.max_items]

    scores: List[ArticleScore] = []
    for i, it in enumerate(items):
        try:
            scores.append(score_item(i, it))
        except Exception:
            # Skip malformed items safely
            continue

    risk_vals = [s.risk_score for s in scores]
    pos_vals = [s.positive_score for s in scores]
    unc_vals = [s.uncertainty_score for s in scores]

    daily = {
        "risk": {
            "mean": safe_mean(risk_vals),
            "std": safe_std(risk_vals),
            "p90": percentile(risk_vals, 90),
            "p99": percentile(risk_vals, 99),
        },
        "positive": {
            "mean": safe_mean(pos_vals),
            "std": safe_std(pos_vals),
            "p90": percentile(pos_vals, 90),
            "p99": percentile(pos_vals, 99),
        },
        "uncertainty": {
            "mean": safe_mean(unc_vals),
            "std": safe_std(unc_vals),
            "p90": percentile(unc_vals, 90),
            "p99": percentile(unc_vals, 99),
        },
    }

    out_json = Path(f"data/world_politics/analysis/sentiment_{date}.json")
    out_csv = Path("data/world_politics/analysis/sentiment_timeseries.csv")

    payload: Dict[str, Any] = {
        "version": "sentiment_spec_v1",
        "date": date,
        "input_path": str(in_path).replace("\\", "/"),
        "articles": len(scores),
        "keywords": {
            "risk": sorted(RISK_WORDS),
            "positive": sorted(POSITIVE_WORDS),
            "uncertainty": sorted(UNCERTAINTY_WORDS),
        },
        "daily": daily,
        "items": [
            {
                "idx": s.idx,
                "source": s.source,
                "title": s.title,
                "token_count": s.token_count,
                "risk_hits": s.risk_hits,
                "positive_hits": s.positive_hits,
                "uncertainty_hits": s.uncertainty_hits,
                "risk_score": s.risk_score,
                "positive_score": s.positive_score,
                "uncertainty_score": s.uncertainty_score,
            }
            for s in scores
        ],
    }

    write_daily_json(out_json, payload)

    upsert_timeseries_row(
        out_csv,
        {
            "date": date,
            "risk": daily["risk"]["mean"],
            "positive": daily["positive"]["mean"],
            "uncertainty": daily["uncertainty"]["mean"],
            "articles": len(scores),
        },
    )

    print(f"[OK] input: {in_path}")
    print(f"[OK] wrote: {out_json}")
    print(f"[OK] upsert: {out_csv}")
    print(
        f"[SUM] {date} articles={len(scores)} "
        f"risk={daily['risk']['mean']:.6f} "
        f"pos={daily['positive']['mean']:.6f} "
        f"unc={daily['uncertainty']['mean']:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

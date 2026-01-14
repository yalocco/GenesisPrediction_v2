#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build weak anchor candidate list from the last N days of daily_summary_*.json.

Reads:
- data/world_politics/analysis/daily_summary_YYYY-MM-DD.json

Uses:
- anchors_quality.items[*].score and tags (if present)

Writes:
- data/world_politics/analysis/weak_anchor_candidates_14d.csv
- data/world_politics/analysis/weak_anchor_candidates_14d.json

Safe:
- Does not modify any JSON inputs.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_date_from_name(name: str) -> str:
    # daily_summary_YYYY-MM-DD.json
    prefix = "daily_summary_"
    suffix = ".json"
    if name.startswith(prefix) and name.endswith(suffix):
        return name[len(prefix) : -len(suffix)]
    return ""


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def is_entity_like(tags: List[str]) -> bool:
    # we used "entity_like" as a light positive tag
    return "entity_like" in tags


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/world_politics/analysis", help="analysis dir")
    ap.add_argument("--days", type=int, default=14, help="lookback days by file date")
    ap.add_argument("--score_th", type=float, default=0.45, help="score threshold for weakness")
    ap.add_argument("--min_days", type=int, default=3, help="must appear in >= this many days")
    ap.add_argument("--out_prefix", default="weak_anchor_candidates_14d", help="output file prefix (no ext)")
    args = ap.parse_args()

    base = Path(args.dir)
    files = []
    for p in base.glob("daily_summary_*.json"):
        d = extract_date_from_name(p.name)
        if not d:
            continue
        files.append((parse_date(d), p))
    files.sort(key=lambda x: x[0])

    if not files:
        print("[ERR] no daily_summary_*.json found")
        return 2

    # take last N distinct days
    tail = files[-args.days :]
    used_days = [dt.strftime("%Y-%m-%d") for dt, _ in tail]

    # stats by token
    tok_days = defaultdict(set)          # token -> set(days)
    tok_scores = defaultdict(list)       # token -> list(scores)
    tok_tags = defaultdict(set)          # token -> set(tags)
    tok_total = defaultdict(int)         # token -> total occurrences across days

    for dt, p in tail:
        day = dt.strftime("%Y-%m-%d")
        doc = load_json(p)

        aq = doc.get("anchors_quality") or {}
        if not isinstance(aq, dict):
            continue
        items = aq.get("items") or []
        if not isinstance(items, list):
            continue

        for it in items:
            if not isinstance(it, dict):
                continue
            tok = str(it.get("token", "")).strip()
            if not tok:
                continue
            score = it.get("score", None)
            try:
                score_f = float(score)
            except Exception:
                continue

            tags = it.get("tags") or []
            if not isinstance(tags, list):
                tags = []

            tok_total[tok] += 1
            tok_days[tok].add(day)
            tok_scores[tok].append(score_f)
            for t in tags:
                tok_tags[tok].add(str(t))

    # build candidates
    candidates = []
    for tok, days_set in tok_days.items():
        days_n = len(days_set)
        if days_n < args.min_days:
            continue

        scores = tok_scores.get(tok, [])
        if not scores:
            continue
        avg = sum(scores) / len(scores)

        tags = sorted(tok_tags.get(tok, set()))
        # if it is consistently entity-like, do not propose it
        if is_entity_like(tags) and avg >= args.score_th:
            continue

        # weakness criteria: avg low OR often low
        low_rate = sum(1 for s in scores if s < args.score_th) / max(1, len(scores))
        if not (avg < args.score_th or low_rate >= 0.6):
            continue

        candidates.append(
            {
                "token": tok,
                "avg_score": round(avg, 4),
                "low_rate": round(low_rate, 4),
                "days_n": days_n,
                "total_n": tok_total.get(tok, 0),
                "tags": tags,
                "days": sorted(list(days_set)),
            }
        )

    # sort: most suspicious first
    candidates.sort(key=lambda x: (x["avg_score"], -x["days_n"], -x["total_n"], x["token"]))

    out_json = base / f"{args.out_prefix}.json"
    out_csv = base / f"{args.out_prefix}.csv"

    out_json.write_text(
        json.dumps(
            {
                "lookback_days": args.days,
                "used_days": used_days,
                "score_th": args.score_th,
                "min_days": args.min_days,
                "candidates": candidates,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["token", "avg_score", "low_rate", "days_n", "total_n", "tags"])
        w.writeheader()
        for c in candidates:
            w.writerow(
                {
                    "token": c["token"],
                    "avg_score": c["avg_score"],
                    "low_rate": c["low_rate"],
                    "days_n": c["days_n"],
                    "total_n": c["total_n"],
                    "tags": "|".join(c["tags"]),
                }
            )

    print(f"[DONE] candidates={len(candidates)} -> {out_csv.as_posix()} / {out_json.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

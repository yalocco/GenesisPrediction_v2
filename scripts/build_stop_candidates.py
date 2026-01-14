#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build STOP-word candidates from anchors_quality over last N days.

Reads:
- data/world_politics/analysis/daily_summary_YYYY-MM-DD.json

Writes (generated artifacts; do NOT commit):
- data/world_politics/analysis/stop_candidates_14d.txt
- data/world_politics/analysis/stop_candidates_14d.json

Safe:
- does not modify input JSON
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/world_politics/analysis", help="analysis dir")
    ap.add_argument("--days", type=int, default=14, help="lookback days by file date")
    ap.add_argument("--score_th", type=float, default=0.45, help="score threshold treated as weak")
    ap.add_argument("--min_days", type=int, default=3, help="must appear in >= this many distinct days")
    ap.add_argument("--min_low_rate", type=float, default=0.6, help="weak score rate threshold")
    ap.add_argument("--max_avg_score", type=float, default=0.55, help="avg score must be <= this to be candidate")
    ap.add_argument("--out_prefix", default="stop_candidates_14d", help="output file prefix (no ext)")
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

    tail = files[-args.days :]
    used_days = [dt.strftime("%Y-%m-%d") for dt, _ in tail]

    tok_days = defaultdict(set)     # token -> set(days)
    tok_scores = defaultdict(list)  # token -> list(scores)
    tok_tags = defaultdict(set)     # token -> set(tags)
    tok_total = defaultdict(int)    # token -> total occurrences

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

            # keep original case in output but compute with raw token string
            try:
                score = float(it.get("score"))
            except Exception:
                continue

            tags = it.get("tags") or []
            if not isinstance(tags, list):
                tags = []

            tok_total[tok] += 1
            tok_days[tok].add(day)
            tok_scores[tok].append(score)
            for t in tags:
                tok_tags[tok].add(str(t))

    candidates = []
    for tok, days_set in tok_days.items():
        days_n = len(days_set)
        if days_n < args.min_days:
            continue

        scores = tok_scores.get(tok, [])
        if not scores:
            continue

        avg = sum(scores) / len(scores)
        low_rate = sum(1 for s in scores if s < args.score_th) / max(1, len(scores))
        tags = sorted(tok_tags.get(tok, set()))

        # entity-likeは除外寄り（ただし avg が明確に低いなら候補に残す）
        entity_like = "entity_like" in tags

        # 基本条件：平均が低い + 低スコア率が高い
        # ただし entity_like の場合はより厳しくする（実体を誤ってSTOPにしない）
        max_avg = args.max_avg_score if not entity_like else min(args.max_avg_score, 0.45)
        min_low = args.min_low_rate if not entity_like else max(args.min_low_rate, 0.8)

        if not (avg <= max_avg and low_rate >= min_low):
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
    candidates.sort(key=lambda x: (x["avg_score"], -x["low_rate"], -x["days_n"], -x["total_n"], x["token"].lower()))

    out_json = base / f"{args.out_prefix}.json"
    out_txt = base / f"{args.out_prefix}.txt"

    out_json.write_text(
        json.dumps(
            {
                "lookback_days": args.days,
                "used_days": used_days,
                "score_th": args.score_th,
                "min_days": args.min_days,
                "min_low_rate": args.min_low_rate,
                "max_avg_score": args.max_avg_score,
                "candidates": candidates,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # txt: one token per line (lowercased for STOP usage)
    lines = [c["token"].strip().lower() for c in candidates if c.get("token")]
    out_txt.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    print(f"[DONE] stop_candidates={len(candidates)} -> {out_txt.as_posix()} / {out_json.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

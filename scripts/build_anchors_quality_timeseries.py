#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Build timeseries CSV from daily_summary_*.json:
- date, overall_score, flag, anchors_n, weak_n
Safe: reads JSON only, writes CSV only (does not modify JSON).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/world_politics/analysis", help="analysis dir")
    ap.add_argument("--out", default="data/world_politics/analysis/anchors_quality_timeseries.csv", help="output CSV")
    args = ap.parse_args()

    base = Path(args.dir)
    out = Path(args.out)

    files = sorted(base.glob("daily_summary_*.json"))
    rows: List[Dict[str, Any]] = []

    for p in files:
        date = extract_date_from_name(p.name)
        if not date:
            continue

        doc = load_json(p)

        anchors = doc.get("anchors") or []
        if not isinstance(anchors, list):
            anchors = []

        aq = doc.get("anchors_quality") or {}
        if not isinstance(aq, dict):
            aq = {}

        overall = aq.get("overall_score", "")
        flag = aq.get("flag", "")
        weak_tokens = aq.get("weak_tokens") or []
        if not isinstance(weak_tokens, list):
            weak_tokens = []

        rows.append(
            {
                "date": date,
                "overall_score": overall,
                "flag": flag,
                "anchors_n": len(anchors),
                "weak_n": len(weak_tokens),
            }
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "overall_score", "flag", "anchors_n", "weak_n"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"[DONE] wrote {len(rows)} rows -> {out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

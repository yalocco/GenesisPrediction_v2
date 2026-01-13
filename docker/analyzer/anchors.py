#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Clean weak/generic tokens from daily_summary_YYYY-MM-DD.json anchors.

Usage (PowerShell, repo root):
  .\.venv\Scripts\python.exe scripts\clean_daily_summary_anchors.py
  .\.venv\Scripts\python.exe scripts\clean_daily_summary_anchors.py data/world_politics/analysis/daily_summary_2026-01-09.json
  .\.venv\Scripts\python.exe scripts\clean_daily_summary_anchors.py --all
  .\.venv\Scripts\python.exe scripts\clean_daily_summary_anchors.py --words would plan door back politics

Options:
  --all       : clean all daily_summary_*.json under data/world_politics/analysis/
  --dry-run   : show what would change without writing
  --words ... : override removal list (space-separated)
"""

import argparse
import json
from pathlib import Path

DEFAULT_REMOVE = {
    # weak / auxiliary / meta
    "would", "plan", "door", "back",
    # add more if you want:
    # "politics", "global", "view",
}

DS_GLOB = "daily_summary_*.json"


def _load_json(p):
    return json.loads(p.read_text(encoding="utf-8"))


def _dump_json(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _clean_list(xs, remove_set):
    if not isinstance(xs, list):
        return xs, []
    removed = []
    out = []
    for x in xs:
        if isinstance(x, str) and x.strip().lower() in remove_set:
            removed.append(x)
            continue
        out.append(x)
    return out, removed


def clean_daily_summary_obj(ds, remove_set):
    removed_all = []

    ds["anchors"], rem = _clean_list(ds.get("anchors"), remove_set)
    removed_all += rem

    ad = ds.get("anchors_detail")
    if isinstance(ad, dict):
        for k in ("top_tokens", "hints", "top_domains"):
            if k in ad:
                ad[k], rem = _clean_list(ad.get(k), remove_set)
                removed_all += [f"{k}:{x}" for x in rem]
        ds["anchors_detail"] = ad

    return ds, removed_all


def pick_latest_daily_summary(analysis_dir):
    candidates = sorted(analysis_dir.glob(DS_GLOB))
    return candidates[-1] if candidates else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=None, help="path to daily_summary_YYYY-MM-DD.json (optional)")
    ap.add_argument("--all", action="store_true", help="clean all daily_summary_*.json under analysis dir")
    ap.add_argument("--dry-run", action="store_true", help="do not write files")
    ap.add_argument("--words", nargs="*", default=None, help="override removal words list")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    analysis_dir = repo_root / "data" / "world_politics" / "analysis"

    remove_set = set((w or "").strip().lower() for w in (args.words or DEFAULT_REMOVE))
    remove_set.discard("")

    targets = []
    if args.all:
        targets = sorted(analysis_dir.glob(DS_GLOB))
    elif args.path:
        p = Path(args.path)
        targets = [(repo_root / p).resolve() if not p.is_absolute() else p.resolve()]
    else:
        latest = pick_latest_daily_summary(analysis_dir)
        if latest:
            targets = [latest]

    if not targets:
        print(f"[NG] daily_summary not found. looked under: {analysis_dir}")
        return 2

    total_removed = 0
    for p in targets:
        if not p.exists():
            print(f"[SKIP] not found: {p}")
            continue

        ds = _load_json(p)
        before = list(ds.get("anchors") or []) if isinstance(ds.get("anchors"), list) else None
        ds2, removed = clean_daily_summary_obj(ds, remove_set)
        after = list(ds2.get("anchors") or []) if isinstance(ds2.get("anchors"), list) else None

        if before is not None and after is not None and before == after:
            print(f"[OK] {p.name}: no change")
            continue

        total_removed += len(removed)
        print(f"[CHG] {p.name}")
        if before is not None:
            print("  anchors(before):", before)
            print("  anchors(after) :", after)
        if removed:
            print("  removed:", removed)

        if not args.dry_run:
            bak = p.with_suffix(p.suffix + ".bak")
            if not bak.exists():
                bak.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
            _dump_json(p, ds2)

    print(f"[DONE] removed items: {total_removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

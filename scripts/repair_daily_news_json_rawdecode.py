#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repair_daily_news_json_rawdecode.py

Fix corrupted daily news JSON where extra bytes/data were appended after a valid JSON object.
Strategy:
  - Read file as text
  - Use json.JSONDecoder().raw_decode to parse the first JSON object from the beginning
  - If trailing data exists, rewrite the file with the parsed object only
  - Always create a .bak backup (only once) before rewriting

Usage:
  python scripts/repair_daily_news_json_rawdecode.py data/world_politics/2026-02-25.json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any


def read_text_best_effort(path: Path) -> str:
    # Try common encodings; the fetched raw should usually be utf-8
    encodings = ["utf-8", "utf-8-sig", "cp932"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Could not read text: {path} (last_err={last_err})")


def is_expected_shape(obj: Any) -> bool:
    # Soft validation (don’t be too strict)
    if not isinstance(obj, dict):
        return False
    if "articles" not in obj:
        return False
    if not isinstance(obj.get("articles"), list):
        return False
    # optional keys: fetched_at, query, totalResults
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to daily raw JSON file (e.g., data/world_politics/YYYY-MM-DD.json)")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"[ERR] missing: {p}")
        return 1

    raw = read_text_best_effort(p)

    dec = json.JSONDecoder()
    try:
        obj, end = dec.raw_decode(raw)
    except json.JSONDecodeError as e:
        print(f"[ERR] raw_decode failed: {p}")
        print(f"      {e}")
        return 1

    if not is_expected_shape(obj):
        print(f"[ERR] parsed JSON does not look like daily news payload: {p}")
        print(f"      keys={list(obj.keys()) if isinstance(obj, dict) else type(obj)}")
        return 1

    trailing_len = len(raw) - end
    if trailing_len <= 0:
        # It parses cleanly from beginning; still might have whitespace only at tail
        try:
            json.loads(raw)
            print(f"[OK] already valid JSON (no repair needed): {p}")
            return 0
        except json.JSONDecodeError:
            # There is trailing non-whitespace or some other weirdness; proceed to rewrite first object
            pass

    bak = p.with_suffix(p.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(p, bak)
        print(f"[OK] backup created: {bak}")
    else:
        print(f"[WARN] backup exists (kept): {bak}")

    # Rewrite with pretty JSON (stable, readable)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, p)

    # Verify
    try:
        json.load(p.open("r", encoding="utf-8"))
    except Exception as e:
        print(f"[ERR] wrote repaired file but JSON still invalid: {p}")
        print(f"      {e}")
        return 1

    print(f"[OK] repaired by raw_decode: {p}")
    print(f"     parsed_end={end} trailing_bytes={trailing_len}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
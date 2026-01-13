#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Clean weak/generic tokens from daily_summary_YYYY-MM-DD.json:
- anchors
- anchors_detail.top_tokens
- anchors_detail.hints
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ここに「確実に落としたい弱語」を追加していく（小文字で）
BAD_ANCHORS = {
    "would",
    "plan",
    "door",
    "back",
    "might",
    "must",
    "here",
    "next",
    "start",
    # 必要なら追加:
    # "could", "should", "may", "will", "can",
}

def _is_bad(x: Any) -> bool:
    return isinstance(x, str) and x.strip().lower() in BAD_ANCHORS

def _filter_list_str(xs: Any) -> Any:
    if not isinstance(xs, list):
        return xs
    out = []
    for v in xs:
        if _is_bad(v):
            continue
        out.append(v)
    return out

def clean_one_file(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False

    changed = False

    # anchors
    if isinstance(data.get("anchors"), list):
        new_anchors = _filter_list_str(data["anchors"])
        if new_anchors != data["anchors"]:
            data["anchors"] = new_anchors
            changed = True

    # anchors_detail
    if isinstance(data.get("anchors_detail"), dict):
        ad = data["anchors_detail"]

        if isinstance(ad.get("top_tokens"), list):
            new_top = _filter_list_str(ad["top_tokens"])
            if new_top != ad["top_tokens"]:
                ad["top_tokens"] = new_top
                changed = True

        if isinstance(ad.get("hints"), list):
            new_hints = _filter_list_str(ad["hints"])
            if new_hints != ad["hints"]:
                ad["hints"] = new_hints
                changed = True

    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return changed

def main() -> int:
    # ローカル実行を想定（D:\AI\Projects\GenesisPrediction_v2）
    # data/world_politics/analysis 配下の daily_summary_*.json を対象にする
    analysis_dir = Path("data") / "world_politics" / "analysis"
    if not analysis_dir.exists():
        print(f"[SKIP] not found: {analysis_dir}")
        return 0

    files = sorted(analysis_dir.glob("daily_summary_*.json"))
    if not files:
        print(f"[SKIP] no files: {analysis_dir / 'daily_summary_*.json'}")
        return 0

    cleaned = 0
    for p in files:
        if clean_one_file(p):
            cleaned += 1
            print(f"[CLEANED] {p.name}")

    print(f"[DONE] cleaned files: {cleaned}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_data_health.py
Generate a lightweight "Data Health" JSON for the GUI (read-only SST).

Output (default):
  data/world_politics/analysis/health_latest.json
  data/world_politics/analysis/health_<DATE>.json   (optional, if --write-dated)

GUI (Home) will auto-pick:
  /analysis/health_latest.json  (then falls back to other names)
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


JST = timezone(timedelta(hours=9))


@dataclass
class CheckSpec:
    name: str
    path: Path
    kind: str  # "json"|"html"|"png"|"csv"|"md"|"txt"|"other"
    required: bool = True


def iso_now_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S%z")


def iso_mtime_jst(p: Path) -> str:
    ts = p.stat().st_mtime
    dt = datetime.fromtimestamp(ts, JST)
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


def human_bytes(n: int) -> str:
    # small helper for detail string; keep simple
    units = ["B", "KB", "MB", "GB"]
    x = float(n)
    for u in units:
        if x < 1024.0 or u == units[-1]:
            return f"{x:.1f}{u}" if u != "B" else f"{int(x)}B"
        x /= 1024.0
    return f"{n}B"


def status_for_file(p: Path, required: bool) -> str:
    if not p.exists():
        return "NG" if required else "WARN"
    try:
        size = p.stat().st_size
    except Exception:
        return "WARN"
    if size <= 0:
        return "WARN"
    return "OK"


def make_detail(p: Path) -> str:
    if not p.exists():
        return "missing"
    try:
        st = p.stat()
        return f"size={human_bytes(st.st_size)} mtime={iso_mtime_jst(p)}"
    except Exception as e:
        return f"exists but stat failed: {e}"


def build_specs(analysis_dir: Path, date_str: str) -> List[CheckSpec]:
    """
    Keep this list conservative and stable.
    We check both "latest" and dated artifacts where it makes sense.
    """
    a = analysis_dir

    specs: List[CheckSpec] = [
        # Core summary/news (common in this repo)
        CheckSpec("daily_summary_latest", a / "daily_summary_latest.json", "json", required=False),
        CheckSpec("daily_news_latest", a / "daily_news_latest.json", "json", required=False),

        # Sentiment outputs (known from your pipeline)
        CheckSpec("sentiment_latest", a / "sentiment_latest.json", "json", required=True),
        CheckSpec("sentiment_timeseries", a / "sentiment_timeseries.csv", "csv", required=True),

        # FX overlays (known from your GUI integration)
        CheckSpec("jpy_thb_remittance_overlay", a / "jpy_thb_remittance_overlay.png", "png", required=False),
        CheckSpec(f"fx_overlay_{date_str}", a / f"fx_overlay_{date_str}.png", "png", required=False),

        # Observation (if present)
        CheckSpec("observation_latest_md", a / "observation_latest.md", "md", required=False),
        CheckSpec(f"observation_{date_str}_md", a / f"observation_{date_str}.md", "md", required=False),
        CheckSpec(f"observation_{date_str}_json", a / f"observation_{date_str}.json", "json", required=False),

        # Overlay HTML (if your GUI publishes it under analysis)
        CheckSpec(f"daily_news_{date_str}_html", a / f"daily_news_{date_str}.html", "html", required=False),
    ]

    return specs


def to_relposix(p: Path, base: Path) -> str:
    try:
        rel = p.relative_to(base)
        return rel.as_posix()
    except Exception:
        return p.as_posix()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--analysis-dir",
        default="data/world_politics/analysis",
        help="Analysis directory that the GUI serves as /analysis/ (default: data/world_politics/analysis)",
    )
    ap.add_argument(
        "--date",
        default=None,
        help="Date in YYYY-MM-DD. Default: today (JST).",
    )
    ap.add_argument(
        "--out-latest",
        default=None,
        help="Override latest output filename (default: <analysis-dir>/health_latest.json).",
    )
    ap.add_argument(
        "--write-dated",
        action="store_true",
        help="Also write dated file: <analysis-dir>/health_<DATE>.json",
    )
    args = ap.parse_args()

    analysis_dir = Path(args.analysis_dir)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    if args.date:
        date_str = args.date.strip()
    else:
        date_str = datetime.now(JST).strftime("%Y-%m-%d")

    out_latest = Path(args.out_latest) if args.out_latest else (analysis_dir / "health_latest.json")
    out_dated = analysis_dir / f"health_{date_str}.json"

    specs = build_specs(analysis_dir, date_str)

    checks: List[Dict[str, Any]] = []
    ok = warn = ng = 0

    for s in specs:
        st = status_for_file(s.path, s.required)
        if st == "OK":
            ok += 1
        elif st == "WARN":
            warn += 1
        else:
            ng += 1

        item: Dict[str, Any] = {
            "name": s.name,
            "status": st,
            "required": bool(s.required),
            "kind": s.kind,
            # Important: store path relative to analysis dir so it's easy to inspect
            "path": to_relposix(s.path, analysis_dir),
            "detail": make_detail(s.path),
        }

        if s.path.exists():
            try:
                item["bytes"] = int(s.path.stat().st_size)
                item["updated_at"] = iso_mtime_jst(s.path)
            except Exception:
                pass

        checks.append(item)

    payload: Dict[str, Any] = {
        "generated_at": iso_now_jst(),
        "date": date_str,
        "analysis_dir": analysis_dir.as_posix(),
        "summary": {
            "ok": ok,
            "warn": warn,
            "ng": ng,
            "total": len(checks),
        },
        "checks": checks,
    }

    # Write latest
    out_latest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Optionally write dated
    if args.write_dated:
        out_dated.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[OK] wrote health json")
    print(f"  latest: {out_latest}")
    if args.write_dated:
        print(f"  dated : {out_dated}")
    print(f"  counts: OK={ok} WARN={warn} NG={ng} total={len(checks)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

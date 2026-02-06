#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_data_health.py
Generate a lightweight "Data Health" JSON for the GUI (read-only SST).

Outputs (default):
  data/world_politics/analysis/health_latest.json
  data/world_politics/analysis/health_<DATE>.json   (optional, if --write-dated)

Adds freshness evaluation:
- exists/size checks
- age_seconds / age_hours
- freshness: OK/WARN/NG by thresholds (customizable)

GUI (Home) will pick:
  /analysis/health_latest.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List


JST = timezone(timedelta(hours=9))


@dataclass
class CheckSpec:
    name: str
    path: Path
    kind: str  # "json"|"html"|"png"|"csv"|"md"|"txt"|"other"
    required: bool = True


def iso_now_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S%z")


def dt_now_jst() -> datetime:
    return datetime.now(JST)


def iso_mtime_jst(p: Path) -> str:
    ts = p.stat().st_mtime
    dt = datetime.fromtimestamp(ts, JST)
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


def human_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    x = float(n)
    for u in units:
        if x < 1024.0 or u == units[-1]:
            return f"{x:.1f}{u}" if u != "B" else f"{int(x)}B"
        x /= 1024.0
    return f"{n}B"


def to_relposix(p: Path, base: Path) -> str:
    try:
        return p.relative_to(base).as_posix()
    except Exception:
        return p.as_posix()


def build_specs(analysis_dir: Path, date_str: str) -> List[CheckSpec]:
    a = analysis_dir
    return [
        # Core summary/news (optional depending on pipeline)
        CheckSpec("daily_summary_latest", a / "daily_summary_latest.json", "json", required=False),
        CheckSpec("daily_news_latest", a / "daily_news_latest.json", "json", required=False),

        # Sentiment outputs (known from your pipeline)
        CheckSpec("sentiment_latest", a / "sentiment_latest.json", "json", required=True),
        CheckSpec("sentiment_timeseries", a / "sentiment_timeseries.csv", "csv", required=True),

        # FX overlays (optional)
        CheckSpec("jpy_thb_remittance_overlay", a / "jpy_thb_remittance_overlay.png", "png", required=False),
        CheckSpec(f"fx_overlay_{date_str}", a / f"fx_overlay_{date_str}.png", "png", required=False),

        # Observation (optional)
        CheckSpec("observation_latest_md", a / "observation_latest.md", "md", required=False),
        CheckSpec(f"observation_{date_str}_md", a / f"observation_{date_str}.md", "md", required=False),
        CheckSpec(f"observation_{date_str}_json", a / f"observation_{date_str}.json", "json", required=False),

        # HTML artifacts (optional)
        CheckSpec(f"daily_news_{date_str}_html", a / f"daily_news_{date_str}.html", "html", required=False),
    ]


def evaluate_freshness(
    *,
    exists: bool,
    required: bool,
    age_seconds: int | None,
    ok_age_sec: int,
    warn_age_sec: int,
) -> str:
    """
    Freshness rules:
    - Missing:
        required -> NG
        optional -> WARN
    - Exists but no age -> WARN (shouldn't happen)
    - Exists with age:
        <= ok_age_sec  -> OK
        <= warn_age_sec -> WARN
        >  warn_age_sec -> NG if required else WARN
    """
    if not exists:
        return "NG" if required else "WARN"
    if age_seconds is None:
        return "WARN"

    if age_seconds <= ok_age_sec:
        return "OK"
    if age_seconds <= warn_age_sec:
        return "WARN"
    return "NG" if required else "WARN"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--analysis-dir",
        default="data/world_politics/analysis",
        help="Analysis directory that the GUI serves as /analysis/ (default: data/world_politics/analysis)",
    )
    ap.add_argument("--date", default=None, help="Date in YYYY-MM-DD. Default: today (JST).")
    ap.add_argument("--out-latest", default=None, help="Override latest output filename.")
    ap.add_argument("--write-dated", action="store_true", help="Also write dated health_<DATE>.json")

    # freshness thresholds
    ap.add_argument(
        "--ok-age-hours",
        type=float,
        default=24.0,
        help="Freshness OK threshold in hours (default: 24h)",
    )
    ap.add_argument(
        "--warn-age-hours",
        type=float,
        default=48.0,
        help="Freshness WARN threshold in hours (default: 48h). Beyond this is NG for required items.",
    )

    args = ap.parse_args()

    analysis_dir = Path(args.analysis_dir)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    if args.date:
        date_str = args.date.strip()
    else:
        date_str = dt_now_jst().strftime("%Y-%m-%d")

    out_latest = Path(args.out_latest) if args.out_latest else (analysis_dir / "health_latest.json")
    out_dated = analysis_dir / f"health_{date_str}.json"

    ok_age_sec = int(args.ok_age_hours * 3600)
    warn_age_sec = int(args.warn_age_hours * 3600)

    now = dt_now_jst()
    specs = build_specs(analysis_dir, date_str)

    checks: List[Dict[str, Any]] = []
    ok = warn = ng = 0

    for s in specs:
        exists = s.path.exists()
        age_seconds = None
        age_hours = None
        bytes_ = None
        updated_at = None

        if exists:
            try:
                st = s.path.stat()
                bytes_ = int(st.st_size)
                updated_at = iso_mtime_jst(s.path)
                mtime = datetime.fromtimestamp(st.st_mtime, JST)
                age_seconds = int((now - mtime).total_seconds())
                age_hours = round(age_seconds / 3600.0, 3)
            except Exception:
                # keep as None -> WARN
                pass

        # Old "size <= 0" should degrade at least to WARN/NG logic
        if exists and bytes_ is not None and bytes_ <= 0:
            # treat as missing content
            freshness = "NG" if s.required else "WARN"
        else:
            freshness = evaluate_freshness(
                exists=exists,
                required=s.required,
                age_seconds=age_seconds,
                ok_age_sec=ok_age_sec,
                warn_age_sec=warn_age_sec,
            )

        if freshness == "OK":
            ok += 1
        elif freshness == "WARN":
            warn += 1
        else:
            ng += 1

        detail_parts = []
        if not exists:
            detail_parts.append("missing")
        else:
            if bytes_ is not None:
                detail_parts.append(f"size={human_bytes(bytes_)}")
            if updated_at:
                detail_parts.append(f"mtime={updated_at}")
            if age_hours is not None:
                detail_parts.append(f"age={age_hours}h")

        item: Dict[str, Any] = {
            "name": s.name,
            "status": freshness,            # what GUI uses (OK/WARN/NG)
            "freshness": freshness,         # explicit alias
            "required": bool(s.required),
            "kind": s.kind,
            "path": to_relposix(s.path, analysis_dir),
            "detail": " ".join(detail_parts).strip() or "-",
        }

        if bytes_ is not None:
            item["bytes"] = bytes_
        if updated_at:
            item["updated_at"] = updated_at
        if age_seconds is not None:
            item["age_seconds"] = age_seconds
        if age_hours is not None:
            item["age_hours"] = age_hours

        # thresholds for transparency
        item["ok_age_hours"] = float(args.ok_age_hours)
        item["warn_age_hours"] = float(args.warn_age_hours)

        checks.append(item)

    payload: Dict[str, Any] = {
        "generated_at": iso_now_jst(),
        "date": date_str,
        "analysis_dir": analysis_dir.as_posix(),
        "thresholds": {
            "ok_age_hours": float(args.ok_age_hours),
            "warn_age_hours": float(args.warn_age_hours),
        },
        "summary": {
            "ok": ok,
            "warn": warn,
            "ng": ng,
            "total": len(checks),
        },
        "checks": checks,
    }

    out_latest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.write_dated:
        out_dated.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[OK] wrote health json")
    print(f"  latest: {out_latest}")
    if args.write_dated:
        print(f"  dated : {out_dated}")
    print(f"  thresholds: OK<={args.ok_age_hours}h WARN<={args.warn_age_hours}h")
    print(f"  counts: OK={ok} WARN={warn} NG={ng} total={len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

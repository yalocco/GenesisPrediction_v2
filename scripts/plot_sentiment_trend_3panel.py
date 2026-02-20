#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sentiment Trend 3-panel plotter (safe evolution A-stage)

Goal:
- Do NOT touch UI/CSS or data pipeline
- Read sentiment_timeseries.csv and render 3 stacked subplots:
  risk / positive / uncertainty (independent y-scales)
- Output PNG(s) for GUI to pick up (compatible "latest" copy)

Usage (recommended):
  .\.venv\Scripts\python.exe scripts\plot_sentiment_trend_3panel.py

Options:
  --csv <path>     : explicit CSV path
  --out <path>     : explicit output PNG path
  --days <N>       : last N days (default: 180). use 0 for ALL
  --title <text>   : title prefix
  --write-latest   : also write *_latest.png (default: on)
  --no-latest      : disable latest copy

This script tries common repo paths automatically.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt


# ----------------------------
# Repo-aware defaults
# ----------------------------

COMMON_CSV_CANDIDATES = [
    Path("analysis/sentiment/sentiment_timeseries.csv"),
    Path("analysis/sentiment_timeseries.csv"),
    Path("data/sentiment/sentiment_timeseries.csv"),
    Path("data/sentiment_timeseries.csv"),
    Path("sentiment_timeseries.csv"),
]

COMMON_OUT_DIR_CANDIDATES = [
    Path("analysis/plots"),
    Path("analysis"),
    Path("app/static/assets"),
    Path("app/static"),
    Path("data/plots"),
    Path("data"),
    Path("."),
]

DEFAULT_DAYS = 180


@dataclass
class ResolvedPaths:
    csv_path: Path
    out_path: Path
    latest_path: Optional[Path]


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def _find_first_existing(paths: list[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists() and p.is_file():
            return p
    return None


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _detect_date_column(df: pd.DataFrame) -> str:
    candidates = ["date", "day", "datetime", "timestamp", "dt"]
    for c in candidates:
        if c in df.columns:
            return c
    # also allow first column if it looks like date
    if len(df.columns) > 0:
        c0 = df.columns[0]
        if df[c0].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}").any():
            return c0
    raise ValueError(f"date column not found. columns={list(df.columns)}")


def _require_columns(df: pd.DataFrame) -> Tuple[str, str, str]:
    # allow mild variations
    def pick(names: list[str]) -> Optional[str]:
        for n in names:
            if n in df.columns:
                return n
        return None

    risk = pick(["risk", "risk_mean", "risk_score"])
    pos = pick(["positive", "positive_mean", "positive_score", "positivity"])
    unc = pick(["uncertainty", "uncertainty_mean", "uncertainty_score", "unc"])

    missing = [k for k, v in [("risk", risk), ("positive", pos), ("uncertainty", unc)] if v is None]
    if missing:
        raise ValueError(f"missing required columns: {missing}. columns={list(df.columns)}")

    return risk, pos, unc


def resolve_paths(csv_arg: Optional[str], out_arg: Optional[str], write_latest: bool) -> ResolvedPaths:
    # CSV
    if csv_arg:
        csv_path = Path(csv_arg)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")
    else:
        found = _find_first_existing(COMMON_CSV_CANDIDATES)
        if not found:
            raise FileNotFoundError(
                "sentiment_timeseries.csv not found. "
                "Tried: " + ", ".join(str(p) for p in COMMON_CSV_CANDIDATES)
            )
        csv_path = found

    # OUT
    if out_arg:
        out_path = Path(out_arg)
    else:
        out_dir = None
        for d in COMMON_OUT_DIR_CANDIDATES:
            if d.exists() and d.is_dir():
                out_dir = d
                break
        if out_dir is None:
            out_dir = COMMON_OUT_DIR_CANDIDATES[0]
            out_dir.mkdir(parents=True, exist_ok=True)

        # Keep a stable filename so GUI can reference it
        out_path = out_dir / "sentiment_trend_3panel.png"

    latest_path = None
    if write_latest:
        # "latest" companion next to the main out_path
        latest_path = out_path.with_name(out_path.stem + "_latest" + out_path.suffix)

    return ResolvedPaths(csv_path=csv_path, out_path=out_path, latest_path=latest_path)


def load_timeseries(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    date_col = _detect_date_column(df)
    risk_col, pos_col, unc_col = _require_columns(df)

    # Parse date
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).sort_values(date_col)

    # Keep only needed columns (but preserve any extras if you want later)
    df = df[[date_col, risk_col, pos_col, unc_col]].copy()
    df.rename(
        columns={
            date_col: "date",
            risk_col: "risk",
            pos_col: "positive",
            unc_col: "uncertainty",
        },
        inplace=True,
    )

    # Ensure numeric
    for c in ["risk", "positive", "uncertainty"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["risk", "positive", "uncertainty"])
    return df


def filter_last_days(df: pd.DataFrame, days: int) -> pd.DataFrame:
    if days <= 0:
        return df
    if df.empty:
        return df
    end = df["date"].max()
    start = end - pd.Timedelta(days=days)
    return df[df["date"] >= start]


def plot_3panel(df: pd.DataFrame, out_path: Path, title_prefix: str) -> None:
    if df.empty:
        raise ValueError("No data to plot (df is empty after filtering).")

    # 3 stacked panels, shared x
    fig, axes = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(12, 8))
    ax_risk, ax_pos, ax_unc = axes

    # Basic lines (no explicit colors -> minimal style coupling)
    ax_risk.plot(df["date"], df["risk"])
    ax_pos.plot(df["date"], df["positive"])
    ax_unc.plot(df["date"], df["uncertainty"])

    # Labels / grids
    ax_risk.set_ylabel("risk")
    ax_pos.set_ylabel("positive")
    ax_unc.set_ylabel("uncertainty")
    for ax in axes:
        ax.grid(True, alpha=0.3)

    # Title
    d0 = df["date"].min().strftime("%Y-%m-%d")
    d1 = df["date"].max().strftime("%Y-%m-%d")
    fig.suptitle(f"{title_prefix} ({d0} → {d1})", fontsize=14)

    # Tight layout
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    _ensure_parent_dir(out_path)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def copy_latest(src: Path, dst: Path) -> None:
    # Use binary copy to avoid Windows symlink requirements
    data = src.read_bytes()
    dst.write_bytes(data)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=str, default=None, help="Path to sentiment_timeseries.csv")
    ap.add_argument("--out", type=str, default=None, help="Output PNG path")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Last N days (0 = ALL)")
    ap.add_argument("--title", type=str, default="Sentiment Trend (3-panel)", help="Title prefix")
    ap.add_argument("--write-latest", action="store_true", help="Write *_latest.png (default ON)")
    ap.add_argument("--no-latest", action="store_true", help="Disable latest copy")
    args = ap.parse_args(argv)

    write_latest = True
    if args.no_latest:
        write_latest = False
    if args.write_latest:
        write_latest = True

    paths = resolve_paths(args.csv, args.out, write_latest=write_latest)

    _log(f"CSV  : {paths.csv_path}")
    _log(f"OUT  : {paths.out_path}")
    if paths.latest_path:
        _log(f"LATEST: {paths.latest_path}")

    df = load_timeseries(paths.csv_path)
    df = filter_last_days(df, args.days)

    _log(f"rows : {len(df)} (days={args.days})")
    plot_3panel(df, paths.out_path, args.title)

    if paths.latest_path:
        _ensure_parent_dir(paths.latest_path)
        copy_latest(paths.out_path, paths.latest_path)
        _log("latest copy written")

    _log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
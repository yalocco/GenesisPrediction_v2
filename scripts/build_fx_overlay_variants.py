#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build FX overlay variants and "serve" them into:
  - analysis/fx/                       (canonical build outputs)
  - data/world_politics/analysis/fx/   (FastAPI static-serving target)

Variants:
  - JPYTHB: prefer prediction overlay image if exists; else copy legacy latest
  - USDJPY: prefer prediction overlay image if exists; else build from CSV
  - USDTHB: build "prediction-style" overlay from CSV (Band + ON/WARN/OFF markers)

This script is designed to be safe to run repeatedly (no SameFileError).
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt


# ----------------------------
# Helpers
# ----------------------------

def repo_root_from_this_file() -> Path:
    # scripts/build_fx_overlay_variants.py -> <ROOT>/scripts/...
    return Path(__file__).resolve().parents[1]


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def same_file(a: Path, b: Path) -> bool:
    try:
        return a.resolve().samefile(b.resolve())
    except Exception:
        return a.resolve() == b.resolve()


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    if not src.exists():
        print(f"[WARN] not found: {src}")
        return
    if dst.exists() and same_file(src, dst):
        print(f"[OK] samefile (skip): {dst}")
        return
    shutil.copyfile(src, dst)
    print(f"[OK] -> {dst}")


def parse_date(s: str) -> Date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def infer_fx_date_from_csv(csv_path: Path) -> Optional[Date]:
    if not csv_path.exists():
        return None
    try:
        df = pd.read_csv(csv_path)
        if "date" not in df.columns:
            return None
        last = str(df["date"].dropna().iloc[-1])
        # allow 'YYYY-MM-DD' only
        return parse_date(last[:10])
    except Exception:
        return None


def load_rates_csv(csv_path: Path) -> pd.DataFrame:
    """
    Expect columns:
      - date (YYYY-MM-DD)
      - rate (float)  OR close (float)
    """
    df = pd.read_csv(csv_path)
    if "date" not in df.columns:
        raise ValueError(f"missing 'date' column in {csv_path}")
    if "rate" in df.columns:
        ycol = "rate"
    elif "close" in df.columns:
        ycol = "close"
    else:
        # try any numeric col
        num_cols = [c for c in df.columns if c != "date"]
        if not num_cols:
            raise ValueError(f"no rate-like column in {csv_path}")
        ycol = num_cols[0]

    out = df[["date", ycol]].copy()
    out.columns = ["date", "rate"]
    out["date"] = pd.to_datetime(out["date"])
    out["rate"] = pd.to_numeric(out["rate"], errors="coerce")
    out = out.dropna().sort_values("date").reset_index(drop=True)
    return out


def compute_band(df: pd.DataFrame, window: int = 20, k: float = 2.0) -> pd.DataFrame:
    x = df.copy()
    x["ma"] = x["rate"].rolling(window).mean()
    x["sd"] = x["rate"].rolling(window).std()
    x["lo"] = x["ma"] - k * x["sd"]
    x["hi"] = x["ma"] + k * x["sd"]
    return x


def decision_rule(df: pd.DataFrame) -> pd.Series:
    """
    Simple, deterministic rule to emulate "prediction-style" markers:
      - OFF  : rate < lo
      - WARN : lo <= rate < ma
      - ON   : rate >= ma
    Note: This is NOT a trading recommendation; it's a visualization rule only.
    """
    off = df["rate"] < df["lo"]
    warn = (~off) & (df["rate"] < df["ma"])
    on = df["rate"] >= df["ma"]
    out = pd.Series(np.where(off, "OFF", np.where(warn, "WARN", "ON")), index=df.index)
    return out


def plot_overlay(
    df: pd.DataFrame,
    title: str,
    ylabel: str,
    out_png: Path,
    show_markers: bool = True,
) -> None:
    ensure_dir(out_png.parent)

    x = compute_band(df)
    # band needs ma/sd available
    valid = x.dropna(subset=["ma", "lo", "hi"]).copy()

    fig = plt.figure(figsize=(12, 6), dpi=140)
    ax = fig.add_subplot(111)

    ax.plot(x["date"], x["rate"], label=title.split()[0].lower())
    ax.plot(valid["date"], valid["ma"], label="MA20")
    ax.fill_between(valid["date"], valid["lo"], valid["hi"], alpha=0.18, label="Band")

    if show_markers and len(valid) > 0:
        d = valid.copy()
        d["decision"] = decision_rule(d)

        # plot markers by decision
        for name, marker in [("ON", "o"), ("WARN", "^"), ("OFF", "x")]:
            sel = d[d["decision"] == name]
            if len(sel) == 0:
                continue
            ax.scatter(sel["date"], sel["rate"], s=18, marker=marker, label=name)

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


@dataclass
class Paths:
    root: Path
    analysis_fx: Path
    served_fx: Path
    data_fx: Path
    legacy_latest_fx_overlay_png: Path

    usdthb_csv: Path
    usdjpy_csv: Path

    # preferred (prediction-style) images if they exist
    preferred_jpythb_png: Path
    preferred_usdjpy_png: Path
    preferred_usdthb_png: Path


def build_paths(root: Path) -> Paths:
    analysis_fx = root / "analysis" / "fx"
    served_fx = root / "data" / "world_politics" / "analysis" / "fx"
    data_fx = root / "data" / "fx"

    # legacy location (your pipeline keeps this alive)
    legacy_latest_fx_overlay_png = root / "data" / "world_politics" / "analysis" / "fx" / "fx_overlay_latest.png"

    usdthb_csv = data_fx / "usdthb.csv"
    usdjpy_csv = data_fx / "usdjpy.csv"

    # These two already exist in your data/fx by earlier logs
    preferred_jpythb_png = data_fx / "fx_multi_jpy_thb_overlay.png"
    preferred_usdjpy_png = data_fx / "fx_multi_jpy_usd_overlay.png"

    # Create/consume this for USDTHB "prediction-style" overlay
    # (We will generate it if missing.)
    preferred_usdthb_png = data_fx / "fx_multi_usd_thb_overlay.png"

    return Paths(
        root=root,
        analysis_fx=analysis_fx,
        served_fx=served_fx,
        data_fx=data_fx,
        legacy_latest_fx_overlay_png=legacy_latest_fx_overlay_png,
        usdthb_csv=usdthb_csv,
        usdjpy_csv=usdjpy_csv,
        preferred_jpythb_png=preferred_jpythb_png,
        preferred_usdjpy_png=preferred_usdjpy_png,
        preferred_usdthb_png=preferred_usdthb_png,
    )


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (optional)")
    args = ap.parse_args()

    root = repo_root_from_this_file()
    P = build_paths(root)

    ensure_dir(P.analysis_fx)
    ensure_dir(P.served_fx)

    # decide date
    if args.date:
        d = parse_date(args.date)
    else:
        # infer from csv last date (prefer usdthb, else usdjpy)
        d = infer_fx_date_from_csv(P.usdthb_csv) or infer_fx_date_from_csv(P.usdjpy_csv) or datetime.utcnow().date()

    # --- JPYTHB ---
    jpythb_latest = P.analysis_fx / "fx_overlay_latest_jpythb.png"
    jpythb_dated = P.analysis_fx / f"fx_overlay_{d.isoformat()}_jpythb.png"

    # prefer prediction image; fallback to legacy latest
    if P.preferred_jpythb_png.exists():
        print(f"[OK] jpythb latest from (preferred): {P.preferred_jpythb_png}")
        copy_file(P.preferred_jpythb_png, jpythb_latest)
        copy_file(P.preferred_jpythb_png, jpythb_dated)
    else:
        print(f"[WARN] preferred jpythb not found: {P.preferred_jpythb_png}")
        if P.legacy_latest_fx_overlay_png.exists():
            print(f"[OK] jpythb latest from (legacy): {P.legacy_latest_fx_overlay_png}")
            copy_file(P.legacy_latest_fx_overlay_png, jpythb_latest)
            copy_file(P.legacy_latest_fx_overlay_png, jpythb_dated)
        else:
            print(f"[WARN] not found: {P.legacy_latest_fx_overlay_png} (jpythb skipped)")

    # serve
    copy_file(jpythb_latest, P.served_fx / jpythb_latest.name)
    copy_file(jpythb_dated, P.served_fx / jpythb_dated.name)

    # --- USDJPY (prediction-style if preferred exists; else build from CSV with markers) ---
    usdjpy_latest = P.analysis_fx / "fx_overlay_latest_usdjpy.png"
    usdjpy_dated = P.analysis_fx / f"fx_overlay_{d.isoformat()}_usdjpy.png"

    if P.preferred_usdjpy_png.exists():
        print(f"[OK] usdjpy latest from (preferred): {P.preferred_usdjpy_png}")
        copy_file(P.preferred_usdjpy_png, usdjpy_latest)
        copy_file(P.preferred_usdjpy_png, usdjpy_dated)
    else:
        # build from CSV (with markers)
        if P.usdjpy_csv.exists():
            df = load_rates_csv(P.usdjpy_csv)
            plot_overlay(
                df=df,
                title="USD↔JPY Overlay",
                ylabel="JPY per USD",
                out_png=usdjpy_dated,
                show_markers=True,
            )
            copy_file(usdjpy_dated, usdjpy_latest)
            print(f"[OK] built: {usdjpy_dated}")
            print(f"[OK] latest: {usdjpy_latest}")
        else:
            print(f"[WARN] missing csv: {P.usdjpy_csv} (usdjpy skipped)")

    copy_file(usdjpy_latest, P.served_fx / usdjpy_latest.name)
    copy_file(usdjpy_dated, P.served_fx / usdjpy_dated.name)

    # --- USDTHB (prediction-style): generate preferred image if needed, then use it ---
    usdthb_latest = P.analysis_fx / "fx_overlay_latest_usdthb.png"
    usdthb_dated = P.analysis_fx / f"fx_overlay_{d.isoformat()}_usdthb.png"

    # ensure preferred exists by generating it (prediction-style) from CSV
    if not P.preferred_usdthb_png.exists():
        if P.usdthb_csv.exists():
            df = load_rates_csv(P.usdthb_csv)
            # build "prediction-style" overlay into data/fx preferred path
            plot_overlay(
                df=df,
                title="USD↔THB Overlay",
                ylabel="THB per USD",
                out_png=P.preferred_usdthb_png,
                show_markers=True,
            )
            print(f"[OK] generated (preferred): {P.preferred_usdthb_png}")
        else:
            print(f"[WARN] missing csv: {P.usdthb_csv} (usdthb cannot be generated)")

    if P.preferred_usdthb_png.exists():
        print(f"[OK] usdthb latest from (preferred): {P.preferred_usdthb_png}")
        copy_file(P.preferred_usdthb_png, usdthb_latest)
        copy_file(P.preferred_usdthb_png, usdthb_dated)
    else:
        # last resort: build from CSV without markers (but should not happen if CSV exists)
        if P.usdthb_csv.exists():
            df = load_rates_csv(P.usdthb_csv)
            plot_overlay(
                df=df,
                title="USD↔THB Overlay",
                ylabel="THB per USD",
                out_png=usdthb_dated,
                show_markers=False,
            )
            copy_file(usdthb_dated, usdthb_latest)
            print(f"[OK] built (fallback): {usdthb_dated}")
            print(f"[OK] latest (fallback): {usdthb_latest}")
        else:
            print(f"[WARN] missing csv: {P.usdthb_csv} (usdthb skipped)")

    copy_file(usdthb_latest, P.served_fx / usdthb_latest.name)
    copy_file(usdthb_dated, P.served_fx / usdthb_dated.name)

    print("\n[INFO] served overlays (data/world_politics/analysis/fx):")
    try:
        for p in sorted(P.served_fx.glob("fx_overlay_*")):
            if p.suffix.lower() == ".png":
                print(f" - {p.as_posix()}")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
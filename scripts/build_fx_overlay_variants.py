#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build FX overlay variants and "serve" them into:
  - analysis/fx/                       (canonical build outputs)
  - data/world_politics/analysis/fx/   (FastAPI static-serving target)

Variants:
  - JPYTHB: prefer prediction overlay image if exists; else copy legacy latest
  - USDJPY: prefer prediction overlay image if exists; else build from CSV
  - USDTHB: ALWAYS rebuild prediction-style overlay from CSV
            (Band + ON/WARN/OFF markers) so it matches JPYTHB / USDJPY style

This script is designed to be safe to run repeatedly (no SameFileError).
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import date as Date
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt


DEFAULT_PERIOD = "90d"


def repo_root_from_this_file() -> Path:
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
        return parse_date(last[:10])
    except Exception:
        return None


def load_rates_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "date" not in df.columns:
        raise ValueError(f"missing 'date' column in {csv_path}")

    if "rate" in df.columns:
        ycol = "rate"
    elif "close" in df.columns:
        ycol = "close"
    else:
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
    off = df["rate"] < df["lo"]
    warn = (~off) & (df["rate"] < df["ma"])
    on = df["rate"] >= df["ma"]
    return pd.Series(np.where(off, "OFF", np.where(warn, "WARN", "ON")), index=df.index)


def window_df(df: pd.DataFrame, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    if period.upper() == "ALL":
        return df.copy()

    if period.endswith("d"):
        days = int(period[:-1])
        last = df["date"].max()
        start = last - pd.Timedelta(days=days)
        out = df[df["date"] >= start].copy()
        if not out.empty:
            return out

    return df.copy()


def autoscale_y(ax, df: pd.DataFrame) -> None:
    cols = [c for c in ["rate", "ma", "lo", "hi"] if c in df.columns]
    if not cols:
        return
    vals = pd.concat([pd.to_numeric(df[c], errors="coerce") for c in cols], axis=0).dropna()
    if vals.empty:
        return
    vmin = float(vals.min())
    vmax = float(vals.max())
    pad = (vmax - vmin) * 0.08 if vmax > vmin else max(abs(vmin) * 0.02, 0.01)
    ax.set_ylim(vmin - pad, vmax + pad)


def plot_overlay(
    df: pd.DataFrame,
    title: str,
    ylabel: str,
    out_png: Path,
    show_markers: bool = True,
    period: str = DEFAULT_PERIOD,
) -> None:
    ensure_dir(out_png.parent)

    x = compute_band(df)
    x = window_df(x, period=period)
    valid = x.dropna(subset=["ma", "lo", "hi"]).copy()

    fig = plt.figure(figsize=(12, 6), dpi=140)
    ax = fig.add_subplot(111)

    ax.plot(x["date"], x["rate"], label=title.split()[0].lower())
    if len(valid) > 0:
        ax.plot(valid["date"], valid["ma"], label="MA20")
        ax.fill_between(valid["date"], valid["lo"], valid["hi"], alpha=0.18, label="Band")

    if show_markers and len(valid) > 0:
        d = valid.copy()
        d["decision"] = decision_rule(d)
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

    if not x.empty:
        ax.set_xlim(x["date"].min(), x["date"].max())
        autoscale_y(ax, x)

    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
    print(f"[OK] built overlay: {out_png}")


@dataclass
class Paths:
    root: Path
    analysis_fx: Path
    served_fx: Path
    data_fx: Path
    legacy_latest_fx_overlay_png: Path
    usdthb_csv: Path
    usdjpy_csv: Path
    preferred_jpythb_png: Path
    preferred_usdjpy_png: Path
    preferred_usdthb_png: Path


def build_paths(root: Path) -> Paths:
    analysis_fx = root / "analysis" / "fx"
    served_fx = root / "data" / "world_politics" / "analysis" / "fx"
    data_fx = root / "data" / "fx"

    legacy_latest_fx_overlay_png = root / "data" / "world_politics" / "analysis" / "fx" / "fx_overlay_latest.png"

    usdthb_csv = data_fx / "usdthb.csv"
    usdjpy_csv = data_fx / "usdjpy.csv"

    preferred_jpythb_png = data_fx / "fx_multi_jpy_thb_overlay.png"
    preferred_usdjpy_png = data_fx / "fx_multi_jpy_usd_overlay.png"
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (optional)")
    ap.add_argument("--period", type=str, default=DEFAULT_PERIOD, help="90d / 180d / ALL")
    args = ap.parse_args()

    root = repo_root_from_this_file()
    p = build_paths(root)

    ensure_dir(p.analysis_fx)
    ensure_dir(p.served_fx)

    if args.date:
        d = parse_date(args.date)
    else:
        d = infer_fx_date_from_csv(p.usdthb_csv) or infer_fx_date_from_csv(p.usdjpy_csv) or datetime.utcnow().date()

    # --- JPYTHB ---
    jpythb_latest = p.analysis_fx / "fx_overlay_latest_jpythb.png"
    jpythb_dated = p.analysis_fx / f"fx_overlay_{d.isoformat()}_jpythb.png"

    if p.preferred_jpythb_png.exists():
        print(f"[OK] jpythb latest from (preferred): {p.preferred_jpythb_png}")
        copy_file(p.preferred_jpythb_png, jpythb_latest)
        copy_file(p.preferred_jpythb_png, jpythb_dated)
    else:
        print(f"[WARN] preferred jpythb not found: {p.preferred_jpythb_png}")
        if p.legacy_latest_fx_overlay_png.exists():
            print(f"[OK] jpythb latest from (legacy): {p.legacy_latest_fx_overlay_png}")
            copy_file(p.legacy_latest_fx_overlay_png, jpythb_latest)
            copy_file(p.legacy_latest_fx_overlay_png, jpythb_dated)
        else:
            print(f"[WARN] not found: {p.legacy_latest_fx_overlay_png} (jpythb skipped)")

    copy_file(jpythb_latest, p.served_fx / jpythb_latest.name)
    copy_file(jpythb_dated, p.served_fx / jpythb_dated.name)

    # --- USDJPY ---
    usdjpy_latest = p.analysis_fx / "fx_overlay_latest_usdjpy.png"
    usdjpy_dated = p.analysis_fx / f"fx_overlay_{d.isoformat()}_usdjpy.png"

    if p.preferred_usdjpy_png.exists():
        print(f"[OK] usdjpy latest from (preferred): {p.preferred_usdjpy_png}")
        copy_file(p.preferred_usdjpy_png, usdjpy_latest)
        copy_file(p.preferred_usdjpy_png, usdjpy_dated)
    else:
        if p.usdjpy_csv.exists():
            df = load_rates_csv(p.usdjpy_csv)
            plot_overlay(
                df=df,
                title="USD↔JPY Overlay",
                ylabel="JPY per USD",
                out_png=usdjpy_dated,
                show_markers=True,
                period=args.period,
            )
            copy_file(usdjpy_dated, usdjpy_latest)
            print(f"[OK] latest: {usdjpy_latest}")
        else:
            print(f"[WARN] missing csv: {p.usdjpy_csv} (usdjpy skipped)")

    copy_file(usdjpy_latest, p.served_fx / usdjpy_latest.name)
    copy_file(usdjpy_dated, p.served_fx / usdjpy_dated.name)

    # --- USDTHB ---
    usdthb_latest = p.analysis_fx / "fx_overlay_latest_usdthb.png"
    usdthb_dated = p.analysis_fx / f"fx_overlay_{d.isoformat()}_usdthb.png"

    if p.usdthb_csv.exists():
        df = load_rates_csv(p.usdthb_csv)
        plot_overlay(
            df=df,
            title="USD↔THB Overlay",
            ylabel="THB per USD",
            out_png=p.preferred_usdthb_png,
            show_markers=True,
            period=args.period,
        )
        print(f"[OK] regenerated (preferred): {p.preferred_usdthb_png}")

        copy_file(p.preferred_usdthb_png, usdthb_latest)
        copy_file(p.preferred_usdthb_png, usdthb_dated)
        print(f"[OK] usdthb latest from (preferred): {p.preferred_usdthb_png}")
    else:
        print(f"[WARN] missing csv: {p.usdthb_csv} (usdthb skipped)")

    copy_file(usdthb_latest, p.served_fx / usdthb_latest.name)
    copy_file(usdthb_dated, p.served_fx / usdthb_dated.name)

    print("\n[INFO] served overlays (data/world_politics/analysis/fx):")
    try:
      for item in sorted(p.served_fx.glob("fx_overlay_*")):
          if item.suffix.lower() == ".png":
              print(f" - {item.as_posix()}")
    except Exception:
      pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
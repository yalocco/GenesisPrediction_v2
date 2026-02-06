# scripts/plot_fx_major_pairs.py
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]

FX_DIR = ROOT / "data" / "fx"
OUT_DIR = ROOT / "data" / "world_politics" / "analysis"

PAIR_SPECS = [
    ("usdjpy", ["usdjpy", "usd_jpy", "usd-jpy", "usdjp y", "usd jpy"]),
    ("eurjpy", ["eurjpy", "eur_jpy", "eur-jpy", "eurojpy", "euro_jpy", "eur jpy"]),
    ("eurusd", ["eurusd", "eur_usd", "eur-usd", "eurodollar", "eur usd"]),
]


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _find_candidate_csv(pair_keys: list[str]) -> Optional[Path]:
    if not FX_DIR.exists():
        return None

    keys_norm = [_normalize(k) for k in pair_keys]

    best: Optional[Tuple[int, Path]] = None  # score, path
    for p in FX_DIR.glob("*.csv"):
        name_norm = _normalize(p.name)
        score = 0
        for k in keys_norm:
            if k and k in name_norm:
                score += 10

        # slight boost for likely “rate series” style names
        if "spot" in name_norm or "rate" in name_norm or "series" in name_norm:
            score += 2
        if "noise" in name_norm or "forecast" in name_norm or "eval" in name_norm or "miss" in name_norm:
            score -= 3

        if score <= 0:
            continue

        if best is None or score > best[0]:
            best = (score, p)

    return best[1] if best else None


def _pick_xy(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Try to infer x(date) and y(value) from arbitrary CSV.
    - x: date/time column or index
    - y: first numeric column that looks like a rate
    """
    # normalize columns
    cols = [c.strip() for c in df.columns]
    df.columns = cols

    # X 후보
    xcol = None
    for c in cols:
        cn = c.lower()
        if cn in ("date", "day", "time", "timestamp", "datetime"):
            xcol = c
            break
        if "date" in cn or "time" in cn:
            xcol = c
            break

    if xcol is not None:
        x = pd.to_datetime(df[xcol], errors="coerce")
        df2 = df.drop(columns=[xcol])
    else:
        # indexで勝負
        x = pd.to_datetime(df.index, errors="coerce")
        df2 = df

    # y候補（数値列）
    numeric_cols = [c for c in df2.columns if pd.api.types.is_numeric_dtype(df2[c])]
    if not numeric_cols:
        # try coerce numeric
        for c in df2.columns:
            s = pd.to_numeric(df2[c], errors="coerce")
            if s.notna().sum() >= max(5, int(len(s) * 0.3)):
                df2[c] = s
        numeric_cols = [c for c in df2.columns if pd.api.types.is_numeric_dtype(df2[c])]

    if not numeric_cols:
        raise ValueError("no numeric columns")

    # それっぽい列名優先
    priority = ["close", "rate", "value", "price", "mid", "last"]
    ycol = None
    for key in priority:
        for c in numeric_cols:
            if key in c.lower():
                ycol = c
                break
        if ycol:
            break
    if ycol is None:
        ycol = numeric_cols[0]

    y = df2[ycol]
    return x, y


def _render_placeholder(out_png: Path, title: str, note: str) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 4))
    plt.axis("off")
    plt.text(0.02, 0.70, title, fontsize=18, fontweight="bold")
    plt.text(0.02, 0.45, note, fontsize=12)
    plt.text(0.02, 0.20, "source: (not found)", fontsize=10, alpha=0.7)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def _render_plot(out_png: Path, title: str, src_csv: Path) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(src_csv)
    if df.empty:
        raise ValueError("empty csv")

    x, y = _pick_xy(df)

    # clean
    m = x.notna() & y.notna()
    x = x[m]
    y = y[m]
    if len(x) < 5:
        raise ValueError("too few points")

    # sort by time
    order = x.argsort()
    x = x.iloc[order]
    y = y.iloc[order]

    plt.figure(figsize=(10, 4))
    plt.plot(x, y, linewidth=1.6)
    plt.title(title)
    plt.xlabel("")
    plt.ylabel("")
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    date = args.date

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for pair, keys in PAIR_SPECS:
        out_dated = OUT_DIR / f"fx_{pair}_{date}.png"
        out_latest = OUT_DIR / f"fx_{pair}_latest.png"

        src = _find_candidate_csv(keys)
        title = pair.upper()

        try:
            if src is None:
                _render_placeholder(out_dated, f"{title}", "missing CSV under data/fx/")
            else:
                _render_plot(out_dated, f"{title}", src)
            # update latest alias
            out_latest.write_bytes(out_dated.read_bytes())
        except Exception as e:
            _render_placeholder(out_dated, f"{title}", f"failed to plot: {type(e).__name__}: {e}")
            out_latest.write_bytes(out_dated.read_bytes())

    print("[OK] FX major overlays generated")
    print(f"  out: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

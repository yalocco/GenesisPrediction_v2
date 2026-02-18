# scripts/fx_multi_overlay_from_rates.py
# Build a simple multi-overlay image from available FX rate CSVs (USDJPY, USDTHB) and write data/fx/fx_multi_overlay.png
#
# This is used by FX overlay pipeline.
#
# Run:
#   .\.venv\Scripts\python.exe scripts\fx_multi_overlay_from_rates.py

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_FX = REPO_ROOT / "data" / "fx"
OUT_PNG = DATA_FX / "fx_multi_overlay.png"

USDJPY = DATA_FX / "usdjpy.csv"
USDTHB = DATA_FX / "usdthb.csv"


def _load_series(path: Path, label: str) -> pd.Series:
    df = pd.read_csv(path)
    # guess date col
    date_col = None
    for c in ["date", "Date", "DATE", "day", "Day", "DAY", "timestamp", "time"]:
        if c in df.columns:
            date_col = c
            break
    if date_col is None:
        date_col = df.columns[0]

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).copy()
    df = df.sort_values(date_col)

    # guess value col
    value_col = None
    for c in ["close", "Close", "CLOSE", "rate", "Rate", "RATE", "value", "Value", "VALUE"]:
        if c in df.columns:
            value_col = c
            break
    if value_col is None:
        # pick first numeric
        for c in df.columns:
            if c == date_col:
                continue
            if pd.api.types.is_numeric_dtype(df[c]):
                value_col = c
                break
    if value_col is None:
        raise RuntimeError(f"no numeric column found in {path}")

    s = pd.to_numeric(df[value_col], errors="coerce")
    idx = df[date_col].dt.strftime("%Y-%m-%d")
    out = pd.Series(s.values, index=idx.values, dtype="float64")
    out = out.dropna()
    out = out[~out.index.duplicated(keep="last")]
    out.name = label
    return out


def main() -> int:
    DATA_FX.mkdir(parents=True, exist_ok=True)

    series = []
    if USDJPY.exists():
        series.append(_load_series(USDJPY, "USDJPY"))
    if USDTHB.exists():
        series.append(_load_series(USDTHB, "USDTHB"))

    if not series:
        raise SystemExit("no rate csv found")

    plt.figure()
    for s in series:
        plt.plot(list(range(len(s))), s.values, label=s.name)
    plt.legend()
    plt.title("FX Multi Overlay (normalized index)")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150)
    plt.close()

    print("[OK] fx_multi_overlay_from_rates: wrote", OUT_PNG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

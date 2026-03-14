#!/usr/bin/env python3
# Build FX overlay images from rates CSV

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

DATA_FX = ROOT / "data" / "fx"

USDJPY = DATA_FX / "usdjpy.csv"
USDTHB = DATA_FX / "usdthb.csv"

OUT_USDJPY = DATA_FX / "fx_multi_jpy_usd_overlay.png"
OUT_USDTHB = DATA_FX / "fx_multi_usd_thb_overlay.png"


def load_series(path):

    df = pd.read_csv(path)

    date_col = None
    for c in ["date", "Date", "timestamp"]:
        if c in df.columns:
            date_col = c
            break

    if date_col is None:
        date_col = df.columns[0]

    value_col = None
    for c in ["close", "rate", "value"]:
        if c in df.columns:
            value_col = c
            break

    if value_col is None:
        value_col = df.columns[1]

    df[date_col] = pd.to_datetime(df[date_col])

    s = pd.Series(df[value_col].values, index=df[date_col])

    return s


def plot_overlay(series, title, out):

    plt.figure(figsize=(12,6))
    plt.plot(series.index, series.values)
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(out, dpi=150)
    plt.close()

    print("[OK] wrote", out)


def main():

    DATA_FX.mkdir(parents=True, exist_ok=True)

    if USDJPY.exists():

        s = load_series(USDJPY)

        plot_overlay(
            s,
            "USD/JPY Overlay",
            OUT_USDJPY
        )

    if USDTHB.exists():

        s = load_series(USDTHB)

        plot_overlay(
            s,
            "USD/THB Overlay",
            OUT_USDTHB
        )


if __name__ == "__main__":
    main()
# scripts/fx_remittance_overlay.py
# FX Multi Overlay (JPY↔THB / JPY↔USD)
#
# - pair: jpy_thb / jpy_usd
# - Default: jpy_thb (backward compatible)
# - Saves PNG (no GUI by default; use --show to display)
#
# Run:
#   python scripts/fx_remittance_overlay.py --pair jpy_thb
#   python scripts/fx_remittance_overlay.py --pair jpy_usd

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons


# ----------------------------
# Settings (tunable)
# ----------------------------
MA_N = 20
VOL_N = 20
BAND_K = 1.0
DEFAULT_PERIOD = "90d"  # '90d' | '180d' | 'ALL'

ROOT = Path(__file__).resolve().parents[1]
FX_DIR = ROOT / "data" / "fx"
DASH_DIR = FX_DIR / "dashboard"

# legacy (must keep for current pipeline)
LEGACY_THB_DASH = FX_DIR / "jpy_thb_remittance_dashboard.csv"
LEGACY_THB_PNG = FX_DIR / "jpy_thb_remittance_overlay.png"

# new pair-based outputs (local)
PAIR_PNG = {
    "jpy_thb": FX_DIR / "fx_jpy_thb_overlay.png",
    "jpy_usd": FX_DIR / "fx_jpy_usd_overlay.png",
}

PAIR_DASH = {
    "jpy_thb": DASH_DIR / "jpy_thb_dashboard.csv",
    "jpy_usd": DASH_DIR / "jpy_usd_dashboard.csv",
}


# ----------------------------
# Small helper: scroll zoom + drag pan
# ----------------------------
@dataclass
class _ViewState:
    press_event: object | None = None
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None


def enable_scroll_zoom_and_pan(fig: matplotlib.figure.Figure, ax: matplotlib.axes.Axes) -> None:
    state = _ViewState()

    def _on_scroll(event):
        if event.inaxes != ax:
            return
        step = getattr(event, "step", None)
        if step is None:
            if getattr(event, "button", None) == "up":
                step = 1
            elif getattr(event, "button", None) == "down":
                step = -1
            else:
                return

        base_scale = 1.2
        scale_factor = 1 / base_scale if step > 0 else base_scale

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        xdata = event.xdata
        ydata = event.ydata
        if xdata is None or ydata is None:
            return

        def _scale_range(low, high, center, s):
            new_low = center - (center - low) * s
            new_high = center + (high - center) * s
            return new_low, new_high

        ax.set_xlim(_scale_range(cur_xlim[0], cur_xlim[1], xdata, scale_factor))
        ax.set_ylim(_scale_range(cur_ylim[0], cur_ylim[1], ydata, scale_factor))
        fig.canvas.draw_idle()

    def _on_press(event):
        if event.inaxes != ax:
            return
        if event.button != 1:
            return
        state.press_event = event
        state.xlim = ax.get_xlim()
        state.ylim = ax.get_ylim()

    def _on_release(event):
        state.press_event = None
        state.xlim = None
        state.ylim = None

    def _on_motion(event):
        if state.press_event is None:
            return
        if event.inaxes != ax:
            return
        if state.xlim is None or state.ylim is None:
            return

        dx = (event.xdata - state.press_event.xdata) if (event.xdata is not None and state.press_event.xdata is not None) else 0
        dy = (event.ydata - state.press_event.ydata) if (event.ydata is not None and state.press_event.ydata is not None) else 0

        ax.set_xlim(state.xlim[0] - dx, state.xlim[1] - dx)
        ax.set_ylim(state.ylim[0] - dy, state.ylim[1] - dy)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("scroll_event", _on_scroll)
    fig.canvas.mpl_connect("button_press_event", _on_press)
    fig.canvas.mpl_connect("button_release_event", _on_release)
    fig.canvas.mpl_connect("motion_notify_event", _on_motion)


# ----------------------------
# Data
# ----------------------------
def _must_have_cols(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(f"[ERR] {label} missing columns: {missing}")


def load_dashboard(pair: str) -> pd.DataFrame:
    if pair == "jpy_thb":
        # Prefer legacy if exists (overlay.html freeze compatibility)
        csv_path = LEGACY_THB_DASH if LEGACY_THB_DASH.exists() else PAIR_DASH[pair]
        label = str(csv_path)
        if not csv_path.exists():
            raise SystemExit(f"[ERR] input not found: {csv_path}")

        df = pd.read_csv(csv_path)
        _must_have_cols(df, ["date", "jpy_thb"], label)
        y_col = "jpy_thb"

    elif pair == "jpy_usd":
        csv_path = PAIR_DASH[pair]
        label = str(csv_path)
        if not csv_path.exists():
            raise SystemExit(f"[ERR] input not found: {csv_path}")

        df = pd.read_csv(csv_path)
        _must_have_cols(df, ["date", "jpy_usd"], label)
        y_col = "jpy_usd"

    else:
        raise SystemExit(f"[ERR] unknown pair: {pair}")

    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values("date").reset_index(drop=True)

    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df = df.dropna(subset=[y_col]).copy()

    # optional columns
    if "combined_decision" not in df.columns:
        df["combined_decision"] = "ON"
    if "combined_noise_prob" not in df.columns:
        df["combined_noise_prob"] = np.nan
    if "remit_note" not in df.columns:
        df["remit_note"] = ""

    df.attrs["y_col"] = y_col
    return df


def add_ma_band(df: pd.DataFrame, y_col: str) -> pd.DataFrame:
    px = df[y_col].astype(float)
    ma = px.rolling(MA_N).mean()
    vol = px.pct_change().rolling(VOL_N).std()
    band = ma * (vol * BAND_K)

    out = df.copy()
    out["ma"] = ma
    out["band"] = band
    out["upper"] = ma + band
    out["lower"] = ma - band
    return out


# ----------------------------
# Plot helpers
# ----------------------------
def _window_mask(df: pd.DataFrame, period_label: str) -> pd.Series:
    if period_label.upper() == "ALL":
        return pd.Series([True] * len(df), index=df.index)
    if period_label.endswith("d"):
        n = int(period_label[:-1])
        last = df["date"].max()
        start = last - pd.Timedelta(days=n)
        return df["date"] >= start
    return pd.Series([True] * len(df), index=df.index)


def _autoscale_y(ax: matplotlib.axes.Axes, df_win: pd.DataFrame, y_col: str) -> None:
    cols = [y_col, "upper", "lower", "ma"]
    vals = []
    for c in cols:
        if c in df_win.columns:
            vals.append(pd.to_numeric(df_win[c], errors="coerce"))
    if not vals:
        return
    v = pd.concat(vals, axis=0).dropna()
    if v.empty:
        return
    vmin = float(v.min())
    vmax = float(v.max())
    pad = (vmax - vmin) * 0.08 if vmax > vmin else 0.01
    ax.set_ylim(vmin - pad, vmax + pad)


def plot_overlay(pair: str, df: pd.DataFrame, out_png: Path, show: bool) -> None:
    y_col = str(df.attrs.get("y_col", "value"))
    df = add_ma_band(df, y_col)

    fig = plt.figure(figsize=(12.5, 7.0))
    ax = fig.add_axes([0.08, 0.12, 0.68, 0.78])

    axp = fig.add_axes([0.80, 0.70, 0.16, 0.20])
    axp.set_title("Period", fontsize=10)

    periods = ["90d", "180d", "ALL"]
    rb = RadioButtons(axp, periods, active=periods.index(DEFAULT_PERIOD))

    # base plot + labels
    if pair == "jpy_thb":
        title = "JPY→THB Remittance Overlay"
        ylab = "THB per JPY"
        line_label = "JPY→THB (THB per JPY)"
    else:
        title = "JPY→USD Overlay"
        ylab = "USD per JPY"
        line_label = "JPY→USD (USD per JPY)"

    ax.plot(df["date"], df[y_col], label=line_label)
    ax.plot(df["date"], df["ma"], label=f"MA{MA_N}")
    ax.fill_between(df["date"], df["lower"], df["upper"], alpha=0.2, label="Band")

    # decision markers
    dec = df["combined_decision"].astype(str).str.upper()
    m_on = dec == "ON"
    m_warn = dec == "WARN"
    m_off = dec == "OFF"

    ax.scatter(df.loc[m_on, "date"], df.loc[m_on, y_col], s=25, label="ON")
    ax.scatter(df.loc[m_warn, "date"], df.loc[m_warn, y_col], s=40, marker="^", label="WARN")
    ax.scatter(df.loc[m_off, "date"], df.loc[m_off, y_col], s=40, marker="x", label="OFF")

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylab)
    ax.grid(True)
    ax.legend(loc="best")

    enable_scroll_zoom_and_pan(fig, ax)

    def apply_period(label: str) -> None:
        mask = _window_mask(df, label)
        df_win = df.loc[mask].copy()
        if df_win.empty:
            return
        ax.set_xlim(df_win["date"].min(), df_win["date"].max())
        _autoscale_y(ax, df_win, y_col)
        fig.canvas.draw_idle()

    rb.on_clicked(lambda label: apply_period(label))
    apply_period(DEFAULT_PERIOD)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=180)
    print(f"[OK] saved: {out_png}")

    if show:
        plt.show(block=True)
    else:
        plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", choices=["jpy_thb", "jpy_usd"], default="jpy_thb")
    ap.add_argument("--show", action="store_true", help="display window (manual use)")
    args = ap.parse_args()

    # In automation: avoid GUI backend
    if not args.show:
        matplotlib.use("Agg")

    pair = args.pair
    df = load_dashboard(pair)

    out_main = PAIR_PNG[pair]
    plot_overlay(pair, df, out_main, show=args.show)

    # backward compatibility for THB: also write legacy output name
    if pair == "jpy_thb":
        # copy-save (same figure already closed); easiest is to save again by re-plot quickly
        # keep it simple: re-render in Agg with same data
        matplotlib.use("Agg")
        df2 = df.copy()
        plot_overlay(pair, df2, LEGACY_THB_PNG, show=False)


if __name__ == "__main__":
    main()

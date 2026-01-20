# fx_remittance_overlay.py
# JPY→THB Remittance Overlay (from USDJPY × USDTHB)
#
# Features
# - Mouse wheel zoom (around cursor) + left-drag pan (backend independent)
# - Period selector: 90d / 180d / ALL
# - Saves a PNG under data/fx/
#
# Run:
#   .\.venv\Scripts\python.exe scripts\fx_remittance_overlay.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons


# ----------------------------
# Settings
# ----------------------------
IN_CSV = Path("data/fx/jpy_thb_remittance_dashboard.csv")
OUT_PNG = Path("data/fx/jpy_thb_remittance_overlay.png")

MA_N = 20
VOL_N = 20
BAND_K = 1.0

DEFAULT_PERIOD = "90d"  # '90d' | '180d' | 'ALL'


# ----------------------------
# Small helper: scroll zoom + drag pan
# ----------------------------
@dataclass
class _ViewState:
    press_event: object | None = None
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None


def enable_scroll_zoom_and_pan(fig: matplotlib.figure.Figure, ax: matplotlib.axes.Axes) -> None:
    """Enable wheel-zoom + left-button drag-pan for the given axes."""

    state = _ViewState()

    def _on_scroll(event):
        if event.inaxes != ax:
            return

        # Older matplotlib backends sometimes use event.step; newer use event.button
        step = getattr(event, "step", None)
        if step is None:
            if getattr(event, "button", None) == "up":
                step = 1
            elif getattr(event, "button", None) == "down":
                step = -1
            else:
                return

        # zoom factor
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

        new_xlim = _scale_range(cur_xlim[0], cur_xlim[1], xdata, scale_factor)
        new_ylim = _scale_range(cur_ylim[0], cur_ylim[1], ydata, scale_factor)

        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)
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

        dx = event.xdata - state.press_event.xdata if (event.xdata is not None and state.press_event.xdata is not None) else 0
        dy = event.ydata - state.press_event.ydata if (event.ydata is not None and state.press_event.ydata is not None) else 0

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

def _must_have_cols(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise SystemExit(f"[ERR] {IN_CSV} missing columns: {missing}")


def load_dashboard(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise SystemExit(f"[ERR] input not found: {csv_path}")

    df = pd.read_csv(csv_path)
    _must_have_cols(df, ["date", "jpy_thb"])

    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.sort_values("date").reset_index(drop=True)

    df["jpy_thb"] = pd.to_numeric(df["jpy_thb"], errors="coerce")
    df = df.dropna(subset=["jpy_thb"]).copy()

    # optional columns
    if "combined_decision" not in df.columns:
        df["combined_decision"] = "ON"
    if "combined_noise_prob" not in df.columns:
        df["combined_noise_prob"] = np.nan
    if "remit_note" not in df.columns:
        df["remit_note"] = ""

    return df


def add_ma_band(df: pd.DataFrame) -> pd.DataFrame:
    px = df["jpy_thb"].astype(float)
    ma = px.rolling(MA_N).mean()
    vol = px.pct_change().rolling(VOL_N).std()

    # band in price space (simple, consistent with your other scripts)
    band = ma * (vol * BAND_K)

    df = df.copy()
    df["ma"] = ma
    df["band"] = band
    df["upper"] = ma + band
    df["lower"] = ma - band

    return df


# ----------------------------
# Plot
# ----------------------------

def _date_to_num(dts: pd.Series) -> np.ndarray:
    # matplotlib works fine with datetime, but for xlim maths we keep numeric too
    return matplotlib.dates.date2num(pd.to_datetime(dts).dt.to_pydatetime())


def _window_mask(df: pd.DataFrame, period_label: str) -> pd.Series:
    if period_label.upper() == "ALL":
        return pd.Series([True] * len(df), index=df.index)
    if period_label.endswith("d"):
        n = int(period_label[:-1])
        last = df["date"].max()
        start = last - pd.Timedelta(days=n)
        return df["date"] >= start
    # fallback
    return pd.Series([True] * len(df), index=df.index)


def _autoscale_y(ax: matplotlib.axes.Axes, df_win: pd.DataFrame) -> None:
    cols = ["jpy_thb", "upper", "lower", "ma"]
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


def plot_remittance(df: pd.DataFrame) -> None:
    df = add_ma_band(df)

    # ---- layout: main axes + right side control panel
    fig = plt.figure(figsize=(12.5, 7.0))
    ax = fig.add_axes([0.08, 0.12, 0.68, 0.78])

    # Period selector panel
    axp = fig.add_axes([0.80, 0.70, 0.16, 0.20])
    axp.set_title("Period", fontsize=10)

    periods = ["90d", "180d", "ALL"]
    if DEFAULT_PERIOD not in periods:
        periods = [DEFAULT_PERIOD] + [p for p in periods if p != DEFAULT_PERIOD]

    rb = RadioButtons(axp, periods, active=periods.index(DEFAULT_PERIOD))

    # ---- base plot
    ax.plot(df["date"], df["jpy_thb"], label="JPY→THB (THB per JPY)")
    ax.plot(df["date"], df["ma"], label=f"MA{MA_N}")
    ax.fill_between(df["date"], df["lower"], df["upper"], alpha=0.2, label="Band")

    # decisions markers (optional)
    dec = df["combined_decision"].astype(str).str.upper()
    m_on = dec == "ON"
    m_warn = dec == "WARN"
    m_off = dec == "OFF"

    ax.scatter(df.loc[m_on, "date"], df.loc[m_on, "jpy_thb"], s=25, label="ON")
    ax.scatter(df.loc[m_warn, "date"], df.loc[m_warn, "jpy_thb"], s=40, marker="^", label="WARN")
    ax.scatter(df.loc[m_off, "date"], df.loc[m_off, "jpy_thb"], s=40, marker="x", label="OFF")

    ax.set_title("JPY→THB Remittance Overlay")
    ax.set_xlabel("Date")
    ax.set_ylabel("THB per JPY")
    ax.grid(True)
    ax.legend(loc="best")

    # ---- make interactive zoom/pan work
    enable_scroll_zoom_and_pan(fig, ax)

    # ---- period logic
    def apply_period(label: str) -> None:
        mask = _window_mask(df, label)
        df_win = df.loc[mask].copy()
        if df_win.empty:
            return

        # x-range
        left = df_win["date"].min()
        right = df_win["date"].max()
        ax.set_xlim(left, right)

        # y-range
        _autoscale_y(ax, df_win)

        # redraw
        fig.canvas.draw_idle()

    def _on_period_change(label: str) -> None:
        apply_period(label)

    rb.on_clicked(_on_period_change)

    # initial window
    apply_period(DEFAULT_PERIOD)

    # save
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PNG, dpi=180)
    print(f"[OK] saved: {OUT_PNG}")

    plt.show(block=True)


def main() -> None:
    df = load_dashboard(IN_CSV)
    plot_remittance(df)


if __name__ == "__main__":
    main()

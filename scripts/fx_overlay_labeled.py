import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================
# Settings
# ============================
PAIR_NAME = "USDJPY"
STOOQ_URL = "https://stooq.com/q/d/l/?s=usdjpy&i=d"

YEARS = 2
MA_N = 20
BAND_VOL_N = 20
BAND_K = 1.0

# 入力（あなたのパイプラインの出力に合わせる）
LABELED3_CSV = Path("data/fx/usd_jpy_miss_events_labeled3.csv")

# 出力（必ず残す）
OUT_DIR = Path("data/fx")
OUT_PNG = OUT_DIR / "usd_jpy_overlay_labeled.png"


# ============================
# Helpers
# ============================
def _require_file(p: Path):
    if not p.exists():
        raise SystemExit(f"[ERR] required file not found: {p}")


def _to_date_index(df: pd.DataFrame, col="Date") -> pd.DataFrame:
    df[col] = pd.to_datetime(df[col])
    df = df.sort_values(col).set_index(col)
    return df


# ============================
# Main
# ============================
def main():
    # --- load labeled miss table (3-class)
    _require_file(LABELED3_CSV)
    lab = pd.read_csv(LABELED3_CSV)
    if "miss_date" not in lab.columns:
        raise SystemExit("[ERR] labeled3 csv must have 'miss_date' column")

    # class3 を使う（無ければ class を使う）
    if "class3" in lab.columns:
        cls_col = "class3"
    elif "class" in lab.columns:
        cls_col = "class"
    else:
        raise SystemExit("[ERR] labeled3 csv must have 'class3' or 'class' column")

    lab["miss_date"] = pd.to_datetime(lab["miss_date"]).dt.date

    # --- load price from stooq
    try:
        df = pd.read_csv(STOOQ_URL)
    except Exception as e:
        raise SystemExit(f"[ERR] failed to read stooq csv: {e}")

    if "Date" not in df.columns or "Close" not in df.columns:
        raise SystemExit("[ERR] stooq csv must have Date, Close columns")

    df = _to_date_index(df, "Date")

    # --- limit to last N years
    df = df[df.index >= (df.index.max() - pd.DateOffset(years=YEARS))]
    px = df["Close"].astype(float)

    # --- forecast baseline (MA)
    pred = px.rolling(MA_N).mean()

    # --- forecast band (volatility of returns)
    vol = px.pct_change().rolling(BAND_VOL_N).std()
    band = pred * vol * BAND_K
    upper = pred + band
    lower = pred - band

    # --- miss definition (same as fx_overlay style)
    # direction miss
    actual_dir = np.sign(px.diff())
    pred_dir = np.sign(pred.diff())
    direction_match = (actual_dir == pred_dir)

    # error miss (outside band)
    err = (px - pred).abs()
    tol = band.fillna(0.0)
    error_match = err <= tol

    # miss mask: either direction mismatch OR outside band (あなたの好みに合わせて調整可)
    miss_mask = (~direction_match) | (~error_match)

    # --- align labeled miss dates with plot range
    px_dates = set(px.index.date)
    lab = lab[lab["miss_date"].isin(px_dates)].copy()

    # miss日だけに絞る（念のため）
    lab = lab[lab["miss_date"].isin(set(px.index.date[pd.Series(miss_mask, index=px.index).fillna(False).values]))].copy()

    # --- build scatter groups
    def pick_y(d):
        # d: python date
        dt = pd.to_datetime(d)
        if dt in px.index:
            return float(px.loc[dt])
        # もし休日などでズレたら近い営業日（前方優先）
        nearest = px.index[px.index.get_indexer([dt], method="nearest")]
        return float(px.loc[nearest[0]])

    lab["y"] = [pick_y(d) for d in lab["miss_date"]]

    # class colors/markers（色はmatplotlibデフォルト。markerで判別）
    # macro_hit: o, regime_break: ^, noise: .
    marker_map = {
        "macro_hit": "o",
        "regime_break": "^",
        "noise": ".",
    }

    # 未知クラスは x
    lab["marker"] = lab[cls_col].map(marker_map).fillna("x")

    # ============================
    # Plot
    # ============================
    plt.figure(figsize=(14, 7))
    plt.title(f"{PAIR_NAME}: Actual vs Forecast (MA{MA_N}) + Miss (labeled)")

    # lines
    plt.plot(px.index, px.values, label=f"Actual {PAIR_NAME}")
    plt.plot(pred.index, pred.values, label=f"Forecast baseline (MA{MA_N})")
    plt.fill_between(upper.index, lower.values, upper.values, alpha=0.2, label="Forecast band")

    # scatter by class
    for cls in ["macro_hit", "regime_break", "noise"]:
        sub = lab[lab[cls_col] == cls]
        if sub.empty:
            continue
        xs = [pd.to_datetime(d) for d in sub["miss_date"]]
        ys = sub["y"].astype(float).values
        plt.scatter(xs, ys, s=40 if cls != "noise" else 20, marker=marker_map.get(cls, "x"), label=f"Miss: {cls}")

    plt.grid(True)
    plt.legend()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150)

    # 必ずユーザーに分かるように出す
    print("[OK] overlay labeled plot generated")
    print(f" - saved: {OUT_PNG}")

    # 画面表示（VSCode/ローカルなら出る）
    plt.show()


if __name__ == "__main__":
    main()

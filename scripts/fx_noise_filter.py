import numpy as np
import pandas as pd
from pathlib import Path

# ============================
# Settings
# ============================
PAIR_NAME = "USDJPY"
STOOQ_URL = "https://stooq.com/q/d/l/?s=usdjpy&i=d"

YEARS = 2
MA_N = 20
VOL_N = 20

LABELED3_CSV = Path("data/fx/usd_jpy_miss_events_labeled3.csv")
OUT_CSV = Path("data/fx/usd_jpy_noise_forecast.csv")

# thresholds (決め打ち・後で調整可)
NOISE_SCORE_OFF = 0.60   # これ以上なら trade OFF
NOISE_SCORE_WARN = 0.40  # これ以上なら注意

# ============================
# Helpers
# ============================
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

# ============================
# Main
# ============================
def main():
    # ---- load labeled miss info
    lab = pd.read_csv(LABELED3_CSV)
    lab["miss_date"] = pd.to_datetime(lab["miss_date"]).dt.date

    # ---- load price
    px = pd.read_csv(STOOQ_URL)
    px["Date"] = pd.to_datetime(px["Date"])
    px = px.sort_values("Date").set_index("Date")
    px = px[px.index >= (px.index.max() - pd.DateOffset(years=YEARS))]
    price = px["Close"].astype(float)

    # ---- indicators
    ret = price.pct_change()
    vol = ret.rolling(VOL_N).std()

    vol_z = (vol - vol.rolling(VOL_N).mean()) / vol.rolling(VOL_N).std()
    vol_jump = vol_z > 1.0

    ma = price.rolling(MA_N).mean()
    band = ma * vol
    band_expansion = band.pct_change() > 0.3

    actual_dir = np.sign(price.diff())
    pred_dir = np.sign(ma.diff())
    dir_mismatch = actual_dir != pred_dir

    # ---- miss streak
    miss_days = set(lab["miss_date"].tolist())
    streak = []
    s = 0
    for d in price.index.date:
        if d in miss_days:
            s += 1
        else:
            s = 0
        streak.append(s)
    streak = pd.Series(streak, index=price.index)

    # ---- regime_break history
    regime_days = set(lab[lab["class3"] == "regime_break"]["miss_date"].tolist())
    recent_regime = price.index.date
    recent_regime = pd.Series(
        [1 if d in regime_days else 0 for d in recent_regime],
        index=price.index
    ).rolling(3).max() > 0

    # ---- noise score (前日情報のみ)
    score = (
        0.30 * vol_jump.shift(1).fillna(False).astype(int) +
        0.20 * band_expansion.shift(1).fillna(False).astype(int) +
        0.20 * dir_mismatch.shift(1).fillna(False).astype(int) +
        0.20 * (streak.shift(1).fillna(0) >= 2).astype(int) +
        0.10 * recent_regime.shift(1).fillna(False).astype(int)
    )

    noise_prob = sigmoid(3 * (score - 0.5))

    # ---- decision
    decision = []
    for p in noise_prob:
        if p >= NOISE_SCORE_OFF:
            decision.append("OFF")
        elif p >= NOISE_SCORE_WARN:
            decision.append("WARN")
        else:
            decision.append("ON")

    out = pd.DataFrame({
        "date": price.index.date,
        "noise_score": score.values,
        "noise_prob": noise_prob.values,
        "decision": decision,
    })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print("[OK] noise forecast generated")
    print(f" - {OUT_CSV}")
    print(out.tail(10))

if __name__ == "__main__":
    main()

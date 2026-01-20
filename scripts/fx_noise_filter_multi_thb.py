import numpy as np
import pandas as pd
from pathlib import Path

# ============================
# Settings
# ============================
YEARS = 2

MA_N = 20
VOL_N = 20
BAND_K = 1.0

# noise score thresholds
NOISE_PROB_OFF = 0.60
NOISE_PROB_WARN = 0.40

# pairs: stooq symbol (daily)
PAIRS = {
    "USDJPY": "usdjpy",
    "USDTHB": "usdthb",
}

OUT_DIR = Path("data/fx")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================
# Helpers
# ============================
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def load_stooq_daily(symbol: str, years: int = 2) -> pd.Series:
    """
    Fetch daily close from Stooq.
    URL format: https://stooq.com/q/d/l/?s=<symbol>&i=d
    Returns: pd.Series with DatetimeIndex, name='Close'
    """
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    df = pd.read_csv(url)
    if "Date" not in df.columns or "Close" not in df.columns:
        raise RuntimeError(f"Stooq response missing columns for symbol={symbol}")

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")

    # limit to last N years
    df = df[df.index >= (df.index.max() - pd.DateOffset(years=years))]
    px = df["Close"].astype(float).rename("Close")
    return px

def compute_miss_mask(price: pd.Series) -> pd.Series:
    """
    Define "miss day" using the same spirit as your overlay:
    pred = MA20, band = pred * vol * BAND_K, miss if abs(price - pred) > band
    """
    pred = price.rolling(MA_N).mean()
    vol = price.pct_change().rolling(VOL_N).std()
    band = (pred * vol * BAND_K).fillna(0.0)

    abs_err = (price - pred).abs()
    miss = (abs_err > band) & pred.notna()
    return miss.rename("miss")

def noise_forecast_from_price(price: pd.Series) -> pd.DataFrame:
    """
    Uses only price-derived features (no events needed).
    Outputs per-date: noise_score, noise_prob, decision.
    """
    ret = price.pct_change()
    vol = ret.rolling(VOL_N).std()

    # vol jump (zscore-ish)
    vol_mean = vol.rolling(VOL_N).mean()
    vol_std = vol.rolling(VOL_N).std()
    vol_z = (vol - vol_mean) / vol_std
    vol_jump = (vol_z > 1.0).fillna(False)

    # band expansion
    pred = price.rolling(MA_N).mean()
    band = (pred * vol * BAND_K)
    band_expansion = (band.pct_change() > 0.3).fillna(False)

    # direction mismatch vs MA slope
    actual_dir = np.sign(price.diff())
    pred_dir = np.sign(pred.diff())
    dir_mismatch = (actual_dir != pred_dir).fillna(False)

    # miss streak
    miss = compute_miss_mask(price).astype(bool)
    s = 0
    streak = []
    for v in miss.values:
        s = (s + 1) if v else 0
        streak.append(s)
    streak = pd.Series(streak, index=price.index)

    # recent "mini regime" proxy: miss in last 3 days
    recent_miss = miss.rolling(3).max().fillna(False)

    # ---- score uses ONLY t-1 info (shift(1))
    vj = vol_jump.shift(1).fillna(False).astype(bool)
    be = band_expansion.shift(1).fillna(False).astype(bool)
    dm = dir_mismatch.shift(1).fillna(False).astype(bool)
    st = (streak.shift(1).fillna(0).astype(float) >= 2)
    rm = recent_miss.shift(1).fillna(False).astype(bool)

    score = (
        0.30 * vj.astype(int) +
        0.20 * be.astype(int) +
        0.20 * dm.astype(int) +
        0.20 * st.astype(int) +
        0.10 * rm.astype(int)
    )

    # prob (center 0.5)
    noise_prob = sigmoid(3 * (score - 0.5))

    decision = np.where(noise_prob >= NOISE_PROB_OFF, "OFF",
               np.where(noise_prob >= NOISE_PROB_WARN, "WARN", "ON"))

    out = pd.DataFrame({
        "date": price.index.date,
        "noise_score": score.values,
        "noise_prob": noise_prob,
        "decision": decision,
        "close": price.values,
    })

    return out.dropna(subset=["noise_score"])

def combine_usdjpy_usdthb(usdjpy: pd.DataFrame, usdthb: pd.DataFrame) -> pd.DataFrame:
    """
    Build remittance-focused view:
      - JPYTHB (THB per JPY) synthetic = USDTHB / USDJPY
      - combined_noise_prob = max(prob_jpy, prob_thb)  (conservative)
      - combined_decision   derived from combined_noise_prob
    """
    a = usdjpy[["date", "noise_prob", "decision", "close"]].rename(
        columns={"noise_prob": "usd_jpy_noise_prob", "decision": "usd_jpy_decision", "close": "usd_jpy_close"}
    )
    b = usdthb[["date", "noise_prob", "decision", "close"]].rename(
        columns={"noise_prob": "usd_thb_noise_prob", "decision": "usd_thb_decision", "close": "usd_thb_close"}
    )

    m = a.merge(b, on="date", how="inner")

    # synthetic cross
    # USDJPY = JPY per USD, USDTHB = THB per USD
    # THB per JPY = (THB/USD) / (JPY/USD) = USDTHB / USDJPY
    m["jpy_thb"] = m["usd_thb_close"] / m["usd_jpy_close"]

    # conservative union risk
    m["combined_noise_prob"] = m[["usd_jpy_noise_prob", "usd_thb_noise_prob"]].max(axis=1)

    m["combined_decision"] = np.where(
        m["combined_noise_prob"] >= NOISE_PROB_OFF, "OFF",
        np.where(m["combined_noise_prob"] >= NOISE_PROB_WARN, "WARN", "ON")
    )

    # handy note for remittance
    # - OFF: avoid / split remittance
    # - WARN: split or smaller size
    # - ON: normal
    m["remit_note"] = np.where(
        m["combined_decision"] == "OFF", "split_or_wait",
        np.where(m["combined_decision"] == "WARN", "split_or_small", "normal")
    )

    return m

def main():
    results = {}
    for name, sym in PAIRS.items():
        try:
            price = load_stooq_daily(sym, years=YEARS)
        except Exception as e:
            raise SystemExit(
                f"[ERR] failed to load {name} via Stooq (symbol='{sym}').\n"
                f"      error: {e}\n"
                f"      If Stooq doesn't have this pair, tell me and I'll switch loader (Yahoo/AlphaVantage)."
            )

        out = noise_forecast_from_price(price)
        results[name] = out

        out_path = OUT_DIR / f"{sym}_noise_forecast.csv"
        out.to_csv(out_path, index=False, encoding="utf-8")
        print(f"[OK] saved {name} -> {out_path}")

    combo = combine_usdjpy_usdthb(results["USDJPY"], results["USDTHB"])
    combo_path = OUT_DIR / "jpy_thb_remittance_dashboard.csv"
    combo.to_csv(combo_path, index=False, encoding="utf-8")
    print(f"[OK] saved JPYTHB remittance dashboard -> {combo_path}")

    # show last 10 lines
    print("\n[TAIL] remittance dashboard (last 10)")
    cols = ["date", "jpy_thb", "usd_jpy_decision", "usd_thb_decision", "combined_decision", "combined_noise_prob", "remit_note"]
    print(combo[cols].tail(10).to_string(index=False))

if __name__ == "__main__":
    main()

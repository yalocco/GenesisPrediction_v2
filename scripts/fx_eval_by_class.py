import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

PAIR_NAME = "USDJPY"
STOOQ_URL = "https://stooq.com/q/d/l/?s=usdjpy&i=d"

YEARS = 2
MA_N = 20
BAND_VOL_N = 20
BAND_K = 1.0

LABELED3_CSV = Path("data/fx/usd_jpy_miss_events_labeled3.csv")
OUT_CSV = Path("data/fx/usd_jpy_eval_by_class.csv")

def main():
    if not LABELED3_CSV.exists():
        raise SystemExit(f"[ERR] not found: {LABELED3_CSV}")

    lab = pd.read_csv(LABELED3_CSV)
    if "miss_date" not in lab.columns:
        raise SystemExit("[ERR] labeled3 csv must have 'miss_date' column")

    cls_col = "class3" if "class3" in lab.columns else ("class" if "class" in lab.columns else None)
    if not cls_col:
        raise SystemExit("[ERR] labeled3 csv must have 'class3' or 'class' column")

    lab["miss_date"] = pd.to_datetime(lab["miss_date"]).dt.date

    # price
    df = pd.read_csv(STOOQ_URL)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    df = df[df.index >= (df.index.max() - pd.DateOffset(years=YEARS))]
    px = df["Close"].astype(float)

    pred = px.rolling(MA_N).mean()
    vol = px.pct_change().rolling(BAND_VOL_N).std()
    band = pred * vol * BAND_K
    tol = band.fillna(0.0)

    # metrics per day
    actual_dir = np.sign(px.diff())
    pred_dir = np.sign(pred.diff())
    direction_match = (actual_dir == pred_dir)

    abs_err = (px - pred).abs()
    error_match = abs_err <= tol

    # unify into a per-date frame
    m = pd.DataFrame({
        "date": px.index.date,
        "px": px.values,
        "pred": pred.values,
        "abs_err": abs_err.values,
        "band": tol.values,
        "direction_match": direction_match.values,
        "error_match": error_match.values,
    }).dropna(subset=["pred"])

    # attach class labels only on miss days we classified
    lab_small = lab[["miss_date", cls_col]].copy()
    lab_small = lab_small.rename(columns={"miss_date": "date", cls_col: "class3"})

    mm = m.merge(lab_small, on="date", how="left")

    # We evaluate two things:
    # 1) overall performance on all days
    # 2) performance specifically on labeled miss days (class3 != NaN)
    def summarize(df, name):
        out = {
            "scope": name,
            "days": len(df),
            "direction_match_rate": float(np.nanmean(df["direction_match"])) if len(df) else np.nan,
            "error_match_rate": float(np.nanmean(df["error_match"])) if len(df) else np.nan,
            "mean_abs_err": float(np.nanmean(df["abs_err"])) if len(df) else np.nan,
            "mean_band": float(np.nanmean(df["band"])) if len(df) else np.nan,
            "err_over_band_mean": float(np.nanmean(df["abs_err"] / df["band"].replace(0, np.nan))) if len(df) else np.nan,
        }
        return out

    rows = []
    rows.append(summarize(mm, "ALL_DAYS"))

    labeled = mm[mm["class3"].notna()].copy()
    rows.append(summarize(labeled, "LABELED_MISS_DAYS"))

    for cls in ["macro_hit", "regime_break", "noise"]:
        sub = labeled[labeled["class3"] == cls]
        rows.append(summarize(sub, f"MISS_{cls}"))

    out_df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print("[OK] evaluation saved")
    print(f" - {OUT_CSV}")
    print(out_df.to_string(index=False))

if __name__ == "__main__":
    main()

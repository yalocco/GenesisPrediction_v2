# scripts/fx_remittance_today.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FX_DIR = ROOT / "data" / "fx"

USDJPY_CSV = FX_DIR / "usdjpy.csv"
USDTHB_CSV = FX_DIR / "usdthb.csv"
DASH_CSV = FX_DIR / "jpy_thb_remittance_dashboard.csv"

# optional forecast files (best effort)
USDJPY_FORE = FX_DIR / "usdjpy_noise_forecast.csv"
USDTHB_FORE = FX_DIR / "usdthb_noise_forecast.csv"


def _load_rates(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing rates: {path}")
    df = pd.read_csv(path)
    if "date" not in df.columns or "rate" not in df.columns:
        raise ValueError(f"{name} must have columns: date,rate -> {path}")
    df = df[["date", "rate"]].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df.dropna().sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


def _load_forecast(path: Path) -> Optional[pd.Series]:
    """
    Expect CSV with columns: date, prob (or probability/noise_prob).
    Returns Series indexed by date(str)->prob(float).
    """
    if not path.exists():
        return None
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    if "date" not in cols:
        return None
    dcol = cols["date"]
    pcol = None
    for key in ("prob", "probability", "noise_prob", "noise_probability"):
        if key in cols:
            pcol = cols[key]
            break
    if pcol is None:
        return None

    s = df[[dcol, pcol]].copy()
    s[dcol] = pd.to_datetime(s[dcol], errors="coerce").dt.strftime("%Y-%m-%d")
    s[pcol] = pd.to_numeric(s[pcol], errors="coerce")
    s = s.dropna()
    ser = pd.Series(s[pcol].values, index=s[dcol].values)
    return ser


def _decision(prob: float) -> str:
    # matches your observed behavior:
    # OFF around 0.71, WARN around 0.57, ON around 0.23
    if prob <= 0.35:
        return "ON"
    if prob <= 0.65:
        return "WARN"
    return "OFF"


def _note(dec: str) -> str:
    if dec == "ON":
        return "send"
    if dec == "WARN":
        return "split_or_small"
    return "split_or_wait"


def _build_dashboard_until(latest: str) -> pd.DataFrame:
    usdjpy = _load_rates(USDJPY_CSV, "USDJPY")
    usdthb = _load_rates(USDTHB_CSV, "USDTHB")

    last_common = min(usdjpy["date"].iloc[-1], usdthb["date"].iloc[-1])
    if latest > last_common:
        # clamp: you asked a date newer than available rates
        latest = last_common

    # load existing dashboard if present
    if DASH_CSV.exists():
        dash = pd.read_csv(DASH_CSV)
    else:
        dash = pd.DataFrame(columns=[
            "date",
            "usd_jpy_noise_prob","usd_jpy_decision","usd_jpy_close",
            "usd_thb_noise_prob","usd_thb_decision","usd_thb_close",
            "jpy_thb",
            "combined_noise_prob","combined_decision","remit_note"
        ])

    # normalize existing
    if "date" not in dash.columns:
        dash["date"] = []

    dash["date"] = pd.to_datetime(dash["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    dash = dash.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # determine start date to append
    start = dash["date"].iloc[-1] if len(dash) else None

    # join closes for all dates up to latest
    m = usdjpy.merge(usdthb, on="date", suffixes=("_jpy", "_thb"))
    m = m[m["date"] <= latest].copy()
    m.rename(columns={"rate_jpy": "usd_jpy_close", "rate_thb": "usd_thb_close"}, inplace=True)
    m["jpy_thb"] = (m["usd_thb_close"] / m["usd_jpy_close"]).astype(float)

    # forecasts best-effort (fallback to 0.5)
    f_jpy = _load_forecast(USDJPY_FORE)
    f_thb = _load_forecast(USDTHB_FORE)

    def prob_for(date: str, f: Optional[pd.Series]) -> float:
        if f is None:
            return 0.5
        v = f.get(date)
        if v is None:
            return 0.5
        try:
            return float(v)
        except Exception:
            return 0.5

    # fill rows
    rows = []
    for _, r in m.iterrows():
        d = r["date"]
        if start is not None and d <= start:
            continue

        pj = prob_for(d, f_jpy)
        pt = prob_for(d, f_thb)
        dj = _decision(pj)
        dt = _decision(pt)

        combined = max(pj, pt)  # conservative (matches your past combined==usd_jpy often)
        dcomb = _decision(combined)

        rows.append({
            "date": d,
            "usd_jpy_noise_prob": pj,
            "usd_jpy_decision": dj,
            "usd_jpy_close": float(r["usd_jpy_close"]),
            "usd_thb_noise_prob": pt,
            "usd_thb_decision": dt,
            "usd_thb_close": float(r["usd_thb_close"]),
            "jpy_thb": float(r["jpy_thb"]),
            "combined_noise_prob": combined,
            "combined_decision": dcomb,
            "remit_note": _note(dcomb),
        })

    if rows:
        dash = pd.concat([dash, pd.DataFrame(rows)], ignore_index=True)

    # keep last per date, sorted
    dash = dash.sort_values("date").groupby("date", as_index=False).tail(1)
    dash = dash.sort_values("date").reset_index(drop=True)

    # enforce column order
    cols = [
        "date",
        "usd_jpy_noise_prob","usd_jpy_decision","usd_jpy_close",
        "usd_thb_noise_prob","usd_thb_decision","usd_thb_close",
        "jpy_thb",
        "combined_noise_prob","combined_decision","remit_note"
    ]
    for c in cols:
        if c not in dash.columns:
            dash[c] = None
    dash = dash[cols]

    DASH_CSV.parent.mkdir(parents=True, exist_ok=True)
    dash.to_csv(DASH_CSV, index=False)
    return dash


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    ap.add_argument("--recent", type=int, default=0)
    args = ap.parse_args()

    # clamp date to available rates common last day
    usdjpy = _load_rates(USDJPY_CSV, "USDJPY")
    usdthb = _load_rates(USDTHB_CSV, "USDTHB")
    last_common = min(usdjpy["date"].iloc[-1], usdthb["date"].iloc[-1])
    target = min(args.date, last_common)

    dash = _build_dashboard_until(target)

    # print today line (target)
    row = dash[dash["date"] == target]
    if row.empty:
        print(f"{args.date} | decision=OFF | noise=0.500 | USDJPY=0.500 USDTHB=0.500 | note=split_or_wait | action=wait | reason=rate not available")
        return 0

    r = row.iloc[-1]
    decision = r["combined_decision"]
    noise = float(r["combined_noise_prob"])
    uj = float(r["usd_jpy_noise_prob"])
    ut = float(r["usd_thb_noise_prob"])
    note = r["remit_note"]

    # action text aligned with prior logs
    action = "wait" if decision == "OFF" else ("split_or_small" if decision == "WARN" else "send")
    reason = "ノイズ高水準のため見送り推奨" if decision == "OFF" else ("軽度WARNのため分割または少額推奨" if decision == "WARN" else "低ノイズのため送金可")

    print(f"{args.date} | decision={decision} | noise={noise:.3f} | USDJPY={uj:.3f} USDTHB={ut:.3f} | note={note} | action={action} | reason={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

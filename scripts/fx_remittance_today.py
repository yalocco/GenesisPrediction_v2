# scripts/fx_remittance_today.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FX_DIR = ROOT / "data" / "fx"

# rates (materialized by fx_materialize_rates.py)
USDJPY_CSV = FX_DIR / "usdjpy.csv"
USDTHB_CSV = FX_DIR / "usdthb.csv"

# legacy dashboard path (must keep for existing pipeline)
LEGACY_THB_DASH = FX_DIR / "jpy_thb_remittance_dashboard.csv"

# new normalized dashboard location (pair-based)
DASH_DIR = FX_DIR / "dashboard"
DASH_DIR.mkdir(parents=True, exist_ok=True)

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
    return pd.Series(s[pcol].values, index=s[dcol].values)


def _decision(prob: float) -> str:
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


def _prob_for(date: str, f: Optional[pd.Series]) -> float:
    if f is None:
        return 0.5
    v = f.get(date)
    if v is None:
        return 0.5
    try:
        return float(v)
    except Exception:
        return 0.5


# ----------------------------
# Pair engines
# ----------------------------
def _pair_last_common(pair: str, usdjpy: pd.DataFrame, usdthb: Optional[pd.DataFrame]) -> str:
    if pair == "jpy_thb":
        assert usdthb is not None
        return min(usdjpy["date"].iloc[-1], usdthb["date"].iloc[-1])
    if pair == "jpy_usd":
        return usdjpy["date"].iloc[-1]
    raise ValueError(f"unknown pair: {pair}")


def _pair_dashboard_path(pair: str) -> Path:
    return DASH_DIR / f"{pair}_dashboard.csv"


def _empty_dashboard(pair: str) -> pd.DataFrame:
    if pair == "jpy_thb":
        return pd.DataFrame(
            columns=[
                "date",
                "usd_jpy_noise_prob",
                "usd_jpy_decision",
                "usd_jpy_close",
                "usd_thb_noise_prob",
                "usd_thb_decision",
                "usd_thb_close",
                "jpy_thb",
                "combined_noise_prob",
                "combined_decision",
                "remit_note",
            ]
        )
    if pair == "jpy_usd":
        return pd.DataFrame(
            columns=[
                "date",
                "usd_jpy_noise_prob",
                "usd_jpy_decision",
                "usd_jpy_close",
                "jpy_usd",
                "combined_noise_prob",
                "combined_decision",
                "remit_note",
            ]
        )
    raise ValueError(f"unknown pair: {pair}")


def _load_existing_dashboard(pair: str) -> pd.DataFrame:
    new_path = _pair_dashboard_path(pair)

    if pair == "jpy_thb":
        if LEGACY_THB_DASH.exists():
            return pd.read_csv(LEGACY_THB_DASH)
        if new_path.exists():
            return pd.read_csv(new_path)
        return _empty_dashboard(pair)

    if pair == "jpy_usd":
        if new_path.exists():
            return pd.read_csv(new_path)
        return _empty_dashboard(pair)

    raise ValueError(f"unknown pair: {pair}")


def _normalize_existing(dash: pd.DataFrame) -> pd.DataFrame:
    if "date" not in dash.columns:
        dash["date"] = []
    dash["date"] = pd.to_datetime(dash["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    dash = dash.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return dash


def _append_rows_safely(dash: pd.DataFrame, rows: list[dict]) -> pd.DataFrame:
    """
    pandas FutureWarning 対策：
    - 既存dashが空なら、concatせず rows で新規作成
    - 空でないなら concat
    """
    if not rows:
        return dash
    new_df = pd.DataFrame(rows)
    if dash is None or dash.empty:
        return new_df.reset_index(drop=True)
    return pd.concat([dash, new_df], ignore_index=True)


def _append_dashboard_until(pair: str, latest: str) -> pd.DataFrame:
    usdjpy = _load_rates(USDJPY_CSV, "USDJPY")
    usdthb = _load_rates(USDTHB_CSV, "USDTHB") if pair == "jpy_thb" else None

    last_common = _pair_last_common(pair, usdjpy, usdthb)
    if latest > last_common:
        latest = last_common  # clamp

    dash = _normalize_existing(_load_existing_dashboard(pair))
    start = dash["date"].iloc[-1] if len(dash) else None

    f_jpy = _load_forecast(USDJPY_FORE)
    f_thb = _load_forecast(USDTHB_FORE) if pair == "jpy_thb" else None

    rows: list[dict] = []

    if pair == "jpy_thb":
        assert usdthb is not None
        m = usdjpy.merge(usdthb, on="date", suffixes=("_jpy", "_thb"))
        m = m[m["date"] <= latest].copy()
        m.rename(columns={"rate_jpy": "usd_jpy_close", "rate_thb": "usd_thb_close"}, inplace=True)
        m["jpy_thb"] = (m["usd_thb_close"] / m["usd_jpy_close"]).astype(float)

        for _, r in m.iterrows():
            d = r["date"]
            if start is not None and d <= start:
                continue

            pj = _prob_for(d, f_jpy)
            pt = _prob_for(d, f_thb)
            dj = _decision(pj)
            dt = _decision(pt)

            combined = max(pj, pt)
            dcomb = _decision(combined)

            rows.append(
                {
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
                }
            )

        cols = [
            "date",
            "usd_jpy_noise_prob",
            "usd_jpy_decision",
            "usd_jpy_close",
            "usd_thb_noise_prob",
            "usd_thb_decision",
            "usd_thb_close",
            "jpy_thb",
            "combined_noise_prob",
            "combined_decision",
            "remit_note",
        ]

    elif pair == "jpy_usd":
        m = usdjpy[usdjpy["date"] <= latest].copy()
        m.rename(columns={"rate": "usd_jpy_close"}, inplace=True)
        m["jpy_usd"] = (1.0 / m["usd_jpy_close"]).astype(float)

        for _, r in m.iterrows():
            d = r["date"]
            if start is not None and d <= start:
                continue

            pj = _prob_for(d, f_jpy)
            dj = _decision(pj)

            rows.append(
                {
                    "date": d,
                    "usd_jpy_noise_prob": pj,
                    "usd_jpy_decision": dj,
                    "usd_jpy_close": float(r["usd_jpy_close"]),
                    "jpy_usd": float(r["jpy_usd"]),
                    "combined_noise_prob": pj,
                    "combined_decision": dj,
                    "remit_note": _note(dj),
                }
            )

        cols = [
            "date",
            "usd_jpy_noise_prob",
            "usd_jpy_decision",
            "usd_jpy_close",
            "jpy_usd",
            "combined_noise_prob",
            "combined_decision",
            "remit_note",
        ]
    else:
        raise ValueError(f"unknown pair: {pair}")

    dash = _append_rows_safely(dash, rows)

    # keep last per date, sorted
    if not dash.empty:
        dash = dash.sort_values("date").groupby("date", as_index=False).tail(1)
        dash = dash.sort_values("date").reset_index(drop=True)

    # enforce column order
    for c in cols:
        if c not in dash.columns:
            dash[c] = None
    dash = dash[cols]

    # write pair-based
    out_pair = _pair_dashboard_path(pair)
    out_pair.parent.mkdir(parents=True, exist_ok=True)
    dash.to_csv(out_pair, index=False)

    # backward compatibility
    if pair == "jpy_thb":
        dash.to_csv(LEGACY_THB_DASH, index=False)

    return dash


def _print_today_line(pair: str, args_date: str, target: str, dash: pd.DataFrame) -> int:
    row = dash[dash["date"] == target]
    if row.empty:
        if pair == "jpy_thb":
            print(
                f"{args_date} | decision=OFF | noise=0.500 | USDJPY=0.500 USDTHB=0.500 | "
                f"note=split_or_wait | action=wait | reason=rate not available"
            )
        else:
            print(
                f"{args_date} | decision=OFF | noise=0.500 | USDJPY=0.500 | "
                f"note=split_or_wait | action=wait | reason=rate not available"
            )
        return 0

    r = row.iloc[-1]
    decision = str(r["combined_decision"])
    noise = float(r["combined_noise_prob"])
    note = str(r["remit_note"])

    uj = float(r["usd_jpy_noise_prob"])
    action = "wait" if decision == "OFF" else ("split_or_small" if decision == "WARN" else "send")
    reason = (
        "ノイズ高水準のため見送り推奨"
        if decision == "OFF"
        else ("軽度WARNのため分割または少額推奨" if decision == "WARN" else "低ノイズのため送金可")
    )

    if pair == "jpy_thb":
        ut = float(r["usd_thb_noise_prob"])
        print(
            f"{args_date} | decision={decision} | noise={noise:.3f} | "
            f"USDJPY={uj:.3f} USDTHB={ut:.3f} | note={note} | action={action} | reason={reason}"
        )
    else:
        print(
            f"{args_date} | decision={decision} | noise={noise:.3f} | "
            f"USDJPY={uj:.3f} | note={note} | action={action} | reason={reason}"
        )

    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", choices=["jpy_thb", "jpy_usd"], default="jpy_thb")
    ap.add_argument("--date", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    ap.add_argument("--recent", type=int, default=0)  # reserved (compat)
    args = ap.parse_args()

    pair = args.pair

    usdjpy = _load_rates(USDJPY_CSV, "USDJPY")
    usdthb = _load_rates(USDTHB_CSV, "USDTHB") if pair == "jpy_thb" else None

    last_common = _pair_last_common(pair, usdjpy, usdthb)
    target = min(args.date, last_common)

    dash = _append_dashboard_until(pair, target)
    return _print_today_line(pair, args.date, target, dash)


if __name__ == "__main__":
    raise SystemExit(main())

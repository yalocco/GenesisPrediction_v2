# scripts/fx_remittance_dashboard_update.py
"""
fx_remittance_dashboard_update.py

目的:
- data/fx/usdjpy.csv と data/fx/usdthb.csv から
  data/fx/jpy_thb_remittance_dashboard.csv を target_date まで進める。

出力:
- data/fx/jpy_thb_remittance_dashboard.csv (追記)
- 進められない場合は exit!=0（overlay 生成を止めるため）

注意:
- ノイズは noise_forecast.csv から読む（無ければ 0.5 として WARN 扱いになりやすい）
- THB per JPY = (USDTHB rate) / (USDJPY rate)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date as _date
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "fx"

USDJPY_CSV = DATA_DIR / "usdjpy.csv"
USDTHB_CSV = DATA_DIR / "usdthb.csv"
DASH_CSV = DATA_DIR / "jpy_thb_remittance_dashboard.csv"

USDJPY_NOISE = DATA_DIR / "usdjpy_noise_forecast.csv"
USDTHB_NOISE = DATA_DIR / "usdthb_noise_forecast.csv"

ON_TH = 0.45
WARN_TH = 0.60


def _read_last_date(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        if df.empty:
            return None
        # dashboard is no-header CSV in your current data; handle both
        if "date" in [c.lower() for c in df.columns]:
            dcol = df.columns[[c.lower() for c in df.columns].index("date")]
            s = pd.to_datetime(df[dcol], errors="coerce").dropna()
            if s.empty:
                return None
            return s.max().strftime("%Y-%m-%d")
        # no header -> first column is date
        s = pd.to_datetime(df.iloc[:, 0], errors="coerce").dropna()
        if s.empty:
            return None
        return s.max().strftime("%Y-%m-%d")
    except Exception:
        return None


def _load_rates(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required rates file: {path}")
    df = pd.read_csv(path)
    if not {"date", "rate"}.issubset({c.lower() for c in df.columns}):
        raise ValueError(f"Rates CSV must have columns date,rate: {path}")
    dcol = df.columns[[c.lower() for c in df.columns].index("date")]
    rcol = df.columns[[c.lower() for c in df.columns].index("rate")]
    out = df[[dcol, rcol]].copy()
    out.columns = ["date", "rate"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["rate"] = pd.to_numeric(out["rate"], errors="coerce")
    out = out.dropna(subset=["date", "rate"]).sort_values("date")
    out = out.groupby("date", as_index=False).tail(1).reset_index(drop=True)
    return out


def _read_noise(csv_path: Path, target_date: str) -> float:
    if not csv_path.exists():
        # safe fallback: unknown -> WARN寄り
        return 0.50
    df = pd.read_csv(csv_path)
    if df.empty:
        return 0.50

    # pick date col
    dcol = None
    for c in df.columns:
        if c.lower() in ("date", "ds", "day"):
            dcol = c
            break
    if dcol is None:
        dcol = df.columns[0]

    df[dcol] = pd.to_datetime(df[dcol], errors="coerce").dt.strftime("%Y-%m-%d")

    # pick prob col
    pcol = None
    for key in ("noise_prob", "prob", "p", "noise_probability", "yhat", "yhat_prob"):
        for c in df.columns:
            if c.lower() == key:
                pcol = c
                break
        if pcol:
            break
    if pcol is None:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        pcol = num_cols[-1] if num_cols else None
    if pcol is None:
        return 0.50

    row = df.loc[df[dcol] == target_date]
    if row.empty:
        row = df.tail(1)

    try:
        v = float(row.iloc[0][pcol])
    except Exception:
        v = 0.50
    return max(0.0, min(1.0, v))


def _decision_from_noise(p: float) -> str:
    if p < ON_TH:
        return "ON"
    if p < WARN_TH:
        return "WARN"
    return "OFF"


def _default_note(decision: str) -> str:
    if decision == "ON":
        return "normal"
    if decision == "WARN":
        return "split_or_small"
    return "split_or_wait"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="Target date YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    target = args.date or _date.today().strftime("%Y-%m-%d")

    usdjpy = _load_rates(USDJPY_CSV)
    usdthb = _load_rates(USDTHB_CSV)

    max_usdjpy = usdjpy["date"].max()
    max_usdthb = usdthb["date"].max()
    if max_usdjpy < target or max_usdthb < target:
        print(
            f"[WARN] rates are stale: need={target} usdjpy_max={max_usdjpy} usdthb_max={max_usdthb}"
        )
        return 2

    # get today rates
    rj = float(usdjpy.loc[usdjpy["date"] == target].iloc[0]["rate"])
    rt = float(usdthb.loc[usdthb["date"] == target].iloc[0]["rate"])
    jpy_thb = rt / rj

    pj = _read_noise(USDJPY_NOISE, target)
    pt = _read_noise(USDTHB_NOISE, target)
    combined = max(pj, pt)

    dj = _decision_from_noise(pj)
    dt = _decision_from_noise(pt)
    dc = _decision_from_noise(combined)
    note = _default_note(dc)

    # dashboard format: your current file is no-header CSV with many columns.
    # We'll write in the SAME column order you showed:
    # date, combined_noise_prob, combined_decision,
    # usdjpy_close, usdjpy_noise_prob, usdjpy_decision,
    # usdthb_close, usdthb_noise_prob, jpy_thb,
    # combined_noise_prob(dup), combined_decision(dup), remit_note
    row = [
        target,
        f"{combined:.15f}",
        dc,
        f"{rj:.4f}",
        f"{pj:.15f}",
        dj,
        f"{rt:.4f}",
        f"{pt:.15f}",
        f"{jpy_thb:.15f}",
        f"{combined:.15f}",
        dc,
        note,
    ]

    DASH_CSV.parent.mkdir(parents=True, exist_ok=True)

    # prevent duplicates: if same date exists, rewrite file (safe)
    if DASH_CSV.exists():
        lines = DASH_CSV.read_text(encoding="utf-8", errors="ignore").splitlines()
        kept = [ln for ln in lines if not ln.strip().startswith(target + ",")]
        kept.append(",".join(row))
        DASH_CSV.write_text("\n".join(kept) + "\n", encoding="utf-8")
    else:
        DASH_CSV.write_text(",".join(row) + "\n", encoding="utf-8")

    print(f"[OK] dashboard updated: {DASH_CSV} date={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

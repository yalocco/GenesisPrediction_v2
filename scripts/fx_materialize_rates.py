# scripts/fx_materialize_rates.py
"""
Materialize USDJPY / USDTHB rates using Alpha Vantage (primary).

Policy:
- Alpha Vantage FX_DAILY is primary online source.
- Source files (*_source.csv / *_source.txt) still take precedence if present.
- If online fetch fails:
    - keep existing CSV if exists (warn only)
    - otherwise hard fail
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "fx"
API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")


# ----------------------------
# Normalize
# ----------------------------
def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    out = df[["date", "rate"]]
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["rate"] = pd.to_numeric(out["rate"], errors="coerce")
    out = out.dropna()
    out = out.sort_values("date").groupby("date", as_index=False).tail(1)
    return out.reset_index(drop=True)


# ----------------------------
# Source handling
# ----------------------------
def _backup_bad_source(src: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bad = src.with_name(f"{src.stem}.bad_{ts}{src.suffix}")
    try:
        shutil.move(src, bad)
    except Exception:
        shutil.copy2(src, bad)
    return bad


def _read_source_any(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "date" not in df.columns or "rate" not in df.columns:
        raise ValueError("source must have date,rate")
    return _normalize(df)


# ----------------------------
# Alpha Vantage fetch
# ----------------------------
def _fetch_alpha_vantage(pair: str) -> pd.DataFrame:
    if not API_KEY:
        raise RuntimeError("ALPHAVANTAGE_API_KEY not set")

    to_symbol = {"usdjpy": "JPY", "usdthb": "THB"}[pair]
    url = (
        "https://www.alphavantage.co/query"
        f"?function=FX_DAILY&from_symbol=USD&to_symbol={to_symbol}"
        f"&outputsize=full&apikey={API_KEY}"
    )

    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    key = "Time Series FX (Daily)"
    if key not in raw:
        raise RuntimeError(f"Alpha Vantage error: {raw.get('Note') or raw.get('Error Message')}")

    rows = []
    for d, v in raw[key].items():
        rows.append((d, float(v["4. close"])))

    return _normalize(pd.DataFrame(rows, columns=["date", "rate"]))


# ----------------------------
# Materialize
# ----------------------------
def materialize(pair: str) -> tuple[Path, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = DATA_DIR / f"{pair}.csv"

    existing_df: Optional[pd.DataFrame] = None
    if out_csv.exists():
        try:
            existing_df = _normalize(pd.read_csv(out_csv))
        except Exception:
            existing_df = None

    src = next((p for p in [
        DATA_DIR / f"{pair}_source.csv",
        DATA_DIR / f"{pair}_source.txt",
    ] if p.exists()), None)

    df: Optional[pd.DataFrame] = None

    # source first
    if src is not None:
        try:
            df = _read_source_any(src)
        except Exception as e:
            bad = _backup_bad_source(src)
            print(f"[WARN] bad source -> {bad} ({e})")

    # alpha vantage
    if df is None:
        try:
            df = _fetch_alpha_vantage(pair)
        except Exception as e:
            if existing_df is not None:
                last = existing_df["date"].iloc[-1]
                print(f"[WARN] Alpha Vantage failed for {pair}; keep existing CSV (last={last})")
                print(f"       reason: {e}")
                return out_csv, last
            raise RuntimeError(f"rates unavailable for {pair}") from e

    if existing_df is not None:
        df = pd.concat([existing_df, df], ignore_index=True)
        df = _normalize(df)

    df.to_csv(out_csv, index=False)
    last_date = df["date"].iloc[-1]
    return out_csv, last_date


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", choices=["usdjpy", "usdthb", "both"], default="both")
    args = ap.parse_args()

    targets = ["usdjpy", "usdthb"] if args.pair == "both" else [args.pair]
    for t in targets:
        out, last = materialize(t)
        print(f"[OK] materialized {t}: {out} (last={last})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

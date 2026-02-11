# scripts/fx_materialize_rates.py
"""
Materialize USDJPY / USDTHB daily rates.

Priority:
1) data/fx/<pair>_source.csv or <pair>_source.txt  (must have date,rate)
2) Alpha Vantage (FX_DAILY)
3) exchangerate.host timeseries (requires access_key)
4) If online fails:
   - strict=False: keep existing CSV if present (warn only). If no CSV, hard fail.
   - strict=True : hard fail (even if CSV exists)

Pairs:
- usdjpy
- usdthb
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "fx"

AV_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
HOST_KEY = os.getenv("EXCHANGERATE_HOST_ACCESS_KEY")


# ----------------------------
# Utils
# ----------------------------
def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "date" not in df.columns or "rate" not in df.columns:
        raise ValueError("df must have columns: date, rate")
    out = df[["date", "rate"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["rate"] = pd.to_numeric(out["rate"], errors="coerce")
    out = out.dropna()
    out = out.sort_values("date").groupby("date", as_index=False).tail(1)
    return out.reset_index(drop=True)


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


def _http_json(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ----------------------------
# Alpha Vantage
# ----------------------------
def _fetch_alpha_vantage(pair: str) -> pd.DataFrame:
    if not AV_KEY:
        raise RuntimeError("ALPHAVANTAGE_API_KEY not set")

    to_symbol = {"usdjpy": "JPY", "usdthb": "THB"}[pair]
    url = (
        "https://www.alphavantage.co/query?"
        + urllib.parse.urlencode(
            {
                "function": "FX_DAILY",
                "from_symbol": "USD",
                "to_symbol": to_symbol,
                "outputsize": "full",
                "apikey": AV_KEY,
            }
        )
    )

    raw = _http_json(url)
    ts = raw.get("Time Series FX (Daily)")
    if not ts:
        raise RuntimeError(
            f"AlphaVantage error: {raw.get('Note') or raw.get('Error Message') or 'no timeseries'}"
        )

    rows = [(d, float(v["4. close"])) for d, v in ts.items()]
    return _normalize(pd.DataFrame(rows, columns=["date", "rate"]))


# ----------------------------
# exchangerate.host (timeseries)
# ----------------------------
def _fetch_exchangerate_host(pair: str) -> pd.DataFrame:
    if not HOST_KEY:
        raise RuntimeError("EXCHANGERATE_HOST_ACCESS_KEY not set")

    symbol = {"usdjpy": "JPY", "usdthb": "THB"}[pair]

    start_date = "2000-01-01"
    end_date = datetime.utcnow().strftime("%Y-%m-%d")

    params = {
        "access_key": HOST_KEY,
        "base": "USD",
        "symbols": symbol,
        "start_date": start_date,
        "end_date": end_date,
    }

    url = "https://api.exchangerate.host/timeseries?" + urllib.parse.urlencode(params)
    raw = _http_json(url)

    if raw.get("success") is False:
        err = raw.get("error") or {}
        raise RuntimeError(
            f"exchangerate.host error: {err.get('type') or err.get('code')} {err.get('info') or ''}".strip()
        )

    rates = raw.get("rates")
    if not isinstance(rates, dict) or not rates:
        raise RuntimeError("exchangerate.host returned no rates")

    rows = []
    for d, kv in rates.items():
        if isinstance(kv, dict) and symbol in kv:
            rows.append((d, float(kv[symbol])))

    if not rows:
        raise RuntimeError("exchangerate.host returned no rows for symbol")

    return _normalize(pd.DataFrame(rows, columns=["date", "rate"]))


# ----------------------------
# Materialize
# ----------------------------
def materialize(pair: str, *, strict: bool = False) -> tuple[Path, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = DATA_DIR / f"{pair}.csv"

    existing_df: Optional[pd.DataFrame] = None
    if out_csv.exists():
        try:
            existing_df = _normalize(pd.read_csv(out_csv))
        except Exception:
            existing_df = None

    # 1) local source (manual bootstrap)
    src = next(
        (p for p in [DATA_DIR / f"{pair}_source.csv", DATA_DIR / f"{pair}_source.txt"] if p.exists()),
        None,
    )

    df: Optional[pd.DataFrame] = None

    if src is not None:
        try:
            df = _read_source_any(src)
        except Exception as e:
            bad = _backup_bad_source(src)
            print(f"[WARN] bad source -> {bad} ({e})")

    # 2) Alpha Vantage
    if df is None:
        try:
            df = _fetch_alpha_vantage(pair)
        except Exception as e:
            print(f"[WARN] Alpha Vantage failed for {pair}")
            print(f"       reason: {e}")

    # 3) exchangerate.host fallback
    if df is None:
        try:
            df = _fetch_exchangerate_host(pair)
        except Exception as e:
            print(f"[WARN] exchangerate.host failed for {pair}")
            print(f"       reason: {e}")

    # 4) if still none
    if df is None:
        if strict:
            raise RuntimeError(f"rates unavailable for {pair} (strict=True)")
        if existing_df is not None and len(existing_df) > 0:
            last = existing_df["date"].iloc[-1]
            print(f"[WARN] online fetch unavailable for {pair}; keep existing CSV (last={last})")
            return out_csv, last
        raise RuntimeError(f"rates unavailable for {pair}")

    # merge with existing
    if existing_df is not None and len(existing_df) > 0:
        df = pd.concat([existing_df, df], ignore_index=True)
        df = _normalize(df)

    df.to_csv(out_csv, index=False)
    last_date = df["date"].iloc[-1]
    return out_csv, last_date


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", choices=["usdjpy", "usdthb", "both"], default="both")
    ap.add_argument("--strict", action="store_true", help="hard fail if online fetch fails")
    args = ap.parse_args()

    targets = ["usdjpy", "usdthb"] if args.pair == "both" else [args.pair]
    for t in targets:
        out, last = materialize(t, strict=args.strict)
        print(f"[OK] materialized {t}: {out} (last={last})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

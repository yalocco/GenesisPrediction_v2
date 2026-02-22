# scripts/fx_materialize_rates.py
# Materialize FX daily rates into data/fx/<pair>.csv with quota-friendly guards.
#
# Goals
# - No external deps (NO requests): uses Python stdlib only
# - Minimize API calls:
#     * skip when already fresh locally
#     * skip repeated attempts per day (state file)
# - Weekend-aware default:
#     * if today is Sat/Sun, treat target date as last business day (Fri)
# - Primary -> Secondary fallback (no double-call on success)
#
# Usage:
#   .\.venv\Scripts\python.exe scripts\fx_materialize_rates.py --pair usdthb
#   .\.venv\Scripts\python.exe scripts\fx_materialize_rates.py --pair usdjpy --date 2026-02-22
#   .\.venv\Scripts\python.exe scripts\fx_materialize_rates.py --pair usdjpy --date 2026-02-22 --force
#
# Env:
#   ALPHAVANTAGE_API_KEY
#   EXCHANGERATE_HOST_ACCESS_KEY
#
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

# ----------------------------
# Settings
# ----------------------------
DATA_DIR = Path("data") / "fx"
STATE_PATH = DATA_DIR / "_api_state.json"

ALPHA_KEY_ENV = "ALPHAVANTAGE_API_KEY"
EXH_KEY_ENV = "EXCHANGERATE_HOST_ACCESS_KEY"

ALPHA_ENDPOINT = "https://www.alphavantage.co/query"
EXH_ENDPOINT = "https://api.exchangerate.host/timeseries"

DEFAULT_LOOKBACK_DAYS = 4000  # used only when no local csv exists

# ----------------------------
# Pair map
# ----------------------------
@dataclass(frozen=True)
class PairDef:
    base: str
    quote: str


PAIR_MAP: Dict[str, PairDef] = {
    "usdthb": PairDef("USD", "THB"),
    "usdjpy": PairDef("USD", "JPY"),
    "eurusd": PairDef("EUR", "USD"),
    "gbpusd": PairDef("GBP", "USD"),
    "audusd": PairDef("AUD", "USD"),
    "usdcny": PairDef("USD", "CNY"),
}

# ----------------------------
# HTTP (stdlib only)
# ----------------------------
def _http_get_json(url: str, params: Dict[str, str], timeout_sec: int = 25) -> dict:
    qs = urlencode(params)
    full = f"{url}?{qs}"
    req = Request(
        full,
        headers={
            "User-Agent": "GenesisPrediction-v2/1.0 (+stdlib urllib)",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=timeout_sec) as resp:
            status = getattr(resp, "status", None) or 200
            body = resp.read().decode("utf-8", errors="replace")
            if status < 200 or status >= 300:
                raise RuntimeError(f"HTTP {status}: {body[:300]}")
            try:
                return json.loads(body)
            except Exception as e:
                raise RuntimeError(f"JSON decode failed: {e}; body_head={body[:200]!r}")
    except Exception as e:
        raise RuntimeError(f"HTTP GET failed: {e}")

# ----------------------------
# Utilities
# ----------------------------
def _today_local() -> date:
    return datetime.now().date()


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _read_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(state: dict) -> None:
    _ensure_dir(DATA_DIR)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def _normalize_existing_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize to columns ['date','rate'] with date as YYYY-MM-DD string."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "rate"])

    if "date" not in df.columns:
        if df.index.name in ("date", "Date", None) and len(df.columns) >= 1:
            df = df.reset_index()
        if "date" not in df.columns:
            df = df.rename(columns={df.columns[0]: "date"})

    if "rate" not in df.columns:
        for cand in ("rate", "Rate", "close", "Close", "value", "Value", "4. close", "4. Close"):
            if cand in df.columns:
                df = df.rename(columns={cand: "rate"})
                break
        if "rate" not in df.columns:
            other_cols = [c for c in df.columns if c != "date"]
            if other_cols:
                df = df.rename(columns={other_cols[0]: "rate"})

    df = df[["date", "rate"]].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["date"])
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df.dropna(subset=["rate"])
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.sort_values("date")
    return df


def _read_pair_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["date", "rate"])
    try:
        return _normalize_existing_csv(pd.read_csv(path))
    except Exception:
        try:
            return _normalize_existing_csv(pd.read_csv(path, index_col=0))
        except Exception as e:
            print(f"[ERR] Failed to read existing CSV: {path} ({e})")
            return pd.DataFrame(columns=["date", "rate"])


def _last_date_in_df(df: pd.DataFrame) -> Optional[date]:
    if df is None or df.empty:
        return None
    try:
        return _parse_date(str(df["date"].iloc[-1]))
    except Exception:
        return None


def _merge_and_write(path: Path, existing: pd.DataFrame, incoming: pd.DataFrame) -> Tuple[int, Optional[date]]:
    existing_n = _normalize_existing_csv(existing)
    incoming_n = _normalize_existing_csv(incoming)
    merged = pd.concat([existing_n, incoming_n], ignore_index=True)
    merged = merged.drop_duplicates(subset=["date"], keep="last").sort_values("date")

    _ensure_dir(path.parent)
    merged.to_csv(path, index=False, encoding="utf-8")

    lastd = _last_date_in_df(merged)
    return len(merged), lastd


def _last_business_day(d: date) -> date:
    wd = d.weekday()  # Mon=0 ... Sun=6
    if wd == 5:  # Sat
        return d - timedelta(days=1)
    if wd == 6:  # Sun
        return d - timedelta(days=2)
    return d

# ----------------------------
# Provider: Alpha Vantage
# ----------------------------
def _fetch_alpha_daily(base: str, quote: str, api_key: str) -> pd.DataFrame:
    params = {
        "function": "FX_DAILY",
        "from_symbol": base,
        "to_symbol": quote,
        "outputsize": "full",
        "apikey": api_key,
    }
    j = _http_get_json(ALPHA_ENDPOINT, params=params)

    if isinstance(j, dict):
        if "Error Message" in j:
            raise RuntimeError(f"AlphaVantage error: {j.get('Error Message')}")
        if "Note" in j:
            raise RuntimeError(f"AlphaVantage note: {j.get('Note')}")
        if "Information" in j:
            raise RuntimeError(f"AlphaVantage info: {j.get('Information')}")

    key = None
    for k in ("Time Series FX (Daily)", "Time Series FX (Daily) "):
        if isinstance(j, dict) and k in j:
            key = k
            break
    if not key and isinstance(j, dict):
        for k in j.keys():
            if "Time Series" in k:
                key = k
                break
    if not key:
        raise RuntimeError("AlphaVantage response missing time series")

    ts = j.get(key, {})
    rows = []
    for d, ohlc in ts.items():
        if isinstance(ohlc, dict):
            v = ohlc.get("4. close") or ohlc.get("4. Close") or ohlc.get("close") or ohlc.get("Close")
            if v is None:
                for vv in ohlc.values():
                    v = vv
                    break
            rows.append((d, v))

    df = pd.DataFrame(rows, columns=["date", "rate"])
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df.dropna(subset=["rate"])
    df = df.sort_values("date")
    return df

# ----------------------------
# Provider: exchangerate.host
# ----------------------------
def _fetch_exchangerate_timeseries(
    base: str,
    quote: str,
    access_key: str,
    start: date,
    end: date,
) -> pd.DataFrame:
    params = {
        "base": base,
        "symbols": quote,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "access_key": access_key,
    }
    j = _http_get_json(EXH_ENDPOINT, params=params)

    if isinstance(j, dict) and j.get("success") is False:
        err = j.get("error") or {}
        raise RuntimeError(f"exchangerate.host error: {err}")

    rates = j.get("rates")
    if not isinstance(rates, dict):
        raise RuntimeError("exchangerate.host response missing rates")

    rows = []
    for d, qmap in rates.items():
        if isinstance(qmap, dict) and quote in qmap:
            rows.append((d, qmap[quote]))

    df = pd.DataFrame(rows, columns=["date", "rate"])
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
    df = df.dropna(subset=["rate"]).sort_values("date")
    return df

# ----------------------------
# Quota-friendly guard logic
# ----------------------------
def _state_key(pair: str) -> str:
    return f"fx_materialize_rates::{pair}"


def _should_skip_online(
    pair: str,
    target_date: date,
    last_local: Optional[date],
    state: dict,
) -> Tuple[bool, str]:
    if last_local is not None and last_local >= target_date:
        return True, "fresh_local"

    k = _state_key(pair)
    s = state.get(k, {})
    last_attempt = s.get("last_attempt_date")
    last_success = s.get("last_success_date")
    last_result = s.get("last_attempt_result")  # "ok" | "fail"

    if last_attempt == target_date.strftime("%Y-%m-%d"):
        return True, f"already_attempted_today({last_result or 'unknown'})"

    if last_success == target_date.strftime("%Y-%m-%d"):
        return True, "already_succeeded_today"

    return False, "needs_online"


def _update_state(
    state: dict,
    pair: str,
    target_date: date,
    attempt_result: str,
    provider: Optional[str],
    success_date: Optional[date],
    message: Optional[str] = None,
) -> dict:
    k = _state_key(pair)
    s = state.get(k, {})
    s["last_attempt_date"] = target_date.strftime("%Y-%m-%d")
    s["last_attempt_result"] = attempt_result
    if provider:
        s["last_provider"] = provider
    if success_date:
        s["last_success_date"] = success_date.strftime("%Y-%m-%d")
    if message:
        s["last_message"] = message[:400]
    s["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state[k] = s
    return state

# ----------------------------
# Main
# ----------------------------
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", required=True, help=f"pair key: {', '.join(sorted(PAIR_MAP.keys()))}")
    parser.add_argument("--date", default=None, help="target date YYYY-MM-DD (default: today local)")
    parser.add_argument("--force", action="store_true", help="ignore guards AND do not shift weekend date")
    args = parser.parse_args()

    pair = args.pair.lower().strip()
    if pair not in PAIR_MAP:
        print(f"[ERR] unknown pair: {pair}")
        print(f"      allowed: {', '.join(sorted(PAIR_MAP.keys()))}")
        return 2

    raw_target = _parse_date(args.date) if args.date else _today_local()
    target = raw_target if args.force else _last_business_day(raw_target)
    if target != raw_target:
        print(f"[INFO] target date adjusted (weekend): {raw_target} -> {target}")

    base = PAIR_MAP[pair].base
    quote = PAIR_MAP[pair].quote

    out_csv = DATA_DIR / f"{pair}.csv"
    existing = _read_pair_csv(out_csv)
    last_local = _last_date_in_df(existing)

    state = _read_state()

    if not args.force:
        skip, reason = _should_skip_online(pair, target, last_local, state)
        if skip:
            if last_local is not None:
                print(f"[OK] skip online ({reason}): {pair} -> {out_csv} (last={last_local})")
                return 0
            print(f"[WARN] guard wants skip but local missing; will try once: {pair} reason={reason}")

    # Determine fetch window
    if last_local is not None:
        start = last_local + timedelta(days=1)
    else:
        start = target - timedelta(days=min(DEFAULT_LOOKBACK_DAYS, 3650))
    end = target

    alpha_key = os.getenv(ALPHA_KEY_ENV, "").strip()
    exh_key = os.getenv(EXH_KEY_ENV, "").strip()

    # --- Primary: Alpha Vantage ---
    if alpha_key:
        try:
            df_alpha = _fetch_alpha_daily(base, quote, alpha_key)
            df_alpha["date"] = pd.to_datetime(df_alpha["date"])
            df_alpha = df_alpha[(df_alpha["date"] >= pd.Timestamp(start)) & (df_alpha["date"] <= pd.Timestamp(end))]
            df_alpha["date"] = df_alpha["date"].dt.strftime("%Y-%m-%d")

            n, lastd = _merge_and_write(out_csv, existing, df_alpha)
            state = _update_state(
                state,
                pair,
                target,
                attempt_result="ok",
                provider="alphavantage",
                success_date=lastd,
            )
            _write_state(state)

            print(f"[OK] materialized {pair} (AlphaVantage): {out_csv} (rows={n}, last={lastd})")
            return 0
        except Exception as e:
            msg = str(e)
            print(f"[WARN] AlphaVantage failed: {msg}")
            state = _update_state(
                state,
                pair,
                target,
                attempt_result="fail",
                provider="alphavantage",
                success_date=None,
                message=msg,
            )
            _write_state(state)
    else:
        print(f"[WARN] {ALPHA_KEY_ENV} not set -> skip AlphaVantage")

    # --- Secondary: exchangerate.host (ONLY if primary failed) ---
    if exh_key:
        try:
            df_exh = _fetch_exchangerate_timeseries(base, quote, exh_key, start=start, end=end)
            n, lastd = _merge_and_write(out_csv, existing, df_exh)
            state = _update_state(
                state,
                pair,
                target,
                attempt_result="ok",
                provider="exchangerate.host",
                success_date=lastd,
            )
            _write_state(state)

            print(f"[OK] materialized {pair} (exchangerate.host): {out_csv} (rows={n}, last={lastd})")
            return 0
        except Exception as e:
            msg = str(e)
            print(f"[WARN] exchangerate.host failed: {msg}")
            state = _update_state(
                state,
                pair,
                target,
                attempt_result="fail",
                provider="exchangerate.host",
                success_date=None,
                message=msg,
            )
            _write_state(state)
    else:
        print(f"[WARN] {EXH_KEY_ENV} not set -> skip exchangerate.host")

    # --- Final fallback: local only ---
    if last_local is not None:
        print(f"[OK] keep local CSV only: {pair} -> {out_csv} (last={last_local})")
        return 0

    print(f"[ERR] no local data and all providers unavailable/failed: {pair}")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
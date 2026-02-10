# scripts/fx_fetch_usd_pairs.py
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request


DATA_DIR = Path("data/fx")
USDJPY_CSV = DATA_DIR / "usdjpy.csv"
USDTHB_CSV = DATA_DIR / "usdthb.csv"

API_BASE = "https://api.exchangerate.host"
TIMEOUT_SEC = 20


@dataclass
class RateRow:
    date: str
    rate: float


def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _read_last_date(csv_path: Path) -> str | None:
    if not csv_path.exists():
        return None
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            return None
        rows.sort(key=lambda r: r.get("date", ""))
        return rows[-1].get("date")
    except Exception:
        return None


def _append_or_replace_row(csv_path: Path, row: RateRow) -> None:
    _ensure_dir(csv_path)
    rows: list[dict[str, str]] = []
    if csv_path.exists():
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))

    # remove same-date rows
    rows = [r for r in rows if r.get("date") != row.date]
    rows.append({"date": row.date, "rate": f"{row.rate:.10f}"})
    rows.sort(key=lambda r: r["date"])

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "rate"])
        w.writeheader()
        w.writerows(rows)


def _fetch_usd_rates(target_date: str) -> dict[str, float]:
    # exchangerate.host: /timeseries?base=USD&symbols=JPY,THB&start_date=...&end_date=...
    # We request one-day timeseries to avoid ambiguity.
    params = {
        "base": "USD",
        "symbols": "JPY,THB",
        "start_date": target_date,
        "end_date": target_date,
    }
    url = f"{API_BASE}/timeseries?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "GenesisPrediction/FXFetcher"})
    with urlopen(req, timeout=TIMEOUT_SEC) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if not data.get("success", True) and "error" in data:
        raise RuntimeError(f"API error: {data['error']}")

    rates_by_day = data.get("rates") or {}
    day = rates_by_day.get(target_date)
    if not day:
        raise RuntimeError(f"no rates for date={target_date} from exchangerate.host")
    if "JPY" not in day or "THB" not in day:
        raise RuntimeError(f"missing JPY/THB in response for date={target_date}")
    return {"JPY": float(day["JPY"]), "THB": float(day["THB"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    target = args.date or Date.today().isoformat()

    try:
        got = _fetch_usd_rates(target)
    except Exception as e:
        print(f"[ERR] fx_fetch_usd_pairs failed: {e}", file=sys.stderr)
        return 2

    usdjpy = got["JPY"]
    usdthb = got["THB"]

    _append_or_replace_row(USDJPY_CSV, RateRow(target, usdjpy))
    _append_or_replace_row(USDTHB_CSV, RateRow(target, usdthb))

    print(f"[OK] wrote USDJPY: {USDJPY_CSV} date={target} rate={usdjpy}")
    print(f"[OK] wrote USDTHB: {USDTHB_CSV} date={target} rate={usdthb}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# scripts/fx_major_pairs_fetch.py
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "fx"


@dataclass(frozen=True)
class Pair:
    name: str
    base: str
    quote: str
    out_csv: str


PAIRS = [
    Pair("USDJPY", "USD", "JPY", "usdjpy.csv"),
    Pair("EURJPY", "EUR", "JPY", "eurjpy.csv"),
    Pair("EURUSD", "EUR", "USD", "eurusd.csv"),
]


def http_get_json(url: str, timeout: int = 20) -> dict:
    req = Request(url, headers={"User-Agent": "GenesisPrediction_v2/1.0"})
    with urlopen(req, timeout=timeout) as r:
        data = r.read().decode("utf-8")
    return json.loads(data)


def fetch_timeseries_exchangerate_host(base: str, quote: str, start: str, end: str) -> tuple[list[tuple[str, float]], str]:
    # exchangerate.host: /timeseries?base=USD&symbols=JPY&start_date=...&end_date=...
    params = urlencode({"base": base, "symbols": quote, "start_date": start, "end_date": end})
    url = f"https://api.exchangerate.host/timeseries?{params}"
    j = http_get_json(url)

    if not j.get("success", False):
        raise RuntimeError(f"exchangerate.host failed: {j}")

    rates = j.get("rates", {})
    rows: list[tuple[str, float]] = []
    for d, v in rates.items():
        if isinstance(v, dict) and quote in v:
            try:
                rows.append((d, float(v[quote])))
            except Exception:
                pass

    rows.sort(key=lambda x: x[0])
    if not rows:
        raise RuntimeError("exchangerate.host: empty rows")
    return rows, "exchangerate.host"


def fetch_timeseries_frankfurter(base: str, quote: str, start: str, end: str) -> tuple[list[tuple[str, float]], str]:
    # frankfurter: https://api.frankfurter.app/2024-01-01..2024-12-31?from=EUR&to=JPY
    params = urlencode({"from": base, "to": quote})
    url = f"https://api.frankfurter.app/{start}..{end}?{params}"
    j = http_get_json(url)

    rates = j.get("rates", {})
    rows: list[tuple[str, float]] = []
    for d, v in rates.items():
        if isinstance(v, dict) and quote in v:
            try:
                rows.append((d, float(v[quote])))
            except Exception:
                pass

    rows.sort(key=lambda x: x[0])
    if not rows:
        raise RuntimeError("frankfurter.app: empty rows")
    return rows, "frankfurter.app"


def fetch_pair(base: str, quote: str, start: str, end: str) -> tuple[list[tuple[str, float]], str]:
    # まず exchangerate.host → ダメなら frankfurter
    try:
        return fetch_timeseries_exchangerate_host(base, quote, start, end)
    except Exception:
        return fetch_timeseries_frankfurter(base, quote, start, end)


def write_csv(path: Path, rows: list[tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "rate"])
        for d, r in rows:
            w.writerow([d, f"{r:.10f}"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--end", default=date.today().isoformat(), help="YYYY-MM-DD (default: today)")
    ap.add_argument("--days", type=int, default=400, help="lookback days")
    args = ap.parse_args()

    end_d = date.fromisoformat(args.end)
    start_d = end_d - timedelta(days=int(args.days))
    start = start_d.isoformat()
    end = end_d.isoformat()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for p in PAIRS:
        rows, src = fetch_pair(p.base, p.quote, start, end)
        out = OUT_DIR / p.out_csv
        write_csv(out, rows)

        (OUT_DIR / f"{p.name.lower()}_source.txt").write_text(
            f"source={src}\nbase={p.base}\nquote={p.quote}\nstart={start}\nend={end}\nrows={len(rows)}\n",
            encoding="utf-8",
        )

        print(f"[OK] wrote {p.name}: {out} rows={len(rows)} src={src}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

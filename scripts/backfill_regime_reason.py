# scripts/backfill_regime_reason.py
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_ymd(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def daterange(d0: datetime, d1: datetime):
    d = d0
    while d <= d1:
        yield d
        d += timedelta(days=1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    start = parse_ymd(args.start)
    end = parse_ymd(args.end)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    ok = skip = err = 0

    for d in daterange(start, end):
        day = d.strftime("%Y-%m-%d")
        outpath = outdir / f"regime_reason_{day}.json"
        if outpath.exists() and not args.force:
            skip += 1
            continue

        # ★ここは手順1の --help を見て “正しい引数” に合わせて変更する
        cmd = [
            sys.executable,
            "scripts/build_regime_reason.py",
            "--date", day,
            "--out", str(outpath),
        ]

        if args.dry_run:
            print("[PLAN]", " ".join(cmd))
            continue

        r = subprocess.run(cmd)
        if r.returncode == 0:
            ok += 1
        else:
            err += 1
            print("[ERROR]", day, "returncode=", r.returncode)

    print(f"[backfill_regime_reason] OK={ok} SKIP={skip} ERROR={err}")
    return 0 if err == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

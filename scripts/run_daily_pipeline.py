from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main() -> None:
    ap = argparse.ArgumentParser(description="Daily pipeline (docker analyzer entry)")
    ap.add_argument(
        "--analysis-dir",
        default=str(Path("data") / "world_politics" / "analysis"),
        help="analysis dir",
    )
    ap.add_argument("--with-scenarios", action="store_true", help="also run scenario predictions")
    args = ap.parse_args()

    analysis_dir = Path(args.analysis_dir)

    # 1) diff / daily_summary（入口は docker compose analyzer）
    run(["docker", "compose", "run", "--rm", "analyzer"])

    # 2) regime_reason（最新日に対して作る：build_regime_reason.py は analysis_dir の daily_summary_* を走査する）
    run([sys.executable, "scripts/build_regime_reason.py", "--outdir", str(analysis_dir)])

    # 3) predictions（任意）
    if args.with_scenarios:
        run([sys.executable, "scripts/run_scenarios.py", "--latest", "--analysis-dir", str(analysis_dir)])

    print("[OK] daily pipeline finished")


if __name__ == "__main__":
    main()

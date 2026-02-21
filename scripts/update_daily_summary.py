from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Morning ritual helper: update daily_summary artifacts")
    parser.add_argument("--date", default=None, help="UTC date YYYY-MM-DD (optional)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    scripts_dir = root / "scripts"

    # The repo currently contains build_daily_summary_index.py (present in your dir listing).
    # Prefer running it to (re)build summary-related outputs.
    candidate = scripts_dir / "build_daily_summary_index.py"
    if not candidate.exists():
        # If the intended builder is missing, do not hard-fail the whole ritual.
        # Return 0 so the ritual can proceed; it will surface elsewhere via Health/WARN if needed.
        print(f"[WARN] missing expected builder: {candidate}")
        return 0

    cmd = [sys.executable, str(candidate)]
    # Pass --date if the target script supports it; if not, it may error.
    # In that case, we retry without --date once.
    if args.date:
        cmd_with_date = cmd + ["--date", args.date]
        print(f"[INFO] run: {' '.join(cmd_with_date)}")
        p = subprocess.run(cmd_with_date, cwd=str(root))
        if p.returncode == 0:
            return 0

        print(f"[WARN] builder returned {p.returncode} with --date; retrying without --date...")

    print(f"[INFO] run: {' '.join(cmd)}")
    p2 = subprocess.run(cmd, cwd=str(root))
    return int(p2.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
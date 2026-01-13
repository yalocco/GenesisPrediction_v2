#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, *, shell=False):
    print(f"[RUN] {cmd}")
    subprocess.check_call(cmd, shell=shell)

def main():
    # 1) analyzer 実行（既存の安定ルート）
    run(
        ["docker", "compose", "run", "--rm", "analyzer"],
    )

    # 2) daily_summary の anchors を後処理で掃除（確実・安全）
    python_exe = ROOT / ".venv" / "Scripts" / "python.exe"
    cleaner = ROOT / "scripts" / "clean_daily_summary_anchors.py"

    run(
        [str(python_exe), str(cleaner)]
    )

    print("[DONE] daily pipeline finished successfully")

if __name__ == "__main__":
    sys.exit(main())

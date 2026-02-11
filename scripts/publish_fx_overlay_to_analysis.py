# scripts/publish_fx_overlay_to_analysis.py
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

SRC = ROOT / "data" / "fx" / "jpy_thb_remittance_overlay.png"
ANALYSIS = ROOT / "data" / "world_politics" / "analysis"

DST_LATEST = ANALYSIS / "jpy_thb_remittance_overlay.png"
LATEST_POINTER = ANALYSIS / "fx_overlay_latest.txt"


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    date = args.date
    _ensure_dir(ANALYSIS)

    if not SRC.exists():
        raise SystemExit(f"missing src: {SRC}")

    dated = ANALYSIS / f"fx_overlay_{date}.png"

    # 1) dated を作る（証拠）
    shutil.copy2(SRC, dated)

    # 2) latest を更新（GUIが参照する先）
    shutil.copy2(SRC, DST_LATEST)

    # 3) latest が指している dated をテキストで固定（運用・将来改修用）
    LATEST_POINTER.write_text(dated.name + "\n", encoding="utf-8")

    print("[OK] published FX overlay")
    print(f"  src:   {SRC.as_posix()}")
    print(f"  dst:   {DST_LATEST.as_posix()}")
    print(f"  dated: {dated.as_posix()}")
    print(f"  ptr:   {LATEST_POINTER.as_posix()} -> {dated.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

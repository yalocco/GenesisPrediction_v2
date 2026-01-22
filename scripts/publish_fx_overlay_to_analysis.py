"""
Publish FX overlay PNG into the GUI's "analysis outputs" folder.

Why:
- The FastAPI GUI lists outputs from data/world_politics/analysis/.
- FX overlay is generated under data/fx/ (source of truth).
- To show the overlay in the GUI without touching server.py/index.html,
  copy (publish) the latest overlay into the analysis folder.

Usage:
  python scripts/publish_fx_overlay_to_analysis.py --date 2026-01-22
  python scripts/publish_fx_overlay_to_analysis.py --latest
"""

from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FX_DIR = REPO_ROOT / "data" / "fx"
ANALYSIS_DIR = REPO_ROOT / "data" / "world_politics" / "analysis"

# Source-of-truth overlay produced by fx_remittance_* scripts
SRC_OVERLAY = FX_DIR / "jpy_thb_remittance_overlay.png"

# Published filename (stable) so the GUI always shows "the latest"
DST_STABLE = ANALYSIS_DIR / "jpy_thb_remittance_overlay.png"


def publish(target_date: str | None, latest: bool) -> Path:
    if not SRC_OVERLAY.exists():
        raise FileNotFoundError(f"Source overlay not found: {SRC_OVERLAY}")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # Always publish the stable name
    shutil.copy2(SRC_OVERLAY, DST_STABLE)

    # Optionally also publish a dated snapshot for history
    if latest:
        d = date.today().isoformat()
        dst_dated = ANALYSIS_DIR / f"fx_overlay_{d}.png"
        shutil.copy2(SRC_OVERLAY, dst_dated)
        return dst_dated

    if target_date:
        dst_dated = ANALYSIS_DIR / f"fx_overlay_{target_date}.png"
        shutil.copy2(SRC_OVERLAY, dst_dated)
        return dst_dated

    return DST_STABLE


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (also writes fx_overlay_YYYY-MM-DD.png)")
    ap.add_argument("--latest", action="store_true", help="Also write fx_overlay_<today>.png")
    args = ap.parse_args()

    out = publish(args.date, args.latest)
    print("[OK] published FX overlay")
    print(f"  src: {SRC_OVERLAY}")
    print(f"  dst: {DST_STABLE}")
    if out != DST_STABLE:
        print(f"  dated: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# scripts/find_prediction_score_sources.py
# Find where numeric prediction scores live in GenesisPrediction_v2 repo.
#
# Run:
#   .\.venv\Scripts\python.exe scripts\find_prediction_score_sources.py

from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
ANALYSIS_DIR = REPO_ROOT / "analysis"
OUT_DIR = ANALYSIS_DIR / "prediction_backtests"

JSON_GLOB_IGNORE = {".venv", "node_modules", "dist", ".git", "__pycache__"}

TARGET_KEYS = {
    "risk",
    "positive",
    "pos",
    "uncertainty",
    "unc",
    "net",
    "confidence",
    "regime",
    "anchors",
    "signals",
    "scenario",
    "prediction",
    "predictions",
    "sentiment",
}

DATE_IN_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _safe_float(x: Any):
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def _read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _walk(obj: Any, found: Dict[str, int], numeric_found: Dict[str, int], depth: int, max_depth: int):
    if depth > max_depth:
        return

    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in TARGET_KEYS:
                found[lk] = found.get(lk, 0) + 1
                fv = _safe_float(v)
                if fv is not None:
                    numeric_found[lk] = numeric_found.get(lk, 0) + 1
            _walk(v, found, numeric_found, depth + 1, max_depth)

    elif isinstance(obj, list):
        for v in obj[:8]:
            _walk(v, found, numeric_found, depth + 1, max_depth)


def scan_file(p: Path) -> Tuple[Dict[str, int], Dict[str, int], str]:
    try:
        j = _read_json(p)
    except Exception:
        return {}, {}, "unreadable"

    found: Dict[str, int] = {}
    numeric: Dict[str, int] = {}
    _walk(j, found, numeric, 0, 6)

    if isinstance(j, dict):
        top = list(j.keys())[:25]
        shape = f"dict top_keys={top}"
    elif isinstance(j, list):
        shape = f"list len={len(j)}"
    else:
        shape = f"type={type(j).__name__}"
    return found, numeric, shape


def iter_json_files() -> List[Path]:
    out: List[Path] = []
    for base in [DATA_DIR, ANALYSIS_DIR]:
        if not base.exists():
            continue
        for p in base.rglob("*.json"):
            parts = {x.lower() for x in p.parts}
            if parts & JSON_GLOB_IGNORE:
                continue
            out.append(p)
    return sorted(out)


def score_rank(found: Dict[str, int], numeric: Dict[str, int]) -> int:
    score = 0
    for k in ["risk", "positive", "pos", "uncertainty", "unc", "net", "confidence", "regime"]:
        score += 10 * numeric.get(k, 0)
        score += 2 * found.get(k, 0)
    for k in ["signals", "scenario", "prediction", "predictions", "sentiment"]:
        score += 5 * numeric.get(k, 0)
        score += 3 * found.get(k, 0)
    return score


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / f"score_sources_scan_{ts}.txt"

    files = iter_json_files()
    rows = []

    for p in files:
        found, numeric, shape = scan_file(p)
        if not found and not numeric:
            continue
        r = score_rank(found, numeric)
        if r <= 0:
            continue
        rows.append((r, p, found, numeric, shape))

    rows.sort(key=lambda x: x[0], reverse=True)

    lines: List[str] = []
    lines.append("GenesisPrediction v2 - score sources scan")
    lines.append(f"generated_at_local: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"repo_root: {REPO_ROOT}")
    lines.append(f"scanned_files_total: {len(files)}")
    lines.append(f"candidates_found: {len(rows)}")
    lines.append("")
    lines.append("TOP CANDIDATES (ranked)")
    lines.append("------------------------------------------------------------")

    keys_of_interest = ["risk", "positive", "pos", "uncertainty", "unc", "net", "confidence", "regime", "sentiment", "signals", "prediction"]
    for i, (r, p, found, numeric, shape) in enumerate(rows[:40], start=1):
        lines.append(f"[{i:02d}] score={r}  path={p}")
        hi = []
        for k in keys_of_interest:
            if k in found or k in numeric:
                hi.append(f"{k}:found={found.get(k,0)}/num={numeric.get(k,0)}")
        lines.append("     " + "  ".join(hi) if hi else "     (no highlights?)")
        lines.append(f"     shape: {shape}")
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("[OK] wrote:", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

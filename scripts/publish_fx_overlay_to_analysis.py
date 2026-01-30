# scripts/publish_fx_overlay_to_analysis.py
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_last_fx_date(dashboard_csv: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    dashboard CSV format (expected):
      date, usd_jpy, ..., jpy_thb, ..., decision, ...
    Returns:
      (last_date_str, error_reason)
    """
    if not dashboard_csv.exists():
        return None, f"dashboard_csv_not_found:{dashboard_csv}"

    last_date: Optional[str] = None
    try:
        with dashboard_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                d = (row[0] or "").strip()
                if len(d) == 10 and d[4] == "-" and d[7] == "-":
                    last_date = d
    except Exception as e:
        return None, f"dashboard_csv_read_error:{e}"

    if not last_date:
        return None, "dashboard_csv_no_date_rows"
    return last_date, None


def parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    date = args.date.strip()
    if len(date) != 10:
        raise SystemExit("invalid --date. use YYYY-MM-DD")

    repo = Path(".")
    src_png = repo / "data" / "fx" / "jpy_thb_remittance_overlay.png"
    dashboard_csv = repo / "data" / "fx" / "jpy_thb_remittance_dashboard.csv"

    analysis_dir = repo / "data" / "world_politics" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # 1) Copy PNG (fixed + dated)
    if not src_png.exists():
        raise SystemExit(f"source png not found: {src_png}")

    dst_fixed = analysis_dir / "jpy_thb_remittance_overlay.png"
    dst_dated = analysis_dir / f"fx_overlay_{date}.png"

    # atomic copy (tmp -> rename)
    for dst in (dst_fixed, dst_dated):
        tmp = dst.with_suffix(dst.suffix + ".tmp")
        tmp.write_bytes(src_png.read_bytes())
        tmp.replace(dst)

    # 2) Create status json (stale/missing)
    last_fx_date, reason = read_last_fx_date(dashboard_csv)
    stale = False
    if last_fx_date:
        try:
            stale = parse_date(last_fx_date) < parse_date(date)
        except Exception:
            stale = True
            reason = (reason or "") + "|date_parse_error"
    else:
        stale = True

    status = {
        "target_date": date,
        "stale": bool(stale),
        "last_fx_date": last_fx_date,
        "reason": reason or "",
        "src_png": str(src_png).replace("\\", "/"),
        "src_png_sha256": sha256_file(src_png),
        "published_fixed": str(dst_fixed).replace("\\", "/"),
        "published_dated": str(dst_dated).replace("\\", "/"),
        "published_at": datetime.now().isoformat(timespec="seconds"),
    }

    import json

    status_path = analysis_dir / f"fx_overlay_status_{date}.json"
    latest_path = analysis_dir / "fx_overlay_status_latest.json"

    for p in (status_path, latest_path):
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)

    print("[OK] published FX overlay")
    print(f"  src:   {src_png}")
    print(f"  dst:   {dst_fixed}")
    print(f"  dated: {dst_dated}")
    print(f"[OK] fx status: stale={stale} last_fx_date={last_fx_date} reason={reason or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

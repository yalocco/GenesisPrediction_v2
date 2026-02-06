# scripts/publish_daily_news_latest.py
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "world_politics"
ANALYSIS_DIR = RAW_DIR / "analysis"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    src = RAW_DIR / f"{args.date}.json"
    if not src.exists():
        raise SystemExit(f"[ERR] missing raw news: {src}")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    dst_latest = ANALYSIS_DIR / "daily_news_latest.json"
    dst_dated = ANALYSIS_DIR / f"daily_news_{args.date}.json"

    # 読めることを保証してからコピー（壊れたJSONをlatestにしない）
    obj = json.loads(src.read_text(encoding="utf-8"))
    txt = json.dumps(obj, ensure_ascii=False, indent=2)

    dst_latest.write_text(txt, encoding="utf-8")
    dst_dated.write_text(txt, encoding="utf-8")

    print("[OK] published daily_news_latest")
    print(f"  src : {src}")
    print(f"  latest: {dst_latest}")
    print(f"  dated : {dst_dated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

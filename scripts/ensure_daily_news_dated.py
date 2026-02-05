from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="yyyy-mm-dd")
    args = ap.parse_args()

    date = args.date

    # candidates
    dst = Path(f"data/world_politics/analysis/daily_news_{date}.json")

    candidates = [
        Path(f"data/world_politics/{date}.json"),
        Path(f"data/world_politics/analysis/daily_news_{date}.json"),
        Path("data/world_politics/analysis/daily_news_latest.json"),
        Path(f"data/world_politics/analysis/daily_news_{date}.json"),  # duplicated but harmless
    ]

    if dst.exists():
        print(f"[OK] exists: {dst}")
        return 0

    src = next((p for p in candidates if p.exists()), None)
    if src is None:
        print("[WARN] no source daily news found; nothing to ensure")
        return 0

    dst.parent.mkdir(parents=True, exist_ok=True)

    # sanity load/save to normalize encoding
    obj = json.loads(src.read_text(encoding="utf-8"))
    dst.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] ensured: {dst} (from {src})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

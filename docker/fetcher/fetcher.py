# docker/fetcher/fetcher.py
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests


# ----------------------------
# Config
# ----------------------------
API_KEY = os.getenv("NEWSAPI_KEY")
QUERY = os.getenv("NEWS_QUERY", "world politics")
LANG = os.getenv("NEWS_LANG", "en")
PAGE_SIZE = int(os.getenv("NEWS_PAGE_SIZE", "50"))
TIMEOUT_SEC = int(os.getenv("NEWS_TIMEOUT_SEC", "30"))

OUT_DIR = Path("/data/world_politics")

if not API_KEY:
    raise RuntimeError("NEWSAPI_KEY is not set")

NEWSAPI_URL = "https://newsapi.org/v2/everything"


# ----------------------------
# Helpers
# ----------------------------
def utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def atomic_write_json(final_path: Path, payload: Dict[str, Any]) -> None:
    """
    LAST SAFETY DEVICE (tmp -> rename):
      1) write to tmp (same dir)
      2) flush + fsync (file)
      3) read-back validate json
      4) os.replace(tmp, final)  (atomic on same filesystem)
      5) best-effort fsync(dir) on Linux
    """
    final_path.parent.mkdir(parents=True, exist_ok=True)

    # unique tmp name (avoid collision if multiple runs)
    stamp = int(time.time() * 1000)
    pid = os.getpid()
    tmp_path = final_path.with_name(f"{final_path.name}.tmp.{pid}.{stamp}")

    # cleanup old tmp files for same target (best-effort)
    try:
        for p in final_path.parent.glob(f"{final_path.name}.tmp.*"):
            # only delete old ones; keep "just-created" safe
            if p != tmp_path:
                p.unlink(missing_ok=True)
    except Exception:
        pass

    try:
        # 1) write tmp
        with tmp_path.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")  # nicer & helps some tools
            f.flush()
            os.fsync(f.fileno())

        # 2) read-back validate (prevents “empty/half file” becoming final)
        #    If this fails, we DO NOT touch final_path.
        with tmp_path.open("r", encoding="utf-8") as rf:
            _ = json.load(rf)

        # 3) atomic replace
        os.replace(tmp_path, final_path)

        # 4) best-effort fsync dir (Linux container)
        try:
            if hasattr(os, "O_DIRECTORY"):
                fd = os.open(str(final_path.parent), os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
        except Exception:
            pass

    finally:
        # if anything failed before replace, tmp might remain
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def fetch_news() -> Dict[str, Any]:
    params = {
        "q": QUERY,
        "language": LANG,
        "pageSize": PAGE_SIZE,
        "sortBy": "publishedAt",
        "apiKey": API_KEY,
    }
    res = requests.get(NEWSAPI_URL, params=params, timeout=TIMEOUT_SEC)
    res.raise_for_status()
    return res.json()


def main() -> None:
    data = fetch_news()

    today = utc_today()
    out_path = OUT_DIR / f"{today}.json"

    payload: Dict[str, Any] = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "query": QUERY,
        "totalResults": data.get("totalResults"),
        "articles": data.get("articles", []) or [],
    }

    # write with last safety device
    atomic_write_json(out_path, payload)

    print(f"[OK] saved {len(payload['articles'])} articles to {out_path}")


if __name__ == "__main__":
    main()

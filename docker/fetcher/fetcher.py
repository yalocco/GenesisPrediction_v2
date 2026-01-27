# docker/fetcher/fetcher.py
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests


# ----------------------------
# Config
# ----------------------------
API_KEY = os.getenv("NEWSAPI_KEY", "").strip()
QUERY = os.getenv("NEWS_QUERY", "world politics").strip()
LANG = os.getenv("NEWS_LANG", "en").strip()
PAGE_SIZE = int(os.getenv("NEWS_PAGE_SIZE", "50"))

OUT_DIR = Path(os.getenv("NEWS_OUT_DIR", "/data/world_politics"))

NEWSAPI_URL = "https://newsapi.org/v2/everything"


# ----------------------------
# Helpers
# ----------------------------
def utc_today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_payload(payload: Dict[str, Any]) -> None:
    # 最低限の形だけ保証（ここが崩れてたら“保存しない”）
    if not isinstance(payload, dict):
        raise ValueError("payload is not a dict")
    if "articles" not in payload:
        raise ValueError("payload missing 'articles'")
    if not isinstance(payload["articles"], list):
        raise ValueError("'articles' is not a list")


def atomic_write_json(path: Path, obj: Any) -> None:
    """
    安全装置の本体：
    - 同一ディレクトリに tmp を作る（rename/replace が原子的に効くため）
    - 書き込み→flush→fsync
    - 最後に os.replace で本番へ（同名があっても置換）
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Windows/Unixとも “同一dir” に tmp を置くのが重要
    tmp_fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)

    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # ここで “一発入れ替え”
        os.replace(tmp_path, path)

    except Exception:
        # 失敗したら tmp を消して終わり（本番は汚さない）
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
        raise


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    if not API_KEY:
        raise RuntimeError("NEWSAPI_KEY is not set")

    params = {
        "q": QUERY,
        "language": LANG,
        "pageSize": PAGE_SIZE,
        "sortBy": "publishedAt",
        "apiKey": API_KEY,
    }

    res = requests.get(NEWSAPI_URL, params=params, timeout=30)
    res.raise_for_status()
    data = res.json()

    today = utc_today_str()
    out_path = OUT_DIR / f"{today}.json"

    payload: Dict[str, Any] = {
        "fetched_at": utc_now_iso(),
        "query": QUERY,
        "totalResults": data.get("totalResults"),
        "articles": data.get("articles", []) or [],
    }

    validate_payload(payload)
    atomic_write_json(out_path, payload)

    print(f"[OK] saved {len(payload['articles'])} articles to {out_path}")


if __name__ == "__main__":
    main()

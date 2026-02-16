# scripts/ensure_daily_news_dated.py
"""
Ensure dated daily news artifacts exist for a given date.

Goal (self-healing):
- Ensure data/world_politics/analysis/daily_news_YYYY-MM-DD.json exists
- Ensure data/world_politics/analysis/daily_news_YYYY-MM-DD.html exists

Design notes:
- This script is intentionally conservative: it never touches GUI/CSS/HTML files.
- It generates a simple, standalone HTML from the dated JSON so Data Health can converge to OK.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from datetime import datetime


def repo_root() -> Path:
    # scripts/ensure_daily_news_dated.py -> repo root
    return Path(__file__).resolve().parents[1]


def analysis_dir(root: Path) -> Path:
    return root / "data" / "world_politics" / "analysis"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_items(obj: object) -> list[dict]:
    """
    Try to extract news items robustly from various schemas.
    We only need: title, url, source, published/ts.
    """
    items: list[dict] = []

    if isinstance(obj, dict):
        # Common shapes
        if isinstance(obj.get("items"), list):
            raw = obj["items"]
        elif isinstance(obj.get("articles"), list):
            raw = obj["articles"]
        elif isinstance(obj.get("events"), list):
            raw = obj["events"]
        else:
            # Could be already a list-like dict? fallback
            raw = []
        for it in raw:
            if isinstance(it, dict):
                items.append(it)
        return items

    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict):
                items.append(it)
        return items

    return items


def pick(it: dict, keys: list[str], default: str = "") -> str:
    for k in keys:
        v = it.get(k)
        if v is None:
            continue
        if isinstance(v, (str, int, float)):
            s = str(v).strip()
            if s:
                return s
    return default


def to_html(date_str: str, json_path: Path, html_path: Path) -> None:
    obj = load_json(json_path)
    items = extract_items(obj)

    title = f"Daily News {date_str}"
    lines: list[str] = []
    lines.append("<!doctype html>")
    lines.append('<html lang="en">')
    lines.append("<head>")
    lines.append('<meta charset="utf-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    lines.append(f"<title>{html.escape(title)}</title>")
    # Minimal inline style (self-contained; does not touch app.css)
    lines.append(
        "<style>"
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
        "margin:24px;line-height:1.45}"
        "h1{margin:0 0 8px 0}"
        ".meta{color:#666;margin:0 0 16px 0;font-size:14px}"
        "ol{padding-left:18px}"
        "li{margin:10px 0}"
        ".src{color:#666;font-size:12px}"
        "</style>"
    )
    lines.append("</head>")
    lines.append("<body>")
    lines.append(f"<h1>{html.escape(title)}</h1>")
    lines.append(
        f'<p class="meta">source: {html.escape(str(json_path.as_posix()))} / '
        f'generated_at: {html.escape(datetime.now().isoformat(timespec="seconds"))}</p>'
    )

    if not items:
        lines.append("<p><b>WARN</b>: No items found in JSON.</p>")
    else:
        lines.append("<ol>")
        for it in items:
            t = pick(it, ["title", "headline", "name"], default="(no title)")
            u = pick(it, ["url", "link", "source_url"], default="")
            src = pick(it, ["source", "publisher", "site", "domain"], default="")
            ts = pick(it, ["published_at", "published", "time", "ts", "date"], default="")

            t_esc = html.escape(t)
            src_esc = html.escape(src)
            ts_esc = html.escape(ts)

            if u:
                u_esc = html.escape(u, quote=True)
                lines.append(f'<li><a href="{u_esc}" target="_blank" rel="noopener noreferrer">{t_esc}</a>')
            else:
                lines.append(f"<li>{t_esc}")

            meta_bits = []
            if src_esc:
                meta_bits.append(src_esc)
            if ts_esc:
                meta_bits.append(ts_esc)
            if meta_bits:
                lines.append(f'<div class="src">{" / ".join(meta_bits)}</div>')
            lines.append("</li>")
        lines.append("</ol>")

    lines.append("</body>")
    lines.append("</html>")
    html_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    root = repo_root()
    adir = analysis_dir(root)
    adir.mkdir(parents=True, exist_ok=True)

    date_str = args.date.strip()

    json_path = adir / f"daily_news_{date_str}.json"
    html_path = adir / f"daily_news_{date_str}.html"

    if not json_path.exists():
        print(f"[WARN] missing: {json_path.as_posix()}")
        print("[HINT] run scripts/publish_daily_news_latest.py --date YYYY-MM-DD first")
        return 2

    print(f"[OK] exists: {json_path.as_posix()}")

    if html_path.exists():
        print(f"[OK] exists: {html_path.as_posix()}")
        return 0

    to_html(date_str, json_path, html_path)
    print(f"[OK] created: {html_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

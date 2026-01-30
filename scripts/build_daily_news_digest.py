# scripts/build_daily_news_digest.py
from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path
from typing import Any, Optional, Tuple


# ----------------------------
# Paths (repo-relative)
# ----------------------------
ROOT = Path(".")
DATA_DIR = ROOT / "data" / "world_politics"
ANALYSIS_DIR = DATA_DIR / "analysis"

OUT_LATEST_HTML = ANALYSIS_DIR / "daily_news_digest_latest.html"


# ----------------------------
# Helpers
# ----------------------------
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _extract_date_from_name(p: Path) -> Optional[str]:
    m = DATE_RE.search(p.name)
    return m.group(1) if m else None


def _safe_read_json(p: Path) -> Optional[dict]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _list_dated_json_files(dir_path: Path) -> list[Path]:
    if not dir_path.exists():
        return []
    cands = []
    for p in dir_path.glob("*.json"):
        d = _extract_date_from_name(p)
        if d:
            cands.append((d, p))
    cands.sort(key=lambda x: x[0])
    return [p for _, p in cands]


@dataclass
class ResolvedInput:
    in_path: Path
    resolved_date: str
    payload: dict


def resolve_input(requested_date: str) -> ResolvedInput:
    """
    We want to build digest even if the "expected" dated raw file is missing.
    Priority:
      1) data/world_politics/{date}.json
      2) data/world_politics/analysis/daily_news_{date}.json
      3) data/world_politics/analysis/daily_news_latest.json
      4) data/world_politics/analysis/latest.json
      5) newest dated json in data/world_politics/*.json
    """
    candidates: list[Tuple[Path, Optional[str]]] = [
        (DATA_DIR / f"{requested_date}.json", requested_date),
        (ANALYSIS_DIR / f"daily_news_{requested_date}.json", requested_date),
        (ANALYSIS_DIR / "daily_news_latest.json", None),
        (ANALYSIS_DIR / "latest.json", None),
    ]

    for p, forced_date in candidates:
        if p.exists():
            payload = _safe_read_json(p)
            if isinstance(payload, dict):
                d = forced_date or payload.get("date") or _extract_date_from_name(p) or requested_date
                return ResolvedInput(in_path=p, resolved_date=str(d), payload=payload)

    # fallback: newest dated json under data/world_politics
    dated = _list_dated_json_files(DATA_DIR)
    if dated:
        p = dated[-1]
        payload = _safe_read_json(p) or {}
        d = payload.get("date") or _extract_date_from_name(p) or requested_date
        return ResolvedInput(in_path=p, resolved_date=str(d), payload=payload)

    raise FileNotFoundError(
        f"input not found: tried {DATA_DIR}/{requested_date}.json, "
        f"{ANALYSIS_DIR}/daily_news_{requested_date}.json, "
        f"{ANALYSIS_DIR}/daily_news_latest.json, {ANALYSIS_DIR}/latest.json, "
        f"and any dated json under {DATA_DIR}"
    )


def _pick_articles(payload: dict) -> list[dict]:
    """
    Accept multiple schema shapes:
      - {"articles": [ ... ]} (NewsAPI style)
      - {"items": [ ... ]} (sentiment style - but we handle it anyway)
    """
    if isinstance(payload.get("articles"), list):
        return payload["articles"]
    if isinstance(payload.get("items"), list):
        # normalize keys
        items = []
        for it in payload["items"]:
            if not isinstance(it, dict):
                continue
            items.append(
                {
                    "title": it.get("title"),
                    "url": it.get("url"),
                    "urlToImage": it.get("image_url") or it.get("urlToImage"),
                    "source": {"name": it.get("source")},
                    "publishedAt": it.get("publishedAt"),
                    "description": it.get("description"),
                }
            )
        return items
    return []


def _get_source_name(a: dict) -> str:
    src = a.get("source")
    if isinstance(src, dict):
        return str(src.get("name") or src.get("id") or "")
    if isinstance(src, str):
        return src
    return ""


def _esc(s: Any) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def render_digest_html(d: str, input_path: Path, articles: list[dict]) -> str:
    rows = []
    for a in articles:
        title = _esc(a.get("title") or "(no title)")
        url = _esc(a.get("url") or "")
        src = _esc(_get_source_name(a) or "")
        img = _esc(a.get("urlToImage") or "")
        desc = _esc(a.get("description") or "")
        # small card
        rows.append(
            f"""
            <div class="card">
              <div class="thumb">{f'<img src="{img}" alt="">' if img else ''}</div>
              <div class="body">
                <div class="title"><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></div>
                <div class="meta">{src}</div>
                {f'<div class="desc">{desc}</div>' if desc else ''}
              </div>
            </div>
            """
        )

    items_html = "\n".join(rows) if rows else '<div class="empty">No articles found in input.</div>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Daily News Digest {html.escape(d)}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b0f14;
      --panel: rgba(20, 30, 45, 0.55);
      --panel2: rgba(20, 30, 45, 0.35);
      --stroke: rgba(255,255,255,0.10);
      --text: rgba(255,255,255,0.92);
      --muted: rgba(255,255,255,0.65);
      --link: rgba(130, 200, 255, 0.95);
    }}
    html, body {{
      margin: 0; padding: 0;
      background: radial-gradient(1200px 700px at 20% 10%, rgba(50,120,160,0.20), transparent 60%),
                  radial-gradient(900px 600px at 80% 30%, rgba(120,60,160,0.18), transparent 55%),
                  var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Noto Sans", "Apple Color Emoji","Segoe UI Emoji";
    }}
    .wrap {{
      max-width: 1100px;
      margin: 28px auto;
      padding: 0 18px 40px;
    }}
    .header {{
      background: var(--panel);
      border: 1px solid var(--stroke);
      border-radius: 18px;
      padding: 18px 18px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.35);
    }}
    .h1 {{
      font-size: 26px;
      font-weight: 700;
      letter-spacing: 0.2px;
      margin: 0 0 6px;
    }}
    .sub {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }}
    .grid {{
      margin-top: 14px;
      display: grid;
      gap: 12px;
    }}
    .card {{
      display: grid;
      grid-template-columns: 72px 1fr;
      gap: 12px;
      align-items: start;
      padding: 12px;
      border-radius: 18px;
      border: 1px solid var(--stroke);
      background: var(--panel2);
    }}
    .thumb {{
      width: 72px; height: 72px;
      border-radius: 16px;
      background: rgba(255,255,255,0.06);
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.08);
    }}
    .thumb img {{
      width: 100%; height: 100%;
      object-fit: cover;
      display: block;
    }}
    .title {{
      font-size: 16px;
      font-weight: 650;
      line-height: 1.25;
      margin: 2px 0 6px;
    }}
    .title a {{
      color: var(--text);
      text-decoration: none;
    }}
    .title a:hover {{
      color: var(--link);
      text-decoration: underline;
    }}
    .meta {{
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
    }}
    .desc {{
      font-size: 12px;
      color: rgba(255,255,255,0.72);
      line-height: 1.4;
    }}
    .empty {{
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--stroke);
      background: var(--panel2);
      color: var(--muted);
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="h1">Daily News Digest</div>
      <p class="sub">date: <b>{html.escape(d)}</b> / input: <code>{html.escape(str(input_path))}</code></p>
    </div>
    <div class="grid">
      {items_html}
    </div>
  </div>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=Date.today().isoformat(), help="target date (YYYY-MM-DD)")
    args = ap.parse_args()

    requested = str(args.date)

    resolved = resolve_input(requested)
    articles = _pick_articles(resolved.payload)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_dated = ANALYSIS_DIR / f"daily_news_digest_{resolved.resolved_date}.html"

    html_text = render_digest_html(resolved.resolved_date, resolved.in_path, articles)
    out_dated.write_text(html_text, encoding="utf-8")
    OUT_LATEST_HTML.write_text(html_text, encoding="utf-8")

    print("[OK] digest built")
    print(f"  requested: {requested}")
    print(f"  input:     {resolved.in_path}")
    print(f"  resolved:  {resolved.resolved_date}")
    print(f"  out:       {out_dated}")
    print(f"  latest:    {OUT_LATEST_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


# --- Priority keyword sets (B -> A) ---
SECURITY_TERMS = {
    "military","defense","security","war","conflict","strike","attack","escalation",
    "missile","nuclear","drone","weapon","air force","navy","army","troops",
    "sanction","sanctions","ceasefire","hostage","terror","insurgent",
    "taiwan","strait","south china sea","red sea","gaza","ukraine","russia","iran","israel","yemen","hezbollah",
    "ship","shipping","blockade","intercept","airstrike","bombing","artillery","mobilization",
}

FIN_STOCK_TERMS = {
    "market","markets","stock","stocks","equity","equities","share","shares",
    "index","indices","dow","nasdaq","s&p","nikkei","topix",
    "earnings","guidance","revenue","profit","loss","valuation","rally","selloff","volatility",
    "ipo","merger","acquisition","m&a","sell-off","risk-off","risk on",
}

FIN_FX_TERMS = {
    "fx","forex","currency","currencies","dollar","usd","eur","euro","jpy","yen","gbp","pound","cny","yuan",
    "exchange rate","devaluation","appreciation","depreciation","intervention",
    "usd/jpy","eur/usd","dxy",
}

FIN_ENERGY_TERMS = {
    "oil","crude","brent","wti","gas","lng","energy","opec","pipeline","shipping","tanker",
    "refinery","barrel","production cut","output",
}

FIN_RATES_TERMS = {
    "bond","bonds","yield","yields","rate","rates","interest","treasury","gilts",
    "inflation","cpi","ppi","central bank","fed","ecb","boj","bank of japan",
    "tightening","easing","cut rates","rate cut","hike","rate hike",
}

ENTERTAINMENT_TERMS = {
    "movie","film","actor","actress","celebrity","music","concert","album","box office",
    "tv show","netflix","hollywood","awards","oscar","grammy","red carpet",
}

JAPAN_TERMS = {
    "japan","tokyo","boj","bank of japan","yen","jpy","nikkei","topix",
    "japanese","fukushima","tokyo stock exchange","tse",
}


def _norm_text(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s)
    return s


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            out.append(json.loads(s))
        except Exception:
            continue
    return out


def pick(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def domain_from_url(u: str) -> str:
    try:
        p = urlparse(u)
        return p.netloc or ""
    except Exception:
        return ""


def first_line(s: str, n: int = 160) -> str:
    s = " ".join((s or "").split())
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def classify_tags(title: str, summary: str, domain: str) -> List[str]:
    t = _norm_text(f"{title} {summary} {domain}")
    tags: List[str] = []

    if any(k in t for k in SECURITY_TERMS):
        tags.append("SECURITY")

    # Finance priority: A/B first
    if any(k in t for k in FIN_STOCK_TERMS):
        tags.append("FIN-STOCKS")
    if any(k in t for k in FIN_FX_TERMS):
        tags.append("FIN-FX")

    # Next priority: C/D
    if any(k in t for k in FIN_ENERGY_TERMS):
        tags.append("FIN-ENERGY")
    if any(k in t for k in FIN_RATES_TERMS):
        tags.append("FIN-RATES")

    if any(k in t for k in JAPAN_TERMS):
        tags.append("JP")

    if any(k in t for k in ENTERTAINMENT_TERMS):
        tags.append("ENT")

    return tags


def score_item(tags: List[str]) -> int:
    score = 0

    # Security: highest
    if "SECURITY" in tags:
        score += 60

    # Finance: A/B strongest
    if "FIN-STOCKS" in tags:
        score += 50
    if "FIN-FX" in tags:
        score += 50

    # Finance: C/D next
    if "FIN-ENERGY" in tags:
        score += 30
    if "FIN-RATES" in tags:
        score += 30

    # Japan relevance: modest boost
    if "JP" in tags:
        score += 15

    # Entertainment: push down (do not remove)
    if "ENT" in tags:
        score -= 40

    return score


def render_md(date: str, items: List[Dict[str, Any]], out_path: Path) -> None:
    lines: List[str] = []
    lines.append(f"# Daily News Digest — {date}")
    lines.append("")
    lines.append(f"- items: {len(items)}")
    lines.append("")

    for i, ev in enumerate(items, 1):
        url = str(pick(ev, "url", "link") or "").strip()
        title = str(pick(ev, "title", "headline") or "(no title)").strip()
        summary = str(pick(ev, "summary", "one_liner", "description", "snippet") or "").strip()
        dom = domain_from_url(url) if url else str(pick(ev, "source", "domain") or "")

        tags = classify_tags(title, summary, dom)
        tag_s = ", ".join(tags) if tags else ""

        anchors = pick(ev, "anchors", "tokens", "keywords")
        if isinstance(anchors, list):
            anchors_s = ", ".join(str(x) for x in anchors[:12])
        else:
            anchors_s = ""

        lines.append(f"## {i}. {title}")
        if url:
            lines.append(f"- URL: {url}")
        if dom:
            lines.append(f"- Domain: {dom}")
        if tag_s:
            lines.append(f"- Tags: {tag_s}")
        if summary:
            lines.append(f"- Summary: {first_line(summary, 220)}")
        if anchors_s:
            lines.append(f"- Tokens: {anchors_s}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def render_html(date: str, items: List[Dict[str, Any]], out_path: Path) -> None:
    css = """
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
           margin: 24px; background: #0f1115; color: #e7e9ee; }
    h1 { font-size: 22px; margin: 0 0 12px 0; }
    .meta { color: #aeb4c0; margin-bottom: 18px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; }
    .card { background: #151923; border: 1px solid #242a38; border-radius: 14px; padding: 14px; }
    .title { font-size: 15px; font-weight: 650; margin: 0 0 8px 0; line-height: 1.35; }
    .title a { color: #e7e9ee; text-decoration: none; }
    .title a:hover { text-decoration: underline; }
    .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; color: #aeb4c0; font-size: 12px; margin-bottom: 10px; }
    .pill { padding: 2px 8px; border: 1px solid #2a3142; border-radius: 999px; }
    .sum { font-size: 13px; color: #d5d9e2; line-height: 1.45; margin: 0 0 10px 0; }
    .tokens { font-size: 12px; color: #aeb4c0; line-height: 1.4; }
    img.thumb { width: 100%; height: 180px; object-fit: cover; border-radius: 12px; border: 1px solid #242a38; margin-bottom: 10px; background: #0f1115; }
    """
    parts: List[str] = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'/>")
    parts.append(f"<title>Daily News Digest {html.escape(date)}</title>")
    parts.append(f"<style>{css}</style></head><body>")
    parts.append(f"<h1>Daily News Digest — {html.escape(date)}</h1>")
    parts.append(f"<div class='meta'>items: {len(items)}</div>")
    parts.append("<div class='grid'>")

    for ev in items:
        url = str(pick(ev, "url", "link") or "").strip()
        title = str(pick(ev, "title", "headline") or "(no title)").strip()
        summary = str(pick(ev, "summary", "one_liner", "description", "snippet") or "").strip()
        dom = domain_from_url(url) if url else str(pick(ev, "source", "domain") or "")

        # Use image only if present in events
        img_url = str(pick(ev, "image", "thumbnail", "image_url") or "").strip()

        tags = classify_tags(title, summary, dom)

        anchors = pick(ev, "anchors", "tokens", "keywords")
        tokens = ""
        if isinstance(anchors, list):
            tokens = ", ".join(html.escape(str(x)) for x in anchors[:14])

        parts.append("<div class='card'>")
        if img_url:
            parts.append(f"<img class='thumb' src='{html.escape(img_url)}' loading='lazy'/>")

        if url:
            parts.append(
                f"<div class='title'><a href='{html.escape(url)}' target='_blank' rel='noreferrer'>"
                f"{html.escape(title)}</a></div>"
            )
        else:
            parts.append(f"<div class='title'>{html.escape(title)}</div>")

        parts.append("<div class='row'>")
        if dom:
            parts.append(f"<span class='pill'>{html.escape(dom)}</span>")
        for tg in tags:
            parts.append(f"<span class='pill'>{html.escape(tg)}</span>")
        parts.append("</div>")

        if summary:
            parts.append(f"<p class='sum'>{html.escape(first_line(summary, 260))}</p>")
        if tokens:
            parts.append(f"<div class='tokens'><b>Tokens:</b> {tokens}</div>")

        parts.append("</div>")

    parts.append("</div></body></html>")
    out_path.write_text("".join(parts), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (optional; default: infer latest events file)")
    ap.add_argument("--dir", default="data/world_politics/analysis", help="analysis dir")
    ap.add_argument("--limit", type=int, default=40, help="max cards")
    args = ap.parse_args()

    base = Path(args.dir)
    if not base.exists():
        print(f"[ERR] dir not found: {base}")
        return 2

    date = args.date.strip()
    if date:
        ev_path = base / f"events_{date}.jsonl"
    else:
        candidates = sorted(base.glob("events_*.jsonl"))
        if not candidates:
            print("[SKIP] no events_*.jsonl")
            return 0
        ev_path = candidates[-1]
        date = ev_path.stem.replace("events_", "")

    events = read_jsonl(ev_path)
    if not events:
        print(f"[SKIP] no events in {ev_path.name}")
        return 0

    def sort_key(ev: Dict[str, Any]) -> Tuple[int, int, int]:
        url = str(pick(ev, "url", "link") or "").strip()
        title = str(pick(ev, "title", "headline") or "").strip()
        summary = str(pick(ev, "summary", "one_liner", "description", "snippet") or "").strip()
        dom = domain_from_url(url) if url else str(pick(ev, "source", "domain") or "")

        tags = classify_tags(title, summary, dom)
        s = score_item(tags)

        has_url = 1 if url else 0
        has_title = 1 if title else 0

        # Prefer "news-like" items if score ties
        return (s, has_url + has_title, has_title)

    events_sorted = sorted(events, key=sort_key, reverse=True)[: max(1, args.limit)]

    md_out = base / f"daily_news_{date}.md"
    html_out = base / f"daily_news_{date}.html"

    render_md(date, events_sorted, md_out)
    render_html(date, events_sorted, html_out)

    print(f"[DONE] md   -> {md_out}")
    print(f"[DONE] html -> {html_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

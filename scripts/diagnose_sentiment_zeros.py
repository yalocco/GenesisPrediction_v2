# scripts/diagnose_sentiment_zeros.py
"""
Diagnose sentiment zeros / fallback coverage for a given day.

Fixes:
- Robustly reads daily_news JSON in one of:
  A) {"items":[...]}
  B) {"articles":[...]}
  C) [...] (list at root)
- Classification is based on sentiment item "reason" if present:
    - fallback_background => ALL_ZERO (background)
    - rule_hit*          => HAS_SIGNAL
  Otherwise, falls back to score/raw_score heuristics.

Usage:
  .\.venv\Scripts\python.exe scripts\diagnose_sentiment_zeros.py --news data/world_politics/analysis/daily_news_2026-01-30.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


ANALYSIS_DIR = Path("data/world_politics/analysis")
SENT_LATEST = ANALYSIS_DIR / "sentiment_latest.json"
DIAG_DIR = ANALYSIS_DIR / "diagnostics"
OUT_REPORT_TMPL = DIAG_DIR / "sentiment_zero_report_{date}.csv"

DROP_QUERY_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "ref", "ref_src",
}

EPS = 1e-6


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()

    if url.startswith("//"):
        url = "https:" + url
    elif not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        if "." in url.split("/")[0]:
            url = "https://" + url

    parts = urlsplit(url)
    scheme = (parts.scheme or "https").lower()
    netloc = (parts.netloc or "").lower()

    q = []
    for k, v in parse_qsl(parts.query, keep_blank_values=True):
        if k.lower() in DROP_QUERY_KEYS:
            continue
        q.append((k, v))
    query = urlencode(q, doseq=True)

    fragment = ""

    path = parts.path or ""
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunsplit((scheme, netloc, path, query, fragment))


def extract_news_items(news_json: Any) -> List[Dict[str, Any]]:
    if news_json is None:
        return []
    if isinstance(news_json, list):
        return [x for x in news_json if isinstance(x, dict)]
    if isinstance(news_json, dict):
        if isinstance(news_json.get("items"), list):
            return [x for x in news_json["items"] if isinstance(x, dict)]
        if isinstance(news_json.get("articles"), list):
            return [x for x in news_json["articles"] if isinstance(x, dict)]
        # best-effort nested
        for key in ("data", "result", "payload", "news"):
            inner = news_json.get(key)
            if isinstance(inner, dict):
                if isinstance(inner.get("items"), list):
                    return [x for x in inner["items"] if isinstance(x, dict)]
                if isinstance(inner.get("articles"), list):
                    return [x for x in inner["articles"] if isinstance(x, dict)]
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
    return []


@dataclass
class Counts:
    all_zero: int
    has_signal: int
    only_unc: int


def classify_sent_item(it: Dict[str, Any]) -> str:
    """
    Returns one of: ALL_ZERO, HAS_SIGNAL, ONLY_UNC
    Priority:
      1) reason field (new spec)
      2) raw_score / score heuristic (backward compatibility)
    """
    reason = str(it.get("reason") or "").strip().lower()

    if reason == "fallback_background":
        return "ALL_ZERO"
    if reason.startswith("rule_hit"):
        return "HAS_SIGNAL"

    # Backward fallback:
    raw = it.get("raw_score", None)
    score = it.get("score", it.get("sentiment", 0.0))
    unc = it.get("uncertainty", it.get("unc", 0.0))

    try:
        raw_f = float(raw) if raw is not None else None
    except Exception:
        raw_f = None

    try:
        score_f = float(score)
    except Exception:
        score_f = 0.0

    try:
        unc_f = float(unc)
    except Exception:
        unc_f = 0.0

    if raw_f is not None and abs(raw_f) > EPS:
        return "HAS_SIGNAL"
    if abs(score_f) <= EPS and unc_f > EPS:
        return "ONLY_UNC"
    if abs(score_f) <= EPS:
        return "ALL_ZERO"
    # Non-zero but no reason — treat as signal
    return "HAS_SIGNAL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--news", required=True, help="Path to daily_news_YYYY-MM-DD.json")
    ap.add_argument("--sent", default=str(SENT_LATEST), help="Path to sentiment_latest.json (default: analysis/sentiment_latest.json)")
    ap.add_argument("--eps", type=float, default=EPS, help="epsilon for float comparisons")
    args = ap.parse_args()

    news_path = Path(args.news)
    sent_path = Path(args.sent)

    if not sent_path.exists():
        raise FileNotFoundError(f"sentiment not found: {sent_path}")
    if not news_path.exists():
        raise FileNotFoundError(f"news not found: {news_path}")

    sent = load_json(sent_path)
    print(f"[OK] loaded: {sent_path}")

    date_str = str(sent.get("date") or "")
    s_items = sent.get("items", []) if isinstance(sent, dict) else []
    print(f"[OK] date={date_str} items={len(s_items)} eps={args.eps:g}")

    # classify sentiment
    c_all = c_sig = c_unc = 0
    for it in s_items:
        cls = classify_sent_item(it)
        if cls == "ALL_ZERO":
            c_all += 1
        elif cls == "HAS_SIGNAL":
            c_sig += 1
        else:
            c_unc += 1

    print(f"  - ALL_ZERO: {c_all}")
    print(f"  - HAS_SIGNAL: {c_sig}")
    print(f"  - ONLY_UNC: {c_unc}")

    # load news + overlap
    news_json = load_json(news_path)
    n_items = extract_news_items(news_json)

    n_norms = [normalize_url((x.get("url") or "").strip()) for x in n_items]
    n_norms = [u for u in n_norms if u]

    s_norms = [str(x.get("norm_url") or "").strip() for x in s_items]
    s_norms = [u for u in s_norms if u]

    n_set = set(n_norms)
    s_set = set(s_norms)
    overlap = len(n_set & s_set)

    print(f"[NEWS] items={len(n_items)} unique_norm_urls={len(n_set)} | [SENT] items={len(s_items)} unique_norm_urls={len(s_set)} | overlap={overlap}")

    # write CSV report
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = Path(str(OUT_REPORT_TMPL).format(date=date_str or "unknown"))
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "class", "score", "raw_score", "uncertainty", "reason", "norm_url", "title"])
        for it in s_items:
            cls = classify_sent_item(it)
            w.writerow([
                date_str,
                cls,
                it.get("score", it.get("sentiment")),
                it.get("raw_score"),
                it.get("uncertainty"),
                it.get("reason"),
                it.get("norm_url"),
                it.get("title"),
            ])

    print(f"[OK] wrote: {out_csv}")

    if len(n_set) > 0 and overlap == len(n_set):
        print("[OK] URL overlap is 100% (join stable).")
    elif len(n_set) == 0:
        print("[HINT] NEWS items=0. daily_news JSON shape may be different; this script now supports items/articles/root-list, so check if file is empty.")
    else:
        print("[HINT] URL overlap not 100% -> check normalize_url consistency between builders.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

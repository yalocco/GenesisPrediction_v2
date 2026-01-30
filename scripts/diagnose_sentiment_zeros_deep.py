#!/usr/bin/env python3
# scripts/diagnose_sentiment_zeros_deep.py
#
# Purpose:
#   Deeper diagnosis for why many sentiment items show all zeros.
#   - Confirms join coverage vs daily_news (normalized URL overlap)
#   - Checks field coverage (title/description/content/image_url) per category
#   - Emits token-frequency summaries to see what "ALL_ZERO" articles look like
#
# Run (PowerShell):
#   .\.venv\Scripts\python.exe scripts\diagnose_sentiment_zeros_deep.py --news data/world_politics/analysis/daily_news_YYYY-MM-DD.json
#
# Output:
#   data/world_politics/analysis/diagnostics/
#     sentiment_zero_report_deep_YYYY-MM-DD.csv
#     sentiment_zero_tokens_YYYY-MM-DD.csv
#     sentiment_zero_token_summary_YYYY-MM-DD.csv

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, urlparse, urlunparse, urlencode

TRACKING_KEYS_PREFIX = ("utm_",)
TRACKING_KEYS_EXACT = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "ref_url",
}

STOPWORDS = {
    "the","a","an","and","or","to","of","in","on","for","with","as","at","by","from",
    "is","are","was","were","be","been","this","that","these","those","it","its","they","their",
    "you","your","we","our","us","but","not","no","yes","into","over","after","before","about",
    "than","then","now","new","latest","today","says","said","say","will","can","could","would","should",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-']{1,}")


def normalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url)
    except Exception:
        return url.strip()

    scheme = (p.scheme or "http").lower()
    netloc = (p.netloc or "").lower()

    path = p.path or ""
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    q = []
    for k, v in parse_qsl(p.query, keep_blank_values=True):
        kl = (k or "").lower()
        if kl in TRACKING_KEYS_EXACT or kl.startswith(TRACKING_KEYS_PREFIX):
            continue
        q.append((k, v))
    q.sort(key=lambda kv: (kv[0], kv[1]))
    query = urlencode(q, doseq=True)

    return urlunparse((scheme, netloc, path, "", query, ""))


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def as_float(x: Any) -> float:
    try:
        if x is None:
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def clean_text(s: str) -> str:
    s = s or ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(text: str) -> List[str]:
    text = clean_text(text).lower()
    toks = TOKEN_RE.findall(text)
    out: List[str] = []
    for t in toks:
        t = t.strip("-'")
        if not t or len(t) <= 2:
            continue
        if t in STOPWORDS:
            continue
        if t.isdigit():
            continue
        out.append(t)
    return out


def classify_item(item: Dict[str, Any], eps: float) -> str:
    r = abs(as_float(item.get("risk_score")))
    p = abs(as_float(item.get("positive_score")))
    u = abs(as_float(item.get("uncertainty_score")))
    if r <= eps and p <= eps and u <= eps:
        return "ALL_ZERO"
    if r <= eps and p <= eps and u > eps:
        return "ONLY_UNC"
    return "HAS_SIGNAL"


@dataclass
class Coverage:
    has_image: int = 0
    has_desc: int = 0
    has_content: int = 0
    n: int = 0


def cov_add(cov: Coverage, it: Dict[str, Any]) -> None:
    cov.n += 1
    if (it.get("image_url") or "").strip():
        cov.has_image += 1
    if (it.get("description") or "").strip():
        cov.has_desc += 1
    if (it.get("content") or "").strip():
        cov.has_content += 1


def top_tokens(items: List[Dict[str, Any]]) -> Counter:
    c = Counter()
    for it in items:
        text = " ".join([str(it.get("title") or ""), str(it.get("description") or ""), str(it.get("content") or "")])
        c.update(tokenize(text))
    return c


def contrast_rows(name: str, c_bucket: Counter, c_other: Counter, topn: int) -> List[Tuple[str, int, float]]:
    rows: List[Tuple[str, int, float]] = []
    for tok, n in c_bucket.most_common():
        score = n / (c_other.get(tok, 0) + 1)
        rows.append((tok, n, score))
    rows.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return rows[:topn]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sent", default="data/world_politics/analysis/sentiment_latest.json", help="Path to sentiment JSON")
    ap.add_argument("--news", default=None, help="Path to daily_news JSON (recommended). Used to verify join coverage.")
    ap.add_argument("--eps", type=float, default=1e-6, help="Zero epsilon (default 1e-6)")
    ap.add_argument("--max_tokens_per_item", type=int, default=40, help="Max tokens to write per item (default 40)")
    args = ap.parse_args()

    sent_path = Path(args.sent)
    if not sent_path.exists():
        raise FileNotFoundError(f"sentiment not found: {sent_path}")

    sent = load_json(sent_path)
    items = sent.get("items") or []
    if not isinstance(items, list):
        raise ValueError("sentiment JSON: items must be a list")

    date = str(sent.get("date") or "unknown")
    eps = float(args.eps)

    if args.news:
        news_path = Path(args.news)
        if not news_path.exists():
            raise FileNotFoundError(f"news not found: {news_path}")
        news = load_json(news_path)
        nitems = news.get("items") or []
        if not isinstance(nitems, list):
            raise ValueError("news JSON: items must be a list")

        news_norm = {normalize_url(str(x.get("url") or "")) for x in nitems}
        sent_norm = {normalize_url(str(x.get("url") or "")) for x in items}
        news_norm.discard("")
        sent_norm.discard("")
        overlap = len(news_norm & sent_norm)
        print(f"[JOIN] news={len(nitems)} sent={len(items)} overlap={overlap}")
    else:
        print("[JOIN] (skip) --news not provided")

    buckets: Dict[str, List[Dict[str, Any]]] = {"ALL_ZERO": [], "ONLY_UNC": [], "HAS_SIGNAL": []}
    for it in items:
        buckets[classify_item(it, eps)].append(it)

    print(f"[OK] loaded: {sent_path}")
    print(f"[OK] date={date} items={len(items)} eps={eps:g}")
    print(f"  - ALL_ZERO: {len(buckets['ALL_ZERO'])}")
    print(f"  - HAS_SIGNAL: {len(buckets['HAS_SIGNAL'])}")
    print(f"  - ONLY_UNC: {len(buckets['ONLY_UNC'])}")

    cov = {k: Coverage() for k in buckets.keys()}
    for k, lst in buckets.items():
        for it in lst:
            cov_add(cov[k], it)

    for k in ["HAS_SIGNAL", "ONLY_UNC", "ALL_ZERO"]:
        c = cov[k]
        print(f"[COVERAGE] {k}: has_image={c.has_image}/{c.n} has_desc={c.has_desc}/{c.n} has_content={c.has_content}/{c.n}")

    out_dir = Path("data/world_politics/analysis/diagnostics")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / f"sentiment_zero_report_deep_{date}.csv"
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date","category","source","title","url","image_url","risk_score","positive_score","uncertainty_score","net","desc_len","content_len"])
        for k in ["HAS_SIGNAL","ONLY_UNC","ALL_ZERO"]:
            for it in buckets[k]:
                desc = clean_text(str(it.get("description") or ""))
                cont = clean_text(str(it.get("content") or ""))
                w.writerow([
                    date, k, it.get("source") or "", (it.get("title") or "")[:300], it.get("url") or "",
                    it.get("image_url") or "", as_float(it.get("risk_score")), as_float(it.get("positive_score")),
                    as_float(it.get("uncertainty_score")), as_float(it.get("net")), len(desc), len(cont),
                ])

    out_tokens = out_dir / f"sentiment_zero_tokens_{date}.csv"
    with out_tokens.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date","category","source","title","url","tokens"])
        for k in ["HAS_SIGNAL","ONLY_UNC","ALL_ZERO"]:
            for it in buckets[k]:
                text = " ".join([str(it.get("title") or ""), str(it.get("description") or ""), str(it.get("content") or "")])
                toks = tokenize(text)[: int(args.max_tokens_per_item)]
                w.writerow([date, k, it.get("source") or "", (it.get("title") or "")[:200], it.get("url") or "", " ".join(toks)])

    c_sig = top_tokens(buckets["HAS_SIGNAL"])
    c_unc = top_tokens(buckets["ONLY_UNC"])
    c_zero = top_tokens(buckets["ALL_ZERO"])

    out_summary = out_dir / f"sentiment_zero_token_summary_{date}.csv"
    with out_summary.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bucket","token","count","contrast_vs_other"])
        for tok, n, sc in contrast_rows("HAS_SIGNAL_vs_ALL_ZERO", c_sig, c_zero, topn=60):
            w.writerow(["HAS_SIGNAL_vs_ALL_ZERO", tok, n, f"{sc:.3f}"])
        for tok, n, sc in contrast_rows("ALL_ZERO_vs_HAS_SIGNAL", c_zero, c_sig, topn=60):
            w.writerow(["ALL_ZERO_vs_HAS_SIGNAL", tok, n, f"{sc:.3f}"])
        for tok, n, sc in contrast_rows("ONLY_UNC_vs_OTHERS", c_unc, c_sig + c_zero, topn=40):
            w.writerow(["ONLY_UNC_vs_OTHERS", tok, n, f"{sc:.3f}"])

    print(f"[OK] wrote: {out_csv}")
    print(f"[OK] wrote: {out_tokens}")
    print(f"[OK] wrote: {out_summary}")
    print("[HINT] If ALL_ZERO items have description/content but still zero, scoring is likely keyword/threshold based.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

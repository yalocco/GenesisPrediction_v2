# scripts/build_daily_sentiment.py
r"""
Daily Sentiment Builder (C: fallback) + MAX compat for GUI.

What this fixes:
- Some GUI variants read risk/pos/unc from different key names (aliases).
- We output many aliases at:
    top-level, sentiment(obj), scores(obj), sent(obj)

Also:
- When reason == fallback_background, we set unc to a small default (>0)
  so "undetected == uncertain" becomes visible in GUI.

Run:
  ./.venv/Scripts/python.exe scripts/build_daily_sentiment.py --date 2026-01-30
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


ANALYSIS_DIR = Path("data/world_politics/analysis")
DEFAULT_NEWS_TMPL = "daily_news_{date}.json"

OUT_LATEST = "sentiment_latest.json"
OUT_DATED_TMPL = "sentiment_{date}.json"

FALLBACK_SCORE = 0.10
FALLBACK_UNC = 0.20  # <-- NEW: fallback を「未検出＝不確実」として見える化
MIN_ABS_RAW_TO_KEEP = 0.15

POS_WEIGHT = +1.00
NEG_WEIGHT = -1.00
UNC_WEIGHT = +0.60

NEG_TOKENS = {
    "attack", "war", "strike", "crisis", "collapse", "kill", "killed", "dead", "death",
    "terror", "terrorist", "bomb", "explosion", "sanction", "sanctions",
    "inflation", "recession", "default", "missile", "hostage", "riot",
    "shooting", "violence", "clash", "conflict", "invasion", "threat",
    "nuclear", "outage", "blackout", "earthquake", "tsunami", "flood",
}
POS_TOKENS = {
    "deal", "agreement", "peace", "ceasefire", "growth", "recover", "recovery",
    "approval", "aid", "support", "rescue", "success", "stabilize", "stability",
    "increase", "improve", "improvement",
}
UNC_TOKENS = {
    "may", "might", "could", "unclear", "uncertainty", "unknown", "reportedly",
    "alleged", "allegedly", "suspected", "rumor", "speculation",
    "possible", "potential", "expected", "likely", "risk",
}

DROP_QUERY_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "ref", "ref_src",
}


def clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def infer_date_from_news_path(news_path: Path) -> Optional[str]:
    m = re.search(r"daily_news_(\d{4}-\d{2}-\d{2})\.json$", news_path.name)
    return m.group(1) if m else None


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


_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def tokenize_light(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


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
    return []


def pick_image_url(it: Dict[str, Any]) -> str:
    for k in ("image_url", "imageUrl", "urlToImage", "image", "thumbnail", "thumb"):
        v = it.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


@dataclass
class ScoreResult:
    raw_score: float
    unc_score: float
    final_score: float
    reason: str


def score_text(title: str, description: str, content: str, *, fallback_score: float) -> ScoreResult:
    blob = " ".join([title or "", description or "", content or ""]).strip()
    toks = tokenize_light(blob)

    hits_pos = sum(1 for t in toks if t in POS_TOKENS)
    hits_neg = sum(1 for t in toks if t in NEG_TOKENS)
    hits_unc = sum(1 for t in toks if t in UNC_TOKENS)

    raw = (hits_pos * POS_WEIGHT) + (hits_neg * NEG_WEIGHT)
    denom = math.sqrt(max(40.0, float(len(toks))))
    raw = raw / denom

    unc = (hits_unc * UNC_WEIGHT) / denom

    if abs(raw) < MIN_ABS_RAW_TO_KEEP:
        raw = 0.0

    if raw != 0.0:
        final = raw
        reason = "rule_hit"
    else:
        final = float(fallback_score)
        reason = "fallback_background"

    return ScoreResult(
        raw_score=clip(raw, -1.0, 1.0),
        unc_score=clip(unc, 0.0, 1.0),
        final_score=clip(final, -1.0, 1.0),
        reason=reason,
    )


def make_legacy(final_score: float, unc_score: float) -> Dict[str, float]:
    net = float(final_score)
    pos = max(0.0, net)
    risk = max(0.0, -net)
    unc = float(unc_score)
    return {"net": net, "pos": pos, "risk": risk, "unc": unc}


def add_aliases(dst: Dict[str, Any], legacy: Dict[str, float]) -> None:
    # canonical
    dst["net"] = legacy["net"]
    dst["risk"] = legacy["risk"]
    dst["pos"] = legacy["pos"]
    dst["unc"] = legacy["unc"]

    # snake
    dst["risk_score"] = legacy["risk"]
    dst["pos_score"] = legacy["pos"]
    dst["unc_score"] = legacy["unc"]

    # camel
    dst["riskScore"] = legacy["risk"]
    dst["posScore"] = legacy["pos"]
    dst["uncScore"] = legacy["unc"]

    # extra common variants (pos/unc が出ない時の保険)
    dst["positive"] = legacy["pos"]
    dst["positive_score"] = legacy["pos"]
    dst["positiveScore"] = legacy["pos"]

    dst["negative"] = legacy["risk"]
    dst["neg"] = legacy["risk"]
    dst["negative_score"] = legacy["risk"]
    dst["negativeScore"] = legacy["risk"]

    dst["uncert"] = legacy["unc"]
    dst["uncertainty_score"] = legacy["unc"]
    dst["uncertaintyScore"] = legacy["unc"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD")
    ap.add_argument("--news", default=None, help="Path to daily_news_YYYY-MM-DD.json")
    ap.add_argument("--analysis-dir", default=str(ANALYSIS_DIR))
    ap.add_argument("--fallback-score", type=float, default=FALLBACK_SCORE)
    ap.add_argument("--fallback-unc", type=float, default=FALLBACK_UNC)
    args = ap.parse_args()

    analysis_dir = Path(args.analysis_dir)

    news_path: Optional[Path] = Path(args.news) if args.news else None
    date_str = args.date
    if not date_str and news_path:
        date_str = infer_date_from_news_path(news_path)
    if not date_str:
        date_str = Date.today().isoformat()

    if not news_path:
        news_path = analysis_dir / DEFAULT_NEWS_TMPL.format(date=date_str)

    if not news_path.exists():
        raise FileNotFoundError(f"news not found: {news_path}")

    news_json = load_json(news_path)
    news_items = extract_news_items(news_json)

    out_items: List[Dict[str, Any]] = []
    n_rule = 0
    n_fallback = 0

    for it in news_items:
        url = (it.get("url") or "").strip()
        norm = normalize_url(url)
        title = (it.get("title") or "").strip()
        desc = (it.get("description") or "").strip()
        content = (it.get("content") or "").strip()
        image_url = pick_image_url(it)

        sr = score_text(title, desc, content, fallback_score=float(args.fallback_score))

        # if fallback, treat as "undetected => uncertain"
        unc_for_legacy = sr.unc_score
        if sr.reason == "fallback_background":
            unc_for_legacy = max(unc_for_legacy, float(args.fallback_unc))

        legacy = make_legacy(sr.final_score, unc_for_legacy)

        if sr.reason.startswith("rule_hit"):
            n_rule += 1
        else:
            n_fallback += 1

        sentiment_obj: Dict[str, Any] = {}
        add_aliases(sentiment_obj, legacy)

        scores_obj: Dict[str, Any] = {}
        add_aliases(scores_obj, legacy)

        sent_obj: Dict[str, Any] = {}
        add_aliases(sent_obj, legacy)

        row: Dict[str, Any] = {
            "url": url,
            "norm_url": norm,
            "title": title,
            "source": it.get("source"),
            "published_at": it.get("published_at") or it.get("publishedAt"),
            "image_url": image_url,
            "urlToImage": image_url,

            # primary numeric
            "score": sr.final_score,
            "raw_score": sr.raw_score,
            "uncertainty": unc_for_legacy,
            "reason": sr.reason,

            # BOTH styles:
            "sentiment": sentiment_obj,         # object (GUI-friendly)
            "sentiment_score": sr.final_score,  # float alias
            "scores": scores_obj,
            "sent": sent_obj,
        }

        # top-level aliases too
        add_aliases(row, legacy)

        out_items.append(row)

    payload = {
        "date": date_str,
        "items": out_items,
        "summary": {
            "n_items": len(out_items),
            "n_rule_hit": n_rule,
            "n_fallback_background": n_fallback,
            "fallback_score": float(args.fallback_score),
            "fallback_unc": float(args.fallback_unc),
        },
    }

    out_latest = analysis_dir / OUT_LATEST
    out_dated = analysis_dir / OUT_DATED_TMPL.format(date=date_str)
    write_json(out_latest, payload)
    write_json(out_dated, payload)

    print("[OK] built sentiment")
    print(f"  news : {news_path}")
    print(f"  out  : {out_latest}")
    print(f"  dated: {out_dated}")
    print(f"  items={len(out_items)} rule_hit={n_rule} fallback={n_fallback} fallback_score={float(args.fallback_score)} fallback_unc={float(args.fallback_unc)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

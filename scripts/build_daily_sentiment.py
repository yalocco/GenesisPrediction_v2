# scripts/build_daily_sentiment.py
# Build sentiment_latest.json (and dated sentiment_YYYY-MM-DD.json) from daily_news_YYYY-MM-DD.json
#
# Goals
# - Deterministic (no network, no LLM) and stable
# - Avoid "all same" values by using lightweight lexical scoring on title/description
# - Output schema compatible with sentiment.html (url/title/source + risk/positive/uncertainty/net)
#
# Run:
#   .\.venv\Scripts\python.exe scripts/build_daily_sentiment.py --date 2026-02-14
#
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"
DAILY_NEWS_TMPL = ANALYSIS_DIR / "daily_news_{date}.json"
OUT_LATEST = ANALYSIS_DIR / "sentiment_latest.json"
OUT_DATED_TMPL = ANALYSIS_DIR / "sentiment_{date}.json"


# -------------------------
# Lightweight lexicons
# -------------------------
NEG_WORDS = {
    # conflict / violence
    "war","wars","battle","battles","attack","attacks","attacked","assault","bomb","bombing","missile","rocket",
    "strike","strikes","shelling","shooting","shot","killed","kill","dead","death","fatal","massacre","terror","terrorist",
    "hostage","abduct","abduction","kidnap","kidnapped","explosion","explosive","blast","violence","violent",
    # crisis / disaster
    "crisis","collapse","disaster","earthquake","flood","wildfire","hurricane","typhoon","storm","drought",
    "outbreak","epidemic","pandemic","disease","infected","infection",
    # economy / hardship
    "recession","inflation","unemployment","poverty","hunger","famine","shortage","default","bankrupt","bankruptcy",
    # politics / instability
    "coup","sanction","sanctions","arrest","arrested","detained","detention","raid","crackdown","protest","protests",
    "riot","riots","fraud","corruption","scandal","resign","resignation","impeach","impeachment",
    # misc negative
    "threat","threats","warning","warns","risk","risky","danger","dangerous","failed","failure","decline","declines",
    "loss","losses","lose","losing","cut","cuts","slashed","ban","banned","lawsuit","sue","suing","court","trial",
    "hate","racist","racism",
}

POS_WORDS = {
    "peace","deal","ceasefire","truce","agreement","accord","talks","negotiation","negotiations",
    "aid","relief","support","help","rescue","rescued","donation","funding","grant",
    "growth","recover","recovery","improve","improves","improved","boost","record","surge",
    "win","wins","won","success","successful","progress","breakthrough","advance","advances","achieve","achieved",
    "election","elected","vote","voted",
    "launch","released","opens","opened","announce","announces","announced",
    "safe","safer","stability","stable","partnership","cooperate","cooperation",
}

RISK_WORDS = {
    # words that imply risk/uncertainty even if net isn't strongly negative
    "uncertain","uncertainty","volatile","volatility","tension","tensions","escalate","escalation","stand-off","standoff",
    "probe","investigation","investigate","investigating","allegation","allegations",
    "concern","concerns","fear","fears","doubt","doubts",
}


TOKEN_RE = re.compile(r"[a-z0-9']+")


def _pick(obj: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in obj and obj[k] is not None:
            return obj[k]
    return None


def _extract_items(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Supports various shapes
    for k in ["items", "articles", "data", "news", "rows"]:
        v = doc.get(k)
        if isinstance(v, list):
            return [x for x in v if isinstance(x, dict)]
    # sometimes nested: {"daily_news": {"items":[...]}}
    for k in ["daily_news", "payload", "result"]:
        v = doc.get(k)
        if isinstance(v, dict):
            items = _extract_items(v)
            if items:
                return items
    return []


def _tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass
class Score:
    risk: float
    positive: float
    uncertainty: float
    net: float
    method: str  # "lex" or "fallback"


def score_text(title: str, desc: str) -> Score:
    text = f"{title} {desc}".strip()
    toks = _tokenize(text)

    if not toks:
        # pure fallback
        return Score(risk=0.0, positive=0.0, uncertainty=0.25, net=0.0, method="fallback")

    pos = sum(1 for t in toks if t in POS_WORDS)
    neg = sum(1 for t in toks if t in NEG_WORDS)
    rsk = sum(1 for t in toks if t in RISK_WORDS)

    # If nothing matched, still try a tiny signal from generic patterns (safe)
    if (pos + neg + rsk) == 0:
        # common weak cues
        weak_neg = sum(1 for t in toks if t in {"down","fall","falls","drop","drops","slump","slumps","weaken","weaker","crash"})
        weak_pos = sum(1 for t in toks if t in {"up","rise","rises","gain","gains","strong","stronger","record"})
        pos += weak_pos
        neg += weak_neg

    hits = pos + neg + rsk
    if hits == 0:
        return Score(risk=0.0, positive=0.0, uncertainty=0.25, net=0.0, method="fallback")

    # net score: pos is positive, neg and risk are negative-ish (risk has smaller weight)
    raw = (pos - neg) - 0.5 * rsk

    # normalize (keep small amplitude; stable)
    denom = max(6.0, float(hits) * 2.0)
    net = max(-1.0, min(1.0, raw / denom))

    positive = max(0.0, net)
    risk = max(0.0, -net)

    # uncertainty: higher when |net| is small, lower when strong signal
    # range about 0.12 .. 0.30
    uncertainty = 0.12 + 0.18 * (1.0 - min(1.0, abs(net) * 2.0))

    return Score(
        risk=float(risk),
        positive=float(positive),
        uncertainty=float(uncertainty),
        net=float(net),
        method="lex",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    date = args.date.strip()
    src = DAILY_NEWS_TMPL.with_name(f"daily_news_{date}.json")
    if not src.exists():
        raise SystemExit(f"[ERR] missing daily news: {src}")

    doc = json.loads(src.read_text(encoding="utf-8"))
    items = _extract_items(doc)

    out_items: List[Dict[str, Any]] = []
    rule_hit = 0
    fallback = 0

    for it in items:
        url = _pick(it, ["url", "link", "href"]) or ""
        title = _pick(it, ["title", "headline", "name"]) or ""
        desc = _pick(it, ["description", "summary", "content", "snippet"]) or ""
        source = _pick(it, ["source", "publisher", "site", "domain"]) or ""

        s = score_text(str(title), str(desc))
        if s.method == "lex":
            rule_hit += 1
        else:
            fallback += 1

        out_items.append(
            {
                "url": url,
                "title": title,
                "source": source,
                "description": desc,
                "risk": round(s.risk, 6),
                "positive": round(s.positive, 6),
                "uncertainty": round(s.uncertainty, 6),
                "net": round(s.net, 6),
                "method": s.method,
            }
        )

    # aggregate "today"
    n = len(out_items)
    if n:
        avg_risk = sum(x["risk"] for x in out_items) / n
        avg_pos = sum(x["positive"] for x in out_items) / n
        avg_unc = sum(x["uncertainty"] for x in out_items) / n
        # net average (not clipped)
        avg_net = sum(x["net"] for x in out_items) / n
    else:
        avg_risk = avg_pos = avg_unc = avg_net = 0.0

    payload = {
        "date": date,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "items": out_items,
        "today": {
            "articles": n,
            "risk": round(avg_risk, 6),
            "positive": round(avg_pos, 6),
            "uncertainty": round(avg_unc, 6),
            "net": round(avg_net, 6),
        },
        "summary": {
            "rule_hit": int(rule_hit),
            "fallback": int(fallback),
        },
        "base": date,
        "base_date": date,
    }

    OUT_LATEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_dated = OUT_DATED_TMPL.with_name(f"sentiment_{date}.json")
    out_dated.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[OK] built sentiment")
    print(f"  news : {src.as_posix()}")
    print(f"  out  : {OUT_LATEST.as_posix()}")
    print(f"  dated: {out_dated.as_posix()}")
    print(f"  items={n} rule_hit={rule_hit} fallback={fallback}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

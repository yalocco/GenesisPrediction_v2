from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


# --- same tag logic as digest (keep in sync) ---
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


def classify_tags(title: str, summary: str, domain: str) -> List[str]:
    t = _norm_text(f"{title} {summary} {domain}")
    tags: List[str] = []

    if any(k in t for k in SECURITY_TERMS):
        tags.append("SECURITY")

    # Finance priority: A/B
    if any(k in t for k in FIN_STOCK_TERMS):
        tags.append("FIN-STOCKS")
    if any(k in t for k in FIN_FX_TERMS):
        tags.append("FIN-FX")

    # Next: C/D
    if any(k in t for k in FIN_ENERGY_TERMS):
        tags.append("FIN-ENERGY")
    if any(k in t for k in FIN_RATES_TERMS):
        tags.append("FIN-RATES")

    if any(k in t for k in JAPAN_TERMS):
        tags.append("JP")

    if any(k in t for k in ENTERTAINMENT_TERMS):
        tags.append("ENT")

    return tags


def score_tags(tags: List[str]) -> int:
    score = 0
    if "SECURITY" in tags:
        score += 60
    if "FIN-STOCKS" in tags:
        score += 50
    if "FIN-FX" in tags:
        score += 50
    if "FIN-ENERGY" in tags:
        score += 30
    if "FIN-RATES" in tags:
        score += 30
    if "JP" in tags:
        score += 15
    if "ENT" in tags:
        score -= 40
    return score


def extract_focus_terms(text: str) -> List[str]:
    """
    Very lightweight "focus term" extractor:
    - split words
    - keep longer tokens
    - not a replacement for anchors, just for readable observation log
    """
    t = _norm_text(text)
    toks = re.findall(r"[a-z0-9][a-z0-9\-/]{2,}", t)
    # filter obvious noise
    bad = {
        "the","and","for","with","from","that","this","will","says","said","over","into","after","before",
        "about","more","than","into","their","they","them","his","her","its","have","has","had",
        "news","report","reports","update","live","watch",
    }
    out = [x for x in toks if x not in bad and not x.isdigit()]
    return out


def build_observation(date: str, events: List[Dict[str, Any]], top_n: int = 8) -> Tuple[Dict[str, Any], str]:
    # Score and tag each event
    tagged: List[Dict[str, Any]] = []
    tag_counts = Counter()
    domain_counts = Counter()

    focus_counter = Counter()

    for ev in events:
        url = str(pick(ev, "url", "link") or "").strip()
        title = str(pick(ev, "title", "headline") or "").strip()
        summary = str(pick(ev, "summary", "one_liner", "description", "snippet") or "").strip()
        dom = domain_from_url(url) if url else str(pick(ev, "source", "domain") or "")

        tags = classify_tags(title, summary, dom)
        score = score_tags(tags)

        for tg in tags:
            tag_counts[tg] += 1
        if dom:
            domain_counts[dom] += 1

        # focus terms from title+summary (readable)
        for tok in extract_focus_terms(f"{title} {summary}"):
            focus_counter[tok] += 1

        tagged.append({
            "title": title,
            "url": url,
            "domain": dom,
            "summary": summary,
            "tags": tags,
            "score": score,
        })

    tagged_sorted = sorted(tagged, key=lambda x: x["score"], reverse=True)

    # buckets
    sec_n = tag_counts["SECURITY"]
    fin_ab_n = tag_counts["FIN-STOCKS"] + tag_counts["FIN-FX"]
    fin_cd_n = tag_counts["FIN-ENERGY"] + tag_counts["FIN-RATES"]
    ent_n = tag_counts["ENT"]
    jp_n = tag_counts["JP"]

    top_focus = [w for (w, c) in focus_counter.most_common(40)]
    # Prefer focus terms that look geopolitical/finance-ish by simple boosts
    boost = {"iran","israel","ukraine","russia","taiwan","china","missile","nuclear","sanction","oil","gas","yen","jpy","usd","dollar","boj","fed","rate","rates","yield","stocks","market"}
    top_focus2 = sorted(
        top_focus,
        key=lambda w: (1 if w in boost else 0, focus_counter[w]),
        reverse=True
    )
    top_focus2 = top_focus2[:12]

    # Narrative generator (simple, stable)
    lines: List[str] = []
    lines.append(f"## 観測ログ — {date}")
    lines.append("")
    lines.append(f"- 収集記事数: {len(events)}")
    lines.append(f"- SECURITY: {sec_n} / FIN(A,B)=FIN-STOCKS+FIN-FX: {fin_ab_n} / FIN(C,D)=ENERGY+RATES: {fin_cd_n} / JP: {jp_n} / ENT: {ent_n}")
    lines.append("")

    # Headline-like observation
    obs_bits: List[str] = []
    if sec_n > 0:
        obs_bits.append("安全保障・紛争系が前面")
    if fin_ab_n > 0:
        obs_bits.append("株・為替の反応を伴う文脈が増加")
    if fin_cd_n > 0 and fin_ab_n == 0:
        obs_bits.append("エネルギー・金利の文脈が目立つ")
    if jp_n > 0:
        obs_bits.append("日本関連（円・日銀・日本市場）への接続あり")
    if ent_n > 0 and (sec_n + fin_ab_n + fin_cd_n) > 0:
        obs_bits.append("娯楽系は存在するが主軸ではない")

    if not obs_bits:
        obs_bits.append("大きな偏りは少なく、分散した日")

    lines.append("### 今日の要約")
    lines.append(f"- {' / '.join(obs_bits)}")
    if top_focus2:
        lines.append(f"- 目立つ焦点語: {', '.join(top_focus2)}")
    lines.append("")

    # Top cards (by score)
    lines.append("### 上位カード（優先度順）")
    for i, it in enumerate(tagged_sorted[:top_n], 1):
        tg = ",".join(it["tags"]) if it["tags"] else "-"
        title = it["title"] or "(no title)"
        url = it["url"]
        dom = it["domain"]
        if url:
            lines.append(f"{i}. [{title}]({url}) ({dom}) 〔{tg}〕")
        else:
            lines.append(f"{i}. {title} ({dom}) 〔{tg}〕")
    lines.append("")

    # Simple "watch" suggestion
    watch: List[str] = []
    # watch conditions
    if sec_n >= 3:
        watch.append("安全保障の連鎖（制裁・報復・航路リスク）を数日監視")
    if fin_ab_n >= 3:
        watch.append("株・為替のボラティリティ兆候（risk-off / intervention）を監視")
    if "iran" in top_focus2 or "israel" in top_focus2:
        watch.append("中東（イラン/イスラエル）関連の拡張を監視")
    if "taiwan" in top_focus2 or "strait" in top_focus2:
        watch.append("台湾海峡/南シナ海の緊張上昇を監視")
    if "oil" in top_focus2 or "brent" in top_focus2 or "wti" in top_focus2:
        watch.append("原油（供給/航路）→インフレ→金利への波及を監視")
    if not watch:
        watch.append("明確な連鎖テーマは弱め。次の日の変化に注目。")

    lines.append("### 監視メモ（自動）")
    for w in watch[:4]:
        lines.append(f"- {w}")
    lines.append("")

    # JSON payload
    payload = {
        "date": date,
        "counts": {
            "events": len(events),
            "SECURITY": sec_n,
            "FIN_STOCKS": tag_counts["FIN-STOCKS"],
            "FIN_FX": tag_counts["FIN-FX"],
            "FIN_ENERGY": tag_counts["FIN-ENERGY"],
            "FIN_RATES": tag_counts["FIN-RATES"],
            "JP": jp_n,
            "ENT": ent_n,
        },
        "top_focus_terms": top_focus2,
        "top_cards": tagged_sorted[:top_n],
        "watch_notes": watch[:6],
    }

    return payload, "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (optional; default: infer latest events file)")
    ap.add_argument("--dir", default="data/world_politics/analysis", help="analysis dir")
    ap.add_argument("--top", type=int, default=8, help="top cards to include")
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

    payload, md = build_observation(date, events, top_n=max(1, args.top))

    md_out = base / f"observation_{date}.md"
    js_out = base / f"observation_{date}.json"

    md_out.write_text(md, encoding="utf-8")
    js_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[DONE] md   -> {md_out}")
    print(f"[DONE] json -> {js_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

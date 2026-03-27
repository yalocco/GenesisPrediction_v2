from __future__ import annotations

# scripts/build_daily_sentiment.py
# Build sentiment_latest.json (and dated sentiment_YYYY-MM-DD.json)
#
# Primary input:
#   data/world_politics/YYYY-MM-DD.json   (NewsAPI raw daily file)
#
# Fallback input:
#   data/world_politics/analysis/daily_news_YYYY-MM-DD.json
#
# Output schema is kept compatible with existing Sentiment / Digest consumers,
# while adding per-item fields useful for UI article cards:
#   positive / negative / neutral / mixed
#   publishedAt
#   image
#   *_i18n fields
#
# Usage:
#   .\.venv\Scripts\python.exe scripts/build_daily_sentiment.py --date 2026-03-13

import argparse
import importlib.util
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]

DATA_WORLD_DIR = ROOT / "data" / "world_politics"
ANALYSIS_DIR = DATA_WORLD_DIR / "analysis"

OUT_LATEST = ANALYSIS_DIR / "sentiment_latest.json"
OUT_DATED_TMPL = ANALYSIS_DIR / "sentiment_{date}.json"

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")

POSITIVE_WORDS = {
    "advance", "advances", "agreement", "agreements", "aid", "aids", "ally", "boost",
    "booming", "breakthrough", "calm", "ceasefire", "cooperate", "cooperation", "deal",
    "deals", "deescalation", "ease", "eases", "easing", "gain", "gains", "good",
    "growth", "improve", "improves", "improved", "launch", "launched", "opens",
    "optimism", "peace", "progress", "record", "recovery", "relief", "rescue", "rise",
    "rises", "rising", "safe", "settlement", "stability", "stable", "strong", "stronger",
    "success", "surge", "truce", "victory", "wins",
}

NEGATIVE_WORDS = {
    "attack", "attacks", "bomb", "bombing", "chaos", "collapse", "collapsed", "conflict",
    "crackdown", "crash", "crisis", "death", "deaths", "decline", "declines", "defeat",
    "drop", "drops", "escalate", "escalates", "escalation", "fail", "fails", "fall",
    "falls", "famine", "fear", "fraud", "hit", "hostage", "inflation", "kill", "killed",
    "loss", "losses", "missile", "panic", "protest", "recession", "sanction", "scandal",
    "shortage", "slump", "slumps", "strike", "strikes", "tension", "threat", "threats",
    "violence", "war", "worse", "worst",
}

RISK_WORDS = {
    "alert", "alerts", "armed", "boycott", "danger", "dispute", "hostile", "instability",
    "military", "nuclear", "probe", "probes", "retaliation", "rocket", "shelling", "shock",
    "uncertain", "uncertainty", "warning", "warnings",
}

WEAK_NEGATIVE_WORDS = {
    "down", "fall", "falls", "drop", "drops", "slump", "slumps", "weaken", "weaker", "crash",
}

WEAK_POSITIVE_WORDS = {
    "up", "rise", "rises", "gain", "gains", "strong", "stronger", "record",
}


@dataclass
class Score:
    risk: float
    positive: float
    uncertainty: float
    net: float
    method: str


def _pick(obj: Any, keys: Iterable[str], default: Any = None) -> Any:
    if not isinstance(obj, dict):
        return default
    for k in keys:
        if k in obj and obj[k] is not None:
            return obj[k]
    return default


def _as_str(value: Any) -> str:
    return "" if value is None else str(value)


def _extract_items(doc: Any) -> List[Dict[str, Any]]:
    if isinstance(doc, dict):
        for key in ("items", "articles", "rows", "data", "news"):
            v = doc.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    if isinstance(doc, list):
        return [x for x in doc if isinstance(x, dict)]
    return []


def _tokenize(*parts: str) -> List[str]:
    text = " ".join(p for p in parts if p)
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def _source_name(it: Dict[str, Any]) -> str:
    src = it.get("source")
    if isinstance(src, dict):
        return _as_str(src.get("name") or src.get("id") or "")
    return _as_str(
        _pick(it, ["source", "publisher", "site", "domain"], "") or ""
    )


def _image_url(it: Dict[str, Any]) -> str:
    return _as_str(
        _pick(it, ["urlToImage", "image", "thumbnail", "thumb", "og_image"], "") or ""
    )


def _published_at(it: Dict[str, Any]) -> str:
    return _as_str(
        _pick(
            it,
            ["publishedAt", "published_at", "pubDate", "date", "datetime"],
            "",
        ) or ""
    )


def _load_i18n_builder() -> Optional[Callable[[str], Dict[str, str]]]:
    script_path = ROOT / "scripts" / "build_explanation_multilang.py"
    if not script_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("build_explanation_multilang", script_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    candidates = [
        "build_i18n_block",
        "make_i18n_block",
        "to_i18n_block",
        "build_multilang_block",
    ]
    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    return None


_I18N_BUILDER = _load_i18n_builder()


def _build_i18n_block(text: str) -> Dict[str, str]:
    value = _as_str(text).strip()
    if not value:
        return {"en": "", "ja": "", "th": ""}

    if _I18N_BUILDER is not None:
        try:
            block = _I18N_BUILDER(value)
            if isinstance(block, dict):
                return {
                    "en": _as_str(block.get("en")),
                    "ja": _as_str(block.get("ja")),
                    "th": _as_str(block.get("th")),
                }
        except Exception:
            pass

    return {"en": value, "ja": value, "th": value}


def score_text(title: str, desc: str) -> Score:
    toks = _tokenize(title, desc)
    if not toks:
        return Score(risk=0.0, positive=0.0, uncertainty=0.25, net=0.0, method="fallback")

    pos = sum(1 for t in toks if t in POSITIVE_WORDS)
    neg = sum(1 for t in toks if t in NEGATIVE_WORDS)
    rsk = sum(1 for t in toks if t in RISK_WORDS)

    if (pos + neg + rsk) == 0:
        weak_neg = sum(1 for t in toks if t in WEAK_NEGATIVE_WORDS)
        weak_pos = sum(1 for t in toks if t in WEAK_POSITIVE_WORDS)
        pos += weak_pos
        neg += weak_neg

    hits = pos + neg + rsk
    if hits == 0:
        return Score(risk=0.0, positive=0.0, uncertainty=0.25, net=0.0, method="fallback")

    raw = (pos - neg) - 0.5 * rsk
    denom = max(6.0, float(hits) * 2.0)
    net = max(-1.0, min(1.0, raw / denom))

    positive = max(0.0, net)
    risk = max(0.0, -net)
    uncertainty = 0.12 + 0.18 * (1.0 - min(1.0, abs(net) * 2.0))

    return Score(
        risk=float(risk),
        positive=float(positive),
        uncertainty=float(uncertainty),
        net=float(net),
        method="lex",
    )


def classify_sentiment(s: Score) -> str:
    if s.uncertainty >= 0.24 and abs(s.net) <= 0.10:
        return "mixed"
    if s.net >= 0.12:
        return "positive"
    if s.net <= -0.12:
        return "negative"
    return "neutral"


def _label_counts(items: List[Dict[str, Any]]) -> Dict[str, int]:
    out = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "unknown": 0}
    for it in items:
        lab = str(it.get("sentiment") or it.get("sentiment_label") or "unknown").strip().lower()
        out[lab if lab in out else "unknown"] += 1
    return out


def _resolve_input(date: str) -> Path:
    raw_daily = DATA_WORLD_DIR / f"{date}.json"
    analysis_daily = ANALYSIS_DIR / f"daily_news_{date}.json"
    latest_daily = ANALYSIS_DIR / "daily_news_latest.json"

    # Prefer NewsAPI raw daily file because it contains full article objects.
    if raw_daily.exists():
        return raw_daily

    # Fallback to dated analysis file if raw is missing.
    if analysis_daily.exists():
        return analysis_daily

    # Last fallback to latest alias.
    if latest_daily.exists():
        return latest_daily

    raise SystemExit(
        "[ERR] missing daily news input: "
        f"{raw_daily} / {analysis_daily} / {latest_daily}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    date = args.date.strip()
    src = _resolve_input(date)

    doc = json.loads(src.read_text(encoding="utf-8"))
    items = _extract_items(doc)

    out_items: List[Dict[str, Any]] = []
    rule_hit = 0
    fallback = 0

    for it in items:
        url = _as_str(_pick(it, ["url", "link", "href"], "") or "")
        title = _as_str(_pick(it, ["title", "headline", "name"], "") or "")
        desc = _as_str(_pick(it, ["description", "summary", "content", "snippet"], "") or "")
        source = _source_name(it)
        published_at = _published_at(it)
        image = _image_url(it)

        s = score_text(title, desc)
        label = classify_sentiment(s)

        if s.method == "lex":
            rule_hit += 1
        else:
            fallback += 1

        out_items.append(
            {
                "url": url,
                "title": title,
                "title_i18n": _build_i18n_block(title),
                "source": source,
                "source_i18n": _build_i18n_block(source),
                "description": desc,
                "description_i18n": _build_i18n_block(desc),
                "publishedAt": published_at,
                "image": image,
                "risk": round(s.risk, 6),
                "positive": round(s.positive, 6),
                "uncertainty": round(s.uncertainty, 6),
                "net": round(s.net, 6),
                "score": round(s.net, 6),
                "sentiment": label,
                "sentiment_label": label,
                "method": s.method,
            }
        )

    n = len(out_items)
    if n:
        avg_risk = sum(x["risk"] for x in out_items) / n
        avg_pos = sum(x["positive"] for x in out_items) / n
        avg_unc = sum(x["uncertainty"] for x in out_items) / n
        avg_net = sum(x["net"] for x in out_items) / n
    else:
        avg_risk = avg_pos = avg_unc = avg_net = 0.0

    label_counts = _label_counts(out_items)
    today_score = Score(
        risk=float(avg_risk),
        positive=float(avg_pos),
        uncertainty=float(avg_unc),
        net=float(avg_net),
        method="agg",
    )
    today_label = classify_sentiment(today_score) if n else "neutral"

    payload = {
        "date": date,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "items": out_items,
        "today": {
            "articles": n,
            "risk": round(avg_risk, 6),
            "positive": round(avg_pos, 6),
            "uncertainty": round(avg_unc, 6),
            "net": round(avg_net, 6),
            "score": round(avg_net, 6),
            "sentiment": today_label,
            "sentiment_label": today_label,
            "label_counts": label_counts,
        },
        "summary": {
            "rule_hit": int(rule_hit),
            "fallback": int(fallback),
            "positive": int(label_counts["positive"]),
            "negative": int(label_counts["negative"]),
            "neutral": int(label_counts["neutral"]),
            "mixed": int(label_counts["mixed"]),
            "unknown": int(label_counts["unknown"]),
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
    print(
        "  labels="
        f"positive:{label_counts['positive']} "
        f"negative:{label_counts['negative']} "
        f"neutral:{label_counts['neutral']} "
        f"mixed:{label_counts['mixed']} "
        f"unknown:{label_counts['unknown']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

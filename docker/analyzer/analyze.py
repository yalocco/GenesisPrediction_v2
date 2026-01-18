# docker/analyzer/analyze.py
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from diff import generate_diff
from history_analog import derive_current_tags, find_historical_analogs


DATA_DIR = Path("/data")
CATEGORY = "world_politics"
PROVIDER = "newsapi"

RAW_DIR = DATA_DIR / CATEGORY
ANALYSIS_DIR = RAW_DIR / "analysis"


# -----------------------------
# Utilities
# -----------------------------
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    return str(x)



# --- predictions/daily_summary helpers (A-spec) -------------------------------
PRED_RE = re.compile(r"^predictions_(\d{4}-\d{2}-\d{2})\.json$")

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def _find_latest_predictions_file(analysis_dir: Path) -> Optional[Path]:
    """Pick latest predictions_YYYY-MM-DD.json under analysis_dir."""
    best_date: Optional[str] = None
    best_path: Optional[Path] = None
    if not analysis_dir.exists():
        return None
    for p in analysis_dir.iterdir():
        if not p.is_file():
            continue
        m = PRED_RE.match(p.name)
        if not m:
            continue
        d = m.group(1)
        if (best_date is None) or (d > best_date):
            best_date = d
            best_path = p
    return best_path

MAX_ONE_LINER = 120  # hard cap for one_liner (chars)

def _shorten(s: str, n: int = 30) -> str:
    """Shorten string to n characters with ellipsis."""
    s = safe_text(s).strip()
    if len(s) <= n:
        return s
    return s[: max(n - 1, 1)] + "…"
def _build_one_liner(headline: str, bullets: List[str], uncertainty: str) -> str:
    """One-liner for daily ops (A-spec, fixed format)."""
    headline = safe_text(headline).strip()
    # one_liner は1行に固定（headlineが複数行でも先頭行だけ採用）
    if headline:
        headline = headline.splitlines()[0].strip()
    bullets = [safe_text(x).strip() for x in (bullets or []) if safe_text(x).strip()]
    b1 = bullets[0] if len(bullets) > 0 else ""
    b2 = bullets[1] if len(bullets) > 1 else ""
    unc_short = _shorten(uncertainty, 30)

    if not headline and not b1 and not b2 and not unc_short:
        return ""

    s = f"{headline}｜根拠: {b1}"
    if b2:
        s += f" / {b2}"
    s += f"｜不確実: {unc_short}"
    # 120文字程度で強制短縮（UI崩れ防止）
    if len(s) > MAX_ONE_LINER:
        s = s[: max(MAX_ONE_LINER - 1, 1)] + "…"
    return s

def _build_a_explain_from_predictions(pred_doc: dict, *, max_preds: int = 3, max_bullets: int = 6) -> dict:
    """
    A仕様（短い・機械的）
    - headline: [{scenario_id}] {claim} を改行で最大3件
    - bullets: rationale をprefix付きで最大max_bullets
    - uncertainty: 上位1件を採用（空なら次を探す）
    - watch: 上位1件から最大2行（prefix付き）
    欠損/型ゆれ耐性あり
    """
    preds = list(pred_doc.get("predictions") or [])
    if not preds:
        return {"headline": "", "bullets": [], "uncertainty": "predictions empty", "watch": []}

    def _score(x: dict) -> float:
        try:
            return float(x.get("score", 0.0))
        except Exception:
            return 0.0

    preds.sort(key=lambda x: (-_score(x), str(x.get("scenario_id", ""))))
    preds = preds[:max_preds]

    # headline
    lines: List[str] = []
    for p in preds:
        sid = str(p.get("scenario_id") or "unknown")
        claim = safe_text(p.get("claim")).strip()
        if claim:
            lines.append(f"[{sid}] {claim}")
    headline = "\n".join(lines)

    # bullets
    bullets: List[str] = []
    for p in preds:
        sid = str(p.get("scenario_id") or "unknown")
        rat = p.get("rationale") or []
        if isinstance(rat, str):
            rat = [rat]
        if isinstance(rat, list):
            for s in rat:
                s = safe_text(s).strip()
                if not s:
                    continue
                bullets.append(f"[{sid}] {s}")
                if len(bullets) >= max_bullets:
                    break
        if len(bullets) >= max_bullets:
            break

    # uncertainty
    uncertainty = ""
    for p in preds:
        u = safe_text(p.get("uncertainty")).strip()
        if u:
            uncertainty = u
            break

    # watch
    watch: List[str] = []
    p0 = preds[0]
    sid0 = str(p0.get("scenario_id") or "unknown")
    w = p0.get("watch") or []
    if isinstance(w, str):
        w = [w]
    if isinstance(w, list):
        for s in w[:2]:
            s = safe_text(s).strip()
            if s:
                watch.append(f"[{sid0}] {s}")

    return {"headline": headline, "bullets": bullets, "uncertainty": uncertainty, "watch": watch}
# --- /predictions/daily_summary helpers --------------------------------------

# --- "Why" reasoning (rule-based, anchors) -----------------------------------
from collections import Counter as _Counter

_STOPWORDS = {
    "the","a","an","and","or","but","to","of","in","on","for","with","from","by","as",
    "is","are","was","were","be","been","being","at","it","this","that","these","those",
    "into","over","under","after","before","between","within","without","about",
    # news boilerplate
    "news","report","reports","says","said","live","update","updates","watch","video",
    "opinion","analysis","explainer","how","why","what","when","where","who",
}

_COUNTRY_OR_ORG_HINTS = {
    "ukraine","russia","china","taiwan","iran","israel","gaza","palestine","syria",
    "japan","korea","india","pakistan","myanmar",
    "un","nato","eu","asean","quad","g7","g20",
    "trump","beijing",
}

def _tokenize_title(title: str) -> List[str]:
    if not title:
        return []
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", safe_text(title))
    toks = [t.lower() for t in cleaned.split()]
    toks = [t for t in toks if len(t) >= 4 and t not in _STOPWORDS]
    return toks

def _domain(url: str) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"^https?://([^/]+)/", safe_text(url))
    return m.group(1).lower() if m else None

def extract_anchors(diff_doc: dict, max_tokens: int = 10) -> dict:
    """Pick concrete anchors from diff: title tokens + domains + hint words."""
    ev = diff_doc.get("event_level") or {}
    added   = ev.get("added") or []
    removed = ev.get("removed") or []
    changed = ev.get("changed") or []

    dom_counter = _Counter()
    for x in (list(added) + list(removed) + list(changed)):
        dom = _domain((x or {}).get("url"))
        if dom:
            dom_counter[dom] += 1

    tok_counter = _Counter()
    for x in (list(added) + list(removed)):
        tok_counter.update(_tokenize_title((x or {}).get("title") or ""))

    top_domains = [d for d,_ in dom_counter.most_common(5)]
    top_tokens  = [t for t,_ in tok_counter.most_common(max_tokens)]
    hints       = [t for t in top_tokens if t in _COUNTRY_OR_ORG_HINTS][:8]

    return {
        "counts": {"added": len(list(added)), "removed": len(list(removed)), "changed": len(list(changed))},
        "top_domains": top_domains,
        "top_tokens": top_tokens,
        "hints": hints,
    }

def build_why_fields(diff_doc: dict) -> dict:
    """
    Returns:
      delta_explanation: str
      change_reason_hypotheses: list[dict]
      confidence_of_hypotheses: float
      anchors: dict
    """
    inp = diff_doc.get("input") or {}
    summary = diff_doc.get("summary") or {}

    today_n = (inp.get("today") or {}).get("events_count") or 0
    base_n  = (inp.get("baseline") or {}).get("events_count") or 0
    denom = float(base_n or today_n or 1)

    delta_events = summary.get("delta_events")
    anchors = extract_anchors(diff_doc)

    churn = (anchors["counts"]["added"] + anchors["counts"]["removed"]) / denom
    churn = float(max(0.0, min(1.0, churn)))

    tokens_preview  = ", ".join(anchors["top_tokens"][:6]) if anchors["top_tokens"] else ""
    domains_preview = ", ".join(anchors["top_domains"][:3]) if anchors["top_domains"] else ""

    if (delta_events == 0) and (anchors["counts"]["added"] or anchors["counts"]["removed"]):
        delta_explanation = (
            "総記事数は横ばいだが、追加/削除が発生しており『入れ替わり（回転）』が起きています。"
            f" 目立つ語: {tokens_preview}."
        )
    elif isinstance(delta_events, (int, float)) and delta_events > 0:
        delta_explanation = (
            f"総記事数が増加（+{int(delta_events)}）。"
            f" 追加側で目立つ語: {tokens_preview}."
        )
    elif isinstance(delta_events, (int, float)) and delta_events < 0:
        delta_explanation = (
            f"総記事数が減少（{int(delta_events)}）。"
            " 削除側の語/テーマの比重低下が疑われます。"
        )
    else:
        delta_explanation = f"差分が小さい/未検出です。目立つ語: {tokens_preview}."

    hyps: List[dict] = []

    if churn >= 0.12:
        conf = min(0.88, 0.45 + churn)
        hyps.append({
            "hypothesis": "話題の回転（Top入替）が起きている",
            "rationale": f"追加+削除が相対的に多い（churn≈{churn:.2f}）。総量変化より入替が主体。",
            "anchors": anchors["top_tokens"][:8],
            "confidence": round(conf, 2),
        })

    yearish = any(t in {"2024","2025","2026","year","predictions","forecast","outlook"} for t in anchors["top_tokens"])
    if yearish:
        conf = 0.55 + (0.15 if churn >= 0.12 else 0.05)
        hyps.append({
            "hypothesis": "年末年始の総括/展望系コンテンツが差分を押し上げている",
            "rationale": "年号/総括語が上位に出現（例: 2025, year, 2026, predictions）。",
            "anchors": [t for t in anchors["top_tokens"] if t in {"2024","2025","2026","year","predictions","outlook","forecast"}][:8],
            "confidence": round(min(0.85, conf), 2),
        })

    if anchors["top_domains"]:
        conf = 0.30 + (0.15 if len(anchors["top_domains"]) <= 2 else 0.10) + (0.10 if churn >= 0.12 else 0.0)
        hyps.append({
            "hypothesis": "特定メディア/ドメイン比率の変化が差分に影響",
            "rationale": f"差分内で目立つドメイン: {domains_preview}。",
            "anchors": anchors["top_domains"][:5],
            "confidence": round(min(0.75, conf), 2),
        })

    if anchors["hints"]:
        conf = 0.40 + 0.08 * min(5, len(anchors["hints"])) + (0.08 if churn >= 0.12 else 0.0)
        hyps.append({
            "hypothesis": "地政学トピックの焦点が移動（国/組織/人物の言及が増減）",
            "rationale": f"国/組織/人物ヒント語が上位に出現: {', '.join(anchors['hints'][:6])}。",
            "anchors": anchors["hints"][:8],
            "confidence": round(min(0.82, conf), 2),
        })

    if not hyps:
        hyps.append({
            "hypothesis": "差分が小さく、意味づけが難しい",
            "rationale": "追加/削除/変更が少ないため、明確な要因を推定できません。",
            "anchors": anchors["top_tokens"][:6],
            "confidence": 0.20,
        })

    hyps.sort(key=lambda x: float(x.get("confidence", 0.0)), reverse=True)
    top_conf = float(hyps[0].get("confidence", 0.0)) if hyps else 0.0

    return {
        "anchors": anchors,
        "churn": round(churn, 4),
        "delta_explanation": delta_explanation,
        "change_reason_hypotheses": hyps,
        "confidence_of_hypotheses": round(top_conf, 2),
    }


def classify_regime(conf: float | None, churn: float | None, conf_thr: float = 0.7, churn_thr: float = 0.12) -> str:
    """Coarse regime label for dashboarding (rule-based)."""
    try:
        c = float(conf) if conf is not None else 0.0
    except Exception:
        c = 0.0
    try:
        ch = float(churn) if churn is not None else 0.0
    except Exception:
        ch = 0.0

    high_c = c >= conf_thr
    high_ch = ch >= churn_thr

    if high_c and high_ch:
        return "rotation (high conf/high churn)"
    if high_c and (not high_ch):
        return "stable (high conf/low churn)"
    if (not high_c) and high_ch:
        return "noisy (low conf/high churn)"
    return "quiet (low conf/low churn)"
# --- /"Why" reasoning ---------------------------------------------------------

def parse_date_from_filename(p: Path) -> Optional[str]:
    # expects .../YYYY-MM-DD.json
    stem = p.stem
    if DATE_RE.match(stem):
        return stem
    return None


def ensure_dirs() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


def read_json_file(path: Path) -> Dict[str, Any]:
    # Robust JSON load (and helpful error message)
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # show the first ~200 chars to help debugging
        head = raw[:200].replace("\n", "\\n")
        raise RuntimeError(
            f"JSON parse error in {path} : {e}\n"
            f"File head: {head}"
        ) from e


def list_daily_raw_files() -> List[Path]:
    if not RAW_DIR.exists():
        return []
    files = []
    for p in RAW_DIR.glob("*.json"):
        d = parse_date_from_filename(p)
        if d:
            files.append(p)
    return sorted(files, key=lambda p: p.stem)  # YYYY-MM-DD sorts lexicographically OK


def pick_today_and_yesterday(files: List[Path]) -> Tuple[Optional[Path], Optional[Path]]:
    if not files:
        return None, None
    today = files[-1]
    yesterday = files[-2] if len(files) >= 2 else None
    return today, yesterday


# -----------------------------
# Rule-based sentiment & topic
# -----------------------------
POS_WORDS = {
    "progress", "peace", "agreement", "deal", "growth", "recover", "win", "stabilize",
    "improve", "success", "aid", "support", "ceasefire", "truce",
}
NEG_WORDS = {
    "war", "conflict", "attack", "killed", "dead", "crisis", "sanction", "inflation",
    "collapse", "terror", "bomb", "strike", "violence", "hostage", "risk", "famine",
}

TOPIC_RULES = {
    "war": [r"\bwar\b", r"\battack\b", r"\bstrike\b", r"\bbomb\b", r"\bmissile\b", r"\bconflict\b"],
    "diplomacy": [r"\bdiplomacy\b", r"\bsummit\b", r"\btalks\b", r"\bnegotiat", r"\bceasefire\b", r"\btruce\b"],
    "economy": [r"\beconom", r"\bmarket\b", r"\binflation\b", r"\bsanction", r"\btrade\b", r"\bgdp\b"],
}


def compute_sentiment(title: str, desc: str) -> Tuple[str, float]:
    """
    returns: (label, score)
    score: roughly in [-1, +1]
    """
    text = f"{title} {desc}".lower()
    pos = sum(1 for w in POS_WORDS if w in text)
    neg = sum(1 for w in NEG_WORDS if w in text)
    if pos == 0 and neg == 0:
        return "neutral", 0.0
    score = (pos - neg) / max(pos + neg, 1)
    if score > 0.15:
        return "positive", float(score)
    if score < -0.15:
        return "negative", float(score)
    return "neutral", float(score)


def compute_topic(title: str, desc: str) -> str:
    text = f"{title} {desc}".lower()
    for topic, patterns in TOPIC_RULES.items():
        for pat in patterns:
            if re.search(pat, text):
                return topic
    return "other"


# -----------------------------
# Normalization
# -----------------------------
@dataclass
class Event:
    schema_version: str
    category: str
    provider: str
    query: str
    fetched_at: str
    published_at: str
    title: str
    description: str
    url: str
    source: Dict[str, Any]
    author: str
    image: str
    content: str
    sentiment_label: str
    sentiment_score: float
    topic: str


def normalize_article(article: Dict[str, Any], *, query: str, fetched_at: str) -> Event:
    title = safe_text(article.get("title"))
    description = safe_text(article.get("description"))
    url = safe_text(article.get("url"))
    published_at = safe_text(article.get("publishedAt"))  # NewsAPI uses publishedAt

    label, score = compute_sentiment(title, description)
    topic = compute_topic(title, description)

    return Event(
        schema_version="v2",
        category=CATEGORY,
        provider=PROVIDER,
        query=query,
        fetched_at=fetched_at,
        published_at=published_at,
        title=title,
        description=description,
        url=url,
        source=article.get("source") or {},
        author=safe_text(article.get("author")),
        image=safe_text(article.get("urlToImage")),
        content=safe_text(article.get("content")),
        sentiment_label=label,
        sentiment_score=score,
        topic=topic,
    )


def load_events_from_daily_file(path: Path) -> Tuple[str, str, List[Event]]:
    obj = read_json_file(path)
    fetched_at = safe_text(obj.get("fetched_at") or obj.get("fetchedAt") or "")
    query = safe_text(obj.get("query") or "")
    articles = obj.get("articles") or []
    if not isinstance(articles, list):
        articles = []
    date = parse_date_from_filename(path) or path.stem
    events = [normalize_article(a, query=query, fetched_at=fetched_at) for a in articles if isinstance(a, dict)]
    return date, fetched_at, events


# -----------------------------
# Outputs
# -----------------------------
def write_jsonl(path: Path, events: List[Event]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e.__dict__, ensure_ascii=False) + "\n")


def write_daily_counts_csv(path: Path, counts_by_date: Dict[str, int]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "count"])
        for d in sorted(counts_by_date.keys()):
            w.writerow([d, counts_by_date[d]])


def summarize_events(events: List[Event]) -> Dict[str, Any]:
    if not events:
        return {
            "count": 0,
            "avg_sentiment": 0.0,
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
            "topics": {},
            "unique_urls": 0,
        }

    sent_counts = {"positive": 0, "neutral": 0, "negative": 0}
    topic_counts: Dict[str, int] = {}
    total_score = 0.0
    urls = set()

    for e in events:
        sent_counts[e.sentiment_label] = sent_counts.get(e.sentiment_label, 0) + 1
        topic_counts[e.topic] = topic_counts.get(e.topic, 0) + 1
        total_score += float(e.sentiment_score)
        if e.url:
            urls.add(e.url)

    return {
        "count": len(events),
        "avg_sentiment": total_score / max(len(events), 1),
        "sentiment": sent_counts,
        "topics": dict(sorted(topic_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "unique_urls": len(urls),
    }


def diff_summary(today: Dict[str, Any], yesterday: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not yesterday:
        return {"available": False}

    delta: Dict[str, Any] = {"available": True}

    # simple numeric deltas
    delta["count"] = today.get("count", 0) - yesterday.get("count", 0)
    delta["avg_sentiment"] = float(today.get("avg_sentiment", 0.0)) - float(yesterday.get("avg_sentiment", 0.0))
    delta["unique_urls"] = today.get("unique_urls", 0) - yesterday.get("unique_urls", 0)

    # sentiment deltas
    t_sent = today.get("sentiment", {}) or {}
    y_sent = yesterday.get("sentiment", {}) or {}
    delta["sentiment"] = {
        k: int(t_sent.get(k, 0)) - int(y_sent.get(k, 0))
        for k in ["positive", "neutral", "negative"]
    }

    # topic deltas (union keys)
    t_topics = today.get("topics", {}) or {}
    y_topics = yesterday.get("topics", {}) or {}
    keys = set(t_topics.keys()) | set(y_topics.keys())
    delta_topics = {k: int(t_topics.get(k, 0)) - int(y_topics.get(k, 0)) for k in keys}
    # sort by abs change desc
    delta["topics"] = dict(sorted(delta_topics.items(), key=lambda kv: (-abs(kv[1]), kv[0])))

    return delta


def url_set(events: List[Event]) -> set:
    return {e.url for e in events if e.url}


def main() -> None:
    ensure_dirs()

    files = list_daily_raw_files()
    if not files:
        print(f"[WARN] No daily raw files found in {RAW_DIR}")
        return

    today_file, yesterday_file = pick_today_and_yesterday(files)

    assert today_file is not None
    today_date, today_fetched_at, today_events = load_events_from_daily_file(today_file)

    # Write today's events jsonl
    events_path = ANALYSIS_DIR / f"events_{today_date}.jsonl"
    write_jsonl(events_path, today_events)
    print(f"[OK] events: {len(today_events)} -> {events_path}")

    # daily_counts across all days (raw JSON count)
    counts_by_date: Dict[str, int] = {}
    for p in files:
        d, _, ev = load_events_from_daily_file(p)
        counts_by_date[d] = len(ev)
    daily_counts_path = ANALYSIS_DIR / "daily_counts.csv"
    write_daily_counts_csv(daily_counts_path, counts_by_date)
    print(f"[OK] daily counts -> {daily_counts_path}")

    # latest.json: keep compact info from latest day
    latest_obj = {
        "date": today_date,
        "generated_at": iso_now(),
        "source_file": str(today_file),
        "count": len(today_events),
        "latest": {
            "title": today_events[0].title if today_events else "",
            "url": today_events[0].url if today_events else "",
            "published_at": today_events[0].published_at if today_events else "",
            "sentiment_label": today_events[0].sentiment_label if today_events else "neutral",
            "sentiment_score": today_events[0].sentiment_score if today_events else 0.0,
            "topic": today_events[0].topic if today_events else "other",
        },
    }
    latest_path = ANALYSIS_DIR / "latest.json"
    latest_path.write_text(json.dumps(latest_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] latest -> {latest_path}")

    # sentiment_summary.json + topic_counts.json for latest day
    today_summary = summarize_events(today_events)

    sentiment_summary_path = ANALYSIS_DIR / "sentiment_summary.json"
    sentiment_summary_path.write_text(
        json.dumps(
            {
                "date": today_date,
                "count": today_summary["count"],
                "avg_sentiment": today_summary["avg_sentiment"],
                "positive": today_summary["sentiment"]["positive"],
                "negative": today_summary["sentiment"]["negative"],
                "neutral": today_summary["sentiment"]["neutral"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    topic_counts_path = ANALYSIS_DIR / "topic_counts.json"
    topic_counts_path.write_text(
        json.dumps(today_summary["topics"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Yesterday summary & URL diff (new URLs)
    y_summary: Optional[Dict[str, Any]] = None
    new_urls: List[str] = []
    if yesterday_file is not None:
        y_date, _, y_events = load_events_from_daily_file(yesterday_file)
        y_summary = summarize_events(y_events)
        new_urls = sorted(list(url_set(today_events) - url_set(y_events)))[:50]  # cap

    # summary.json (main “thinking” output)
    summary_obj = {
        "date": today_date,
        "generated_at": iso_now(),
        "today": today_summary,
        "yesterday": y_summary if y_summary else None,
        "delta_vs_yesterday": diff_summary(today_summary, y_summary),
        "new_urls_vs_yesterday": new_urls,
    }

    summary_path = ANALYSIS_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] summary -> {summary_path}")
    

    # generate daily diff (Genesis diff v1)
    diff_path = generate_diff(
        analysis_dir=str(ANALYSIS_DIR),
        date_str=today_date
        )
    print(f"[OK] diff -> {diff_path}")

    # --- A仕様 Explain（predictions_YYYY-MM-DD.json → headline/bullets/uncertainty/watch）---
    pred_doc: dict = {}

    pred_path = _find_latest_predictions_file(ANALYSIS_DIR)
    if pred_path is None:
        explain_a = {"headline": "", "bullets": [], "uncertainty": "predictions file not found", "watch": []}
    else:
        try:
            pred_doc = _load_json(pred_path)
        except Exception:
            pred_doc = {}
        explain_a = _build_a_explain_from_predictions(pred_doc)

    summary_obj["headline"] = explain_a["headline"]
    summary_obj["bullets"] = explain_a["bullets"]
    summary_obj["uncertainty"] = explain_a["uncertainty"]
    summary_obj["watch"] = explain_a["watch"]
    summary_obj.setdefault("sources", {})
    summary_obj["sources"]["predictions_file"] = str(pred_path) if pred_path else None

    # summary.json を上書き保存（headline等が入った版）
    summary_path.write_text(json.dumps(summary_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] summary(+A explain) -> {summary_path}")

    # --- daily_summary_YYYY-MM-DD.json (schema fixed + one_liner + why v1) ---
    headline = safe_text(summary_obj.get("headline")).strip()
    bullets = summary_obj.get("bullets") or []
    if isinstance(bullets, str):
        bullets = [bullets]
    bullets = [safe_text(x).strip() for x in bullets if safe_text(x).strip()]

    uncertainty = safe_text(summary_obj.get("uncertainty")).strip()

    watch = summary_obj.get("watch") or []
    if isinstance(watch, str):
        watch = [watch]
    watch = [safe_text(x).strip() for x in watch if safe_text(x).strip()]

    baseline_date = None
    if yesterday_file is not None:
        try:
            y_date, _, _ = load_events_from_daily_file(yesterday_file)
            baseline_date = y_date
        except Exception:
            baseline_date = None

    # diff_doc を読み、Whyフィールドを生成（欠損耐性）
    try:
        diff_doc = _load_json(Path(diff_path)) if diff_path else {}
    except Exception:
        diff_doc = {}

    # --- build why fields (must exist) ---
    try:
        why = build_why_fields(diff_doc) if diff_doc else {
            "delta_explanation": "",
            "change_reason_hypotheses": [],
            "confidence_of_hypotheses": 0.0,
            "anchors": {},
            "churn": 0.0,
        }
    except Exception as e:
        print(f"[WARN] build_why_fields failed: {e!r}")
        why = {
            "delta_explanation": "",
            "change_reason_hypotheses": [],
            "confidence_of_hypotheses": 0.0,
            "anchors": {},
            "churn": 0.0,
        }
    # --- /build why fields ---

    # anchors dict -> list（表示用）
    if isinstance(why.get("anchors"), dict) and "anchors_list" not in why:
        # 優先順：hints > top_tokens > top_domains
        xs = []
        for k in ("hints", "top_tokens", "top_domains"):
            v = why["anchors"].get(k) if isinstance(why.get("anchors"), dict) else None
            if isinstance(v, list):
                xs.extend([str(s) for s in v])
            elif isinstance(v, str):
                xs.append(v)
        # 重複除去しつつ最大10
        seen = set()
        out = []
        for s in xs:
            t = s.strip()
            if not t:
                continue
            key = t.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(t)
        why["anchors_list"] = out[:10]


    daily_summary = {
        "schema": {"name": "genesis.daily_summary", "version": "0.2.0"},
        "meta": {
            "dataset": CATEGORY,
            "date": today_date,
            "baseline_date": baseline_date,
            "generated_at": iso_now(),
            "generator": {"component": "analyzer"},
        },
        "source": {
            "predictions_file": str(pred_path) if pred_path else None,
            "diff_file": str(diff_path) if diff_path else None,
        },

        "headline": headline,
        "bullets": bullets[:3],
        "uncertainty": uncertainty,
        "watch": watch[:3],

        "one_liner": _build_one_liner(headline, bullets[:2], uncertainty),

        # thinking v1
        "delta_explanation": why.get("delta_explanation") or "",
        "change_reason_hypotheses": why.get("change_reason_hypotheses") or [],
        "confidence_of_hypotheses": why.get("confidence_of_hypotheses") or 0.0,
        "anchors_detail": why.get("anchors") or {},
        "anchors": (why.get("anchors_list") or []),

        "churn": why.get("churn"),
        "regime": classify_regime(why.get("confidence_of_hypotheses"), why.get("churn")),
        "debug": {
            "predictions_count": len(pred_doc.get("predictions") or []) if isinstance(pred_doc, dict) else 0,
            "scenario_ids": [str(p.get("scenario_id")) for p in (pred_doc.get("predictions") or [])] if isinstance(pred_doc, dict) else [],
        },
    }

    # --- historical analogs (v1) ---
    try:
        anchors = daily_summary.get("anchors") or []
        regime = daily_summary.get("regime") or None

        current_tags = derive_current_tags(anchors=anchors, regime=regime)

        # v1: safety fallback（必ず何か出るように）
        if not current_tags:
            current_tags = [
                "bloc_polarization",
                "financial_regime",
                "arms_race",
                "debt_cycle",
            ]

        daily_summary["historical_analogs"] = find_historical_analogs(
            current_tags, top_k=3
        )
        daily_summary["historical_analog_tags"] = current_tags

    except Exception as e:
        # 失敗しても既存分析は壊さない
        daily_summary["historical_analogs_error"] = str(e)

    # --- thin diff template (C) ---
    try:
        summary = diff_doc.get("summary") or {}
        delta_events = float(summary.get("delta_events") or 0.0)

        ev = diff_doc.get("event_level") or {}
        added = ev.get("added") or []
        removed = ev.get("removed") or []

        churn_n = len(added) + len(removed)

        # ① 薄い日：差分も回転も小さい
        if abs(delta_events) <= 1.0 and churn_n <= 6:
            anchors = daily_summary.get("anchors") if isinstance(daily_summary.get("anchors"), list) else []
            a = ", ".join(anchors[:3]) if anchors else "主要トピック"
            daily_summary["delta_explanation"] = (
                "本日は前日比の変化が小さく、全体としては『現状維持』に近い一日です。"
                f"観測上は {a} に関連する小さな揺れはあるものの、"
                "新規の大型材料は限定的でした。"
            )
            daily_summary["confidence_of_hypotheses"] = min(
                float(daily_summary.get("confidence_of_hypotheses") or 0.5),
                0.60
            )

        # ② 回転日：純増は小さいが入れ替わりが大きい
        elif abs(delta_events) <= 1.0 and churn_n >= 40:
            anchors = daily_summary.get("anchors") if isinstance(daily_summary.get("anchors"), list) else []
            a = ", ".join(anchors[:5]) if anchors else "主要トピック"
            daily_summary["delta_explanation"] = (
                "総量は横ばいだが、追加/削除が多く『入れ替わり（回転）』が強い一日です。"
                f"目立つ語: {a}."
            )
            daily_summary["confidence_of_hypotheses"] = min(
                float(daily_summary.get("confidence_of_hypotheses") or 0.7),
                0.85
            )
    except Exception as e:
        print(f"[WARN] thin-day template failed: {e!r}")
    # --- /thin diff template ---

    daily_summary_path = ANALYSIS_DIR / f"daily_summary_{today_date}.json"
    daily_summary_path.write_text(json.dumps(daily_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] daily_summary -> {daily_summary_path}")
    # --- /daily_summary ---


if __name__ == "__main__":
    main()

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


if __name__ == "__main__":
    main()

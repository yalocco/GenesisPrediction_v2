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


# --- daily_summary helpers ---
PRED_RE = re.compile(r"^predictions_(\d{4}-\d{2}-\d{2})\.json$")

def _find_latest_predictions_file(analysis_dir: Path) -> Optional[Path]:
    best_date = None
    best_path = None
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

def _shorten(s: str, n: int = 30) -> str:
    s = safe_text(s).strip()
    if len(s) <= n:
        return s
    return s[: max(n - 1, 1)] + "…"

def _build_one_liner(headline: str, bullets: List[str], uncertainty: str) -> str:
    headline = safe_text(headline).strip()
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
    return s
# --- /daily_summary helpers ---


PRED_RE = re.compile(r"^predictions_(\d{4}-\d{2}-\d{2})\.json$")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_latest_predictions_file(analysis_dir: Path) -> Optional[Path]:
    best_date = None
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


def _build_a_explain_from_predictions(pred_doc: dict, *, max_preds: int = 3, max_bullets: int = 6) -> dict:
    """
    A仕様（短い・機械的）
    - headline: [{scenario_id}] {claim} を改行で最大3件
    - bullets: rationale をprefix付きで最大max_bullets
    - uncertainty: 上位1件を採用（空なら次を探す）
    - watch: 上位1件から最大2行（prefix付き）
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

    # headline（最大3件）
    lines: List[str] = []
    for p in preds:
        sid = str(p.get("scenario_id") or "unknown")
        claim = str(p.get("claim") or "").strip()
        if claim:
            lines.append(f"[{sid}] {claim}")
    headline = "\n".join(lines)

    # bullets（rationale 最大 max_bullets）
    bullets: List[str] = []
    for p in preds:
        sid = str(p.get("scenario_id") or "unknown")
        rat = p.get("rationale") or []
        if isinstance(rat, str):
            rat = [rat]
        if isinstance(rat, list):
            for s in rat:
                s = str(s).strip()
                if not s:
                    continue
                bullets.append(f"[{sid}] {s}")
                if len(bullets) >= max_bullets:
                    break
        if len(bullets) >= max_bullets:
            break

    # uncertainty（最初に見つかった非空）
    uncertainty = ""
    for p in preds:
        u = str(p.get("uncertainty") or "").strip()
        if u:
            uncertainty = u
            break

    # watch（上位1件から最大2行）
    watch: List[str] = []
    p0 = preds[0]
    sid0 = str(p0.get("scenario_id") or "unknown")
    w = p0.get("watch") or []
    if isinstance(w, str):
        w = [w]
    if isinstance(w, list):
        for s in w[:2]:
            s = str(s).strip()
            if s:
                watch.append(f"[{sid0}] {s}")

    return {"headline": headline, "bullets": bullets, "uncertainty": uncertainty, "watch": watch}


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
        date_str=today_date,
    )
    print(f"[OK] diff -> {diff_path}")

    # --- A仕様 Explain（predictions_YYYY-MM-DD.json → headline/bullets/uncertainty/watch）---
    pred_path = _find_latest_predictions_file(ANALYSIS_DIR)
    if pred_path is None:
        explain_a = {"headline": "", "bullets": [], "uncertainty": "predictions file not found", "watch": []}
    else:
        pred_doc = _load_json(pred_path)
        explain_a = _build_a_explain_from_predictions(pred_doc)

    # 既存 summary_obj に差し込む（キー追加のみ）
    summary_obj["headline"] = explain_a["headline"]
    summary_obj["bullets"] = explain_a["bullets"]
    summary_obj["uncertainty"] = explain_a["uncertainty"]
    summary_obj["watch"] = explain_a["watch"]
    summary_obj.setdefault("sources", {})
    summary_obj["sources"]["predictions_file"] = str(pred_path) if pred_path else None

    # summary.json を上書き保存（headline等が入った版）
    summary_path.write_text(json.dumps(summary_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] summary(+A explain) -> {summary_path}")

    # --- daily_summary_YYYY-MM-DD.json (schema fixed + one_liner) ---
    # daily_summary は explain_a から作る（順序事故を防ぐ）
    headline = safe_text(explain_a.get("headline")).strip()

    bullets = explain_a.get("bullets") or []
    if isinstance(bullets, str):
        bullets = [bullets]
    bullets = [safe_text(x).strip() for x in bullets if safe_text(x).strip()]

    uncertainty = safe_text(explain_a.get("uncertainty")).strip()

    watch = explain_a.get("watch") or []
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

    daily_summary = {
        "schema": {"name": "genesis.daily_summary", "version": "0.1.0"},
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
        "debug": {
            "predictions_count": len(bullets),
            "scenario_ids": [],
        },
    }

    daily_summary_path = ANALYSIS_DIR / f"daily_summary_{today_date}.json"
    daily_summary_path.write_text(
        json.dumps(daily_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] daily_summary -> {daily_summary_path}")
    # --- /daily_summary ---


    # --- A仕様 Explain（predictions_YYYY-MM-DD.json → headline/bullets/uncertainty/watch）---
    pred_path = _find_latest_predictions_file(ANALYSIS_DIR)
    if pred_path is None:
        explain_a = {"headline": "", "bullets": [], "uncertainty": "predictions file not found", "watch": []}
    else:
        pred_doc = _load_json(pred_path)
        explain_a = _build_a_explain_from_predictions(pred_doc)

    # 既存 summary_obj に差し込む（互換性を壊しにくい：キー追加のみ）
    summary_obj["headline"] = explain_a["headline"]
    summary_obj["bullets"] = explain_a["bullets"]
    summary_obj["uncertainty"] = explain_a["uncertainty"]
    summary_obj["watch"] = explain_a["watch"]
    summary_obj.setdefault("sources", {})
    summary_obj["sources"]["predictions_file"] = str(pred_path) if pred_path else None

    # もう一度 summary.json を上書き保存（headline等が入った版）
    summary_path.write_text(json.dumps(summary_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    

if __name__ == "__main__":
    main()

# docker/analyzer/analyze.py
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# anchors.py の実装差に耐える（どちらでも動く）
try:
    # あなたの anchors.py がこちらを提供している想定
    from anchors import extract_anchors, anchors_to_strings, Anchor  # type: ignore
    _ANCHOR_MODE = "extract_anchors"
except Exception:
    extract_anchors = None  # type: ignore
    anchors_to_strings = None  # type: ignore
    Anchor = object  # type: ignore
    _ANCHOR_MODE = "unknown"

try:
    # あなたの repo 側で存在する想定（best-effort）
    from history_analog import build_history_analog  # type: ignore
except Exception:
    build_history_analog = None  # type: ignore


# ----------------------------
# Paths (container side)
# ----------------------------
DATA_ROOT = Path("/data")
WORLD_DIR = DATA_ROOT / "world_politics"
ANALYSIS_DIR = WORLD_DIR / "analysis"
HISTORY_DIR = DATA_ROOT / "history"

RAW_DIR = WORLD_DIR  # daily raw files live directly under /data/world_politics/*.json

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ----------------------------
# JSON helpers (robust)
# ----------------------------
def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _date_from_stem(p: Path) -> Optional[str]:
    # expects YYYY-MM-DD.json
    stem = p.stem
    return stem if _DATE_RE.match(stem) else None


def resolve_target_date() -> Optional[str]:
    """
    Priority:
      1) env ANALYZE_DATE (recommended)
      2) env GENESIS_DATE (alias)
      3) env DATE (fallback)
      4) None -> auto (latest readable raw)
    """
    d = (os.getenv("ANALYZE_DATE") or os.getenv("GENESIS_DATE") or os.getenv("DATE") or "").strip()
    if not d:
        return None
    if not _DATE_RE.match(d):
        raise ValueError(f"Invalid date '{d}'. Use YYYY-MM-DD.")
    return d


def _list_raw_date_files() -> Dict[str, Path]:
    """
    /data/world_politics/*.json のうち、
    "YYYY-MM-DD.json" だけを raw として採用する。
    (daily_news_*.json 等は対象外)
    """
    dated: Dict[str, Path] = {}
    for p in RAW_DIR.glob("*.json"):
        ds = _date_from_stem(p)
        if ds:
            dated[ds] = p
    return dated


def _is_readable_raw(path: Path) -> bool:
    try:
        _load_json(path)
        return True
    except Exception:
        return False


def _pick_latest_readable_date(dated: Dict[str, Path]) -> str:
    for d in sorted(dated.keys(), reverse=True):
        if _is_readable_raw(dated[d]):
            return d
    raise FileNotFoundError(f"No readable raw JSON found under {RAW_DIR} (all candidates failed to parse)")


def pick_today_and_yesterday(dated: Dict[str, Path], target_date: Optional[str]) -> Tuple[Path, Optional[Path]]:
    """
    - target_date があれば、その日を優先（ただし壊れていたらエラー）
    - target_date がなければ、最新の “読める日” を today にする
    - yesterday は (today-1) があればそれ、無ければそれ以前の直近
      ※ yesterday が壊れていたら、さらに過去へスキップ
    """
    if not dated:
        raise FileNotFoundError(f"No raw date files (YYYY-MM-DD.json) found under {RAW_DIR}")

    if target_date:
        if target_date not in dated:
            raise FileNotFoundError(
                f"Target raw not found for date={target_date}. Expected: {RAW_DIR / (target_date + '.json')}"
            )
        today_path = dated[target_date]
        if not _is_readable_raw(today_path):
            raise RuntimeError(f"Target raw JSON is not readable (broken JSON): {today_path}")

        td = datetime.strptime(target_date, "%Y-%m-%d")
        for i in range(1, 60):
            y = (td - timedelta(days=i)).strftime("%Y-%m-%d")
            if y in dated and _is_readable_raw(dated[y]):
                return today_path, dated[y]
        return today_path, None

    today_date = _pick_latest_readable_date(dated)
    today_path = dated[today_date]

    td = datetime.strptime(today_date, "%Y-%m-%d")
    for i in range(1, 60):
        y = (td - timedelta(days=i)).strftime("%Y-%m-%d")
        if y in dated and _is_readable_raw(dated[y]):
            return today_path, dated[y]

    return today_path, None


# ----------------------------
# Raw parsing
# ----------------------------
def load_events_from_daily_file(path: Path) -> Tuple[str, str, List[Dict[str, Any]]]:
    data = _load_json(path)
    date_str = path.stem  # YYYY-MM-DD
    fetched_at = str(data.get("fetched_at", ""))
    articles = data.get("articles", []) or []
    if not isinstance(articles, list):
        articles = []

    safe: List[Dict[str, Any]] = []
    for a in articles:
        if isinstance(a, dict):
            safe.append(a)
    return date_str, fetched_at, safe


def summarize_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    titles = [str(e.get("title", "")).strip() for e in events if str(e.get("title", "")).strip()]
    return {"n": len(events), "titles": titles[:50]}


def url_set(events: List[Dict[str, Any]]) -> set:
    s = set()
    for e in events:
        u = e.get("url")
        if isinstance(u, str) and u:
            s.add(u)
    return s


def build_min_daily_doc(today_date: str, today_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    titles = [str(e.get("title", "")).strip() for e in today_events if str(e.get("title", "")).strip()]
    headline = titles[0] if titles else f"Daily Summary {today_date}"
    bullets = titles[1:9] if len(titles) > 1 else []
    return {
        "date": today_date,
        "headline": headline,
        "bullets": bullets,
        "one_liner": "",
        "delta_explanation": "",
    }


def build_min_diff(y_events: List[Dict[str, Any]], t_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    diff.py に依存せず、最低限の差分を作る。
    anchors.py に渡す“材料”として十分。
    """
    y_urls = url_set(y_events)
    t_urls = url_set(t_events)
    new_urls = sorted(list(t_urls - y_urls))
    gone_urls = sorted(list(y_urls - t_urls))

    y_titles = [str(e.get("title", "")).strip() for e in y_events if str(e.get("title", "")).strip()]
    t_titles = [str(e.get("title", "")).strip() for e in t_events if str(e.get("title", "")).strip()]

    return {
        "counts": {"yesterday": len(y_events), "today": len(t_events), "delta": len(t_events) - len(y_events)},
        "new_urls": new_urls[:80],
        "gone_urls": gone_urls[:80],
        "today_titles_top": t_titles[:30],
        "yesterday_titles_top": y_titles[:30],
    }


def anchors_to_jsonable(xs: List[Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for a in xs:
        try:
            out.append(asdict(a))  # dataclass -> dict
        except Exception:
            out.append(
                {"text": getattr(a, "text", ""), "kind": getattr(a, "kind", ""), "score": getattr(a, "score", 0.0)}
            )
    return out


# ----------------------------
# Main pipeline
# ----------------------------
def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    target_date = resolve_target_date()
    dated = _list_raw_date_files()

    today_file, yesterday_file = pick_today_and_yesterday(dated, target_date)
    today_date, fetched_at, today_events = load_events_from_daily_file(today_file)

    y_summary: Optional[Dict[str, Any]] = None
    y_events: List[Dict[str, Any]] = []
    diff_out: Dict[str, Any] = {"counts": {"yesterday": 0, "today": len(today_events), "delta": len(today_events)}}

    if yesterday_file is not None:
        _, _, y_events = load_events_from_daily_file(yesterday_file)
        y_summary = summarize_events(y_events)
        diff_out = build_min_diff(y_events, today_events)

        # diff_YYYY-MM-DD.json を出す（GUI/後段の材料）
        _write_json(ANALYSIS_DIR / f"diff_{today_date}.json", diff_out)

    # daily_doc（anchors抽出の材料）
    daily_doc = build_min_daily_doc(today_date, today_events)

    # anchors
    anchors_json: Dict[str, Any] = {"date": today_date, "anchors": [], "strings": []}
    if extract_anchors is not None and anchors_to_strings is not None:
        anchors_list = extract_anchors(diff_out, daily_doc, max_anchors=12)
        anchors_json = {
            "date": today_date,
            "anchors": anchors_to_jsonable(anchors_list),
            "strings": anchors_to_strings(anchors_list, max_n=10),
        }
    else:
        # ここに来るなら anchors 側の関数名が想定と違う
        anchors_json["note"] = "anchors module did not provide extract_anchors/anchors_to_strings"

    _write_json(ANALYSIS_DIR / "anchors.json", anchors_json)

    # summary.json
    summary = {
        "date": today_date,
        "fetched_at": fetched_at,
        "n_events": len(today_events),
        "yesterday_summary": y_summary,
        "new_urls": diff_out.get("new_urls", [])[:50] if isinstance(diff_out, dict) else [],
        "anchors": anchors_json.get("strings", []),
        "raw_file": str(today_file),
        "yesterday_file": str(yesterday_file) if yesterday_file else None,
    }
    _write_json(ANALYSIS_DIR / "summary.json", summary)

    # history analog（best-effort）
    if build_history_analog is not None:
        try:
            analog = build_history_analog(today_events, HISTORY_DIR)
            _write_json(ANALYSIS_DIR / f"analog_{today_date}.json", analog)
        except Exception:
            pass

    # latest.json
    _write_json(ANALYSIS_DIR / "latest.json", {"date": today_date})

    print(f"[OK] today: {today_date} events={len(today_events)} raw={today_file}")
    if yesterday_file is not None:
        print(f"[OK] yesterday: {yesterday_file.stem} raw={yesterday_file}")
        print(f"[OK] diff: {ANALYSIS_DIR / f'diff_{today_date}.json'}")
    else:
        print("[OK] yesterday: None")
    print(f"[OK] anchors: {ANALYSIS_DIR / 'anchors.json'} mode={_ANCHOR_MODE}")
    print(f"[OK] summary: {ANALYSIS_DIR / 'summary.json'}")
    print(f"[OK] latest: {ANALYSIS_DIR / 'latest.json'}")


if __name__ == "__main__":
    main()

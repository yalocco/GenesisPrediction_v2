#!/usr/bin/env python
"""
GenesisPrediction v2
build_view_model_latest.py

Purpose
- Rebuild data/world_politics/analysis/view_model_latest.json from the freshest "*_latest.json" artifacts.
- Fix cases where view_model_latest.json becomes stale while daily_summary/sentiment/health are updated.

Safe design
- Copy/merge only. Does NOT modify source artifacts.
- Writes only the target view_model_latest.json (and an optional timestamped backup if the target exists).

Run:
  .\.venv\Scripts\python.exe scripts\build_view_model_latest.py --date 2026-02-28

If --date is omitted, uses UTC date (yyyy-mm-dd).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union


Json = Union[Dict[str, Any], List[Any]]


# ----------------------------
# Time helpers
# ----------------------------
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def utc_today_ymd() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ----------------------------
# IO helpers
# ----------------------------
def read_json(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    raw = raw.lstrip("\ufeff").strip()
    return json.loads(raw) if raw else {}


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def backup_if_exists(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = path.with_suffix(path.suffix + f".bak.{ts}")
    bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return bak


# ----------------------------
# JSON probing (robust)
# ----------------------------
def _iter_items(obj: Any) -> Iterable[Any]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield v
    elif isinstance(obj, list):
        for v in obj:
            yield v


def deep_find_values(
    obj: Any,
    key_names: Iterable[str],
    want_type: Union[type, Tuple[type, ...]],
    *,
    max_depth: int = 10,
) -> List[Any]:
    """
    Depth-first search for values whose key (case-insensitive) matches any in key_names.
    Returns list of values (may be empty).
    """
    keys = {k.lower() for k in key_names}
    out: List[Any] = []

    def walk(x: Any, depth: int) -> None:
        if depth > max_depth:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, str) and k.lower() in keys and isinstance(v, want_type):
                    out.append(v)
                walk(v, depth + 1)
        elif isinstance(x, list):
            for v in x:
                walk(v, depth + 1)

    walk(obj, 0)
    return out


def deep_find_first(
    obj: Any,
    key_names: Iterable[str],
    want_type: Union[type, Tuple[type, ...]],
    *,
    max_depth: int = 10,
) -> Optional[Any]:
    vals = deep_find_values(obj, key_names, want_type, max_depth=max_depth)
    return vals[0] if vals else None


def deep_find_event_count(obj: Any) -> Optional[int]:
    """
    Try to infer an event count.
    - explicit keys
    - list lengths for keys like "events"/"articles"
    """
    explicit = deep_find_first(obj, ["events_count", "eventsCount", "n_events", "nEvents", "count"], (int, float))
    if isinstance(explicit, (int, float)):
        return int(explicit)

    # try list under common keys
    for key in ["events", "articles", "items", "rows"]:
        lst = deep_find_first(obj, [key], list)
        if isinstance(lst, list):
            return len(lst)

    return None


def normalize_as_of(obj: Dict[str, Any]) -> Optional[str]:
    """
    Extract a reasonable date-like string from known keys (flat or nested).
    """
    direct = deep_find_first(
        obj,
        ["as_of", "asOf", "date", "day", "generated_at", "generatedAt", "fetched_at", "fetchedAt"],
        str,
    )
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    # Sometimes date is an int like 20260228
    num = deep_find_first(obj, ["as_of", "asOf", "date", "day"], (int, float))
    if isinstance(num, (int, float)):
        s = str(int(num))
        if len(s) == 8:
            return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return None


def parse_ymd(s: str) -> Optional[str]:
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    # accept YYYY-MM-DD and ISO -> take first 10 chars if it looks like a date
    if len(s) >= 10 and s[4:5] == "-" and s[7:8] == "-":
        return s[:10]
    return None


def pick_first_nonempty(*vals: Any) -> Any:
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        return v
    return None


def coerce_summary_text(obj: Any) -> Optional[str]:
    """
    Try many known keys and common nesting; also supports a list of bullet strings.
    """
    # 1) direct/nested keys
    s = deep_find_first(obj, ["summary", "daily_summary", "text", "body", "content", "digest"], str)
    if isinstance(s, str) and s.strip():
        return s.strip()

    # 2) bullet list -> join
    bullets = deep_find_first(obj, ["bullets", "points", "highlights"], list)
    if isinstance(bullets, list):
        parts = [str(x).strip() for x in bullets if isinstance(x, (str, int, float)) and str(x).strip()]
        if parts:
            return "\n".join(f"- {p}" for p in parts)

    return None


def coerce_sentiment(obj: Any) -> Dict[str, Optional[float]]:
    """
    Try to find risk / positive / uncertainty numbers anywhere.
    This is intentionally permissive to survive schema changes.
    """
    # Prefer latest/today sections if present
    candidate = None
    for k in ["latest", "today", "current"]:
        sub = deep_find_first(obj, [k], dict)
        if isinstance(sub, dict):
            candidate = sub
            break
    x = candidate if candidate is not None else obj

    risk = deep_find_first(x, ["risk", "neg", "negative", "risk_score", "riskScore"], (int, float))
    pos = deep_find_first(x, ["positive", "pos", "positive_score", "positiveScore"], (int, float))
    unc = deep_find_first(x, ["uncertainty", "uncertain", "uncertainty_score", "uncertaintyScore"], (int, float))

    def f(v: Any) -> Optional[float]:
        if isinstance(v, (int, float)):
            return float(v)
        return None

    return {"risk": f(risk), "positive": f(pos), "uncertainty": f(unc)}


def coerce_health(obj: Any) -> Dict[str, Optional[int]]:
    """
    Try to find ok / warn / ng counts anywhere.
    """
    ok = deep_find_first(obj, ["ok", "OK", "ok_count", "okCount"], (int, float))
    warn = deep_find_first(obj, ["warn", "WARN", "warn_count", "warnCount"], (int, float))
    ng = deep_find_first(obj, ["ng", "NG", "ng_count", "ngCount"], (int, float))

    def i(v: Any) -> Optional[int]:
        if isinstance(v, (int, float)):
            return int(v)
        return None

    return {"ok": i(ok), "warn": i(warn), "ng": i(ng)}


# ----------------------------
# Main builder
# ----------------------------
@dataclass
class Inputs:
    root: Path
    date: str  # UTC YYYY-MM-DD
    src_dir: Path
    out_path: Path


def build_view_model(inp: Inputs) -> Dict[str, Any]:
    src = inp.src_dir

    paths = {
        "daily_summary_latest": src / "daily_summary_latest.json",
        "sentiment_latest": src / "sentiment_latest.json",
        "health_latest": src / "health_latest.json",
    }

    loaded: Dict[str, Any] = {}
    missing: Dict[str, str] = {}

    for k, p in paths.items():
        if p.exists():
            loaded[k] = read_json(p)
        else:
            missing[k] = str(p)

    summary_obj = loaded.get("daily_summary_latest", {})
    sentiment_obj = loaded.get("sentiment_latest", {})
    health_obj = loaded.get("health_latest", {})

    # as_of: freshest among the three artifacts; fallback to --date
    as_of_candidates = [
        parse_ymd(normalize_as_of(summary_obj) or ""),
        parse_ymd(normalize_as_of(sentiment_obj) or ""),
        parse_ymd(normalize_as_of(health_obj) or ""),
        inp.date,
    ]
    as_of = next((x for x in as_of_candidates if x), inp.date)

    daily_summary_text = coerce_summary_text(summary_obj)

    events_count = deep_find_event_count(summary_obj) or deep_find_event_count(loaded)  # fallback

    query = pick_first_nonempty(
        deep_find_first(summary_obj, ["query", "topic", "keyword"], str),
        deep_find_first(loaded, ["query", "topic", "keyword"], str),
    )

    sentiment = coerce_sentiment(sentiment_obj)
    health = coerce_health(health_obj)

    vm: Dict[str, Any] = {
        "meta": {
            "as_of": as_of,
            "generated_at": utc_now_iso(),
            "schema": "view_model_latest.v1",
            "notes": "rebuilt from *_latest.json (daily_summary/sentiment/health)",
        },
        "as_of": as_of,  # flat alias for older UIs
        "query": query,
        "events_count": events_count,
        "daily_summary": daily_summary_text,
        "sentiment": sentiment,
        "health": health,
        "sources": {
            "daily_summary_latest": str(paths["daily_summary_latest"]),
            "sentiment_latest": str(paths["sentiment_latest"]),
            "health_latest": str(paths["health_latest"]),
        },
        "missing": missing,
    }

    return vm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", type=str, default="", help="UTC date YYYY-MM-DD (default: UTC today)")
    ap.add_argument("--root", type=str, default="", help="Repo root (default: auto from this script location)")
    args = ap.parse_args()

    here = Path(__file__).resolve()
    root = Path(args.root).resolve() if args.root else here.parents[1]

    date = args.date.strip() or utc_today_ymd()
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(f"[ERROR] --date must be YYYY-MM-DD, got: {date}")

    src_dir = root / "data" / "world_politics" / "analysis"
    out_path = src_dir / "view_model_latest.json"

    if not src_dir.exists():
        raise SystemExit(f"[ERROR] source dir not found: {src_dir}")

    inp = Inputs(root=root, date=date, src_dir=src_dir, out_path=out_path)

    bak = backup_if_exists(out_path)
    vm = build_view_model(inp)

    ensure_dir(out_path.parent)
    out_path.write_text(json.dumps(vm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("[OK] rebuilt view_model_latest.json")
    print(f"  out : {out_path}")
    if bak:
        print(f"  bak : {bak}")
    print(f"  as_of: {vm.get('meta', {}).get('as_of')}  generated_at: {vm.get('meta', {}).get('generated_at')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def pick_number(*values: Any) -> Optional[float]:
    for value in values:
        try:
            n = float(value)
        except Exception:
            continue
        if n == n:
            return n
    return None


def normalize_percent_number(value: Any) -> Optional[float]:
    n = pick_number(value)
    if n is None:
        return None
    return n * 100.0 if n <= 1.0 else n


def normalize_list_items(value: Any) -> List[str]:
    items: List[str] = []
    for item in safe_list(value):
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
        elif isinstance(item, dict):
            text = first_non_empty(
                item.get("summary"),
                item.get("label"),
                item.get("name"),
                item.get("title"),
                item.get("description"),
                item.get("message"),
                item.get("text"),
                item.get("signal"),
                item.get("kind"),
            )
            if text:
                items.append(text)

    seen = set()
    unique: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def normalize_fx_status(value: Any) -> str:
    text = str(value or "").strip().upper()

    if text in {"SAFE", "OK", "ON", "BUY", "RISK_ON"}:
        return "SAFE"
    if text in {"CAUTION", "WARN", "WARNING", "HOLD", "MIXED"}:
        return "CAUTION"
    if text in {"DANGER", "OFF", "SELL", "RISK_OFF"}:
        return "DANGER"

    return ""


def extract_summary_text(summary_json: Dict[str, Any], daily_summary_json: Dict[str, Any]) -> Optional[str]:
    candidates: List[Any] = [
        summary_json.get("summary"),
        summary_json.get("text"),
        summary_json.get("daily_summary"),
        summary_json.get("body"),
        summary_json.get("content"),
    ]

    overview = summary_json.get("overview")
    if isinstance(overview, dict):
        candidates.extend([
            overview.get("summary"),
            overview.get("text"),
            overview.get("body"),
        ])

    daily_candidates: List[Any] = [
        daily_summary_json.get("summary"),
        daily_summary_json.get("text"),
        daily_summary_json.get("daily_summary"),
        daily_summary_json.get("summary_text"),
        daily_summary_json.get("body"),
        daily_summary_json.get("content"),
    ]

    yesterday_summary = daily_summary_json.get("yesterday_summary")
    if isinstance(yesterday_summary, dict):
        daily_candidates.extend([
            yesterday_summary.get("summary"),
            yesterday_summary.get("text"),
            yesterday_summary.get("body"),
        ])

    return first_non_empty(*(candidates + daily_candidates))


def extract_titles(news_json: Dict[str, Any], daily_summary_json: Dict[str, Any]) -> List[str]:
    titles: List[str] = []

    for key in ("events", "items", "articles", "news"):
        items = news_json.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    title = first_non_empty(
                        item.get("title"),
                        item.get("headline"),
                        item.get("name"),
                    )
                    if title:
                        titles.append(title)

    yesterday_summary = daily_summary_json.get("yesterday_summary")
    if isinstance(yesterday_summary, dict):
        ys_titles = yesterday_summary.get("titles")
        if isinstance(ys_titles, list):
            for title in ys_titles:
                if isinstance(title, str) and title.strip():
                    titles.append(title.strip())

    seen = set()
    unique_titles: List[str] = []
    for title in titles:
        if title not in seen:
            seen.add(title)
            unique_titles.append(title)
    return unique_titles


def extract_highlights(summary_json: Dict[str, Any], daily_summary_json: Dict[str, Any], titles: List[str]) -> List[str]:
    highlights: List[str] = []

    for key in ("highlights", "bullets", "key_points"):
        value = summary_json.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    highlights.append(item.strip())

    anchors = daily_summary_json.get("anchors")
    if isinstance(anchors, list):
        anchor_line = ", ".join(str(x).strip() for x in anchors if str(x).strip())
        if anchor_line:
            highlights.append(f"Anchors: {anchor_line}")

    if not highlights:
        highlights.extend(titles[:5])

    return highlights[:8]


def extract_prediction_block(prediction_json: Dict[str, Any]) -> Dict[str, Any]:
    if not prediction_json:
        return {
            "available": False,
            "as_of": "",
            "generated_at": "",
            "engine_version": "",
            "risk": "",
            "dominant_scenario": "",
            "confidence": None,
            "confidence_pct": None,
            "summary": "",
            "drivers": [],
            "watchpoints": [],
            "action_bias": "",
            "historical_context": [],
            "source": "analysis/prediction/prediction_latest.json",
        }

    dominant_scenario = first_non_empty(
        prediction_json.get("dominant_scenario"),
        prediction_json.get("dominant_branch"),
        prediction_json.get("scenario"),
        prediction_json.get("regime"),
    )

    confidence_raw = pick_number(prediction_json.get("confidence"))
    confidence_pct = normalize_percent_number(confidence_raw)

    summary = first_non_empty(
        prediction_json.get("summary"),
        prediction_json.get("prediction_statement"),
        prediction_json.get("primary_narrative"),
    )

    drivers = normalize_list_items(prediction_json.get("key_drivers"))
    watchpoints = normalize_list_items(prediction_json.get("monitoring_priorities"))
    historical_context = normalize_list_items(prediction_json.get("historical_context"))

    return {
        "available": True,
        "as_of": first_non_empty(
            prediction_json.get("as_of"),
            prediction_json.get("date"),
            prediction_json.get("generated_at"),
        ) or "",
        "generated_at": first_non_empty(prediction_json.get("generated_at")) or "",
        "engine_version": first_non_empty(prediction_json.get("engine_version")) or "",
        "risk": first_non_empty(prediction_json.get("risk")) or "",
        "dominant_scenario": dominant_scenario or "",
        "confidence": confidence_raw,
        "confidence_pct": confidence_pct,
        "summary": summary or "",
        "drivers": drivers[:5],
        "watchpoints": watchpoints[:5],
        "action_bias": first_non_empty(prediction_json.get("action_bias")) or "",
        "historical_context": historical_context[:3],
        "source": "analysis/prediction/prediction_latest.json",
    }


def extract_fx_block(fx_json: Dict[str, Any]) -> Dict[str, Any]:
    if not fx_json:
        return {
            "available": False,
            "as_of": "",
            "generated_at": "",
            "status": "",
            "raw_status": "",
            "pair": "",
            "summary": "",
            "reason": "",
            "action": "",
            "source": "analysis/fx/fx_decision_latest.json",
        }

    raw_status = first_non_empty(
        fx_json.get("primary"),
        fx_json.get("decision"),
        fx_json.get("status"),
        fx_json.get("regime"),
    ) or ""

    status = normalize_fx_status(raw_status)
    pair = first_non_empty(
        fx_json.get("pair"),
        fx_json.get("primary_pair"),
        fx_json.get("symbol"),
    ) or ""

    reason = first_non_empty(
        fx_json.get("reason"),
        fx_json.get("note"),
        fx_json.get("message"),
    ) or ""

    action = first_non_empty(
        fx_json.get("action"),
        fx_json.get("recommendation"),
    ) or ""

    summary = first_non_empty(
        fx_json.get("summary"),
        fx_json.get("headline"),
    )
    if not summary:
        summary_parts: List[str] = []
        if pair:
            summary_parts.append(pair)
        if status:
            summary_parts.append(status)
        elif raw_status:
            summary_parts.append(raw_status.upper())
        if reason:
            summary_parts.append(reason)
        summary = ": ".join(summary_parts[:2]) if len(summary_parts) >= 2 else " ".join(summary_parts)

    return {
        "available": True,
        "as_of": first_non_empty(
            fx_json.get("as_of"),
            fx_json.get("date"),
            fx_json.get("generated_at"),
            fx_json.get("updated"),
        ) or "",
        "generated_at": first_non_empty(
            fx_json.get("generated_at"),
            fx_json.get("updated"),
        ) or "",
        "status": status,
        "raw_status": raw_status.upper() if raw_status else "",
        "pair": pair,
        "summary": summary or "",
        "reason": reason,
        "action": action,
        "source": "analysis/fx/fx_decision_latest.json",
    }


def build_payload(
    date_value: str,
    summary_text: Optional[str],
    titles: List[str],
    highlights: List[str],
    daily_summary_json: Dict[str, Any],
    prediction_json: Dict[str, Any],
    fx_json: Dict[str, Any],
) -> Dict[str, Any]:
    new_urls = daily_summary_json.get("new_urls")
    if not isinstance(new_urls, list):
        new_urls = []

    n_events = daily_summary_json.get("n_events")
    if not isinstance(n_events, int):
        n_events = len(titles)

    prediction_block = extract_prediction_block(prediction_json)
    fx_block = extract_fx_block(fx_json)

    return {
        "status": "ok",
        "generated_at": now_iso(),
        "date": date_value,
        "summary": summary_text or "",
        "summary_available": bool(summary_text),
        "highlights": highlights,
        "articles": titles[:12],
        "meta": {
            "n_events": n_events,
            "new_url_count": len(new_urls),
        },
        "prediction": prediction_block,
        "fx": fx_block,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build digest view model.")
    parser.add_argument("--date", required=True, help="Target local date YYYY-MM-DD")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    world_analysis_dir = root / "data" / "world_politics" / "analysis"
    digest_dir = root / "data" / "digest"
    digest_view_dir = digest_dir / "view"
    prediction_analysis_dir = root / "analysis" / "prediction"
    fx_analysis_dir = root / "analysis" / "fx"

    daily_news_path = world_analysis_dir / f"daily_news_{args.date}.json"
    daily_summary_latest_path = world_analysis_dir / "daily_summary_latest.json"
    summary_json_path = world_analysis_dir / "summary.json"
    prediction_latest_path = prediction_analysis_dir / "prediction_latest.json"
    fx_decision_latest_path = fx_analysis_dir / "fx_decision_latest.json"

    daily_news_json = load_json(daily_news_path)
    daily_summary_json = load_json(daily_summary_latest_path)
    summary_json = load_json(summary_json_path)
    prediction_json = load_json(prediction_latest_path)
    fx_json = load_json(fx_decision_latest_path)

    summary_text = extract_summary_text(summary_json, daily_summary_json)
    titles = extract_titles(daily_news_json, daily_summary_json)
    highlights = extract_highlights(summary_json, daily_summary_json, titles)

    payload = build_payload(
        date_value=args.date,
        summary_text=summary_text,
        titles=titles,
        highlights=highlights,
        daily_summary_json=daily_summary_json,
        prediction_json=prediction_json,
        fx_json=fx_json,
    )

    dated_path = digest_view_dir / f"{args.date}.json"
    latest_path_a = digest_dir / "view_model_latest.json"
    latest_path_b = digest_view_dir / "view_model_latest.json"

    write_json(dated_path, payload)
    write_json(latest_path_a, payload)
    write_json(latest_path_b, payload)

    print(f"[OK] wrote dated : {dated_path.as_posix()}")
    print(f"[OK] wrote latest: {latest_path_a.as_posix()}")
    print(f"[OK] wrote latest: {latest_path_b.as_posix()}")

    if payload["summary_available"]:
        print("[OK] summary loaded")
    else:
        print("[WARN] summary missing (summary.json / daily_summary_latest.json text not found)")

    if payload["prediction"]["available"]:
        print("[OK] prediction integrated")
        print(f"[OK] prediction risk       : {payload['prediction']['risk']}")
        print(f"[OK] prediction dominant   : {payload['prediction']['dominant_scenario']}")
        print(f"[OK] prediction confidence : {payload['prediction']['confidence_pct']}")
    else:
        print("[WARN] prediction missing (analysis/prediction/prediction_latest.json not found)")

    if payload["fx"]["available"]:
        print("[OK] fx integrated")
        print(f"[OK] fx status            : {payload['fx']['status'] or payload['fx']['raw_status']}")
        print(f"[OK] fx pair              : {payload['fx']['pair']}")
    else:
        print("[WARN] fx missing (analysis/fx/fx_decision_latest.json not found)")


if __name__ == "__main__":
    main()
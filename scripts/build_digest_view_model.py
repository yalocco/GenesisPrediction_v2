#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


LANG_DEFAULT = "ja"
SUPPORTED_LANGUAGES = ["en", "ja", "th"]


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

    if text in {"SAFE", "OK", "ON", "BUY", "RISK_ON", "SEND"}:
        return "SAFE"
    if text in {"CAUTION", "WARN", "WARNING", "HOLD", "MIXED", "SPLIT"}:
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


def normalize_lang_map(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, str] = {}
    for lang in SUPPORTED_LANGUAGES:
        text = value.get(lang)
        if text is None:
            continue
        text_str = str(text).strip()
        if text_str:
            out[lang] = text_str
    return out


def normalize_lang_list_map(value: Any) -> Dict[str, List[str]]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, List[str]] = {}
    for lang in SUPPORTED_LANGUAGES:
        items = value.get(lang)
        if not isinstance(items, list):
            continue
        out[lang] = [str(x).strip() for x in items if str(x).strip()]
    return out


def finalize_text_i18n(base_text: str, partial: Dict[str, str]) -> Dict[str, str]:
    en_text = str(partial.get("en") or base_text or "").strip()
    ja_text = str(partial.get("ja") or en_text).strip()
    th_text = str(partial.get("th") or en_text).strip()
    return {
        "en": en_text,
        "ja": ja_text,
        "th": th_text,
    }


def finalize_list_i18n(base_list: List[str], partial: Dict[str, List[str]]) -> Dict[str, List[str]]:
    en_list = partial.get("en") or list(base_list)
    ja_list = partial.get("ja") or list(en_list)
    th_list = partial.get("th") or list(en_list)
    return {
        "en": en_list,
        "ja": ja_list,
        "th": th_list,
    }


def pick_i18n_text(data: Dict[str, Any], base_key: str) -> str:
    i18n = normalize_lang_map(data.get(f"{base_key}_i18n"))
    if i18n:
        preferred = str(i18n.get(LANG_DEFAULT) or "").strip()
        if preferred:
            return preferred
        en_text = str(i18n.get("en") or "").strip()
        if en_text:
            return en_text
        first_text = first_non_empty(*(i18n.get(lang) for lang in SUPPORTED_LANGUAGES))
        if first_text:
            return first_text
    return str(data.get(base_key) or "").strip()


def pick_i18n_text_map(data: Dict[str, Any], base_key: str) -> Dict[str, str]:
    base_text = str(data.get(base_key) or "").strip()
    partial = normalize_lang_map(data.get(f"{base_key}_i18n"))
    return finalize_text_i18n(base_text, partial)


def pick_i18n_list(data: Dict[str, Any], base_key: str) -> List[str]:
    partial = normalize_lang_list_map(data.get(f"{base_key}_i18n"))
    preferred = partial.get(LANG_DEFAULT)
    if preferred:
        return preferred
    en_list = partial.get("en")
    if en_list:
        return en_list
    base_list = normalize_list_items(data.get(base_key))
    return base_list


def pick_i18n_list_map(data: Dict[str, Any], base_key: str) -> Dict[str, List[str]]:
    base_list = normalize_list_items(data.get(base_key))
    partial = normalize_lang_list_map(data.get(f"{base_key}_i18n"))
    return finalize_list_i18n(base_list, partial)


def extract_historical_context_items(prediction_json: Dict[str, Any]) -> List[str]:
    historical_context = prediction_json.get("historical_context")
    if isinstance(historical_context, dict):
        summary_i18n = normalize_lang_map(historical_context.get("summary_i18n"))
        if summary_i18n:
            preferred = summary_i18n.get(LANG_DEFAULT) or summary_i18n.get("en")
            if preferred:
                return [str(preferred).strip()]
        summary = first_non_empty(historical_context.get("summary"))
        if summary:
            return [summary]
    return normalize_list_items(historical_context)


def extract_historical_context_i18n(prediction_json: Dict[str, Any]) -> Dict[str, List[str]]:
    historical_context = prediction_json.get("historical_context")
    if isinstance(historical_context, dict):
        summary = first_non_empty(historical_context.get("summary")) or ""
        summary_i18n = normalize_lang_map(historical_context.get("summary_i18n"))
        if summary_i18n or summary:
            return finalize_list_i18n([summary] if summary else [], {
                "en": [summary_i18n.get("en", summary)] if summary_i18n.get("en") or summary else [],
                "ja": [summary_i18n.get("ja", summary_i18n.get("en", summary))] if summary_i18n.get("ja") or summary_i18n.get("en") or summary else [],
                "th": [summary_i18n.get("th", summary_i18n.get("en", summary))] if summary_i18n.get("th") or summary_i18n.get("en") or summary else [],
            })
    return finalize_list_i18n(
        normalize_list_items(historical_context),
        normalize_lang_list_map(prediction_json.get("historical_context_i18n")),
    )


def extract_prediction_block(prediction_json: Dict[str, Any]) -> Dict[str, Any]:
    if not prediction_json:
        return {
            "available": False,
            "as_of": "",
            "generated_at": "",
            "engine_version": "",
            "lang_default": LANG_DEFAULT,
            "languages": SUPPORTED_LANGUAGES,
            "risk": "",
            "dominant_scenario": "",
            "confidence": None,
            "confidence_pct": None,
            "summary": "",
            "summary_i18n": {"en": "", "ja": "", "th": ""},
            "prediction_statement": "",
            "prediction_statement_i18n": {"en": "", "ja": "", "th": ""},
            "primary_narrative": "",
            "primary_narrative_i18n": {"en": "", "ja": "", "th": ""},
            "drivers": [],
            "drivers_i18n": {"en": [], "ja": [], "th": []},
            "watchpoints": [],
            "watchpoints_i18n": {"en": [], "ja": [], "th": []},
            "action_bias": "",
            "action_bias_i18n": {"en": "", "ja": "", "th": ""},
            "expected_outcomes": [],
            "expected_outcomes_i18n": {"en": [], "ja": [], "th": []},
            "historical_context": [],
            "historical_context_i18n": {"en": [], "ja": [], "th": []},
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

    summary_i18n = pick_i18n_text_map(prediction_json, "summary")
    prediction_statement_i18n = pick_i18n_text_map(prediction_json, "prediction_statement")
    primary_narrative_i18n = pick_i18n_text_map(prediction_json, "primary_narrative")
    action_bias_i18n = pick_i18n_text_map(prediction_json, "action_bias")

    drivers_i18n = pick_i18n_list_map(prediction_json, "key_drivers")
    watchpoints_i18n = pick_i18n_list_map(prediction_json, "monitoring_priorities")
    expected_outcomes_i18n = pick_i18n_list_map(prediction_json, "expected_outcomes")
    historical_context_i18n = extract_historical_context_i18n(prediction_json)

    summary = first_non_empty(
        summary_i18n.get(LANG_DEFAULT),
        summary_i18n.get("en"),
        prediction_statement_i18n.get(LANG_DEFAULT),
        prediction_statement_i18n.get("en"),
        primary_narrative_i18n.get(LANG_DEFAULT),
        primary_narrative_i18n.get("en"),
    )

    drivers = drivers_i18n.get(LANG_DEFAULT) or drivers_i18n.get("en") or []
    watchpoints = watchpoints_i18n.get(LANG_DEFAULT) or watchpoints_i18n.get("en") or []
    expected_outcomes = expected_outcomes_i18n.get(LANG_DEFAULT) or expected_outcomes_i18n.get("en") or []
    historical_context = historical_context_i18n.get(LANG_DEFAULT) or historical_context_i18n.get("en") or []

    return {
        "available": True,
        "as_of": first_non_empty(
            prediction_json.get("as_of"),
            prediction_json.get("date"),
            prediction_json.get("generated_at"),
        ) or "",
        "generated_at": first_non_empty(prediction_json.get("generated_at")) or "",
        "engine_version": first_non_empty(prediction_json.get("engine_version")) or "",
        "lang_default": first_non_empty(prediction_json.get("lang_default")) or LANG_DEFAULT,
        "languages": prediction_json.get("languages") if isinstance(prediction_json.get("languages"), list) else list(SUPPORTED_LANGUAGES),
        "risk": first_non_empty(prediction_json.get("risk")) or "",
        "dominant_scenario": dominant_scenario or "",
        "confidence": confidence_raw,
        "confidence_pct": confidence_pct,
        "summary": summary or "",
        "summary_i18n": summary_i18n,
        "prediction_statement": pick_i18n_text(prediction_json, "prediction_statement"),
        "prediction_statement_i18n": prediction_statement_i18n,
        "primary_narrative": pick_i18n_text(prediction_json, "primary_narrative"),
        "primary_narrative_i18n": primary_narrative_i18n,
        "drivers": drivers[:5],
        "drivers_i18n": {
            "en": (drivers_i18n.get("en") or [])[:5],
            "ja": (drivers_i18n.get("ja") or drivers_i18n.get("en") or [])[:5],
            "th": (drivers_i18n.get("th") or drivers_i18n.get("en") or [])[:5],
        },
        "watchpoints": watchpoints[:5],
        "watchpoints_i18n": {
            "en": (watchpoints_i18n.get("en") or [])[:5],
            "ja": (watchpoints_i18n.get("ja") or watchpoints_i18n.get("en") or [])[:5],
            "th": (watchpoints_i18n.get("th") or watchpoints_i18n.get("en") or [])[:5],
        },
        "action_bias": pick_i18n_text(prediction_json, "action_bias"),
        "action_bias_i18n": action_bias_i18n,
        "expected_outcomes": expected_outcomes[:10],
        "expected_outcomes_i18n": {
            "en": (expected_outcomes_i18n.get("en") or [])[:10],
            "ja": (expected_outcomes_i18n.get("ja") or expected_outcomes_i18n.get("en") or [])[:10],
            "th": (expected_outcomes_i18n.get("th") or expected_outcomes_i18n.get("en") or [])[:10],
        },
        "historical_context": historical_context[:3],
        "historical_context_i18n": {
            "en": (historical_context_i18n.get("en") or [])[:3],
            "ja": (historical_context_i18n.get("ja") or historical_context_i18n.get("en") or [])[:3],
            "th": (historical_context_i18n.get("th") or historical_context_i18n.get("en") or [])[:3],
        },
        "source": "analysis/prediction/prediction_latest.json",
    }


def extract_fx_block(fx_json: Dict[str, Any]) -> Dict[str, Any]:
    if not fx_json:
        return {
            "available": False,
            "as_of": "",
            "generated_at": "",
            "lang_default": LANG_DEFAULT,
            "languages": SUPPORTED_LANGUAGES,
            "status": "",
            "status_i18n": {"en": "", "ja": "", "th": ""},
            "raw_status": "",
            "pair": "",
            "pair_i18n": {"en": "", "ja": "", "th": ""},
            "summary": "",
            "summary_i18n": {"en": "", "ja": "", "th": ""},
            "reason": "",
            "reason_i18n": {"en": "", "ja": "", "th": ""},
            "action": "",
            "action_i18n": {"en": "", "ja": "", "th": ""},
            "watchpoints": [],
            "watchpoints_i18n": {"en": [], "ja": [], "th": []},
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

    pair_i18n = pick_i18n_text_map(fx_json, "pair")
    decision_i18n = pick_i18n_text_map(fx_json, "decision")
    status_i18n = pick_i18n_text_map(fx_json, "status")
    action_i18n = pick_i18n_text_map(fx_json, "action")
    recommendation_i18n = pick_i18n_text_map(fx_json, "recommendation")
    reason_i18n = pick_i18n_text_map(fx_json, "reason")
    watchpoints_i18n = pick_i18n_list_map(fx_json, "watchpoints")

    reason = pick_i18n_text(fx_json, "reason")
    action = first_non_empty(
        pick_i18n_text(fx_json, "action"),
        pick_i18n_text(fx_json, "recommendation"),
    ) or ""

    summary_i18n = normalize_lang_map(fx_json.get("summary_i18n"))
    summary = first_non_empty(
        summary_i18n.get(LANG_DEFAULT),
        summary_i18n.get("en"),
        reason_i18n.get(LANG_DEFAULT),
        reason_i18n.get("en"),
    )

    if not summary:
        summary_parts: List[str] = []
        pair_text = first_non_empty(pair_i18n.get(LANG_DEFAULT), pair_i18n.get("en"), pair)
        status_text = first_non_empty(status_i18n.get(LANG_DEFAULT), status_i18n.get("en"), decision_i18n.get(LANG_DEFAULT), decision_i18n.get("en"), raw_status.upper() if raw_status else "")
        if pair_text:
            summary_parts.append(pair_text)
        if status_text:
            summary_parts.append(status_text)
        summary = ": ".join(summary_parts[:2]) if len(summary_parts) >= 2 else " ".join(summary_parts)

    if not summary_i18n:
        summary_i18n = finalize_text_i18n(summary or "", {
            "en": first_non_empty(reason_i18n.get("en"), summary) or "",
            "ja": first_non_empty(reason_i18n.get("ja"), reason_i18n.get("en"), summary) or "",
            "th": first_non_empty(reason_i18n.get("th"), reason_i18n.get("en"), summary) or "",
        })

    watchpoints = watchpoints_i18n.get(LANG_DEFAULT) or watchpoints_i18n.get("en") or []

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
        "lang_default": first_non_empty(fx_json.get("lang_default")) or LANG_DEFAULT,
        "languages": fx_json.get("languages") if isinstance(fx_json.get("languages"), list) else list(SUPPORTED_LANGUAGES),
        "status": first_non_empty(
            status_i18n.get(LANG_DEFAULT),
            status_i18n.get("en"),
            decision_i18n.get(LANG_DEFAULT),
            decision_i18n.get("en"),
            status,
            raw_status.upper() if raw_status else "",
        ) or "",
        "status_i18n": finalize_text_i18n(
            first_non_empty(status, raw_status.upper() if raw_status else "") or "",
            {
                "en": first_non_empty(status_i18n.get("en"), decision_i18n.get("en"), status, raw_status.upper() if raw_status else "") or "",
                "ja": first_non_empty(status_i18n.get("ja"), decision_i18n.get("ja"), status_i18n.get("en"), decision_i18n.get("en"), status, raw_status.upper() if raw_status else "") or "",
                "th": first_non_empty(status_i18n.get("th"), decision_i18n.get("th"), status_i18n.get("en"), decision_i18n.get("en"), status, raw_status.upper() if raw_status else "") or "",
            },
        ),
        "raw_status": raw_status.upper() if raw_status else "",
        "pair": first_non_empty(pair_i18n.get(LANG_DEFAULT), pair_i18n.get("en"), pair) or "",
        "pair_i18n": finalize_text_i18n(pair, pair_i18n),
        "summary": summary or "",
        "summary_i18n": summary_i18n,
        "reason": reason,
        "reason_i18n": reason_i18n,
        "action": first_non_empty(
            action_i18n.get(LANG_DEFAULT),
            action_i18n.get("en"),
            recommendation_i18n.get(LANG_DEFAULT),
            recommendation_i18n.get("en"),
            action,
        ) or "",
        "action_i18n": finalize_text_i18n(action, {
            "en": first_non_empty(action_i18n.get("en"), recommendation_i18n.get("en"), action) or "",
            "ja": first_non_empty(action_i18n.get("ja"), recommendation_i18n.get("ja"), action_i18n.get("en"), recommendation_i18n.get("en"), action) or "",
            "th": first_non_empty(action_i18n.get("th"), recommendation_i18n.get("th"), action_i18n.get("en"), recommendation_i18n.get("en"), action) or "",
        }),
        "watchpoints": watchpoints[:5],
        "watchpoints_i18n": {
            "en": (watchpoints_i18n.get("en") or [])[:5],
            "ja": (watchpoints_i18n.get("ja") or watchpoints_i18n.get("en") or [])[:5],
            "th": (watchpoints_i18n.get("th") or watchpoints_i18n.get("en") or [])[:5],
        },
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
        "lang_default": LANG_DEFAULT,
        "languages": SUPPORTED_LANGUAGES,
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
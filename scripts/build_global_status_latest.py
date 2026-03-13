#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scripts/build_global_status_latest.py

Purpose
-------
Build analysis/global_status_latest.json as the single source of truth
for the shared Global Status UI component.

Design Rules
------------
- analysis is the Single Source of Truth
- UI must be display only
- This script may read existing analysis artifacts only
- No UI-side fallback logic
- No page-specific workaround logic

Input candidates
----------------
- analysis/prediction/prediction_latest.json
- analysis/prediction_latest.json
- analysis/scenario_latest.json
- analysis/signal_latest.json
- analysis/daily_summary_latest.json
- analysis/sentiment_latest.json
- analysis/health_latest.json
- analysis/fx_decision_latest.json

Output
------
- analysis/global_status_latest.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RISK_ORDER = {
    "low": 0,
    "guarded": 1,
    "elevated": 2,
    "high": 3,
    "critical": 4,
}


@dataclass
class LoadedJson:
    path: str
    data: dict[str, Any] | None


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_first(root: Path, candidates: list[str]) -> LoadedJson:
    for rel in candidates:
        p = root / rel
        data = _read_json(p)
        if isinstance(data, dict):
            return LoadedJson(path=rel.replace("\\", "/"), data=data)
    return LoadedJson(path="", data=None)


def _safe_number(value: Any, fallback: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return fallback
        n = float(value)
        if n != n:  # NaN check
            return fallback
        return n
    except Exception:
        return fallback


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _normalize_risk_level(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in RISK_ORDER:
        return text
    if text == "warn":
        return "elevated"
    if text == "warning":
        return "elevated"
    if text == "ok":
        return "low"
    if text == "ready":
        return "low"
    if text == "risk_off":
        return "high"
    if text == "mixed":
        return "guarded"
    return ""


def _risk_from_score(score: float | None) -> str:
    if score is None:
        return ""
    s = max(0.0, min(1.0, score))
    if s >= 0.86:
        return "critical"
    if s >= 0.68:
        return "high"
    if s >= 0.48:
        return "elevated"
    if s >= 0.24:
        return "guarded"
    return "low"


def _sentiment_counts(sentiment: dict[str, Any] | None) -> dict[str, int]:
    if not isinstance(sentiment, dict):
        return {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "mixed": 0,
            "items": 0,
        }

    labels = sentiment.get("labels") or sentiment.get("counts") or {}

    positive = int(_safe_number(_first_non_empty(sentiment.get("positive"), labels.get("positive")), 0) or 0)
    negative = int(_safe_number(_first_non_empty(sentiment.get("negative"), labels.get("negative")), 0) or 0)
    neutral = int(_safe_number(_first_non_empty(sentiment.get("neutral"), labels.get("neutral")), 0) or 0)
    mixed = int(_safe_number(_first_non_empty(sentiment.get("mixed"), labels.get("mixed")), 0) or 0)

    items = int(
        _safe_number(
            _first_non_empty(
                sentiment.get("items"),
                sentiment.get("count"),
            ),
            positive + negative + neutral + mixed,
        )
        or 0
    )

    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "mixed": mixed,
        "items": max(items, positive + negative + neutral + mixed),
    }


def _derive_sentiment_value(sentiment: dict[str, Any] | None) -> tuple[str, str, dict[str, int]]:
    if not isinstance(sentiment, dict):
        return "--", "sentiment unavailable", _sentiment_counts(None)

    counts = _sentiment_counts(sentiment)

    positive = counts["positive"]
    negative = counts["negative"]
    neutral = counts["neutral"]
    mixed = counts["mixed"]

    if mixed >= positive and mixed >= negative and mixed >= neutral:
        value = "MIX"
    elif negative >= positive and negative >= neutral:
        value = "NEG"
    elif positive >= neutral:
        value = "POS"
    else:
        value = "NEU"

    sub = f"pos {positive} / neg {negative} / neu {neutral} / mix {mixed}"
    return value, sub, counts


def _derive_health_value(health: dict[str, Any] | None) -> tuple[str, str, dict[str, int]]:
    if not isinstance(health, dict):
        return "--", "health unavailable", {
            "ok": 0,
            "warn": 0,
            "ng": 0,
            "total": 0,
        }

    summary = health.get("summary") if isinstance(health.get("summary"), dict) else {}

    explicit = _first_non_empty(
        summary.get("status"),
        health.get("status"),
    ).upper()

    ok = int(_safe_number(_first_non_empty(summary.get("ok"), health.get("ok")), 0) or 0)
    warn = int(_safe_number(_first_non_empty(summary.get("warn"), health.get("warn")), 0) or 0)
    ng = int(_safe_number(_first_non_empty(summary.get("ng"), health.get("ng")), 0) or 0)
    total = int(_safe_number(_first_non_empty(summary.get("total"), health.get("total")), ok + warn + ng) or 0)

    if explicit and explicit != "DEGRADED":
        value = explicit
    elif ng > 0:
        value = "NG"
    elif warn > 0:
        value = "WARN"
    elif explicit == "DEGRADED":
        value = "DEGRADED"
    else:
        value = "OK"

    sub = f"ok {ok} / warn {warn} / ng {ng}"
    return value, sub, {
        "ok": ok,
        "warn": warn,
        "ng": ng,
        "total": total,
    }


def _derive_fx_value(fx_decision: dict[str, Any] | None) -> tuple[str, str]:
    if not isinstance(fx_decision, dict):
        return "--", "fx decision unavailable"

    value = _first_non_empty(
        fx_decision.get("decision"),
        fx_decision.get("status"),
        fx_decision.get("regime"),
    ).upper()

    sub = _first_non_empty(
        fx_decision.get("reason"),
        fx_decision.get("note"),
        fx_decision.get("action"),
    )

    return value or "--", sub or "fx decision latest"


def _derive_articles_value(summary: dict[str, Any] | None) -> tuple[str, str, int]:
    if not isinstance(summary, dict):
        return "--", "daily summary unavailable", 0

    count = int(
        _safe_number(
            _first_non_empty(
                summary.get("n_events"),
                summary.get("events"),
                summary.get("event_count"),
            ),
            0,
        )
        or 0
    )
    return str(count), "daily summary latest", count


def _derive_as_of(
    summary: dict[str, Any] | None,
    prediction: dict[str, Any] | None,
    sentiment: dict[str, Any] | None,
    health: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
) -> str:
    # Single source priority:
    # 1) daily_summary
    # 2) prediction
    # 3) sentiment
    # 4) health
    # 5) scenario
    # 6) signal
    # No current-time fallback allowed.

    candidates = [
        _first_non_empty(
            summary.get("as_of") if isinstance(summary, dict) else None,
            summary.get("date") if isinstance(summary, dict) else None,
            summary.get("generated_at") if isinstance(summary, dict) else None,
            summary.get("updated") if isinstance(summary, dict) else None,
        ),
        _first_non_empty(
            prediction.get("as_of") if isinstance(prediction, dict) else None,
            prediction.get("date") if isinstance(prediction, dict) else None,
            prediction.get("generated_at") if isinstance(prediction, dict) else None,
            prediction.get("updated") if isinstance(prediction, dict) else None,
        ),
        _first_non_empty(
            sentiment.get("as_of") if isinstance(sentiment, dict) else None,
            sentiment.get("date") if isinstance(sentiment, dict) else None,
            sentiment.get("generated_at") if isinstance(sentiment, dict) else None,
            sentiment.get("updated") if isinstance(sentiment, dict) else None,
        ),
        _first_non_empty(
            health.get("as_of") if isinstance(health, dict) else None,
            health.get("date") if isinstance(health, dict) else None,
            health.get("generated_at") if isinstance(health, dict) else None,
            health.get("updated") if isinstance(health, dict) else None,
        ),
        _first_non_empty(
            scenario.get("as_of") if isinstance(scenario, dict) else None,
            scenario.get("date") if isinstance(scenario, dict) else None,
            scenario.get("generated_at") if isinstance(scenario, dict) else None,
            scenario.get("updated") if isinstance(scenario, dict) else None,
        ),
        _first_non_empty(
            signal.get("as_of") if isinstance(signal, dict) else None,
            signal.get("date") if isinstance(signal, dict) else None,
            signal.get("generated_at") if isinstance(signal, dict) else None,
            signal.get("updated") if isinstance(signal, dict) else None,
        ),
    ]

    for value in candidates:
        if value:
            return value
    return "--"


def _derive_risk_value(
    prediction: dict[str, Any] | None,
    scenario: dict[str, Any] | None,
    signal: dict[str, Any] | None,
    summary: dict[str, Any] | None,
    sentiment: dict[str, Any] | None,
) -> tuple[str, str]:
    # Preferred explicit source: prediction -> scenario -> signal
    explicit = _normalize_risk_level(
        _first_non_empty(
            prediction.get("overall_risk_level") if isinstance(prediction, dict) else None,
            prediction.get("overall_risk") if isinstance(prediction, dict) else None,
            prediction.get("signal") if isinstance(prediction, dict) else None,
            prediction.get("dominant_branch", {}).get("risk_level") if isinstance(prediction, dict) and isinstance(prediction.get("dominant_branch"), dict) else None,
            scenario.get("overall_risk_level") if isinstance(scenario, dict) else None,
            scenario.get("overall_risk") if isinstance(scenario, dict) else None,
            signal.get("summary", {}).get("overall_signal_bias") if isinstance(signal, dict) and isinstance(signal.get("summary"), dict) else None,
        )
    )

    if explicit:
        confidence = _safe_number(
            _first_non_empty(
                prediction.get("confidence") if isinstance(prediction, dict) else None,
                scenario.get("scenario_confidence") if isinstance(scenario, dict) else None,
            ),
            None,
        )
        if confidence is not None:
            return explicit.upper(), f"analysis explicit / conf {confidence:.2f}"
        return explicit.upper(), "analysis explicit"

    score = _safe_number(
        _first_non_empty(
            prediction.get("overall_risk_score") if isinstance(prediction, dict) else None,
            prediction.get("dominant_branch", {}).get("risk_score") if isinstance(prediction, dict) and isinstance(prediction.get("dominant_branch"), dict) else None,
            scenario.get("overall_risk_score") if isinstance(scenario, dict) else None,
            summary.get("risk_score") if isinstance(summary, dict) else None,
            summary.get("summary_risk_score") if isinstance(summary, dict) else None,
            summary.get("risk", {}).get("score") if isinstance(summary, dict) and isinstance(summary.get("risk"), dict) else None,
            summary.get("summary", {}).get("risk_score") if isinstance(summary, dict) and isinstance(summary.get("summary"), dict) else None,
        ),
        None,
    )
    level = _risk_from_score(score)
    if level:
        return level.upper(), "analysis score-derived"

    counts = _sentiment_counts(sentiment)
    total = counts["items"]
    if total > 0:
        neg_ratio = counts["negative"] / total
        mixed_ratio = counts["mixed"] / total
        if neg_ratio >= 0.5:
            level = "high"
        elif neg_ratio >= 0.3 or mixed_ratio >= 0.5:
            level = "elevated"
        elif neg_ratio > 0.15:
            level = "guarded"
        else:
            level = "low"
        return level.upper(), "sentiment-derived"

    return "--", "risk unavailable"


def build_global_status(root: Path) -> dict[str, Any]:
    prediction_res = _load_first(root, [
        "analysis/prediction/prediction_latest.json",
        "analysis/prediction_latest.json",
    ])
    scenario_res = _load_first(root, [
        "analysis/prediction/scenario_latest.json",
        "analysis/scenario_latest.json",
    ])
    signal_res = _load_first(root, [
        "analysis/prediction/signal_latest.json",
        "analysis/signal_latest.json",
    ])
    summary_res = _load_first(root, [
        "analysis/daily_summary_latest.json",
    ])
    sentiment_res = _load_first(root, [
        "analysis/sentiment_latest.json",
    ])
    health_res = _load_first(root, [
        "analysis/health_latest.json",
    ])
    fx_res = _load_first(root, [
        "analysis/fx_decision_latest.json",
    ])

    prediction = prediction_res.data
    scenario = scenario_res.data
    signal = signal_res.data
    summary = summary_res.data
    sentiment = sentiment_res.data
    health = health_res.data
    fx_decision = fx_res.data

    risk_value, risk_sub = _derive_risk_value(
        prediction=prediction,
        scenario=scenario,
        signal=signal,
        summary=summary,
        sentiment=sentiment,
    )
    sentiment_value, sentiment_sub, sentiment_counts = _derive_sentiment_value(sentiment)
    fx_value, fx_sub = _derive_fx_value(fx_decision)
    articles_value, articles_sub, articles_count = _derive_articles_value(summary)
    health_value, health_sub, health_counts = _derive_health_value(health)
    as_of = _derive_as_of(
        summary=summary,
        prediction=prediction,
        sentiment=sentiment,
        health=health,
        scenario=scenario,
        signal=signal,
    )

    payload: dict[str, Any] = {
        "as_of": as_of,
        "updated": as_of,
        "global_risk": risk_value,
        "global_risk_sub": risk_sub,
        "sentiment_balance": sentiment_value,
        "sentiment_balance_sub": sentiment_sub,
        "fx_regime": fx_value,
        "fx_regime_sub": fx_sub,
        "articles": articles_value,
        "articles_sub": articles_sub,
        "health": health_value,
        "health_sub": health_sub,
        "cards": {
            "events": articles_count,
            "health_ok": health_counts["ok"],
            "health_warn": health_counts["warn"],
            "health_ng": health_counts["ng"],
            "health_total": health_counts["total"],
            "sentiment_items": sentiment_counts["items"],
            "summary_state": "OK" if isinstance(summary, dict) else "--",
        },
        "sentiment_counts": {
            "positive": sentiment_counts["positive"],
            "negative": sentiment_counts["negative"],
            "neutral": sentiment_counts["neutral"],
            "mixed": sentiment_counts["mixed"],
        },
        "events_today": {
            "count": articles_count,
            "status": _first_non_empty(summary.get("status") if isinstance(summary, dict) else None, "ok" if isinstance(summary, dict) else "--"),
            "generated_at": _first_non_empty(
                summary.get("generated_at") if isinstance(summary, dict) else None,
                summary.get("updated") if isinstance(summary, dict) else None,
                "",
            ),
            "date": _first_non_empty(
                summary.get("date") if isinstance(summary, dict) else None,
                summary.get("as_of") if isinstance(summary, dict) else None,
                as_of,
            ),
            "summary": _first_non_empty(
                summary.get("summary") if isinstance(summary, dict) else None,
                summary.get("text") if isinstance(summary, dict) else None,
                "summary unavailable" if not isinstance(summary, dict) else "",
            ),
            "source": summary_res.path or "--",
        },
        "sources": {
            "prediction": prediction_res.path,
            "scenario": scenario_res.path,
            "signal": signal_res.path,
            "summary": summary_res.path,
            "sentiment": sentiment_res.path,
            "health": health_res.path,
            "fxDecision": fx_res.path,
        },
        "artifacts": {
            "prediction": prediction,
            "scenario": scenario,
            "signal": signal,
            "summary": summary,
            "sentiment": sentiment,
            "health_json": health,
            "fx_decision": fx_decision,
        },
    }

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build analysis/global_status_latest.json")
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root path (default: current directory)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Write pretty JSON with indentation",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_path = root / "analysis" / "global_status_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = build_global_status(root)

    json_text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
    )
    out_path.write_text(json_text + ("\n" if args.pretty else ""), encoding="utf-8")

    print(f"[ok] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
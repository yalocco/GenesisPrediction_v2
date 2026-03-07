#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenesisPrediction v2
Prediction Runtime Orchestrator

Purpose:
- Load analysis inputs (Runtime SST)
- Build trend_latest.json
- Build signal_latest.json
- Build scenario_latest.json
- Build prediction_latest.json
- Optionally write history snapshot

Status:
- v1 bootstrap implementation
- Safe, deterministic, file-based orchestrator
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

# Preferred runtime layout
ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"
PREDICTION_HISTORY_DIR = PREDICTION_DIR / "history"

# Legacy / current repo layout fallbacks
DATA_DIR = ROOT / "data"
WP_ANALYSIS_DIR = DATA_DIR / "world_politics" / "analysis"
DIGEST_DATA_DIR = DATA_DIR / "digest"
FX_DATA_DIR = DATA_DIR / "fx"

# Preferred / legacy input candidates
SENTIMENT_CANDIDATES = [
    ANALYSIS_DIR / "world_politics" / "sentiment_latest.json",
    WP_ANALYSIS_DIR / "sentiment_latest.json",
]

DAILY_SUMMARY_CANDIDATES = [
    ANALYSIS_DIR / "world_politics" / "daily_summary_latest.json",
    WP_ANALYSIS_DIR / "daily_summary_latest.json",
]

HEALTH_CANDIDATES = [
    ANALYSIS_DIR / "health_latest.json",
    DIGEST_DATA_DIR / "health_latest.json",
    WP_ANALYSIS_DIR / "health_latest.json",
]

DIGEST_DIR_CANDIDATES = [
    ANALYSIS_DIR / "digest",
    DIGEST_DATA_DIR,
]

FX_DIR_CANDIDATES = [
    ANALYSIS_DIR / "fx",
    FX_DATA_DIR,
]

TREND_LATEST = PREDICTION_DIR / "trend_latest.json"
SIGNAL_LATEST = PREDICTION_DIR / "signal_latest.json"
SCENARIO_LATEST = PREDICTION_DIR / "scenario_latest.json"
PREDICTION_LATEST = PREDICTION_DIR / "prediction_latest.json"


# ============================================================
# Constants
# ============================================================

DEFAULT_HORIZON = "7d"

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

NEGATIVE_WORDS = {
    "war", "conflict", "attack", "escalation", "crisis", "tension", "sanction",
    "strike", "missile", "violence", "threat", "collapse", "risk", "shock"
}


# ============================================================
# Logging
# ============================================================

def log(message: str) -> None:
    print(f"[Prediction] {message}")


def debug_log(enabled: bool, message: str) -> None:
    if enabled:
        log(f"DEBUG: {message}")


# ============================================================
# Utilities
# ============================================================

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp_path.replace(path)


def first_existing(paths: List[Path]) -> Optional[Path]:
    for path in paths:
        if path.exists():
            return path
    return None


def first_existing_dir(paths: List[Path]) -> Optional[Path]:
    for path in paths:
        if path.exists() and path.is_dir():
            return path
    return None


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or isinstance(value, bool):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stddev(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((v - m) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def detect_as_of(
    cli_date: Optional[str],
    daily_summary: Optional[Dict[str, Any]],
    sentiment_root: Optional[Dict[str, Any]],
) -> str:
    if cli_date:
        return cli_date

    candidates = [
        (daily_summary or {}).get("as_of"),
        (daily_summary or {}).get("date"),
        (sentiment_root or {}).get("date"),
        (sentiment_root or {}).get("base_date"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()

    return datetime.now(UTC).strftime("%Y-%m-%d")


def collect_json_files(directory: Path) -> List[Path]:
    if not directory.exists():
        return []
    return sorted(p for p in directory.glob("*.json") if p.is_file())


def find_numeric_values(obj: Any, collected: List[float]) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            find_numeric_values(v, collected)
    elif isinstance(obj, list):
        for v in obj:
            find_numeric_values(v, collected)
    else:
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            collected.append(float(obj))


def extract_summary_text(daily_summary: Dict[str, Any]) -> str:
    candidates = [
        daily_summary.get("summary"),
        daily_summary.get("text_summary"),
        daily_summary.get("daily_summary"),
        daily_summary.get("yesterday_summary_text"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return ""


def classify_health_severity(health: Dict[str, Any]) -> Tuple[str, Dict[str, float]]:
    summary = health.get("summary", {}) if isinstance(health, dict) else {}
    ok_count = safe_float(summary.get("ok"), 0.0)
    warn_count = safe_float(summary.get("warn"), 0.0)
    ng_count = safe_float(summary.get("ng"), 0.0)
    total = safe_float(summary.get("total"), ok_count + warn_count + ng_count)

    warn_ratio = (warn_count / total) if total > 0 else 0.0
    ng_ratio = (ng_count / total) if total > 0 else 0.0

    if ng_ratio >= 0.20:
        severity = "critical"
    elif ng_ratio > 0 or warn_ratio >= 0.30:
        severity = "high"
    elif warn_ratio > 0:
        severity = "medium"
    else:
        severity = "low"

    return severity, {
        "ok": ok_count,
        "warn": warn_count,
        "ng": ng_count,
        "total": total,
        "warn_ratio": round(warn_ratio, 4),
        "ng_ratio": round(ng_ratio, 4),
    }


def count_negative_keywords(text: str) -> int:
    lowered = text.lower()
    return sum(1 for w in NEGATIVE_WORDS if w in lowered)


def parse_sentiment_items(sentiment_root: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(sentiment_root, dict):
        return []

    if isinstance(sentiment_root.get("items"), list):
        return [x for x in sentiment_root["items"] if isinstance(x, dict)]

    if isinstance(sentiment_root.get("articles"), list):
        return [x for x in sentiment_root["articles"] if isinstance(x, dict)]

    if isinstance(sentiment_root.get("data"), list):
        return [x for x in sentiment_root["data"] if isinstance(x, dict)]

    return []


def normalize_sentiment_label(item: Dict[str, Any]) -> str:
    for key in ("sentiment_label", "sentiment", "label"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return "unknown"


def extract_sentiment_counts(
    sentiment_root: Dict[str, Any],
    items: List[Dict[str, Any]],
) -> Dict[str, int]:
    preferred_sources = [
        sentiment_root.get("today"),
        sentiment_root.get("summary"),
    ]
    for src in preferred_sources:
        if isinstance(src, dict):
            counts = {}
            all_present = True
            for key in ("positive", "negative", "neutral", "mixed", "unknown"):
                if key in src:
                    counts[key] = int(safe_float(src.get(key), 0.0))
                else:
                    all_present = False
            if all_present:
                return counts

    counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "unknown": 0}
    for item in items:
        label = normalize_sentiment_label(item)
        counts[label if label in counts else "unknown"] += 1
    return counts


def compute_sentiment_strength(counts: Dict[str, int]) -> Dict[str, float]:
    total = max(1, sum(counts.values()))
    positive = counts.get("positive", 0)
    negative = counts.get("negative", 0)
    neutral = counts.get("neutral", 0)
    mixed = counts.get("mixed", 0)
    unknown = counts.get("unknown", 0)

    negative_ratio = negative / total
    positive_ratio = positive / total
    uncertainty_ratio = (mixed + unknown) / total

    return {
        "total": total,
        "negative_ratio": round(negative_ratio, 4),
        "positive_ratio": round(positive_ratio, 4),
        "neutral_ratio": round(neutral / total, 4),
        "uncertainty_ratio": round(uncertainty_ratio, 4),
        "net_score": round(positive_ratio - negative_ratio, 4),
    }


# ============================================================
# Validation
# ============================================================

@dataclass
class ValidationResult:
    hard_failures: List[str]
    warnings: List[str]
    sentiment_path: Optional[Path]
    daily_summary_path: Optional[Path]
    health_path: Optional[Path]
    digest_dir: Optional[Path]
    fx_dir: Optional[Path]


def validate_inputs(strict: bool = False) -> ValidationResult:
    hard_failures: List[str] = []
    warnings: List[str] = []

    sentiment_path = first_existing(SENTIMENT_CANDIDATES)
    daily_summary_path = first_existing(DAILY_SUMMARY_CANDIDATES)
    health_path = first_existing(HEALTH_CANDIDATES)
    digest_dir = first_existing_dir(DIGEST_DIR_CANDIDATES)
    fx_dir = first_existing_dir(FX_DIR_CANDIDATES)

    if sentiment_path is None:
        hard_failures.append(
            "missing required input: " + " OR ".join(str(p) for p in SENTIMENT_CANDIDATES)
        )

    if daily_summary_path is None:
        hard_failures.append(
            "missing required input: " + " OR ".join(str(p) for p in DAILY_SUMMARY_CANDIDATES)
        )

    if health_path is None:
        msg = "optional input missing: " + " OR ".join(str(p) for p in HEALTH_CANDIDATES)
        if strict:
            hard_failures.append(msg)
        else:
            warnings.append(msg)

    if digest_dir is None:
        warnings.append("optional directory missing: " + " OR ".join(str(p) for p in DIGEST_DIR_CANDIDATES))

    if fx_dir is None:
        warnings.append("optional directory missing: " + " OR ".join(str(p) for p in FX_DIR_CANDIDATES))

    return ValidationResult(
        hard_failures=hard_failures,
        warnings=warnings,
        sentiment_path=sentiment_path,
        daily_summary_path=daily_summary_path,
        health_path=health_path,
        digest_dir=digest_dir,
        fx_dir=fx_dir,
    )


# ============================================================
# Trend Engine
# ============================================================

def build_trend(
    as_of: str,
    sentiment_root: Dict[str, Any],
    daily_summary: Dict[str, Any],
    health_root: Optional[Dict[str, Any]],
    fx_payloads: List[Tuple[str, Dict[str, Any]]],
    horizon: str = DEFAULT_HORIZON,
) -> Dict[str, Any]:
    items = parse_sentiment_items(sentiment_root)
    counts = extract_sentiment_counts(sentiment_root, items)
    sentiment_strength = compute_sentiment_strength(counts)

    summary_text = extract_summary_text(daily_summary)
    negative_keyword_hits = count_negative_keywords(summary_text)

    negative_ratio = sentiment_strength["negative_ratio"]
    positive_ratio = sentiment_strength["positive_ratio"]
    uncertainty_ratio = sentiment_strength["uncertainty_ratio"]
    net_score = sentiment_strength["net_score"]

    world_entries: List[Dict[str, Any]] = []
    sentiment_entries: List[Dict[str, Any]] = []
    fx_entries: List[Dict[str, Any]] = []
    health_entries: List[Dict[str, Any]] = []
    risk_entries: List[Dict[str, Any]] = []

    sentiment_entries.append({
        "metric": "negative_sentiment",
        "direction": "increase" if negative_ratio >= 0.35 else "stable",
        "score": round(clamp((negative_ratio - 0.20) / 0.50, -1.0, 1.0), 4),
        "duration": 1,
        "slope": round(negative_ratio, 4),
        "momentum": round(abs(net_score), 4),
        "summary": (
            "negative sentiment elevated"
            if negative_ratio >= 0.35
            else "negative sentiment not elevated"
        ),
    })

    sentiment_entries.append({
        "metric": "positive_sentiment",
        "direction": "increase" if positive_ratio >= 0.35 else "stable",
        "score": round(clamp((positive_ratio - 0.20) / 0.50, -1.0, 1.0), 4),
        "duration": 1,
        "slope": round(positive_ratio, 4),
        "momentum": round(abs(net_score), 4),
        "summary": (
            "positive sentiment elevated"
            if positive_ratio >= 0.35
            else "positive sentiment not elevated"
        ),
    })

    sentiment_entries.append({
        "metric": "uncertainty",
        "direction": "increase" if uncertainty_ratio >= 0.40 else "stable",
        "score": round(clamp((uncertainty_ratio - 0.25) / 0.50, -1.0, 1.0), 4),
        "duration": 1,
        "slope": round(uncertainty_ratio, 4),
        "momentum": round(uncertainty_ratio, 4),
        "summary": (
            "uncertainty elevated"
            if uncertainty_ratio >= 0.40
            else "uncertainty not elevated"
        ),
    })

    world_entries.append({
        "metric": "headline_risk_pressure",
        "direction": "increase" if negative_keyword_hits >= 2 else "stable",
        "score": round(clamp(negative_keyword_hits / 6.0, 0.0, 1.0), 4),
        "duration": 1,
        "slope": round(min(1.0, negative_keyword_hits / 5.0), 4),
        "momentum": round(min(1.0, max(negative_ratio, uncertainty_ratio)), 4),
        "summary": (
            f"risk-related headline pressure detected ({negative_keyword_hits} keyword hits)"
            if negative_keyword_hits > 0
            else "no strong risk headline pressure detected"
        ),
    })

    risk_score = safe_float(daily_summary.get("risk_score"), 0.0)
    if risk_score == 0.0:
        numeric_values: List[float] = []
        find_numeric_values(daily_summary, numeric_values)
        risk_score = max(numeric_values) if numeric_values else 0.0

    risk_entries.append({
        "metric": "summary_risk_score",
        "direction": "increase" if risk_score >= 0.60 else "stable",
        "score": round(clamp(risk_score, 0.0, 1.0), 4),
        "duration": 1,
        "slope": round(clamp(risk_score, 0.0, 1.0), 4),
        "momentum": round(clamp(max(negative_ratio, uncertainty_ratio), 0.0, 1.0), 4),
        "summary": (
            "summary risk score elevated"
            if risk_score >= 0.60
            else "summary risk score not elevated"
        ),
    })

    if health_root is not None:
        severity, stats = classify_health_severity(health_root)
        health_entries.append({
            "metric": "pipeline_health",
            "direction": "deteriorating" if severity in {"medium", "high", "critical"} else "stable",
            "score": round(clamp(stats["warn_ratio"] + stats["ng_ratio"] * 2.0, 0.0, 1.0), 4),
            "duration": 1,
            "slope": round(stats["warn_ratio"] + stats["ng_ratio"], 4),
            "momentum": round(stats["ng_ratio"], 4),
            "summary": f"pipeline health severity: {severity}",
        })

    for fx_name, fx_payload in fx_payloads:
        numeric_values: List[float] = []
        find_numeric_values(fx_payload, numeric_values)
        if not numeric_values:
            continue

        fx_mean = mean(numeric_values)
        fx_sd = stddev(numeric_values)
        volatility_score = 0.0
        if abs(fx_mean) > 1e-9:
            volatility_score = abs(fx_sd / fx_mean)
        volatility_score = clamp(volatility_score, 0.0, 1.0)

        fx_entries.append({
            "metric": fx_name,
            "direction": "increase" if volatility_score >= 0.15 else "stable",
            "score": round(volatility_score, 4),
            "duration": 1,
            "slope": round(volatility_score, 4),
            "momentum": round(min(1.0, volatility_score * 1.25), 4),
            "summary": (
                f"{fx_name} volatility expanding"
                if volatility_score >= 0.15
                else f"{fx_name} volatility stable"
            ),
        })

    return {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "window": horizon,
        "domains": {
            "world_politics": world_entries,
            "sentiment": sentiment_entries,
            "fx": fx_entries,
            "health": health_entries,
            "risk": risk_entries,
        },
        "meta": {
            "bootstrap_mode": True,
            "note": "Single-run heuristic trend build. History-aware trend logic can replace this later.",
        },
    }


# ============================================================
# Signal Engine
# ============================================================

def severity_from_score(score: float) -> str:
    if score >= 0.80:
        return "critical"
    if score >= 0.60:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def build_signal(as_of: str, trend_payload: Dict[str, Any]) -> Dict[str, Any]:
    signals: List[Dict[str, Any]] = []

    domains = trend_payload.get("domains", {})
    if not isinstance(domains, dict):
        domains = {}

    signal_idx = 1
    for domain, entries in domains.items():
        if not isinstance(entries, list):
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            metric = str(entry.get("metric", "unknown"))
            direction = str(entry.get("direction", "stable"))
            score = safe_float(entry.get("score"), 0.0)
            duration = int(safe_float(entry.get("duration"), 0))
            momentum = safe_float(entry.get("momentum"), 0.0)

            signal_type = None

            if direction in {"increase", "deteriorating"} and score >= 0.35:
                signal_type = "persistence" if duration >= 1 else "acceleration"
            elif direction == "stable" and score >= 0.60:
                signal_type = "anomaly"
            elif momentum >= 0.45:
                signal_type = "acceleration"

            if score >= 0.15 and "volatility" in metric.lower():
                signal_type = "volatility_expansion"

            if signal_type is None:
                continue

            severity = severity_from_score(score)
            confidence = clamp(0.50 + score * 0.40 + min(0.10, momentum * 0.10), 0.0, 1.0)

            signals.append({
                "id": f"SIG-{domain[:3].upper()}-{signal_idx:03d}",
                "type": signal_type,
                "domain": domain,
                "severity": severity,
                "confidence": round(confidence, 4),
                "source_trend": metric,
                "duration": duration,
                "summary": entry.get("summary", f"{metric} generated a {signal_type} signal"),
            })
            signal_idx += 1

    return {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "signals": signals,
        "meta": {
            "bootstrap_mode": True,
            "signal_count": len(signals),
        },
    }


# ============================================================
# Scenario Engine
# ============================================================

def build_scenario(as_of: str, signal_payload: Dict[str, Any], horizon: str = DEFAULT_HORIZON) -> Dict[str, Any]:
    raw_signals = signal_payload.get("signals", [])
    signals = [s for s in raw_signals if isinstance(s, dict)]

    if not signals:
        scenarios = [
            {
                "name": "best_case",
                "probability": 0.30,
                "confidence": 0.45,
                "drivers": [],
                "invalidation_conditions": ["new adverse signals emerge"],
                "implications": ["risk pressure remains limited"],
                "watchpoints": ["emerging negative signals"],
                "summary": "Risk remains limited if no stronger adverse signals emerge.",
            },
            {
                "name": "base_case",
                "probability": 0.55,
                "confidence": 0.50,
                "drivers": [],
                "invalidation_conditions": ["multiple high-severity signals appear"],
                "implications": ["monitor for new deterioration"],
                "watchpoints": ["signal count", "signal severity"],
                "summary": "The system remains in a neutral monitoring state.",
            },
            {
                "name": "worst_case",
                "probability": 0.15,
                "confidence": 0.40,
                "drivers": [],
                "invalidation_conditions": ["signal set stays quiet"],
                "implications": ["stress could rise if adverse signals appear"],
                "watchpoints": ["adverse signal emergence"],
                "summary": "A worsening path remains possible but not dominant.",
            },
        ]
    else:
        total_weight = 0.0
        high_weight = 0.0
        critical_weight = 0.0
        low_positive_offset = 0.0
        drivers: List[str] = []
        watchpoints: List[str] = []
        domain_set = set()

        for s in signals:
            severity = str(s.get("severity", "low"))
            confidence = safe_float(s.get("confidence"), 0.5)
            weight = SEVERITY_ORDER.get(severity, 1) * confidence
            total_weight += weight
            domain_set.add(str(s.get("domain", "unknown")))

            summary = str(s.get("summary", "")).strip()
            if summary:
                drivers.append(summary)

            stype = str(s.get("type", ""))
            source_trend = str(s.get("source_trend", ""))
            if source_trend:
                watchpoints.append(source_trend)

            if severity == "high":
                high_weight += weight
            elif severity == "critical":
                critical_weight += weight
            elif severity == "low":
                low_positive_offset += 0.20 * confidence

            if stype == "volatility_expansion":
                watchpoints.append("volatility breakout")
            if stype == "anomaly":
                watchpoints.append("anomaly persistence")

        multi_domain_bonus = min(0.10, max(0, len(domain_set) - 1) * 0.03)

        worst_prob = clamp(0.12 + 0.06 * high_weight + 0.08 * critical_weight + multi_domain_bonus, 0.10, 0.70)
        best_prob = clamp(0.18 + low_positive_offset - 0.04 * high_weight - 0.06 * critical_weight, 0.05, 0.45)
        base_prob = clamp(1.0 - worst_prob - best_prob, 0.20, 0.80)

        total = best_prob + base_prob + worst_prob
        best_prob /= total
        base_prob /= total
        worst_prob /= total

        common_conf = clamp(0.45 + min(0.30, total_weight * 0.05) + multi_domain_bonus, 0.0, 0.95)

        scenarios = [
            {
                "name": "best_case",
                "probability": round(best_prob, 4),
                "confidence": round(clamp(common_conf - 0.06, 0.0, 1.0), 4),
                "drivers": drivers[:2],
                "invalidation_conditions": ["adverse signals intensify", "headline risk increases"],
                "implications": ["risk pressure softens", "conditions stabilize"],
                "watchpoints": sorted(set(watchpoints))[:4],
                "summary": "Risk pressure softens and conditions stabilize if adverse signals fade.",
            },
            {
                "name": "base_case",
                "probability": round(base_prob, 4),
                "confidence": round(common_conf, 4),
                "drivers": drivers[:3],
                "invalidation_conditions": ["clear improvement signals dominate", "major escalation breaks out"],
                "implications": ["elevated conditions persist", "caution remains warranted"],
                "watchpoints": sorted(set(watchpoints))[:5],
                "summary": "Elevated conditions persist without a confirmed major break in regime.",
            },
            {
                "name": "worst_case",
                "probability": round(worst_prob, 4),
                "confidence": round(clamp(common_conf - 0.02 + min(0.08, critical_weight * 0.05), 0.0, 1.0), 4),
                "drivers": drivers[:4],
                "invalidation_conditions": ["adverse signals fade", "volatility compresses"],
                "implications": ["market stress risk rises", "defensive posture becomes more important"],
                "watchpoints": sorted(set(watchpoints))[:6],
                "summary": "A stronger adverse escalation path drives broader instability and stress.",
            },
        ]

    return {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "horizon": horizon,
        "scenarios": scenarios,
        "meta": {
            "bootstrap_mode": True,
            "signal_count": len(signals),
        },
    }


# ============================================================
# Prediction Engine
# ============================================================

def risk_from_worst_prob(worst_prob: float, base_prob: float, signal_count: int) -> str:
    if worst_prob >= 0.45:
        return "critical"
    if worst_prob >= 0.30:
        return "high"
    if worst_prob >= 0.18 or (base_prob >= 0.50 and signal_count >= 2):
        return "elevated"
    if worst_prob >= 0.10:
        return "guarded"
    return "low"


def build_prediction(as_of: str, scenario_payload: Dict[str, Any], horizon: str = DEFAULT_HORIZON) -> Dict[str, Any]:
    raw_scenarios = scenario_payload.get("scenarios", [])
    scenarios = [s for s in raw_scenarios if isinstance(s, dict)]

    if not scenarios:
        raise ValueError("scenario payload has no valid scenarios")

    by_name = {str(s.get("name")): s for s in scenarios}
    best = by_name.get("best_case", {})
    base = by_name.get("base_case", {})
    worst = by_name.get("worst_case", {})

    best_prob = safe_float(best.get("probability"), 0.0)
    base_prob = safe_float(base.get("probability"), 0.0)
    worst_prob = safe_float(worst.get("probability"), 0.0)

    dominant = max(
        [("best_case", best_prob), ("base_case", base_prob), ("worst_case", worst_prob)],
        key=lambda x: x[1],
    )[0]

    scenario_confidences = [
        safe_float(best.get("confidence"), 0.0),
        safe_float(base.get("confidence"), 0.0),
        safe_float(worst.get("confidence"), 0.0),
    ]
    confidence = round(clamp(mean(scenario_confidences), 0.0, 1.0), 4)

    signal_count = int(safe_float(scenario_payload.get("meta", {}).get("signal_count"), 0))
    overall_risk = risk_from_worst_prob(worst_prob, base_prob, signal_count)

    dominant_summary = str(by_name.get(dominant, {}).get("summary", "")).strip()
    if not dominant_summary:
        dominant_summary = "The outlook remains under review."

    summary = (
        f"Risk is {overall_risk} over the next {horizon} as "
        f"{dominant_summary[0].lower() + dominant_summary[1:] if dominant_summary else 'conditions remain under review.'}"
    )

    drivers = []
    watchpoints = []
    invalidation_conditions = []
    key_implications = []

    for key in (dominant, "worst_case", "base_case"):
        scenario = by_name.get(key, {})
        for v in scenario.get("drivers", []):
            if isinstance(v, str) and v.strip():
                drivers.append(v.strip())
        for v in scenario.get("watchpoints", []):
            if isinstance(v, str) and v.strip():
                watchpoints.append(v.strip())
        for v in scenario.get("invalidation_conditions", []):
            if isinstance(v, str) and v.strip():
                invalidation_conditions.append(v.strip())
        for v in scenario.get("implications", []):
            if isinstance(v, str) and v.strip():
                key_implications.append(v.strip())

    return {
        "as_of": as_of,
        "generated_at": utc_now_iso(),
        "horizon": horizon,
        "overall_risk": overall_risk,
        "confidence": confidence,
        "dominant_scenario": dominant,
        "scenario_probabilities": {
            "best_case": round(best_prob, 4),
            "base_case": round(base_prob, 4),
            "worst_case": round(worst_prob, 4),
        },
        "summary": summary,
        "key_implications": list(dict.fromkeys(key_implications))[:3],
        "watchpoints": list(dict.fromkeys(watchpoints))[:5],
        "drivers": list(dict.fromkeys(drivers))[:4],
        "invalidation_conditions": list(dict.fromkeys(invalidation_conditions))[:4],
        "meta": {
            "bootstrap_mode": True,
            "signal_count": signal_count,
        },
    }


# ============================================================
# History
# ============================================================

def write_history_snapshot(
    as_of: str,
    trend_payload: Dict[str, Any],
    signal_payload: Dict[str, Any],
    scenario_payload: Dict[str, Any],
    prediction_payload: Dict[str, Any],
) -> None:
    date_dir = PREDICTION_HISTORY_DIR / as_of
    ensure_dir(date_dir)
    write_json(date_dir / "trend.json", trend_payload)
    write_json(date_dir / "signal.json", signal_payload)
    write_json(date_dir / "scenario.json", scenario_payload)
    write_json(date_dir / "prediction.json", prediction_payload)


# ============================================================
# FX Input Loading
# ============================================================

def load_fx_payloads(fx_dir: Optional[Path], debug: bool = False) -> List[Tuple[str, Dict[str, Any]]]:
    payloads: List[Tuple[str, Dict[str, Any]]] = []
    if fx_dir is None or not fx_dir.exists():
        return payloads

    for path in collect_json_files(fx_dir):
        try:
            payload = load_json(path)
            if isinstance(payload, dict):
                payloads.append((path.stem, payload))
                debug_log(debug, f"Loaded FX JSON: {path}")
        except Exception as exc:
            debug_log(debug, f"Skipped FX JSON {path}: {exc}")
            continue
    return payloads


# ============================================================
# Validation of Outputs
# ============================================================

def validate_trend_output(payload: Dict[str, Any]) -> None:
    domains = payload.get("domains")
    if not isinstance(domains, dict):
        raise ValueError("trend_latest.json missing domains")
    if not any(isinstance(v, list) and v for v in domains.values()):
        raise ValueError("trend_latest.json has no trend entries")


def validate_signal_output(payload: Dict[str, Any]) -> None:
    signals = payload.get("signals")
    if not isinstance(signals, list):
        raise ValueError("signal_latest.json missing signals array")


def validate_scenario_output(payload: Dict[str, Any]) -> None:
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenario_latest.json missing scenarios")
    names = {str(s.get("name")) for s in scenarios if isinstance(s, dict)}
    if not {"best_case", "base_case", "worst_case"}.intersection(names):
        raise ValueError("scenario_latest.json missing best/base/worst cases")


def validate_prediction_output(payload: Dict[str, Any]) -> None:
    if not payload.get("overall_risk"):
        raise ValueError("prediction_latest.json missing overall_risk")
    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("prediction_latest.json missing summary")
    if not isinstance(payload.get("watchpoints"), list):
        raise ValueError("prediction_latest.json watchpoints must be a list")
    if not payload.get("dominant_scenario"):
        raise ValueError("prediction_latest.json missing dominant_scenario")


# ============================================================
# Main
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GenesisPrediction prediction pipeline.")
    parser.add_argument("--date", dest="date", default=None, help="Target date (YYYY-MM-DD)")
    parser.add_argument("--write-history", action="store_true", help="Write history snapshot")
    parser.add_argument("--strict", action="store_true", help="Treat optional input issues as failures")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    log("START")

    validation = validate_inputs(strict=args.strict)
    for warning in validation.warnings:
        log(f"WARN: {warning}")

    if validation.hard_failures:
        for failure in validation.hard_failures:
            log(f"ERROR: {failure}")
        log("STOP (input validation failed)")
        return 2

    try:
        assert validation.sentiment_path is not None
        assert validation.daily_summary_path is not None

        debug_log(args.debug, f"sentiment input: {validation.sentiment_path}")
        debug_log(args.debug, f"daily summary input: {validation.daily_summary_path}")
        if validation.health_path:
            debug_log(args.debug, f"health input: {validation.health_path}")
        if validation.fx_dir:
            debug_log(args.debug, f"fx dir: {validation.fx_dir}")

        log("Load required inputs")
        sentiment_root = load_json(validation.sentiment_path)
        daily_summary = load_json(validation.daily_summary_path)
        health_root = load_json(validation.health_path) if validation.health_path else None
        fx_payloads = load_fx_payloads(validation.fx_dir, debug=args.debug)

        if not isinstance(sentiment_root, dict):
            raise ValueError("sentiment_latest.json root must be an object")
        if not isinstance(daily_summary, dict):
            raise ValueError("daily_summary_latest.json root must be an object")
        if health_root is not None and not isinstance(health_root, dict):
            raise ValueError("health_latest.json root must be an object if present")

        as_of = detect_as_of(args.date, daily_summary, sentiment_root)
        debug_log(args.debug, f"Using as_of={as_of}")

        log("Build trend")
        trend_payload = build_trend(
            as_of=as_of,
            sentiment_root=sentiment_root,
            daily_summary=daily_summary,
            health_root=health_root,
            fx_payloads=fx_payloads,
            horizon=DEFAULT_HORIZON,
        )
        validate_trend_output(trend_payload)

        log("Build signal")
        signal_payload = build_signal(as_of=as_of, trend_payload=trend_payload)
        validate_signal_output(signal_payload)

        log("Build scenario")
        scenario_payload = build_scenario(as_of=as_of, signal_payload=signal_payload, horizon=DEFAULT_HORIZON)
        validate_scenario_output(scenario_payload)

        log("Build prediction")
        prediction_payload = build_prediction(as_of=as_of, scenario_payload=scenario_payload, horizon=DEFAULT_HORIZON)
        validate_prediction_output(prediction_payload)

        log("Write outputs")
        write_json(TREND_LATEST, trend_payload)
        write_json(SIGNAL_LATEST, signal_payload)
        write_json(SCENARIO_LATEST, scenario_payload)
        write_json(PREDICTION_LATEST, prediction_payload)

        if args.write_history:
            log("Write history snapshot")
            write_history_snapshot(
                as_of=as_of,
                trend_payload=trend_payload,
                signal_payload=signal_payload,
                scenario_payload=scenario_payload,
                prediction_payload=prediction_payload,
            )

        log("DONE")
        return 0

    except Exception as exc:
        log(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

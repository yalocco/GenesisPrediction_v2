#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]

ANALYSIS_DIR = ROOT / "analysis"
DATA_DIR = ROOT / "data"

PREDICTION_LATEST_PATH = ANALYSIS_DIR / "prediction" / "prediction_latest.json"

ANALYSIS_FX_DIR = ANALYSIS_DIR / "fx"
DATA_FX_DIR = DATA_DIR / "fx"

COMMON_RATE_CANDIDATES = [
    ANALYSIS_FX_DIR / "fx_rates_latest.json",
    ANALYSIS_FX_DIR / "fx_dashboard_latest.json",
    ANALYSIS_FX_DIR / "fx_inputs_latest.json",
    ANALYSIS_FX_DIR / "latest_rates.json",
    DATA_FX_DIR / "fx_rates_latest.json",
    DATA_FX_DIR / "fx_dashboard_latest.json",
    DATA_FX_DIR / "fx_inputs_latest.json",
    DATA_FX_DIR / "latest_rates.json",
]

PAIR_CONFIGS: Dict[str, Dict[str, Any]] = {
    "JPYTHB": {
        "aliases": ["JPYTHB", "JPY_THB", "JPY-THB", "THBJPY", "THB_JPY"],
        "objective": "JPY to THB remittance timing",
        "preferred_direction": "higher",
        "pair_type": "remittance",
        "quote_note": "Higher JPYTHB is generally better for JPY→THB remittance execution.",
    },
    "USDJPY": {
        "aliases": ["USDJPY", "USD_JPY", "USD-JPY"],
        "objective": "USD vs JPY strength monitoring",
        "preferred_direction": "higher",
        "pair_type": "macro_fx",
        "quote_note": "Higher USDJPY indicates relative USD strength vs JPY.",
    },
    "USDTHB": {
        "aliases": ["USDTHB", "USD_THB", "USD-THB"],
        "objective": "USD vs THB strength monitoring",
        "preferred_direction": "higher",
        "pair_type": "macro_fx",
        "quote_note": "Higher USDTHB indicates relative USD strength vs THB.",
    },
}
ORDERED_PAIRS = ["JPYTHB", "USDJPY", "USDTHB"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def titleize(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace("_", " ").replace("-", " ").title()


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def clamp01(value: float) -> float:
    return clamp(value, 0.0, 1.0)


def first_non_empty(*values: Any) -> Optional[Any]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list) and len(value) > 0:
            return value
        if value not in (None, "", [], {}):
            return value
    return None


def normalize_list_items(value: Any) -> List[str]:
    items: List[str] = []
    if not isinstance(value, list):
        return items

    for item in value:
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
            if isinstance(text, str) and text.strip():
                items.append(text.strip())

    seen = set()
    out: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def detect_rate_source_path(explicit_path: Optional[str]) -> Optional[Path]:
    if explicit_path:
        path = Path(explicit_path)
        if not path.is_absolute():
            path = (ROOT / path).resolve()
        return path if path.exists() else None

    for path in COMMON_RATE_CANDIDATES:
        if path.exists():
            return path
    return None


def find_key_case_insensitive(container: Dict[str, Any], target: str) -> Optional[str]:
    target_norm = normalize_text(target)
    for key in container.keys():
        if normalize_text(key) == target_norm:
            return key
    return None


def alias_variants(pair: str) -> List[str]:
    config = PAIR_CONFIGS.get(pair, {})
    aliases = list(config.get("aliases", []))
    if pair not in aliases:
        aliases.insert(0, pair)
    return aliases


def maybe_extract_numeric_fields(obj: Dict[str, Any]) -> Dict[str, Optional[float]]:
    return {
        "rate": safe_float(first_non_empty(obj.get("rate"), obj.get("latest"), obj.get("last"), obj.get("value"), obj.get("close"))),
        "change_pct": safe_float(first_non_empty(obj.get("change_pct"), obj.get("daily_change_pct"), obj.get("pct_change"), obj.get("changePercent"), obj.get("change_percent"))),
        "ma7": safe_float(first_non_empty(obj.get("ma7"), obj.get("sma7"), obj.get("avg7"), obj.get("average_7d"), obj.get("moving_avg_7d"))),
        "ma30": safe_float(first_non_empty(obj.get("ma30"), obj.get("sma30"), obj.get("avg30"), obj.get("average_30d"), obj.get("moving_avg_30d"))),
        "zscore": safe_float(first_non_empty(obj.get("zscore"), obj.get("z_score"))),
        "volatility": safe_float(first_non_empty(obj.get("volatility"), obj.get("vol"), obj.get("atr_pct"))),
    }


def extract_pair_object(rate_data: Dict[str, Any], pair: str) -> Dict[str, Any]:
    aliases = alias_variants(pair)

    containers: List[Any] = [rate_data]
    for key in ("pairs", "rates", "fx", "series", "dashboard", "today", "latest"):
        value = rate_data.get(key)
        if isinstance(value, dict):
            containers.append(value)

    for container in containers:
        if not isinstance(container, dict):
            continue
        for alias in aliases:
            hit = find_key_case_insensitive(container, alias)
            if not hit:
                continue
            value = container.get(hit)
            if isinstance(value, dict):
                return value
            if isinstance(value, (int, float, str)):
                return {"rate": value}

    return {}


def extract_pair_snapshot(rate_data: Dict[str, Any], pair: str) -> Dict[str, Any]:
    obj = extract_pair_object(rate_data, pair)
    fields = maybe_extract_numeric_fields(obj)

    if fields["rate"] is None:
        aliases = alias_variants(pair)
        flat_candidates = {}
        for alias in aliases:
            alias_low = normalize_text(alias)
            flat_candidates[alias_low] = safe_float(rate_data.get(alias))
            flat_candidates[f"{alias_low}_rate"] = safe_float(rate_data.get(f"{alias}_rate"))
            flat_candidates[f"{alias_low}_latest"] = safe_float(rate_data.get(f"{alias}_latest"))
            flat_candidates[f"{alias_low}_change_pct"] = safe_float(rate_data.get(f"{alias}_change_pct"))
            flat_candidates[f"{alias_low}_ma7"] = safe_float(rate_data.get(f"{alias}_ma7"))
            flat_candidates[f"{alias_low}_ma30"] = safe_float(rate_data.get(f"{alias}_ma30"))
            flat_candidates[f"{alias_low}_volatility"] = safe_float(rate_data.get(f"{alias}_volatility"))

        for key, value in flat_candidates.items():
            if value is None:
                continue
            if key.endswith("_change_pct"):
                fields["change_pct"] = value
            elif key.endswith("_ma7"):
                fields["ma7"] = value
            elif key.endswith("_ma30"):
                fields["ma30"] = value
            elif key.endswith("_volatility"):
                fields["volatility"] = value
            elif fields["rate"] is None:
                fields["rate"] = value

    snapshot = {
        "pair": pair,
        "as_of": first_non_empty(
            obj.get("as_of"),
            obj.get("date"),
            obj.get("timestamp"),
            rate_data.get("as_of"),
            rate_data.get("date"),
            rate_data.get("generated_at"),
        ) or "",
        "rate": fields["rate"],
        "change_pct": fields["change_pct"],
        "ma7": fields["ma7"],
        "ma30": fields["ma30"],
        "zscore": fields["zscore"],
        "volatility": fields["volatility"],
        "source_path": "",
    }
    return snapshot


def risk_rank(risk: str) -> int:
    value = normalize_text(risk)
    if "critical" in value:
        return 5
    if "high" in value:
        return 4
    if "elevated" in value or "warn" in value:
        return 3
    if "guard" in value:
        return 2
    if "stable" in value or "low" in value:
        return 1
    return 0


def scenario_bias_score(dominant_scenario: str) -> float:
    value = normalize_text(dominant_scenario)
    if "best" in value or "stabil" in value:
        return 0.18
    if "worst" in value or "shock" in value or "escalat" in value:
        return -0.22
    return 0.0


def action_bias_score(action_bias: str) -> float:
    value = normalize_text(action_bias)
    if not value:
        return 0.0
    score = 0.0
    if any(token in value for token in ("execute", "opportun", "favorable", "add", "buy")):
        score += 0.16
    if any(token in value for token in ("wait", "monitor", "neutral")):
        score += 0.0
    if any(token in value for token in ("defensive", "reduce", "avoid", "hold", "hedge")):
        score -= 0.18
    return score


def prediction_regime_score(prediction: Dict[str, Any]) -> Tuple[float, List[str]]:
    reasons: List[str] = []

    confidence = safe_float(prediction.get("confidence"), 0.5) or 0.5
    confidence = clamp01(confidence)

    risk = str(first_non_empty(prediction.get("risk"), "guarded"))
    dominant = str(first_non_empty(prediction.get("dominant_scenario"), "base_case"))
    action_bias = str(first_non_empty(prediction.get("action_bias"), ""))

    score = 0.0

    rr = risk_rank(risk)
    if rr >= 4:
        score -= 0.35
        reasons.append(f"prediction risk is {risk}")
    elif rr == 3:
        score -= 0.18
        reasons.append(f"prediction risk is {risk}")
    elif rr == 2:
        score -= 0.06
        reasons.append(f"prediction risk is {risk}")
    else:
        score += 0.08
        reasons.append(f"prediction risk is {risk
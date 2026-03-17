#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GenesisPrediction v2
build_fx_inputs_latest.py

Purpose
-------
Build analysis/fx/fx_inputs_latest.json as the stable input artifact
for scripts/fx_decision_engine.py.

Design Principles
-----------------
- analysis/ is the Single Source of Truth
- scripts/ generate artifacts
- UI reads artifacts only
- v1 stays deterministic, rule-based, and explainable

This version:
- auto-discovers FX source files under analysis/fx and data/fx
- supports JSON and CSV
- supports dashboard-style CSV files
- normalizes inverse pairs automatically
  * JPYUSD -> USDJPY
  * THBUSD -> USDTHB
  * THBJPY -> JPYTHB
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from statistics import pstdev
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_OUTPUT_PATH = Path("analysis/fx/fx_inputs_latest.json")
SEARCH_ROOTS = [Path("analysis/fx"), Path("data/fx")]
PAIRS = ("JPYTHB", "USDJPY", "USDTHB")

PAIR_ROLE = {
    "JPYTHB": "primary_remittance_pair",
    "USDJPY": "risk_proxy_pair",
    "USDTHB": "thb_side_crosscheck",
}

PAIR_NOTES = {
    "JPYTHB": [
        "Primary operational pair for JPY to THB remittance.",
        "Higher JPYTHB is generally better for sending JPY into THB.",
    ],
    "USDJPY": [
        "Supporting pair used as macro and JPY risk proxy.",
        "Not the direct remittance execution pair.",
    ],
    "USDTHB": [
        "Supporting pair used to cross-check THB side conditions.",
        "Used together with JPYTHB and USDJPY for multi-pair interpretation.",
    ],
}

DIRECT_PAIR_TOKENS = {
    "JPYTHB": ["JPYTHB", "JPY_THB", "JPY-THB"],
    "USDJPY": ["USDJPY", "USD_JPY", "USD-JPY"],
    "USDTHB": ["USDTHB", "USD_THB", "USD-THB"],
}

INVERSE_PAIR_TOKENS = {
    "JPYTHB": ["THBJPY", "THB_JPY", "THB-JPY"],
    "USDJPY": ["JPYUSD", "JPY_USD", "JPY-USD"],
    "USDTHB": ["THBUSD", "THB_USD", "THB-USD"],
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        text = str(value).strip().replace(",", "")
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def normalize_token(text: str) -> str:
    return (
        str(text)
        .upper()
        .replace("-", "")
        .replace("_", "")
        .replace("/", "")
        .replace(" ", "")
    )


def path_pair_matches(path: Path, pair: str) -> bool:
    stem = path.stem.upper()
    normalized_stem = normalize_token(path.stem)

    for token in DIRECT_PAIR_TOKENS[pair] + INVERSE_PAIR_TOKENS[pair]:
        if token in stem or normalize_token(token) in normalized_stem:
            return True
    return False


def infer_pair_orientation_from_path(path: Path, pair: str) -> str:
    stem = path.stem.upper()
    normalized_stem = normalize_token(path.stem)

    for token in INVERSE_PAIR_TOKENS[pair]:
        if token in stem or normalize_token(token) in normalized_stem:
            return "inverse"

    for token in DIRECT_PAIR_TOKENS[pair]:
        if token in stem or normalize_token(token) in normalized_stem:
            return "direct"

    return "unknown"


def is_candidate_extension(path: Path) -> bool:
    return path.suffix.lower() in {".json", ".csv"}


def is_obvious_non_source(path: Path) -> bool:
    name = path.name.lower()
    blocked_keywords = [
        "overlay",
        "decision",
        "inputs_latest",
        "fx_inputs_latest",
        "related_news",
        "multi_overlay",
        "publish",
        "deploy",
        "health",
        "view_model",
        "prediction",
        "signal",
        "scenario",
        "sentiment",
    ]
    return any(keyword in name for keyword in blocked_keywords)


def discover_candidate_files(pair: str) -> List[Path]:
    candidates: List[Path] = []

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if not is_candidate_extension(path):
                continue
            if is_obvious_non_source(path):
                continue
            if not path_pair_matches(path, pair):
                continue
            candidates.append(path)

    def score(path: Path) -> Tuple[int, int, int, str]:
        name = path.name.lower()
        parent = str(path.parent).replace("\\", "/").lower()
        score_value = 0

        if parent.startswith("analysis/fx"):
            score_value += 30
        elif "/analysis/fx/" in parent:
            score_value += 25
        elif parent.startswith("data/fx"):
            score_value += 20

        if "rates" in name or "rate" in name:
            score_value += 20
        if "history" in name or "timeseries" in name or "series" in name:
            score_value += 15
        if "dashboard" in name:
            score_value += 12
        if "remittance" in name:
            score_value += 10
        if "latest" in name:
            score_value += 5

        if "miss_days" in name:
            score_value -= 25

        if path.suffix.lower() == ".json":
            score_value += 5

        return (-score_value, len(str(path)), 0, str(path))

    candidates.sort(key=score)
    return candidates


def read_json_series(path: Path) -> List[Dict[str, Any]]:
    raw = load_json(path)

    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]

    if isinstance(raw, dict):
        for key in ("series", "rates", "items", "history", "data", "rows"):
            value = raw.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]

        if {"date", "rate"} <= set(raw.keys()):
            return [raw]

        if "rates" in raw and isinstance(raw["rates"], dict):
            rows: List[Dict[str, Any]] = []
            for date_key, value in raw["rates"].items():
                if isinstance(value, (int, float, str)):
                    rows.append({"date": date_key, "rate": value})
                elif isinstance(value, dict):
                    rate_candidate = (
                        value.get("rate")
                        or value.get("close")
                        or value.get("value")
                        or value.get("mid")
                        or value.get("price")
                    )
                    rows.append({"date": date_key, "rate": rate_candidate})
            return rows

    return []


def detect_date_column(fieldnames: List[str]) -> Optional[str]:
    if not fieldnames:
        return None

    preferred = [
        "date",
        "as_of",
        "day",
        "datetime",
        "timestamp",
        "Date",
        "DATE",
    ]
    lower_map = {name.lower(): name for name in fieldnames}

    for key in preferred:
        if key.lower() in lower_map:
            return lower_map[key.lower()]

    for name in fieldnames:
        lname = name.lower()
        if "date" in lname or "day" in lname or "time" in lname:
            return name

    return None


def score_rate_column_name(pair: str, col: str) -> int:
    name = col.lower()
    score = 0

    generic_positive = [
        "rate",
        "close",
        "value",
        "mid",
        "price",
        "fx",
        "last",
    ]
    for token in generic_positive:
        if token in name:
            score += 10

    if pair == "JPYTHB":
        pair_tokens = [
            "jpythb",
            "jpy_thb",
            "jpy-thb",
            "thbjpy",
            "thb_jpy",
            "thb-jpy",
        ]
        remit_tokens = ["remit", "remittance", "send", "transfer", "buy", "tt", "telegraphic"]
        for token in pair_tokens:
            if token in name:
                score += 40
        for token in remit_tokens:
            if token in name:
                score += 18

    elif pair == "USDJPY":
        pair_tokens = [
            "usdjpy",
            "usd_jpy",
            "usd-jpy",
            "jpyusd",
            "jpy_usd",
            "jpy-usd",
        ]
        for token in pair_tokens:
            if token in name:
                score += 40

    elif pair == "USDTHB":
        pair_tokens = [
            "usdthb",
            "usd_thb",
            "usd-thb",
            "thbusd",
            "thb_usd",
            "thb-usd",
        ]
        for token in pair_tokens:
            if token in name:
                score += 40

    blocked = [
        "diff",
        "change",
        "pct",
        "percent",
        "vol",
        "volatility",
        "note",
        "comment",
        "spread",
        "days",
        "miss",
        "missing",
    ]
    for token in blocked:
        if token in name:
            score -= 20

    return score


def detect_rate_column(pair: str, fieldnames: List[str], sample_rows: List[Dict[str, Any]]) -> Optional[str]:
    if not fieldnames:
        return None

    ranked: List[Tuple[int, str]] = []
    for col in fieldnames:
        score = score_rate_column_name(pair, col)

        numeric_count = 0
        positive_count = 0
        for row in sample_rows[:20]:
            value = safe_float(row.get(col), None)
            if value is not None:
                numeric_count += 1
                if value > 0:
                    positive_count += 1

        score += numeric_count * 2
        score += positive_count
        ranked.append((score, col))

    ranked.sort(key=lambda x: (-x[0], x[1]))
    if not ranked:
        return None

    best_score, best_col = ranked[0]
    if best_score < 8:
        return None
    return best_col


def read_csv_series(path: Path, pair: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        raw_rows = [dict(row) for row in reader if isinstance(row, dict)]

    if not raw_rows:
        return rows

    date_col = detect_date_column(fieldnames)
    rate_col = detect_rate_column(pair, fieldnames, raw_rows)

    if date_col and rate_col:
        for row in raw_rows:
            rows.append(
                {
                    "date": row.get(date_col),
                    "rate": row.get(rate_col),
                    "_rate_column": rate_col,
                }
            )
        return rows

    return raw_rows


def normalize_date_text(date_value: Any) -> Optional[str]:
    if date_value is None:
        return None

    date_text = str(date_value).strip()
    if not date_text:
        return None

    if "T" in date_text:
        date_text = date_text.split("T", 1)[0]
    if " " in date_text and len(date_text) > 10:
        date_text = date_text.split(" ", 1)[0]
    if "/" in date_text and len(date_text) >= 8:
        date_text = date_text.replace("/", "-")

    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_text):
        return date_text

    return date_text


def detect_orientation_from_column(pair: str, column_name: Optional[str]) -> str:
    if not column_name:
        return "unknown"

    name = str(column_name).lower()

    if pair == "USDJPY":
        if any(token in name for token in ["jpyusd", "jpy_usd", "jpy-usd"]):
            return "inverse"
        if any(token in name for token in ["usdjpy", "usd_jpy", "usd-jpy"]):
            return "direct"

    if pair == "USDTHB":
        if any(token in name for token in ["thbusd", "thb_usd", "thb-usd"]):
            return "inverse"
        if any(token in name for token in ["usdthb", "usd_thb", "usd-thb"]):
            return "direct"

    if pair == "JPYTHB":
        if any(token in name for token in ["thbjpy", "thb_jpy", "thb-jpy"]):
            return "inverse"
        if any(token in name for token in ["jpythb", "jpy_thb", "jpy-thb"]):
            return "direct"

    return "unknown"


def normalize_record(raw: Dict[str, Any], pair: str, source_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    date_value = (
        raw.get("date")
        or raw.get("as_of")
        or raw.get("day")
        or raw.get("timestamp")
        or raw.get("datetime")
        or raw.get("Date")
        or raw.get("DATE")
    )
    date_text = normalize_date_text(date_value)
    if date_text is None:
        return None

    pair_specific_candidates: List[Any] = []

    if pair == "JPYTHB":
        pair_specific_candidates.extend(
            [
                raw.get("jpythb"),
                raw.get("JPYTHB"),
                raw.get("jpy_thb"),
                raw.get("JPY_THB"),
                raw.get("jpy-thb"),
                raw.get("JPY-THB"),
                raw.get("remittance_rate"),
                raw.get("REMITTANCE_RATE"),
                raw.get("send_rate"),
                raw.get("SEND_RATE"),
                raw.get("buy_rate"),
                raw.get("BUY_RATE"),
                raw.get("tt_buy"),
                raw.get("TT_BUY"),
                raw.get("tt"),
                raw.get("TT"),
                raw.get("thbjpy"),
                raw.get("THBJPY"),
                raw.get("thb_jpy"),
                raw.get("THB_JPY"),
                raw.get("thb-jpy"),
                raw.get("THB-JPY"),
            ]
        )
    elif pair == "USDJPY":
        pair_specific_candidates.extend(
            [
                raw.get("usdjpy"),
                raw.get("USDJPY"),
                raw.get("usd_jpy"),
                raw.get("USD_JPY"),
                raw.get("usd-jpy"),
                raw.get("USD-JPY"),
                raw.get("jpyusd"),
                raw.get("JPYUSD"),
                raw.get("jpy_usd"),
                raw.get("JPY_USD"),
                raw.get("jpy-usd"),
                raw.get("JPY-USD"),
            ]
        )
    elif pair == "USDTHB":
        pair_specific_candidates.extend(
            [
                raw.get("usdthb"),
                raw.get("USDTHB"),
                raw.get("usd_thb"),
                raw.get("USD_THB"),
                raw.get("usd-thb"),
                raw.get("USD-THB"),
                raw.get("thbusd"),
                raw.get("THBUSD"),
                raw.get("thb_usd"),
                raw.get("THB_USD"),
                raw.get("thb-usd"),
                raw.get("THB-USD"),
            ]
        )

    generic_candidates = [
        raw.get("rate"),
        raw.get("close"),
        raw.get("value"),
        raw.get("mid"),
        raw.get("price"),
        raw.get("Rate"),
        raw.get("Close"),
        raw.get("Value"),
    ]

    rate_candidates = pair_specific_candidates + generic_candidates

    rate_value: Optional[float] = None
    for candidate in rate_candidates:
        value = safe_float(candidate, None)
        if value is not None and value > 0:
            rate_value = value
            break

    if rate_value is None:
        return None

    orientation = "unknown"
    rate_column = raw.get("_rate_column")

    col_orientation = detect_orientation_from_column(pair, rate_column)
    if col_orientation != "unknown":
        orientation = col_orientation
    elif source_path is not None:
        path_orientation = infer_pair_orientation_from_path(source_path, pair)
        if path_orientation != "unknown":
            orientation = path_orientation

    normalized_rate = float(rate_value)
    if orientation == "inverse" and normalized_rate > 0:
        normalized_rate = 1.0 / normalized_rate

    return {
        "date": date_text,
        "rate": normalized_rate,
    }


def try_load_series_from_path(path: Path, pair: str) -> List[Dict[str, Any]]:
    try:
        if path.suffix.lower() == ".json":
            rows = read_json_series(path)
        elif path.suffix.lower() == ".csv":
            rows = read_csv_series(path, pair)
        else:
            rows = []
    except Exception:
        return []

    normalized: List[Dict[str, Any]] = []
    seen = set()

    for row in rows:
        item = normalize_record(row, pair, source_path=path)
        if item is None:
            continue
        key = (item["date"], round(float(item["rate"]), 12))
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)

    normalized.sort(key=lambda x: x["date"])
    return normalized


def load_pair_history(pair: str) -> Tuple[List[Dict[str, Any]], Optional[Path], List[Path]]:
    candidates = discover_candidate_files(pair)
    for candidate in candidates:
        series = try_load_series_from_path(candidate, pair)
        if len(series) >= 2:
            return series, candidate, candidates
        if len(series) == 1:
            return series, candidate, candidates
    return [], None, candidates


def percent_change(current: float, previous: Optional[float]) -> float:
    if previous is None or previous == 0:
        return 0.0
    return ((current / previous) - 1.0) * 100.0


def latest_previous_rate(series: List[Dict[str, Any]], days_back: int) -> Optional[float]:
    if not series:
        return None
    if len(series) <= days_back:
        return float(series[0]["rate"])
    return float(series[-(days_back + 1)]["rate"])


def compute_return_series(series: List[Dict[str, Any]], periods: int = 7) -> List[float]:
    if len(series) < 2:
        return []

    returns: List[float] = []
    start = max(1, len(series) - periods)
    subset = series[start - 1 :]

    for idx in range(1, len(subset)):
        prev_rate = float(subset[idx - 1]["rate"])
        curr_rate = float(subset[idx]["rate"])
        if prev_rate > 0:
            returns.append(((curr_rate / prev_rate) - 1.0) * 100.0)

    return returns


def compute_volatility_7d(series: List[Dict[str, Any]]) -> float:
    returns = compute_return_series(series, periods=8)
    if len(returns) < 2:
        return 0.0
    return float(pstdev(returns))


def simple_moving_average_gap_pct(series: List[Dict[str, Any]], window: int = 7) -> float:
    if not series:
        return 0.0

    latest = float(series[-1]["rate"])
    subset = series[-window:] if len(series) >= window else series
    avg = sum(float(x["rate"]) for x in subset) / len(subset)

    if avg == 0:
        return 0.0

    return ((latest / avg) - 1.0) * 100.0


def infer_trend(change_7d_pct: float, ma_gap_pct: float) -> str:
    if change_7d_pct >= 0.5 or ma_gap_pct >= 0.5:
        return "up"
    if change_7d_pct <= -0.5 or ma_gap_pct <= -0.5:
        return "down"
    return "stable"


def infer_bias_hint(pair: str, change_7d_pct: float, trend: str, volatility_7d: float) -> str:
    if pair == "JPYTHB":
        if volatility_7d >= 1.2:
            return "volatile_caution"
        if change_7d_pct >= 1.0 and trend == "up":
            return "favorable_for_send"
        if change_7d_pct <= -1.0 and trend == "down":
            return "unfavorable_for_send"
        return "mixed_signal"

    if pair == "USDJPY":
        if volatility_7d >= 1.2:
            return "macro_risk_watch"
        if change_7d_pct >= 1.0:
            return "yen_weakness_watch"
        if change_7d_pct <= -1.0:
            return "yen_strength_watch"
        return "neutral_macro"

    if pair == "USDTHB":
        if volatility_7d >= 1.2:
            return "thb_volatility_watch"
        if trend == "stable":
            return "neutral_crosscheck"
        return "thb_side_watch"

    return "neutral"


def pair_contract(pair: str, series: List[Dict[str, Any]]) -> Dict[str, Any]:
    latest_rate = float(series[-1]["rate"]) if series else 0.0
    change_1d = percent_change(latest_rate, latest_previous_rate(series, 1))
    change_7d = percent_change(latest_rate, latest_previous_rate(series, 7))
    change_30d = percent_change(latest_rate, latest_previous_rate(series, 30))
    vol_7d = compute_volatility_7d(series)
    ma_gap_pct = simple_moving_average_gap_pct(series, window=7)
    trend = infer_trend(change_7d, ma_gap_pct)
    bias_hint = infer_bias_hint(pair, change_7d, trend, vol_7d)

    return {
        "pair": pair,
        "role": PAIR_ROLE[pair],
        "rate": round(latest_rate, 6),
        "change_1d_pct": round(change_1d, 4),
        "change_7d_pct": round(change_7d, 4),
        "change_30d_pct": round(change_30d, 4),
        "volatility_7d": round(vol_7d, 4),
        "trend": trend,
        "ma_gap_pct": round(ma_gap_pct, 4),
        "bias_hint": bias_hint,
        "notes": PAIR_NOTES[pair],
    }


def resolve_as_of(histories: Dict[str, List[Dict[str, Any]]], explicit_date: Optional[str]) -> str:
    if explicit_date:
        return explicit_date

    all_dates: List[str] = []
    for series in histories.values():
        if series:
            all_dates.append(str(series[-1]["date"]))

    if not all_dates:
        return datetime.now().strftime("%Y-%m-%d")

    return max(all_dates)


def build_thresholds() -> Dict[str, Any]:
    return {
        "volatility_7d": {
            "moderate": 0.80,
            "high": 1.20,
            "extreme": 2.00,
        },
        "change_7d_pct": {
            "meaningful_move": 1.00,
            "strong_move": 1.50,
        },
        "change_30d_pct": {
            "meaningful_move": 2.00,
            "strong_move": 3.00,
        },
        "ma_gap_pct": {
            "above_trend": 1.00,
            "below_trend": -1.00,
        },
    }


def build_payload(
    as_of: str,
    pair_contracts: Dict[str, Dict[str, Any]],
    source_map: Dict[str, Optional[Path]],
) -> Dict[str, Any]:
    sources: Dict[str, str] = {}
    for pair, path in source_map.items():
        if path is not None:
            sources[pair] = str(path).replace("\\", "/")

    return {
        "as_of": as_of,
        "engine_version": "fx_inputs_v1",
        "base_currency": "JPY",
        "quote_context": (
            "FX inputs for Decision Support. JPYTHB is the primary "
            "operational pair for remittance judgment. USDJPY and USDTHB "
            "are supporting cross-check pairs."
        ),
        "primary_pair": "JPYTHB",
        "pairs": pair_contracts,
        "thresholds": build_thresholds(),
        "policy": {
            "decision_mode": "rule_based_explainable_v1",
            "split_allowed": True,
            "human_final_judgment": True,
            "auto_execute": False,
        },
        "sources": sources,
        "schema_notes": [
            "This artifact is an input contract for scripts/fx_decision_engine.py.",
            "The UI must not calculate from this artifact directly.",
            "Missing values should be tolerated by the engine using safe defaults.",
        ],
    }


def validate_required_pairs(histories: Dict[str, List[Dict[str, Any]]], strict: bool) -> None:
    missing = [pair for pair, series in histories.items() if not series]
    if missing and strict:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"missing FX history for required pairs: {joined}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build analysis/fx/fx_inputs_latest.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output path for fx_inputs_latest.json",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Optional explicit as_of date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any required pair source is missing",
    )
    args = parser.parse_args()

    histories: Dict[str, List[Dict[str, Any]]] = {}
    source_map: Dict[str, Optional[Path]] = {}
    candidates_map: Dict[str, List[Path]] = {}

    for pair in PAIRS:
        series, source, candidates = load_pair_history(pair)
        histories[pair] = series
        source_map[pair] = source
        candidates_map[pair] = candidates

    validate_required_pairs(histories, strict=args.strict)

    pair_contracts: Dict[str, Dict[str, Any]] = {}
    for pair in PAIRS:
        pair_contracts[pair] = pair_contract(pair, histories[pair])

    as_of = resolve_as_of(histories, args.date)
    payload = build_payload(as_of, pair_contracts, source_map)
    save_json(args.output, payload)

    print(f"[build_fx_inputs_latest] wrote {args.output}")
    for pair in PAIRS:
        source = source_map[pair]
        if source:
            source_text = str(source)
        else:
            source_text = "(no source found; default zeros used)"

        print(f"[build_fx_inputs_latest] {pair:<6} source={source_text}")
        print(
            f"[build_fx_inputs_latest] {pair:<6} "
            f"rate={pair_contracts[pair]['rate']} "
            f"chg7d={pair_contracts[pair]['change_7d_pct']} "
            f"vol7d={pair_contracts[pair]['volatility_7d']} "
            f"trend={pair_contracts[pair]['trend']}"
        )

        if not source and candidates_map[pair]:
            print(f"[build_fx_inputs_latest] {pair:<6} candidate scan:")
            for candidate in candidates_map[pair][:5]:
                print(f"  - {candidate}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]

DOCS_DIR = ROOT / "docs"
ANALYSIS_DIR = ROOT / "analysis"
PREDICTION_DIR = ANALYSIS_DIR / "prediction"

DECISION_LOG_PATH = DOCS_DIR / "core" / "decision_log.md"
PREDICTION_HISTORY_DIR = PREDICTION_DIR / "history"
HISTORICAL_DIR = ANALYSIS_DIR / "historical"
EXPLANATION_DIR = ANALYSIS_DIR / "explanation"

VECTOR_MEMORY_BUILD_LATEST_PATH = PREDICTION_DIR / "vector_memory_build_latest.json"


@dataclass
class SourceState:
    label: str
    path: str
    exists: bool
    latest_mtime_iso: Optional[str]
    latest_item: Optional[str]
    reason: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def path_mtime_iso(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def safe_load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_iso_to_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def latest_file_under(
    base_dir: Path,
    patterns: Iterable[str],
) -> Tuple[Optional[Path], Optional[datetime]]:
    latest_path: Optional[Path] = None
    latest_dt: Optional[datetime] = None

    if not base_dir.exists():
        return None, None

    for pattern in patterns:
        for path in base_dir.rglob(pattern):
            if not path.is_file():
                continue
            dt = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if latest_dt is None or dt > latest_dt:
                latest_path = path
                latest_dt = dt

    return latest_path, latest_dt


def newest_prediction_history_snapshot() -> Tuple[Optional[Path], Optional[datetime]]:
    if not PREDICTION_HISTORY_DIR.exists():
        return None, None

    latest_path: Optional[Path] = None
    latest_dt: Optional[datetime] = None

    for dated_dir in PREDICTION_HISTORY_DIR.iterdir():
        if not dated_dir.is_dir():
            continue

        for filename in (
            "prediction.json",
            "scenario.json",
            "signal.json",
            "historical_pattern.json",
            "historical_analog.json",
            "reference_memory.json",
        ):
            candidate = dated_dir / filename
            if not candidate.exists():
                continue
            dt = datetime.fromtimestamp(candidate.stat().st_mtime, tz=timezone.utc)
            if latest_dt is None or dt > latest_dt:
                latest_path = candidate
                latest_dt = dt

    return latest_path, latest_dt


def get_vector_memory_build_time(path: Path) -> Optional[datetime]:
    data = safe_load_json(path)

    for key in ("generated_at", "updated_at", "built_at"):
        dt = parse_iso_to_dt(data.get(key))
        if dt is not None:
            return dt

    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

    return None


def build_source_states() -> List[SourceState]:
    states: List[SourceState] = []

    decision_exists = DECISION_LOG_PATH.exists()
    states.append(
        SourceState(
            label="decision_log",
            path=str(DECISION_LOG_PATH.relative_to(ROOT)),
            exists=decision_exists,
            latest_mtime_iso=path_mtime_iso(DECISION_LOG_PATH),
            latest_item=str(DECISION_LOG_PATH.relative_to(ROOT)) if decision_exists else None,
            reason="docs/core/decision_log.md is a primary vector-memory source.",
        )
    )

    history_path, history_dt = newest_prediction_history_snapshot()
    states.append(
        SourceState(
            label="prediction_history",
            path=str(PREDICTION_HISTORY_DIR.relative_to(ROOT)),
            exists=PREDICTION_HISTORY_DIR.exists(),
            latest_mtime_iso=history_dt.replace(microsecond=0).isoformat() if history_dt else None,
            latest_item=str(history_path.relative_to(ROOT)) if history_path else None,
            reason="analysis/prediction/history contains daily snapshot memory sources.",
        )
    )

    historical_path, historical_dt = latest_file_under(
        HISTORICAL_DIR,
        patterns=["*.json"],
    )
    states.append(
        SourceState(
            label="historical",
            path=str(HISTORICAL_DIR.relative_to(ROOT)),
            exists=HISTORICAL_DIR.exists(),
            latest_mtime_iso=historical_dt.replace(microsecond=0).isoformat() if historical_dt else None,
            latest_item=str(historical_path.relative_to(ROOT)) if historical_path else None,
            reason="analysis/historical contains historical pattern and analog memory sources.",
        )
    )

    explanation_path, explanation_dt = latest_file_under(
        EXPLANATION_DIR,
        patterns=["*.json"],
    )
    states.append(
        SourceState(
            label="explanation",
            path=str(EXPLANATION_DIR.relative_to(ROOT)),
            exists=EXPLANATION_DIR.exists(),
            latest_mtime_iso=explanation_dt.replace(microsecond=0).isoformat() if explanation_dt else None,
            latest_item=str(explanation_path.relative_to(ROOT)) if explanation_path else None,
            reason="analysis/explanation contains explanation memory sources.",
        )
    )

    return states


def build_report() -> Dict[str, Any]:
    build_exists = VECTOR_MEMORY_BUILD_LATEST_PATH.exists()
    build_dt = get_vector_memory_build_time(VECTOR_MEMORY_BUILD_LATEST_PATH)
    source_states = build_source_states()

    stale_reasons: List[str] = []

    if not build_exists:
        stale_reasons.append("vector_memory_build_latest.json does not exist")

    if build_dt is None:
        stale_reasons.append("vector_memory_build_latest.json has no detectable build time")

    latest_source_dt: Optional[datetime] = None
    latest_source_label: Optional[str] = None
    latest_source_item: Optional[str] = None

    for state in source_states:
        source_dt = parse_iso_to_dt(state.latest_mtime_iso)
        if source_dt is None:
            continue

        if latest_source_dt is None or source_dt > latest_source_dt:
            latest_source_dt = source_dt
            latest_source_label = state.label
            latest_source_item = state.latest_item

        if build_dt is not None and source_dt > build_dt:
            stale_reasons.append(
                f"{state.label} is newer than vector memory build"
                + (f" ({state.latest_item})" if state.latest_item else "")
            )

    status = "fresh"
    if stale_reasons:
        status = "stale"

    recommended_command = "python scripts/build_vector_memory.py"

    return {
        "checked_at": utc_now_iso(),
        "status": status,
        "vector_memory_build": {
            "path": str(VECTOR_MEMORY_BUILD_LATEST_PATH.relative_to(ROOT)),
            "exists": build_exists,
            "build_time": build_dt.replace(microsecond=0).isoformat() if build_dt else None,
        },
        "sources": [
            {
                "label": s.label,
                "path": s.path,
                "exists": s.exists,
                "latest_mtime": s.latest_mtime_iso,
                "latest_item": s.latest_item,
                "reason": s.reason,
            }
            for s in source_states
        ],
        "latest_source": {
            "label": latest_source_label,
            "latest_item": latest_source_item,
            "latest_mtime": latest_source_dt.replace(microsecond=0).isoformat() if latest_source_dt else None,
        },
        "stale_reasons": stale_reasons,
        "recommended_command": recommended_command,
    }


def print_report(report: Dict[str, Any]) -> int:
    status = report.get("status", "unknown")
    build_info = report.get("vector_memory_build", {})
    stale_reasons = report.get("stale_reasons", []) or []
    recommended_command = report.get("recommended_command", "")

    if status == "fresh":
        print("[OK] vector memory is fresh")
        print(f"  build_stamp     : {build_info.get('path')}")
        print(f"  build_time      : {build_info.get('build_time')}")
        latest_source = report.get("latest_source", {})
        if latest_source.get("latest_item"):
            print(f"  latest_source   : {latest_source.get('latest_item')}")
            print(f"  latest_mtime    : {latest_source.get('latest_mtime')}")
        return 0

    print("[WARN] vector memory rebuild recommended")
    print(f"  build_stamp     : {build_info.get('path')}")
    print(f"  build_time      : {build_info.get('build_time')}")

    latest_source = report.get("latest_source", {})
    if latest_source.get("latest_item"):
        print(f"  latest_source   : {latest_source.get('latest_item')}")
        print(f"  latest_mtime    : {latest_source.get('latest_mtime')}")

    for reason in stale_reasons:
        print(f"  - {reason}")

    if recommended_command:
        print("  suggested_command:")
        print(f"    {recommended_command}")

    return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether GenesisPrediction vector memory rebuild is recommended."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print report as JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(0 if report.get("status") == "fresh" else 2)

    exit_code = print_report(report)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
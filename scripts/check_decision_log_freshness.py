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

DECISION_LOG_PATH = DOCS_DIR / "core" / "decision_log.md"

DECISION_RELEVANT_DOCS = [
    DOCS_DIR / "core",
    DOCS_DIR / "active",
    DOCS_DIR / "reference",
]

DECISION_RELEVANT_PATTERNS = [
    "*.md",
]

IGNORE_FILENAMES = {
    "decision_log.md",
}

CANDIDATE_KEYWORDS = [
    "rule",
    "rules",
    "agreement",
    "architecture",
    "design",
    "policy",
    "standard",
    "map",
    "contract",
    "schema",
    "roadmap",
    "system",
    "memory",
    "prediction",
    "pipeline",
    "ui",
    "layout",
    "language",
    "decision",
]


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


def safe_load_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def latest_file_under(
    base_dir: Path,
    patterns: Iterable[str],
    *,
    ignore_names: Optional[set[str]] = None,
    keyword_filter: Optional[list[str]] = None,
) -> Tuple[Optional[Path], Optional[datetime]]:
    latest_path: Optional[Path] = None
    latest_dt: Optional[datetime] = None

    if not base_dir.exists():
        return None, None

    ignore_names = ignore_names or set()
    keyword_filter = keyword_filter or []

    for pattern in patterns:
        for path in base_dir.rglob(pattern):
            if not path.is_file():
                continue
            if path.name in ignore_names:
                continue

            path_text = path.as_posix().lower()
            if keyword_filter:
                if not any(keyword in path_text for keyword in keyword_filter):
                    continue

            dt = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if latest_dt is None or dt > latest_dt:
                latest_path = path
                latest_dt = dt

    return latest_path, latest_dt


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
            reason="docs/core/decision_log.md stores human design decisions.",
        )
    )

    for base_dir in DECISION_RELEVANT_DOCS:
        latest_path, latest_dt = latest_file_under(
            base_dir,
            DECISION_RELEVANT_PATTERNS,
            ignore_names=IGNORE_FILENAMES,
            keyword_filter=CANDIDATE_KEYWORDS,
        )
        states.append(
            SourceState(
                label=f"candidate_docs:{base_dir.name}",
                path=str(base_dir.relative_to(ROOT)),
                exists=base_dir.exists(),
                latest_mtime_iso=latest_dt.replace(microsecond=0).isoformat() if latest_dt else None,
                latest_item=str(latest_path.relative_to(ROOT)) if latest_path else None,
                reason="Potential rule / architecture / system documents that may require a decision log update.",
            )
        )

    return states


def extract_recent_decision_titles(limit: int = 5) -> List[str]:
    text = safe_load_text(DECISION_LOG_PATH)
    if not text:
        return []

    titles: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## Decision:"):
            title = stripped.replace("## Decision:", "", 1).strip()
            if title:
                titles.append(title)

    return titles[-limit:]


def build_report() -> Dict[str, Any]:
    source_states = build_source_states()
    decision_log_state = next((s for s in source_states if s.label == "decision_log"), None)

    decision_log_dt = parse_iso_to_dt(decision_log_state.latest_mtime_iso if decision_log_state else None)
    stale_reasons: List[str] = []

    latest_candidate_dt: Optional[datetime] = None
    latest_candidate_label: Optional[str] = None
    latest_candidate_item: Optional[str] = None

    for state in source_states:
        if state.label == "decision_log":
            continue

        source_dt = parse_iso_to_dt(state.latest_mtime_iso)
        if source_dt is None:
            continue

        if latest_candidate_dt is None or source_dt > latest_candidate_dt:
            latest_candidate_dt = source_dt
            latest_candidate_label = state.label
            latest_candidate_item = state.latest_item

        if decision_log_dt is None:
            stale_reasons.append(
                f"decision_log.md is missing or has no detectable update time; review {state.path}"
            )
            continue

        if source_dt > decision_log_dt:
            stale_reasons.append(
                f"{state.label} is newer than decision_log.md"
                + (f" ({state.latest_item})" if state.latest_item else "")
            )

    status = "fresh"
    if stale_reasons:
        status = "stale"

    recent_titles = extract_recent_decision_titles(limit=5)

    return {
        "checked_at": utc_now_iso(),
        "status": status,
        "decision_log": {
            "path": str(DECISION_LOG_PATH.relative_to(ROOT)),
            "exists": DECISION_LOG_PATH.exists(),
            "updated_at": decision_log_state.latest_mtime_iso if decision_log_state else None,
            "recent_titles": recent_titles,
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
        "latest_candidate": {
            "label": latest_candidate_label,
            "latest_item": latest_candidate_item,
            "latest_mtime": latest_candidate_dt.replace(microsecond=0).isoformat() if latest_candidate_dt else None,
        },
        "stale_reasons": stale_reasons,
        "suggested_action": (
            "Review docs/core/decision_log.md and record important human decisions if needed."
        ),
        "suggested_followup": (
            "After updating decision_log.md, run: python scripts/build_vector_memory.py"
        ),
    }


def print_report(report: Dict[str, Any]) -> int:
    status = report.get("status", "unknown")
    decision_log = report.get("decision_log", {})
    stale_reasons = report.get("stale_reasons", []) or []

    if status == "fresh":
        print("[OK] decision log looks current")
        print(f"  decision_log   : {decision_log.get('path')}")
        print(f"  updated_at     : {decision_log.get('updated_at')}")
        recent_titles = decision_log.get("recent_titles", []) or []
        if recent_titles:
            print("  recent_titles  :")
            for title in recent_titles:
                print(f"    - {title}")
        latest_candidate = report.get("latest_candidate", {})
        if latest_candidate.get("latest_item"):
            print(f"  latest_source  : {latest_candidate.get('latest_item')}")
            print(f"  latest_mtime   : {latest_candidate.get('latest_mtime')}")
        return 0

    print("[WARN] decision log update may be needed")
    print(f"  decision_log   : {decision_log.get('path')}")
    print(f"  updated_at     : {decision_log.get('updated_at')}")

    latest_candidate = report.get("latest_candidate", {})
    if latest_candidate.get("latest_item"):
        print(f"  latest_source  : {latest_candidate.get('latest_item')}")
        print(f"  latest_mtime   : {latest_candidate.get('latest_mtime')}")

    recent_titles = decision_log.get("recent_titles", []) or []
    if recent_titles:
        print("  recent_titles  :")
        for title in recent_titles:
            print(f"    - {title}")

    for reason in stale_reasons:
        print(f"  - {reason}")

    print("  suggested_action:")
    print(f"    {report.get('suggested_action')}")
    print("  suggested_followup:")
    print(f"    {report.get('suggested_followup')}")

    return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether docs/core/decision_log.md may need an update."
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
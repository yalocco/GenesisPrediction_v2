#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
save_observation_memory.py

Purpose:
    Save latest analysis snapshots into daily history files.

Design:
    - analysis = Single Source of Truth (current truth)
    - history  = observation memory (daily snapshots)
    - UI       = read-only
    - This script does not transform business logic; it only copies validated JSON
      from latest analysis outputs into dated history storage.

Default targets:
    - data/world_politics/analysis/sentiment_latest.json
    - data/world_politics/analysis/daily_summary_latest.json
    - data/world_politics/analysis/health_latest.json

Default history destinations:
    - data/world_politics/history/sentiment/sentiment_YYYY-MM-DD.json
    - data/world_politics/history/daily_summary/daily_summary_YYYY-MM-DD.json
    - data/world_politics/history/health/health_YYYY-MM-DD.json

Usage:
    python scripts/save_observation_memory.py --date 2026-03-07

Options:
    --date YYYY-MM-DD   Target observation date. If omitted, local today is used.
    --dry-run           Show what would happen without writing files.
    --strict            Exit non-zero if any source file is missing/invalid.
    --verbose           Print extra details.

Exit codes:
    0 = success
    1 = partial failure / strict failure / unexpected error
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent

DEFAULT_TARGETS = [
    {
        "name": "sentiment",
        "source": REPO_ROOT / "data" / "world_politics" / "analysis" / "sentiment_latest.json",
        "history_dir": REPO_ROOT / "data" / "world_politics" / "history" / "sentiment",
        "filename_prefix": "sentiment",
    },
    {
        "name": "daily_summary",
        "source": REPO_ROOT / "data" / "world_politics" / "analysis" / "daily_summary_latest.json",
        "history_dir": REPO_ROOT / "data" / "world_politics" / "history" / "daily_summary",
        "filename_prefix": "daily_summary",
    },
    {
        "name": "health",
        "source": REPO_ROOT / "data" / "world_politics" / "analysis" / "health_latest.json",
        "history_dir": REPO_ROOT / "data" / "world_politics" / "history" / "health",
        "filename_prefix": "health",
    },
]


@dataclass
class SaveResult:
    name: str
    source: Path
    destination: Path
    ok: bool
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save latest analysis snapshots into dated history files."
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Observation date in YYYY-MM-DD format. Defaults to local today.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned operations without writing files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any source file is missing or invalid.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra details.",
    )
    return parser.parse_args()


def resolve_target_date(date_str: str | None) -> str:
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d")

    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid --date value: {date_str!r}. Expected YYYY-MM-DD.") from exc

    return parsed.strftime("%Y-%m-%d")


def validate_json_file(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "source file not found"

    if not path.is_file():
        return False, "source path is not a file"

    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:
        return False, f"failed to read file: {exc}"

    if not raw.strip():
        return False, "source file is empty"

    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        return False, f"invalid JSON: {exc}"

    return True, "ok"


def build_destination(history_dir: Path, filename_prefix: str, target_date: str) -> Path:
    filename = f"{filename_prefix}_{target_date}.json"
    return history_dir / filename


def copy_snapshot(
    *,
    name: str,
    source: Path,
    destination: Path,
    dry_run: bool,
    verbose: bool,
) -> SaveResult:
    valid, reason = validate_json_file(source)
    if not valid:
        return SaveResult(
            name=name,
            source=source,
            destination=destination,
            ok=False,
            message=reason,
        )

    if dry_run:
        return SaveResult(
            name=name,
            source=source,
            destination=destination,
            ok=True,
            message="dry-run: validated, not written",
        )

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    except Exception as exc:
        return SaveResult(
            name=name,
            source=source,
            destination=destination,
            ok=False,
            message=f"copy failed: {exc}",
        )

    if verbose:
        size = destination.stat().st_size if destination.exists() else 0
        return SaveResult(
            name=name,
            source=source,
            destination=destination,
            ok=True,
            message=f"saved ({size} bytes)",
        )

    return SaveResult(
        name=name,
        source=source,
        destination=destination,
        ok=True,
        message="saved",
    )


def print_header(target_date: str, dry_run: bool, strict: bool) -> None:
    print("save_observation_memory")
    print(f"ROOT    : {REPO_ROOT}")
    print(f"DATE    : {target_date}")
    print(f"DRY_RUN : {'ON' if dry_run else 'OFF'}")
    print(f"STRICT  : {'ON' if strict else 'OFF'}")
    print("")


def print_result(result: SaveResult) -> None:
    status = "OK" if result.ok else "NG"
    print(f"[{status}] {result.name}")
    print(f"  source : {result.source}")
    print(f"  dest   : {result.destination}")
    print(f"  detail : {result.message}")
    print("")


def summarize(results: List[SaveResult]) -> int:
    ok_count = sum(1 for r in results if r.ok)
    ng_count = sum(1 for r in results if not r.ok)

    print("summary")
    print(f"  ok : {ok_count}")
    print(f"  ng : {ng_count}")

    return 0 if ng_count == 0 else 1


def main() -> int:
    args = parse_args()

    try:
        target_date = resolve_target_date(args.date)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print_header(target_date=target_date, dry_run=args.dry_run, strict=args.strict)

    results: List[SaveResult] = []

    for target in DEFAULT_TARGETS:
        destination = build_destination(
            history_dir=target["history_dir"],
            filename_prefix=target["filename_prefix"],
            target_date=target_date,
        )

        result = copy_snapshot(
            name=target["name"],
            source=target["source"],
            destination=destination,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
        results.append(result)
        print_result(result)

    has_failure = any(not r.ok for r in results)

    if has_failure and args.strict:
        print("STRICT mode: failure detected.")
        return 1

    return summarize(results)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise SystemExit(1)
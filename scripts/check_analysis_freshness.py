#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FreshnessTarget:
    name: str
    path: Path
    required: bool = True


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_yyyy_mm_dd(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def extract_date_string(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None

        # Accept plain YYYY-MM-DD and common ISO datetime strings.
        if len(raw) >= 10:
            return raw[:10]

        return raw

    return str(value)


def check_target(target: FreshnessTarget, expected_date: date, allow_previous_day: bool) -> bool:
    print(f"--- {target.name} ---")
    print(f"path: {target.path}")

    if not target.path.exists():
        level = "FAIL" if target.required else "WARN"
        print(f"[{level}] missing artifact")
        return not target.required

    try:
        data = load_json(target.path)
    except Exception as e:
        print("[FAIL] json load failed")
        print(f"reason: {e}")
        return False

    if not isinstance(data, dict):
        print("[FAIL] root json is not an object")
        return False

    raw_as_of = data.get("as_of")
    as_of_text = extract_date_string(raw_as_of)

    if not as_of_text:
        print("[FAIL] missing as_of")
        return False

    try:
        as_of_date = parse_yyyy_mm_dd(as_of_text)
    except ValueError:
        print("[FAIL] invalid as_of format")
        print(f"as_of: {raw_as_of}")
        print("expected: YYYY-MM-DD or ISO datetime beginning with YYYY-MM-DD")
        return False

    if as_of_date > expected_date:
        print("[FAIL] as_of is in the future")
        print(f"as_of        : {as_of_date.isoformat()}")
        print(f"expected_date: {expected_date.isoformat()}")
        return False

    accepted_dates = {expected_date}
    if allow_previous_day:
        accepted_dates.add(expected_date - timedelta(days=1))

    if as_of_date not in accepted_dates:
        print("[FAIL] stale artifact")
        print(f"as_of        : {as_of_date.isoformat()}")
        print(f"expected_date: {expected_date.isoformat()}")
        if allow_previous_day:
            print(f"allowed      : {', '.join(sorted(d.isoformat() for d in accepted_dates))}")
        return False

    print("[OK] fresh")
    print(f"as_of: {as_of_date.isoformat()}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check GenesisPrediction analysis artifact freshness before unattended deploy."
    )
    parser.add_argument("--root", required=True, help="Repository root")
    parser.add_argument("--date", required=True, help="Expected run date in YYYY-MM-DD")
    parser.add_argument(
        "--allow-previous-day",
        action="store_true",
        help="Accept expected date or expected date - 1 day. Useful for workflows that intentionally publish previous-day analysis.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()

    try:
        expected_date = parse_yyyy_mm_dd(args.date)
    except ValueError:
        print("[FAIL] invalid --date. Expected YYYY-MM-DD.")
        print(f"value: {args.date}")
        return 1

    targets = [
        FreshnessTarget(
            name="prediction_latest",
            path=root / "analysis" / "prediction" / "prediction_latest.json",
            required=True,
        ),
        FreshnessTarget(
            name="prediction_explanation_latest",
            path=root / "analysis" / "explanation" / "prediction_explanation_latest.json",
            required=True,
        ),
        FreshnessTarget(
            name="global_status_latest",
            path=root / "analysis" / "global_status_latest.json",
            required=True,
        ),
    ]

    print("=== GenesisPrediction Analysis Freshness Check ===")
    print(f"root              : {root}")
    print(f"expected_date     : {expected_date.isoformat()}")
    print(f"allow_previous_day: {args.allow_previous_day}")
    print("")

    all_ok = True

    for target in targets:
        ok = check_target(
            target=target,
            expected_date=expected_date,
            allow_previous_day=args.allow_previous_day,
        )
        all_ok = all_ok and ok
        print("")

    if all_ok:
        print("[DONE] Analysis freshness check passed")
        return 0

    print("[FAILED] Analysis freshness check failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())

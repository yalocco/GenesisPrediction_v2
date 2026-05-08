#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    encodings = ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be")

    for encoding in encodings:
        try:
            data = json.loads(path.read_text(encoding=encoding))
            if isinstance(data, dict):
                return data
            return {"_error": "json_root_not_object", "_type": type(data).__name__}
        except Exception:
            continue

    return {"_error": "json_read_failed"}


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if pretty:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    path.write_text(text + "\n", encoding="utf-8")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_get(data: dict[str, Any] | None, keys: list[str], default: Any = None) -> Any:
    if not isinstance(data, dict):
        return default

    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)

    return current if current is not None else default


def load_history(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)

    if not isinstance(data, dict) or data.get("_error"):
        return []

    entries = data.get("entries")
    if not isinstance(entries, list):
        return []

    return [entry for entry in entries if isinstance(entry, dict)]


def trim_entries(entries: list[dict[str, Any]], keep: int) -> list[dict[str, Any]]:
    if keep <= 0:
        return entries

    return entries[-keep:]


def count_status(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}

    for entry in entries:
        value = entry.get(field)
        key = str(value) if value is not None else "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1

    return counts


def derive_streak(entries: list[dict[str, Any]], field: str, target: str) -> int:
    streak = 0

    for entry in reversed(entries):
        if str(entry.get(field)) == target:
            streak += 1
        else:
            break

    return streak


def latest_snapshot_summary(root: Path) -> dict[str, Any]:
    snapshot_dir = root / "analysis" / "ops" / "deploy_snapshots"
    manifests = sorted(
        snapshot_dir.glob("deploy_snapshot_*.manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not manifests:
        return {
            "available": False,
            "reason": "no_snapshot_manifest",
        }

    manifest = read_json(manifests[0])

    if not isinstance(manifest, dict) or manifest.get("_error"):
        return {
            "available": False,
            "manifest_path": str(manifests[0]),
            "reason": safe_get(manifest, ["_error"], "manifest_read_failed"),
        }

    return {
        "available": True,
        "manifest_path": str(manifests[0]),
        "created_at_utc": manifest.get("created_at_utc"),
        "expected_date": manifest.get("expected_date"),
        "snapshot_sha256": manifest.get("snapshot_sha256"),
        "summary": manifest.get("summary"),
    }


def build_entry(root: Path, expected_date: str | None, note: str) -> dict[str, Any]:
    pipeline_path = root / "analysis" / "ops" / "pipeline_health_latest.json"
    incident_path = root / "analysis" / "ops" / "incidents" / "incident_reconstruction_latest.json"
    global_status_path = root / "analysis" / "global_status_latest.json"

    pipeline = read_json(pipeline_path)
    incident = read_json(incident_path)
    global_status = read_json(global_status_path)

    return {
        "recorded_at_utc": now_utc_iso(),
        "expected_date": expected_date,
        "note": note,
        "pipeline": {
            "available": isinstance(pipeline, dict) and not pipeline.get("_error"),
            "overall_status": safe_get(pipeline, ["overall_status"]),
            "deploy_ready": safe_get(pipeline, ["deploy_readiness", "eligible"]),
            "deploy_reason": safe_get(pipeline, ["deploy_readiness", "reason"]),
            "summary": safe_get(pipeline, ["summary"]),
            "stale_count": len(safe_get(pipeline, ["stale_candidates"], [])),
            "generated_at_utc": safe_get(pipeline, ["generated_at_utc"]),
        },
        "incident": {
            "available": isinstance(incident, dict) and not incident.get("_error"),
            "incident_level": safe_get(incident, ["incident_level"]),
            "reasons": safe_get(incident, ["reasons"], []),
            "created_at_utc": safe_get(incident, ["created_at_utc"]),
        },
        "global_status": {
            "available": isinstance(global_status, dict) and not global_status.get("_error"),
            "as_of": safe_get(global_status, ["as_of"]),
            "global_risk": safe_get(global_status, ["global_risk"]),
            "sentiment_balance": safe_get(global_status, ["sentiment_balance"]),
            "fx_regime": safe_get(global_status, ["fx_regime"]),
            "health": safe_get(global_status, ["health"]),
        },
        "rollback_snapshot": latest_snapshot_summary(root),
        "source_paths": {
            "pipeline_health": str(pipeline_path),
            "incident_reconstruction": str(incident_path),
            "global_status": str(global_status_path),
        },
    }


def derive_trend_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {
            "entries": 0,
            "pipeline_status_counts": {},
            "incident_level_counts": {},
            "deploy_ready_counts": {},
            "current_pipeline_ok_streak": 0,
            "current_incident_ok_streak": 0,
        }

    deploy_ready_counts: dict[str, int] = {}

    for entry in entries:
        value = safe_get(entry, ["pipeline", "deploy_ready"])
        key = "true" if value is True else "false" if value is False else "unknown"
        deploy_ready_counts[key] = deploy_ready_counts.get(key, 0) + 1

    flattened = []
    for entry in entries:
        flattened.append(
            {
                "pipeline_status": safe_get(entry, ["pipeline", "overall_status"], "UNKNOWN"),
                "incident_level": safe_get(entry, ["incident", "incident_level"], "UNKNOWN"),
            }
        )

    pipeline_ok_streak = 0
    for entry in reversed(entries):
        if safe_get(entry, ["pipeline", "overall_status"]) == "OK":
            pipeline_ok_streak += 1
        else:
            break

    incident_ok_streak = 0
    for entry in reversed(entries):
        if safe_get(entry, ["incident", "incident_level"]) == "OK":
            incident_ok_streak += 1
        else:
            break

    return {
        "entries": len(entries),
        "pipeline_status_counts": count_status(flattened, "pipeline_status"),
        "incident_level_counts": count_status(flattened, "incident_level"),
        "deploy_ready_counts": deploy_ready_counts,
        "current_pipeline_ok_streak": pipeline_ok_streak,
        "current_incident_ok_streak": incident_ok_streak,
        "latest_recorded_at_utc": entries[-1].get("recorded_at_utc"),
        "oldest_recorded_at_utc": entries[0].get("recorded_at_utc"),
    }


def build_history(root: Path, expected_date: str | None, note: str, keep: int) -> dict[str, Any]:
    out_path = root / "analysis" / "ops" / "operational_trend_history.json"

    existing_entries = load_history(out_path)
    new_entry = build_entry(root=root, expected_date=expected_date, note=note)
    entries = trim_entries(existing_entries + [new_entry], keep=keep)

    trend_summary = derive_trend_summary(entries)

    return {
        "schema_version": "1.0",
        "updated_at_utc": now_utc_iso(),
        "root": str(root),
        "retention": {
            "keep": keep,
            "entry_count": len(entries),
        },
        "trend_summary": trend_summary,
        "entries": entries,
        "meaning": {
            "operational_trend_history": "History of operational evidence snapshots. It is not runtime truth.",
            "deploy_ready_counts": "Historical readiness observations, not deploy authority.",
            "streaks": "Consecutive observed OK states in recorded history.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append GenesisPrediction operational health and incident status into trend history."
    )
    parser.add_argument("--root", required=True, help="Repository root")
    parser.add_argument("--date", default="", help="Expected artifact date YYYY-MM-DD. Optional.")
    parser.add_argument("--note", default="", help="Optional human note")
    parser.add_argument("--keep", type=int, default=120, help="Number of entries to retain")
    parser.add_argument("--pretty", action="store_true", help="Write pretty JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    expected_date = args.date.strip() or None

    payload = build_history(
        root=root,
        expected_date=expected_date,
        note=args.note.strip(),
        keep=args.keep,
    )

    out_path = root / "analysis" / "ops" / "operational_trend_history.json"
    write_json(out_path, payload, pretty=args.pretty)

    summary = payload["trend_summary"]

    print("=== GenesisPrediction Operational Trend History ===")
    print(f"root                    : {root}")
    print(f"expected_date           : {expected_date}")
    print(f"out                     : {out_path}")
    print(f"entries                 : {summary['entries']}")
    print(f"pipeline_status_counts  : {summary['pipeline_status_counts']}")
    print(f"incident_level_counts   : {summary['incident_level_counts']}")
    print(f"deploy_ready_counts     : {summary['deploy_ready_counts']}")
    print(f"pipeline_ok_streak      : {summary['current_pipeline_ok_streak']}")
    print(f"incident_ok_streak      : {summary['current_incident_ok_streak']}")
    print("[DONE] operational trend history updated")

    return 0


if __name__ == "__main__":
    sys.exit(main())

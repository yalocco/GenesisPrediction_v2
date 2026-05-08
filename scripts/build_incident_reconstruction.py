#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
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
            return {
                "_error": "json_root_not_object",
                "_type": type(data).__name__,
            }
        except Exception:
            continue

    return {
        "_error": "json_read_failed",
    }


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")


def safe_get(data: dict[str, Any] | None, path: list[str], default: Any = None) -> Any:
    if not isinstance(data, dict):
        return default

    current: Any = data

    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)

    return current if current is not None else default


def file_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
        }

    stat = path.stat()

    return {
        "path": str(path),
        "exists": True,
        "size_bytes": stat.st_size,
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }


def latest_snapshot_manifest(snapshot_dir: Path) -> Path | None:
    if not snapshot_dir.exists():
        return None

    manifests = sorted(
        snapshot_dir.glob("deploy_snapshot_*.manifest.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not manifests:
        return None

    return manifests[0]


def collect_artifact_state(root: Path) -> dict[str, Any]:
    paths = {
        "prediction_latest": root / "analysis" / "prediction" / "prediction_latest.json",
        "prediction_explanation_latest": root
        / "analysis"
        / "explanation"
        / "prediction_explanation_latest.json",
        "global_status_latest": root / "analysis" / "global_status_latest.json",
        "pipeline_health_latest": root / "analysis" / "ops" / "pipeline_health_latest.json",
    }

    result: dict[str, Any] = {}

    for name, path in paths.items():
        data = read_json(path)
        result[name] = {
            "file": file_meta(path),
            "as_of": safe_get(data, ["as_of"]),
            "status": safe_get(data, ["overall_status"])
            or safe_get(data, ["status"])
            or safe_get(data, ["health"]),
            "read_error": safe_get(data, ["_error"]),
        }

    return result


def collect_pipeline_health(root: Path) -> dict[str, Any]:
    path = root / "analysis" / "ops" / "pipeline_health_latest.json"
    data = read_json(path)

    if not isinstance(data, dict) or data.get("_error"):
        return {
            "available": False,
            "file": file_meta(path),
            "error": safe_get(data, ["_error"]),
        }

    return {
        "available": True,
        "file": file_meta(path),
        "overall_status": data.get("overall_status"),
        "summary": data.get("summary"),
        "deploy_readiness": data.get("deploy_readiness"),
        "stale_candidates": data.get("stale_candidates", []),
        "expected_date": data.get("expected_date"),
        "generated_at_utc": data.get("generated_at_utc"),
    }


def collect_latest_snapshot(root: Path) -> dict[str, Any]:
    snapshot_dir = root / "analysis" / "ops" / "deploy_snapshots"
    manifest_path = latest_snapshot_manifest(snapshot_dir)

    if manifest_path is None:
        return {
            "available": False,
            "snapshot_dir": str(snapshot_dir),
            "reason": "no_snapshot_manifest",
        }

    manifest = read_json(manifest_path)

    if not isinstance(manifest, dict) or manifest.get("_error"):
        return {
            "available": False,
            "snapshot_dir": str(snapshot_dir),
            "manifest_file": file_meta(manifest_path),
            "reason": safe_get(manifest, ["_error"], "manifest_read_failed"),
        }

    zip_path = Path(str(manifest.get("snapshot_zip", "")))

    return {
        "available": True,
        "snapshot_dir": str(snapshot_dir),
        "manifest_file": file_meta(manifest_path),
        "zip_file": file_meta(zip_path),
        "created_at_utc": manifest.get("created_at_utc"),
        "expected_date": manifest.get("expected_date"),
        "snapshot_sha256": manifest.get("snapshot_sha256"),
        "summary": manifest.get("summary"),
        "retention": manifest.get("retention"),
    }


def derive_incident_level(
    artifact_state: dict[str, Any],
    pipeline_health: dict[str, Any],
    snapshot: dict[str, Any],
) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if pipeline_health.get("available"):
        status = str(pipeline_health.get("overall_status", "")).upper()
        if status == "FAIL":
            reasons.append("pipeline_health_failed")
        elif status == "WARN":
            reasons.append("pipeline_health_warn")
    else:
        reasons.append("pipeline_health_unavailable")

    deploy_readiness = pipeline_health.get("deploy_readiness") if pipeline_health.get("available") else None
    if isinstance(deploy_readiness, dict) and deploy_readiness.get("eligible") is False:
        reasons.append(f"deploy_not_ready:{deploy_readiness.get('reason')}")

    stale_candidates = pipeline_health.get("stale_candidates") if pipeline_health.get("available") else None
    if stale_candidates:
        reasons.append("stale_candidates_present")

    for name, state in artifact_state.items():
        file_info = state.get("file", {})
        if not file_info.get("exists"):
            reasons.append(f"missing_artifact:{name}")
        if state.get("read_error"):
            reasons.append(f"artifact_read_error:{name}:{state.get('read_error')}")

    if not snapshot.get("available"):
        reasons.append("rollback_snapshot_unavailable")

    if any(reason.startswith("missing_artifact") for reason in reasons):
        return "FAIL", reasons

    if any(reason in {"pipeline_health_failed", "pipeline_health_unavailable"} for reason in reasons):
        return "FAIL", reasons

    if any(
        reason.startswith("deploy_not_ready")
        or reason in {"pipeline_health_warn", "stale_candidates_present", "rollback_snapshot_unavailable"}
        for reason in reasons
    ):
        return "WARN", reasons

    return "OK", reasons


def build_incident_reconstruction(root: Path, expected_date: str | None, note: str) -> dict[str, Any]:
    artifact_state = collect_artifact_state(root)
    pipeline_health = collect_pipeline_health(root)
    snapshot = collect_latest_snapshot(root)

    level, reasons = derive_incident_level(
        artifact_state=artifact_state,
        pipeline_health=pipeline_health,
        snapshot=snapshot,
    )

    return {
        "schema_version": "1.0",
        "created_at_utc": now_utc_iso(),
        "root": str(root),
        "expected_date": expected_date,
        "incident_level": level,
        "reasons": reasons,
        "note": note,
        "timeline": [
            {
                "phase": "artifact_state",
                "status": "observed",
                "details": artifact_state,
            },
            {
                "phase": "pipeline_health",
                "status": "observed" if pipeline_health.get("available") else "unavailable",
                "details": pipeline_health,
            },
            {
                "phase": "rollback_snapshot",
                "status": "observed" if snapshot.get("available") else "unavailable",
                "details": snapshot,
            },
        ],
        "artifact_state": artifact_state,
        "pipeline_health": pipeline_health,
        "latest_rollback_snapshot": snapshot,
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "meaning": {
            "incident_reconstruction": "Evidence summary for operational review. It is not source of truth.",
            "incident_level": "Derived operational severity from available artifacts. It does not authorize deployment or rollback.",
            "timeline": "Observed evidence phases, not a complete external event log.",
        },
    }


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if pretty:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    path.write_text(text + "\n", encoding="utf-8")


def update_latest_copy(latest_path: Path, payload: dict[str, Any], pretty: bool) -> None:
    write_json(latest_path, payload, pretty=pretty)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build GenesisPrediction operational incident reconstruction evidence log."
    )
    parser.add_argument("--root", required=True, help="Repository root")
    parser.add_argument("--date", default="", help="Expected artifact date YYYY-MM-DD. Optional.")
    parser.add_argument(
        "--out-dir",
        default="analysis/ops/incidents",
        help="Output directory relative to root unless absolute.",
    )
    parser.add_argument("--note", default="", help="Optional human note for the reconstruction log.")
    parser.add_argument("--pretty", action="store_true", help="Write pretty JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out_dir)

    if not out_dir.is_absolute():
        out_dir = root / out_dir

    expected_date = args.date.strip() or None

    payload = build_incident_reconstruction(
        root=root,
        expected_date=expected_date,
        note=args.note.strip(),
    )

    stamp = now_stamp()
    out_path = out_dir / f"incident_reconstruction_{stamp}.json"
    latest_path = out_dir / "incident_reconstruction_latest.json"

    write_json(out_path, payload, pretty=args.pretty)
    update_latest_copy(latest_path, payload, pretty=args.pretty)

    print("=== GenesisPrediction Incident Reconstruction ===")
    print(f"root           : {root}")
    print(f"expected_date  : {expected_date}")
    print(f"incident_level : {payload['incident_level']}")
    print(f"reasons        : {', '.join(payload['reasons']) if payload['reasons'] else 'none'}")
    print(f"out            : {out_path}")
    print(f"latest         : {latest_path}")

    if payload["incident_level"] == "FAIL":
        print("[FAILED] incident reconstruction found failure-level evidence")
        return 1

    print("[DONE] incident reconstruction written")
    return 0


if __name__ == "__main__":
    sys.exit(main())

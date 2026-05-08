#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArtifactTarget:
    name: str
    path: Path
    required: bool
    expects_as_of: bool = True


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    encodings = ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be")

    for encoding in encodings:
        try:
            data = json.loads(path.read_text(encoding=encoding))
            if isinstance(data, dict):
                return data
            return {"_non_object_json": True, "type": type(data).__name__}
        except Exception:
            continue

    return {"_json_read_error": True}


def parse_as_of(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    if len(text) >= 10:
        return text[:10]

    return text


def artifact_status(target: ArtifactTarget) -> dict[str, Any]:
    exists = target.path.exists()

    result: dict[str, Any] = {
        "name": target.name,
        "path": str(target.path),
        "required": target.required,
        "exists": exists,
        "status": "missing",
        "as_of": None,
        "error": None,
    }

    if not exists:
        result["status"] = "fail" if target.required else "warn"
        result["error"] = "missing"
        return result

    data = read_json(target.path)
    if data is None:
        result["status"] = "fail"
        result["error"] = "json_read_failed"
        return result

    if data.get("_json_read_error"):
        result["status"] = "fail"
        result["error"] = "json_read_failed"
        return result

    if data.get("_non_object_json"):
        result["status"] = "fail"
        result["error"] = "json_root_not_object"
        return result

    as_of = parse_as_of(data.get("as_of"))
    result["as_of"] = as_of

    if target.expects_as_of and not as_of:
        result["status"] = "fail"
        result["error"] = "missing_as_of"
        return result

    result["status"] = "ok"
    return result


def summarize_artifacts(artifacts: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total": len(artifacts),
        "ok": 0,
        "warn": 0,
        "fail": 0,
        "missing": 0,
    }

    for item in artifacts:
        status = item.get("status")
        if status == "ok":
            summary["ok"] += 1
        elif status == "warn":
            summary["warn"] += 1
        elif status == "fail":
            summary["fail"] += 1

        if not item.get("exists"):
            summary["missing"] += 1

    return summary


def derive_overall_status(summary: dict[str, int]) -> str:
    if summary["fail"] > 0:
        return "FAIL"
    if summary["warn"] > 0:
        return "WARN"
    return "OK"


def load_optional_global_status(root: Path) -> dict[str, Any]:
    path = root / "analysis" / "global_status_latest.json"
    data = read_json(path)

    if not isinstance(data, dict) or data.get("_json_read_error") or data.get("_non_object_json"):
        return {
            "available": False,
            "path": str(path),
        }

    return {
        "available": True,
        "path": str(path),
        "as_of": data.get("as_of"),
        "global_risk": data.get("global_risk"),
        "sentiment_balance": data.get("sentiment_balance"),
        "fx_regime": data.get("fx_regime"),
        "articles": data.get("articles"),
        "health": data.get("health"),
    }


def build_pipeline_health(root: Path, expected_date: str | None) -> dict[str, Any]:
    targets = [
        ArtifactTarget(
            name="prediction_latest",
            path=root / "analysis" / "prediction" / "prediction_latest.json",
            required=True,
        ),
        ArtifactTarget(
            name="prediction_explanation_latest",
            path=root / "analysis" / "explanation" / "prediction_explanation_latest.json",
            required=True,
        ),
        ArtifactTarget(
            name="global_status_latest",
            path=root / "analysis" / "global_status_latest.json",
            required=True,
        ),
        ArtifactTarget(
            name="published_prediction_latest",
            path=root / "data" / "prediction" / "prediction_latest.json",
            required=False,
        ),
        ArtifactTarget(
            name="published_prediction_explanation_latest",
            path=root / "data" / "explanation" / "prediction_explanation_latest.json",
            required=False,
        ),
        ArtifactTarget(
            name="prediction_history_index",
            path=root / "analysis" / "prediction" / "prediction_history_index.json",
            required=False,
            expects_as_of=False,
        ),
    ]

    artifacts = [artifact_status(target) for target in targets]
    summary = summarize_artifacts(artifacts)
    overall_status = derive_overall_status(summary)

    stale_candidates: list[dict[str, Any]] = []
    if expected_date:
        for item in artifacts:
            as_of = item.get("as_of")
            if as_of and as_of != expected_date:
                stale_candidates.append(
                    {
                        "name": item["name"],
                        "as_of": as_of,
                        "expected_date": expected_date,
                    }
                )

        if stale_candidates and overall_status == "OK":
            overall_status = "WARN"

    deploy_readiness = {
        "eligible": overall_status == "OK" and not stale_candidates,
        "reason": "ok",
    }

    if overall_status == "FAIL":
        deploy_readiness["eligible"] = False
        deploy_readiness["reason"] = "required_artifact_failed"
    elif stale_candidates:
        deploy_readiness["eligible"] = False
        deploy_readiness["reason"] = "stale_artifact_detected"

    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    return {
        "schema_version": "1.0",
        "generated_at_utc": now_utc,
        "root": str(root),
        "expected_date": expected_date,
        "overall_status": overall_status,
        "summary": summary,
        "deploy_readiness": deploy_readiness,
        "artifacts": artifacts,
        "stale_candidates": stale_candidates,
        "global_status_snapshot": load_optional_global_status(root),
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
        },
        "meaning": {
            "overall_status": "Operational health of generated pipeline artifacts, not geopolitical risk.",
            "deploy_readiness": "Whether artifacts appear safe to deploy from an operations perspective. This is not authority to deploy.",
            "stale_candidates": "Artifacts whose as_of differs from the expected date.",
        },
    }


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if pretty:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    path.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build GenesisPrediction operational pipeline health summary."
    )
    parser.add_argument("--root", required=True, help="Repository root")
    parser.add_argument("--date", default="", help="Expected date YYYY-MM-DD. Optional.")
    parser.add_argument(
        "--out",
        default="analysis/ops/pipeline_health_latest.json",
        help="Output path relative to root unless absolute.",
    )
    parser.add_argument("--pretty", action="store_true", help="Write pretty JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    expected_date = args.date.strip() or None
    out_path = Path(args.out)

    if not out_path.is_absolute():
        out_path = root / out_path

    payload = build_pipeline_health(root=root, expected_date=expected_date)
    write_json(out_path, payload, pretty=args.pretty)

    print("=== GenesisPrediction Pipeline Health Summary ===")
    print(f"root          : {root}")
    print(f"expected_date : {expected_date}")
    print(f"out           : {out_path}")
    print(f"status        : {payload['overall_status']}")
    print(f"deploy_ready  : {payload['deploy_readiness']['eligible']}")
    print(f"reason        : {payload['deploy_readiness']['reason']}")
    print("[DONE] pipeline health summary written")

    if payload["overall_status"] == "FAIL":
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

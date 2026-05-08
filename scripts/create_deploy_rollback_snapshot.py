#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SnapshotTarget:
    label: str
    path: Path
    required: bool


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")


def read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    encodings = ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be")

    for encoding in encodings:
        try:
            data = json.loads(path.read_text(encoding=encoding))
            if isinstance(data, dict):
                return data
            return None
        except Exception:
            continue

    return None


def extract_as_of(path: Path) -> str | None:
    data = read_json_object(path)
    if not isinstance(data, dict):
        return None

    value = data.get("as_of")
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    return text[:10] if len(text) >= 10 else text


def iter_files(path: Path) -> list[Path]:
    if not path.exists():
        return []

    if path.is_file():
        return [path]

    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.is_file())

    return []


def add_target_to_zip(
    zf: zipfile.ZipFile,
    root: Path,
    target: SnapshotTarget,
    base_arc_prefix: str,
) -> dict[str, Any]:
    exists = target.path.exists()
    files = iter_files(target.path)

    item: dict[str, Any] = {
        "label": target.label,
        "path": str(target.path),
        "required": target.required,
        "exists": exists,
        "file_count": len(files),
        "status": "ok" if exists else ("fail" if target.required else "warn"),
        "as_of": extract_as_of(target.path) if target.path.is_file() else None,
        "files": [],
    }

    if not exists:
        return item

    for file_path in files:
        rel_to_root = file_path.resolve().relative_to(root)
        arcname = str(Path(base_arc_prefix) / rel_to_root).replace("\\", "/")

        zf.write(file_path, arcname=arcname)

        stat = file_path.stat()
        item["files"].append(
            {
                "path": str(file_path),
                "archive_path": arcname,
                "size_bytes": stat.st_size,
                "sha256": sha256_file(file_path),
            }
        )

    return item


def build_targets(root: Path, include_payload: bool) -> list[SnapshotTarget]:
    targets = [
        SnapshotTarget(
            label="prediction_latest",
            path=root / "analysis" / "prediction" / "prediction_latest.json",
            required=True,
        ),
        SnapshotTarget(
            label="prediction_explanation_latest",
            path=root / "analysis" / "explanation" / "prediction_explanation_latest.json",
            required=True,
        ),
        SnapshotTarget(
            label="global_status_latest",
            path=root / "analysis" / "global_status_latest.json",
            required=True,
        ),
        SnapshotTarget(
            label="pipeline_health_latest",
            path=root / "analysis" / "ops" / "pipeline_health_latest.json",
            required=False,
        ),
        SnapshotTarget(
            label="published_prediction",
            path=root / "data" / "prediction",
            required=False,
        ),
        SnapshotTarget(
            label="published_explanation",
            path=root / "data" / "explanation",
            required=False,
        ),
    ]

    if include_payload:
        targets.append(
            SnapshotTarget(
                label="deploy_payload",
                path=root / "dist" / "labos_deploy",
                required=False,
            )
        )

    return targets


def prune_old_snapshots(snapshot_root: Path, keep: int) -> list[str]:
    if keep <= 0 or not snapshot_root.exists():
        return []

    zip_files = sorted(
        snapshot_root.glob("deploy_snapshot_*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    removed: list[str] = []

    for old_zip in zip_files[keep:]:
        manifest = old_zip.with_suffix(".manifest.json")

        try:
            old_zip.unlink()
            removed.append(str(old_zip))
        except FileNotFoundError:
            pass

        if manifest.exists():
            try:
                manifest.unlink()
                removed.append(str(manifest))
            except FileNotFoundError:
                pass

    return removed


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if pretty:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    path.write_text(text + "\n", encoding="utf-8")


def build_deploy_snapshot(
    root: Path,
    out_dir: Path,
    expected_date: str | None,
    include_payload: bool,
    keep: int,
    pretty: bool,
) -> tuple[Path, Path, dict[str, Any]]:
    stamp = utc_stamp()
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_path = out_dir / f"deploy_snapshot_{stamp}.zip"
    manifest_path = out_dir / f"deploy_snapshot_{stamp}.manifest.json"

    targets = build_targets(root=root, include_payload=include_payload)

    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "root": str(root),
        "expected_date": expected_date,
        "snapshot_zip": str(zip_path),
        "snapshot_manifest": str(manifest_path),
        "include_payload": include_payload,
        "targets": [],
        "summary": {
            "total_targets": len(targets),
            "ok": 0,
            "warn": 0,
            "fail": 0,
            "file_count": 0,
        },
        "retention": {
            "keep": keep,
            "removed": [],
        },
        "meaning": {
            "snapshot": "Rollback assistance artifact. It is not source of truth and does not authorize rollback.",
            "manifest": "Integrity and file listing for the snapshot archive.",
        },
    }

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for target in targets:
            item = add_target_to_zip(
                zf=zf,
                root=root,
                target=target,
                base_arc_prefix="snapshot",
            )
            manifest["targets"].append(item)

            status = item["status"]
            if status == "ok":
                manifest["summary"]["ok"] += 1
            elif status == "warn":
                manifest["summary"]["warn"] += 1
            else:
                manifest["summary"]["fail"] += 1

            manifest["summary"]["file_count"] += item["file_count"]

        zf.writestr(
            "snapshot/README_ROLLBACK_SNAPSHOT.txt",
            "\n".join(
                [
                    "GenesisPrediction rollback snapshot",
                    "",
                    "Purpose:",
                    "- Preserve deploy-relevant generated artifacts for recovery assistance.",
                    "- This archive is not the source of truth.",
                    "- Git + analysis remain authoritative.",
                    "",
                    "Use:",
                    "- Inspect manifest before restoring anything.",
                    "- Prefer Git/rebuild recovery before manual snapshot restoration.",
                    "- Never treat snapshot presence as deploy or rollback authority.",
                    "",
                ]
            ),
        )

    manifest["snapshot_sha256"] = sha256_file(zip_path)
    write_json(manifest_path, manifest, pretty=pretty)

    removed = prune_old_snapshots(out_dir, keep=keep)
    manifest["retention"]["removed"] = removed
    write_json(manifest_path, manifest, pretty=pretty)

    return zip_path, manifest_path, manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create rollback assistance snapshot for GenesisPrediction deploy-relevant artifacts."
    )
    parser.add_argument("--root", required=True, help="Repository root")
    parser.add_argument(
        "--out-dir",
        default="analysis/ops/deploy_snapshots",
        help="Output directory relative to root unless absolute.",
    )
    parser.add_argument("--date", default="", help="Expected artifact date YYYY-MM-DD. Optional.")
    parser.add_argument(
        "--include-payload",
        action="store_true",
        help="Include dist/labos_deploy if present.",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=10,
        help="Number of latest snapshot zip files to retain.",
    )
    parser.add_argument("--pretty", action="store_true", help="Write pretty manifest JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out_dir)

    if not out_dir.is_absolute():
        out_dir = root / out_dir

    expected_date = args.date.strip() or None

    zip_path, manifest_path, manifest = build_deploy_snapshot(
        root=root,
        out_dir=out_dir,
        expected_date=expected_date,
        include_payload=args.include_payload,
        keep=args.keep,
        pretty=args.pretty,
    )

    print("=== GenesisPrediction Deploy Rollback Snapshot ===")
    print(f"root          : {root}")
    print(f"expected_date : {expected_date}")
    print(f"zip           : {zip_path}")
    print(f"manifest      : {manifest_path}")
    print(f"sha256        : {manifest['snapshot_sha256']}")
    print(f"targets       : {manifest['summary']['total_targets']}")
    print(f"files         : {manifest['summary']['file_count']}")
    print(f"ok            : {manifest['summary']['ok']}")
    print(f"warn          : {manifest['summary']['warn']}")
    print(f"fail          : {manifest['summary']['fail']}")
    print(f"removed       : {len(manifest['retention']['removed'])}")

    if manifest["summary"]["fail"] > 0:
        print("[FAILED] required snapshot targets are missing or invalid")
        return 1

    print("[DONE] rollback snapshot created")
    return 0


if __name__ == "__main__":
    sys.exit(main())

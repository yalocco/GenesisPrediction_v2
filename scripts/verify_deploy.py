#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_json_url(url: str, timeout: int) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GenesisPrediction-DeployVerify/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return json.loads(resp.read().decode(charset))


def stable_json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(data: Any) -> str:
    return hashlib.sha256(stable_json_text(data).encode("utf-8")).hexdigest()


def compare_artifact(name: str, local_path: Path, remote_url: str, timeout: int) -> tuple[bool, str]:
    local_data = load_json_file(local_path)
    remote_data = load_json_url(remote_url, timeout=timeout)

    local_hash = stable_hash(local_data)
    remote_hash = stable_hash(remote_data)

    if local_hash == remote_hash:
        return True, f"[OK] {name}: exact match"

    local_as_of = local_data.get("as_of") if isinstance(local_data, dict) else None
    remote_as_of = remote_data.get("as_of") if isinstance(remote_data, dict) else None

    details = [
        f"[NG] {name}: content mismatch",
        f"  local_path : {local_path}",
        f"  remote_url : {remote_url}",
        f"  local_hash : {local_hash}",
        f"  remote_hash: {remote_hash}",
    ]

    if local_as_of is not None or remote_as_of is not None:
        details.append(f"  local_as_of: {local_as_of}")
        details.append(f"  remote_as_of: {remote_as_of}")

    return False, "\n".join(details)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify LABOS deployed JSON artifacts against local artifacts.")
    parser.add_argument("--root", required=True, help="Repository root")
    parser.add_argument("--base-url", default="https://labos.soma-samui.com", help="Deployed site base URL")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    base_url = args.base_url.rstrip("/")

    targets = [
        (
            "prediction_latest",
            root / "analysis" / "prediction" / "prediction_latest.json",
            f"{base_url}/data/prediction/prediction_latest.json",
        ),
        (
            "prediction_explanation_latest",
            root / "analysis" / "explanation" / "prediction_explanation_latest.json",
            f"{base_url}/data/explanation/prediction_explanation_latest.json",
        ),
    ]

    all_ok = True

    print("=== VERIFY DEPLOY ===")
    print(f"ROOT     : {root}")
    print(f"BASE URL : {base_url}")

    for name, local_path, remote_url in targets:
        if not local_path.exists():
            print(f"[NG] Missing local artifact: {local_path}")
            all_ok = False
            continue

        try:
            ok, message = compare_artifact(name, local_path, remote_url, timeout=args.timeout)
            print(message)
            if not ok:
                all_ok = False
        except urllib.error.URLError as e:
            print(f"[NG] {name}: remote fetch failed: {remote_url}")
            print(f"  reason: {e}")
            all_ok = False
        except Exception as e:
            print(f"[NG] {name}: unexpected error")
            print(f"  reason: {e}")
            all_ok = False

    if all_ok:
        print("[DONE] Deploy verification passed")
        return 0

    print("[FAILED] Deploy verification failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())

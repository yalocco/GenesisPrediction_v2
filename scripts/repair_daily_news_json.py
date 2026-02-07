# scripts/repair_daily_news_json.py
# Repair broken daily news JSON files that contain "extra data" (concatenated JSON, log garbage, etc.)
#
# Typical symptom:
#   json.decoder.JSONDecodeError: Extra data: line ... column ... (char ...)
#
# This script:
# - reads file as text (UTF-8; tolerant)
# - strips ANSI escape sequences
# - extracts the most plausible JSON payload (from first '{' or '[' to last '}' or ']')
# - if still failing, trims the end progressively until json.loads succeeds
# - writes fixed JSON back (with a .bak backup by default)
#
# Usage:
#   .\.venv\Scripts\python.exe scripts\repair_daily_news_json.py data/world_politics/2026-02-05.json
#   .\.venv\Scripts\python.exe scripts\repair_daily_news_json.py data/world_politics/2026-02-05.json --no-backup
#
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Optional, Tuple


ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def read_text_loose(path: Path) -> str:
    b = path.read_bytes()
    # Try utf-8-sig first, then fallback decode errors ignored.
    try:
        s = b.decode("utf-8-sig")
    except Exception:
        s = b.decode("utf-8", errors="ignore")
    return s


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def extract_json_payload(s: str) -> Optional[str]:
    if not s or not s.strip():
        return None
    s = strip_ansi(s).replace("\r\n", "\n")

    i_obj = s.find("{")
    i_arr = s.find("[")
    if i_obj < 0 and i_arr < 0:
        return None

    if i_obj >= 0 and i_arr >= 0:
        start = min(i_obj, i_arr)
    else:
        start = i_obj if i_obj >= 0 else i_arr

    end_obj = s.rfind("}")
    end_arr = s.rfind("]")
    if end_obj < 0 and end_arr < 0:
        return None
    end = max(end_obj, end_arr)

    if end <= start:
        return None
    return s[start : end + 1]


def try_load(payload: str) -> Tuple[bool, Optional[object], Optional[str]]:
    try:
        return True, json.loads(payload), None
    except Exception as e:
        return False, None, str(e)


def trim_until_load(payload: str, min_len: int = 200) -> Tuple[Optional[object], str]:
    """
    If payload ends with extra garbage, progressively trim from the end until json.loads works.
    This is robust for 'Extra data' and accidental trailing logs.
    """
    p = payload.rstrip()
    ok, obj, err = try_load(p)
    if ok:
        return obj, "ok"

    # Progressive trimming (bounded)
    end = len(p)
    # Trim up to 200k chars in worst case; if file is huge it's likely not a daily-news JSON anyway.
    max_steps = min(200_000, end - min_len) if end > min_len else 0

    for step in range(1, max_steps + 1):
        cand = p[: end - step].rstrip()
        # Quick heuristic: end should likely be '}' or ']'
        if not cand:
            break
        last = cand[-1]
        if last not in ("}", "]"):
            continue
        ok, obj, _ = try_load(cand)
        if ok:
            return obj, f"trimmed_end_chars={step}"

    raise RuntimeError(f"Could not repair JSON by trimming. Last error: {err}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=str, help="Path to daily news JSON file (e.g., data/world_politics/2026-02-05.json)")
    ap.add_argument("--no-backup", action="store_true", help="Do not create a .bak backup")
    ap.add_argument("--compact", action="store_true", help="Write compact JSON (no indentation)")
    args = ap.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"[ERR] not found: {path}")
        return 2
    if not path.is_file():
        print(f"[ERR] not a file: {path}")
        return 2

    raw = read_text_loose(path)
    payload = extract_json_payload(raw)
    if payload is None:
        print(f"[ERR] no JSON payload detected in: {path}")
        return 3

    try:
        obj, note = trim_until_load(payload)
    except Exception as e:
        print(f"[ERR] repair failed: {path}")
        print(f"      {e}")
        return 4

    # Backup
    if not args.no_backup:
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            bak.write_bytes(path.read_bytes())
            print(f"[OK] backup created: {bak}")
        else:
            print(f"[WARN] backup exists (kept): {bak}")

    # Write fixed JSON
    if args.compact:
        out = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    else:
        out = json.dumps(obj, ensure_ascii=False, indent=2)

    path.write_text(out + "\n", encoding="utf-8")
    print(f"[OK] repaired: {path} ({note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

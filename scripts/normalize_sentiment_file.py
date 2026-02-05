from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_path", required=True)
    ap.add_argument("--out", dest="out_path", required=True)
    args = ap.parse_args()

    inp = Path(args.in_path)
    outp = Path(args.out_path)

    if not inp.exists():
        raise SystemExit(f"[ERR] missing: {inp}")

    data = json.loads(inp.read_text(encoding="utf-8"))

    # minimal normalization: ensure numbers are floats and presence of today keys
    today = data.get("today") or {}
    def f(x):
        try:
            return float(x)
        except Exception:
            return 0.0

    today_norm = {
        "articles": int(today.get("articles") or 0),
        "risk": f(today.get("risk")),
        "positive": f(today.get("positive")),
        "uncertainty": f(today.get("uncertainty")),
    }
    data["today"] = today_norm

    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] normalized file: {inp} -> {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

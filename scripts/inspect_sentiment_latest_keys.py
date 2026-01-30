# scripts/inspect_sentiment_latest_keys.py
from __future__ import annotations

import json
from pathlib import Path

P = Path("data/world_politics/analysis/sentiment_latest.json")

def main() -> int:
    if not P.exists():
        print(f"[ERR] not found: {P}")
        return 1

    d = json.loads(P.read_text(encoding="utf-8"))
    items = d.get("items") or []
    print(f"[OK] date={d.get('date')} items={len(items)}")

    if not items:
        print("[ERR] items is empty")
        return 2

    it = items[0]
    keys = sorted(list(it.keys()))
    print("\n[TOP-LEVEL KEYS]")
    for k in keys:
        print(" ", k)

    # show common candidate paths
    print("\n[CHECK VALUES]")
    for k in ["net","risk","pos","unc","risk_score","pos_score","unc_score","riskScore","posScore","uncScore"]:
        if k in it:
            print(f"  {k} = {it.get(k)!r}")

    for nest in ["sentiment", "scores", "sent"]:
        v = it.get(nest)
        if isinstance(v, dict):
            print(f"\n[{nest}.* KEYS]")
            for k in sorted(v.keys()):
                print(" ", k)
            for k in ["net","risk","pos","unc","risk_score","pos_score","unc_score","riskScore","posScore","uncScore"]:
                if k in v:
                    print(f"  {nest}.{k} = {v.get(k)!r}")
        else:
            print(f"\n[{nest}] = {type(v).__name__} {v!r}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

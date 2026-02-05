# scripts/normalize_sentiment_latest.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_IN = Path("data/world_politics/analysis/sentiment_latest.json")
DEFAULT_OUT = Path("data/world_politics/analysis/sentiment_latest.json")


def _get_number(d: Dict[str, Any], keys: List[str], default: float = 0.0) -> float:
    for k in keys:
        v = d.get(k, None)
        if isinstance(v, (int, float)):
            return float(v)
        # strings like "0.123"
        if isinstance(v, str):
            try:
                return float(v)
            except Exception:
                pass
    return float(default)


def _extract_item_scores(item: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Returns (risk, positive, uncertainty) for one item.
    Accept multiple schema variants.
    """
    s = item.get("sentiment", {})
    if not isinstance(s, dict):
        s = {}

    risk = _get_number(s, ["risk", "riskScore", "negative", "negative_score"], 0.0)
    pos = _get_number(s, ["positive", "pos", "posScore", "positive_score"], 0.0)
    unc = _get_number(s, ["uncertainty", "unc", "uncScore", "uncertainty_score"], 0.0)

    # Some pipelines store net only; derive risk/pos if needed
    net = _get_number(s, ["net", "score"], 0.0)
    if risk == 0.0 and pos == 0.0 and net != 0.0:
        risk = max(0.0, -net)
        pos = max(0.0, net)

    return (risk, pos, unc)


def _summarize_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(items)
    if n == 0:
        return {
            "articles": 0,
            "risk": 0.0,
            "positive": 0.0,
            "uncertainty": 0.0,
        }

    r_sum = 0.0
    p_sum = 0.0
    u_sum = 0.0
    for it in items:
        r, p, u = _extract_item_scores(it if isinstance(it, dict) else {})
        r_sum += r
        p_sum += p
        u_sum += u

    # mean
    risk = r_sum / n
    pos = p_sum / n
    unc = u_sum / n

    return {
        "articles": n,
        "risk": risk,
        "positive": pos,
        "uncertainty": unc,
    }


def _normalize_today(root: Dict[str, Any]) -> None:
    """
    Ensure root['today'] exists and has usable numeric summary.
    If missing/invalid, compute from root['items'].
    Also ensure alias keys riskScore/posScore/uncScore exist.
    """
    items = root.get("items", [])
    if not isinstance(items, list):
        items = []

    today = root.get("today", {})
    if not isinstance(today, dict):
        today = {}

    # detect "broken" today: missing keys OR all None
    articles = today.get("articles", None)
    risk = today.get("risk", None)
    pos = today.get("positive", None)
    unc = today.get("uncertainty", None)

    broken = False
    if not isinstance(articles, int):
        broken = True
    if not isinstance(risk, (int, float)):
        broken = True
    if not isinstance(pos, (int, float)):
        broken = True
    if not isinstance(unc, (int, float)):
        broken = True

    # also treat "articles=0 but items exist" as broken
    if isinstance(articles, int) and articles == 0 and len(items) > 0:
        broken = True

    if broken:
        s = _summarize_items([it for it in items if isinstance(it, dict)])
        today["articles"] = int(s["articles"])
        today["risk"] = float(s["risk"])
        today["positive"] = float(s["positive"])
        today["uncertainty"] = float(s["uncertainty"])

    # Add aliases used by some UIs
    today["riskScore"] = float(_get_number(today, ["riskScore", "risk"], 0.0))
    today["posScore"] = float(_get_number(today, ["posScore", "positive"], 0.0))
    today["uncScore"] = float(_get_number(today, ["uncScore", "uncertainty"], 0.0))

    root["today"] = today


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(DEFAULT_IN))
    ap.add_argument("--out", dest="out", default=str(DEFAULT_OUT))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)

    if not inp.exists():
        raise SystemExit(f"[ERR] missing input: {inp}")

    root = json.loads(inp.read_text(encoding="utf-8"))
    if not isinstance(root, dict):
        raise SystemExit("[ERR] sentiment_latest.json is not an object")

    _normalize_today(root)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(root, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.quiet:
        t = root.get("today", {})
        print(f"[OK] normalized: {out}")
        print(f"  articles={t.get('articles')} risk={t.get('risk')} positive={t.get('positive')} uncertainty={t.get('uncertainty')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

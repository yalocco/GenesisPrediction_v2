# scripts/normalize_sentiment_latest.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

IN_PATH = Path("data/world_politics/analysis/sentiment_latest.json")


def _as_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _pick_first(d: Dict[str, Any], keys: Tuple[str, ...]) -> Optional[Any]:
    for k in keys:
        if k in d:
            return d[k]
    return None


def _extract(doc: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Return (risk, pos, unc, net) from many possible layouts.
    """
    # nested first
    for base in ("scores", "sentiment"):
        obj = doc.get(base)
        if isinstance(obj, dict):
            risk = _pick_first(obj, ("risk", "risk_score", "riskScore"))
            pos  = _pick_first(obj, ("pos", "positive", "pos_score", "posScore", "positive_score", "positiveScore"))
            unc  = _pick_first(obj, ("unc", "uncertainty", "unc_score", "uncScore", "uncertainty_score", "uncertaintyScore"))
            net  = _pick_first(obj, ("net", "score", "raw_score", "rawScore", "sentiment_score"))
            return _as_float(risk), _as_float(pos), _as_float(unc), _as_float(net)

    # top-level
    risk = _pick_first(doc, ("risk", "risk_score", "riskScore"))
    pos  = _pick_first(doc, ("pos", "positive", "pos_score", "posScore", "positive_score", "positiveScore"))
    unc  = _pick_first(doc, ("unc", "uncertainty", "unc_score", "uncScore", "uncertainty_score", "uncertaintyScore"))
    net  = _pick_first(doc, ("net", "score", "raw_score", "rawScore", "sentiment_score"))

    # fallback summary (your generator uses this)
    if risk is None and pos is None and unc is None:
        summ = doc.get("summary")
        if isinstance(summ, dict):
            # fallback_score is basically "pos"
            pos = summ.get("fallback_score", pos)
            # fallback_unc is basically "unc"
            unc = summ.get("fallback_unc", unc)
            # risk doesn't exist in fallback -> treat as 0
            risk = 0.0 if risk is None else risk

    return _as_float(risk), _as_float(pos), _as_float(unc), _as_float(net)


def main() -> int:
    if not IN_PATH.exists():
        raise FileNotFoundError(f"not found: {IN_PATH}")

    doc = json.loads(IN_PATH.read_text(encoding="utf-8"))

    # Keep existing date/items if any
    date = doc.get("date")
    items = doc.get("items")

    risk, pos, unc, net = _extract(doc)

    # --- Top-level keys (GUI friendly) ---
    if date is not None:
        doc["date"] = date
    if items is not None:
        doc["items"] = items

    if risk is not None:
        doc["risk"] = risk
        doc["risk_score"] = risk
        doc["riskScore"] = risk

    if pos is not None:
        # provide every common alias
        doc["positive"] = pos
        doc["pos"] = pos
        doc["pos_score"] = pos
        doc["posScore"] = pos
        doc["positive_score"] = pos
        doc["positiveScore"] = pos

    if unc is not None:
        doc["uncertainty"] = unc
        doc["unc"] = unc
        doc["unc_score"] = unc
        doc["uncScore"] = unc
        doc["uncertainty_score"] = unc
        doc["uncertaintyScore"] = unc

    if net is not None:
        doc["net"] = net
        doc["sentiment_score"] = net

    # --- Stable nested form too ---
    doc.setdefault("scores", {})
    if isinstance(doc["scores"], dict):
        if risk is not None:
            doc["scores"]["risk"] = risk
            doc["scores"]["risk_score"] = risk
        if pos is not None:
            doc["scores"]["positive"] = pos
            doc["scores"]["pos"] = pos
            doc["scores"]["pos_score"] = pos
        if unc is not None:
            doc["scores"]["uncertainty"] = unc
            doc["scores"]["unc"] = unc
            doc["scores"]["unc_score"] = unc
        if net is not None:
            doc["scores"]["net"] = net

    IN_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[OK] normalized:", str(IN_PATH))
    print("  date =", doc.get("date"))
    print("  items =", doc.get("items"))
    print("  risk =", doc.get("risk"))
    print("  pos/positive =", doc.get("pos"), doc.get("positive"))
    print("  unc/uncertainty =", doc.get("unc"), doc.get("uncertainty"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

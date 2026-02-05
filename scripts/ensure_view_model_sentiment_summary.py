# scripts/ensure_view_model_sentiment_summary.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional


SENT_LATEST = Path("data/world_politics/analysis/sentiment_latest.json")
VM_DATE = Path("data/digest/view")  # /{date}.json
VM_LATEST_1 = Path("data/digest/view_model_latest.json")
VM_LATEST_2 = Path("data/digest/view/view_model_latest.json")


def _num(v: Any, default: float = 0.0) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except Exception:
            return float(default)
    return float(default)


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(p: Path, obj: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _pick_today_summary(sent: Dict[str, Any]) -> Dict[str, Any]:
    today = sent.get("today", {})
    if not isinstance(today, dict):
        today = {}

    # prefer canonical keys
    articles = today.get("articles", None)
    risk = today.get("risk", None)
    pos = today.get("positive", None)
    unc = today.get("uncertainty", None)

    # fallback aliases
    if articles is None:
        articles = today.get("n", today.get("count", 0))
    if risk is None:
        risk = today.get("riskScore", 0.0)
    if pos is None:
        pos = today.get("posScore", 0.0)
    if unc is None:
        unc = today.get("uncScore", 0.0)

    # ensure types
    try:
        articles_i = int(articles) if articles is not None else 0
    except Exception:
        articles_i = 0

    return {
        "articles": articles_i,
        "risk": _num(risk, 0.0),
        "positive": _num(pos, 0.0),
        "uncertainty": _num(unc, 0.0),
        # aliases (UIがどっち読んでもOK)
        "riskScore": _num(today.get("riskScore", risk), 0.0),
        "posScore": _num(today.get("posScore", pos), 0.0),
        "uncScore": _num(today.get("uncScore", unc), 0.0),
    }


def _patch_view_model(vm: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Try multiple placements (schema variations):
    - vm["sentiment_summary"]
    - vm["today"]["sentiment"]
    - vm["today"]["sentiment_summary"]
    """
    vm.setdefault("sentiment_summary", {})
    if isinstance(vm["sentiment_summary"], dict):
        vm["sentiment_summary"].update(summary)

    today = vm.get("today", {})
    if isinstance(today, dict):
        today.setdefault("sentiment", {})
        if isinstance(today["sentiment"], dict):
            today["sentiment"].update(summary)

        today.setdefault("sentiment_summary", {})
        if isinstance(today["sentiment_summary"], dict):
            today["sentiment_summary"].update(summary)

        vm["today"] = today

    return vm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    date = args.date

    vm_path = VM_DATE / f"{date}.json"
    if not vm_path.exists():
        raise SystemExit(f"[ERR] missing view model: {vm_path}")

    if not SENT_LATEST.exists():
        raise SystemExit(f"[ERR] missing sentiment_latest: {SENT_LATEST}")

    sent = _load_json(SENT_LATEST)
    vm = _load_json(vm_path)

    summary = _pick_today_summary(sent)
    vm = _patch_view_model(vm, summary)

    _write_json(vm_path, vm)
    # “latest” pointers も同じ内容にしておく（GUIの読み先ブレ対策）
    _write_json(VM_LATEST_1, vm)
    _write_json(VM_LATEST_2, vm)

    if not args.quiet:
        print(f"[OK] patched: {vm_path}")
        print(f"[OK] patched: {VM_LATEST_1}")
        print(f"[OK] patched: {VM_LATEST_2}")
        print(f"  summary: articles={summary['articles']} risk={summary['risk']:.6f} positive={summary['positive']:.6f} uncertainty={summary['uncertainty']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime


ANALYSIS_DIR = Path("data/world_politics/analysis")


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_date(s: str) -> str | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s).strftime("%Y-%m-%d")
    except Exception:
        return s


def compute_confidence_analog_delta(historical_analogs) -> tuple[float, str]:
    """
    historical_analogs: list[dict] with "score"
    Returns (delta, reason), delta in [-0.05, +0.05]
      avg=0.0 -> -0.05
      avg=0.5 ->  0.00
      avg=1.0 -> +0.05
    """
    if not historical_analogs:
        return 0.0, "no historical_analogs"

    top = historical_analogs[:3]
    scores: list[float] = []
    for a in top:
        try:
            s = float(a.get("score", 0.0))
        except Exception:
            s = 0.0
        scores.append(s)

    if not scores:
        return 0.0, "no scores"

    avg = sum(scores) / len(scores)
    delta = _clamp((avg - 0.5) * 0.1, -0.05, +0.05)
    reason = f"analog avg score={avg:.3f} -> delta={delta:+.3f}"
    return delta, reason


def find_target_file(date_str: str | None = None) -> Path | None:
    files = sorted(ANALYSIS_DIR.glob("daily_summary_*.json"))
    if not files:
        return None

    if date_str:
        candidate = ANALYSIS_DIR / f"daily_summary_{date_str}.json"
        if candidate.exists():
            return candidate

    return max(files, key=lambda p: p.stat().st_mtime)


def apply_to_one(path: Path) -> tuple[bool, str]:
    """
    Idempotent patch:
    - Save confidence_analog_delta / reason every time
    - Save confidence_analog_base once (original confidence before any analog adjustment)
    - Set confidence = clamp(base + delta) every time (no drift)
    """
    doc = _read_json(path)

    meta = doc.get("meta") or {}
    date_str = _normalize_date(meta.get("date") or "")

    analogs = doc.get("historical_analogs") or []
    delta, reason = compute_confidence_analog_delta(analogs)

    # Read confidence field (support both keys)
    conf = _safe_float(doc.get("confidence_of_hypotheses"))
    conf_key = "confidence_of_hypotheses"
    if conf is None:
        conf = _safe_float(doc.get("confidence"))
        conf_key = "confidence"

    # Always store explanation fields (even if delta=0)
    doc["confidence_analog_delta"] = float(delta)
    doc["confidence_analog_reason"] = reason

    # If there is no confidence at all, only write delta/reason
    if conf is None:
        _write_json(path, doc)
        return True, f"[OK] patched {path.name} ({date_str or 'unknown-date'}): no confidence field; wrote delta/reason only"

    # Idempotency: base is frozen once
    base = _safe_float(doc.get("confidence_analog_base"))
    if base is None:
        base = float(conf)
        doc["confidence_analog_base"] = float(base)

    new_conf = _clamp(float(base) + float(delta), 0.0, 1.0)
    before = _safe_float(doc.get(conf_key), base)

    doc[conf_key] = float(new_conf)

    _write_json(path, doc)
    return True, (
        f"[OK] patched {path.name} ({date_str or 'unknown-date'}): "
        f"{conf_key} {float(before):.4f} -> {new_conf:.4f} (base {float(base):.4f}, delta {delta:+.3f})"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="", help="YYYY-MM-DD (optional). If missing, patch latest.")
    args = parser.parse_args()

    target = find_target_file(args.date.strip() or None)
    if not target:
        print("[WARN] no daily_summary_*.json found")
        return

    _changed, msg = apply_to_one(target)
    print(msg)


if __name__ == "__main__":
    main()

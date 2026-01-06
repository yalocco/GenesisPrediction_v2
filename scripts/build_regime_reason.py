from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ANALYSIS_DIR = Path("data") / "world_politics" / "analysis"
TEMPLATES_PATH = Path("configs") / "regime_reason_templates.json"

DAILY_RE = re.compile(r"^daily_summary_(\d{4}-\d{2}-\d{2})\.json$")

def _read_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))

def _write_json(p: Path, obj: Dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

def _safe_str(x: Any, default: str = "") -> str:
    return str(x) if x is not None else default

def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def _pick_anchors_top(daily: Dict[str, Any], n: int) -> List[str]:
    anchors = daily.get("anchors") or {}
    if not isinstance(anchors, dict):
        return []

    tokens = []
    for key in ("top_tokens", "hints"):
        for t in _as_list(anchors.get(key)):
            s = _safe_str(t).strip()
            if s and s not in tokens:
                tokens.append(s)

    return tokens[:n]

def _pick_top_hypothesis(daily: Dict[str, Any]) -> str:
    hyps = daily.get("change_reason_hypotheses")
    if isinstance(hyps, list) and hyps:
        h0 = hyps[0]
        if isinstance(h0, dict):
            return _safe_str(h0.get("hypothesis", "")).strip()
        return _safe_str(h0).strip()
    if isinstance(hyps, str):
        return hyps.strip()
    return ""

def _infer_regime(conf: float, churn: float) -> str:
    if conf >= 0.65 and churn >= 0.12:
        return "rotation (high conf/high churn)"
    if conf >= 0.65:
        return "stable (high conf/low churn)"
    if churn >= 0.12:
        return "noisy (low conf/high churn)"
    return "quiet (low conf/low churn)"

@dataclass
class Templates:
    regime_templates: Dict[str, List[str]]
    transition_templates: List[str]
    short_templates: List[str]
    defaults: Dict[str, Any]

def _load_templates(path: Path) -> Templates:
    doc = _read_json(path)
    return Templates(
        regime_templates={k: _as_list(v) for k, v in doc["regime_templates"].items()},
        transition_templates=_as_list(doc.get("transition_templates")),
        short_templates=_as_list(doc.get("short_templates")),
        defaults=doc.get("defaults", {}),
    )

def _find_daily_summaries() -> List[Tuple[str, Path]]:
    out = []
    for p in ANALYSIS_DIR.glob("daily_summary_*.json"):
        m = DAILY_RE.match(p.name)
        if m:
            out.append((m.group(1), p))
    return sorted(out)

def main():
    templates = _load_templates(TEMPLATES_PATH)
    summaries = _find_daily_summaries()

    prev_date = None
    prev_daily = None

    for date, path in summaries:
        daily = _read_json(path)

        conf = _safe_float(daily.get("confidence_of_hypotheses"))
        churn = _safe_float(daily.get("churn"))
        regime = daily.get("regime") or _infer_regime(conf, churn)

        anchors = _pick_anchors_top(daily, 6)
        hypo = _pick_top_hypothesis(daily)

        ctx = {
            "date": date,
            "regime": regime,
            "prev_date": prev_date or "",
            "prev_regime": prev_daily.get("regime") if prev_daily else "",
            "conf": f"{conf:.2f}",
            "prev_conf": f"{_safe_float(prev_daily.get('confidence_of_hypotheses')):.2f}" if prev_daily else "",
            "churn": f"{churn:.2f}",
            "prev_churn": f"{_safe_float(prev_daily.get('churn')):.2f}" if prev_daily else "",
            "anchors_top": ", ".join(anchors),
            "top_hypo": hypo,
        }

        if prev_daily and templates.transition_templates:
            reason = templates.transition_templates[0].format(**ctx)
        else:
            reason = templates.regime_templates.get(regime, [""])[0].format(**ctx)

        out = {
            "date": date,
            "regime": regime,
            "reason": reason,
            "reason_short": templates.short_templates[0].format(**ctx),
        }

        out_path = ANALYSIS_DIR / f"regime_reason_{date}.json"
        _write_json(out_path, out)

        prev_date = date
        prev_daily = daily

    print("[OK] regime_reason generated")

if __name__ == "__main__":
    main()

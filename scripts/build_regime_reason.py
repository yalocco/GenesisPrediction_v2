from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, date as date_type
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =========================
# Paths / constants
# =========================
ANALYSIS_DIR = Path("data") / "world_politics" / "analysis"
TEMPLATES_PATH = Path("configs") / "regime_reason_templates.json"
DAILY_RE = re.compile(r"^daily_summary_(\d{4}-\d{2}-\d{2})\.json$")

# =========================
# Utilities
# =========================
def _parse_ymd(s: str) -> date_type:
    return datetime.strptime(s, "%Y-%m-%d").date()

def _daterange(d0: date_type, d1: date_type):
    d = d0
    while d <= d1:
        yield d
        d += timedelta(days=1)

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

# =========================
# Templates
# =========================
@dataclass
class Templates:
    regime_templates: Dict[str, List[str]]
    transition_templates: List[str]
    short_templates: List[str]

def _load_templates(path: Path) -> Templates:
    obj = _read_json(path)
    return Templates(
        regime_templates=obj.get("regime_templates", {}),
        transition_templates=obj.get("transition_templates", []),
        short_templates=obj.get("short_templates", ["{regime}"]),
    )

# =========================
# Core helpers
# =========================
def _find_daily_summaries() -> List[Tuple[str, Path]]:
    out: List[Tuple[str, Path]] = []
    for p in ANALYSIS_DIR.glob("daily_summary_*.json"):
        m = DAILY_RE.match(p.name)
        if m:
            out.append((m.group(1), p))
    return sorted(out)

def _infer_regime(conf: float, churn: float) -> str:
    if conf >= 0.7 and churn <= 0.3:
        return "stable"
    if churn >= 0.7:
        return "volatile"
    if conf <= 0.4:
        return "uncertain"
    return "mixed"

def _pick_anchors_top(daily: Dict[str, Any], k: int) -> List[str]:
    anchors = daily.get("anchors") or daily.get("anchor_words") or []
    if isinstance(anchors, list):
        return [str(a) for a in anchors[:k]]
    return []

def _pick_top_hypothesis(daily: Dict[str, Any]) -> str:
    hyps = daily.get("hypotheses") or []
    if isinstance(hyps, list) and hyps:
        return str(hyps[0])
    return ""

# =========================
# Builder
# =========================
def _build_for_dates(
    summaries: List[Tuple[str, Path]],
    templates: Templates,
    *,
    start: Optional[str],
    end: Optional[str],
    outdir: Path,
    force: bool,
    dry_run: bool,
) -> Tuple[int, int, int]:
    if start or end:
        s0 = _parse_ymd(start) if start else _parse_ymd(summaries[0][0])
        s1 = _parse_ymd(end) if end else _parse_ymd(summaries[-1][0])
        allow = {d.strftime("%Y-%m-%d") for d in _daterange(s0, s1)}
        summaries = [(d, p) for (d, p) in summaries if d in allow]

    ok = skip = err = 0
    prev_date: Optional[str] = None
    prev_daily: Optional[Dict[str, Any]] = None

    for date, path in summaries:
        out_path = outdir / f"regime_reason_{date}.json"
        if out_path.exists() and not force:
            skip += 1
            prev_date = date
            prev_daily = _read_json(path)
            continue

        if dry_run:
            print(f"[PLAN] {date} -> {out_path.as_posix()}")
            prev_date = date
            prev_daily = _read_json(path)
            continue

        try:
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

            _write_json(out_path, out)
            ok += 1
            prev_date = date
            prev_daily = daily
        except Exception as e:
            err += 1
            print(f"[ERROR] {date}: {e!r}")
            prev_date = date
            try:
                prev_daily = _read_json(path)
            except Exception:
                prev_daily = None

    return ok, skip, err

# =========================
# CLI
# =========================
def main() -> None:
    ap = argparse.ArgumentParser(description="Build regime_reason json files")
    ap.add_argument("--start", help="YYYY-MM-DD")
    ap.add_argument("--end", help="YYYY-MM-DD")
    ap.add_argument("--date", help="YYYY-MM-DD (single day)")
    ap.add_argument("--outdir", default=str(ANALYSIS_DIR))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    start = args.start
    end = args.end
    if args.date:
        start = args.date
        end = args.date

    templates = _load_templates(TEMPLATES_PATH)
    summaries = _find_daily_summaries()
    outdir = Path(args.outdir)

    ok, skip, err = _build_for_dates(
        summaries,
        templates,
        start=start,
        end=end,
        outdir=outdir,
        force=args.force,
        dry_run=args.dry_run,
    )

    print(f"[OK] regime_reason generated OK={ok} SKIP={skip} ERROR={err}")
    if err:
        raise SystemExit(2)

if __name__ == "__main__":
    main()

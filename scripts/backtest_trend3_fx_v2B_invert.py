# scripts/backtest_trend3_fx_v2B_invert.py
# Trend3 FX backtest (v2B) - SAME as backtest_trend3_fx_v2.py (v2A) but EXPECTED SIGN IS INVERTED.
#
# Why:
#   If v2A is systematically "wrong-way", inverting sign should boost hit_rate materially.
#
# Fix (Py3.13/dataclasses + dynamic import):
#   Register module in sys.modules BEFORE exec_module().
#
# Output:
#   analysis/prediction_backtests/trend3_fx_v2B_invert_YYYYMMDD_HHMMSS.{txt,csv,json}
#
# Run:
#   .\.venv\Scripts\python.exe scripts\backtest_trend3_fx_v2B_invert.py --threshold 0.08
#   .\.venv\Scripts\python.exe scripts\backtest_trend3_fx_v2B_invert.py --threshold 0.08 --max-uncertainty 0.25
#
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = REPO_ROOT / "analysis"
OUT_DIR = ANALYSIS_DIR / "prediction_backtests"
BACKTEST_V2A_PATH = REPO_ROOT / "scripts" / "backtest_trend3_fx_v2.py"


def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_v2a_module() -> Any:
    if not BACKTEST_V2A_PATH.exists():
        raise RuntimeError(f"missing: {BACKTEST_V2A_PATH}")

    modname = "backtest_trend3_fx_v2A_mod_for_invert"
    spec = importlib.util.spec_from_file_location(modname, str(BACKTEST_V2A_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to create import spec for v2A module")

    mod = importlib.util.module_from_spec(spec)

    # critical fix for Py3.13 + dataclasses
    sys.modules[modname] = mod

    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _trend3_equal(net2: float, net1: float, net0: float) -> float:
    return (net2 + net1 + net0) / 3.0


def _invert_expected_fx_sign(v2a_mod: Any, dir_: str) -> int:
    # v2A: +1/-1/0 -> invert by multiplying -1
    return -int(v2a_mod.expected_fx_sign(dir_))


def _run_backtest(
    v2a_mod: Any,
    threshold: float,
    max_uncertainty: Optional[float],
) -> Dict[str, Any]:
    # use v2A loaders (handles mixed sentiment schemas)
    scores: Dict[str, Any] = v2a_mod.load_daily_scores()
    fx, fx_dbg = v2a_mod.load_fx_thb_per_jpy()

    dates = sorted(scores.keys())

    rows = 0
    hit = 0
    miss = 0
    no_call = 0

    detail_rows: List[Dict[str, Any]] = []

    for i in range(2, len(dates) - 1):
        d0 = dates[i]
        d1 = dates[i - 1]
        d2 = dates[i - 2]
        dn = dates[i + 1]

        if d0 not in fx.index or dn not in fx.index:
            continue

        s0 = scores[d0]
        s1 = scores[d1]
        s2 = scores[d2]

        tr = _trend3_equal(float(s2.net), float(s1.net), float(s0.net))
        dir_ = v2a_mod.direction(tr, float(threshold))

        if max_uncertainty is not None and float(s0.uncertainty) > float(max_uncertainty):
            dir_ = "NEUTRAL"

        fx0 = float(fx[d0])
        fx1 = float(fx[dn])
        delta = fx1 - fx0

        exp = _invert_expected_fx_sign(v2a_mod, dir_)

        rows += 1

        if exp == 0:
            no_call += 1
            detail_rows.append(
                {
                    "date": d0,
                    "next_date": dn,
                    "trend": tr,
                    "dir": dir_,
                    "exp": exp,
                    "fx0": fx0,
                    "fx1": fx1,
                    "delta": delta,
                    "ok": None,
                }
            )
            continue

        ok = (delta > 0 and exp > 0) or (delta < 0 and exp < 0)

        if ok:
            hit += 1
        else:
            miss += 1

        detail_rows.append(
            {
                "date": d0,
                "next_date": dn,
                "trend": tr,
                "dir": dir_,
                "exp": exp,
                "fx0": fx0,
                "fx1": fx1,
                "delta": delta,
                "ok": bool(ok),
            }
        )

    calls = hit + miss
    hit_rate = (hit / calls) if calls else None
    call_rate = (calls / rows) if rows else None

    return {
        "meta": {
            "generated_at_local": datetime.now().isoformat(timespec="seconds"),
            "threshold": float(threshold),
            "max_uncertainty": (float(max_uncertainty) if max_uncertainty is not None else None),
            "fx_strategy": fx_dbg.get("strategy"),
            "fx_points": int(len(fx)),
            "sentiment_days": int(len(scores)),
            "notes": "Same as v2A but expected_fx_sign is inverted (multiplied by -1).",
        },
        "summary": {
            "rows": int(rows),
            "calls": int(calls),
            "hit": int(hit),
            "miss": int(miss),
            "no_call": int(no_call),
            "call_rate": call_rate,
            "hit_rate": hit_rate,
        },
        "details": detail_rows,
    }


def _write_outputs(result: Dict[str, Any]) -> Dict[str, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = _now_ts()
    base = OUT_DIR / f"trend3_fx_v2B_invert_{ts}"

    p_txt = str(base.with_suffix(".txt"))
    p_csv = str(base.with_suffix(".csv"))
    p_json = str(base.with_suffix(".json"))

    # json
    Path(p_json).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # csv details
    df = pd.DataFrame(result["details"])
    df.to_csv(p_csv, index=False)

    # txt
    m = result["meta"]
    s = result["summary"]
    lines: List[str] = []
    lines.append("Trend3 FX v2B (INVERTED expected_fx_sign)")
    lines.append(f"generated_at_local: {m.get('generated_at_local')}")
    lines.append(f"threshold: {m.get('threshold')}")
    lines.append(f"max_uncertainty: {m.get('max_uncertainty')}")
    lines.append(f"fx_strategy: {m.get('fx_strategy')}")
    lines.append("")
    lines.append(f"rows={s['rows']}")
    lines.append(f"calls={s['calls']}")
    lines.append(f"hit={s['hit']}")
    lines.append(f"miss={s['miss']}")
    lines.append(f"no_call={s['no_call']}")
    lines.append(f"call_rate={s.get('call_rate')}")
    lines.append(f"hit_rate={s.get('hit_rate')}")
    lines.append("")
    Path(p_txt).write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {"txt": p_txt, "csv": p_csv, "json": p_json}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.08)
    ap.add_argument("--max-uncertainty", type=float, default=None)
    args = ap.parse_args()

    v2a = _load_v2a_module()
    result = _run_backtest(v2a, float(args.threshold), args.max_uncertainty)

    out = _write_outputs(result)
    s = result["summary"]

    print("[OK] backtest written:")
    print(" -", out["txt"])
    print(" -", out["csv"])
    print(" -", out["json"])
    print(
        f"[SUMMARY] calls={s['calls']} hit={s['hit']} miss={s['miss']} "
        f"hit_rate={s.get('hit_rate')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

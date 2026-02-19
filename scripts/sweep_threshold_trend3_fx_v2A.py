# scripts/sweep_threshold_trend3_fx_v2A.py
# Sweep threshold for Trend3 FX model using the SAME loaders/logic as backtest_trend3_fx_v2.py (v2A).
#
# Why:
#   Weight sweep did not move results -> bottleneck is "CALL / NO_CALL" gating.
#   This script explores threshold vs (calls, hit_rate) tradeoff.
#
# Fix (Py3.13/dataclasses + dynamic import):
#   Register module in sys.modules BEFORE exec_module().
#
# Output:
#   analysis/prediction_backtests/threshold_sweep_trend3_fx_v2A_YYYYMMDD_HHMMSS.{txt,csv,json}
#
# Run:
#   .\.venv\Scripts\python.exe scripts\sweep_threshold_trend3_fx_v2A.py
#   .\.venv\Scripts\python.exe scripts\sweep_threshold_trend3_fx_v2A.py --max-uncertainty 0.25
#   .\.venv\Scripts\python.exe scripts\sweep_threshold_trend3_fx_v2A.py --tmin 0.02 --tmax 0.20 --tstep 0.01
#   .\.venv\Scripts\python.exe scripts\sweep_threshold_trend3_fx_v2A.py --min-calls 10
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
BACKTEST_PATH = REPO_ROOT / "scripts" / "backtest_trend3_fx_v2.py"


def _now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_backtest_module() -> Any:
    if not BACKTEST_PATH.exists():
        raise RuntimeError(f"missing: {BACKTEST_PATH}")

    modname = "backtest_trend3_fx_v2A_mod_for_threshold_sweep"
    spec = importlib.util.spec_from_file_location(modname, str(BACKTEST_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to create import spec")

    mod = importlib.util.module_from_spec(spec)
    # critical fix for Py3.13 + dataclasses
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _trend3_equal_weights(net2: float, net1: float, net0: float) -> float:
    # v2A uses a 3-day trend; we keep it simple and stable here:
    # equal weights (1,1,1). Threshold sweep is about gating, not weights.
    return (net2 + net1 + net0) / 3.0


def _evaluate_threshold(
    mod: Any,
    scores: Dict[str, Any],
    fx: pd.Series,
    threshold: float,
    max_uncertainty: Optional[float],
) -> Dict[str, Any]:
    dates = sorted(scores.keys())
    rows = 0
    hit = 0
    miss = 0
    no_call = 0

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

        tr = _trend3_equal_weights(float(s2.net), float(s1.net), float(s0.net))
        dir_ = mod.direction(tr, float(threshold))

        # uncertainty cap: if too uncertain -> NEUTRAL
        if max_uncertainty is not None and float(s0.uncertainty) > float(max_uncertainty):
            dir_ = "NEUTRAL"

        fx0 = float(fx[d0])
        fx1 = float(fx[dn])
        delta = fx1 - fx0

        exp = mod.expected_fx_sign(dir_)  # +1/-1/0

        rows += 1

        if exp == 0:
            no_call += 1
            continue

        ok = (delta > 0 and exp > 0) or (delta < 0 and exp < 0)
        if ok:
            hit += 1
        else:
            miss += 1

    calls = hit + miss
    hit_rate = (hit / calls) if calls else None
    call_rate = (calls / rows) if rows else None

    return {
        "threshold": float(threshold),
        "max_uncertainty": (float(max_uncertainty) if max_uncertainty is not None else None),
        "rows": int(rows),
        "calls": int(calls),
        "no_call": int(no_call),
        "call_rate": call_rate,
        "hit": int(hit),
        "miss": int(miss),
        "hit_rate": hit_rate,
    }


def _write_outputs(df: pd.DataFrame, meta: Dict[str, Any]) -> Dict[str, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = _now_ts()
    base = OUT_DIR / f"threshold_sweep_trend3_fx_v2A_{ts}"

    p_csv = str(base.with_suffix(".csv"))
    p_json = str(base.with_suffix(".json"))
    p_txt = str(base.with_suffix(".txt"))

    df.to_csv(p_csv, index=False)
    Path(p_json).write_text(
        json.dumps({"meta": meta, "results": df.to_dict(orient="records")}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines: List[str] = []
    lines.append("Threshold sweep: Trend3 FX (v2A loaders, equal-weight trend3)")
    lines.append(f"generated_at_local: {meta.get('generated_at_local')}")
    lines.append(f"repo_root: {meta.get('repo_root')}")
    lines.append(f"tmin={meta.get('tmin')} tmax={meta.get('tmax')} tstep={meta.get('tstep')}")
    lines.append(f"max_uncertainty={meta.get('max_uncertainty')}")
    lines.append(f"min_calls={meta.get('min_calls')}")
    lines.append(f"tested={meta.get('tested')} thresholds")
    lines.append("")

    if len(df) == 0:
        lines.append("No results (maybe min_calls too high).")
    else:
        best = df.iloc[0].to_dict()
        lines.append(
            f"BEST(hit_rate,calls): threshold={best['threshold']} "
            f"calls={best['calls']} hit={best['hit']} miss={best['miss']} "
            f"hit_rate={best['hit_rate']} call_rate={best['call_rate']}"
        )
        lines.append("")

        # also pick "aggressive" by calls first (then hit_rate)
        df_calls = df.sort_values(["calls", "hit_rate"], ascending=[False, False]).reset_index(drop=True)
        agg = df_calls.iloc[0].to_dict()
        lines.append(
            f"BEST(calls,hit_rate): threshold={agg['threshold']} "
            f"calls={agg['calls']} hit={agg['hit']} miss={agg['miss']} "
            f"hit_rate={agg['hit_rate']} call_rate={agg['call_rate']}"
        )
        lines.append("")

        lines.append("TOP 20 by (hit_rate desc, calls desc):")
        cols = ["threshold", "calls", "hit", "miss", "hit_rate", "no_call", "call_rate"]
        lines.append(",".join(cols))
        for _, r in df.head(20).iterrows():
            hr = r["hit_rate"]
            cr = r["call_rate"]
            hr_s = "" if pd.isna(hr) else f"{float(hr):.6f}"
            cr_s = "" if pd.isna(cr) else f"{float(cr):.6f}"
            lines.append(
                f"{float(r['threshold']):.6f},{int(r['calls'])},{int(r['hit'])},{int(r['miss'])},"
                f"{hr_s},{int(r['no_call'])},{cr_s}"
            )

    Path(p_txt).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"csv": p_csv, "json": p_json, "txt": p_txt}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmin", type=float, default=0.02)
    ap.add_argument("--tmax", type=float, default=0.20)
    ap.add_argument("--tstep", type=float, default=0.01)
    ap.add_argument("--max-uncertainty", type=float, default=None)
    ap.add_argument("--min-calls", type=int, default=6)
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    mod = _load_backtest_module()

    scores = mod.load_daily_scores()
    fx, fx_dbg = mod.load_fx_thb_per_jpy()

    if len(scores) < 5:
        raise RuntimeError(f"Not enough sentiment days (got {len(scores)})")
    if len(fx) < 10:
        raise RuntimeError(f"Not enough FX points (got {len(fx)}). fx_debug.strategy={fx_dbg.get('strategy')}")

    tmin = float(args.tmin)
    tmax = float(args.tmax)
    tstep = float(args.tstep)
    if not (tmin > 0 and tmax >= tmin and tstep > 0):
        raise RuntimeError("invalid tmin/tmax/tstep")

    thresholds: List[float] = []
    t = tmin
    # avoid floating accumulation drift by rounding
    while t <= tmax + 1e-12:
        thresholds.append(round(t, 6))
        t += tstep

    results: List[Dict[str, Any]] = []
    for th in thresholds:
        r = _evaluate_threshold(
            mod=mod,
            scores=scores,
            fx=fx,
            threshold=float(th),
            max_uncertainty=(float(args.max_uncertainty) if args.max_uncertainty is not None else None),
        )
        results.append(r)

    df = pd.DataFrame(results)

    # filter: require min calls
    df = df[df["calls"] >= int(args.min_calls)].copy()

    # rank: hit_rate desc, calls desc, call_rate desc
    df["_hr"] = df["hit_rate"].fillna(-1.0)
    df["_cr"] = df["call_rate"].fillna(-1.0)
    df = df.sort_values(["_hr", "calls", "_cr"], ascending=[False, False, False]).drop(columns=["_hr", "_cr"]).reset_index(drop=True)

    meta = {
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "tmin": tmin,
        "tmax": tmax,
        "tstep": tstep,
        "tested": int(len(thresholds)),
        "max_uncertainty": (float(args.max_uncertainty) if args.max_uncertainty is not None else None),
        "min_calls": int(args.min_calls),
        "sentiment_days": int(len(scores)),
        "fx_points": int(len(fx)),
        "fx_strategy": fx_dbg.get("strategy"),
    }

    out = _write_outputs(df, meta)

    print("[OK] sweep written:")
    print(" -", out["txt"])
    print(" -", out["csv"])
    print(" -", out["json"])

    if len(df) == 0:
        print("[WARN] no thresholds met min_calls filter")
        return 0

    best = df.iloc[0]
    hr = float(best["hit_rate"]) if best["hit_rate"] is not None else -1.0
    print(
        f"[BEST] threshold={float(best['threshold']):.6f} calls={int(best['calls'])} "
        f"hit={int(best['hit'])} miss={int(best['miss'])} hit_rate={hr:.6f} "
        f"no_call={int(best['no_call'])} call_rate={float(best['call_rate']):.6f}"
    )

    top_n = min(int(args.top), len(df))
    print(f"[TOP {top_n}]")
    show = df.head(top_n)[["threshold", "calls", "hit", "miss", "hit_rate", "no_call", "call_rate"]]
    with pd.option_context("display.max_rows", 200, "display.width", 200):
        print(show.to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

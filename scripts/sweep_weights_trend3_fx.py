# scripts/sweep_weights_trend3_fx.py
# Sweep (w1,w2,w3) weights for Trend3 FX model using the SAME loaders/logic as backtest_trend3_fx_v2.py (v2A).
#
# Fix for Python 3.13 + dataclasses + dynamic import:
#   Register module in sys.modules BEFORE exec_module().
#
# Purpose:
#   Find weight triples that improve hit_rate beyond 0.5 in a stable way.
#
# Output:
#   analysis/prediction_backtests/weight_sweep_trend3_fx_YYYYMMDD_HHMMSS.{txt,csv,json}
#
# Run:
#   .\.venv\Scripts\python.exe scripts\sweep_weights_trend3_fx.py --threshold 0.08 --wmin 1 --wmax 7 --top 20 --min-calls 6
#   .\.venv\Scripts\python.exe scripts\sweep_weights_trend3_fx.py --threshold 0.08 --max-uncertainty 0.25 --wmin 1 --wmax 7 --top 20 --min-calls 6
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
    """
    Dynamically import scripts/backtest_trend3_fx_v2.py safely.
    IMPORTANT (Py3.13/dataclasses):
      sys.modules[modname] must be set before exec_module().
    """
    if not BACKTEST_PATH.exists():
        raise RuntimeError(f"missing: {BACKTEST_PATH}")

    modname = "backtest_trend3_fx_v2A_mod"
    spec = importlib.util.spec_from_file_location(modname, str(BACKTEST_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to create import spec for backtest module")

    mod = importlib.util.module_from_spec(spec)

    # --- critical fix ---
    sys.modules[modname] = mod

    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _weighted_mean(a: float, b: float, c: float, w1: float, w2: float, w3: float) -> float:
    den = (w1 + w2 + w3)
    if den == 0:
        return 0.0
    return (w1 * a + w2 * b + w3 * c) / den


def _evaluate_weights(
    mod: Any,
    scores: Dict[str, Any],
    fx: pd.Series,
    threshold: float,
    max_uncertainty: Optional[float],
    w1: int,
    w2: int,
    w3: int,
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

        # Weighted trend on net
        tr = _weighted_mean(float(s2.net), float(s1.net), float(s0.net), w1, w2, w3)
        dir_ = mod.direction(tr, threshold)

        # uncertainty filter semantics same as v2A:
        # if uncertainty is above cap => force NEUTRAL
        if max_uncertainty is not None and float(s0.uncertainty) > float(max_uncertainty):
            dir_ = "NEUTRAL"

        fx0 = float(fx[d0])
        fx1 = float(fx[dn])
        delta = fx1 - fx0

        exp = mod.expected_fx_sign(dir_)  # +1 / -1 / 0

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

    return {
        "w1": int(w1),
        "w2": int(w2),
        "w3": int(w3),
        "threshold": float(threshold),
        "max_uncertainty": (float(max_uncertainty) if max_uncertainty is not None else None),
        "rows": int(rows),
        "calls": int(calls),
        "hit": int(hit),
        "miss": int(miss),
        "no_call": int(no_call),
        "hit_rate": hit_rate,
    }


def _write_outputs(df: pd.DataFrame, meta: Dict[str, Any]) -> Dict[str, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = _now_ts()
    base = OUT_DIR / f"weight_sweep_trend3_fx_{ts}"

    p_csv = str(base.with_suffix(".csv"))
    p_json = str(base.with_suffix(".json"))
    p_txt = str(base.with_suffix(".txt"))

    df.to_csv(p_csv, index=False)
    Path(p_json).write_text(
        json.dumps({"meta": meta, "results": df.to_dict(orient="records")}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines: List[str] = []
    lines.append("Weight sweep: Trend3 FX (v2A loaders)")
    lines.append(f"generated_at_local: {meta.get('generated_at_local')}")
    lines.append(f"threshold: {meta.get('threshold')}")
    lines.append(f"max_uncertainty: {meta.get('max_uncertainty')}")
    lines.append(f"weights: wmin={meta.get('wmin')} wmax={meta.get('wmax')}")
    lines.append(f"tested_total: {meta.get('tested_total')} combos")
    lines.append(f"kept_after_min_calls: {meta.get('kept_after_min_calls')} combos (min_calls={meta.get('min_calls')})")
    lines.append("")

    if len(df) == 0:
        lines.append("No results.")
    else:
        best = df.iloc[0].to_dict()
        lines.append(
            f"BEST: w=({best['w1']},{best['w2']},{best['w3']}) "
            f"calls={best['calls']} hit={best['hit']} miss={best['miss']} hit_rate={best['hit_rate']}"
        )
        lines.append("")
        lines.append("TOP 20:")
        cols = ["w1", "w2", "w3", "calls", "hit", "miss", "hit_rate", "no_call"]
        lines.append(",".join(cols))
        for _, r in df.head(20).iterrows():
            hr = r["hit_rate"]
            hr_s = "" if pd.isna(hr) else f"{float(hr):.6f}"
            lines.append(
                f"{int(r['w1'])},{int(r['w2'])},{int(r['w3'])},"
                f"{int(r['calls'])},{int(r['hit'])},{int(r['miss'])},"
                f"{hr_s},{int(r['no_call'])}"
            )

    Path(p_txt).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"csv": p_csv, "json": p_json, "txt": p_txt}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.08)
    ap.add_argument("--max-uncertainty", type=float, default=None)
    ap.add_argument("--wmin", type=int, default=1)
    ap.add_argument("--wmax", type=int, default=7)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-calls", type=int, default=6, help="filter out combos with calls < N")
    args = ap.parse_args()

    mod = _load_backtest_module()

    scores = mod.load_daily_scores()
    fx, fx_dbg = mod.load_fx_thb_per_jpy()

    if len(scores) < 5:
        raise RuntimeError(f"Not enough sentiment days (got {len(scores)})")
    if len(fx) < 10:
        raise RuntimeError(f"Not enough FX points (got {len(fx)}). fx_debug.strategy={fx_dbg.get('strategy')}")

    wmin = int(args.wmin)
    wmax = int(args.wmax)
    if wmin <= 0 or wmax < wmin:
        raise RuntimeError("--wmin must be >=1 and --wmax >= --wmin")

    results: List[Dict[str, Any]] = []
    tested_total = 0

    for w1 in range(wmin, wmax + 1):
        for w2 in range(wmin, wmax + 1):
            for w3 in range(wmin, wmax + 1):
                tested_total += 1
                r = _evaluate_weights(
                    mod=mod,
                    scores=scores,
                    fx=fx,
                    threshold=float(args.threshold),
                    max_uncertainty=(float(args.max_uncertainty) if args.max_uncertainty is not None else None),
                    w1=w1,
                    w2=w2,
                    w3=w3,
                )
                results.append(r)

    df = pd.DataFrame(results)

    # filter
    df = df[df["calls"] >= int(args.min_calls)].copy()

    # rank
    df["_hr"] = df["hit_rate"].fillna(-1.0)
    df = df.sort_values(["_hr", "calls", "hit"], ascending=[False, False, False]).drop(columns=["_hr"]).reset_index(drop=True)

    meta = {
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "threshold": float(args.threshold),
        "max_uncertainty": (float(args.max_uncertainty) if args.max_uncertainty is not None else None),
        "wmin": wmin,
        "wmax": wmax,
        "tested_total": int(tested_total),
        "kept_after_min_calls": int(len(df)),
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
        print("[WARN] no combos met min_calls filter")
        return 0

    best = df.iloc[0]
    print(
        f"[BEST] w=({int(best['w1'])},{int(best['w2'])},{int(best['w3'])}) "
        f"calls={int(best['calls'])} hit={int(best['hit'])} miss={int(best['miss'])} hit_rate={float(best['hit_rate']):.6f}"
    )

    top_n = min(int(args.top), len(df))
    print(f"[TOP {top_n}]")
    show = df.head(top_n)[["w1", "w2", "w3", "calls", "hit", "miss", "hit_rate", "no_call"]]
    with pd.option_context("display.max_rows", 200, "display.width", 200):
        print(show.to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

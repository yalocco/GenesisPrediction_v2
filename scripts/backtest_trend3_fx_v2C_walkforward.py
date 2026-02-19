# scripts/backtest_trend3_fx_v2C_walkforward.py
# Walk-forward validation for Trend3 FX with EXPECTED SIGN INVERTED (v2B).
#
# Goal:
#   Detect overfitting by splitting evaluation days into two chronological halves
#   and reporting hit_rate separately (first_half vs second_half).
#
# Uses backtest_trend3_fx_v2.py (v2A) loaders via dynamic import,
# and ONLY inverts expected_fx_sign by multiplying by -1.
#
# Fix (Py3.13/dataclasses + dynamic import):
#   Register module in sys.modules BEFORE exec_module().
#
# Output:
#   analysis/prediction_backtests/trend3_fx_v2C_walkforward_YYYYMMDD_HHMMSS.{txt,csv,json}
#
# Run (recommended):
#   .\.venv\Scripts\python.exe scripts\backtest_trend3_fx_v2C_walkforward.py --threshold 0.02
#   .\.venv\Scripts\python.exe scripts\backtest_trend3_fx_v2C_walkforward.py --threshold 0.03
#   .\.venv\Scripts\python.exe scripts\backtest_trend3_fx_v2C_walkforward.py --threshold 0.02 --max-uncertainty 0.25
#
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

    modname = "backtest_trend3_fx_v2A_mod_for_walkforward"
    spec = importlib.util.spec_from_file_location(modname, str(BACKTEST_V2A_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to create import spec")

    mod = importlib.util.module_from_spec(spec)
    # critical fix for Py3.13 + dataclasses
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def _trend3_equal(net2: float, net1: float, net0: float) -> float:
    return (net2 + net1 + net0) / 3.0


def _expected_fx_sign_inverted(v2a_mod: Any, dir_: str) -> int:
    # v2A returns +1/-1/0. Invert by multiplying -1.
    return -int(v2a_mod.expected_fx_sign(dir_))


def _build_eval_rows(
    v2a_mod: Any,
    threshold: float,
    max_uncertainty: Optional[float],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    scores: Dict[str, Any] = v2a_mod.load_daily_scores()
    fx, fx_dbg = v2a_mod.load_fx_thb_per_jpy()

    dates = sorted(scores.keys())

    rows: List[Dict[str, Any]] = []

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

        unc0 = float(s0.uncertainty)
        unc_filtered = False
        if max_uncertainty is not None and unc0 > float(max_uncertainty):
            dir_ = "NEUTRAL"
            unc_filtered = True

        fx0 = float(fx[d0])
        fx1 = float(fx[dn])
        delta = fx1 - fx0

        exp = _expected_fx_sign_inverted(v2a_mod, dir_)
        called = (exp != 0)

        ok: Optional[bool]
        if not called:
            ok = None
        else:
            ok = bool((delta > 0 and exp > 0) or (delta < 0 and exp < 0))

        rows.append(
            {
                "date": d0,
                "next_date": dn,
                "net_d2": float(s2.net),
                "net_d1": float(s1.net),
                "net_d0": float(s0.net),
                "trend3": tr,
                "dir": dir_,
                "uncertainty": unc0,
                "unc_filtered": bool(unc_filtered),
                "expected_sign_inverted": int(exp),
                "called": bool(called),
                "fx0": fx0,
                "fx1": fx1,
                "delta": delta,
                "ok": ok,
            }
        )

    if len(rows) == 0:
        raise RuntimeError("No evaluation rows built (check FX dashboard coverage)")

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    meta = {
        "generated_at_local": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "threshold": float(threshold),
        "max_uncertainty": (float(max_uncertainty) if max_uncertainty is not None else None),
        "fx_strategy": fx_dbg.get("strategy"),
        "fx_points": int(len(fx)),
        "sentiment_days": int(len(scores)),
        "notes": "Walk-forward split into two halves, expected sign inverted (v2B).",
    }
    return df, meta


def _summarize(df: pd.DataFrame) -> Dict[str, Any]:
    total_rows = int(len(df))
    calls = int(df["called"].sum())
    no_call = int((~df["called"]).sum())
    hit = int(((df["called"]) & (df["ok"] == True)).sum())  # noqa: E712
    miss = int(((df["called"]) & (df["ok"] == False)).sum())  # noqa: E712

    hit_rate = (hit / calls) if calls else None
    call_rate = (calls / total_rows) if total_rows else None

    # also useful: average abs trend magnitude on called vs not
    try:
        avg_abs_trend_called = float(df.loc[df["called"], "trend3"].abs().mean()) if calls else None
        avg_abs_trend_nocall = float(df.loc[~df["called"], "trend3"].abs().mean()) if no_call else None
    except Exception:
        avg_abs_trend_called = None
        avg_abs_trend_nocall = None

    return {
        "rows": total_rows,
        "calls": calls,
        "hit": hit,
        "miss": miss,
        "no_call": no_call,
        "call_rate": call_rate,
        "hit_rate": hit_rate,
        "avg_abs_trend_called": avg_abs_trend_called,
        "avg_abs_trend_nocall": avg_abs_trend_nocall,
    }


def _split_walkforward(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # chronological split into two halves
    n = len(df)
    mid = n // 2
    first = df.iloc[:mid].copy().reset_index(drop=True)
    second = df.iloc[mid:].copy().reset_index(drop=True)
    return first, second


def _write_outputs(df: pd.DataFrame, meta: Dict[str, Any]) -> Dict[str, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = _now_ts()
    base = OUT_DIR / f"trend3_fx_v2C_walkforward_{ts}"

    p_txt = str(base.with_suffix(".txt"))
    p_csv = str(base.with_suffix(".csv"))
    p_json = str(base.with_suffix(".json"))

    first, second = _split_walkforward(df)
    sum_all = _summarize(df)
    sum_first = _summarize(first)
    sum_second = _summarize(second)

    payload = {
        "meta": meta,
        "summary_all": sum_all,
        "summary_first_half": sum_first,
        "summary_second_half": sum_second,
        "details": df.to_dict(orient="records"),
    }

    Path(p_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    df.to_csv(p_csv, index=False)

    lines: List[str] = []
    lines.append("Trend3 FX v2C Walk-Forward (expected sign inverted)")
    lines.append(f"generated_at_local: {meta.get('generated_at_local')}")
    lines.append(f"threshold: {meta.get('threshold')}")
    lines.append(f"max_uncertainty: {meta.get('max_uncertainty')}")
    lines.append(f"fx_strategy: {meta.get('fx_strategy')}")
    lines.append("")

    def _block(name: str, s: Dict[str, Any]) -> None:
        lines.append(f"[{name}]")
        lines.append(f"rows={s['rows']} calls={s['calls']} hit={s['hit']} miss={s['miss']} no_call={s['no_call']}")
        lines.append(f"call_rate={s.get('call_rate')} hit_rate={s.get('hit_rate')}")
        lines.append(f"avg_abs_trend_called={s.get('avg_abs_trend_called')} avg_abs_trend_nocall={s.get('avg_abs_trend_nocall')}")
        lines.append("")

    _block("ALL", sum_all)
    _block("FIRST_HALF", sum_first)
    _block("SECOND_HALF", sum_second)

    # quick sanity: date ranges
    lines.append("[DATE_RANGES]")
    lines.append(f"all   : {df['date'].min()} .. {df['date'].max()} (n={len(df)})")
    lines.append(f"first : {first['date'].min()} .. {first['date'].max()} (n={len(first)})")
    lines.append(f"second: {second['date'].min()} .. {second['date'].max()} (n={len(second)})")
    lines.append("")

    Path(p_txt).write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {"txt": p_txt, "csv": p_csv, "json": p_json}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.02)
    ap.add_argument("--max-uncertainty", type=float, default=None)
    args = ap.parse_args()

    v2a = _load_v2a_module()

    df, meta = _build_eval_rows(v2a, float(args.threshold), args.max_uncertainty)
    out = _write_outputs(df, meta)

    first, second = _split_walkforward(df)
    sum_all = _summarize(df)
    sum_first = _summarize(first)
    sum_second = _summarize(second)

    print("[OK] walkforward written:")
    print(" -", out["txt"])
    print(" -", out["csv"])
    print(" -", out["json"])
    print(
        f"[SUMMARY ALL] calls={sum_all['calls']} hit={sum_all['hit']} miss={sum_all['miss']} "
        f"hit_rate={sum_all.get('hit_rate')}"
    )
    print(
        f"[SUMMARY FIRST] calls={sum_first['calls']} hit={sum_first['hit']} miss={sum_first['miss']} "
        f"hit_rate={sum_first.get('hit_rate')}"
    )
    print(
        f"[SUMMARY SECOND] calls={sum_second['calls']} hit={sum_second['hit']} miss={sum_second['miss']} "
        f"hit_rate={sum_second.get('hit_rate')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

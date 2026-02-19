# scripts/backtest_trend3_fx_v2D_returns.py
# Return-based evaluation for Trend3 FX (v2B: expected sign inverted)

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "analysis" / "prediction_backtests"
BACKTEST_V2A_PATH = REPO_ROOT / "scripts" / "backtest_trend3_fx_v2.py"


def _load_v2a():
    modname = "v2a_mod_returns"
    spec = importlib.util.spec_from_file_location(modname, str(BACKTEST_V2A_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def trend3_equal(n2: float, n1: float, n0: float) -> float:
    return (n2 + n1 + n0) / 3.0


def expected_sign_inverted(v2a, dir_: str) -> int:
    return -int(v2a.expected_fx_sign(dir_))


def max_drawdown(series: np.ndarray) -> float:
    peak = -np.inf
    max_dd = 0.0
    for x in series:
        peak = max(peak, x)
        dd = peak - x
        max_dd = max(max_dd, dd)
    return float(max_dd)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.02)
    ap.add_argument("--max-uncertainty", type=float, default=None)
    args = ap.parse_args()

    v2a = _load_v2a()
    scores = v2a.load_daily_scores()
    fx, _ = v2a.load_fx_thb_per_jpy()

    dates = sorted(scores.keys())
    rows: List[Dict[str, Any]] = []

    for i in range(2, len(dates) - 1):
        d0 = dates[i]
        d1 = dates[i - 1]
        d2 = dates[i - 2]
        dn = dates[i + 1]

        if d0 not in fx.index or dn not in fx.index:
            continue

        s0, s1, s2 = scores[d0], scores[d1], scores[d2]

        tr = trend3_equal(float(s2.net), float(s1.net), float(s0.net))
        dir_ = v2a.direction(tr, float(args.threshold))

        if args.max_uncertainty is not None:
            if float(s0.uncertainty) > float(args.max_uncertainty):
                dir_ = "NEUTRAL"

        exp = expected_sign_inverted(v2a, dir_)
        if exp == 0:
            continue

        fx0 = float(fx[d0])
        fx1 = float(fx[dn])
        delta = fx1 - fx0

        ret = exp * delta

        rows.append({
            "date": d0,
            "delta": delta,
            "expected_sign": exp,
            "strategy_return": ret
        })

    if not rows:
        raise RuntimeError("No trades generated")

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    returns = df["strategy_return"].values
    cumulative = np.cumsum(returns)

    total_return = float(np.sum(returns))
    avg_return = float(np.mean(returns))
    std_return = float(np.std(returns, ddof=1)) if len(returns) > 1 else 0.0
    sharpe_like = float(avg_return / std_return) if std_return > 0 else None

    wins = returns[returns > 0]
    losses = returns[returns < 0]

    win_count = int(len(wins))
    loss_count = int(len(losses))

    avg_win = float(np.mean(wins)) if win_count else None
    avg_loss = float(np.mean(losses)) if loss_count else None
    max_win = float(np.max(wins)) if win_count else None
    max_loss = float(np.min(losses)) if loss_count else None

    profit_factor = float(np.sum(wins) / abs(np.sum(losses))) if loss_count else None
    mdd = max_drawdown(cumulative)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "threshold": args.threshold,
        "max_uncertainty": args.max_uncertainty,
        "trades": len(df),
        "total_return": total_return,
        "avg_return_per_trade": avg_return,
        "sharpe_like": sharpe_like,
        "profit_factor": profit_factor,
        "max_drawdown": mdd,
        "win_count": win_count,
        "loss_count": loss_count,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "max_win": max_win,
        "max_loss": max_loss,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = OUT_DIR / f"trend3_fx_v2D_returns_{ts}"

    df.to_csv(base.with_suffix(".csv"), index=False)
    Path(base.with_suffix(".json")).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("[SUMMARY]")
    for k, v in summary.items():
        print(f"{k}: {v}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

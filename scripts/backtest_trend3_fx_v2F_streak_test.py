# scripts/backtest_trend3_fx_v2F_streak_test.py
# Streak analysis for Trend3 FX (v2B inverted sign)

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKTEST_V2A_PATH = REPO_ROOT / "scripts" / "backtest_trend3_fx_v2.py"


def _load_v2a():
    modname = "v2a_mod_streak"
    spec = importlib.util.spec_from_file_location(modname, str(BACKTEST_V2A_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def trend3_equal(n2: float, n1: float, n0: float) -> float:
    return (n2 + n1 + n0) / 3.0


def expected_sign_inverted(v2a, dir_: str) -> int:
    return -int(v2a.expected_fx_sign(dir_))


def compute_streaks(series: List[int]) -> Dict[str, int]:
    max_win = 0
    max_loss = 0
    current = 0

    for val in series:
        if val == 1:
            if current >= 0:
                current += 1
            else:
                current = 1
        else:
            if current <= 0:
                current -= 1
            else:
                current = -1

        max_win = max(max_win, current if current > 0 else 0)
        max_loss = min(max_loss, current if current < 0 else 0)

    return {
        "max_consecutive_wins": max_win,
        "max_consecutive_losses": abs(max_loss)
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.02)
    args = ap.parse_args()

    v2a = _load_v2a()
    scores = v2a.load_daily_scores()
    fx, _ = v2a.load_fx_thb_per_jpy()

    dates = sorted(scores.keys())
    results: List[int] = []

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

        exp = expected_sign_inverted(v2a, dir_)
        if exp == 0:
            continue

        fx0 = float(fx[d0])
        fx1 = float(fx[dn])
        delta = fx1 - fx0

        ok = (delta > 0 and exp > 0) or (delta < 0 and exp < 0)
        results.append(1 if ok else 0)

    if not results:
        raise RuntimeError("No trades generated")

    streak_stats = compute_streaks(results)

    print("[STREAK TEST]")
    print("trades:", len(results))
    print("max_consecutive_wins:", streak_stats["max_consecutive_wins"])
    print("max_consecutive_losses:", streak_stats["max_consecutive_losses"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

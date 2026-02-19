# scripts/montecarlo_trend3_fx_v2B_significance.py
# Monte Carlo significance test for Trend3 FX v2B (invert) hit-rate.
#
# This script fixes the common mistake: "randomization that doesn't change outcomes".
# We test the null hypothesis that each trade is a fair coin (p=0.5) for being correct.
# Observed: calls=N, hits=H. We compute:
#   - Monte Carlo p-value: P(H_sim >= H_obs)
#   - Exact binomial tail p-value (no scipy)
#
# Input is a backtest CSV written under:
#   analysis/prediction_backtests/trend3_fx_v2B_invert_*.csv
#
# Run examples:
#   .\.venv\Scripts\python.exe scripts\montecarlo_trend3_fx_v2B_significance.py --threshold 0.02 --iters 100000 --seed 42
#   .\.venv\Scripts\python.exe scripts\montecarlo_trend3_fx_v2B_significance.py --csv analysis/prediction_backtests/trend3_fx_v2B_invert_YYYYMMDD_HHMMSS.csv
#
from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
BT_DIR = REPO_ROOT / "analysis" / "prediction_backtests"

DEFAULT_PATTERN = "trend3_fx_v2B_invert_*.csv"
DEFAULT_OK_COL = "ok"
DEFAULT_DATE_COL = "date"


@dataclass(frozen=True)
class Observed:
    csv_path: Path
    calls: int
    hits: int
    misses: int
    hit_rate: float


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_latest_csv(pattern: str) -> Path:
    cands = sorted(BT_DIR.glob(pattern))
    if not cands:
        raise RuntimeError(
            "No backtest CSV found.\n"
            f"Looked under: {BT_DIR}\n"
            f"Pattern: {pattern}\n"
            "Tip: run backtest first:\n"
            "  .\\.venv\\Scripts\\python.exe scripts\\backtest_trend3_fx_v2B_invert.py --threshold 0.02\n"
        )
    # newest by mtime
    cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0]


def _parse_ok_value(x: str) -> Optional[int]:
    """
    Convert ok column value into 0/1, or None for no-call / empty.
    Handles: True/False, 1/0, "true"/"false", "".
    """
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return None
    if s.lower() in {"true", "t", "yes", "y"}:
        return 1
    if s.lower() in {"false", "f", "no", "n"}:
        return 0
    # numeric-ish
    try:
        v = float(s)
        if math.isnan(v) or math.isinf(v):
            return None
        return 1 if int(v) != 0 else 0
    except Exception:
        raise RuntimeError(f"Could not parse correctness value into 0/1: {x!r}")


def load_observed_from_csv(csv_path: Path, ok_col: str = DEFAULT_OK_COL) -> Observed:
    if not csv_path.exists():
        raise RuntimeError(f"CSV not found: {csv_path}")

    hits = 0
    misses = 0
    calls = 0

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise RuntimeError("CSV has no header row.")
        if ok_col not in reader.fieldnames:
            raise RuntimeError(
                f"correctness column not found: {ok_col}\n"
                f"columns={reader.fieldnames}"
            )

        for row in reader:
            ok = _parse_ok_value(row.get(ok_col, ""))
            if ok is None:
                continue
            calls += 1
            if ok == 1:
                hits += 1
            else:
                misses += 1

    if calls <= 0:
        raise RuntimeError(
            "No callable trades found in CSV (all ok were empty/nan?).\n"
            f"csv={csv_path}"
        )

    return Observed(
        csv_path=csv_path,
        calls=calls,
        hits=hits,
        misses=misses,
        hit_rate=hits / float(calls),
    )


def _binom_tail_exact(n: int, k_ge: int, p: float = 0.5) -> float:
    """
    Exact P(X >= k_ge) for X~Binomial(n,p), computed in probability space.
    For p=0.5 we can do comb/2^n safely for n<=200-ish.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError("p out of range")
    if k_ge <= 0:
        return 1.0
    if k_ge > n:
        return 0.0

    # for p=0.5: use comb / 2^n (exact-ish in float)
    if abs(p - 0.5) < 1e-12:
        denom = 2.0 ** n
        s = 0.0
        for k in range(k_ge, n + 1):
            s += math.comb(n, k) / denom
        return min(max(s, 0.0), 1.0)

    # general p: sum comb(n,k)*p^k*(1-p)^(n-k)
    s = 0.0
    for k in range(k_ge, n + 1):
        s += math.comb(n, k) * (p ** k) * ((1.0 - p) ** (n - k))
    return min(max(s, 0.0), 1.0)


def _rng(seed: int):
    # small deterministic RNG (LCG) to avoid numpy dependency for this script
    state = seed & 0xFFFFFFFF

    def rand_u32() -> int:
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return state

    def rand_float() -> float:
        return rand_u32() / 4294967296.0  # [0,1)

    return rand_float


def monte_carlo_p_value_ge_hits(n: int, hits_obs: int, iters: int, seed: int, p: float = 0.5) -> Tuple[float, int]:
    """
    Monte Carlo estimate of P(H_sim >= H_obs) with H_sim ~ Binomial(n,p).
    We implement binomial via coin flips to keep it dependency-free.
    Returns (p_value, ge_count).
    """
    if iters <= 0:
        raise ValueError("iters must be > 0")
    if n <= 0:
        raise ValueError("n must be > 0")

    rf = _rng(seed)
    ge = 0
    for _ in range(iters):
        h = 0
        # n coin flips
        for _i in range(n):
            if rf() < p:
                h += 1
        if h >= hits_obs:
            ge += 1
    return ge / float(iters), ge


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=str, default="")
    ap.add_argument("--pattern", type=str, default=DEFAULT_PATTERN)
    ap.add_argument("--ok-col", type=str, default=DEFAULT_OK_COL)
    ap.add_argument("--iters", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--p", type=float, default=0.5, help="Null probability of a correct call (default 0.5)")
    args = ap.parse_args()

    BT_DIR.mkdir(parents=True, exist_ok=True)

    if args.csv.strip():
        csv_path = (REPO_ROOT / args.csv).resolve() if not Path(args.csv).is_absolute() else Path(args.csv).resolve()
    else:
        csv_path = _find_latest_csv(args.pattern)

    obs = load_observed_from_csv(csv_path, ok_col=args.ok_col)

    p_mc, ge = monte_carlo_p_value_ge_hits(
        n=obs.calls,
        hits_obs=obs.hits,
        iters=args.iters,
        seed=args.seed,
        p=float(args.p),
    )
    p_exact = _binom_tail_exact(obs.calls, obs.hits, p=float(args.p))

    # simple normal approx z (for intuition only)
    mu = obs.calls * float(args.p)
    var = obs.calls * float(args.p) * (1.0 - float(args.p))
    z = (obs.hits - mu) / math.sqrt(var) if var > 0 else float("nan")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_base = BT_DIR / f"montecarlo_trend3_fx_v2B_{ts}"
    out_txt = out_base.with_suffix(".txt")
    out_csv = out_base.with_suffix(".csv")
    out_json = out_base.with_suffix(".json")

    # write txt
    lines: List[str] = []
    lines.append("Trend3 FX v2B (invert) - Monte Carlo significance")
    lines.append(f"run_utc: {_utc_now_iso()}")
    lines.append(f"csv: {obs.csv_path}")
    lines.append("")
    lines.append("[OBSERVED]")
    lines.append(f"calls: {obs.calls}")
    lines.append(f"hits: {obs.hits}")
    lines.append(f"misses: {obs.misses}")
    lines.append(f"hit_rate: {obs.hit_rate}")
    lines.append("")
    lines.append("[NULL]")
    lines.append(f"p_correct: {float(args.p)}")
    lines.append("")
    lines.append("[MONTE_CARLO]")
    lines.append(f"iters: {args.iters}")
    lines.append(f"seed: {args.seed}")
    lines.append(f"ge_hits_count: {ge}")
    lines.append(f"p_value_ge_observed: {p_mc}")
    lines.append("")
    lines.append("[EXACT_BINOMIAL_TAIL]")
    lines.append(f"p_value_ge_observed_exact: {p_exact}")
    lines.append("")
    lines.append("[NORMAL_APPROX (intuition)]")
    lines.append(f"z_score: {z}")
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # write csv (single-row)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "generated_at",
                "csv",
                "calls",
                "hits",
                "misses",
                "hit_rate",
                "p_null",
                "iters",
                "seed",
                "p_value_mc_ge",
                "p_value_exact_ge",
                "z_score",
            ]
        )
        w.writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                str(obs.csv_path),
                obs.calls,
                obs.hits,
                obs.misses,
                obs.hit_rate,
                float(args.p),
                args.iters,
                args.seed,
                p_mc,
                p_exact,
                z,
            ]
        )

    # write json (minimal, dependency-free)
    json_text = (
        "{\n"
        f'  "generated_at": "{datetime.now().isoformat(timespec="seconds")}",\n'
        f'  "run_utc": "{_utc_now_iso()}",\n'
        f'  "csv": "{str(obs.csv_path).replace("\\\\", "\\\\\\\\")}",\n'
        f'  "observed": {{"calls": {obs.calls}, "hits": {obs.hits}, "misses": {obs.misses}, "hit_rate": {obs.hit_rate}}},\n'
        f'  "null": {{"p_correct": {float(args.p)}}},\n'
        f'  "montecarlo": {{"iters": {args.iters}, "seed": {args.seed}, "ge": {ge}, "p_value_ge_observed": {p_mc}}},\n'
        f'  "exact": {{"p_value_ge_observed": {p_exact}}},\n'
        f'  "normal_approx": {{"z_score": {z}}}\n'
        "}\n"
    )
    out_json.write_text(json_text, encoding="utf-8")

    print("[OK] montecarlo written:")
    print(" -", out_txt)
    print(" -", out_csv)
    print(" -", out_json)
    print(f"[OBS] calls={obs.calls} hit={obs.hits} miss={obs.misses} hit_rate={obs.hit_rate}")
    print(f"[P] p_value_ge_observed_mc={p_mc}  p_value_ge_observed_exact={p_exact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

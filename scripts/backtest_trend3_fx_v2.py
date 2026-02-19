# scripts/backtest_trend3_fx_v2.py
# Trend3 FX backtest (stable v2-A)
#
# - Uses SENTIMENT daily scores (risk/positive/uncertainty/net) from:
#     data/world_politics/analysis/sentiment_YYYY-MM-DD.json
# - FX series is THB per JPY (THB/JPY) computed by:
#     1) Try dashboard CSV (auto-detect columns)
#     2) Fallback to USD cross: THB/JPY = USDTHB / USDJPY
#
# Added in v2-A:
#   --max-uncertainty  (if uncertainty > max, no-call)
#
# Run:
#   python scripts/backtest_trend3_fx_v2.py
#   python scripts/backtest_trend3_fx_v2.py --threshold 0.08
#   python scripts/backtest_trend3_fx_v2.py --max-uncertainty 0.25
#
# Output:
#   analysis/prediction_backtests/trend3_fx_v2A_YYYYMMDD_HHMMSS.{txt,csv,json}

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
ANALYSIS_DIR = REPO_ROOT / "analysis"

SENTIMENT_DIR = DATA_DIR / "world_politics" / "analysis"

FX_DASHBOARD_PATH = DATA_DIR / "fx" / "jpy_thb_remittance_dashboard.csv"
USDJPY_PATH = DATA_DIR / "fx" / "usdjpy.csv"
USDTHB_PATH = DATA_DIR / "fx" / "usdthb.csv"

OUT_DIR = ANALYSIS_DIR / "prediction_backtests"
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


# =========================
# Generic helpers
# =========================

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _to_date_str_series(s: pd.Series) -> pd.Series:
    """Ensure index is YYYY-MM-DD strings, sorted, unique last."""
    idx = pd.to_datetime(s.index, errors="coerce")
    mask = ~idx.isna()
    s2 = pd.Series(s.values[mask], index=idx[mask])
    s2 = s2.sort_index()
    s2.index = s2.index.strftime("%Y-%m-%d")
    s2 = s2[~s2.index.duplicated(keep="last")]
    s2 = s2.dropna()
    return s2


def _detect_date_col(df: pd.DataFrame) -> Optional[str]:
    candidates = ["date", "Date", "DATE", "time", "Time", "timestamp", "Timestamp"]
    for c in candidates:
        if c in df.columns:
            return c
    # heuristic: first column that can parse as datetime for most rows
    for c in df.columns[:5]:
        parsed = pd.to_datetime(df[c], errors="coerce")
        if parsed.notna().mean() >= 0.7:
            return c
    return None


def _pick_best_numeric_col(df: pd.DataFrame) -> Optional[str]:
    """
    Choose best numeric column from dashboard-like CSV.
    Preference by common names, else pick the numeric column with most non-null.
    """
    preferred = [
        "thb_per_jpy",
        "THB_per_JPY",
        "thb_jpy",
        "thb_per_jpy_mid",
        "rate",
        "Rate",
        "close",
        "Close",
        "value",
        "Value",
        "mid",
        "Mid",
        "jpy_thb",
        "JPYTHB",
        "thbperjpy",
    ]
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        # try to coerce
        tmp = df.copy()
        for c in df.columns:
            tmp[c] = pd.to_numeric(tmp[c], errors="coerce")
        numeric_cols = [c for c in tmp.columns if pd.api.types.is_numeric_dtype(tmp[c]) and tmp[c].notna().any()]
        df = tmp

    if not numeric_cols:
        return None

    for c in preferred:
        if c in numeric_cols:
            return c

    # heuristic by name contains
    name_hits = []
    for c in numeric_cols:
        lc = str(c).lower()
        score = 0
        if "thb" in lc:
            score += 3
        if "jpy" in lc:
            score += 3
        if "per" in lc or "rate" in lc:
            score += 2
        if "close" in lc or "mid" in lc:
            score += 1
        name_hits.append((score, c))
    name_hits.sort(reverse=True)
    if name_hits and name_hits[0][0] > 0:
        return name_hits[0][1]

    # fallback: most populated numeric column
    best = max(numeric_cols, key=lambda c: df[c].notna().sum())
    return best


def _load_timeseries_csv(path: Path) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Load a generic timeseries CSV:
    - detect date column
    - detect best numeric column
    Return (Series, debug_dict)
    """
    dbg: Dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        dbg["error"] = "missing"
        return pd.Series(dtype=float), dbg

    df = pd.read_csv(path)
    dbg["columns"] = list(df.columns)

    date_col = _detect_date_col(df)
    dbg["date_col"] = date_col
    if not date_col:
        dbg["error"] = "no_date_col"
        return pd.Series(dtype=float), dbg

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).sort_values(date_col)

    # coerce numeric
    for c in df.columns:
        if c == date_col:
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")

    num_col = _pick_best_numeric_col(df)
    dbg["value_col"] = num_col
    if not num_col:
        dbg["error"] = "no_numeric_col"
        return pd.Series(dtype=float), dbg

    s = pd.Series(df[num_col].values, index=df[date_col].values)
    s = _to_date_str_series(s)
    dbg["points"] = int(len(s))
    dbg["min_date"] = (min(s.index) if len(s) else None)
    dbg["max_date"] = (max(s.index) if len(s) else None)
    return s, dbg


# =========================
# Sentiment (scores) loader
# =========================

@dataclass(frozen=True)
class DailyScore:
    date: str
    risk: float
    positive: float
    uncertainty: float
    source_path: str

    @property
    def net(self) -> float:
        return self.positive - self.risk


def _extract_scores_from_sentiment_json(j: Dict[str, Any]) -> Optional[Tuple[float, float, float]]:
    """
    Prefer j['summary'] if present, else attempt derive from items/net.
    Returns (risk, positive, uncertainty).
    """
    if isinstance(j.get("summary"), dict):
        s = j["summary"]
        r = _safe_float(s.get("risk"))
        p = _safe_float(s.get("positive") if s.get("positive") is not None else s.get("pos"))
        u = _safe_float(s.get("uncertainty") if s.get("uncertainty") is not None else s.get("unc"))
        n = _safe_float(s.get("net"))
        if r is not None and p is not None:
            return float(r), float(p), float(u or 0.0)
        if n is not None:
            net = float(n)
            return max(0.0, -net), max(0.0, net), float(u or 0.0)

    items = j.get("items")
    if isinstance(items, list) and items:
        nets: List[float] = []
        uncs: List[float] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            n = _safe_float(it.get("net"))
            if n is None and isinstance(it.get("sentiment"), dict):
                n = _safe_float(it["sentiment"].get("net"))
            if n is not None:
                nets.append(float(n))
            u = _safe_float(it.get("uncertainty"))
            if u is None:
                u = _safe_float(it.get("unc"))
            if u is not None:
                uncs.append(float(u))

        if nets:
            net = sum(nets) / len(nets)
            unc = (sum(uncs) / len(uncs)) if uncs else 0.0
            return max(0.0, -net), max(0.0, net), float(unc)

    return None


def load_daily_scores() -> Dict[str, DailyScore]:
    scores: Dict[str, DailyScore] = {}
    for p in sorted(SENTIMENT_DIR.glob("sentiment_????-??-??.json")):
        try:
            j = _read_json(p)
        except Exception:
            continue

        date = j.get("date")
        if not isinstance(date, str) or not DATE_RE.search(date):
            m = DATE_RE.search(p.name)
            if not m:
                continue
            date = m.group(1)

        s = _extract_scores_from_sentiment_json(j)
        if not s:
            continue
        risk, pos, unc = s
        scores[date] = DailyScore(
            date=date,
            risk=float(risk),
            positive=float(pos),
            uncertainty=float(unc),
            source_path=str(p),
        )

    return scores


# =========================
# FX loader (dashboard -> cross fallback)
# =========================

def load_fx_thb_per_jpy() -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Return THB/JPY time series as Series indexed by YYYY-MM-DD.
    Strategy:
      1) dashboard
      2) cross = USDTHB / USDJPY
    """
    dbg: Dict[str, Any] = {"strategy": None, "dashboard": None, "cross": None}

    # 1) dashboard
    dash, dash_dbg = _load_timeseries_csv(FX_DASHBOARD_PATH)
    dbg["dashboard"] = dash_dbg
    if len(dash) >= 10:
        dbg["strategy"] = "dashboard"
        return dash, dbg

    # 2) cross
    usdjpy, jpy_dbg = _load_timeseries_csv(USDJPY_PATH)
    usdthb, thb_dbg = _load_timeseries_csv(USDTHB_PATH)
    dbg["cross"] = {"usdjpy": jpy_dbg, "usdthb": thb_dbg}

    if len(usdjpy) < 10 or len(usdthb) < 10:
        dbg["strategy"] = "none"
        return pd.Series(dtype=float), dbg

    # Align intersection of dates
    common = sorted(set(usdjpy.index).intersection(set(usdthb.index)))
    if len(common) < 10:
        dbg["strategy"] = "none"
        dbg["cross"]["common_points"] = len(common)
        return pd.Series(dtype=float), dbg

    # THB/JPY = (THB/USD) / (JPY/USD) = USDTHB / USDJPY
    cross_vals = []
    cross_idx = []
    for d in common:
        jv = _safe_float(usdjpy[d])
        tv = _safe_float(usdthb[d])
        if jv is None or tv is None or jv == 0:
            continue
        cross_idx.append(d)
        cross_vals.append(float(tv) / float(jv))

    s = pd.Series(cross_vals, index=cross_idx)
    s = s.sort_index()
    s = s[~s.index.duplicated(keep="last")]
    s = s.dropna()

    dbg["strategy"] = "usd_cross"
    dbg["cross"]["points"] = int(len(s))
    dbg["cross"]["min_date"] = (min(s.index) if len(s) else None)
    dbg["cross"]["max_date"] = (max(s.index) if len(s) else None)
    return s, dbg


# =========================
# Trend3 backtest
# =========================

def trend3(a: float, b: float, c: float) -> float:
    return (a + 2.0 * b + 3.0 * c) / 6.0


def direction(tr3: float, threshold: float) -> str:
    if tr3 > threshold:
        return "RISK_ON"
    if tr3 < -threshold:
        return "RISK_OFF"
    return "NEUTRAL"


def expected_fx_sign(direction_: str) -> int:
    """
    We evaluate THB/JPY next-day change:
      - RISK_OFF expects THB/JPY up (+1)  (JPY weak vs THB or THB strong vs JPY)
      - RISK_ON expects THB/JPY down (-1)
    """
    if direction_ == "RISK_OFF":
        return +1
    if direction_ == "RISK_ON":
        return -1
    return 0


def write_outputs(df: pd.DataFrame, meta: Dict[str, Any], prefix: str) -> Dict[str, str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = OUT_DIR / f"{prefix}_{ts}"
    p_txt = str(base.with_suffix(".txt"))
    p_csv = str(base.with_suffix(".csv"))
    p_json = str(base.with_suffix(".json"))

    df.to_csv(p_csv, index=False)

    payload = {
        "meta": meta,
        "rows": df.to_dict(orient="records"),
    }
    Path(p_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # human-readable txt
    calls = df[df["outcome"].isin(["HIT", "MISS"])]
    hit = int((calls["outcome"] == "HIT").sum())
    miss = int((calls["outcome"] == "MISS").sum())
    total = int(len(calls))
    hit_rate = (hit / total) if total else None

    lines: List[str] = []
    lines.append("Trend3 FX backtest v2-A")
    lines.append(f"run_utc: {meta.get('run_utc')}")
    lines.append(f"threshold: {meta.get('threshold')}")
    lines.append(f"max_uncertainty: {meta.get('max_uncertainty')}")
    lines.append(f"fx_strategy: {meta.get('fx_strategy')}")
    lines.append("")
    lines.append(f"SUMMARY: calls={total} hit={hit} miss={miss} hit_rate={hit_rate}")
    lines.append("")
    lines.append("TOP 20 rows:")
    lines.append("date,uncertainty,trend3,direction,fx0,fx1,delta_next,outcome")
    for _, r in df.head(20).iterrows():
        lines.append(
            f"{r['date']},{r['uncertainty']:.6f},{r['trend3']:.6f},{r['direction']},"
            f"{r['fx0']:.6f},{r['fx1']:.6f},{r['delta_next']:.6f},{r['outcome']}"
        )

    Path(p_txt).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"txt": p_txt, "csv": p_csv, "json": p_json}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.08)
    ap.add_argument("--max-uncertainty", type=float, default=None)
    ap.add_argument("--min-calls", type=int, default=1)
    args = ap.parse_args()

    scores = load_daily_scores()
    if len(scores) < 5:
        raise RuntimeError(f"Not enough sentiment days found (got {len(scores)}). Check sentiment_YYYY-MM-DD.json files.")

    fx, fx_dbg = load_fx_thb_per_jpy()
    if len(fx) < 10:
        # emit debug report for quick diagnosis
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dbg_path = OUT_DIR / f"fx_series_debug_{ts}.json"
        dbg_path.write_text(json.dumps(fx_dbg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(
            "FX data not available (dashboard too short and cross fallback failed).\n"
            f"Debug written: {dbg_path}"
        )

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

        tr = trend3(s2.net, s1.net, s0.net)
        dir_ = direction(tr, args.threshold)

        # --- uncertainty filter ---
        if args.max_uncertainty is not None and s0.uncertainty > float(args.max_uncertainty):
            dir_ = "NEUTRAL"

        fx0 = float(fx[d0])
        fx1 = float(fx[dn])
        delta = fx1 - fx0

        exp = expected_fx_sign(dir_)
        outcome = "NO_CALL"
        hit = None

        if exp != 0:
            ok = (delta > 0 and exp > 0) or (delta < 0 and exp < 0)
            outcome = "HIT" if ok else "MISS"
            hit = 1 if ok else 0

        rows.append(
            {
                "date": d0,
                "uncertainty": float(s0.uncertainty),
                "risk": float(s0.risk),
                "positive": float(s0.positive),
                "net": float(s0.net),
                "trend3": float(tr),
                "direction": dir_,
                "fx0": fx0,
                "fx1": fx1,
                "delta_next": float(delta),
                "outcome": outcome,
                "hit": hit,
            }
        )

    if not rows:
        raise RuntimeError("No aligned rows (sentiment dates and fx dates did not overlap).")

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    calls = df[df["outcome"].isin(["HIT", "MISS"])]
    hit = int((calls["outcome"] == "HIT").sum())
    miss = int((calls["outcome"] == "MISS").sum())
    total = int(len(calls))
    hit_rate = (hit / total) if total else None

    meta: Dict[str, Any] = {
        "run_utc": _now_utc_iso(),
        "threshold": float(args.threshold),
        "max_uncertainty": (float(args.max_uncertainty) if args.max_uncertainty is not None else None),
        "fx_strategy": fx_dbg.get("strategy"),
        "fx_debug": fx_dbg,
        "sentiment_days": int(len(scores)),
        "fx_points": int(len(fx)),
        "rows_total": int(len(df)),
        "calls": total,
        "hit": hit,
        "miss": miss,
        "hit_rate": hit_rate,
    }

    files = write_outputs(df, meta, prefix="trend3_fx_v2A")

    print("[OK] backtest written:")
    print(" -", files["txt"])
    print(" -", files["csv"])
    print(" -", files["json"])
    print(f"[SUMMARY] calls={total} hit={hit} miss={miss} hit_rate={hit_rate}")

    # Optional guard: ensure at least min calls
    if total < int(args.min_calls):
        raise RuntimeError(f"Too few calls ({total}) < --min-calls {args.min_calls}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

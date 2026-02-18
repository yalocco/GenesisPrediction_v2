# scripts/backtest_trend3_fx_v2.py
# Trend3 FX backtest (research tool)
#
# - Uses sentiment_YYYY-MM-DD.json as score source (summary preferred; items aggregate fallback)
# - Compares Trend3 direction (weighted 1:2:3 over net[t-2..t]) vs next-day THB/JPY change
# - Default threshold = 0.08 (from sweep)
# - Writes txt/csv/json under analysis/prediction_backtests/
#
# Run:
#   .\.venv\Scripts\python.exe scripts\backtest_trend3_fx_v2.py
#   .\.venv\Scripts\python.exe scripts\backtest_trend3_fx_v2.py --threshold 0.05
#   .\.venv\Scripts\python.exe scripts\backtest_trend3_fx_v2.py --start 2026-01-01 --end 2026-02-18

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


# ----------------------------
# Paths
# ----------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
ANALYSIS_DIR = REPO_ROOT / "analysis"

SENTIMENT_DIR = DATA_DIR / "world_politics" / "analysis"
SENTIMENT_LATEST = SENTIMENT_DIR / "sentiment_latest.json"

FX_DASHBOARD_PATH = DATA_DIR / "fx" / "jpy_thb_remittance_dashboard.csv"
USDTHB_PATH = DATA_DIR / "fx" / "usdthb.csv"
USDJPY_PATH = DATA_DIR / "fx" / "usdjpy.csv"

OUT_DIR = ANALYSIS_DIR / "prediction_backtests"

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


# ----------------------------
# Helpers
# ----------------------------

def _parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_outdir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def _walk_get(d: Any, path: List[str]) -> Any:
    cur = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        if k not in cur:
            return None
        cur = cur[k]
    return cur


# ----------------------------
# Score source: sentiment_YYYY-MM-DD.json
# ----------------------------

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


def _extract_from_summary(j: Dict[str, Any]) -> Optional[Tuple[float, float, float]]:
    summary = j.get("summary")
    if not isinstance(summary, dict):
        return None

    r = _safe_float(summary.get("risk"))
    p = _safe_float(summary.get("positive"))
    if p is None:
        p = _safe_float(summary.get("pos"))

    u = _safe_float(summary.get("uncertainty"))
    if u is None:
        u = _safe_float(summary.get("unc"))

    n = _safe_float(summary.get("net"))

    # direct (risk,pos)
    if r is not None and p is not None:
        return (float(r), float(p), float(u) if u is not None else 0.0)

    # fallback from net
    if n is not None:
        net = float(n)
        risk = max(0.0, -net)
        pos = max(0.0, net)
        return (risk, pos, float(u) if u is not None else 0.0)

    return None


def _extract_from_items_aggregate(j: Dict[str, Any]) -> Optional[Tuple[float, float, float]]:
    items = j.get("items")
    if not isinstance(items, list) or not items:
        return None

    nets: List[float] = []
    uncs: List[float] = []

    for it in items:
        if not isinstance(it, dict):
            continue
        n = _safe_float(it.get("net"))
        if n is None:
            n = _safe_float(_walk_get(it, ["sentiment", "net"]))
        if n is not None:
            nets.append(float(n))

        u = _safe_float(it.get("uncertainty"))
        if u is None:
            u = _safe_float(it.get("unc"))
        if u is not None:
            uncs.append(float(u))

    if not nets:
        return None

    net = sum(nets) / len(nets)
    risk = max(0.0, -net)
    pos = max(0.0, net)
    unc = (sum(uncs) / len(uncs)) if uncs else 0.0
    return (risk, pos, float(unc))


def _load_one_sentiment_file(p: Path) -> Optional[DailyScore]:
    try:
        j = _read_json(p)
    except Exception:
        return None
    if not isinstance(j, dict):
        return None

    date = j.get("date")
    if not isinstance(date, str) or not DATE_RE.fullmatch(date):
        m = DATE_RE.search(p.name)
        if m:
            date = m.group(1)
        else:
            return None

    scores = _extract_from_summary(j)
    if scores is None:
        scores = _extract_from_items_aggregate(j)
    if scores is None:
        return None

    risk, pos, unc = scores
    return DailyScore(
        date=str(date),
        risk=float(risk),
        positive=float(pos),
        uncertainty=float(unc),
        source_path=str(p),
    )


def _find_sentiment_files() -> List[Path]:
    files: List[Path] = []
    if SENTIMENT_DIR.exists():
        files.extend(sorted(SENTIMENT_DIR.glob("sentiment_????-??-??.json")))
    return files


def load_daily_scores(start: Optional[str], end: Optional[str]) -> Tuple[Dict[str, DailyScore], Dict[str, Any]]:
    files = _find_sentiment_files()
    start_dt = _parse_date(start) if start else None
    end_dt = _parse_date(end) if end else None

    out: Dict[str, DailyScore] = {}
    skipped = 0
    examples: List[Dict[str, Any]] = []

    for p in files:
        m = DATE_RE.search(p.name)
        if not m:
            continue
        d = m.group(1)
        dt = _parse_date(d)
        if start_dt and dt < start_dt:
            continue
        if end_dt and dt > end_dt:
            continue

        ds = _load_one_sentiment_file(p)
        if ds is None:
            skipped += 1
            if len(examples) < 5:
                examples.append({"file": str(p), "reason": "cannot_extract_scores"})
            continue
        out[ds.date] = ds

    # allow sentiment_latest as an extra point if it has a new date
    latest_used = False
    if SENTIMENT_LATEST.exists():
        ds = _load_one_sentiment_file(SENTIMENT_LATEST)
        if ds is not None and ds.date not in out:
            dt = _parse_date(ds.date)
            ok = True
            if start_dt and dt < start_dt:
                ok = False
            if end_dt and dt > end_dt:
                ok = False
            if ok:
                out[ds.date] = ds
                latest_used = True

    diag = {
        "sentiment_dir": str(SENTIMENT_DIR),
        "sentiment_files_found": len(files),
        "sentiment_latest_used": latest_used,
        "dates_loaded": len(out),
        "skipped": skipped,
        "examples_skipped": examples,
    }
    return out, diag


# ----------------------------
# FX realized THB/JPY series
# ----------------------------

def _detect_date_col(df: pd.DataFrame) -> Optional[str]:
    for c in ["date", "Date", "DATE", "day", "Day", "DAY"]:
        if c in df.columns:
            return c
    for c in df.columns:
        try:
            pd.to_datetime(df[c], errors="raise")
            return c
        except Exception:
            continue
    return None


def _pick_numeric_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _load_fx_from_dashboard() -> Optional[pd.Series]:
    if not FX_DASHBOARD_PATH.exists():
        return None

    df = pd.read_csv(FX_DASHBOARD_PATH)
    date_col = _detect_date_col(df)
    if not date_col:
        return None

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).copy()
    df["date"] = df[date_col].dt.strftime("%Y-%m-%d")

    numeric_cols = _pick_numeric_cols(df)
    preferred = [
        "thb_per_jpy", "THB_PER_JPY",
        "thb_jpy", "THBJPY",
        "jpy_thb", "JPYTHB",
        "rate", "RATE",
        "fx", "FX",
        "jpy_to_thb", "JPY_TO_THB",
    ]
    col = None
    for name in preferred:
        if name in df.columns and name in numeric_cols:
            col = name
            break

    if col is None and numeric_cols:
        # heuristic pick
        best = None
        best_score = -1.0
        for c in numeric_cols:
            s = pd.to_numeric(df[c], errors="coerce").dropna()
            if s.empty:
                continue
            med = float(s.median())
            if med <= 0:
                continue
            score = 0.0
            if 0.05 <= med <= 5.0:
                score += 2.0
            if 0.1 <= med <= 1.0:
                score += 1.0
            score += 0.1 * min(60, len(s))
            if score > best_score:
                best_score = score
                best = c
        col = best

    if col is None:
        return None

    ser = pd.to_numeric(df[col], errors="coerce")
    out = pd.Series(ser.values, index=df["date"].values, dtype="float64")
    out = out[~out.index.duplicated(keep="last")]
    out = out.dropna()
    return out.sort_index()


def _load_fx_pair_csv(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    date_col = _detect_date_col(df)
    if not date_col:
        return None
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).copy()
    df["date"] = df[date_col].dt.strftime("%Y-%m-%d")

    numeric_cols = _pick_numeric_cols(df)
    preferred = ["close", "Close", "CLOSE", "rate", "Rate", "RATE", "value", "Value", "VALUE"]
    col = None
    for c in preferred:
        if c in df.columns and c in numeric_cols:
            col = c
            break
    if col is None and numeric_cols:
        col = numeric_cols[0]
    if col is None:
        return None

    df["v"] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["v"])
    return df[["date", "v"]].drop_duplicates(subset=["date"], keep="last")


def _load_fx_from_usd_cross() -> Optional[pd.Series]:
    a = _load_fx_pair_csv(USDTHB_PATH)
    b = _load_fx_pair_csv(USDJPY_PATH)
    if a is None or b is None:
        return None
    m = a.merge(b, on="date", how="inner", suffixes=("_usdthb", "_usdjpy"))
    if m.empty:
        return None
    m["thb_per_jpy"] = m["v_usdthb"] / m["v_usdjpy"]
    s = pd.Series(m["thb_per_jpy"].values, index=m["date"].values, dtype="float64")
    s = s.dropna()
    s = s[~s.index.duplicated(keep="last")]
    return s.sort_index()


def load_fx_thb_per_jpy() -> Tuple[pd.Series, str]:
    s = _load_fx_from_dashboard()
    if s is not None and len(s) >= 10:
        return s, str(FX_DASHBOARD_PATH)
    s2 = _load_fx_from_usd_cross()
    if s2 is not None and len(s2) >= 10:
        return s2, "usd_cross"
    raise FileNotFoundError(
        "FX series not found. Expected either dashboard or cross:\n"
        f"  - {FX_DASHBOARD_PATH}\n"
        f"  - {USDTHB_PATH}\n"
        f"  - {USDJPY_PATH}\n"
    )


# ----------------------------
# Trend3 logic (research)
# ----------------------------

def trend3_weighted(net_t2: float, net_t1: float, net_t0: float) -> float:
    return (1.0 * net_t2 + 2.0 * net_t1 + 3.0 * net_t0) / 6.0


def direction_from_trend(trend3: float, threshold: float) -> str:
    if trend3 > threshold:
        return "RISK_ON"
    if trend3 < -threshold:
        return "RISK_OFF"
    return "NEUTRAL"


def expected_fx_sign(direction: str) -> int:
    # THB/JPY up => JPY weaker => risk-off in our heuristic
    if direction == "RISK_OFF":
        return +1
    if direction == "RISK_ON":
        return -1
    return 0


def _sorted_dates(dates: Iterable[str]) -> List[str]:
    return sorted(dates, key=lambda x: _parse_date(x))


def run_backtest(scores: Dict[str, DailyScore], fx: pd.Series, threshold: float) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    all_dates = _sorted_dates(scores.keys())
    fx_idx = set(map(str, fx.index))

    rows: List[Dict[str, Any]] = []
    for i in range(2, len(all_dates) - 1):
        d_t2 = all_dates[i - 2]
        d_t1 = all_dates[i - 1]
        d_t0 = all_dates[i]
        d_tn = all_dates[i + 1]

        if d_t0 not in fx_idx or d_tn not in fx_idx:
            continue

        s2 = scores[d_t2]
        s1 = scores[d_t1]
        s0 = scores[d_t0]

        tr3 = trend3_weighted(s2.net, s1.net, s0.net)
        direction = direction_from_trend(tr3, threshold)

        fx0 = float(fx.loc[d_t0])
        fx1 = float(fx.loc[d_tn])
        delta = fx1 - fx0

        exp = expected_fx_sign(direction)

        outcome = "NO_CALL"
        hit: Optional[int] = None
        if exp != 0:
            if delta == 0:
                outcome = "TIE"
                hit = 0
            else:
                ok = (delta > 0 and exp > 0) or (delta < 0 and exp < 0)
                outcome = "HIT" if ok else "MISS"
                hit = 1 if ok else 0

        rows.append(
            {
                "date": d_t0,
                "date_next": d_tn,
                "risk": s0.risk,
                "positive": s0.positive,
                "uncertainty": s0.uncertainty,
                "net": s0.net,
                "net_t-1": s1.net,
                "net_t-2": s2.net,
                "trend3": tr3,
                "direction": direction,
                "sentiment_source": s0.source_path,
                "fx_thb_per_jpy": fx0,
                "fx_thb_per_jpy_next": fx1,
                "fx_delta_next": delta,
                "outcome": outcome,
                "hit": hit,
            }
        )

    df = pd.DataFrame(rows)

    calls = df[df["outcome"].isin(["HIT", "MISS"])].copy()
    neutral = df[df["outcome"] == "NO_CALL"].copy()

    hit_n = int((calls["outcome"] == "HIT").sum()) if len(calls) else 0
    miss_n = int((calls["outcome"] == "MISS").sum()) if len(calls) else 0
    calls_n = int(len(calls))
    hit_rate = (hit_n / calls_n) if calls_n > 0 else None

    meta: Dict[str, Any] = {
        "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "threshold": float(threshold),
        "fx_source": None,  # filled by caller
        "fx_series_points": int(len(fx)),
        "score_points": int(len(scores)),
        "metrics": {
            "rows_total": int(len(df)),
            "calls": calls_n,
            "neutral_count": int(len(neutral)),
            "hit": hit_n,
            "miss": miss_n,
            "hit_rate": hit_rate,
        },
        "notes": {
            "direction_rule": "trend3 > +threshold => RISK_ON; trend3 < -threshold => RISK_OFF; else NEUTRAL",
            "trend3_rule": "trend3=(net[t-2]+2*net[t-1]+3*net[t])/6",
            "net_rule": "net=positive-risk",
            "fx_rule": "delta_next = fx[t+1]-fx[t] (THB/JPY)",
            "hit_rule": "RISK_OFF expects delta_next>0; RISK_ON expects delta_next<0; NEUTRAL is NO_CALL",
        },
    }
    return df, meta


def write_outputs(df: pd.DataFrame, meta: Dict[str, Any], diag: Dict[str, Any]) -> Tuple[Path, Path, Path]:
    _ensure_outdir()
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = OUT_DIR / f"trend3_fx_v2_{run_ts}"

    csv_path = base.with_suffix(".csv")
    json_path = base.with_suffix(".json")
    txt_path = base.with_suffix(".txt")

    df.to_csv(csv_path, index=False, encoding="utf-8")

    payload = dict(meta)
    payload["diag"] = diag
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    m = meta["metrics"]
    lines: List[str] = []
    lines.append("GenesisPrediction v2 - Backtest (Trend3 FX) v2")
    lines.append(f"run_utc: {meta['run_utc']}")
    lines.append(f"threshold: {meta['threshold']}")
    lines.append(f"fx_source: {meta['fx_source']}")
    lines.append(f"rows_total: {m['rows_total']}")
    lines.append(f"calls: {m['calls']}")
    lines.append(f"neutral_count: {m['neutral_count']}")
    lines.append(f"hit: {m['hit']}")
    lines.append(f"miss: {m['miss']}")
    lines.append(f"hit_rate: {m['hit_rate']}")
    lines.append("")
    lines.append("DIAG")
    lines.append(json.dumps(diag, ensure_ascii=False, indent=2))
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return txt_path, csv_path, json_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.08, help="direction threshold for trend3")
    ap.add_argument("--start", type=str, default=None, help="start date YYYY-MM-DD")
    ap.add_argument("--end", type=str, default=None, help="end date YYYY-MM-DD")
    args = ap.parse_args()

    scores, diag = load_daily_scores(start=args.start, end=args.end)
    if len(scores) < 5:
        raise RuntimeError(f"Not enough sentiment dates loaded (got {len(scores)}). diag={diag}")

    fx, fx_source = load_fx_thb_per_jpy()
    df, meta = run_backtest(scores=scores, fx=fx, threshold=float(args.threshold))
    meta["fx_source"] = fx_source

    txt_path, csv_path, json_path = write_outputs(df, meta, diag)

    print("[OK] backtest written:")
    print(" -", txt_path)
    print(" -", csv_path)
    print(" -", json_path)

    m = meta["metrics"]
    print(f"[SUMMARY] calls={m['calls']} hit={m['hit']} miss={m['miss']} hit_rate={m['hit_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

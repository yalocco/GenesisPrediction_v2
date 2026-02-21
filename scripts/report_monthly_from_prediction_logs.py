#!/usr/bin/env python3
"""
report_monthly_from_prediction_logs.py

Reads:
    analysis/prediction_logs/prediction_log_YYYY-MM-DD.json

Produces:
    analysis/prediction_reports/monthly_trend3_fx_latest.json
    analysis/prediction_reports/monthly_trend3_fx_latest.csv

Specification (v1):
- trade = row where hit is 0 or 1
- return = delta_next
- Sharpe-like = mean(day_return) / std(day_return)
- Max Drawdown computed on cumulative day_return curve
"""

import json
import math
import statistics
from pathlib import Path
from datetime import datetime, timezone
import csv


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "analysis" / "prediction_logs"
OUT_DIR = ROOT / "analysis" / "prediction_reports"

REPORT_SCHEMA_VERSION = 1


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def compute_max_drawdown(equity_curve):
    peak = -float("inf")
    max_dd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        dd = peak - v
        max_dd = max(max_dd, dd)
    return max_dd


def load_prediction_logs():
    files = sorted(LOG_DIR.glob("prediction_log_*.json"))
    logs = []

    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        date_utc = data.get("date_utc")
        if not date_utc:
            continue

        details = data.get("prediction", {}).get("details", {})
        rows = details.get("rows", [])

        trades = []
        wins = 0
        losses = 0

        for r in rows:
            hit = r.get("hit")
            delta = safe_float(r.get("delta_next"))

            # trade definition: hit must be 0/1 and delta must exist
            if hit is None or delta is None:
                continue
            if isinstance(hit, float) and math.isnan(hit):
                continue
            if hit in (0, 1, 0.0, 1.0):
                trades.append(delta)
                if float(hit) == 1.0:
                    wins += 1
                else:
                    losses += 1

        day_return = sum(trades)

        logs.append(
            {
                "date": date_utc,
                "month": date_utc[:7],
                "trades": len(trades),
                "wins": wins,
                "losses": losses,
                "day_return": day_return,
                "trade_returns": trades,
            }
        )

    return logs


def aggregate_monthly(daily_logs):
    monthly = {}
    for d in daily_logs:
        monthly.setdefault(d["month"], []).append(d)

    results = []

    for month, days in sorted(monthly.items()):
        days_total = len(days)
        days_with_trades = sum(1 for d in days if d["trades"] > 0)

        trades_total = sum(d["trades"] for d in days)
        wins_total = sum(d["wins"] for d in days)
        losses_total = sum(d["losses"] for d in days)

        all_trade_returns = []
        for d in days:
            all_trade_returns.extend(d["trade_returns"])

        total_return = sum(d["day_return"] for d in days)

        win_rate_total = wins_total / trades_total if trades_total > 0 else 0.0
        avg_return_per_trade = (
            sum(all_trade_returns) / trades_total if trades_total > 0 else 0.0
        )

        pos_sum = sum(x for x in all_trade_returns if x > 0)
        neg_sum = sum(x for x in all_trade_returns if x < 0)
        profit_factor = pos_sum / abs(neg_sum) if neg_sum < 0 else None

        # Sharpe-like (daily basis): mean(day_return)/pstdev(day_return)
        day_returns = [d["day_return"] for d in days]
        if len(day_returns) > 1:
            denom = statistics.pstdev(day_returns)
            sharpe_like = statistics.mean(day_returns) / denom if denom != 0 else None
        else:
            sharpe_like = None

        # Max drawdown (daily cumulative)
        equity = []
        cumulative = 0.0
        for r in day_returns:
            cumulative += r
            equity.append(cumulative)
        max_dd = compute_max_drawdown(equity) if equity else 0.0

        results.append(
            {
                "month": month,
                "days_total": days_total,
                "days_with_trades": days_with_trades,
                "call_rate_by_day": (days_with_trades / days_total if days_total > 0 else 0.0),
                "trades_total": trades_total,
                "wins_total": wins_total,
                "losses_total": losses_total,
                "win_rate_total": win_rate_total,
                "total_return": total_return,
                "avg_return_per_trade": avg_return_per_trade,
                "profit_factor_month": profit_factor,
                "monthly_sharpe_like": sharpe_like,
                "monthly_max_drawdown": max_dd,
            }
        )

    return results


def save_outputs(results):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    latest_json = OUT_DIR / "monthly_trend3_fx_latest.json"
    latest_csv = OUT_DIR / "monthly_trend3_fx_latest.csv"

    generated_at_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    payload = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc,
        "months": results,
    }

    with open(latest_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    if results:
        keys = list(results[0].keys())
        with open(latest_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)


def main():
    daily_logs = load_prediction_logs()
    results = aggregate_monthly(daily_logs)
    save_outputs(results)
    print("[OK] monthly report generated")
    print(f" months={len(results)}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scripts/build_global_status_latest.py
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RISK_ORDER = {
    "low": 0,
    "guarded": 1,
    "elevated": 2,
    "high": 3,
    "critical": 4,
}


@dataclass
class LoadedJson:
    path: str
    data: dict[str, Any] | None


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    for enc in ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be"]:
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            continue
    return None


def _load_first(root: Path, candidates: list[str]) -> LoadedJson:
    for rel in candidates:
        p = root / rel
        data = _read_json(p)
        if isinstance(data, dict):
            return LoadedJson(path=rel.replace("\\", "/"), data=data)
    return LoadedJson(path="", data=None)


def _safe_number(value: Any, fallback=None):
    try:
        return float(value)
    except Exception:
        return fallback


def _first_non_empty(*values):
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


# ---------------- FX ----------------
def _derive_fx_value(fx_decision: dict | None):
    if not isinstance(fx_decision, dict):
        return "--", "fx decision unavailable"

    value = _first_non_empty(
        fx_decision.get("primary"),
        fx_decision.get("decision"),
        fx_decision.get("status"),
        fx_decision.get("regime"),
    ).upper()

    sub = _first_non_empty(
        fx_decision.get("reason"),
        fx_decision.get("note"),
        fx_decision.get("action"),
    )

    return value or "--", sub or "fx decision latest"


# ---------------- MAIN ----------------
def build_global_status(root: Path):

    prediction = _load_first(root, [
        "analysis/prediction/prediction_latest.json",
        "analysis/prediction_latest.json",
    ]).data

    scenario = _load_first(root, [
        "analysis/prediction/scenario_latest.json",
    ]).data

    signal = _load_first(root, [
        "analysis/prediction/signal_latest.json",
    ]).data

    summary = _load_first(root, [
        "analysis/daily_summary_latest.json",
    ]).data

    sentiment = _load_first(root, [
        "analysis/sentiment_latest.json",
    ]).data

    health = _load_first(root, [
        "analysis/health_latest.json",
    ]).data

    # ★★★ ここが修正ポイント ★★★
    fx_decision = _load_first(root, [
        "analysis/fx/fx_decision_latest.json",
    ]).data

    fx_value, fx_sub = _derive_fx_value(fx_decision)

    return {
        "fx_regime": fx_value,
        "fx_regime_sub": fx_sub,
    }


def main():
    root = Path(".").resolve()
    out = root / "analysis/global_status_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = build_global_status(root)

    out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    print("[OK] global_status_latest updated")


if __name__ == "__main__":
    main()
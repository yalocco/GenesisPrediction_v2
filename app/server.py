# app/server.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent

STATIC_DIR = APP_DIR / "static"
ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"

# ✅ ViewModel is here (your build_digest_view_model.py writes here)
VIEWMODEL_DIR = ROOT / "data" / "digest" / "view"

app = FastAPI(title="GenesisPrediction v2")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
# 🔎 analysis 配下のファイルをブラウザで直読みできる（/analysis/...）
app.mount("/analysis", StaticFiles(directory=str(ANALYSIS_DIR)), name="analysis")


def _latest_json_in(dir_path: Path) -> Path | None:
    if not dir_path.exists():
        return None
    cands = sorted(dir_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def _view_model_path_by_date(date_str: str) -> Path | None:
    # primary
    p1 = VIEWMODEL_DIR / f"{date_str}.json"
    if p1.exists():
        return p1
    # legacy fallback (if any)
    p2 = VIEWMODEL_DIR / f"digest_view_model_{date_str}.json"
    if p2.exists():
        return p2
    return None


def _fx_decision_path_by_date(date_str: str) -> Path | None:
    # primary (dated)
    p1 = ANALYSIS_DIR / f"fx_decision_{date_str}.json"
    if p1.exists():
        return p1
    # fallback (latest)
    p2 = ANALYSIS_DIR / "fx_decision_latest.json"
    if p2.exists():
        return p2
    return None


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    # simple redirect page
    return '<meta http-equiv="refresh" content="0; url=/static/index.html" />'


@app.get("/api/view_model/{date_str}")
def api_view_model(date_str: str) -> Dict[str, Any]:
    p = _view_model_path_by_date(date_str)
    if not p:
        raise HTTPException(status_code=404, detail="view_model not found")
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/api/view_model/latest")
def api_view_model_latest() -> Dict[str, Any]:
    p = _latest_json_in(VIEWMODEL_DIR)
    if not p:
        raise HTTPException(status_code=404, detail="no view_model json found")
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/api/fx_decision/{date_str}")
def api_fx_decision(date_str: str) -> Dict[str, Any]:
    """
    Read-only endpoint for FX decision JSON.
    It reads:
      - data/world_politics/analysis/fx_decision_{date}.json
      - fallback: data/world_politics/analysis/fx_decision_latest.json
    """
    p = _fx_decision_path_by_date(date_str)
    if not p:
        raise HTTPException(status_code=404, detail="fx_decision not found")
    return json.loads(p.read_text(encoding="utf-8"))

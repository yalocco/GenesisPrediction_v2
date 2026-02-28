from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------
# GenesisPrediction v2 - local server
# - Serve:
#     /static   -> app/static (index.html, overlay.html, sentiment.html, etc.)
#     /analysis  -> repo_root/analysis (health_latest.json, view_model_latest.json, etc.)
#     /data     -> repo_root/data (optional fallbacks used by some pages)
# - Root (/) redirects to /static/index.html
# ---------------------------------------------------------------------

HERE = Path(__file__).resolve()
APP_DIR = HERE.parent                  # .../app
ROOT = APP_DIR.parent                  # repo root
STATIC_DIR = APP_DIR / "static"
ANALYSIS_DIR = ROOT / "analysis"
DATA_DIR = ROOT / "data"

app = FastAPI(title="GenesisPrediction v2", docs_url=None, redoc_url=None)

# Root -> UI
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html", status_code=307)

# Static mounts
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

# analysis/ & data/ are used by UI fetch() as same-origin JSON endpoints
if ANALYSIS_DIR.exists():
    app.mount("/analysis", StaticFiles(directory=str(ANALYSIS_DIR), html=False), name="analysis")

if DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=str(DATA_DIR), html=False), name="data")
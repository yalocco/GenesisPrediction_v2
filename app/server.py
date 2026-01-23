# app/server.py
#
# GenesisPrediction v2 - FastAPI GUI server (compat layer)
#
# Goals:
# - Serve /static and /analysis (canonical artifacts)
# - Restore legacy endpoints used by app/static/index.html
# - Provide minimal, safe runners (allowlisted scripts only)
#
# Run:
#   (.venv) uvicorn app.server:app --host 127.0.0.1 --port 8000 --reload

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles


# ----------------------------
# Paths
# ----------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = REPO_ROOT / "app" / "static"
ANALYSIS_DIR = REPO_ROOT / "data" / "world_politics" / "analysis"
SCRIPTS_DIR = REPO_ROOT / "scripts"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ----------------------------
# App
# ----------------------------
app = FastAPI(title="GenesisPrediction v2 GUI", version="2.0-compat")


# ----------------------------
# Static mounts
# ----------------------------
if not STATIC_DIR.exists():
    raise RuntimeError(f"[FATAL] static dir not found: {STATIC_DIR}")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if ANALYSIS_DIR.exists():
    app.mount("/analysis", StaticFiles(directory=str(ANALYSIS_DIR)), name="analysis")


# ----------------------------
# Helpers
# ----------------------------
def _safe_date(date: str) -> str:
    if not _DATE_RE.match(date):
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    return date


def _read_text(path: Path) -> str:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"not found: {path.name}")
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to read text: {path.name} ({e})")


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"not found: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to read json: {path.name} ({e})")


def _find_latest(glob_pat: str, base: Path) -> Optional[Path]:
    if not base.exists():
        return None
    files = [p for p in base.glob(glob_pat) if p.is_file()]
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime)
    return files[-1]


def _rel_analysis_url(p: Path) -> str:
    p = p.resolve()
    base = ANALYSIS_DIR.resolve()
    if not str(p).startswith(str(base)):
        raise HTTPException(status_code=500, detail="path is outside analysis dir")
    rel = p.relative_to(base).as_posix()
    return f"/analysis/{rel}"


def _run_script(args: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [sys.executable, *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "cmd": " ".join([sys.executable, *args]),
            "returncode": proc.returncode,
            "stdout": proc.stdout[-20000:],
            "stderr": proc.stderr[-20000:],
        }
    except Exception as e:
        return {
            "cmd": " ".join([sys.executable, *args]),
            "returncode": 999,
            "stdout": "",
            "stderr": f"exception: {e}",
        }


def _view_model_latest_path() -> Optional[Path]:
    # common "latest" names, then fallback to newest dated
    for p in [
        ANALYSIS_DIR / "digest_view_model_latest.json",
        ANALYSIS_DIR / "view_model_latest.json",
        ANALYSIS_DIR / "digest_view_model.json",
    ]:
        if p.exists():
            return p
    return _find_latest("digest_view_model_*.json", ANALYSIS_DIR)


# ----------------------------
# Base routes
# ----------------------------
@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/static/index.html")


@app.get("/health", include_in_schema=False)
def health() -> dict:
    return {
        "ok": True,
        "static_dir": str(STATIC_DIR),
        "analysis_dir": str(ANALYSIS_DIR),
        "analysis_dir_exists": ANALYSIS_DIR.exists(),
    }


# ----------------------------
# Canonical APIs (passive)
# ----------------------------
@app.get("/api/view_model/latest", include_in_schema=False)
def api_view_model_latest() -> dict:
    p = _view_model_latest_path()
    if not p:
        raise HTTPException(status_code=404, detail="no view model found")
    return _read_json(p)


@app.get("/api/view_model/{date}", include_in_schema=False)
def api_view_model_by_date(date: str) -> dict:
    date = _safe_date(date)
    p = ANALYSIS_DIR / f"digest_view_model_{date}.json"
    return _read_json(p)


# ----------------------------
# Legacy: Digest view (ALL patterns)
# ----------------------------

# pattern used by some GUIs
@app.get("/api/digest/view/latest", include_in_schema=False)
def legacy_digest_latest() -> dict:
    return api_view_model_latest()


# canonical REST style
@app.get("/api/digest/view/{date}", include_in_schema=False)
def legacy_digest_by_date(date: str) -> dict:
    return api_view_model_by_date(date)


# query style (?date=YYYY-MM-DD)
@app.get("/api/digest/view", include_in_schema=False)
def legacy_digest_by_query(date: str = Query(...)) -> dict:
    return api_view_model_by_date(date)


# WEIRD legacy style: /api/digest/view/date=2026-01-23  ← logs show this
@app.get("/api/digest/view/date={date}", include_in_schema=False)
def legacy_digest_by_weird_path(date: str) -> dict:
    return api_view_model_by_date(date)


# ----------------------------
# Legacy: FX status
# ----------------------------
@app.get("/api/fx/remittance/today", include_in_schema=False)
def legacy_fx_remittance_today() -> dict:
    stable = ANALYSIS_DIR / "jpy_thb_remittance_overlay.png"
    latest_dated = _find_latest("fx_overlay_*.png", ANALYSIS_DIR)
    return {
        "ok": True,
        "stable_overlay": _rel_analysis_url(stable) if stable.exists() else None,
        "latest_dated_overlay": _rel_analysis_url(latest_dated) if latest_dated else None,
    }


# ----------------------------
# Legacy: assets/list and assets/latest
# ----------------------------
@app.get("/api/assets/latest", include_in_schema=False)
def legacy_assets_latest(
    dir: str = Query(""),
    ext: str = Query(""),
    recursive: bool = Query(False),
) -> dict:
    base = ANALYSIS_DIR
    sub = base / dir if dir else base
    search_base = sub if sub.exists() else base

    ext = ext.lstrip(".")
    pat = f"*.{ext}" if ext else "*"

    files = list(search_base.rglob(pat)) if recursive else list(search_base.glob(pat))
    files = [p for p in files if p.is_file()]
    if not files:
        return {"ok": False, "path": None, "detail": "no matching files"}

    files.sort(key=lambda p: p.stat().st_mtime)
    latest = files[-1]
    return {
        "ok": True,
        "filename": latest.name,
        "path": _rel_analysis_url(latest),
        "mtime": latest.stat().st_mtime,
    }


# logs show: /api/assets/list?dir=fx&ext=png&recursive=true&limit=80
@app.get("/api/assets/list", include_in_schema=False)
def legacy_assets_list(
    dir: str = Query(""),
    ext: str = Query(""),
    recursive: bool = Query(False),
    limit: int = Query(80),
) -> dict:
    base = ANALYSIS_DIR
    sub = base / dir if dir else base
    search_base = sub if sub.exists() else base

    ext = ext.lstrip(".")
    pat = f"*.{ext}" if ext else "*"

    files = list(search_base.rglob(pat)) if recursive else list(search_base.glob(pat))
    files = [p for p in files if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    out = []
    for p in files[: max(1, min(limit, 500))]:
        out.append({
            "filename": p.name,
            "path": _rel_analysis_url(p),
            "mtime": p.stat().st_mtime,
        })

    return {"ok": True, "count": len(out), "items": out}


# ----------------------------
# Legacy: runners
# ----------------------------

# accept both /api/run/fx and /api/run/fx/ (some fetchers add slash)
@app.post("/api/run/fx", include_in_schema=False)
@app.post("/api/run/fx/", include_in_schema=False)
def legacy_run_fx(date: str = Query(...)) -> dict:
    """
    Runs:
      scripts/fx_remittance_overlay.py
      scripts/publish_fx_overlay_to_analysis.py --date YYYY-MM-DD
    """
    date = _safe_date(date)

    fx_script = SCRIPTS_DIR / "fx_remittance_overlay.py"
    pub_script = SCRIPTS_DIR / "publish_fx_overlay_to_analysis.py"

    if not fx_script.exists():
        raise HTTPException(status_code=500, detail="missing scripts/fx_remittance_overlay.py")
    if not pub_script.exists():
        raise HTTPException(status_code=500, detail="missing scripts/publish_fx_overlay_to_analysis.py")

    r1 = _run_script([str(fx_script)])
    r2 = _run_script([str(pub_script), "--date", date])

    dated = ANALYSIS_DIR / f"fx_overlay_{date}.png"
    stable = ANALYSIS_DIR / "jpy_thb_remittance_overlay.png"

    return {
        "ok": (r1["returncode"] == 0 and r2["returncode"] == 0),
        "steps": [r1, r2],
        "artifacts": {
            "dated_overlay": _rel_analysis_url(dated) if dated.exists() else None,
            "stable_overlay": _rel_analysis_url(stable) if stable.exists() else None,
        },
    }


# daily runner (compat)
@app.post("/api/run/daily", include_in_schema=False)
@app.post("/api/run/daily/", include_in_schema=False)
def legacy_run_daily(date: str = Query(...)) -> dict:
    date = _safe_date(date)

    ps1 = SCRIPTS_DIR / "run_daily.ps1"
    py = SCRIPTS_DIR / "run_daily_pipeline.py"

    results: list[dict[str, Any]] = []
    ok = True

    if ps1.exists():
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1), "-date", date],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            results.append({
                "cmd": " ".join(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1), "-date", date]),
                "returncode": proc.returncode,
                "stdout": proc.stdout[-20000:],
                "stderr": proc.stderr[-20000:],
            })
            ok = ok and (proc.returncode == 0)
        except Exception as e:
            results.append({"cmd": f"powershell ... {ps1}", "returncode": 999, "stdout": "", "stderr": f"exception: {e}"})
            ok = False
    elif py.exists():
        r = _run_script([str(py), "--date", date])
        results.append(r)
        ok = ok and (r["returncode"] == 0)
    else:
        raise HTTPException(status_code=500, detail="no daily runner found (scripts/run_daily.ps1 or scripts/run_daily_pipeline.py)")

    return {"ok": ok, "steps": results}


# ----------------------------
# Optional raw analysis file endpoint (debug)
# ----------------------------
@app.get("/api/raw/{rel_path:path}", include_in_schema=False)
def api_raw(rel_path: str) -> Response:
    if ".." in rel_path or rel_path.startswith(("/", "\\")):
        raise HTTPException(status_code=400, detail="invalid path")

    target = (ANALYSIS_DIR / rel_path).resolve()
    if not str(target).startswith(str(ANALYSIS_DIR.resolve())):
        raise HTTPException(status_code=403, detail="forbidden")
    if not target.exists():
        raise HTTPException(status_code=404, detail="not found")

    return FileResponse(str(target))

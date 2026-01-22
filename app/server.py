from __future__ import annotations

import html
import json
import os
import subprocess
import threading
from datetime import date as _date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# =============================================================================
# GenesisPrediction v2 - Local GUI API
#
# Fixed rules:
# - GUI must NOT parse HTML. GUI reads ViewModel JSON.
# - "Legacy" HTML/MD are view-only.
# - No manual edits of outputs; generation happens by scripts / analyzer.
# - Provide stable endpoints; return 404/na as "not available" not as UI error.
# =============================================================================

REPO_ROOT = Path.cwd()

APP_DIR = REPO_ROOT / "app"
STATIC_DIR = APP_DIR / "static"

DATA_DIR = REPO_ROOT / "data"
WORLD_ANALYSIS_DIR = DATA_DIR / "world_politics" / "analysis"
DIGEST_VIEW_DIR = DATA_DIR / "digest" / "view"

FX_DIR = DATA_DIR / "fx"
FX_REPORT_DIR = FX_DIR / "reports"

# ---- scripts (all optional; missing ones should not crash the server) ----
SCRIPTS_DIR = REPO_ROOT / "scripts"

SCRIPT_BUILD_DAILY_DIGEST = SCRIPTS_DIR / "build_daily_news_digest.py"
SCRIPT_BUILD_DIGEST_VIEW_MODEL = SCRIPTS_DIR / "build_digest_view_model.py"

SCRIPT_FX_TODAY = SCRIPTS_DIR / "fx_remittance_today.py"
SCRIPT_FX_SUMMARY = SCRIPTS_DIR / "fx_remittance_summary.py"
SCRIPT_FX_OVERLAY = SCRIPTS_DIR / "fx_remittance_overlay.py"  # creates overlay png(s)

# ---- docker ----
DOCKER_COMPOSE = "docker"
DOCKER_COMPOSE_ARGS = ["compose"]  # docker compose ...

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = FastAPI(title="GenesisPrediction v2 Local GUI API", version="2")

# Static UI
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve generated artifacts under /data/...
# (Safe: only from repo's data directory)
if DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# -----------------------------------------------------------------------------
# Concurrency guard + last-run state
# -----------------------------------------------------------------------------
_run_lock = threading.Lock()
_last_run: Dict[str, Any] = {
    "running": False,
    "mode": None,           # digest / daily / fx
    "date": None,
    "returncode": None,
    "artifacts": [],
    "log": "",
}

def _set_last_run(**kwargs: Any) -> None:
    _last_run.update(kwargs)

def _tail(s: str, n: int = 20000) -> str:
    if len(s) <= n:
        return s
    return s[-n:]

def _venv_python() -> str:
    venv_py = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return str(Path(os.sys.executable))

def _run_cmd(cmd: List[str], cwd: Path) -> Tuple[int, str]:
    # Capture combined output; do not raise.
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        shell=False,
    )
    out = (p.stdout or "") + (p.stderr or "")
    return int(p.returncode), out

def _safe_relpath(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(p)

def _list_files(root: Path, exts: Optional[List[str]] = None, recursive: bool = True) -> List[Dict[str, Any]]:
    if not root.exists():
        return []
    items: List[Dict[str, Any]] = []
    exts_norm = None
    if exts:
        exts_norm = []
        for e in exts:
            e = e.strip().lower()
            if not e:
                continue
            if not e.startswith("."):
                e = "." + e
            exts_norm.append(e)
    it = root.rglob("*") if recursive else root.glob("*")
    for p in it:
        if not p.is_file():
            continue
        if exts_norm and p.suffix.lower() not in exts_norm:
            continue
        rp = p.resolve()
        try:
            rel = rp.relative_to(DATA_DIR.resolve())
            url = "/data/" + str(rel).replace("\\", "/")
        except Exception:
            # not under /data (should not happen)
            url = None
        st = p.stat()
        items.append({
            "path": _safe_relpath(p),
            "url": url,
            "size": st.st_size,
            "mtime": st.st_mtime,
            "name": p.name,
        })
    items.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return items

def _parse_date(d: str) -> str:
    d = (d or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")
    return d

# -----------------------------------------------------------------------------
# UI root
# -----------------------------------------------------------------------------
@app.get("/")
def root() -> FileResponse:
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail=f"index.html not found: {_safe_relpath(index)}")
    return FileResponse(str(index), media_type="text/html; charset=utf-8")

# -----------------------------------------------------------------------------
# Health / status
# -----------------------------------------------------------------------------
@app.get("/api/status")
def api_status() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "repo_root": str(REPO_ROOT),
            "last_run": _last_run,
            "paths": {
                "world_analysis": _safe_relpath(WORLD_ANALYSIS_DIR),
                "digest_view": _safe_relpath(DIGEST_VIEW_DIR),
                "fx_dir": _safe_relpath(FX_DIR),
            },
        }
    )

# -----------------------------------------------------------------------------
# Legacy digest outputs (HTML/MD) - view only
# -----------------------------------------------------------------------------
@app.get("/api/digest/html")
def api_digest_html(date: str = Query(..., description="YYYY-MM-DD")) -> HTMLResponse:
    d = _parse_date(date)
    path = WORLD_ANALYSIS_DIR / f"daily_news_{d}.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Digest HTML not found.")
    txt = path.read_text(encoding="utf-8", errors="replace")
    # Serve as rendered HTML
    return HTMLResponse(content=txt)

@app.get("/api/digest/md")
def api_digest_md(date: str = Query(..., description="YYYY-MM-DD")) -> JSONResponse:
    d = _parse_date(date)
    path = WORLD_ANALYSIS_DIR / f"daily_news_{d}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Digest MD not found.")
    txt = path.read_text(encoding="utf-8", errors="replace")
    return JSONResponse({"ok": True, "date": d, "text": txt})

@app.get("/api/digest/md_view")
def api_digest_md_view(date: str = Query(..., description="YYYY-MM-DD")) -> HTMLResponse:
    d = _parse_date(date)
    path = WORLD_ANALYSIS_DIR / f"daily_news_{d}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Digest MD not found.")
    txt = path.read_text(encoding="utf-8", errors="replace")
    # Minimal safe viewer: escape then <pre>
    body = (
        f"<html><head><meta charset='utf-8'><title>Daily News Digest {html.escape(d)}</title></head>"
        f"<body style='margin:0;background:#0b0f14;color:#e8eef4'>"
        f"<div style='max-width:1100px;margin:0 auto;padding:24px'>"
        f"<h1 style='margin:0 0 12px'>Daily News Digest — {html.escape(d)}</h1>"
        f"<pre style='white-space:pre-wrap;line-height:1.35;font-size:14px'>{html.escape(txt)}</pre>"
        f"</div></body></html>"
    )
    return HTMLResponse(content=body)

# -----------------------------------------------------------------------------
# Digest ViewModel (SST) - the only "truth" for GUI rendering
# -----------------------------------------------------------------------------
@app.get("/api/digest/view")
def api_digest_view(date: str = Query(..., description="YYYY-MM-DD")) -> JSONResponse:
    d = _parse_date(date)
    path = DIGEST_VIEW_DIR / f"{d}.json"
    if not path.exists():
        # IMPORTANT: not an error for UI. Return "na".
        return JSONResponse(
            {
                "version": "v1",
                "date": d,
                "status": "na",
                "sections": [],
                "notes": f"view not found for {d}",
                "meta": {"generated_at": None, "generator": "digest", "source": "na"},
            }
        )
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return JSONResponse(
            {
                "version": "v1",
                "date": d,
                "status": "error",
                "sections": [],
                "notes": f"failed to read viewmodel: {e}",
                "meta": {"generated_at": None, "generator": "digest", "source": "error"},
            },
            status_code=200,
        )
    # Keep API stable
    return JSONResponse(obj)

@app.get("/api/digest/view/latest")
def api_digest_view_latest() -> JSONResponse:
    if not DIGEST_VIEW_DIR.exists():
        return JSONResponse({"ok": False, "latest": None, "reason": "digest view dir missing"})
    files = sorted(DIGEST_VIEW_DIR.glob("*.json"))
    if not files:
        return JSONResponse({"ok": True, "latest": None})
    # filenames are YYYY-MM-DD.json
    latest = sorted([p.stem for p in files if len(p.stem) == 10])[-1]
    return JSONResponse({"ok": True, "latest": latest})

# -----------------------------------------------------------------------------
# World outputs list (analysis directory)
# -----------------------------------------------------------------------------
@app.get("/api/world/analysis/files")
def api_world_analysis_files(date: str = Query(default="", description="optional YYYY-MM-DD filter")) -> JSONResponse:
    d = (date or "").strip()
    if d and len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")
    if not WORLD_ANALYSIS_DIR.exists():
        return JSONResponse({"ok": True, "files": []})
    items = []
    for p in sorted(WORLD_ANALYSIS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_file():
            continue
        if d and d not in p.name:
            continue
        st = p.stat()
        try:
            rel = p.resolve().relative_to(DATA_DIR.resolve())
            url = "/data/" + str(rel).replace("\\", "/")
        except Exception:
            url = None
        items.append({"name": p.name, "path": _safe_relpath(p), "url": url, "size": st.st_size, "mtime": st.st_mtime})
    return JSONResponse({"ok": True, "files": items})

# -----------------------------------------------------------------------------
# Run: Digest only (legacy generator)
# -----------------------------------------------------------------------------
@app.post("/api/run/digest")
def api_run_digest(
    date: str = Query(default_factory=lambda: _date.today().isoformat(), description="YYYY-MM-DD"),
    limit: int = Query(40, ge=1, le=200),
) -> JSONResponse:
    d = _parse_date(date)

    if not SCRIPT_BUILD_DAILY_DIGEST.exists():
        raise HTTPException(status_code=404, detail=f"Digest script not found: {_safe_relpath(SCRIPT_BUILD_DAILY_DIGEST)}")

    py = _venv_python()
    cmd = [py, str(SCRIPT_BUILD_DAILY_DIGEST), "--date", d, "--limit", str(limit)]

    if not _run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another run is in progress.")

    try:
        _set_last_run(running=True, mode="digest", date=d, returncode=None, artifacts=[], log="")
        rc, out = _run_cmd(cmd, cwd=REPO_ROOT)
        artifacts = []
        for p in [
            WORLD_ANALYSIS_DIR / f"daily_news_{d}.html",
            WORLD_ANALYSIS_DIR / f"daily_news_{d}.md",
        ]:
            if p.exists():
                artifacts.append({"path": _safe_relpath(p), "size": p.stat().st_size, "mtime": p.stat().st_mtime})
        _set_last_run(running=False, returncode=rc, artifacts=artifacts, log=_tail(out))
        return JSONResponse({"ok": rc == 0, "mode": "digest", "date": d, "returncode": rc, "artifacts": artifacts, "log": _tail(out)})
    finally:
        _run_lock.release()

# -----------------------------------------------------------------------------
# Run: DAILY routine (recommended)
# analyzer (docker) -> digest (py) -> viewmodel (py)
# -----------------------------------------------------------------------------
@app.post("/api/run/daily")
def api_run_daily(
    date: str = Query(default_factory=lambda: _date.today().isoformat(), description="YYYY-MM-DD"),
    limit: int = Query(40, ge=1, le=200),
) -> JSONResponse:
    d = _parse_date(date)

    if not _run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another run is in progress.")

    log_parts: List[str] = []
    artifacts: List[Dict[str, Any]] = []

    def add_artifact(p: Path) -> None:
        if p.exists() and p.is_file():
            st = p.stat()
            artifacts.append({"path": _safe_relpath(p), "size": st.st_size, "mtime": st.st_mtime})

    try:
        _set_last_run(running=True, mode="daily", date=d, returncode=None, artifacts=[], log="")

        # STEP 1: analyzer (docker compose run --rm analyzer)
        cmd_an = [DOCKER_COMPOSE, *DOCKER_COMPOSE_ARGS, "run", "--rm", "analyzer"]
        rc, out = _run_cmd(cmd_an, cwd=REPO_ROOT)
        log_parts.append(f"[STEP] analyzer: {' '.join(cmd_an)}\n{out}")
        if rc != 0:
            _set_last_run(running=False, returncode=rc, artifacts=artifacts, log=_tail("\n\n".join(log_parts)))
            return JSONResponse({"ok": False, "mode": "daily", "date": d, "returncode": rc, "artifacts": artifacts, "log": _tail("\n\n".join(log_parts))})

        # STEP 2: digest (legacy HTML/MD)
        if SCRIPT_BUILD_DAILY_DIGEST.exists():
            py = _venv_python()
            cmd_dg = [py, str(SCRIPT_BUILD_DAILY_DIGEST), "--date", d, "--limit", str(limit)]
            rc, out = _run_cmd(cmd_dg, cwd=REPO_ROOT)
            log_parts.append(f"[STEP] digest: {' '.join(cmd_dg)}\n{out}")
            if rc != 0:
                _set_last_run(running=False, returncode=rc, artifacts=artifacts, log=_tail("\n\n".join(log_parts)))
                return JSONResponse({"ok": False, "mode": "daily", "date": d, "returncode": rc, "artifacts": artifacts, "log": _tail("\n\n".join(log_parts))})
        else:
            log_parts.append("[STEP] digest: SKIP (script missing)")

        # STEP 3: viewmodel
        if SCRIPT_BUILD_DIGEST_VIEW_MODEL.exists():
            py = _venv_python()
            cmd_vm = [py, str(SCRIPT_BUILD_DIGEST_VIEW_MODEL), "--date", d]
            rc, out = _run_cmd(cmd_vm, cwd=REPO_ROOT)
            log_parts.append(f"[STEP] viewmodel: {' '.join(cmd_vm)}\n{out}")
            if rc != 0:
                _set_last_run(running=False, returncode=rc, artifacts=artifacts, log=_tail("\n\n".join(log_parts)))
                return JSONResponse({"ok": False, "mode": "daily", "date": d, "returncode": rc, "artifacts": artifacts, "log": _tail("\n\n".join(log_parts))})
        else:
            log_parts.append("[STEP] viewmodel: SKIP (script missing)")

        # Collect artifacts (best-effort)
        add_artifact(WORLD_ANALYSIS_DIR / f"daily_summary_{d}.json")
        add_artifact(WORLD_ANALYSIS_DIR / f"daily_news_{d}.html")
        add_artifact(WORLD_ANALYSIS_DIR / f"daily_news_{d}.md")
        add_artifact(DIGEST_VIEW_DIR / f"{d}.json")

        _set_last_run(running=False, returncode=0, artifacts=artifacts, log=_tail("\n\n".join(log_parts)))
        return JSONResponse({"ok": True, "mode": "daily", "date": d, "returncode": 0, "artifacts": artifacts, "log": _tail("\n\n".join(log_parts))})
    finally:
        _run_lock.release()

# -----------------------------------------------------------------------------
# Run: FX daily (recommended minimal set)
# today -> summary -> overlay images
# -----------------------------------------------------------------------------
@app.post("/api/run/fx")
def api_run_fx(
    date: str = Query(default_factory=lambda: _date.today().isoformat(), description="YYYY-MM-DD"),
) -> JSONResponse:
    d = _parse_date(date)

    if not _run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another run is in progress.")

    py = _venv_python()
    log_parts: List[str] = []
    artifacts: List[Dict[str, Any]] = []

    def add_artifacts_from_dir(root: Path, exts: List[str]) -> None:
        for it in _list_files(root, exts=exts, recursive=True)[:200]:
            artifacts.append(it)

    try:
        _set_last_run(running=True, mode="fx", date=d, returncode=None, artifacts=[], log="")

        steps: List[Tuple[str, Path, List[str]]] = [
            ("fx_today", SCRIPT_FX_TODAY, ["--date", d]),
            ("fx_summary", SCRIPT_FX_SUMMARY, []),
            ("fx_overlay", SCRIPT_FX_OVERLAY, []),
        ]

        for step_name, script_path, args in steps:
            if not script_path.exists():
                log_parts.append(f"[STEP] {step_name}: SKIP (missing {_safe_relpath(script_path)})")
                continue
            cmd = [py, str(script_path), *args]
            rc, out = _run_cmd(cmd, cwd=REPO_ROOT)
            log_parts.append(f"[STEP] {step_name}: {' '.join(cmd)}\n{out}")
            if rc != 0:
                _set_last_run(running=False, returncode=rc, artifacts=artifacts, log=_tail("\n\n".join(log_parts)))
                return JSONResponse({"ok": False, "mode": "fx", "date": d, "returncode": rc, "artifacts": artifacts, "log": _tail("\n\n".join(log_parts))})

        # Collect likely artifacts
        add_artifacts_from_dir(FX_DIR, [".png", ".json", ".csv"])
        add_artifacts_from_dir(FX_REPORT_DIR, [".png", ".json", ".csv"])

        _set_last_run(running=False, returncode=0, artifacts=artifacts, log=_tail("\n\n".join(log_parts)))
        return JSONResponse({"ok": True, "mode": "fx", "date": d, "returncode": 0, "artifacts": artifacts, "log": _tail("\n\n".join(log_parts))})
    finally:
        _run_lock.release()

# -----------------------------------------------------------------------------
# FX: existing summary endpoints (used by UI panels)
# -----------------------------------------------------------------------------
@app.get("/api/fx/remittance/today")
def api_fx_today() -> JSONResponse:
    """
    Best-effort: read latest "today" decision from data/fx outputs if present.
    This endpoint is intentionally tolerant and returns N/A fields when missing.
    """
    # Known files from your pipeline; if not present, return N/A.
    # (Do not invent data.)
    out: Dict[str, Any] = {
        "ok": True,
        "date": None,
        "decision": None,
        "combined_noise": None,
        "USDJPY": None,
        "USDTHB": None,
        "recommended_action": None,
        "note": None,
    }

    # Prefer a small json (if exists)
    cand_json = sorted(FX_DIR.glob("*today*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if cand_json:
        try:
            obj = json.loads(cand_json[0].read_text(encoding="utf-8"))
            out.update(obj if isinstance(obj, dict) else {})
            out["date"] = out.get("date") or out.get("today") or None
            return JSONResponse(out)
        except Exception:
            pass

    # Fallback: dashboard csv (optional)
    dash = FX_DIR / "jpy_thb_remittance_dashboard.csv"
    if dash.exists():
        try:
            txt = dash.read_text(encoding="utf-8", errors="replace").strip().splitlines()
            if len(txt) >= 2:
                # naive parse: header, last row
                header = [h.strip() for h in txt[0].split(",")]
                last = [c.strip() for c in txt[-1].split(",")]
                row = dict(zip(header, last))
                out["date"] = row.get("date") or row.get("today")
                out["decision"] = row.get("decision")
                out["combined_noise"] = row.get("combined_noise")
                out["USDJPY"] = row.get("USDJPY")
                out["USDTHB"] = row.get("USDTHB")
                out["recommended_action"] = row.get("recommended_action")
                out["note"] = row.get("note")
        except Exception:
            pass

    return JSONResponse(out)

@app.get("/api/fx/remittance/month")
def api_fx_month(month: str = Query(..., description="YYYY-MM")) -> JSONResponse:
    """
    Best-effort monthly summary. If scripts produce JSON summaries, expose them.
    """
    m = (month or "").strip()
    if len(m) != 7:
        raise HTTPException(status_code=400, detail="Invalid month. Use YYYY-MM.")
    # Candidate: data/fx/reports/*{month}*.json
    cands = sorted((FX_REPORT_DIR.glob(f"*{m}*.json")), key=lambda p: p.stat().st_mtime, reverse=True)
    if cands:
        try:
            obj = json.loads(cands[0].read_text(encoding="utf-8"))
            return JSONResponse({"ok": True, "month": m, "data": obj, "source": _safe_relpath(cands[0])})
        except Exception as e:
            return JSONResponse({"ok": False, "month": m, "error": str(e), "source": _safe_relpath(cands[0])})
    return JSONResponse({"ok": True, "month": m, "data": None, "source": None})

# -----------------------------------------------------------------------------
# Assets: list / latest for GUI (png/json/csv) under /data
# -----------------------------------------------------------------------------
@app.get("/api/assets/list")
def api_assets_list(
    dir: str = Query(..., description="root dir under /data, e.g. fx or world_politics/analysis"),
    ext: str = Query("png", description="extension without dot, e.g. png"),
    recursive: bool = Query(True),
    limit: int = Query(50, ge=1, le=500),
) -> JSONResponse:
    rel = (dir or "").strip().replace("\\", "/").strip("/")
    if not rel:
        raise HTTPException(status_code=400, detail="dir required")
    root = DATA_DIR / rel
    if not root.exists() or not root.is_dir():
        return JSONResponse({"ok": True, "dir": rel, "items": []})
    items = _list_files(root, exts=[ext], recursive=recursive)[:limit]
    return JSONResponse({"ok": True, "dir": rel, "items": items})

@app.get("/api/assets/latest")
def api_assets_latest(
    dir: str = Query(..., description="root dir under /data, e.g. fx"),
    ext: str = Query("png", description="extension without dot"),
    recursive: bool = Query(True),
    ) -> JSONResponse:
    rel = (dir or "").strip().replace("\\", "/").strip("/")
    if not rel:
        raise HTTPException(status_code=400, detail="dir required")
    root = DATA_DIR / rel
    if not root.exists() or not root.is_dir():
        return JSONResponse({"ok": True, "dir": rel, "item": None})
    items = _list_files(root, exts=[ext], recursive=recursive)
    return JSONResponse({"ok": True, "dir": rel, "item": items[0] if items else None})

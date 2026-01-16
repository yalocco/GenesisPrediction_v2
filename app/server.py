from __future__ import annotations

import json
import os
import subprocess
import threading
from datetime import date as _date
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

# ---- Paths (repo root assumed as current working directory when starting uvicorn) ----
REPO_ROOT = Path.cwd()
STATIC_DIR = REPO_ROOT / "app" / "static"

# Where your outputs live (adjust if needed)
ANALYSIS_DIR = REPO_ROOT / "data" / "world_politics" / "analysis"

# ---- Safety: allow reading files only from these directories ----
ALLOWED_READ_ROOTS = [
    ANALYSIS_DIR,
]

# ---- Single-run lock (avoid double execution) ----
_run_lock = threading.Lock()
_last_status: Dict[str, Any] = {
    "running": False,
    "step": None,
    "started_at": None,
    "ended_at": None,
    "returncode": None,
    "log_tail": "",
}

def _now_iso() -> str:
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")

def _safe_relpath(p: Path) -> str:
    # Return a stable relative path from repo root for UI
    try:
        return str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    except Exception:
        return str(p).replace("\\", "/")

def _is_allowed_file(path: Path) -> bool:
    path = path.resolve()
    for root in ALLOWED_READ_ROOTS:
        try:
            path.relative_to(root.resolve())
            return True
        except Exception:
            continue
    return False

def _run_cmd(cmd: List[str], cwd: Path | None = None) -> Dict[str, Any]:
    """
    Run a command synchronously, capture stdout+stderr combined.
    """
    if cwd is None:
        cwd = REPO_ROOT

    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    out = proc.stdout or ""
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "output": out,
    }

def _list_outputs(target_date: str) -> List[Dict[str, Any]]:
    """
    List key outputs for a date from ANALYSIS_DIR.
    """
    if not ANALYSIS_DIR.exists():
        return []

    # common patterns you have
    patterns = [
        f"events_{target_date}.jsonl",
        f"diff_{target_date}.json",
        f"daily_summary_{target_date}.json",
        f"observation_{target_date}.json",
        f"predictions_{target_date}.json",
        "latest.json",
        "summary.json",
        "daily_counts.csv",
        "anchors_quality_timeseries.csv",
    ]

    # plus HTML/MD digests (your screenshot shows daily_news_YYYY-MM-DD.html/md in analysis dir)
    digest_patterns = [
        f"daily_news_{target_date}.html",
        f"daily_news_{target_date}.md",
    ]

    files: List[Path] = []
    for name in patterns + digest_patterns:
        p = ANALYSIS_DIR / name
        if p.exists():
            files.append(p)

    # Also: show any daily_news_... for date even if naming changes slightly
    for p in ANALYSIS_DIR.glob(f"*{target_date}*.html"):
        if p not in files:
            files.append(p)
    for p in ANALYSIS_DIR.glob(f"*{target_date}*.md"):
        if p not in files:
            files.append(p)

    # sort by mtime desc
    files.sort(key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)

    result: List[Dict[str, Any]] = []
    for p in files:
        try:
            st = p.stat()
            result.append({
                "path": _safe_relpath(p),
                "size": st.st_size,
                "mtime": st.st_mtime,
            })
        except Exception:
            result.append({"path": _safe_relpath(p)})
    return result

# ---- FastAPI app ----
app = FastAPI(title="GenesisPrediction v2 - Local GUI", version="0.1")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    html_path = STATIC_DIR / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>index.html not found</h1>", status_code=500)
    return HTMLResponse(html_path.read_text(encoding="utf-8", errors="replace"))


@app.get("/api/status")
def api_status():
    return JSONResponse(_last_status)


@app.get("/api/outputs")
def api_outputs(date: str = Query(default_factory=lambda: _date.today().isoformat())):
    return JSONResponse({
        "date": date,
        "analysis_dir": _safe_relpath(ANALYSIS_DIR),
        "files": _list_outputs(date),
    })


@app.get("/api/file")
def api_file(path: str):
    """
    Read a file under allowed roots and return:
    - text/plain for .md/.json/.csv
    - text/html for .html
    """
    p = (REPO_ROOT / path).resolve()
    if not _is_allowed_file(p):
        raise HTTPException(status_code=403, detail="File path not allowed.")
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    suffix = p.suffix.lower()
    content = p.read_text(encoding="utf-8", errors="replace")

    if suffix == ".html":
        return HTMLResponse(content)
    # default: show as plain text (JSON will be pretty-printed in UI client side)
    return PlainTextResponse(content)


def _do_step_analyzer() -> Dict[str, Any]:
    # Step 1: docker compose run --rm analyzer
    cmd = ["docker", "compose", "run", "--rm", "analyzer"]
    return _run_cmd(cmd, cwd=REPO_ROOT)


def _do_step_digest(target_date: str, limit: int) -> Dict[str, Any]:
    # Step 2: use current python (run server from .venv) to execute script
    import sys
    cmd = [sys.executable, "scripts/build_daily_news_digest.py", "--date", target_date, "--limit", str(limit)]
    return _run_cmd(cmd, cwd=REPO_ROOT)


def _run_pipeline(target_date: str, limit: int, mode: str) -> Dict[str, Any]:
    """
    mode: 'analyzer' | 'digest' | 'all'
    """
    global _last_status

    if not _run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another run is in progress.")

    try:
        _last_status = {
            "running": True,
            "step": mode,
            "started_at": _now_iso(),
            "ended_at": None,
            "returncode": None,
            "log_tail": "",
        }

        logs: List[str] = []
        rc = 0

        def add_log(block: str):
            nonlocal logs
            logs.append(block)
            tail = "\n".join(logs)[-20000:]  # keep last ~20k chars
            _last_status["log_tail"] = tail

        if mode in ("analyzer", "all"):
            add_log("=== Step 1: Run Analyzer (docker compose) ===\n")
            r1 = _do_step_analyzer()
            add_log("$ " + " ".join(r1["cmd"]) + "\n" + r1["output"] + "\n")
            rc = r1["returncode"]
            if rc != 0:
                _last_status["returncode"] = rc
                _last_status["ended_at"] = _now_iso()
                _last_status["running"] = False
                return {
                    "ok": False,
                    "mode": mode,
                    "date": target_date,
                    "limit": limit,
                    "returncode": rc,
                    "log": "\n".join(logs),
                    "files": _list_outputs(target_date),
                }

        if mode in ("digest", "all"):
            add_log("=== Step 2: Build HTML Digest ===\n")
            r2 = _do_step_digest(target_date, limit)
            add_log("$ " + " ".join(r2["cmd"]) + "\n" + r2["output"] + "\n")
            rc = r2["returncode"]

        _last_status["returncode"] = rc
        _last_status["ended_at"] = _now_iso()
        _last_status["running"] = False

        return {
            "ok": (rc == 0),
            "mode": mode,
            "date": target_date,
            "limit": limit,
            "returncode": rc,
            "log": "\n".join(logs),
            "files": _list_outputs(target_date),
        }
    finally:
        _run_lock.release()


@app.post("/api/run/analyzer")
def run_analyzer(date: str = Query(default_factory=lambda: _date.today().isoformat()),
                 limit: int = Query(40, ge=1, le=500)):
    return JSONResponse(_run_pipeline(date, limit, mode="analyzer"))


@app.post("/api/run/digest")
def run_digest(date: str = Query(default_factory=lambda: _date.today().isoformat()),
               limit: int = Query(40, ge=1, le=500)):
    return JSONResponse(_run_pipeline(date, limit, mode="digest"))


@app.post("/api/run/all")
def run_all(date: str = Query(default_factory=lambda: _date.today().isoformat()),
            limit: int = Query(40, ge=1, le=500)):
    return JSONResponse(_run_pipeline(date, limit, mode="all"))

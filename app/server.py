from __future__ import annotations

import json
import subprocess
import threading
from datetime import date as _date
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse
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


def _run_cmd(cmd: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
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


def _run_cmd_try_with_date_then_fallback(base_cmd: List[str], target_date: str) -> Dict[str, Any]:
    """
    Robust runner:
    1) Try with: ... --date YYYY-MM-DD
    2) If fails AND output suggests 'unrecognized arguments: --date', retry without date
    """
    r1 = _run_cmd(base_cmd + ["--date", target_date], cwd=REPO_ROOT)
    if r1["returncode"] == 0:
        return r1

    out = (r1.get("output") or "").lower()
    if "unrecognized arguments" in out and "--date" in out:
        r2 = _run_cmd(base_cmd, cwd=REPO_ROOT)
        merged = (
            "=== Attempt 1 (with --date) ===\n"
            + "$ " + " ".join(r1["cmd"]) + "\n" + (r1["output"] or "") + "\n\n"
            + "=== Attempt 2 (without --date) ===\n"
            + "$ " + " ".join(r2["cmd"]) + "\n" + (r2["output"] or "")
        )
        r2["output"] = merged
        return r2

    return r1


def _list_outputs(target_date: str) -> List[Dict[str, Any]]:
    """
    List key outputs for a date from ANALYSIS_DIR.
    """
    if not ANALYSIS_DIR.exists():
        return []

    patterns = [
        f"events_{target_date}.jsonl",
        f"diff_{target_date}.json",
        f"daily_summary_{target_date}.json",
        f"predictions_{target_date}.json",
        "latest.json",
        "summary.json",
        "daily_counts.csv",
        "anchors_quality_timeseries.csv",
        f"observation_{target_date}.json",
        f"observation_{target_date}.md",
        "regime_timeline.png",
        "confidence_churn_regime.png",
        "confidence_anchors_dual.png",
        "confidence_vs_anchors.png",
    ]

    digest_patterns = [
        f"daily_news_{target_date}.html",
        f"daily_news_{target_date}.md",
    ]

    files: List[Path] = []
    for name in patterns + digest_patterns:
        p = ANALYSIS_DIR / name
        if p.exists():
            files.append(p)

    # future-proof date-containing files
    for p in ANALYSIS_DIR.glob(f"*{target_date}*.html"):
        if p not in files:
            files.append(p)
    for p in ANALYSIS_DIR.glob(f"*{target_date}*.md"):
        if p not in files:
            files.append(p)
    for p in ANALYSIS_DIR.glob(f"*{target_date}*.json"):
        if p not in files:
            files.append(p)

    for p in ANALYSIS_DIR.glob("*.png"):
        if p not in files:
            files.append(p)

    files.sort(key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)

    result: List[Dict[str, Any]] = []
    for p in files:
        try:
            st = p.stat()
            result.append({"path": _safe_relpath(p), "size": st.st_size, "mtime": st.st_mtime})
        except Exception:
            result.append({"path": _safe_relpath(p)})
    return result


# ---- historical analog helpers ----
def _daily_summary_path_for(date_str: str) -> Path:
    return ANALYSIS_DIR / f"daily_summary_{date_str}.json"


def _pick_latest_daily_summary_path() -> Optional[Path]:
    if not ANALYSIS_DIR.exists():
        return None
    files = sorted(ANALYSIS_DIR.glob("daily_summary_*.json"))
    return files[-1] if files else None


def _load_json_or_none(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _date_from_daily_summary_filename(path: Path) -> str:
    # daily_summary_YYYY-MM-DD.json
    name = path.name
    return name.replace("daily_summary_", "").replace(".json", "")


# ---- FastAPI app ----
app = FastAPI(title="GenesisPrediction v2 - Local GUI", version="0.3")

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
    return JSONResponse({"date": date, "analysis_dir": _safe_relpath(ANALYSIS_DIR), "files": _list_outputs(date)})


@app.get("/api/historical_analogs")
def api_historical_analogs(date: Optional[str] = None):
    """
    (B) fallback behavior:
    - If date is provided and daily_summary_{date}.json exists: use it.
    - If missing: fallback to latest daily_summary_*.json (if exists).
    """
    requested_date = date
    used_latest = False

    if date:
        path = _daily_summary_path_for(date)
        if not path.exists():
            # fallback to latest
            latest = _pick_latest_daily_summary_path()
            if not latest or not latest.exists():
                return JSONResponse(
                    {
                        "date": date,
                        "requested_date": requested_date,
                        "used_latest": False,
                        "historical_analog_tags": [],
                        "historical_analogs": [],
                        "error": f"daily_summary not found for date={date} and no latest daily_summary available.",
                    }
                )
            path = latest
            used_latest = True
            date = _date_from_daily_summary_filename(path)
    else:
        path = _pick_latest_daily_summary_path()
        if not path or not path.exists():
            return JSONResponse(
                {
                    "date": None,
                    "requested_date": None,
                    "used_latest": False,
                    "historical_analog_tags": [],
                    "historical_analogs": [],
                    "error": "No daily_summary_*.json found.",
                }
            )
        date = _date_from_daily_summary_filename(path)

    doc = _load_json_or_none(path) or {}

    return JSONResponse(
        {
            "date": date,
            "requested_date": requested_date,
            "used_latest": used_latest,
            "historical_analog_tags": doc.get("historical_analog_tags", []) or [],
            "historical_analogs": doc.get("historical_analogs", []) or [],
        }
    )


@app.get("/api/file")
def api_file(path: str):
    """
    Read a file under allowed roots and return:
    - FileResponse for .png
    - text/html for .html
    - text/plain for everything else (.md/.json/.csv etc.)
    """
    p = (REPO_ROOT / path).resolve()
    if not _is_allowed_file(p):
        raise HTTPException(status_code=403, detail="File path not allowed.")
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    suffix = p.suffix.lower()

    if suffix == ".png":
        return FileResponse(str(p), media_type="image/png")

    content = p.read_text(encoding="utf-8", errors="replace")
    if suffix == ".html":
        return HTMLResponse(content)

    return PlainTextResponse(content)


def _do_step_analyzer() -> Dict[str, Any]:
    cmd = ["docker", "compose", "run", "--rm", "analyzer"]
    return _run_cmd(cmd, cwd=REPO_ROOT)


def _do_step_digest(target_date: str, limit: int) -> Dict[str, Any]:
    import sys
    cmd = [sys.executable, "scripts/build_daily_news_digest.py", "--date", target_date, "--limit", str(limit)]
    return _run_cmd(cmd, cwd=REPO_ROOT)


def _do_step_plot(target_date: str) -> Dict[str, Any]:
    import sys
    plot_scripts = [
        "scripts/plot_regime_timeline.py",
        "scripts/plot_confidence_churn_regime.py",
        "scripts/plot_confidence_anchors_dual.py",
    ]

    logs: List[str] = []
    rc = 0

    for script in plot_scripts:
        base_cmd = [sys.executable, script]
        r = _run_cmd_try_with_date_then_fallback(base_cmd, target_date)
        logs.append("$ " + " ".join(r["cmd"]) + "\n" + (r["output"] or "") + "\n")
        rc = r["returncode"]
        if rc != 0:
            break

    return {"cmd": ["<plot-batch>"], "returncode": rc, "output": "\n".join(logs)}


def _do_step_observation(target_date: str) -> Dict[str, Any]:
    import sys
    base_cmd = [sys.executable, "scripts/build_daily_observation_log.py"]
    return _run_cmd_try_with_date_then_fallback(base_cmd, target_date)


def _run_pipeline(target_date: str, limit: int, mode: str) -> Dict[str, Any]:
    """
    mode: 'analyzer' | 'digest' | 'plot' | 'observation' | 'all'
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
            logs.append(block)
            _last_status["log_tail"] = "\n".join(logs)[-20000:]

        if mode in ("analyzer", "all"):
            add_log("=== Step 1: Run Analyzer (docker compose) ===\n")
            r1 = _do_step_analyzer()
            add_log("$ " + " ".join(r1["cmd"]) + "\n" + r1["output"] + "\n")
            rc = r1["returncode"]
            if rc != 0:
                _last_status.update({"returncode": rc, "ended_at": _now_iso(), "running": False})
                return {"ok": False, "mode": mode, "date": target_date, "limit": limit, "returncode": rc, "log": "\n".join(logs), "files": _list_outputs(target_date)}

        if mode in ("digest", "all"):
            add_log("=== Step 2: Build HTML Digest ===\n")
            r2 = _do_step_digest(target_date, limit if limit else 40)
            add_log("$ " + " ".join(r2["cmd"]) + "\n" + r2["output"] + "\n")
            rc = r2["returncode"]
            if rc != 0:
                _last_status.update({"returncode": rc, "ended_at": _now_iso(), "running": False})
                return {"ok": False, "mode": mode, "date": target_date, "limit": limit, "returncode": rc, "log": "\n".join(logs), "files": _list_outputs(target_date)}

        if mode in ("plot", "all"):
            add_log("=== Step 3: Plot (visual aids) ===\n")
            r3 = _do_step_plot(target_date)
            add_log((r3["output"] or "") + "\n")
            rc = r3["returncode"]
            if rc != 0:
                _last_status.update({"returncode": rc, "ended_at": _now_iso(), "running": False})
                return {"ok": False, "mode": mode, "date": target_date, "limit": limit, "returncode": rc, "log": "\n".join(logs), "files": _list_outputs(target_date)}

        if mode in ("observation", "all"):
            add_log("=== Step 4: Observation Log ===\n")
            r4 = _do_step_observation(target_date)
            add_log("$ " + " ".join(r4["cmd"]) + "\n" + r4["output"] + "\n")
            rc = r4["returncode"]
            if rc != 0:
                _last_status.update({"returncode": rc, "ended_at": _now_iso(), "running": False})
                return {"ok": False, "mode": mode, "date": target_date, "limit": limit, "returncode": rc, "log": "\n".join(logs), "files": _list_outputs(target_date)}

        _last_status.update({"returncode": rc, "ended_at": _now_iso(), "running": False})
        return {"ok": (rc == 0), "mode": mode, "date": target_date, "limit": limit, "returncode": rc, "log": "\n".join(logs), "files": _list_outputs(target_date)}
    finally:
        _run_lock.release()


@app.post("/api/run/analyzer")
def run_analyzer(date: str = Query(default_factory=lambda: _date.today().isoformat()), limit: int = Query(40, ge=1, le=500)):
    return JSONResponse(_run_pipeline(date, limit, mode="analyzer"))


@app.post("/api/run/digest")
def run_digest(date: str = Query(default_factory=lambda: _date.today().isoformat()), limit: int = Query(40, ge=1, le=500)):
    return JSONResponse(_run_pipeline(date, limit, mode="digest"))


@app.post("/api/run/plot")
def run_plot(date: str = Query(default_factory=lambda: _date.today().isoformat())):
    return JSONResponse(_run_pipeline(date, 0, mode="plot"))


@app.post("/api/run/observation")
def run_observation(date: str = Query(default_factory=lambda: _date.today().isoformat())):
    return JSONResponse(_run_pipeline(date, 0, mode="observation"))


@app.post("/api/run/all")
def run_all(date: str = Query(default_factory=lambda: _date.today().isoformat()), limit: int = Query(40, ge=1, le=500)):
    return JSONResponse(_run_pipeline(date, limit, mode="all"))

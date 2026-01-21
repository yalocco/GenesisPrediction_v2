from __future__ import annotations

import json
import html
import os
import subprocess
import threading
from datetime import date as _date
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# =============================================================================
# GenesisPrediction v2 - Local GUI API
#
# Design goals:
# - Keep UI stable: serve app/static/index.html at "/"
# - Provide deterministic API endpoints used by the UI
# - Serve digest HTML as *rendered* HTML (NOT download dialog)
# - Restrict file reads to known safe roots
# =============================================================================

# --- Paths (repo root assumed as current working directory when starting uvicorn) ---
REPO_ROOT = Path.cwd()
APP_DIR = REPO_ROOT / "app"
STATIC_DIR = APP_DIR / "static"

DATA_DIR = REPO_ROOT / "data"
ANALYSIS_DIR = DATA_DIR / "world_politics" / "analysis"

FX_DIR = DATA_DIR / "fx"
FX_REPORT_DIR = FX_DIR / "reports"
FX_LOG = FX_DIR / "jpy_thb_remittance_decision_log.csv"
FX_DASHBOARD = FX_DIR / "jpy_thb_remittance_dashboard.csv"

# Tracked docs (optional)
DOCS_DIR = REPO_ROOT / "docs"
OBS_MD = DOCS_DIR / "observation.md"

# Scripts
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCRIPT_BUILD_DIGEST = SCRIPTS_DIR / "build_daily_news_digest.py"

# --- Safety: allow reading files only from these directories ---
ALLOWED_READ_ROOTS = [
    STATIC_DIR,
    ANALYSIS_DIR,
    DOCS_DIR,
    FX_DIR,
]

def _is_allowed_file(p: Path) -> bool:
    try:
        rp = p.resolve()
    except Exception:
        return False
    for root in ALLOWED_READ_ROOTS:
        try:
            if rp.is_relative_to(root.resolve()):
                return True
        except AttributeError:
            # Python < 3.9 compatibility (not needed here but harmless)
            try:
                root_r = root.resolve()
                if str(rp).startswith(str(root_r) + os.sep):
                    return True
            except Exception:
                pass
    return False

def _safe_relpath(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(p)

# --- Single-run lock (avoid double execution) ---
_run_lock = threading.Lock()
_last_run: Dict[str, Any] = {
    "running": False,
    "step": None,
    "started_at": None,
    "ended_at": None,
    "returncode": None,
    "log_tail": "",
}

def _set_last_run(**kwargs: Any) -> None:
    _last_run.update(kwargs)

def _tail_text(text: str, max_chars: int = 6000) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]

def _run_cmd(cmd: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
    """Run a command and capture output (short tail saved in status)."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return {"returncode": proc.returncode, "output": out}
    except Exception as e:
        return {"returncode": 1, "output": f"[EXCEPTION] {e!r}"}

# =============================================================================
# FastAPI app
# =============================================================================

app = FastAPI(title="GenesisPrediction v2 - Local GUI")

# Serve static files under /static (optional assets)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def root():
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="index.html not found under app/static")
    return FileResponse(str(index), media_type="text/html")

# =============================================================================
# Basic status / health
# =============================================================================

@app.get("/api/status")
def api_status():
    return JSONResponse(_last_run)

# =============================================================================
# FX remittance endpoints (simple file-based)
# =============================================================================

def _read_csv_last_line(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        # fast tail read
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 8192
            pos = max(0, size - block)
            f.seek(pos)
            data = f.read().decode("utf-8", errors="replace")
        lines = [ln for ln in data.splitlines() if ln.strip()]
        return lines[-1] if lines else None
    except Exception:
        return None

@app.get("/api/fx/remittance/today")
def api_fx_remittance_today():
    """
    Expected producer: scripts/fx_remittance_today.py writing data/fx/jpy_thb_remittance_dashboard.csv
    This endpoint simply returns latest dashboard row if present.
    """
    if not FX_DASHBOARD.exists():
        return JSONResponse({"ok": False, "error": "dashboard csv not found", "path": _safe_relpath(FX_DASHBOARD)}, status_code=404)

    # Best-effort parse: dashboard is typically tiny, so read all.
    try:
        txt = FX_DASHBOARD.read_text(encoding="utf-8", errors="replace").splitlines()
        header = txt[0].split(",") if txt else []
        last = txt[-1].split(",") if len(txt) >= 2 else []
        row = dict(zip(header, last)) if header and last else {}
        return JSONResponse({"ok": True, "path": _safe_relpath(FX_DASHBOARD), "row": row})
    except Exception as e:
        return JSONResponse({"ok": False, "error": repr(e), "path": _safe_relpath(FX_DASHBOARD)}, status_code=500)

@app.get("/api/fx/remittance/month")
def api_fx_remittance_month(month: str = Query(..., description="YYYY-MM")):
    """
    Reads reports/monthly summary if you have one; otherwise returns aggregated from log.
    """
    if not FX_LOG.exists():
        return JSONResponse({"ok": False, "error": "log csv not found", "path": _safe_relpath(FX_LOG)}, status_code=404)

    try:
        lines = FX_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            return JSONResponse({"ok": True, "month": month, "rows": []})
        header = lines[0].split(",")
        rows = []
        for ln in lines[1:]:
            cols = ln.split(",")
            row = dict(zip(header, cols))
            d = (row.get("date") or "")[:7]
            if d == month:
                rows.append(row)
        return JSONResponse({"ok": True, "month": month, "rows": rows})
    except Exception as e:
        return JSONResponse({"ok": False, "error": repr(e)}, status_code=500)

# =============================================================================
# World politics outputs list (optional helper)
# =============================================================================

@app.get("/api/world/analysis/files")
def api_world_analysis_files(date: str = Query(default_factory=lambda: _date.today().isoformat())):
    """
    Returns world_politics/analysis files for the date (best-effort).
    """
    d = (date or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")
    out: List[Dict[str, Any]] = []
    if ANALYSIS_DIR.exists():
        for p in sorted(ANALYSIS_DIR.glob(f"*{d}*")):
            if p.is_file():
                out.append({"path": _safe_relpath(p), "name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime})
    return JSONResponse({"ok": True, "date": d, "files": out})

# =============================================================================
# Digest generation + viewing
# =============================================================================

def _digest_md_path(d: str) -> Path:
    return ANALYSIS_DIR / f"daily_news_{d}.md"

def _digest_html_path(d: str) -> Path:
    return ANALYSIS_DIR / f"daily_news_{d}.html"

@app.post("/api/run/digest")
def api_run_digest(
    date: str = Query(default_factory=lambda: _date.today().isoformat(), description="YYYY-MM-DD"),
    limit: int = Query(40, ge=1, le=200),
):
    """
    Runs scripts/build_daily_news_digest.py to generate md/html under analysis/.
    """
    d = (date or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    if not SCRIPT_BUILD_DIGEST.exists():
        raise HTTPException(status_code=404, detail=f"Digest script not found: {_safe_relpath(SCRIPT_BUILD_DIGEST)}")

    # Try to use venv python if present
    venv_py = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    py = str(venv_py if venv_py.exists() else Path(os.sys.executable))

    cmd = [py, str(SCRIPT_BUILD_DIGEST), "--date", d, "--limit", str(limit)]

    if not _run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another run is in progress.")

    try:
        _set_last_run(running=True, step="digest", started_at=_date.today().isoformat(), ended_at=None, returncode=None, log_tail="")
        res = _run_cmd(cmd, cwd=REPO_ROOT)
        _set_last_run(
            running=False,
            step="digest",
            ended_at=_date.today().isoformat(),
            returncode=res["returncode"],
            log_tail=_tail_text(res["output"]),
        )

        md = _digest_md_path(d)
        html = _digest_html_path(d)
        files = []
        for p in [md, html]:
            if p.exists():
                st = p.stat()
                files.append({"path": _safe_relpath(p), "size": st.st_size, "mtime": st.st_mtime})

        return JSONResponse({"ok": res["returncode"] == 0, "mode": "digest", "date": d, "limit": limit, "returncode": res["returncode"], "files": files, "log": _tail_text(res["output"])})
    finally:
        _run_lock.release()

@app.get("/api/digest/html")
def api_digest_html(date: str = Query(default_factory=lambda: _date.today().isoformat())):
    """
    Serve generated digest HTML as *rendered HTML* (no download dialog).
    """
    d = (date or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    p = _digest_html_path(d)
    if not p.exists():
        # fallback: pick newest daily_news_*.html
        cand = sorted(ANALYSIS_DIR.glob("daily_news_*.html"), key=lambda x: x.stat().st_mtime, reverse=True)
        if cand:
            p = cand[0]

    if not p.exists():
        raise HTTPException(status_code=404, detail="Digest HTML not found.")

    if not _is_allowed_file(p):
        raise HTTPException(status_code=403, detail="File path not allowed.")

    html = p.read_text(encoding="utf-8", errors="replace")
    # Ensure browser treats it as HTML
    return HTMLResponse(content=html)

@app.get("/api/digest/md")
def api_digest_md(date: str = Query(default_factory=lambda: _date.today().isoformat())):
    """
    Serve generated digest markdown as text.
    """
    d = (date or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    p = _digest_md_path(d)
    if not p.exists():
        cand = sorted(ANALYSIS_DIR.glob("daily_news_*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        if cand:
            p = cand[0]

    if not p.exists():
        raise HTTPException(status_code=404, detail="Digest markdown not found.")

    if not _is_allowed_file(p):
        raise HTTPException(status_code=403, detail="File path not allowed.")

    return PlainTextResponse(p.read_text(encoding="utf-8", errors="replace"))



def _md_to_html(md: str) -> str:
    """
    Minimal Markdown -> HTML renderer (headings + unordered lists + paragraphs).
    Keeps it dependency-free (no extra pip installs).
    """
    lines = md.splitlines()
    out: List[str] = []
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for raw in lines:
        line = raw.rstrip("\n")
        if line.startswith("### "):
            close_ul()
            out.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            close_ul()
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            close_ul()
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.strip() == "":
            close_ul()
            out.append("<br/>")
        else:
            close_ul()
            out.append(f"<p>{html.escape(line)}</p>")

    close_ul()
    return "\n".join(out)

@app.get("/api/digest/md_view")
def api_digest_md_view(date: str = Query(default_factory=lambda: _date.today().isoformat())):
    """
    Serve digest markdown rendered as HTML (dependency-free).
    """
    d = (date or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    p = _digest_md_path(d)
    if not p.exists():
        cand = sorted(ANALYSIS_DIR.glob("daily_news_*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        if cand:
            p = cand[0]

    if not p.exists():
        raise HTTPException(status_code=404, detail="Digest MD not found.")

    if "_is_allowed_file" in globals():
        if not _is_allowed_file(p):  # type: ignore[name-defined]
            raise HTTPException(status_code=403, detail="File path not allowed.")

    md = p.read_text(encoding="utf-8", errors="replace")
    body = _md_to_html(md)
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Daily News Digest (MD) — {html.escape(p.name)}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji"; padding: 20px; }}
    h1 {{ margin: 0 0 8px; }}
    h2 {{ margin: 18px 0 8px; }}
    h3 {{ margin: 14px 0 6px; }}
    ul {{ margin: 6px 0 12px 22px; }}
    li {{ margin: 2px 0; }}
    p {{ margin: 4px 0; white-space: pre-wrap; }}
    .meta {{ color: #666; font-size: 12px; margin-bottom: 14px; }}
    .top {{ display:flex; gap:10px; align-items:center; margin-bottom: 8px; }}
    a {{ color: inherit; }}
    .pill {{ display:inline-block; padding:2px 8px; border:1px solid #ddd; border-radius:999px; font-size:12px; color:#444; }}
  </style>
</head>
<body>
  <div class="top">
    <span class="pill">md_view</span>
    <span class="meta">{html.escape(str(p))}</span>
  </div>
  {body}
</body>
</html>"""
    return HTMLResponse(content=page)

# =============================================================================
# Generic file viewer (safe roots only)
# =============================================================================

@app.get("/api/file")
def api_file(path: str):
    """
    Read any file under ALLOWED_READ_ROOTS (as text) for debugging/inspection.
    """
    if not path:
        raise HTTPException(status_code=400, detail="path is required")

    p = (REPO_ROOT / path).resolve()
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="file not found")

    if not _is_allowed_file(p):
        raise HTTPException(status_code=403, detail="file path not allowed")

    # Decide response type
    if p.suffix.lower() in [".html", ".htm"]:
        return HTMLResponse(p.read_text(encoding="utf-8", errors="replace"))
    return PlainTextResponse(p.read_text(encoding="utf-8", errors="replace"))

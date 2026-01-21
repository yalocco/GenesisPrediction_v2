from __future__ import annotations

import csv
import json
import subprocess
import threading
from datetime import date as _date
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles


# --- Paths (repo root assumed as current working directory when starting uvicorn) ---
REPO_ROOT = Path.cwd()

STATIC_DIR = REPO_ROOT / "app" / "static"
INDEX_HTML = STATIC_DIR / "index.html"

ANALYSIS_DIR = REPO_ROOT / "data" / "world_politics" / "analysis"

FX_DIR = REPO_ROOT / "data" / "fx"
FX_LOG = FX_DIR / "jpy_thb_remittance_decision_log.csv"
FX_REPORT_DIR = FX_DIR / "reports"

SCRIPTS_DIR = REPO_ROOT / "scripts"
VENV_PY = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
if not VENV_PY.exists():
    # fallback (Linux/mac, etc.)
    VENV_PY = REPO_ROOT / ".venv" / "bin" / "python"


# --- Safety: allow reading files only from these directories ---
ALLOWED_READ_ROOTS = [
    STATIC_DIR,
    ANALYSIS_DIR,
    FX_DIR,
    FX_REPORT_DIR,
]

def _is_allowed_file(p: Path) -> bool:
    try:
        rp = p.resolve()
    except Exception:
        return False
    for root in ALLOWED_READ_ROOTS:
        try:
            rr = root.resolve()
            rp.relative_to(rr)
            return True
        except Exception:
            pass
    return False

def _safe_relpath(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(p)

def _stat_file(p: Path) -> Dict[str, Any]:
    st = p.stat()
    return {
        "path": _safe_relpath(p),
        "size": int(st.st_size),
        "mtime": float(st.st_mtime),
    }


# --- Single-run lock (avoid double execution for run/digest) ---
_run_lock = threading.Lock()
_status: Dict[str, Any] = {
    "running": False,
    "step": None,
    "started_at": None,
    "ended_at": None,
    "returncode": None,
    "log_tail": "",
}


def _set_status(**kw: Any) -> None:
    _status.update(kw)

def _tail_text(text: str, max_chars: int = 6000) -> str:
    if text is None:
        return ""
    return text[-max_chars:]


# --- FastAPI app ---
app = FastAPI(title="GenesisPrediction v2 - Local GUI")


# ========== UI ==========
@app.get("/", response_class=HTMLResponse)
def root() -> FileResponse:
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(str(INDEX_HTML), media_type="text/html")


# static assets (if any)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


# ========== World Politics ==========
@app.get("/api/outputs")
def api_outputs(date: Optional[str] = None) -> JSONResponse:
    """
    List output files under data/world_politics/analysis.
    If date is provided (YYYY-MM-DD), filter files that contain that date.
    """
    if not ANALYSIS_DIR.exists():
        return JSONResponse({"ok": True, "files": [], "note": "analysis dir not found"})

    files: List[Path] = []
    if date:
        files = sorted(ANALYSIS_DIR.glob(f"*{date}*"))
    else:
        files = sorted(ANALYSIS_DIR.glob("*"))

    out = []
    for p in files:
        if p.is_file():
            out.append(_stat_file(p))
    return JSONResponse({"ok": True, "files": out})


@app.post("/api/run/digest")
def api_run_digest(
    date: str = Query(default_factory=lambda: _date.today().isoformat()),
    limit: int = 40,
) -> JSONResponse:
    """
    Run scripts/build_daily_news_digest.py and generate:
      data/world_politics/analysis/daily_news_YYYY-MM-DD.md
      data/world_politics/analysis/daily_news_YYYY-MM-DD.html
    """
    d = (date or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    if not VENV_PY.exists():
        raise HTTPException(status_code=500, detail=f"venv python not found: {_safe_relpath(VENV_PY)}")

    script = SCRIPTS_DIR / "build_daily_news_digest.py"
    if not script.exists():
        raise HTTPException(status_code=404, detail="scripts/build_daily_news_digest.py not found.")

    if not _run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another run is in progress.")

    try:
        _set_status(
            running=True,
            step="digest",
            started_at=_date.today().isoformat(),
            ended_at=None,
            returncode=None,
            log_tail="",
        )

        cmd = [str(VENV_PY), str(script), "--date", d, "--limit", str(limit)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        _set_status(
            running=False,
            ended_at=_date.today().isoformat(),
            returncode=int(proc.returncode),
            log_tail=_tail_text("=== Step 2: Build HTML Digest ===\n$ " + " ".join(cmd) + "\n" + combined + "\n"),
        )

        # return files that were produced
        produced = []
        for ext in ("md", "html"):
            p = ANALYSIS_DIR / f"daily_news_{d}.{ext}"
            if p.exists():
                produced.append(_stat_file(p))

        return JSONResponse(
            {
                "ok": proc.returncode == 0,
                "mode": "digest",
                "date": d,
                "limit": limit,
                "returncode": int(proc.returncode),
                "log": _status.get("log_tail", ""),
                "files": produced,
            }
        )
    finally:
        _run_lock.release()


@app.get("/api/status")
def api_status() -> JSONResponse:
    return JSONResponse(_status)


@app.get("/api/digest/html")
def api_digest_html(date: str = Query(default_factory=lambda: _date.today().isoformat())) -> FileResponse:
    d = (date or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    p = ANALYSIS_DIR / f"daily_news_{d}.html"
    if not p.exists():
        # fallback: newest matching html
        cand = sorted(ANALYSIS_DIR.glob("daily_news_*.html"), key=lambda x: x.stat().st_mtime, reverse=True)
        if cand:
            p = cand[0]

    if not p.exists():
        raise HTTPException(status_code=404, detail="Digest HTML not found.")

    if not _is_allowed_file(p):
        raise HTTPException(status_code=403, detail="File path not allowed.")

    return FileResponse(str(p), media_type="text/html", filename=p.name)


@app.get("/api/digest/md")
def api_digest_md(date: str = Query(default_factory=lambda: _date.today().isoformat())) -> PlainTextResponse:
    d = (date or "").strip()
    if len(d) != 10:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.")

    p = ANALYSIS_DIR / f"daily_news_{d}.md"
    if not p.exists():
        cand = sorted(ANALYSIS_DIR.glob("daily_news_*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        if cand:
            p = cand[0]

    if not p.exists():
        raise HTTPException(status_code=404, detail="Digest MD not found.")

    if not _is_allowed_file(p):
        raise HTTPException(status_code=403, detail="File path not allowed.")

    return PlainTextResponse(p.read_text(encoding="utf-8", errors="replace"))


# ========== FX Remittance (JPY→THB) ==========
def _read_fx_rows() -> List[Dict[str, str]]:
    if not FX_LOG.exists():
        return []
    rows: List[Dict[str, str]] = []
    with FX_LOG.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


@app.get("/api/fx/remittance/today")
def api_fx_today(date: str = Query(default_factory=lambda: _date.today().isoformat())) -> JSONResponse:
    """
    Returns today's FX remittance decision from CSV log (best-effort).
    """
    d = (date or "").strip()
    rows = _read_fx_rows()
    row = None
    for r in reversed(rows):
        if r.get("date") == d:
            row = r
            break

    if not row:
        # fallback: latest row
        if rows:
            row = rows[-1]
        else:
            return JSONResponse(
                {
                    "ok": False,
                    "date": d,
                    "note": "FX log not found or empty",
                    "path": _safe_relpath(FX_LOG),
                },
                status_code=404,
            )

    def _f(x: str) -> Optional[float]:
        try:
            return float(x)
        except Exception:
            return None

    payload = {
        "ok": True,
        "date": row.get("date"),
        "decision": row.get("decision") or row.get("remit_decision"),
        "combined_noise_prob": _f(row.get("combined_noise_prob", "")) or _f(row.get("combined_noise", "")),
        "usd_jpy_noise": _f(row.get("usd_jpy_noise", "")),
        "usd_thb_noise": _f(row.get("usd_thb_noise", "")),
        "recommended_action": row.get("recommended_action") or row.get("action"),
        "remit_note": row.get("remit_note") or row.get("note"),
        "reports_dir": _safe_relpath(FX_REPORT_DIR),
    }
    return JSONResponse(payload)


@app.get("/api/fx/remittance/monthly")
def api_fx_monthly(month: str = Query(default_factory=lambda: _date.today().strftime("%Y-%m"))) -> JSONResponse:
    """
    Aggregate monthly summary from FX log CSV.
    month: YYYY-MM
    """
    m = (month or "").strip()
    if len(m) != 7:
        raise HTTPException(status_code=400, detail="Invalid month. Use YYYY-MM.")

    rows = _read_fx_rows()
    month_rows = [r for r in rows if (r.get("date") or "").startswith(m)]

    if not month_rows:
        return JSONResponse(
            {"ok": False, "month": m, "days": 0, "avg_noise": None, "counts": {}, "actions": {}, "reports_dir": _safe_relpath(FX_REPORT_DIR)},
            status_code=404,
        )

    noises: List[float] = []
    counts: Dict[str, int] = {}
    actions: Dict[str, int] = {}
    for r in month_rows:
        dec = (r.get("decision") or r.get("remit_decision") or "").upper() or "UNKNOWN"
        counts[dec] = counts.get(dec, 0) + 1

        act = (r.get("recommended_action") or r.get("action") or "").strip() or "unknown"
        actions[act] = actions.get(act, 0) + 1

        try:
            noises.append(float(r.get("combined_noise_prob", "") or r.get("combined_noise", "")))
        except Exception:
            pass

    avg_noise = (sum(noises) / len(noises)) if noises else None

    return JSONResponse(
        {
            "ok": True,
            "month": m,
            "days": len(month_rows),
            "avg_noise": avg_noise,
            "counts": counts,
            "actions": actions,
            "reports_dir": _safe_relpath(FX_REPORT_DIR),
        }
    )

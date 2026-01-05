# scripts/plot_confidence_anchors_dual.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"

def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default

def _safe_int(x, default=0):
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default

def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return None

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    files = sorted(ANALYSIS_DIR.glob("daily_summary_*.json"))
    rows = []

    for fp in files:
        try:
            doc = _load_json(fp)
        except Exception:
            continue

        # date は meta.date を最優先（無ければファイル名から推定）
        date_str = ((doc.get("meta") or {}).get("date") or "").strip()
        if not date_str:
            # daily_summary_YYYY-MM-DD.json
            stem = fp.stem
            if stem.startswith("daily_summary_") and len(stem) >= len("daily_summary_") + 10:
                date_str = stem[len("daily_summary_"):len("daily_summary_") + 10]

        dt = _parse_date(date_str)
        if dt is None:
            continue

        conf = _safe_float(doc.get("confidence_of_hypotheses"), default=None)
        if conf is None:
            # 旧キー等に備えて
            conf = _safe_float(doc.get("confidence"), default=None)
        if conf is None:
            continue

        anchors = doc.get("anchors") or {}
        top_tokens = anchors.get("top_tokens") or []
        if isinstance(top_tokens, str):
            # 念のため
            top_tokens = [t.strip() for t in top_tokens.split(",") if t.strip()]
        anchors_n = len(top_tokens)

        rows.append((dt, date_str, conf, anchors_n))

    if not rows:
        print(f"[NG] no daily_summary_*.json found with confidence in: {ANALYSIS_DIR}")
        return

    rows.sort(key=lambda x: x[0])
    dates = [r[1] for r in rows]
    confs = [r[2] for r in rows]
    anchors_ns = [r[3] for r in rows]

    # ========= 1) 二軸：date × (confidence, anchors_n) =========
    fig, ax1 = plt.subplots()
    ax1.plot(dates, confs, marker="o")
    ax1.set_title("confidence (line) vs anchors_n (bars)")
    ax1.set_xlabel("date")
    ax1.set_ylabel("confidence")
    ax1.set_ylim(0.0, 1.0)
    ax1.tick_params(axis="x", rotation=30)

    ax2 = ax1.twinx()
    ax2.bar(dates, anchors_ns, alpha=0.3)
    ax2.set_ylabel("anchors_n (len(top_tokens))")

    out1 = ANALYSIS_DIR / "confidence_anchors_dual.png"
    fig.tight_layout()
    fig.savefig(out1, dpi=150)
    plt.close(fig)
    print(f"[OK] wrote {out1} ({len(rows)} points)")

    # ========= 2) 散布図：anchors_n × confidence =========
    fig2, ax = plt.subplots()
    ax.scatter(anchors_ns, confs)
    ax.set_title("confidence vs anchors_n")
    ax.set_xlabel("anchors_n (len(top_tokens))")
    ax.set_ylabel("confidence")
    ax.set_ylim(0.0, 1.0)

    # 点に日付ラベル（多すぎると読めないので、まずは全部付ける）
    for (_, dstr, c, a) in rows:
        ax.annotate(dstr, (a, c), fontsize=7, xytext=(4, 4), textcoords="offset points")

    out2 = ANALYSIS_DIR / "confidence_vs_anchors.png"
    fig2.tight_layout()
    fig2.savefig(out2, dpi=150)
    plt.close(fig2)
    print(f"[OK] wrote {out2} ({len(rows)} points)")

if __name__ == "__main__":
    main()

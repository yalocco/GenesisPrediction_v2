# scripts/plot_confidence_anchors_dual.py
from __future__ import annotations

import json
import csv
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"
AQ_CSV = ANALYSIS_DIR / "anchors_quality_timeseries.csv"


def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _parse_date(s: str) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            if fmt == "%Y-%m-%d":
                return datetime.strptime(s[:10], fmt)
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_date_str(doc: dict, fp: Path) -> str | None:
    # meta.date 優先、無ければファイル名 daily_summary_YYYY-MM-DD.json から推定
    date_str = ((doc.get("meta") or {}).get("date") or "").strip()
    if date_str:
        return date_str[:10]
    stem = fp.stem
    if stem.startswith("daily_summary_") and len(stem) >= len("daily_summary_") + 10:
        return stem[len("daily_summary_") : len("daily_summary_") + 10]
    return None


def _extract_confidence(doc: dict) -> float | None:
    # 新旧キーを吸収
    conf = _safe_float(doc.get("confidence_of_hypotheses"), default=None)
    if conf is None:
        conf = _safe_float(doc.get("confidence"), default=None)
    if conf is None:
        conf = _safe_float(doc.get("conf"), default=None)
    return conf


def _extract_anchors_n(doc: dict) -> int:
    """
    anchors が dict/list/str どれでも落ちないように anchors_n を計算する。
    - dict: {"top_tokens":[...]} or {"tokens":[...]} etc
    - list: ["token1", "token2", ...]
    - str:  "token1, token2, ..."
    """
    anchors = doc.get("anchors")

    # dict
    if isinstance(anchors, dict):
        top_tokens = (
            anchors.get("top_tokens")
            or anchors.get("tokens")
            or anchors.get("top")
            or []
        )
    # list
    elif isinstance(anchors, list):
        top_tokens = anchors
    # str
    elif isinstance(anchors, str):
        top_tokens = [t.strip() for t in anchors.split(",") if t.strip()]
    else:
        top_tokens = []

    # 念のため：top_tokens 自体が "a,b,c" の文字列の場合
    if isinstance(top_tokens, str):
        top_tokens = [t.strip() for t in top_tokens.split(",") if t.strip()]

    return len(top_tokens)


def _read_anchors_quality_timeseries() -> dict[str, float]:
    """
    anchors_quality_timeseries.csv があれば読み、date->anchors_quality を返す。
    ヘッダ名は以下を優先して探す:
      date, anchors_quality / quality / anchors_quality_mean
    """
    if not AQ_CSV.exists():
        return {}

    with AQ_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return {}

        fields = {name.strip(): name for name in reader.fieldnames}

        date_col = None
        for cand in ("date", "day", "dt"):
            if cand in fields:
                date_col = fields[cand]
                break

        q_col = None
        for cand in ("anchors_quality", "quality", "anchors_quality_mean", "anchors_quality_avg"):
            if cand in fields:
                q_col = fields[cand]
                break

        if date_col is None or q_col is None:
            return {}

        out: dict[str, float] = {}
        for row in reader:
            d = (row.get(date_col) or "").strip()[:10]
            q = _safe_float(row.get(q_col), default=None)
            if d and q is not None:
                out[d] = q
        return out


def main():
    files = sorted(ANALYSIS_DIR.glob("daily_summary_*.json"))
    if not files:
        print(f"[NG] no daily_summary_*.json found in: {ANALYSIS_DIR}")
        return

    aq_map = _read_anchors_quality_timeseries()

    rows: list[tuple[datetime, str, float, float, str]] = []
    for fp in files:
        try:
            doc = _load_json(fp)
        except Exception:
            continue

        date_str = _extract_date_str(doc, fp)
        if not date_str:
            continue

        dt = _parse_date(date_str)
        if dt is None:
            continue

        conf = _extract_confidence(doc)
        if conf is None:
            continue

        # anchors_quality が使えればそれを優先、無ければ anchors_n
        aq = _safe_float(doc.get("anchors_quality"), default=None)
        if aq is None:
            aq = aq_map.get(date_str)

        anchors_n = _extract_anchors_n(doc)

        metric_val = aq if aq is not None else float(anchors_n)
        metric_name = "anchors_quality" if aq is not None else "anchors_n"

        rows.append((dt, date_str, conf, metric_val, metric_name))

    if not rows:
        print(f"[NG] no usable rows (date+confidence) in: {ANALYSIS_DIR}")
        return

    rows.sort(key=lambda x: x[0])
    dates = [r[1] for r in rows]
    confs = [r[2] for r in rows]
    metric_vals = [r[3] for r in rows]
    metric_name = rows[-1][4]

    # ========= 1) 二軸：date × (confidence, metric) =========
    fig, ax1 = plt.subplots()
    ax1.plot(dates, confs, marker="o")
    ax1.set_title(f"confidence (line) vs {metric_name} (bars)")
    ax1.set_xlabel("date")
    ax1.set_ylabel("confidence")
    ax1.set_ylim(0.0, 1.0)
    ax1.tick_params(axis="x", rotation=30)

    ax2 = ax1.twinx()
    ax2.bar(dates, metric_vals, alpha=0.3)
    ax2.set_ylabel(metric_name)

    out1 = ANALYSIS_DIR / "confidence_anchors_dual.png"
    fig.tight_layout()
    fig.savefig(out1, dpi=150)
    plt.close(fig)
    print(f"[OK] wrote {out1} ({len(rows)} points)")

    # ========= 2) 散布図：metric × confidence =========
    fig2, ax = plt.subplots()
    ax.scatter(metric_vals, confs)
    ax.set_title(f"confidence vs {metric_name}")
    ax.set_xlabel(metric_name)
    ax.set_ylabel("confidence")
    ax.set_ylim(0.0, 1.0)

    for (_, dstr, c, m, _) in rows:
        ax.annotate(dstr, (m, c), fontsize=7, xytext=(4, 4), textcoords="offset points")

    out2 = ANALYSIS_DIR / "confidence_vs_anchors.png"
    fig2.tight_layout()
    fig2.savefig(out2, dpi=150)
    plt.close(fig2)
    print(f"[OK] wrote {out2} ({len(rows)} points)")


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from datetime import datetime

ANALYSIS_DIR = Path("data/world_politics/analysis")
OUT_CSV = ANALYSIS_DIR / "daily_summary_index.csv"
DAILY_COUNTS_CSV = ANALYSIS_DIR / "daily_counts.csv"


def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_daily_counts() -> dict[str, int]:
    """
    daily_counts.csv があれば読む。
    形式は多少違っても耐える（date列とcount列っぽいものを探す）。
    戻り: {"YYYY-MM-DD": count}
    """
    if not DAILY_COUNTS_CSV.exists():
        return {}

    text = DAILY_COUNTS_CSV.read_text(encoding="utf-8-sig", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {}

    reader = csv.DictReader(lines)
    # ヘッダ候補
    date_keys = ["date", "day"]
    count_keys = ["count", "events", "events_count", "n"]

    out: dict[str, int] = {}
    for row in reader:
        if not row:
            continue
        d = None
        for k in date_keys:
            if k in row and row[k]:
                d = row[k].strip()
                break
        if not d:
            continue

        c = None
        for k in count_keys:
            if k in row and row[k]:
                c = row[k].strip()
                break
        if c is None:
            continue

        try:
            out[d] = int(float(c))
        except Exception:
            continue
    return out


def _extract_churn_from_doc(doc: dict, denom: int | None) -> float | None:
    """
    churn = (added + removed) / denom を基本にする。
    denom は baseline(昨日)の events_count を使うのが理想。
    取れない場合は today の events_count → それも無ければ None。
    """
    anchors = doc.get("anchors") or {}
    counts = anchors.get("counts") or {}
    added = int(_safe_float(counts.get("added"), 0) or 0)
    removed = int(_safe_float(counts.get("removed"), 0) or 0)

    if denom is None or denom <= 0:
        return None

    churn = (added + removed) / float(denom)
    # 0..1 に軽くクランプ（外れ値でグラフが壊れるの防止）
    if churn < 0:
        churn = 0.0
    if churn > 1:
        churn = 1.0
    return churn


def _guess_today_count(daily_counts: dict[str, int], date_str: str) -> int | None:
    return daily_counts.get(date_str)


def _guess_baseline_count(daily_counts: dict[str, int], baseline_date: str | None) -> int | None:
    if not baseline_date:
        return None
    return daily_counts.get(baseline_date)


def _normalize_date(s: str) -> str | None:
    # "2026/1/1" や "2026-01-01" を "YYYY-MM-DD" に寄せる
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.fromisoformat(s) if "T" in fmt else datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    # だめならそのまま返す（最悪）
    return s


def main():
    daily_counts = _load_daily_counts()

    files = sorted(ANALYSIS_DIR.glob("daily_summary_*.json"))
    rows = []

    for fp in files:
        try:
            doc = _read_json(fp)
        except Exception:
            continue

        meta = doc.get("meta") or {}
        date_str = _normalize_date(meta.get("date") or "")
        if not date_str:
            continue

        conf = _safe_float(doc.get("confidence_of_hypotheses"))
        if conf is None:
            # 古い形式の可能性を少し救う
            conf = _safe_float(doc.get("confidence"))

        baseline_date = _normalize_date(meta.get("baseline_date") or "")

        # denom は「baseline の events_count」を優先、なければ today
        denom = _guess_baseline_count(daily_counts, baseline_date)
        if denom is None:
            denom = _guess_today_count(daily_counts, date_str)

        churn = _extract_churn_from_doc(doc, denom)

        # churn が取れない日もあるので、空欄で出す（plot側で弾ける）
        rows.append(
            {
                "date": date_str,
                "confidence": "" if conf is None else f"{conf:.4f}",
                "churn": "" if churn is None else f"{churn:.4f}",
            }
        )

    # date 昇順
    rows.sort(key=lambda r: r["date"])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "confidence", "churn"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    kept = sum(1 for r in rows if r.get("confidence") not in ("", None))
    print(f"[OK] wrote {OUT_CSV} ({len(rows)} rows, {kept} with confidence)")


if __name__ == "__main__":
    main()

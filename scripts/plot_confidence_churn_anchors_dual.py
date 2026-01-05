from __future__ import annotations

from pathlib import Path
import csv

import matplotlib.pyplot as plt


DATA_DIR = Path("data")
CATEGORY = "world_politics"
ANALYSIS_DIR = DATA_DIR / CATEGORY / "analysis"


def _read_index_csv(path: Path):
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows


def main() -> None:
    idx = ANALYSIS_DIR / "daily_summary_index.csv"
    if not idx.exists():
        raise FileNotFoundError(idx)

    rows = _read_index_csv(idx)
    # date順（文字列 YYYY-MM-DD 前提）
    rows.sort(key=lambda x: x.get("date", ""))

    dates = [r["date"] for r in rows]
    confidence = [float(r["confidence"]) for r in rows]

    churn = []
    for r in rows:
        v = (r.get("churn") or "").strip()
        churn.append(float(v) if v else None)

    anchors_n = [int(float(r.get("anchors_n") or 0)) for r in rows]

    x = list(range(len(dates)))

    fig, ax1 = plt.subplots(figsize=(12, 4))

    # confidence
    ax1.plot(x, confidence, marker="o", label="confidence")
    ax1.set_ylabel("confidence")

    # churn（ある日だけ描画）
    if any(v is not None for v in churn):
        x2 = [xi for xi, v in zip(x, churn) if v is not None]
        y2 = [v for v in churn if v is not None]
        ax1.plot(x2, y2, marker="x", label="churn")

    ax1.set_ylim(0.0, 1.0)
    ax1.grid(True, axis="y")

    # anchors_n（右軸）
    ax2 = ax1.twinx()
    ax2.bar(x, anchors_n, alpha=0.25, label="anchors_n")
    ax2.set_ylabel("anchors_n (len(top_tokens))")

    ax1.set_xticks(x)
    ax1.set_xticklabels(dates, rotation=30, ha="right")
    ax1.set_title("confidence & churn (lines) vs anchors_n (bars)")

    # 凡例（左右まとめて）
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")

    out = ANALYSIS_DIR / "confidence_churn_anchors_dual.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"[OK] wrote {out} ({len(rows)} points)")


if __name__ == "__main__":
    main()

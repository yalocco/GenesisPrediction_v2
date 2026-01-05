# scripts/plot_confidence_churn_regime.py
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "world_politics" / "analysis"
INDEX_CSV = ANALYSIS_DIR / "daily_summary_index.csv"
OUT_PNG = ANALYSIS_DIR / "regime.png"


def _safe_float(x, default=None):
    try:
        if x is None:
            return default
        s = str(x).strip()
        if s == "":
            return default
        return float(s)
    except Exception:
        return default


def classify_regime(conf: float, churn: float, conf_thr: float, churn_thr: float) -> str:
    """
    4象限:
      - stable:     high conf, low churn
      - rotation:   high conf, high churn
      - noisy:      low  conf, high churn
      - flat/weak:  low  conf, low churn
    """
    high_conf = conf >= conf_thr
    high_churn = churn >= churn_thr

    if high_conf and (not high_churn):
        return "stable (high conf / low churn)"
    if high_conf and high_churn:
        return "rotation (high conf / high churn)"
    if (not high_conf) and high_churn:
        return "noisy (low conf / high churn)"
    return "flat/weak (low conf / low churn)"


def main():
    if not INDEX_CSV.exists():
        raise FileNotFoundError(f"index csv not found: {INDEX_CSV}")

    rows = []
    with INDEX_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # churn / confidence 列名の揺れを吸収
        for r in reader:
            date = (r.get("date") or "").strip()
            conf = _safe_float(r.get("confidence"), default=None)
            churn = _safe_float(r.get("churn"), default=None)

            # どちらか欠けてたらスキップ
            if not date or conf is None or churn is None:
                continue
            rows.append((date, conf, churn))

    if not rows:
        raise RuntimeError("No valid rows found. Ensure daily_summary_index.csv has date, confidence, churn columns.")

    # 日付順（YYYY-MM-DD前提）
    rows.sort(key=lambda x: x[0])

    dates = [d for d, _, _ in rows]
    confs = [c for _, c, _ in rows]
    churns = [ch for _, _, ch in rows]

    # 閾値（頑丈で直感的）
    conf_thr = 0.70
    churn_thr = 0.12

    regimes = [classify_regime(c, ch, conf_thr, churn_thr) for c, ch in zip(confs, churns)]

    # regime ごとに描画（色指定しない＝matplotlibのデフォルト配色に任せる）
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # 描画順を固定（凡例が安定）
    order = [
        "stable (high conf / low churn)",
        "rotation (high conf / high churn)",
        "noisy (low conf / high churn)",
        "flat/weak (low conf / low churn)",
    ]

    for label in order:
        xs = [ch for (d, c, ch), rg in zip(rows, regimes) if rg == label]
        ys = [c for (d, c, ch), rg in zip(rows, regimes) if rg == label]
        ds = [d for (d, c, ch), rg in zip(rows, regimes) if rg == label]
        if not xs:
            continue

        ax.scatter(xs, ys, label=label)

        # 点に日付ラベル（多くなったら後でOFF化してもOK）
        for x, y, d in zip(xs, ys, ds):
            ax.annotate(d, (x, y), textcoords="offset points", xytext=(4, 4), fontsize=8)

    # 閾値線
    ax.axhline(conf_thr)
    ax.axvline(churn_thr)

    ax.set_title("regime: confidence × churn")
    ax.set_xlabel("churn")
    ax.set_ylabel("confidence")
    ax.set_xlim(0.0, max(0.2, max(churns) * 1.25))
    ax.set_ylim(0.0, 1.0)
    ax.legend(loc="lower left", fontsize=8)

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150)

    print(f"[OK] wrote {OUT_PNG} ({len(rows)} points)")
    print(f"[INFO] thresholds: conf_thr={conf_thr}, churn_thr={churn_thr}")
    print("[INFO] If you want stricter/looser regimes, change conf_thr / churn_thr.")


if __name__ == "__main__":
    main()

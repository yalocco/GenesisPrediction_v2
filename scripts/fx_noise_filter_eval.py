import pandas as pd
from pathlib import Path

PRED_CSV = Path("data/fx/usd_jpy_noise_forecast.csv")
LABELED3_CSV = Path("data/fx/usd_jpy_miss_events_labeled3.csv")

def main():
    if not PRED_CSV.exists():
        raise SystemExit(f"[ERR] not found: {PRED_CSV}")
    if not LABELED3_CSV.exists():
        raise SystemExit(f"[ERR] not found: {LABELED3_CSV}")

    pred = pd.read_csv(PRED_CSV)
    pred["date"] = pd.to_datetime(pred["date"]).dt.date

    lab = pd.read_csv(LABELED3_CSV)
    lab["miss_date"] = pd.to_datetime(lab["miss_date"]).dt.date
    cls_col = "class3" if "class3" in lab.columns else ("class" if "class" in lab.columns else None)
    if not cls_col:
        raise SystemExit("[ERR] labeled3 csv must have class3 or class")

    lab = lab.rename(columns={"miss_date": "date", cls_col: "class3"})[["date", "class3"]]

    m = pred.merge(lab, on="date", how="left")

    # ラベルが無い日は「missとして評価対象外」なので落とす
    m = m[m["class3"].notna()].copy()

    # noiseを当てたい（二値化）
    m["is_noise"] = (m["class3"] == "noise").astype(int)
    m["flag"] = m["decision"].isin(["WARN", "OFF"]).astype(int)

    tp = int(((m["flag"] == 1) & (m["is_noise"] == 1)).sum())
    fp = int(((m["flag"] == 1) & (m["is_noise"] == 0)).sum())
    tn = int(((m["flag"] == 0) & (m["is_noise"] == 0)).sum())
    fn = int(((m["flag"] == 0) & (m["is_noise"] == 1)).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    # “避けた日”の比率
    flagged_rate = m["flag"].mean()

    print("[OK] noise filter evaluation")
    print(f"days_evaluated={len(m)}  flagged_rate={flagged_rate:.2%}")
    print(f"TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"precision={precision:.2%}  recall={recall:.2%}")

    # 参考：class別にWARN/OFFがどれくらい出たか
    by_cls = (
        m.groupby("class3")["flag"]
        .agg(["count", "mean"])
        .rename(columns={"mean": "flag_rate"})
        .sort_values("count", ascending=False)
    )
    print("\n[INFO] flag rate by class")
    print(by_cls.to_string())

if __name__ == "__main__":
    main()

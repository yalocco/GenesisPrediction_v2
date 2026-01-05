from pathlib import Path
import csv
import matplotlib.pyplot as plt

DATA_DIR = Path("data")
CATEGORY = "world_politics"
ANALYSIS_DIR = DATA_DIR / CATEGORY / "analysis"

def main():
    csv_path = ANALYSIS_DIR / "daily_summary_index.csv"
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    dates = []
    confidences = []

    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = row.get("date")
            conf = row.get("confidence")
            if not date or not conf:
                continue
            try:
                confidences.append(float(conf))
                dates.append(date)
            except ValueError:
                continue

    if not confidences:
        raise SystemExit("No valid confidence data")

    plt.figure(figsize=(8, 4))
    plt.plot(dates, confidences, marker="o")
    plt.ylim(0, 1.0)
    plt.title("confidence_of_hypotheses")
    plt.xlabel("date")
    plt.ylabel("confidence")
    plt.grid(True)

    out = ANALYSIS_DIR / "confidence.png"
    plt.tight_layout()
    plt.savefig(out)
    plt.close()

    print(f"[OK] wrote {out}")

if __name__ == "__main__":
    main()

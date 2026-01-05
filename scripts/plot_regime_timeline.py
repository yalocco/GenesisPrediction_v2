import json
from pathlib import Path
import matplotlib.pyplot as plt

ANALYSIS_DIR = Path("data/world_politics/analysis")

def normalize(regime: str) -> str:
    return regime.split("(")[0].strip() if regime else "unknown"

def main():
    files = sorted(ANALYSIS_DIR.glob("daily_summary_*.json"))
    if not files:
        raise RuntimeError("No daily_summary_*.json found")

    dates = []
    regimes = []

    for f in files:
        with f.open(encoding="utf-8") as fh:
            doc = json.load(fh)

        date = doc.get("meta", {}).get("date")
        regime = doc.get("regime")

        if not date or not regime:
            continue

        dates.append(date)
        regimes.append(normalize(regime))

    if not dates:
        raise RuntimeError("No valid (date, regime) pairs found")

    # regime を数値に変換
    uniq = list(dict.fromkeys(regimes))
    y = [uniq.index(r) for r in regimes]

    plt.figure(figsize=(10, 4))
    plt.plot(dates, y, marker="o")
    plt.yticks(range(len(uniq)), uniq)
    plt.xlabel("date")
    plt.ylabel("regime")
    plt.title("regime × time")
    plt.grid(True)
    plt.tight_layout()

    out = ANALYSIS_DIR / "regime_timeline.png"
    plt.savefig(out, dpi=150)
    print(f"[OK] wrote {out} ({len(dates)} points)")

if __name__ == "__main__":
    main()

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import csv

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data/world_politics/analysis"
HISTORY = ROOT / "data/history"

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def today_iso(d=None):
    return d if d else datetime.utcnow().strftime("%Y-%m-%d")

def score_event(seed, sentiment, anchors):
    score = 0.0
    matched = {"tags": [], "anchors": [], "sentiment": []}

    # tag match
    for t in seed["tags"]:
        if t in anchors:
            score += 0.02
            matched["tags"].append(t)

    # anchor match
    for a in seed["anchors"]:
        if a in anchors:
            score += 0.03
            matched["anchors"].append(a)

    # sentiment shape
    for k in ["risk", "uncertainty", "positive"]:
        diff = abs(seed["sentiment_profile"][k] - sentiment.get(k, 0))
        score += max(0, 0.1 - diff)
        if diff < 0.2:
            matched["sentiment"].append(k)

    return min(score, 1.0), matched

def main(date=None):
    date = today_iso(date)

    sent = load_json(ANALYSIS / f"sentiment_{date}.json")
    anchors = sent.get("anchors", [])
    sentiment = sent.get("summary", {})

    seeds = load_json(HISTORY / "seed_events.json")["events"]

    ranked = []
    for ev in seeds:
        s, matched = score_event(ev, sentiment, anchors)
        if s > 0:
            ranked.append({
                "event": ev["name"],
                "score": round(s, 3),
                "matched": matched
            })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    top = ranked[:3]

    out = {
        "date": date,
        "top_analogs": top,
        "note": "Analog is similarity, not prediction."
    }

    (ANALYSIS / f"analog_{date}.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # timeseries
    csv_path = ANALYSIS / "analog_timeseries.csv"
    rows = []
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    rows = [r for r in rows if r["date"] != date]
    rows.append({"date": date, "top_score": top[0]["score"] if top else 0})

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "top_score"])
        w.writeheader()
        w.writerows(rows)

if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else None
    main(d)

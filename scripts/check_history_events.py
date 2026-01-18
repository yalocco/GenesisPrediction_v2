import json
from pathlib import Path

path = Path("resources/history/seed_events_10.json")

with path.open("r", encoding="utf-8") as f:
    events = json.load(f)

print(f"loaded events: {len(events)}")
print("sample titles:")
for e in events[:3]:
    print("-", e["title"])

import os
import requests
import json
from datetime import datetime

API_KEY = os.getenv("NEWSAPI_KEY")
QUERY = os.getenv("QUERY", "world politics")
LANG = os.getenv("LANGUAGE", "en")

url = "https://newsapi.org/v2/everything"
params = {
    "q": QUERY,
    "language": LANG,
    "sortBy": "publishedAt",
    "pageSize": 50,
    "apiKey": API_KEY
}

res = requests.get(url, params=params)
res.raise_for_status()
data = res.json()

date = datetime.utcnow().strftime("%Y-%m-%d")
out_dir = "/data/world_politics"
os.makedirs(out_dir, exist_ok=True)

with open(f"{out_dir}/{date}.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Saved {len(data.get('articles', []))} articles")

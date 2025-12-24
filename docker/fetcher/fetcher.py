import os
import json
import requests
from datetime import datetime, timezone

API_KEY = os.getenv("NEWSAPI_KEY")
QUERY = "world politics"
LANG = "en"
PAGE_SIZE = 50

if not API_KEY:
    raise RuntimeError("NEWSAPI_KEY is not set")

url = "https://newsapi.org/v2/everything"
params = {
    "q": QUERY,
    "language": LANG,
    "pageSize": PAGE_SIZE,
    "sortBy": "publishedAt",
    "apiKey": API_KEY,
}

res = requests.get(url, params=params, timeout=30)
res.raise_for_status()
data = res.json()

# 保存先
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
out_dir = "/data/world_politics"
os.makedirs(out_dir, exist_ok=True)
out_path = f"{out_dir}/{today}.json"

payload = {
    "fetched_at": datetime.now(timezone.utc).isoformat(),
    "query": QUERY,
    "totalResults": data.get("totalResults"),
    "articles": data.get("articles", []),
}

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"[OK] saved {len(payload['articles'])} articles to {out_path}")

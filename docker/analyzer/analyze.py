import json
import csv
from pathlib import Path
from datetime import datetime, timezone

DATA_ROOT = Path("/data")
TOPIC = "world_politics"
IN_DIR = DATA_ROOT / TOPIC
OUT_DIR = IN_DIR / "analysis"

def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # NewsAPI: "2025-12-21T04:13:00Z"
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None

def safe_text(x):
    return x if isinstance(x, str) else ""

def load_articles(path: Path):
    obj = json.loads(path.read_text(encoding="utf-8"))
    articles = obj.get("articles", [])
    fetched_at = obj.get("fetched_at") or obj.get("fetchedAt") or obj.get("fetched") or ""
    query = obj.get("query") or ""
    return articles, fetched_at, query, obj

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    json_files = sorted(IN_DIR.glob("*.json"))
    if not json_files:
        print(f"No input json found in: {IN_DIR}")
        return

    # 集計用
    daily_counts = {}          # YYYY-MM-DD -> count
    source_counts = {}         # source_name -> count

    latest_item = None
    latest_dt = None

    # すべての入力を舐めて、正規化イベント(JSONL)を書き出す
    for jf in json_files:
        day = jf.stem  # "2025-12-22"
        events_path = OUT_DIR / f"events_{day}.jsonl"

        articles, fetched_at, query, raw = load_articles(jf)

        # JSONLは毎回作り直し（同日を再フェッチしても最新で上書き）
        with events_path.open("w", encoding="utf-8") as w:
            for a in articles:
                src = a.get("source") or {}
                src_name = safe_text(src.get("name") or src.get("id") or "")

                published = safe_text(a.get("publishedAt"))
                published_dt = parse_dt(published)

                event = {
                    "schema_version": "v1",
                    "category": TOPIC,
                    "provider": "newsapi",
                    "query": query,
                    "fetched_at": fetched_at,
                    "published_at": published,  # 文字列のまま保持
                    "title": safe_text(a.get("title")),
                    "description": safe_text(a.get("description")),
                    "url": safe_text(a.get("url")),
                    "source": {
                        "id": safe_text(src.get("id")),
                        "name": src_name
                    },
                    "author": safe_text(a.get("author")),
                    "image": safe_text(a.get("urlToImage")),
                    "content": safe_text(a.get("content")),
                }

                w.write(json.dumps(event, ensure_ascii=False) + "\n")

                # 集計
                daily_counts[day] = daily_counts.get(day, 0) + 1
                if src_name:
                    source_counts[src_name] = source_counts.get(src_name, 0) + 1

                # 最新記事候補
                if published_dt:
                    if latest_dt is None or published_dt > latest_dt:
                        latest_dt = published_dt
                        latest_item = event

    # daily_counts.csv（昇順）
    csv_path = OUT_DIR / "daily_counts.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "count"])
        for day in sorted(daily_counts.keys()):
            writer.writerow([day, daily_counts[day]])

    # latest.json
    top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    summary = {
        "topic": TOPIC,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": len(daily_counts),
        "total_articles_in_files": sum(daily_counts.values()),
        "top_sources": [{"source": k, "count": v} for k, v in top_sources],
        "latest_article": latest_item,
    }
    (OUT_DIR / "latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Analyzed: {len(json_files)} file(s)")
    print(f"Wrote: {csv_path}")
    print(f"Wrote: {OUT_DIR / 'latest.json'}")

if __name__ == "__main__":
    main()

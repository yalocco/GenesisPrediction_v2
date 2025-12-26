GenesisPrediction_v2/
├─ docker/
│  ├─ fetcher/
│  │  ├─ Dockerfile
│  │  ├─ fetcher.py
│  │  └─ requirements.txt
│  └─ analyzer/
│     ├─ Dockerfile
│     ├─ analyze.py
│     └─ requirements.txt
│
├─ data/                     ← 実行時に生成されるデータ（Git管理外）
│  └─ world_politics/
│     ├─ 2025-12-25.json
│     └─ analysis/
│        ├─ daily_counts.csv
│        ├─ events_*.jsonl
│        ├─ sentiment_summary.json
│        └─ topic_counts.json
│
├─ docker-compose.yml         ← ★唯一使う compose
├─ .env                       ← APIキー（Git管理外）
├─ .gitignore
└─ README.md



cd D:\AI\Projects\GenesisPrediction_v2
docker compose build
docker compose run --rm fetcher
docker compose run --rm analyzer

docker compose build --no-cache
docker compose run --rm fetcher
docker compose run --rm analyzer

docker compose run --rm analyzer

git status
git status --untracked-files
git add -u
git add docker/analyzer/analyze.py
git add docker/analyzer/diff.py
git add docker/analyzer/Dockerfile
git commit -m "Fix daily diff generation and stabilize analyzer execution flow"
git push origin main


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


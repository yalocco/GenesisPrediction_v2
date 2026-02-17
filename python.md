ルーティーン（最短・安全）

朝はこれだけ（正式）：
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1

カテゴリー
powershell -ExecutionPolicy Bypass -File scripts/run_daily_categories.ps1

たまに（Guard付き）：
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Guard

日付指定（検証・復旧用）：
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-16

サーバー（GUI）
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000


公開したい日だけ deploy
powershell -ExecutionPolicy Bypass -File scripts/run_deploy_labos.ps1


週一（メンテ）
report_sentiment_gaps.ps1
backfill_missing_sentiment.ps1


欠損の棚卸し（必要に応じて）
powershell -ExecutionPolicy Bypass -File scripts/report_sentiment_gaps.ps1 -Days 60


欠損を埋めて timeseries を作り直す（週1とかでOK）
powershell -ExecutionPolicy Bypass -File scripts/backfill_missing_sentiment.ps1 -Days 60


画像が最新か確認（例）
Get-Item .\data\world_politics\analysis\jpy_thb_remittance_overlay.png | Select-Object LastWriteTime


Observation（必要な日だけ）
(1) 日次パイプラインを回したあと
.\.venv\Scripts\python.exe scripts\build_daily_observation_log.py --date (Get-Date -Format "yyyy-MM-dd")

(2) まとめMDが欲しい日だけ
.\.venv\Scripts\python.exe scripts\update_observation_md.py --date (Get-Date -Format "yyyy-MM-dd")

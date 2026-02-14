ルーティーン（最短・安全）

サーバー
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000

powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1

FX軽取得
powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_rates.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_inputs.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_daily_fx_overlay.ps1

最後に
powershell -ExecutionPolicy Bypass -File scripts/run_daily_with_publish.ps1 -RunGuard

公開したい日だけdeploy
powershell -ExecutionPolicy Bypass -File scripts/run_deploy_labos.ps1




週一で
report_sentiment_gaps.ps1
backfill_missing_sentiment.ps1

画像正整☑
Get-Item .\data\world_politics\analysis\jpy_thb_remittance_overlay.png | Select-Object LastWriteTime
powershell -ExecutionPolicy Bypass -File scripts/report_sentiment_gaps.ps1 -Days 30

# (1) 日次パイプラインを回したあと
.\.venv\Scripts\python.exe scripts\build_daily_observation_log.py --date (Get-Date -Format "yyyy-MM-dd")

# (2) まとめMDが欲しい日だけ
.\.venv\Scripts\python.exe scripts\update_observation_md.py --date (Get-Date -Format "yyyy-MM-dd")

欠損の棚卸し
powershell -ExecutionPolicy Bypass -File scripts/report_sentiment_gaps.ps1 -Days 60

欠損を埋めて timeseries を作り直す（週1とかでOK）
powershell -ExecutionPolicy Bypass -File scripts/backfill_missing_sentiment.ps1 -Days 60



指定日で回す
.\scripts\run_daily.ps1 -date 2026-01-25

.\.venv\Scripts\python.exe scripts\clean_daily_summary_anchors.py

毎回これだけ実行
.\.venv\Scripts\python.exe scripts\run_daily_pipeline.py

日次ルーチン（更新案）
docker compose run --rm analyzer
.\.venv\Scripts\python.exe scripts\clean_daily_summary_anchors.py
.\.venv\Scripts\python.exe scripts\score_daily_summary_anchors.py

ステップ2（3〜5日後）
.\.venv\Scripts\python.exe scripts\build_stop_candidates.py --days 14

日次ルーチン
fetch / analyze / daily_summary 生成
clean_daily_summary_anchors.py
score_daily_summary_anchors.py
build_anchors_quality_timeseries.py
build_stop_candidates.py
build_weak_anchor_candidates.py
git status → clean なら終了

日次ルーチン
docker compose run --rm analyzer
.\.venv\Scripts\python.exe scripts\clean_daily_summary_anchors.py
.\.venv\Scripts\python.exe scripts\score_daily_summary_anchors.py
.\.venv\Scripts\python.exe scripts\build_anchors_quality_timeseries.py
.\.venv\Scripts\python.exe scripts\build_stop_candidates.py --days 14
.\.venv\Scripts\python.exe scripts\build_weak_anchor_candidates.py --days 14
.\.venv\Scripts\python.exe scripts\build_daily_news_digest.py --date 2026-01-14


guiを起動
.\.venv\Scripts\python.exe -m uvicorn app.server:app --reload --host 127.0.0.1 --port 8000

グラフ起動
.\.venv\Scripts\python.exe scripts\fx_overlay.py
.\.venv\Scripts\python.exe scripts\fx_remittance_overlay.py


events_xxxx-xx-xx.jsonlが生成されない場合
docker compose run --rm analyzer

gui起動 タイバーツ
-NoProfile -ExecutionPolicy Bypass -File "D:\AI\Projects\GenesisPrediction_v2\scripts\fx_monthly_report_gui.ps1"

壊れた raw を退避
Move-Item .\data\world_politics\2026-01-26.json .\data\world_politics\2026-01-26.json.bad
docker compose run --rm fetcher
docker compose run --rm analyzer
























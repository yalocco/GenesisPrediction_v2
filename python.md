ルーティーン（最短・安全）
.\.venv\Scripts\Activate.ps1
docker compose run --rm analyzer
scripts/run_daily.ps1
python -m uvicorn app.server:app --reload --host 127.0.0.1 --port 8000


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























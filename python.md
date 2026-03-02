# GenesisPrediction v2 - Python / Server Routine

■ ルーティーン（最短・安全）
【朝の儀式（正式）】
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1
【日付指定で実行する場合】
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-24

■ ローカルサーバー起動（正式）
powershell -ExecutionPolicy Bypass -File scripts/run_server.ps1
※ これが標準起動方法。
※ 会社PC / 自宅PC 共通。
※ 手打ち禁止（人間ミス防止）。

■ 緊急用（手動起動）
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000
※ run_server.ps1 が使えない場合のみ。
※ 通常は使用しない。

■ Deploy（自宅PC専用）
powershell -ExecutionPolicy Bypass -File scripts/run_deploy_labos.ps1
※ 会社PCでは実行しない。
※ 公開作業は必ず自宅PC。

========================================
■ 起動確認（最低限）
========================================

http://127.0.0.1:8000/static/index.html
http://127.0.0.1:8000/static/overlay.html
http://127.0.0.1:8000/static/sentiment.html

========================================
■ 原則
========================================

・入口は1つに固定する（run_server.ps1）
・差分貼り付け禁止
・完全ファイルのみ更新
・1ターン = 1作業
・Working Tree Clean を維持する
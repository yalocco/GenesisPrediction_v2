# GenesisPrediction v2 - Python / Server Routine

■ ルーティーン（最短・安全）
【朝の儀式（正式）】
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1
【日付指定で実行する場合】
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-24
【未commitある場合】
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -AllowDirtyRepo

■ ローカルサーバー起動（正式）
powershell -ExecutionPolicy Bypass -File scripts/run_server.ps1

■ 緊急用（手動起動）
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000

■ Deploy（自宅PC専用）
powershell -ExecutionPolicy Bypass -File scripts/run_labos_publish.ps1

# 会社PC
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1

# 自宅PC
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -DeployLabos


上は以下を同時に行う
python scripts/build_global_status_latest.py --root . --pretty
powershell -ExecutionPolicy Bypass -File scripts/build_labos_deploy_payload.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_deploy_labos.ps1

--------------------------------------------------------------
docs/ui_data_dependencies.md を更新しますか？

--------------------------------------------------------------
新スレ立ち上げ時
AI bootstrap
docs/ai_bootstrap.md を読み込んでください。

Thread Task:
（今回の作業内容）
--------------------------------------------------------------
ルーティーン（最短・安全）

朝はこれだけ（正式）：
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1

日付をつけて
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-24

サーバー（GUI）
python -m uvicorn app.server:app --host 127.0.0.1 --port 8000

公開したい日だけ deploy
powershell -ExecutionPolicy Bypass -File scripts/run_deploy_labos.ps1


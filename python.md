# GenesisPrediction v2 - Python / Server Routine

■ ルーティーン（最短・安全）
【朝の儀式（正式）】
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1

ガード阻止
git add -A
git commit -m "WIP: pass dirty guard before morning ritual"

【日付指定で実行する場合】
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -Date 2026-02-24

■ ローカルサーバー起動（正式）
powershell -ExecutionPolicy Bypass -File scripts/run_server.ps1

■ VectorDB　更新チェック
python scripts/check_vector_memory_freshness.py

■ VectorDB　更新
python scripts/build_vector_memory.py --recreate

■ Deploy（自宅PC専用）
powershell -ExecutionPolicy Bypass -File scripts/run_labos_publish.ps1

■ decision_index（更新）
python build_decision_index.py --input docs/core/decision_log.md --output docs/core/decision_index.md

--------------------------------------------------------------

■ ollama update
① コンテナ停止
docker stop ollama-docker
② コンテナ削除
docker rm ollama-docker
③ 最新イメージ取得
docker pull ollama/ollama:latest
④ 再作成
docker run -d -p 11435:11434 --name ollama-docker -v ollama:/root/.ollama ollama/ollama:latest
⑤ 再トライ
docker exec -it ollama-docker ollama pull gemma4:e4b




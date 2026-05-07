# README_NoLLM_Final_Fix_v1

Save path:

```text
scripts/run_morning_ritual.ps1
scripts/README_NoLLM_Final_Fix_v1.md
```

Purpose:

This final NoLLM fix passes `--no-llm` to the extra `build_daily_sentiment.py` call inside `run_morning_ritual.ps1`.

Why:

`run_daily_with_publish.ps1` already passed `--no-llm`, but `run_morning_ritual.ps1` invoked `build_daily_sentiment.py` again without that flag. That second call was still able to trigger Ollama `/api/generate`.

Expected verification:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -NoLLM
docker logs ollama-docker --since 10s
```

Expected result:

No new `/api/generate` entries after the NoLLM run has completed.

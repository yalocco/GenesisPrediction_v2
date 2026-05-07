# GenesisPrediction NoLLM Sentiment Fix v1

Purpose: make `-NoLLM` mode fully skip Ollama during daily sentiment generation.

Files:

```text
scripts/build_daily_sentiment.py
scripts/run_daily_with_publish.ps1
```

Usage:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -NoLLM
```

Expected behavior:

```text
- build_daily_sentiment.py receives --no-llm
- title_i18n / description_i18n / summary_i18n keep the same schema
- ja/th values are copied from English in NoLLM mode
- Ollama / GPU translation is not called by sentiment build
```

Line counts:

```text
build_daily_sentiment.py: 845 -> 854
run_daily_with_publish.ps1: 539 -> 545
```

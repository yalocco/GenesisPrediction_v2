# GenesisPrediction NoLLM Digest Fix v1

## Purpose

This package completes the NoLLM path for the digest builder.

In `-NoLLM` mode, `build_digest_view_model.py` now avoids `translate_text_block()` and uses English-shadow i18n instead. This prevents Digest generation from calling Ollama `/api/generate`.

## Files

Save these files into the repository:

```text
scripts/build_digest_view_model.py
scripts/run_daily_with_publish.ps1
scripts/README_NoLLM_Digest_Fix_v1.md
```

## Test command

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -NoLLM
```

## Expected log markers

```text
[NoLLM] build_digest_view_model.py runs without Ollama translation.
[NoLLM] digest i18n runs in English-first mode; Ollama translation is skipped
```

## Ollama verification

Immediately after the run:

```powershell
docker logs ollama-docker --since 5m
```

Expected result: no new `POST "/api/generate"` entries from the NoLLM run.

## Operational meaning

Full mode remains unchanged. Only `-NoLLM` mode bypasses digest LLM translation.

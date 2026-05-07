# GitHub Actions NoLLM Trial

Save this file:

```text
.github/workflows/nollm_morning_ritual_trial.yml
```

Purpose:

```text
iPad / browser → GitHub Actions → NoLLM Morning Ritual trial
```

This first workflow is intentionally trial-only:

- No deploy step
- No Ollama
- No vector memory rebuild
- Runs `scripts/run_morning_ritual.ps1 -NoLLM`
- Uploads generated artifacts for inspection

## How to run

1. Commit and push the workflow file.
2. Open GitHub repository.
3. Go to **Actions**.
4. Select **NoLLM Morning Ritual Trial**.
5. Press **Run workflow**.
6. Leave `run_date` empty unless testing a specific date.
7. Keep `skip_fx=false` first. If FX causes trouble on GitHub runner, rerun with `skip_fx=true`.

## Expected result

The workflow should finish with:

```text
[OK] Morning Ritual completed
```

And an artifact named:

```text
genesis-nollm-trial-artifacts
```

## Important

This is not the final iPad deploy workflow yet. This is a safe runner-compatibility test.
After this succeeds, the next step is adding deploy secrets and a controlled deploy job.

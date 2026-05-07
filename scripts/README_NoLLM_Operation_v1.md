# GenesisPrediction NoLLM Operation v1

Save paths:

- scripts/run_morning_ritual.ps1
- scripts/run_daily_with_publish.ps1

Purpose:

- Enable English-first / NoLLM operation for travel and future iPad/GitHub Actions operation.
- Keep the core Morning Ritual pipeline running without Ollama translation.
- Skip vector memory rebuild in NoLLM mode because vector memory is reference-only.

New command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -NoLLM
```

Behavior in `-NoLLM` mode:

Runs:

- analyzer / fetch lane
- sentiment build
- world view model build without translation/Ollama arguments
- digest build
- trend / signal / scenario / prediction
- health
- refresh latest artifacts

Skips:

- Ollama translation arguments in `run_daily_with_publish.ps1`
- vector memory rebuild in `run_morning_ritual.ps1`

Notes:

- `ja` and `th` translation/refinement scripts are not called by this NoLLM path.
- `build_prediction_explanation.py` and `build_scenario_explanation.py` remain enabled because they are already non-blocking in the current ritual. If either fails, the ritual continues with a warning.
- Use the normal full mode on the home PC for maintenance, translation, vector rebuild, and research work.

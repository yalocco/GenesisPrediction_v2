# GitHub Actions NoLLM Trial v2

Save path:

```text
.github/workflows/nollm_morning_ritual_trial.yml
```

This v2 workflow fixes the first trial failure where `run_daily_with_publish.ps1` received `-Date` without a value on GitHub Actions.

## Change

The workflow now always resolves a concrete run date before calling the PowerShell ritual:

```powershell
$runDate = "${{ github.event.inputs.run_date }}"
if ([string]::IsNullOrWhiteSpace($runDate)) {
  $runDate = Get-Date -Format "yyyy-MM-dd"
}
$argsList = @("-Date", $runDate, "-NoLLM")
./scripts/run_morning_ritual.ps1 @argsList
```

## Usage

1. Save the workflow file over the existing file.
2. Commit and push.
3. Open GitHub → GenesisPrediction_v2 → Actions → NoLLM Morning Ritual Trial.
4. Click **Run workflow**.
5. Leave the date blank unless you want to force a specific date.

This remains a trial workflow. It does not deploy yet.

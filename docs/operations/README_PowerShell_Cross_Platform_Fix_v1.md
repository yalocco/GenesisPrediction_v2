# PowerShell Cross-Platform Fix v1

Purpose:
- Keep Windows Full mode working.
- Allow GitHub Actions Ubuntu runner to execute nested PowerShell scripts.

Change:
- Added Resolve-PowerShellCommand.
- Windows uses `powershell`.
- Linux/macOS/GitHub Actions uses `pwsh`.

Primary file:
- scripts/run_morning_ritual.ps1

Validation:
- Local Windows Full mode should continue to run with:
  powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1
- Local Windows NoLLM mode should continue to run with:
  powershell -ExecutionPolicy Bypass -File scripts/run_morning_ritual.ps1 -NoLLM
- GitHub Actions NoLLM trial should progress beyond the previous `powershell is not recognized` error.

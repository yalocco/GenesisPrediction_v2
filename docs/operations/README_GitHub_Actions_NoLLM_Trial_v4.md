# GitHub Actions NoLLM Trial v4

Fix:
- Ubuntu GitHub runner already runs PowerShell steps with `shell: pwsh`
- Removed nested `powershell` command
- Calls `./scripts/run_morning_ritual.ps1` directly

After replacing the workflow file:
1. git add .
2. git commit -m "Fix GitHub Actions pwsh invocation"
3. git push origin main
4. Re-run workflow from GitHub Actions UI

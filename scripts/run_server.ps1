<# 
GenesisPrediction v2 - Local Dev Server Runner
Stable single entrypoint for local dev server
#>

param(
  [string]$HostAddr = "127.0.0.1",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $here = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $here "..")).Path
}

function Find-PythonExe {
  param([string]$repoRoot)

  $venvWin = Join-Path $repoRoot ".venv\Scripts\python.exe"
  $venvUnix = Join-Path $repoRoot ".venv\bin\python"

  if (Test-Path $venvWin) {
    return $venvWin
  }

  if (Test-Path $venvUnix) {
    return $venvUnix
  }

  return "python"
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

$py = Find-PythonExe $repoRoot

Write-Host ""
Write-Host "GenesisPrediction v2 - Local Server" -ForegroundColor Cyan
Write-Host ("ROOT : {0}" -f $repoRoot)
Write-Host ("PY   : {0}" -f $py)
Write-Host ("HOST : {0}" -f $HostAddr)
Write-Host ("PORT : {0}" -f $Port)
Write-Host ""

$cmd = @(
  "-m", "uvicorn",
  "app.server:app",
  "--host", $HostAddr,
  "--port", "$Port"
)

Write-Host ("CMD  : {0} {1}" -f $py, ($cmd -join " ")) -ForegroundColor DarkGray
Write-Host ""

& $py @cmd
exit $LASTEXITCODE
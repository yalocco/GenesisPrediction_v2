param(
  [Parameter(Mandatory=$false)]
  [string]$Date = ""
)

$ErrorActionPreference = "Stop"

function TodayISO {
  $d = Get-Date
  return $d.ToString("yyyy-MM-dd")
}

if ([string]::IsNullOrWhiteSpace($Date)) {
  $Date = TodayISO
}

# scripts/ 配下に置かれる前提で repo root に移動
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

Write-Output "[RUN] repo_root=$repoRoot"
Write-Output "[RUN] date=$Date"

# 1) Analyzer (Docker)
Write-Output "[STEP] analyzer: docker compose run --rm analyzer"
docker compose run --rm analyzer

# 2) Digest (HTML/MD)
$venvPy = Join-Path $repoRoot ".venv\Scripts\python.exe"
$py = $venvPy
if (!(Test-Path $py)) {
  $py = "python"
}

Write-Output "[STEP] digest: scripts/build_daily_news_digest.py --date $Date --limit 40"
& $py "scripts/build_daily_news_digest.py" --date $Date --limit 40

# 3) ViewModel (digest/view)
Write-Output "[STEP] viewmodel: scripts/build_digest_view_model.py --date $Date"
& $py "scripts/build_digest_view_model.py" --date $Date

Write-Output "[OK] daily pipeline completed for $Date"
exit 0

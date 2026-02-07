# scripts/refresh_latest_artifacts.ps1
# Refresh *_latest.json by copying the newest dated artifact that exists.
# Read-only / SST: no recalculation, only file selection + copy.

[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [string]$AnalysisDir = "data\world_politics\analysis"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-LatestDatedFile {
  param(
    [Parameter(Mandatory=$true)][string]$Dir,
    [Parameter(Mandatory=$true)][string]$Prefix
  )

  if (-not (Test-Path $Dir)) { return $null }

  $rx = "^" + [Regex]::Escape($Prefix) + "_(?<d>\d{4}-\d{2}-\d{2})\.json$"

  $candidates = Get-ChildItem -Path $Dir -File -Filter "${Prefix}_*.json" |
    ForEach-Object {
      $m = [regex]::Match($_.Name, $rx)
      if ($m.Success) {
        [pscustomobject]@{
          Path = $_.FullName
          Date = $m.Groups["d"].Value
        }
      }
    } |
    Where-Object { $_ -ne $null }

  if (-not $candidates) { return $null }

  return ($candidates | Sort-Object Date | Select-Object -Last 1)
}

function Copy-Latest {
  param(
    [Parameter(Mandatory=$true)][string]$Dir,
    [Parameter(Mandatory=$true)][string]$Prefix
  )

  $latest = Get-LatestDatedFile -Dir $Dir -Prefix $Prefix
  if ($null -eq $latest) {
    Write-Warning "No dated files found for prefix '$Prefix' in: $Dir"
    return
  }

  $src = $latest.Path
  $dst = Join-Path $Dir "${Prefix}_latest.json"

  if ($PSCmdlet.ShouldProcess($dst, "Copy from $src")) {
    Copy-Item $src $dst -Force
    Write-Host "[OK] $Prefix -> $($latest.Date)"
  }
}

Write-Host "=== Refresh latest artifacts (SST copy only) ==="
Write-Host "AnalysisDir: $AnalysisDir"
Write-Host ""

"sentiment","daily_news","daily_summary" | ForEach-Object {
  Copy-Latest -Dir $AnalysisDir -Prefix $_
}

Write-Host ""
Write-Host "Done."

param(
    [string]$date = (Get-Date -Format "yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"

$ROOT = Resolve-Path "$PSScriptRoot\.."
$LOG = "$ROOT\logs\fx_overlay_$date.log"

function Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg
    Add-Content -Path $LOG -Value $line
    Write-Host $line
}

function RunPy([string]$script, [string[]]$args) {
    Log ("PY  {0} {1}" -f $script, ($args -join " "))
    & python "$ROOT\scripts\$script" @args
    if ($LASTEXITCODE -ne 0) { throw "Python failed ($script) exit=$LASTEXITCODE" }
}

Log "START FX overlay date=$date"

try {
    RunPy "fx_remittance_overlay.py" @("--pair","jpy_thb")
    RunPy "fx_remittance_overlay.py" @("--pair","jpy_usd")

    Log "DONE FX overlay"
}
catch {
    Log ("ERROR {0}" -f $_)
    exit 1
}

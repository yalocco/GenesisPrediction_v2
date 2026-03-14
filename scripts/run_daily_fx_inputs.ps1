param(
    [string]$date = (Get-Date -Format "yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"

$ROOT = Resolve-Path "$PSScriptRoot\.."
$LOG = "$ROOT\logs\fx_inputs_$date.log"

# 明示的に .venv の Python を使用
$PY = Join-Path $ROOT ".venv\Scripts\python.exe"

function Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $msg
    Add-Content -Path $LOG -Value $line
    Write-Host $line
}

function RunPy([string]$script, [string[]]$args) {
    Log ("PY  {0} {1}" -f $script, ($args -join " "))
    & $PY "$ROOT\scripts\$script" @args
    if ($LASTEXITCODE -ne 0) { throw "Python failed ($script) exit=$LASTEXITCODE" }
}

Log "START FX inputs date=$date"

try {
    $base = @("--date", $date)

    RunPy "fx_remittance_today.py" ($base + @("--pair", "jpy_thb"))
    RunPy "fx_remittance_today.py" ($base + @("--pair", "jpy_usd"))

    #
    # ---- publish FX decision for Global Status ----
    #

    $analysis = Join-Path $ROOT "analysis"
    if (!(Test-Path $analysis)) {
        New-Item -ItemType Directory -Path $analysis | Out-Null
    }

    $fxFile = Join-Path $analysis "fx_decision_latest.json"

    $fx = @{
        as_of = $date
        regime = "neutral"
        decision = "monitor"
        source = "fx_remittance_today"
    }

    $fx | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $fxFile

    Log "publish fx_decision_latest.json"

    Log "DONE FX inputs"
}
catch {
    Log ("ERROR {0}" -f $_)
    exit 1
}
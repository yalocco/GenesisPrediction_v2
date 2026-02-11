param(
    [switch]$strict
)

$ErrorActionPreference = "Stop"

$ROOT = Resolve-Path "$PSScriptRoot\.."
$date = (Get-Date -Format "yyyy-MM-dd")
$LOG = "$ROOT\logs\fx_rates_$date.log"

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

Log "START FX rates strict=$strict"

try {
    $args = @("--pair", "both")
    if ($strict) {
        # strict=True: オンライン取得が失敗したら既存CSV継続ではなく「停止」する
        $args += "--strict"
    }

    RunPy "fx_materialize_rates.py" $args

    Log "DONE FX rates"
}
catch {
    Log ("ERROR {0}" -f $_)
    exit 1
}

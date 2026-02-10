param(
    [string]$date = (Get-Date -Format "yyyy-MM-dd"),
    [switch]$strict
)

$ErrorActionPreference = "Stop"

$ROOT = Resolve-Path "$PSScriptRoot\.."
$LOG = "$ROOT\logs\fx_inputs_$date.log"

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

Log "START FX inputs date=$date strict=$strict"

try {
    $args = @("--date", $date)
    if ($strict) { $args += "--recent"; $args += "0" }  # strict相当の挙動に寄せたい場合。不要なら削除OK

    RunPy "fx_remittance_today.py" $args

    Log "DONE FX inputs"
}
catch {
    Log ("ERROR {0}" -f $_)
    exit 1
}

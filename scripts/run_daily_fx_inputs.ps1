# scripts/run_daily_fx_inputs.ps1
# ------------------------------------------------------------
# Build FX pair dashboards (unified)
#
# Source:
#   data/fx/usdjpy.csv
#   data/fx/usdthb.csv
#
# Output:
#   data/fx/dashboard/jpy_thb_dashboard.csv
#   data/fx/dashboard/jpy_usd_dashboard.csv
#
# Notes:
# - JPY/USD = 1 / USDJPY
# - JPY/THB = USDTHB / USDJPY
# - Existing dashboard decision columns are preserved by date when possible
# - CSV header names are auto-detected
# ------------------------------------------------------------

param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $PSScriptRoot
$FX   = Join-Path $ROOT "data\fx"
$DASH = Join-Path $FX "dashboard"

$USDJPY_CSV = Join-Path $FX "usdjpy.csv"
$USDTHB_CSV = Join-Path $FX "usdthb.csv"

$JPYUSD_DASH = Join-Path $DASH "jpy_usd_dashboard.csv"
$JPYTHB_DASH = Join-Path $DASH "jpy_thb_dashboard.csv"

if (!(Test-Path $DASH)) {
    New-Item -ItemType Directory -Force -Path $DASH | Out-Null
}

Write-Host ""
Write-Host "FX Inputs Builder"
Write-Host "ROOT : $ROOT"
Write-Host "DATE : $Date"
Write-Host "FX   : $FX"
Write-Host "DASH : $DASH"
Write-Host ""

function Get-FirstExistingPropertyName {
    param(
        [Parameter(Mandatory = $true)]$Row,
        [Parameter(Mandatory = $true)][string[]]$Candidates
    )

    $names = @($Row.PSObject.Properties.Name)
    foreach ($candidate in $Candidates) {
        foreach ($name in $names) {
            if ($name -ieq $candidate) {
                return $name
            }
        }
    }
    return $null
}

function Import-FxCsv {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$RateColumnCandidates
    )

    if (!(Test-Path $Path)) {
        throw "Missing FX csv: $Path"
    }

    $rows = Import-Csv $Path
    if (-not $rows -or $rows.Count -eq 0) {
        throw "Empty FX csv: $Path"
    }

    $first = $rows[0]

    $dateCol = Get-FirstExistingPropertyName -Row $first -Candidates @(
        "date", "Date", "timestamp", "Timestamp", "time", "Time"
    )
    if (-not $dateCol) {
        throw "Date column not found in: $Path"
    }

    $rateCol = Get-FirstExistingPropertyName -Row $first -Candidates $RateColumnCandidates
    if (-not $rateCol) {
        $available = ($first.PSObject.Properties.Name -join ", ")
        throw "Rate column not found in: $Path ; available=[$available]"
    }

    $out = foreach ($row in $rows) {
        $dateValue = $row.$dateCol
        $rateValue = $row.$rateCol

        if ([string]::IsNullOrWhiteSpace([string]$dateValue)) {
            continue
        }

        $rate = 0.0
        $parsed = [double]::TryParse(
            [string]$rateValue,
            [System.Globalization.NumberStyles]::Float,
            [System.Globalization.CultureInfo]::InvariantCulture,
            [ref]$rate
        )

        if (-not $parsed) {
            continue
        }

        [PSCustomObject]@{
            date = [string]$dateValue
            rate = [double]$rate
        }
    }

    if (-not $out -or $out.Count -eq 0) {
        throw "No valid rows parsed from: $Path"
    }

    return $out | Sort-Object date
}

function Import-ExistingDashboardMap {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    $map = @{}

    if (!(Test-Path $Path)) {
        return $map
    }

    $rows = Import-Csv $Path
    foreach ($row in $rows) {
        if ([string]::IsNullOrWhiteSpace([string]$row.date)) {
            continue
        }

        $decision = if ($row.PSObject.Properties.Name -contains "combined_decision" -and $row.combined_decision) {
            [string]$row.combined_decision
        } else {
            "ON"
        }

        $noise = if ($row.PSObject.Properties.Name -contains "combined_noise_prob") {
            [string]$row.combined_noise_prob
        } else {
            ""
        }

        $note = if ($row.PSObject.Properties.Name -contains "remit_note") {
            [string]$row.remit_note
        } else {
            ""
        }

        $map[[string]$row.date] = [PSCustomObject]@{
            decision = $decision
            noise    = $noise
            note     = $note
        }
    }

    return $map
}

function Build-JpyUsdDashboard {
    param(
        [Parameter(Mandatory = $true)]$UsdJpyRows,
        [Parameter(Mandatory = $true)][string]$OutPath
    )

    $existing = Import-ExistingDashboardMap -Path $OutPath

    $out = foreach ($row in $UsdJpyRows) {
        if ($row.rate -eq 0) {
            continue
        }

        $dateKey = [string]$row.date
        $prev = $existing[$dateKey]

        [PSCustomObject]@{
            date                = $dateKey
            jpy_usd             = [double](1.0 / $row.rate)
            combined_decision   = if ($prev) { $prev.decision } else { "ON" }
            combined_noise_prob = if ($prev) { $prev.noise } else { "" }
            remit_note          = if ($prev) { $prev.note } else { "" }
        }
    }

    $out | Sort-Object date | Export-Csv $OutPath -NoTypeInformation -Encoding UTF8
    Write-Host "[OK] dashboard updated : $OutPath"
}

function Build-JpyThbDashboard {
    param(
        [Parameter(Mandatory = $true)]$UsdJpyRows,
        [Parameter(Mandatory = $true)]$UsdThbRows,
        [Parameter(Mandatory = $true)][string]$OutPath
    )

    $existing = Import-ExistingDashboardMap -Path $OutPath

    $usdjpyMap = @{}
    foreach ($row in $UsdJpyRows) {
        $usdjpyMap[[string]$row.date] = [double]$row.rate
    }

    $out = foreach ($row in $UsdThbRows) {
        $dateKey = [string]$row.date
        if (-not $usdjpyMap.ContainsKey($dateKey)) {
            continue
        }

        $usdthb = [double]$row.rate
        $usdjpy = [double]$usdjpyMap[$dateKey]

        if ($usdjpy -eq 0) {
            continue
        }

        $prev = $existing[$dateKey]

        [PSCustomObject]@{
            date                = $dateKey
            jpy_thb             = [double]($usdthb / $usdjpy)
            combined_decision   = if ($prev) { $prev.decision } else { "ON" }
            combined_noise_prob = if ($prev) { $prev.noise } else { "" }
            remit_note          = if ($prev) { $prev.note } else { "" }
        }
    }

    $out | Sort-Object date | Export-Csv $OutPath -NoTypeInformation -Encoding UTF8
    Write-Host "[OK] dashboard updated : $OutPath"
}

try {
    $usdJpyRows = Import-FxCsv -Path $USDJPY_CSV -RateColumnCandidates @(
        "usdjpy", "USDJPY", "rate", "close", "value", "price"
    )

    $usdThbRows = Import-FxCsv -Path $USDTHB_CSV -RateColumnCandidates @(
        "usdthb", "USDTHB", "rate", "close", "value", "price"
    )

    Build-JpyUsdDashboard -UsdJpyRows $usdJpyRows -OutPath $JPYUSD_DASH
    Build-JpyThbDashboard -UsdJpyRows $usdJpyRows -UsdThbRows $usdThbRows -OutPath $JPYTHB_DASH

    $usdLast = Import-Csv $JPYUSD_DASH | Select-Object -Last 1
    $thbLast = Import-Csv $JPYTHB_DASH | Select-Object -Last 1

    Write-Host ""
    Write-Host "FX dashboard build complete"
    if ($usdLast) {
        Write-Host ("  JPY/USD last : {0}  {1}" -f $usdLast.date, $usdLast.jpy_usd)
    }
    if ($thbLast) {
        Write-Host ("  JPY/THB last : {0}  {1}" -f $thbLast.date, $thbLast.jpy_thb)
    }
}
catch {
    Write-Error $_
    exit 1
}
# fx_monthly_report_gui.ps1
# Hand-operated GUI for generating monthly FX remittance reports (MD + CSV)
# Fix: Open Output Folder now reliably opens the repo's data\fx\reports folder.

Set-StrictMode -Version Latest
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Show-Error {
    param([string]$Msg)
    [System.Windows.Forms.MessageBox]::Show(
        $Msg,
        "FX Monthly Report",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
}

function Show-Info {
    param([string]$Msg)
    [System.Windows.Forms.MessageBox]::Show(
        $Msg,
        "FX Monthly Report",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    ) | Out-Null
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "FX Monthly Report (Manual)"
$form.Size = New-Object System.Drawing.Size(520,260)
$form.StartPosition = "CenterScreen"
$form.TopMost = $true

$label = New-Object System.Windows.Forms.Label
$label.Text = "Generate FX remittance monthly report (MD + CSV)."
$label.AutoSize = $true
$label.Location = New-Object System.Drawing.Point(20,20)
$form.Controls.Add($label)

$label2 = New-Object System.Windows.Forms.Label
$label2.Text = "Output: data\fx\reports\YYYY-MM.*"
$label2.AutoSize = $true
$label2.Location = New-Object System.Drawing.Point(20,45)
$form.Controls.Add($label2)

$monthLabel = New-Object System.Windows.Forms.Label
$monthLabel.Text = "Month (optional, YYYY-MM):"
$monthLabel.AutoSize = $true
$monthLabel.Location = New-Object System.Drawing.Point(20,80)
$form.Controls.Add($monthLabel)

$monthBox = New-Object System.Windows.Forms.TextBox
$monthBox.Size = New-Object System.Drawing.Size(120,24)
$monthBox.Location = New-Object System.Drawing.Point(220,77)
$form.Controls.Add($monthBox)

$btnPrev = New-Object System.Windows.Forms.Button
$btnPrev.Text = "Generate Previous Month"
$btnPrev.Size = New-Object System.Drawing.Size(220,40)
$btnPrev.Location = New-Object System.Drawing.Point(20,120)
$form.Controls.Add($btnPrev)

$btnMonth = New-Object System.Windows.Forms.Button
$btnMonth.Text = "Generate Specified Month"
$btnMonth.Size = New-Object System.Drawing.Size(220,40)
$btnMonth.Location = New-Object System.Drawing.Point(260,120)
$form.Controls.Add($btnMonth)

$status = New-Object System.Windows.Forms.Label
$status.Text = "Idle"
$status.AutoSize = $true
$status.Location = New-Object System.Drawing.Point(20,185)
$form.Controls.Add($status)

$btnOpen = New-Object System.Windows.Forms.Button
$btnOpen.Text = "Open Output Folder"
$btnOpen.Size = New-Object System.Drawing.Size(220,30)
$btnOpen.Location = New-Object System.Drawing.Point(260,182)
$form.Controls.Add($btnOpen)

function Invoke-Report {
    param([string]$Month)

    try {
        $status.Text = "Running: $Month"
        $form.Refresh()

        $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
        Set-Location $repoRoot

        $py = Join-Path $repoRoot ".venv\Scripts\python.exe"
        if (!(Test-Path $py)) {
            throw "Python not found: $py"
        }

        $scriptPath = Join-Path $repoRoot "scripts\fx_remittance_monthly_report.py"
        if (!(Test-Path $scriptPath)) {
            throw "Report script not found: $scriptPath"
        }

        & $py $scriptPath --month $Month
        if ($LASTEXITCODE -ne 0) {
            throw "Python exited with code $LASTEXITCODE"
        }

        $status.Text = "Completed: $Month"
        Show-Info "Completed: $Month"
    }
    catch {
        $status.Text = "Error"
        Show-Error $_.Exception.Message
    }
}

$btnPrev.Add_Click({
    $m = (Get-Date).AddMonths(-1).ToString("yyyy-MM")
    Invoke-Report $m
})

$btnMonth.Add_Click({
    $m = $monthBox.Text.Trim()
    if ($m -eq "") {
        Show-Error "Please enter month in YYYY-MM format."
        return
    }
    if ($m.Length -ne 7 -or $m[4] -ne '-') {
        Show-Error "Invalid format. Use YYYY-MM (e.g. 2026-01)."
        return
    }
    Invoke-Report $m
})

$btnOpen.Add_Click({
    try {
        $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
        $outDir = Join-Path $repoRoot "data\fx\reports"

        if (!(Test-Path $outDir)) {
            throw "Output folder not found: $outDir"
        }

        # Reliable: pass the folder path as an argument explicitly (quoted)
        Start-Process -FilePath "explorer.exe" -ArgumentList @("`"$outDir`"") | Out-Null
        # Alternative (also works): Invoke-Item $outDir
    }
    catch {
        Show-Error $_.Exception.Message
    }
})

# NOTE: This is the correct way to ignore the return value in PowerShell.
$form.ShowDialog() | Out-Null

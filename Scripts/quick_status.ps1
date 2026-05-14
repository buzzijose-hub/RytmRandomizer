$ErrorActionPreference = "Continue"

$script:quickStatusFailures = 0

function Register-QuickStatusStepExit {
    param(
        [Parameter(Mandatory=$true)]
        [string]$StepName
    )

    if ($LASTEXITCODE -ne 0) {
        $script:quickStatusFailures += 1
        Write-Output "FAILED: $StepName exited with code $LASTEXITCODE"
    }
}

$venvPython = ".\.venv\Scripts\python.exe"
$codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$pythonExe = $null
$pythonArgs = @()

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
    $pythonArgs = @("-3")
} elseif (Test-Path $codexPython) {
    $pythonExe = $codexPython
}

if (-not $pythonExe) {
    Write-Output "No Python command found. Tried .\.venv\Scripts\python.exe, python, py -3, and the bundled Codex runtime."
    exit 1
}

Write-Output "=== Project Status Summary ==="
& $pythonExe @pythonArgs -m rytm_randomizer.cli project-status-report --summary
Register-QuickStatusStepExit "Project Status Summary"

Write-Output ""
Write-Output "=== Project Status Check ==="
& $pythonExe @pythonArgs -m rytm_randomizer.cli project-status-report --check
Register-QuickStatusStepExit "Project Status Check"

Write-Output ""
Write-Output "=== Git Status ==="
git status --short
Register-QuickStatusStepExit "Git Status"

if ($script:quickStatusFailures -gt 0) {
    Write-Output ""
    Write-Output "Quick status failed. Failed step count: $script:quickStatusFailures"
    exit 1
}

exit 0

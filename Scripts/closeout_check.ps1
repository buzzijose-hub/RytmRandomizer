$ErrorActionPreference = "Continue"

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logDir = ".\Docs\Session_Logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$summary = "$logDir\latest_closeout_summary.txt"

$venvPython = ".\.venv\Scripts\python.exe"
$codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$pythonExe = $null
$pythonArgs = @()
$pythonLabel = $null

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
    $pythonLabel = $venvPython
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
    $pythonLabel = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
    $pythonArgs = @("-3")
    $pythonLabel = "py -3"
} elseif (Test-Path $codexPython) {
    $pythonExe = $codexPython
    $pythonLabel = $codexPython
}

"RytmRandomizer Closeout Summary" | Set-Content $summary
"Timestamp: $timestamp" | Add-Content $summary
"" | Add-Content $summary

"=== Python Command ===" | Add-Content $summary
if ($pythonExe) {
    "Using: $pythonLabel" | Add-Content $summary
} else {
    "No Python command found. Tried .\.venv\Scripts\python.exe, python, py -3, and the bundled Codex runtime." | Add-Content $summary
    Get-Content $summary
    exit 1
}

"=== Git Branch ===" | Add-Content $summary
git branch --show-current 2>&1 | Tee-Object -FilePath "$logDir\latest_git_branch.log" | Add-Content $summary

"" | Add-Content $summary
"=== Git Log Latest 12 ===" | Add-Content $summary
git log --oneline --decorate -12 2>&1 | Tee-Object -FilePath "$logDir\latest_git_log.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Scaffold ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_scaffold.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_scaffold.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Validation ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_validation.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_validation.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Inspection ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_inspection.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_inspection.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Preview ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_preview.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_preview.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Audit ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_audit.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_audit.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Profile Lookup ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_profile_lookup.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_profile_lookup.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Scene Lookup ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_scene_lookup.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_scene_lookup.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Command Lookup ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_command_lookup.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_command_lookup.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Registry ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_registry.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_registry.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Registry Report ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_registry_report.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_registry_report.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Registry Report CLI ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_registry_report_cli.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_registry_report_cli.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Passive CLI ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_cli.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_cli.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Mock MIDI ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_mock_midi.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_mock_midi.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Mock Message Mapper ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_mock_message_mapper.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_mock_message_mapper.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Mock Mapper Report ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_mock_mapper_report.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_mock_mapper_report.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Mock-Only Active Candidate ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_mock_only_active_candidate.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_mock_only_active_candidate.log" | Add-Content $summary

"" | Add-Content $summary
"=== V1.34 Reference Diff ===" | Add-Content $summary
git diff -- rytm_hybrid_randomizer_v134.py 2>&1 | Tee-Object -FilePath "$logDir\latest_v134_reference_diff.log" | Add-Content $summary

"" | Add-Content $summary
"=== Git Status ===" | Add-Content $summary
git status --short 2>&1 | Tee-Object -FilePath "$logDir\latest_git_status.log" | Add-Content $summary

"" | Add-Content $summary
"Closeout complete. Review: Docs\Session_Logs\latest_closeout_summary.txt" | Add-Content $summary

Get-Content $summary

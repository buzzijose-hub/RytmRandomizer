$ErrorActionPreference = "Continue"

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logDir = ".\Docs\Session_Logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$summary = "$logDir\latest_closeout_summary.txt"

"RytmRandomizer Closeout Summary" | Set-Content $summary
"Timestamp: $timestamp" | Add-Content $summary
"" | Add-Content $summary

"=== Git Branch ===" | Add-Content $summary
git branch --show-current 2>&1 | Tee-Object -FilePath "$logDir\latest_git_branch.log" | Add-Content $summary

"" | Add-Content $summary
"=== Git Log Latest 12 ===" | Add-Content $summary
git log --oneline --decorate -12 2>&1 | Tee-Object -FilePath "$logDir\latest_git_log.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Scaffold ===" | Add-Content $summary
python .\tests\test_scaffold.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_scaffold.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Validation ===" | Add-Content $summary
python .\tests\test_validation.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_validation.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Inspection ===" | Add-Content $summary
python .\tests\test_inspection.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_inspection.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Preview ===" | Add-Content $summary
python .\tests\test_preview.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_preview.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Audit ===" | Add-Content $summary
python .\tests\test_audit.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_audit.log" | Add-Content $summary

"" | Add-Content $summary
"=== V1.34 Reference Diff ===" | Add-Content $summary
git diff -- rytm_hybrid_randomizer_v134.py 2>&1 | Tee-Object -FilePath "$logDir\latest_v134_reference_diff.log" | Add-Content $summary

"" | Add-Content $summary
"=== Git Status ===" | Add-Content $summary
git status --short 2>&1 | Tee-Object -FilePath "$logDir\latest_git_status.log" | Add-Content $summary

"" | Add-Content $summary
"Closeout complete. Review: Docs\Session_Logs\latest_closeout_summary.txt" | Add-Content $summary

Get-Content $summary

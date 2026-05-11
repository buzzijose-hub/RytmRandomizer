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
"=== Test: Behavior Menu Utility ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_menu_utility.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_menu_utility.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Anchor Profile ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_anchor_profile.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_anchor_profile.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Anchor Profile Report ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_anchor_profile_report.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_anchor_profile_report.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Mutation Depth ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_mutation_depth.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_mutation_depth.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Scene Group ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_scene_group.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_scene_group.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Pad 1 Lane ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_pad1_lane.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_pad1_lane.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Pad 2 Lane ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_pad2_lane.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_pad2_lane.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Pad 3 Lane ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_pad3_lane.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_pad3_lane.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Pad 4 Lane ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_pad4_lane.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_pad4_lane.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Undo Commit State ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_undo_commit_state.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_undo_commit_state.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Selected Profile ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_selected_profile.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_selected_profile.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Behavior Selected Isolated Pad ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_behavior_selected_isolated_pad.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_behavior_selected_isolated_pad.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Selected Target State ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_selected_target_state.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_selected_target_state.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Anchor State ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_anchor_state.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_anchor_state.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Selected Isolated Pad Runtime State ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_selected_isolated_pad_runtime_state.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_selected_isolated_pad_runtime_state.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Runtime-Adjacent Mock-Only PZ ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_runtime_adjacent_mock_only_pz.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_runtime_adjacent_mock_only_pz.log" | Add-Content $summary

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
"=== Test: Active Boundary ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_active_boundary.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_active_boundary.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Active Boundary Report ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_active_boundary_report.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_active_boundary_report.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Real MIDI Import Safety ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_real_midi_import_safety.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_real_midi_import_safety.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Real MIDI Passive CLI Safety ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_real_midi_passive_cli_safety.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_real_midi_passive_cli_safety.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Real MIDI Adapter Boundary ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_real_midi_adapter_boundary.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_real_midi_adapter_boundary.log" | Add-Content $summary

"" | Add-Content $summary
"=== V1.34 Reference Diff ===" | Add-Content $summary
git diff -- rytm_hybrid_randomizer_v134.py 2>&1 | Tee-Object -FilePath "$logDir\latest_v134_reference_diff.log" | Add-Content $summary

"" | Add-Content $summary
"=== Git Status ===" | Add-Content $summary
git status --short 2>&1 | Tee-Object -FilePath "$logDir\latest_git_status.log" | Add-Content $summary

"" | Add-Content $summary
"Closeout complete. Review: Docs\Session_Logs\latest_closeout_summary.txt" | Add-Content $summary

Get-Content $summary

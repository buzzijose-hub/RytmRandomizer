# Collaborator Branch Watch Status Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface the existing passive collaborator branch-watch report in quick status and cross-platform closeout.

**Architecture:** Keep the branch-watch report itself unchanged. Add one passive CLI call to `Scripts/quick_status.ps1` and one passive CLI step to `Scripts/closeout_check.py`, then document the alignment checkpoint. This stays local/read-only and does not query GitHub, check out branches, merge branches, trigger Actions, send MIDI, open ports, or touch hardware.

**Tech Stack:** PowerShell, Python standard library, pytest, existing passive CLI.

---

### Task 1: Add Failing Quick Status And Closeout Contract Expectations

**Files:**
- Modify: `tests/test_quick_status_script.py`
- Modify: `tests/test_closeout_contract.py`

- [x] **Step 1: Add quick-status expectations**

Require `Scripts/quick_status.ps1` to include:

```text
=== Collaborator Branch Watch ===
python -m rytm_randomizer.cli collaborator-branch-watch
Register-QuickStatusStepExit "Collaborator Branch Watch"
```

- [x] **Step 2: Add cross-platform closeout expectations**

Require `Scripts/closeout_check.py` to include:

```text
Collaborator Branch Watch
python -m rytm_randomizer.cli collaborator-branch-watch
```

- [x] **Step 3: Verify red**

Run:

```powershell
pytest tests/test_quick_status_script.py tests/test_closeout_contract.py
```

Expected: fails because the helper scripts do not yet surface the branch-watch report.

### Task 2: Add Passive Report Calls

**Files:**
- Modify: `Scripts/quick_status.ps1`
- Modify: `Scripts/closeout_check.py`

- [x] **Step 1: Add quick-status section**

Insert after `Project Status Check`:

```powershell
Write-Output ""
Write-Output "=== Collaborator Branch Watch ==="
& $pythonExe @pythonArgs -m rytm_randomizer.cli collaborator-branch-watch
Register-QuickStatusStepExit "Collaborator Branch Watch"
```

- [x] **Step 2: Add cross-platform closeout step**

Insert after `Project Status Check`:

```python
(
    "Collaborator Branch Watch",
    [
        sys.executable,
        "-m",
        "rytm_randomizer.cli",
        "collaborator-branch-watch",
    ],
    "python -m rytm_randomizer.cli collaborator-branch-watch",
),
```

- [x] **Step 3: Verify green**

Run:

```powershell
pytest tests/test_quick_status_script.py tests/test_closeout_contract.py
```

Expected: all tests pass.

### Task 3: Document And Verify

**Files:**
- Create: `Docs/COLLABORATOR_BRANCH_WATCH_STATUS_ALIGNMENT_CHECKPOINT.md`
- Modify: `Docs/NEXT_ACTION.md`
- Modify: `Docs/PROJECT_CHECKPOINT_CURRENT.md`
- Modify: `Docs/PASSIVE_ARCHITECTURE_SUMMARY.md`

- [x] **Step 1: Document the checkpoint**

Record:

- quick status now includes `Collaborator Branch Watch`
- cross-platform closeout now includes `Collaborator Branch Watch`
- Windows closeout already includes the report test
- no GitHub mutation, no Actions trigger, no branch checkout/merge
- no real MIDI, ports, active behavior, or hardware

- [x] **Step 2: Run verification**

Run:

```powershell
git diff --check
pytest tests/test_quick_status_script.py tests/test_closeout_contract.py tests/test_collaborator_branch_watch_report.py tests/test_cli.py
python .\Scripts\closeout_check.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [x] **Step 3: Commit and push**

Run:

```powershell
git add .\Docs\COLLABORATOR_BRANCH_WATCH_STATUS_ALIGNMENT_CHECKPOINT.md `
        .\Docs\NEXT_ACTION.md `
        .\Docs\PROJECT_CHECKPOINT_CURRENT.md `
        .\Docs\PASSIVE_ARCHITECTURE_SUMMARY.md `
        .\Docs\superpowers\plans\2026-05-14-collaborator-branch-watch-status-alignment.md `
        .\Scripts\quick_status.ps1 `
        .\Scripts\closeout_check.py `
        .\tests\test_quick_status_script.py `
        .\tests\test_closeout_contract.py

git commit -m "Add collaborator branch watch to status helpers"
git push origin codex/execute-eddie-plan
```

- [x] **Step 4: Confirm no automatic Actions run**

Run:

```powershell
gh run list --repo buzzijose-hub/RytmRandomizer --branch codex/execute-eddie-plan --limit 8 --json databaseId,event,status,conclusion,headSha,name,createdAt
```

Expected: no automatic run for the new commit.

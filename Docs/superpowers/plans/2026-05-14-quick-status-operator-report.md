# Quick Status Operator Report Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the passive `operator-status-report` output to the local quick-status helper.

**Architecture:** Keep `Scripts/quick_status.ps1` as the fast local no-cost operator check. Add one read-only section that calls the existing passive CLI formatter through `python -m rytm_randomizer.cli operator-status-report`, then register the step with the existing failure counter. No GitHub API calls, no Actions trigger, no MIDI, no ports, no active behavior, and no hardware.

**Tech Stack:** PowerShell, Python passive CLI, pytest, existing closeout.

---

### Task 1: Add Quick Status Test Expectations

**Files:**
- Modify: `tests/test_quick_status_script.py`

- [ ] **Step 1: Add failing static expectations**

Update `test_quick_status_script_exists_and_stays_passive()` so it requires:

```python
assert "operator-status-report" in text
assert "=== Operator Status Report ===" in text
assert 'Register-QuickStatusStepExit "Operator Status Report"' in text
```

- [ ] **Step 2: Add failing execution expectations**

Update `test_quick_status_script_runs_passive_status_checks()` so it requires:

```python
assert "=== Operator Status Report ===" in result.stdout
assert "RytmRandomizer Operator Status Report" in result.stdout
assert "- daily_feedback: local_closeout" in result.stdout
assert "- no_pay_policy: True" in result.stdout
```

- [ ] **Step 3: Verify red**

Run:

```powershell
pytest tests/test_quick_status_script.py
```

Expected: fails because `Scripts/quick_status.ps1` does not yet include the operator status section.

### Task 2: Wire Existing Passive Operator Report Into Quick Status

**Files:**
- Modify: `Scripts/quick_status.ps1`

- [ ] **Step 1: Add the new passive section**

Insert after the project status check:

```powershell
Write-Output ""
Write-Output "=== Operator Status Report ==="
& $pythonExe @pythonArgs -m rytm_randomizer.cli operator-status-report
Register-QuickStatusStepExit "Operator Status Report"
```

- [ ] **Step 2: Verify green**

Run:

```powershell
pytest tests/test_quick_status_script.py
```

Expected: all quick-status tests pass.

### Task 3: Document And Verify

**Files:**
- Create: `Docs/QUICK_STATUS_OPERATOR_REPORT_CHECKPOINT.md`
- Modify: `Docs/NEXT_ACTION.md`
- Modify: `Docs/PROJECT_CHECKPOINT_CURRENT.md`
- Modify: `Docs/PASSIVE_ARCHITECTURE_SUMMARY.md`

- [ ] **Step 1: Add docs checkpoint**

Document:

- `Scripts/quick_status.ps1` now includes `=== Operator Status Report ===`
- the quick helper remains local and no-cost
- no GitHub mutation, no Actions trigger, no real MIDI, no ports, no active behavior, no hardware
- next recommended task remains waiting for Eddie's implementation branch or PR

- [ ] **Step 2: Run verification**

Run:

```powershell
git diff --check
pytest tests/test_quick_status_script.py tests/test_operator_status_report.py tests/test_cli.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [ ] **Step 3: Commit and push**

Run:

```powershell
git add .\Docs\QUICK_STATUS_OPERATOR_REPORT_CHECKPOINT.md `
        .\Docs\NEXT_ACTION.md `
        .\Docs\PROJECT_CHECKPOINT_CURRENT.md `
        .\Docs\PASSIVE_ARCHITECTURE_SUMMARY.md `
        .\Docs\superpowers\plans\2026-05-14-quick-status-operator-report.md `
        .\Scripts\quick_status.ps1 `
        .\tests\test_quick_status_script.py

git commit -m "Add operator status to quick status"
git push origin codex/execute-eddie-plan
```

- [ ] **Step 4: Confirm manual Actions gate**

Run:

```powershell
gh run list --repo buzzijose-hub/RytmRandomizer --branch codex/execute-eddie-plan --limit 8 --json databaseId,event,status,conclusion,headSha,name,createdAt
```

Expected: no automatic run for the new commit.

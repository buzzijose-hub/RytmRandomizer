# Cross-Platform Operator Status Closeout Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the passive operator status report to the cross-platform closeout script.

**Architecture:** Keep `Scripts/closeout_check.py` as the OS-portable closeout runner. Add one passive command step after `Project Status Check` that runs `python -m rytm_randomizer.cli operator-status-report`. This improves parity with Windows closeout and quick status without adding GitHub calls, Actions triggers, MIDI, ports, active execution, or hardware behavior.

**Tech Stack:** Python standard library, pytest, existing passive CLI.

---

### Task 1: Add Failing Closeout Contract Expectations

**Files:**
- Modify: `tests/test_closeout_contract.py`

- [x] **Step 1: Add cross-platform operator status expectations**

Update `test_cross_platform_closeout_script_exists_and_runs_core_gates()` so it requires:

```python
assert "Operator Status Report" in script
assert "operator-status-report" in script
assert "python -m rytm_randomizer.cli operator-status-report" in script
```

- [x] **Step 2: Verify red**

Run:

```powershell
pytest tests/test_closeout_contract.py
```

Expected: fails because `Scripts/closeout_check.py` does not yet include the operator status step.

### Task 2: Add Operator Status To Cross-Platform Closeout

**Files:**
- Modify: `Scripts/closeout_check.py`

- [x] **Step 1: Add the passive CLI step**

Insert after the existing `Project Status Check` step:

```python
(
    "Operator Status Report",
    [
        sys.executable,
        "-m",
        "rytm_randomizer.cli",
        "operator-status-report",
    ],
    "python -m rytm_randomizer.cli operator-status-report",
),
```

- [x] **Step 2: Verify green**

Run:

```powershell
pytest tests/test_closeout_contract.py
```

Expected: all closeout contract tests pass.

### Task 3: Document And Verify

**Files:**
- Create: `Docs/CROSS_PLATFORM_OPERATOR_STATUS_CLOSEOUT_CHECKPOINT.md`
- Modify: `Docs/NEXT_ACTION.md`
- Modify: `Docs/PROJECT_CHECKPOINT_CURRENT.md`
- Modify: `Docs/PASSIVE_ARCHITECTURE_SUMMARY.md`

- [x] **Step 1: Document the checkpoint**

Record:

- `Scripts/closeout_check.py` now includes `Operator Status Report`
- the step runs `python -m rytm_randomizer.cli operator-status-report`
- Windows closeout, quick status, and cross-platform closeout now all expose operator status visibility
- no GitHub mutation, no Actions trigger, no real MIDI, no ports, no active behavior, no hardware

- [x] **Step 2: Run verification**

Run:

```powershell
git diff --check
pytest tests/test_closeout_contract.py tests/test_operator_status_report.py tests/test_cli.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [x] **Step 3: Commit and push**

Run:

```powershell
git add .\Docs\CROSS_PLATFORM_OPERATOR_STATUS_CLOSEOUT_CHECKPOINT.md `
        .\Docs\NEXT_ACTION.md `
        .\Docs\PROJECT_CHECKPOINT_CURRENT.md `
        .\Docs\PASSIVE_ARCHITECTURE_SUMMARY.md `
        .\Docs\superpowers\plans\2026-05-14-cross-platform-operator-status-closeout.md `
        .\Scripts\closeout_check.py `
        .\tests\test_closeout_contract.py

git commit -m "Add operator status to cross-platform closeout"
git push origin codex/execute-eddie-plan
```

- [x] **Step 4: Confirm no automatic Actions run**

Run:

```powershell
gh run list --repo buzzijose-hub/RytmRandomizer --branch codex/execute-eddie-plan --limit 8 --json databaseId,event,status,conclusion,headSha,name,createdAt
```

Expected: no automatic run for the new commit.

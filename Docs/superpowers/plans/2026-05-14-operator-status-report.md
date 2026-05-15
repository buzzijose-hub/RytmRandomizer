# Operator Status Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive `operator-status-report` command that summarizes the current safe daily project state in one place.

**Architecture:** Create a focused read-only report module that composes existing passive summaries and static safety policy. Expose it through the existing passive CLI and project-status visibility list, with fixture-backed tests and closeout coverage.

**Tech Stack:** Python standard library, pytest, existing `rytm_randomizer` passive report modules, PowerShell closeout.

---

### Task 1: Add Passive Operator Status Report

**Files:**
- Create: `rytm_randomizer/operator_status_report.py`
- Test: `tests/test_operator_status_report.py`

- [ ] **Step 1: Write failing tests**

Add tests proving:

- importing the module prints nothing
- `build_operator_status_report()` returns deterministic in-memory data
- the report summarizes project status, collaborator intake readiness, manual Actions policy, next recommended move, and safety
- `summarize_operator_status_report()` returns a compact summary
- `format_operator_status_report()` returns deterministic human-readable lines
- returned data is copied and mutation-safe
- no real MIDI libraries are imported
- no active behavior names are exposed

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest tests/test_operator_status_report.py
```

Expected: fails because `rytm_randomizer.operator_status_report` does not exist.

- [ ] **Step 3: Implement the passive report**

Create `rytm_randomizer/operator_status_report.py` using existing passive summaries from:

- `rytm_randomizer.project_status_report`
- `rytm_randomizer.collaborator_intake_readiness_report`

No GitHub calls, no file writes, no MIDI imports, no active behavior.

- [ ] **Step 4: Run focused tests**

Run:

```powershell
pytest tests/test_operator_status_report.py
```

Expected: all tests pass.

### Task 2: Expose Passive CLI Command

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `tests/test_cli.py`
- Create: `tests/fixtures/cli_operator_status_report_expected.txt`
- Create: `tests/fixtures/cli_operator_status_report_help_expected.txt`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Write failing CLI tests and fixtures**

Add fixture-backed tests for:

- `python -m rytm_randomizer.cli operator-status-report`
- `python -m rytm_randomizer.cli operator-status-report --help`
- deterministic repeated output
- no real MIDI library imports
- unknown arguments fail safely

- [ ] **Step 2: Run targeted CLI tests to verify failure**

Run targeted tests for the new command.

Expected: fail because the CLI does not know the command yet.

- [ ] **Step 3: Wire command to passive formatter only**

Add a CLI branch that imports and calls only:

```python
format_operator_status_report()
```

- [ ] **Step 4: Run CLI tests**

Run:

```powershell
pytest tests/test_cli.py
```

Expected: all CLI tests pass.

### Task 3: Update Project Status Visibility And Closeout

**Files:**
- Modify: `rytm_randomizer/project_status_report.py`
- Modify: `tests/test_project_status_report.py`
- Modify: `tests/fixtures/cli_project_status_report_expected.txt`
- Modify: `tests/fixtures/cli_project_status_report_summary_expected.txt`
- Modify: `Scripts/closeout_check.ps1`
- Modify: `tests/test_closeout_contract.py`

- [ ] **Step 1: Add failing expectations**

Update tests so `operator-status-report` is included in the passive command list and command count.

Add a closeout-contract test for:

```text
=== Test: Operator Status Report ===
```

- [ ] **Step 2: Run tests to verify failure**

Run the targeted project-status and closeout-contract tests.

Expected: fail because implementation has not been updated yet.

- [ ] **Step 3: Implement visibility and closeout step**

Add `operator-status-report` to `PASSIVE_CLI_COMMANDS` and add the closeout step for `tests/test_operator_status_report.py`.

- [ ] **Step 4: Run focused tests**

Run:

```powershell
pytest tests/test_operator_status_report.py tests/test_cli.py tests/test_project_status_report.py tests/test_closeout_contract.py
```

Expected: all pass.

### Task 4: Document And Verify

**Files:**
- Create: `Docs/OPERATOR_STATUS_REPORT_CHECKPOINT.md`
- Modify: `Docs/NEXT_ACTION.md`
- Modify: `Docs/PROJECT_CHECKPOINT_CURRENT.md`
- Modify: `Docs/PASSIVE_ARCHITECTURE_SUMMARY.md`

- [ ] **Step 1: Add docs checkpoint**

Document the new passive operator status report, command, closeout label, and safety boundaries.

- [ ] **Step 2: Run full verification**

Run:

```powershell
git diff --check
pytest tests/test_operator_status_report.py tests/test_cli.py tests/test_project_status_report.py tests/test_closeout_contract.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [ ] **Step 3: Commit and push**

Commit message:

```text
Add passive operator status report
```

Push branch:

```powershell
git push origin codex/execute-eddie-plan
```

- [ ] **Step 4: Confirm no automatic Actions run**

Run:

```powershell
gh run list --repo buzzijose-hub/RytmRandomizer --branch codex/execute-eddie-plan --limit 8 --json databaseId,event,status,conclusion,headSha,name,createdAt
```

Expected: no run for the new commit because Actions are manual-only.

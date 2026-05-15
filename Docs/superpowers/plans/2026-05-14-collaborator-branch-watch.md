# Collaborator Branch Watch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive collaborator branch-watch report and CLI command so the owner can see the current collaborator wait-state without triggering GitHub Actions or merging anything.

**Architecture:** Follow the existing passive report pattern. Add an in-memory report module with deterministic branch/PR snapshot data, expose it through `python -m rytm_randomizer.cli collaborator-branch-watch`, add fixture-backed CLI tests, include it in project/operator status, and add Windows closeout coverage. The command will not query GitHub, run `git`, trigger Actions, open ports, send MIDI, or touch hardware.

**Tech Stack:** Python standard library, pytest, existing passive CLI, existing closeout scripts.

---

### Task 1: Add Failing Report Tests

**Files:**
- Create: `tests/test_collaborator_branch_watch_report.py`

- [x] **Step 1: Write tests for passive branch-watch data**

Require:

- import prints nothing
- report title/status are deterministic
- known remote branches are listed
- known PRs are listed
- no implementation branch/PR is observed
- scan commands are informational only
- GitHub Actions policy is manual-only/no-pay
- safety boundaries stay passive
- returned data is mutation-safe
- no real MIDI libraries are imported
- no active behavior names are exposed
- explicit public API is declared

- [x] **Step 2: Verify red**

Run:

```powershell
pytest tests/test_collaborator_branch_watch_report.py
```

Expected: fails because `rytm_randomizer.collaborator_branch_watch_report` does not exist yet.

### Task 2: Implement Passive Branch-Watch Report

**Files:**
- Create: `rytm_randomizer/collaborator_branch_watch_report.py`

- [x] **Step 1: Implement copied in-memory report data**

Add:

- `COLLABORATOR_BRANCH_WATCH_SAFETY`
- `build_collaborator_branch_watch_report()`
- `summarize_collaborator_branch_watch_report()`
- `format_collaborator_branch_watch_report()`

- [x] **Step 2: Verify green**

Run:

```powershell
pytest tests/test_collaborator_branch_watch_report.py
```

Expected: all tests pass.

### Task 3: Add Passive CLI Command

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Create: `tests/fixtures/cli_collaborator_branch_watch_help_expected.txt`
- Create: `tests/fixtures/cli_collaborator_branch_watch_expected.txt`

- [x] **Step 1: Add CLI tests first**

Require:

- top-level help lists `collaborator-branch-watch`
- command help matches fixture
- command output matches fixture
- command output is deterministic
- unknown options fail safely
- command imports no real MIDI libraries

- [x] **Step 2: Verify red**

Run:

```powershell
pytest tests/test_cli.py
```

Expected: fails because the command is not wired yet.

- [x] **Step 3: Wire CLI to formatter only**

Add help text and command dispatch that imports only:

```python
from .collaborator_branch_watch_report import format_collaborator_branch_watch_report
```

- [x] **Step 4: Verify green**

Run:

```powershell
pytest tests/test_cli.py
```

Expected: all CLI tests pass.

### Task 4: Update Status Reports And Closeout

**Files:**
- Modify: `rytm_randomizer/project_status_report.py`
- Modify: `rytm_randomizer/operator_status_report.py`
- Modify: `tests/test_project_status_report.py`
- Modify: `tests/test_operator_status_report.py`
- Modify: `tests/fixtures/cli_project_status_report_expected.txt`
- Modify: `tests/fixtures/cli_project_status_report_summary_expected.txt`
- Modify: `tests/fixtures/cli_operator_status_report_expected.txt`
- Modify: `Scripts/closeout_check.ps1`
- Modify: `tests/test_closeout_contract.py`

- [x] **Step 1: Update status expectations first**

Require passive CLI command count `23` and include `collaborator-branch-watch`.

- [x] **Step 2: Update implementation**

Add the command to project status and operator command visibility.

- [x] **Step 3: Add Windows closeout label**

Add:

```text
=== Test: Collaborator Branch Watch Report ===
```

Run:

```powershell
pytest tests/test_project_status_report.py tests/test_operator_status_report.py tests/test_closeout_contract.py
```

Expected: all pass.

### Task 5: Document And Verify

**Files:**
- Create: `Docs/COLLABORATOR_BRANCH_WATCH_CHECKPOINT.md`
- Modify: `Docs/NEXT_ACTION.md`
- Modify: `Docs/PROJECT_CHECKPOINT_CURRENT.md`
- Modify: `Docs/PASSIVE_ARCHITECTURE_SUMMARY.md`

- [x] **Step 1: Document the checkpoint**

Record:

- new passive module and CLI command
- current remote snapshot still has no Eddie implementation branch
- current PR list still has PR #1 and PR #2 only
- no GitHub mutation, no Actions trigger, no merge
- no real MIDI, ports, active behavior, or hardware

- [x] **Step 2: Run verification**

Run:

```powershell
git diff --check
pytest tests/test_collaborator_branch_watch_report.py tests/test_cli.py tests/test_project_status_report.py tests/test_operator_status_report.py tests/test_closeout_contract.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [ ] **Step 3: Commit and push**

Run:

```powershell
git add .\Docs\COLLABORATOR_BRANCH_WATCH_CHECKPOINT.md `
        .\Docs\NEXT_ACTION.md `
        .\Docs\PROJECT_CHECKPOINT_CURRENT.md `
        .\Docs\PASSIVE_ARCHITECTURE_SUMMARY.md `
        .\Docs\superpowers\plans\2026-05-14-collaborator-branch-watch.md `
        .\Scripts\closeout_check.ps1 `
        .\rytm_randomizer\collaborator_branch_watch_report.py `
        .\rytm_randomizer\cli.py `
        .\rytm_randomizer\operator_status_report.py `
        .\rytm_randomizer\project_status_report.py `
        .\tests\fixtures\cli_collaborator_branch_watch_expected.txt `
        .\tests\fixtures\cli_collaborator_branch_watch_help_expected.txt `
        .\tests\fixtures\cli_help_expected.txt `
        .\tests\fixtures\cli_operator_status_report_expected.txt `
        .\tests\fixtures\cli_project_status_report_expected.txt `
        .\tests\fixtures\cli_project_status_report_summary_expected.txt `
        .\tests\test_cli.py `
        .\tests\test_closeout_contract.py `
        .\tests\test_collaborator_branch_watch_report.py `
        .\tests\test_operator_status_report.py `
        .\tests\test_project_status_report.py

git commit -m "Add passive collaborator branch watch"
git push origin codex/execute-eddie-plan
```

- [ ] **Step 4: Confirm no automatic Actions run**

Run:

```powershell
gh run list --repo buzzijose-hub/RytmRandomizer --branch codex/execute-eddie-plan --limit 8 --json databaseId,event,status,conclusion,headSha,name,createdAt
```

Expected: no automatic run for the new commit.

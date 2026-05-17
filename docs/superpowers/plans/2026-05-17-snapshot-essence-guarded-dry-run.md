# Snapshot Essence Guarded Dry-Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mock-only guarded dry-run sender for the 12-pad Rytm snapshot essence send plan.

**Architecture:** Create a focused guard module that consumes `SnapshotEssenceSendPlan`, refuses unsafe states, and emits eligible events only into `MockMidiSender`. Wire it into the passive CLI as a dry-run report; no real MIDI sender or port access is introduced in this slice.

**Tech Stack:** Python dataclasses, existing `SnapshotEssenceSendPlan`, `MockMidiSender`, passive CLI dispatch, pytest.

---

## File Structure

- Create `rytm_randomizer/snapshot_essence_guarded_sender.py`: result dataclass, guard executor, CLI report formatter, error formatter.
- Modify `rytm_randomizer/cli.py`: add passive guarded dry-run report dispatch.
- Modify `rytm_randomizer/help_text.py`: add usage/help entry.
- Modify `tests/test_cli.py` and `tests/fixtures/cli_help_expected.txt`: update exact help fixtures.
- Create `tests/test_snapshot_essence_guarded_sender.py`: guard behavior and CLI tests.
- Add this spec and plan.

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_snapshot_essence_guarded_sender.py`

- [x] **Step 1: Write import-safety test**

Verify importing `rytm_randomizer.snapshot_essence_guarded_sender` is silent and does not import `mido`, `rtmidi`, or `librosa`.

- [x] **Step 2: Write refusal tests**

Build a valid snapshot essence send plan from a synthetic Rytm kit fixture. Assert `execute_snapshot_essence_guarded_send(..., armed=False, dry_run_confirmed=True)` returns `missing_arming` and emits nothing. Assert `armed=True, dry_run_confirmed=False` returns `missing_dry_run_confirmation` and emits nothing. Assert a manually blocked plan returns `plan_not_ready` and emits nothing.

- [x] **Step 3: Write acceptance and report tests**

Assert a ready plan emits exactly `plan.eligible_event_count` mock messages, preserves ordering, includes `guard` metadata, and formats a report with accepted status, emitted count, guard policy, and passive safety lines.

- [x] **Step 4: Write CLI test**

Run:

```powershell
python -m rytm_randomizer.cli snapshot-essence-guarded-send-dry-run-report <fixture> --slot 1 --depth micro --style "Birmingham dark techno" --discovery 0.35
```

Expected: accepted mock-only report, emitted mock message count, no stderr, no MIDI-sending safety line.

- [x] **Step 5: Run red tests**

Run:

```powershell
pytest tests\test_snapshot_essence_guarded_sender.py -q
```

Expected: fail because the module and CLI command do not exist yet.

### Task 2: Guard Module

**Files:**
- Create: `rytm_randomizer/snapshot_essence_guarded_sender.py`

- [x] **Step 1: Implement result dataclass**

Add `SnapshotEssenceGuardedSendResult` with accepted state, reason, plan metadata, emitted messages, and passive flags.

- [x] **Step 2: Implement executor**

Add `execute_snapshot_essence_guarded_send(plan, sender, armed, dry_run_confirmed)` with refusal ordering: type checks, arming, confirmation, plan readiness, ineligible events, then emit all events.

- [x] **Step 3: Implement dry-run builder and formatters**

Add `build_snapshot_essence_guarded_send_dry_run(plan)`, `format_snapshot_essence_guarded_send_dry_run_report(result)`, and `format_snapshot_essence_guarded_send_error(path, message)`.

- [x] **Step 4: Run module tests**

Run:

```powershell
pytest tests\test_snapshot_essence_guarded_sender.py -q
```

Expected: module tests pass except CLI wiring until Task 3.

### Task 3: CLI Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add CLI dispatch**

Accept:

```text
snapshot-essence-guarded-send-dry-run-report <path> --slot <slot> --depth <depth> --style <style> [--discovery <0..1>]
```

- [x] **Step 2: Add help text**

Add usage, command-list entry, and dedicated `--help` text.

- [x] **Step 3: Run CLI tests**

Run:

```powershell
pytest tests\test_snapshot_essence_guarded_sender.py tests\test_cli.py -q
```

Expected: pass.

### Task 4: Verification

**Files:**
- No source changes expected.

- [x] **Step 1: Run real project guarded dry-run**

Run:

```powershell
python -m rytm_randomizer.cli snapshot-essence-guarded-send-dry-run-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --style "Birmingham dark techno"
```

Expected: accepted mock-only report with the same eligible event count as the send plan.

- [x] **Step 2: Run focused regression**

Run:

```powershell
pytest tests\test_snapshot_essence_guarded_sender.py tests\test_snapshot_essence_send_plan.py tests\test_snapshot_essence_overlay.py tests\test_dual_machine_guarded_sender.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

Expected: pass.

- [x] **Step 3: Run full suite**

Run:

```powershell
pytest -q
```

Expected: pass with existing skips only.

### Task 5: Commit and Push

**Files:**
- All files above.

- [x] **Step 1: Run final guards**

Run:

```powershell
git diff --check
git diff --exit-code -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [ ] **Step 2: Stage and commit**

Run:

```powershell
git add docs/superpowers/specs/2026-05-17-snapshot-essence-guarded-dry-run-design.md docs/superpowers/plans/2026-05-17-snapshot-essence-guarded-dry-run.md rytm_randomizer/snapshot_essence_guarded_sender.py rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_snapshot_essence_guarded_sender.py tests/test_cli.py tests/fixtures/cli_help_expected.txt
git diff --cached --check
git commit -m "Add snapshot essence guarded dry-run report"
```

- [ ] **Step 3: Push**

Run:

```powershell
git push
```

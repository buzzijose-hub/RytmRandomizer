# Snapshot Essence Send Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a passive 12-pad Rytm send-plan report from a saved kit snapshot plus style intent.

**Architecture:** Compose the existing snapshot essence overlay with mapped V1.34 profile anchors and snapshot mutation changes. The module produces ordered inert CC events and can capture them into `MockMidiSender`; CLI wiring exposes the report without any real MIDI access.

**Tech Stack:** Python dataclasses, existing passive snapshot/style/profile modules, passive CLI dispatch, pytest.

---

## File Structure

- Create `rytm_randomizer/snapshot_essence_send_plan.py`: event dataclasses, plan builder, mock capture, formatter, error formatter.
- Modify `rytm_randomizer/cli.py`: add passive report dispatch.
- Modify `rytm_randomizer/help_text.py`: add command usage and help.
- Modify `tests/test_cli.py` and `tests/fixtures/cli_help_expected.txt`: keep global CLI help expectations synchronized.
- Create `tests/test_snapshot_essence_send_plan.py`: import safety, event ordering, mock capture, CLI report.
- Add this spec and plan.

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_snapshot_essence_send_plan.py`

- [x] **Step 1: Write import-safety test**

Verify importing `rytm_randomizer.snapshot_essence_send_plan` is silent and does not import `mido`, `rtmidi`, or `librosa`.

- [x] **Step 2: Write behavior test**

Use a synthetic Rytm kit where Pads 1 and 3 already match the style-selected mapped machines and the remaining pads require engine switches. Assert the plan is ready, separates machine switches, selected-profile anchors, and snapshot mutation events, and orders `CC15` before anchor params on switched pads.

- [x] **Step 3: Write mock capture and CLI tests**

Assert mock capture produces one `MockMidiSender` message per eligible event with metadata, and the CLI prints event counts plus passive safety lines.

- [x] **Step 4: Run red tests**

Run:

```powershell
pytest tests\test_snapshot_essence_send_plan.py -q
```

Expected: fail because the module and CLI command do not exist yet.

### Task 2: Passive Send Plan Module

**Files:**
- Create: `rytm_randomizer/snapshot_essence_send_plan.py`

- [x] **Step 1: Implement dataclasses**

Create `SnapshotEssenceSendPlanEvent` and `SnapshotEssenceSendPlan` with source metadata, style metadata, readiness counts, and ordered events.

- [x] **Step 2: Implement builder**

Add `build_snapshot_essence_send_plan_from_file(path, slot, depth, style, discovery=None)` and `build_snapshot_essence_send_plan(overlay)`.

- [x] **Step 3: Implement event policy**

For engine-switch pads, emit `machine_switch` followed by selected mapped profile anchor params. For same-engine pads, emit snapshot mutation changes. Do not emit events for blocked pads.

- [x] **Step 4: Implement mock capture and formatter**

Convert eligible events to `MockMidiSender` messages and print deterministic report lines with safety policy.

- [x] **Step 5: Run module tests**

Run:

```powershell
pytest tests\test_snapshot_essence_send_plan.py -q
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
snapshot-essence-send-plan-report <path> --slot <slot> --depth <depth> --style <style> [--discovery <0..1>]
```

- [x] **Step 2: Add help text**

Add usage, command-list entry, and dedicated `--help` text.

- [x] **Step 3: Run CLI tests**

Run:

```powershell
pytest tests\test_snapshot_essence_send_plan.py tests\test_cli.py -q
```

Expected: pass.

### Task 4: Verification

**Files:**
- No source changes expected.

- [x] **Step 1: Run real project report**

Run:

```powershell
python -m rytm_randomizer.cli snapshot-essence-send-plan-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --style "Birmingham dark techno"
```

Expected: report reads the real dump and prints 12-pad event plan rows.

- [x] **Step 2: Run focused regression**

Run:

```powershell
pytest tests\test_snapshot_essence_send_plan.py tests\test_snapshot_essence_overlay.py tests\test_twelve_pad_mock_runtime.py tests\test_snapshot_mutation_planner.py tests\test_dual_machine_active_send_plan.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
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
git add docs/superpowers/specs/2026-05-17-snapshot-essence-send-plan-design.md docs/superpowers/plans/2026-05-17-snapshot-essence-send-plan.md rytm_randomizer/snapshot_essence_send_plan.py rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_snapshot_essence_send_plan.py tests/test_cli.py tests/fixtures/cli_help_expected.txt
git diff --cached --check
git commit -m "Add snapshot essence send plan report"
```

- [ ] **Step 3: Push**

Run:

```powershell
git push
```

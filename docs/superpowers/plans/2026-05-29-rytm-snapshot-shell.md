# Analog Rytm Snapshot Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first live-safe all-12-pad snapshot shell that anchors to a current-kit SysEx dump and exposes old V1.34-style mutation commands.

**Architecture:** Add a focused snapshot anchor/command shell under `rytm_randomizer/engines/`, using the existing Rytm snapshot decoder, manual-backed MIDI catalog, and sender boundary. Wire it through `app.py` behind explicit dry-run/armed flags and keep all real MIDI imports lazy.

**Tech Stack:** Python dataclasses, existing Rytm SysEx decoder, manual-backed Rytm CC catalog, `MockMidiSender`, pytest, ruff, black, isort.

---

## File Structure

- Create `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`
  - Snapshot-anchor event extraction.
  - Live-safe mutation commands.
  - Interactive shell loop.
  - Formatting and send helpers.
- Create `tests/test_analog_rytm_snapshot_shell.py`
  - Unit tests for anchor extraction, old commands, depth prompts, `Z`, `U`, and send behavior.
- Modify `rytm_randomizer/app.py`
  - Add `--rytm-snapshot-shell` and `--confirm-rytm-snapshot-shell-send`.
  - Add dry-run and armed runners.
  - Add conflict validation.
- Modify `tests/test_app_validate_one_cc.py`
  - Add app-level dry-run, no-real-MIDI import, armed confirmation, fake-mido send, and conflict tests.
- Modify `README.md`, `docs/MANUAL_HARDWARE_VALIDATION.md`, and `docs/STATUS.md`
  - Document the new shell and hardware safety flow.

## Task 1: Snapshot Anchor Tests

- [x] **Step 1: Write failing tests**

Add tests that build a real-layout Rytm payload with known per-pad byte values and assert:

```python
anchor = build_snapshot_shell_anchor(snapshot)
assert anchor.kit_name == "LIVE"
assert set(anchor.events_by_pad) == set(range(1, 13))
assert anchor.events_by_pad[1]
assert all(event.parameter != "Track Machine Type" for event in anchor.events)
```

- [x] **Step 2: Run focused test**

Run:

```powershell
python -m pytest tests/test_analog_rytm_snapshot_shell.py::test_snapshot_shell_anchor_extracts_all_12_pads_without_machine_switches -n 0
```

Expected: fail because the module does not exist.

- [x] **Step 3: Implement anchor extraction**

Create `analog_rytm_snapshot_shell.py` with dataclasses for anchor events and a helper that extracts promoted safe rows from the snapshot unpacked payload.

- [x] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_analog_rytm_snapshot_shell.py -n 0
```

Expected: anchor tests pass.

## Task 2: Old Command Mutation Surface

- [x] **Step 1: Write failing tests**

Add tests for `S1A`, `S3A`, `S3B`, `S4B`, `4`, `Y`, `V`, `N`, `Z`, and `U`.

- [x] **Step 2: Implement command registry**

Implement a constant-backed command registry in `analog_rytm_snapshot_shell.py`.
Avoid bare string dispatch against canonical mode strings by using `Final`
constants.

- [x] **Step 3: Implement live-safe mutation**

Mutate values around the captured anchor by role, section, command, and depth.
Pad 1 kick filter frequency stays near its captured anchor.

- [x] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_analog_rytm_snapshot_shell.py -n 0
```

Expected: shell command tests pass.

## Task 3: App Wiring

- [x] **Step 1: Write app tests**

Add tests for:

- Dry-run scripted shell run.
- Dry-run imports no real MIDI library.
- Armed send refuses without confirmation before port listing.
- Armed send uses fake mido output and closes the port.
- Conflicts with existing active helpers.

- [x] **Step 2: Add app flags and runners**

Add `--rytm-snapshot-shell` and `--confirm-rytm-snapshot-shell-send`, then wire
dry-run and armed runners that load the SysEx file before starting the shell.

- [x] **Step 3: Verify app tests**

Run:

```powershell
python -m pytest tests/test_app_validate_one_cc.py::test_app_main_dry_run_rytm_snapshot_shell_runs_scripted_v134_style_flow -n 0
```

Expected: pass after wiring.

## Task 4: Documentation

- [x] **Step 1: Update README**

Document dry-run and armed commands plus the old shell command vocabulary.

- [x] **Step 2: Update hardware validation docs**

Add a manual validation section with dry-run first, low monitoring volume, and
stop conditions.

- [x] **Step 3: Update status**

Add a dated status entry for the first snapshot shell.

## Task 5: Verification

- [x] **Step 1: Focused tests**

Run:

```powershell
python -m pytest tests/test_analog_rytm_snapshot_shell.py tests/test_app_validate_one_cc.py tests/test_analog_rytm_performance_mutation.py -n 0
```

- [x] **Step 2: Architecture gate**

Run:

```powershell
python -m pytest tests/architecture/ -q
```

- [x] **Step 3: Lint trio**

Run:

```powershell
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

- [x] **Step 4: Full test suite**

Run:

```powershell
python -m pytest
```

## Self-Review

- Spec coverage: plan covers snapshot anchor extraction, old command vocabulary,
  all-12-pad mutation, app flags, docs, and verification.
- Placeholder scan: no `TBD` or unspecified task remains.
- Type consistency: shell dataclasses and app flag names are consistent across
  tasks.

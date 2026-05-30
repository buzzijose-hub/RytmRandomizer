# Analog Rytm Live Snapshot Receive Shell Implementation Plan

> Status: in-flight (branch codex/rytm-snapshot-pad-compatibility-pr1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a one-command live workflow that receives the current Analog Rytm KIT SysEx from hardware and immediately opens the all-12-pad snapshot mutation shell from that received state.

**Architecture:** Keep SysEx receiving behind the existing real-MIDI provider boundary with lazy MIDI imports. The app chooses an input, waits for one framed KIT SysEx message, decodes it into the existing snapshot shell anchor, then chooses an output and runs the already-built snapshot shell.

**Tech Stack:** Python, `python-rtmidi` lazy input capture, existing Rytm SysEx decoder, existing snapshot shell, pytest, ruff, black, isort.

---

## File Structure

- Modify `rytm_randomizer/mido_provider.py`
  - Add lazy `rtmidi` import and one raw SysEx capture method.
- Modify `rytm_randomizer/app.py`
  - Add `--rytm-live-snapshot-shell`.
  - Add Rytm input prompt, live capture, decode, and handoff to armed snapshot shell.
  - Add conflict and confirmation validation.
- Modify `tests/test_mido_provider.py`
  - Add raw SysEx capture provider tests with fake `rtmidi`.
- Modify `tests/test_app_validate_one_cc.py`
  - Add app-level live receive shell tests.
- Modify `README.md` and `docs/MANUAL_HARDWARE_VALIDATION.md`
  - Document the fresh live receive workflow.

## Task 1: Provider SysEx Capture

- [x] **Step 1: Write failing provider tests**

Add tests proving `MidoMidiPortProvider.capture_sysex_messages()` uses a fake `rtmidi`, enables SysEx, returns the first complete framed message, rejects bad input names, and times out without a frame.

- [x] **Step 2: Verify red**

Run:

```powershell
python -m pytest tests/test_mido_provider.py::test_capture_sysex_messages_returns_first_complete_frame_from_fake_rtmidi -n 0
```

Expected: fail because `capture_sysex_messages` does not exist.

- [x] **Step 3: Implement provider capture**

Add a lazy `_import_rtmidi()` helper and `capture_sysex_messages(port_name, timeout_seconds=...)`.

- [x] **Step 4: Verify provider tests**

Run:

```powershell
python -m pytest tests/test_mido_provider.py -n 0
```

## Task 2: App Live Receive Shell

- [x] **Step 1: Write failing app tests**

Add tests proving `--arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send` chooses input, receives KIT SysEx, chooses output, enters the snapshot shell, sends all 12 pads, and closes output. Add confirmation and conflict tests.

- [x] **Step 2: Verify red**

Run:

```powershell
python -m pytest tests/test_app_validate_one_cc.py::test_app_main_arm_rytm_live_snapshot_shell_receives_kit_then_sends_fake_mido -n 0
```

Expected: fail because the flag does not exist.

- [x] **Step 3: Implement app wiring**

Add parser flag, conflict validation, live capture helper, Rytm input chooser, and dispatch before the file-based snapshot shell.

- [x] **Step 4: Verify app tests**

Run:

```powershell
python -m pytest tests/test_app_validate_one_cc.py -n 0
```

## Task 3: Docs And Verification

- [x] **Step 1: Update operator docs**

Add the live command and fresh workflow to `README.md` and `docs/MANUAL_HARDWARE_VALIDATION.md`.

- [x] **Step 2: Run focused verification**

Run:

```powershell
python -m pytest tests/test_mido_provider.py tests/test_app_validate_one_cc.py tests/test_analog_rytm_snapshot_shell.py -n 0
```

- [x] **Step 3: Run architecture and lint**

Run:

```powershell
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

## Self-Review

- Spec coverage: live receive, decode, output handoff, confirmation safety, and docs are covered.
- Placeholder scan: no placeholder behavior remains.
- Type consistency: provider and app method names match across tasks.

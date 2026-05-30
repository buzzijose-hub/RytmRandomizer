# Analog Rytm 12-Pad Interactive Shell Implementation Plan

> Status: in-flight (branch codex/rytm-snapshot-pad-compatibility-pr1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an all-12-pad interactive Analog Rytm shell with role-safe mutations, preview, send, undo, and reset.

**Architecture:** A new engine module consumes rendered 12-pad style recipe events and owns session state plus deterministic mutation commands. `rytm_randomizer.app` remains the active boundary, creating either a mock sender or one real Rytm output port and passing it into the shell.

**Tech Stack:** Python 3.11 stdlib, frozen dataclasses, existing Rytm style recipe data, existing `midi_io.send_cc`, pytest fake-mido seams.

---

## File Structure

- Create: `rytm_randomizer/engines/analog_rytm_12_pad_shell.py`
  - Role classification, deterministic mutation helpers, preview formatting,
    send helper, and `AnalogRytm12PadShell`.
- Create: `tests/test_analog_rytm_12_pad_shell.py`
  - Pure runtime tests for load, preview, mutations, undo, reset, and send.
- Modify: `rytm_randomizer/app.py`
  - Add `--rytm-12-pad-shell` and `--confirm-rytm-12-pad-send`; wire dry-run
    and armed launch paths.
- Modify: `tests/test_app_validate_one_cc.py`
  - App-level tests for dry-run, import safety, confirmation refusal, fake
    armed send, and flag conflicts.
- Modify: `README.md`, `docs/MANUAL_HARDWARE_VALIDATION.md`, `docs/STATUS.md`
  - Document the new shell and hardware validation sequence.

## Tasks

### Task 1: Runtime Tests

- [ ] Add tests for `AnalogRytm12PadShell`.
- [ ] Assert `load detroit-deep` stages all 12 pads and sends no MIDI.
- [ ] Assert `preview` includes the shell title, style label, mutation label,
      pad count, event count, and per-pad machine lines.
- [ ] Assert each mutation command changes at least one non-machine event on
      every pad.
- [ ] Assert every mutation preserves BD `Filter Frequency <= 32`.
- [ ] Assert `send` sends the staged plan through `MockMidiSender`.
- [ ] Assert `undo` returns to the previous staged plan.
- [ ] Assert `reset` returns to the loaded style anchor.
- [ ] Run the test file and confirm it fails because the module does not exist.

### Task 2: Runtime Implementation

- [ ] Create `rytm_randomizer/engines/analog_rytm_12_pad_shell.py`.
- [ ] Add frozen dataclasses for mutation command metadata and shell state.
- [ ] Add `classify_rytm_pad_role(machine_key)`.
- [ ] Add `mutate_12_pad_events(events, mutation_name)`.
- [ ] Add `format_12_pad_preview(state)`.
- [ ] Add `send_12_pad_events(out, events, skip_sleep)`.
- [ ] Add `AnalogRytm12PadShell.dispatch(raw_command)` and `.run()`.
- [ ] Run runtime tests and confirm they pass.

### Task 3: App Tests

- [ ] Add dry-run app test that runs scripted input:
      `load detroit-deep`, `roll`, `preview`, `send`, `q`.
- [ ] Assert dry-run prints no-hardware/no-port text and captures messages.
- [ ] Add import-safety subprocess test confirming dry-run imports no `mido`,
      `rtmidi`, or `pythonrtmidi`.
- [ ] Add armed confirmation-refusal test that monkeypatches provider methods
      to fail if touched.
- [ ] Add fake-mido armed test that selects output `0`, sends one loaded style,
      and closes the port.
- [ ] Add conflict test against `--rytm-kit-style` and `--validate-one-cc`.
- [ ] Run added app tests and confirm they fail before app wiring.

### Task 4: App Implementation

- [ ] Add parser flags.
- [ ] Add `_run_dry_run_rytm_12_pad_shell()`.
- [ ] Add `_run_armed_rytm_12_pad_shell()`.
- [ ] Add `_run_rytm_12_pad_shell(args)`.
- [ ] Add conflict checks and dispatch before legacy `--arm`/`--dry-run`.
- [ ] Run app and runtime tests.

### Task 5: Docs And Verification

- [ ] Update `README.md` launch examples and command summary.
- [ ] Update manual hardware validation with a 12-pad shell runbook.
- [ ] Update status with the new shell capability.
- [ ] Run targeted tests.
- [ ] Run `python -m pytest tests/architecture/ -q`.
- [ ] Run `python -m pytest -m fast`.
- [ ] Run `python -m pytest`.
- [ ] Run `python -m ruff check .`, `python -m black --check --target-version=py311 .`, and `python -m isort --profile black --check-only .`.

## Safety Boundary

This plan intentionally keeps the shell recipe-grounded and CC-MSB only. It
does not add free-text prompts, samples, performance macros, source level,
track level, amp volume, SysEx, transport, pattern changes, kit saves, or
project writes. Armed mode requires `--arm --rytm-12-pad-shell
--confirm-rytm-12-pad-send`.

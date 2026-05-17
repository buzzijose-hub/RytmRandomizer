# Rytm Engine Cycle Guarded Send Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add guarded dry-run and armed hardware execution for the 12-pad Rytm engine-cycle plan.

**Architecture:** Keep `rytm_engine_cycle_plan` as the pure planner. Add one mock-only guarded sender and one active hardware sender, then wire `rytm_randomizer.app` so `--dry-run --rytm-engine-cycle` and `--arm --rytm-engine-cycle` share the same plan.

**Tech Stack:** Python dataclasses, existing `MockMidiSender`, lazy `midi_io.send_cc`, app argument parsing, pytest.

---

## File Structure

- Create `rytm_randomizer/rytm_engine_cycle_guarded_sender.py`
  - Guarded mock-only execution and report formatting.
- Create `rytm_randomizer/rytm_engine_cycle_hardware_sender.py`
  - Guarded active sender using injected output and lazy `send_cc`.
- Modify `rytm_randomizer/app.py`
  - Add app flags, request parsing, dry-run route, armed route, confirmation prompt, and validation.
- Create `tests/test_rytm_engine_cycle_guarded_sender.py`
  - Mock guard behavior and report coverage.
- Create `tests/test_rytm_engine_cycle_hardware_sender.py`
  - Hardware guard behavior with fake mido and fake port.
- Modify `tests/test_app_entry.py`
  - App-level dry-run, arm, validation, and conflict tests.

## Steps

- [x] Write failing tests for guarded mock sender, active hardware sender, and app routing.
- [x] Run focused tests and confirm they fail for missing modules/flags.
- [x] Implement `rytm_engine_cycle_guarded_sender.py`.
- [x] Implement `rytm_engine_cycle_hardware_sender.py`.
- [x] Wire `--rytm-engine-cycle` into `app.py`.
- [x] Run focused tests, app tests, full suite, diff checks, commit, and push.

# Analog Four Starter Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add named Analog Four safe-starter profiles and expose them through the dual-machine bridge, passive CLI reports, and active app snapshot send.

**Architecture:** Add one focused profile data module, then make the existing dual-machine bridge select a profile before producing A4 CC messages. Downstream active-plan, guarded-send, and hardware-send reports carry the selected profile as metadata; saved-offset A4 snapshot candidates remain blocked and mutually exclusive with non-default starter profiles.

**Tech Stack:** Python frozen dataclasses, existing dual-machine bridge/send-plan modules, passive CLI dispatch, argparse app entry point, pytest.

---

## File Structure

- Create `rytm_randomizer/analog_four_starter_profiles.py`
  - Owns starter profile dataclasses, aliases, profile lookup, and passive profile reports.
- Modify `rytm_randomizer/dual_machine_mock_bridge.py`
  - Accepts `analog_four_profile`.
  - Builds safe-starter plans from resolved profile data.
  - Adds profile metadata to bridge reports and A4 mock messages.
- Modify `rytm_randomizer/dual_machine_active_send_plan.py`
  - Carries optional A4 starter profile metadata in active plans and reports.
- Modify `rytm_randomizer/dual_machine_guarded_sender.py`
  - Carries profile metadata into dry-run reports.
- Modify `rytm_randomizer/dual_machine_hardware_sender.py`
  - Carries profile metadata into armed hardware reports.
- Modify `rytm_randomizer/cli.py` and `rytm_randomizer/help_text.py`
  - Parse and document `--analog-four-profile`.
- Modify `rytm_randomizer/app.py`
  - Parse `--analog-four-profile` for `--dual-machine-snapshot-send`.
- Tests:
  - `tests/test_analog_four_starter_profiles.py`
  - Existing dual-machine/app/CLI tests.

## Steps

- [x] Add red tests for profile listing, alias resolution, profile-specific A4 CC values, CLI parsing, app dry-run output, and snapshot-source conflict.
- [x] Run focused tests and confirm they fail against the current fixed-profile implementation.
- [x] Implement `analog_four_starter_profiles.py` with four profile definitions.
- [x] Wire `analog_four_profile` through the dual-machine bridge and report metadata.
- [x] Wire profile metadata through active-plan, guarded-send, and hardware-send reports.
- [x] Add CLI/app parsing and help text.
- [x] Run focused tests, real project dry-run with `--analog-four-profile birmingham-dark`, full suite, diff checks, commit, and push.

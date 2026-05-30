# Rytm Live Lane Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add session-only tune/noise/fx/filter/amp/lfo lane guardrails to the Analog Rytm snapshot shell so it can act as a trustworthy live sound-design performer beside the OXI.

**Architecture:** Keep the feature inside `rytm_randomizer/engines/analog_rytm_snapshot_shell.py` as shell-session policy. Add immutable lane policy state to `SnapshotSessionGuardrails`, classify each rendered event into a lane, and cap or omit mutation/send behavior through the existing mutation path. Preserve the current pad lock, depth, preset, `kit`, `go`, `z`, and Pad 1 foundation behavior.

**Tech Stack:** Python dataclasses, `Literal` aliases, existing snapshot shell tests, pytest, ruff, black, isort.

---

## File Map

- Modify `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`: add lane policy constants/state, event lane classification, lane-aware active-send filtering, `lane ...` command parsing, and status/help text.
- Modify `tests/test_analog_rytm_snapshot_shell.py`: add red/green tests for defaults, lane-off behavior, lane depth caps, invalid command safety, status output, `kit` preservation, and send counts.
- Modify `README.md`: document the live second-performer model and lane commands.
- Modify `docs/MANUAL_HARDWARE_VALIDATION.md`: add a lane-guardrail listening pass to the snapshot shell validation.
- Modify `docs/STATUS.md`: record the lane guardrail addition.

## Task 1: Add Failing Lane Policy Tests

**Files:**
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [x] **Step 1: Add tests for default lane policy and status output.**

Add tests named:

```python
def test_snapshot_shell_lane_guardrails_default_to_live_trust_profile() -> None:
    ...

def test_snapshot_shell_status_reports_lane_guardrails(capsys) -> None:
    ...
```

Expected defaults:

```text
tune=micro, noise=normal, fx=micro, filter=normal, amp=normal, lfo=off
```

- [x] **Step 2: Run the focused tests and verify they fail.**

Run:

```powershell
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests\test_analog_rytm_snapshot_shell.py::test_snapshot_shell_lane_guardrails_default_to_live_trust_profile tests\test_analog_rytm_snapshot_shell.py::test_snapshot_shell_status_reports_lane_guardrails -n 0
```

Expected: fail because lane state/status does not exist yet.

## Task 2: Add Lane State and Classification

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [x] **Step 1: Add lane type aliases, constants, default mapping, and guardrail state.**

Add `SnapshotLane`, `SnapshotLanePolicy`, `lane_policies`, and default lane
policies. Keep constants `Final`.

- [x] **Step 2: Classify events into lanes.**

Lane mapping:

```text
tune   -> source tune/detune events
noise  -> noise/dust parameter family
fx     -> delay/reverb send parameter family
filter -> FILTER section
amp    -> AMP section excluding fx lane rows
lfo    -> LFO section
```

- [x] **Step 3: Run focused tests.**

Run:

```powershell
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: existing tests may fail where active send counts need to include lane-off LFO behavior.

## Task 3: Apply Lane Policies to Mutation and Send

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [x] **Step 1: Add failing behavior tests.**

Add tests named:

```python
def test_snapshot_shell_lane_lfo_off_omits_lfo_mutation_and_send() -> None:
    ...

def test_snapshot_shell_lane_fx_off_omits_delay_and_reverb_sends() -> None:
    ...

def test_snapshot_shell_lane_filter_micro_caps_filter_movement() -> None:
    ...
```

- [x] **Step 2: Verify red.**

Run:

```powershell
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests\test_analog_rytm_snapshot_shell.py::test_snapshot_shell_lane_lfo_off_omits_lfo_mutation_and_send tests\test_analog_rytm_snapshot_shell.py::test_snapshot_shell_lane_fx_off_omits_delay_and_reverb_sends tests\test_analog_rytm_snapshot_shell.py::test_snapshot_shell_lane_filter_micro_caps_filter_movement -n 0
```

Expected: fail because lane policy is not applied yet.

- [x] **Step 3: Apply lane policy in `_mutate_snapshot_event` and `_is_snapshot_shell_event_active`.**

Use lane `off` to return the current event unchanged and omit that lane from
sendable events. Use `micro`, `normal`, and `wide` to cap effective session
depth before computing deltas.

- [x] **Step 4: Run focused tests.**

Run:

```powershell
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: all snapshot shell tests pass.

## Task 4: Add `lane ...` Commands

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [x] **Step 1: Add failing command tests.**

Add tests named:

```python
def test_snapshot_shell_lane_command_updates_policy_and_preserves_tune_alias(capsys) -> None:
    ...

def test_snapshot_shell_invalid_lane_commands_do_not_mutate_or_send(capsys) -> None:
    ...
```

- [x] **Step 2: Verify red.**

Run:

```powershell
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests\test_analog_rytm_snapshot_shell.py::test_snapshot_shell_lane_command_updates_policy_and_preserves_tune_alias tests\test_analog_rytm_snapshot_shell.py::test_snapshot_shell_invalid_lane_commands_do_not_mutate_or_send -n 0
```

Expected: fail because `lane` is unknown.

- [x] **Step 3: Implement parser/help/status updates.**

Add:

```text
lane tune|noise|fx|filter|amp|lfo off|micro|normal|wide
```

Make `lane tune VALUE` update the existing tune policy too, so the older
`tune ...` command and the new lane command stay coherent.

- [x] **Step 4: Run focused tests.**

Run:

```powershell
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: all snapshot shell tests pass.

## Task 5: Docs and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Update docs with the second-performer framing and lane commands.**

Document the OXI/RytmRandomizer performance split and the recommended first
listening pass:

```text
preset live
lane lfo off
lane fx micro
status
randomize
changes
send
go
changes
send
z
send
```

- [x] **Step 2: Run focused verification.**

Run:

```powershell
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests\test_analog_rytm_snapshot_shell.py tests\test_app_validate_one_cc.py tests\test_mido_provider.py -n 0
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests\architecture\ -q
```

Expected: all pass.

- [x] **Step 3: Run lint and full suite.**

Run:

```powershell
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m ruff check .
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m black --check --target-version=py311 .
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m isort --profile black --check-only .
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest
```

Expected: all pass.

## Self-Review

- Spec coverage: the plan covers the OXI/RytmRandomizer model, all six lane
  names, lane policy defaults, status/help, mutation/send enforcement, docs,
  and verification.
- Placeholder scan: no `TBD`, `TODO`, or unspecified tasks remain.
- Type consistency: lane names and policies match across tests, state, parser,
  status, and docs.

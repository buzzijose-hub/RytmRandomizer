# Rytm Live Session Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add session-only live guardrails to the Analog Rytm snapshot shell so global mutations respect per-pad locks and depth lanes.

**Architecture:** Keep the feature inside `rytm_randomizer/engines/analog_rytm_snapshot_shell.py` because it is shell-session state, not persistent data. Add small immutable session policy dataclasses, make mutation consult the policy per event, and extend dispatch with setup commands (`mode`, `depth`, `pad`, `lock`, `unlock`, `status`). Keep sending passive until explicit `send`.

**Tech Stack:** Python dataclasses, Literal type aliases, existing snapshot shell tests, pytest, ruff, black, isort.

---

## File Map

- Modify `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`: add session guardrail state, command parsing, effective depth resolution, and status formatting.
- Modify `tests/test_analog_rytm_snapshot_shell.py`: add focused tests for default live policy, pad locks, per-pad overrides, mode/depth commands, status, invalid setup safety, and send/again compatibility.
- Modify `README.md`, `docs/MANUAL_HARDWARE_VALIDATION.md`, and `docs/STATUS.md`: document the live control commands and hardware retest path after implementation.

## Task 1: Add Failing Session Policy Tests

**Files:**
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Write tests for defaults, locks, overrides, and status**

Add tests named:

```python
def test_snapshot_shell_live_guardrails_default_to_controlled_pad_lanes() -> None:
    ...

def test_snapshot_shell_lock_prevents_pad_from_mutating() -> None:
    ...

def test_snapshot_shell_pad_depth_override_moves_more_than_global_gentle() -> None:
    ...

def test_snapshot_shell_status_reports_session_guardrails(capsys) -> None:
    ...

def test_snapshot_shell_invalid_guardrail_commands_do_not_mutate_or_send(capsys) -> None:
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: failures for missing guardrail state/commands.

## Task 2: Implement Session Guardrail State

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Add type aliases and policy dataclasses**

Add `SnapshotSessionMode`, `SnapshotSessionDepth`, `SnapshotPadPolicy`, and `SnapshotSessionGuardrails`.

- [ ] **Step 2: Add default live policy**

Default mode is `live`, global depth is `normal`, and pad defaults are:

```python
{
    1: "gentle",
    2: "normal",
    3: "normal",
    4: "normal",
    5: "gentle",
    6: "gentle",
    7: "gentle",
    8: "gentle",
    9: "gentle",
    10: "gentle",
    11: "normal",
    12: "normal",
}
```

- [ ] **Step 3: Add guardrails to shell state**

`RytmSnapshotShellState` gains `guardrails: SnapshotSessionGuardrails`.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: default-policy tests pass; command tests still fail.

## Task 3: Apply Guardrails During Mutation

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Add effective depth helpers**

Add helpers that map session depth into anchor-relative live/studio movement
windows:

```python
gentle -> smallest total distance from captured anchor
normal -> controlled total distance from captured anchor
strong -> larger total distance from captured anchor
wild -> largest total distance from captured anchor
```

- [ ] **Step 2: Skip locked pads**

In `_mutate_snapshot_event`, return `current_event` unchanged when the pad policy is locked.

- [ ] **Step 3: Use per-pad depth override**

Before mutating each event, resolve depth from pad policy first, then global depth.

- [ ] **Step 4: Preserve Pad 1 kick filter safeguards**

Keep existing Pad 1 filter mode/frequency/resonance clamps active in both live and studio mode.

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: lock and override tests pass.

- [ ] **Step 6: Add cumulative-drift regression**

Repeated `4` mutations in `mode live` and `depth gentle` must stay inside the
selected anchor-relative pad lane. This protects live sets from gradual drift
after many send/mutate cycles.

## Task 4: Add Guardrail Setup Commands

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Add commands**

Implement:

```text
mode live
mode studio
depth gentle|normal|strong|wild
lock N
unlock N
pad N gentle|normal|strong|wild
pad N off
status
```

- [ ] **Step 2: Validate commands**

Invalid setup commands print a clear error and do not mutate current events, previous events, sent count, or sender messages.

- [ ] **Step 3: Update help text**

Add the new commands to `_help_text()`.

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: all snapshot-shell tests pass.

## Task 5: Update Docs and Verify

**Files:**
- Modify: `README.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Document commands**

Document the session-only live control commands and the recommended retest flow:

```text
mode live
depth gentle
pad 1 gentle
status
4
changes
send
again
send
```

- [ ] **Step 2: Run focused verification**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py tests\test_app_validate_one_cc.py tests\test_mido_provider.py -n 0
python -m pytest tests\architecture\ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected: all pass.

- [ ] **Step 3: Run full verification**

Run:

```powershell
python -m pytest
```

Expected: full suite passes.

- [ ] **Step 4: Hardware retest**

Run:

```powershell
python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send
```

Inside `snapshot-12>`:

```text
mode live
depth gentle
pad 1 gentle
status
4
changes
send
again
changes
send
q
```

Expected: Pad 1 remains gentle, locked pads remain unchanged when used, later pads show source movement, and no save/write/transport/pattern behavior appears.

## Self-Review

- Spec coverage: session-only controls, live/studio mode, global depth, pad locks, per-pad depth overrides, status, mutation semantics, invalid command safety, docs, and hardware retest are covered.
- Placeholder scan: no placeholder steps remain.
- Type consistency: plan names match intended code names and shell commands.

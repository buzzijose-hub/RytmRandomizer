# Rytm Pad 1 Foundation Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Protect Pad 1 kick-foundation controls in the live snapshot shell while preserving small anchor-relative tuning movement.

**Architecture:** Keep the policy inside the existing snapshot shell engine. Add private predicates for Pad 1 protected events and active sendable events, then reuse them from mutation, status, preview, and send paths.

**Tech Stack:** Python 3.11, pytest, ruff, black, isort.

---

### Task 1: Capture the Pad 1 Protection Contract

**Files:**
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Write failing tests**

Add tests that exercise the current shell through public dispatch methods:

```python
def test_snapshot_shell_pad_1_foundation_controls_are_not_sent() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)
    shell.dispatch("4")

    assert shell.dispatch("send") is True

    protected_names = {"Filter Frequency", "LFO Speed", "Amp Attack Time"}
    sent_controls = {
        message.control
        for message in sender.sent_messages
        if message.channel == 0
    }
    protected_controls = {
        _event_for(shell.state.anchor.events, pad=1, parameter=name).cc_msb
        for name in protected_names
    }
    assert sent_controls.isdisjoint(protected_controls)
```

```python
def test_snapshot_shell_pad_1_foundation_controls_do_not_mutate(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), MockMidiSender())
    shell.dispatch("4")

    assert shell.dispatch("changes") is True

    captured = capsys.readouterr()
    assert "Pad 01 bd_hard Tune:" in captured.out
    assert "Pad 01 bd_hard FILTER" not in captured.out
    assert "Pad 01 bd_hard LFO" not in captured.out
    assert "Pad 01 bd_hard AMP Amp Attack Time" not in captured.out
```

```python
def test_snapshot_shell_pad_1_tune_is_captured_anchor_plus_or_minus_three_in_studio() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("preset studio") is True
    assert shell.dispatch("pad 1 wild") is True
    assert shell.dispatch("4") is True

    assert _delta_for(anchor.events, shell.state.current_events, pad=1, parameter="Tune") <= 3
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0`

Expected: the new send/protection tests fail because the current shell still
mutates and sends Pad 1 filter, LFO, and AMP attack events.

### Task 2: Add the Pad 1 Foundation Filter

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Implement private predicates**

Add constants and helpers:

```python
_AMP_SECTION: Final[str] = "AMP"
_LFO_SECTION: Final[str] = "LFO"
_AMP_ATTACK_TIME: Final[str] = "Amp Attack Time"
_PAD_1_TUNE_WINDOW: Final[int] = 3

def _is_pad_1_foundation_protected_event(event: AnalogRytmRenderedStyleEvent) -> bool:
    if event.pad != 1:
        return False
    if event.section in {_FILTER_SECTION, _LFO_SECTION}:
        return True
    return event.section == _AMP_SECTION and event.parameter == _AMP_ATTACK_TIME

def _is_pad_1_tune_event(event: AnalogRytmRenderedStyleEvent) -> bool:
    return event.pad == 1 and event.source == "machine_src" and "tune" in event.parameter.casefold()

def _is_snapshot_shell_event_active(
    event: AnalogRytmRenderedStyleEvent,
    guardrails: SnapshotSessionGuardrails,
) -> bool:
    if event.pad in guardrails.locked_pads:
        return False
    return not _is_pad_1_foundation_protected_event(event)
```

- [ ] **Step 2: Apply predicates to mutation and send path**

In `_mutate_snapshot_event`, return the captured anchor event when the current
event is foundation-protected. After the normal anchor-limited value is computed,
apply `_PAD_1_TUNE_WINDOW` for Pad 1 tune events.

In `_sendable_snapshot_shell_events`, filter with `_is_snapshot_shell_event_active`.

In `format_snapshot_shell_status`, count only active events.

In `format_snapshot_shell_preview`, build the preview from active events so the
shown event count matches the send plan.

- [ ] **Step 3: Run focused tests to verify green**

Run: `python -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0`

Expected: all snapshot shell tests pass.

### Task 3: Update Operator Docs and Verify

**Files:**
- Modify: `README.md`
- Modify: `docs/hardware-validation/2026-05-29-rytm-live-safe-performance-session.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Document the hardware lesson**

Record that Pad 1 foundation protection excludes filter, LFO, and AMP attack
messages, and that Pad 1 tuning stays within plus or minus 3 of the captured kit
value.

- [ ] **Step 2: Run local verification**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
python -m ruff check rytm_randomizer\engines\analog_rytm_snapshot_shell.py tests\test_analog_rytm_snapshot_shell.py
python -m black --check --target-version=py311 rytm_randomizer\engines\analog_rytm_snapshot_shell.py tests\test_analog_rytm_snapshot_shell.py
python -m isort --profile black --check-only rytm_randomizer\engines\analog_rytm_snapshot_shell.py tests\test_analog_rytm_snapshot_shell.py
python -m pytest
```

Expected: focused tests, lint checks, and the full suite pass.

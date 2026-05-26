# First Outbound 12-Track CC Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove, in the smallest safe sequence, that outbound Rytm CC messages can target all 12 tracks with the correct channel/control/value shape before any broader performance-facing mutation work.

**Architecture:** Use three gates: document the receive-channel model, prove the candidate message stream with mock-only tests, then run a manual armed hardware validation on a disposable kit. The plan does not add scenes, global mutation, SysEx, transport, pattern changes, project writes, or unattended hardware behavior.

**Tech Stack:** Python 3.11-compatible stdlib, pytest, existing `rytm_randomizer.midi_io.send_cc`, existing `rytm_randomizer.mock_midi.MockMidiSender`, existing `rytm_randomizer.devices.strategies.AnalogRytmMessageRenderer`, existing manual hardware validation runbook.

---

## Current Evidence

The 2026-05-26 passive USB input validation proved that manual Rytm track selection plus knob movement reports the following channel map:

| Rytm Track | Pad | Observed mido channel | MIDI channel meaning |
|---:|---:|---:|---:|
| 1 | 1 | 0 | 1 |
| 2 | 2 | 1 | 2 |
| 3 | 3 | 2 | 3 |
| 4 | 4 | 3 | 4 |
| 5 | 5 | 4 | 5 |
| 6 | 6 | 5 | 6 |
| 7 | 7 | 6 | 7 |
| 8 | 8 | 7 | 8 |
| 9 | 9 | 8 | 9 |
| 10 | 10 | 9 | 10 |
| 11 | 11 | 10 | 11 |
| 12 | 12 | 11 | 12 |

Important boundary:

- That pass opened only the Rytm input port.
- That pass sent no MIDI.
- That pass proves observation, not outbound software send correctness.

Current code fact to reconcile before active validation:

- `rytm_randomizer.devices.strategies.analog_rytm_message_renderer.RYTM_DEFAULT_CHANNEL` is `0`.
- `AnalogRytmMessageRenderer(channel=N)` can render messages on any valid channel `0..15`.
- The current renderer docstring says the default convention is single-channel Rytm CC emission.
- The hardware observation says track-channel output is visible as Track N -> mido channel N - 1 when the Rytm is configured for track-channel output.

The first implementation gate selected the per-track channel model for the first
outbound validation: Track N receives on MIDI channel N, rendered as mido
channel N - 1. This is a validation-session decision only; it does not change
the current renderer default or V1.34-compatible selected/default-channel
behavior.

Current command-surface check:

- `python -m rytm_randomizer.app --help` exposes `--arm` and `--dry-run`.
- `InteractiveShell` exposes the V1.34 command surface.
- A dry-run-only one-CC explicit-channel validation helper now exists:
  `python -m rytm_randomizer.app --dry-run --validate-one-cc --channel 0 --control 17 --value 64`.
- The dry-run helper records exactly one inert mock CC through
  `MockMidiSender`, opens no port, sends no MIDI, and imports no real MIDI
  library.
- An armed one-CC explicit-channel validation helper now exists:
  `python -m rytm_randomizer.app --arm --validate-one-cc --channel 0 --control 17 --value 64`.
- The armed helper prompts for the MIDI output port, sends exactly one CC,
  closes the port, prints a confirmation, and exits.
- Real outbound 12-track validation remains limited to this one-CC helper,
  one track at a time, during an explicitly approved disposable-kit hardware
  session.

Hardware validation result:

- On 2026-05-26, the explicit armed one-CC helper was run against the Analog
  Rytm MKII over USB using output port `Elektron Analog Rytm MKII 1`.
- Tracks 1 through 12 were validated one at a time with CC 17 / value 64.
- The operator confirmed that each expected pad changed, no other pad changed,
  and no weird behavior occurred.
- Evidence file:
  `docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md`.

## File Structure

- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
  - Add this plan as the linked next outbound-validation gate.
- Modify: `docs/STATUS.md`
  - Record that the outbound validation plan exists and hardware execution is still not performed by the plan.
- Modify: `tests/test_devices_strategies_message_renderer.py`
  - Add mock-only proof that `AnalogRytmMessageRenderer(channel=N)` preserves channels `0..11`.
- Create: `tests/test_rytm_outbound_channel_matrix.py`
  - Add low-level mock-only proof that `midi_io.send_cc(..., channel=N)` records channels `0..11` through `MockMidiSender`.
- Created after explicit approval:
  `docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md`
  - Manual evidence table for the real hardware run.

No active CLI command, SysEx helper, broad port discovery helper, or unattended
sender implementation is created by this plan. The only runtime command-surface
changes are one-CC validation helpers for dry-run proof and explicitly armed
manual hardware validation.

## Safety Boundaries

- No real MIDI during mock-only tests.
- No output port opening during mock-only tests.
- No hardware required during mock-only tests.
- No profile 4 expansion.
- No Pads 5-12 mutation engine expansion.
- No Analog Four validation.
- No scenes.
- No global mutation.
- No pattern, project, kit-save, transport, clock, or SysEx behavior.
- No bypass of `--arm` for real hardware validation.
- No unattended hardware send.

---

### Task 1: Record The Outbound Receive-Model Decision

**Files:**
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Add a short decision note to the manual validation doc**

Add this text under the 2026-05-26 passive USB input validation section:

```markdown
Outbound validation decision:

- The passive input pass observed Track N as mido channel N - 1 when the Rytm outputs track-channel MIDI.
- The current renderer default remains channel 0 because V1.34 behavior was built around the operator-selected/default channel.
- The first all-12 outbound validation will use the per-track channel model: Track N receives on MIDI channel N, rendered as mido channel N - 1.
- This is a validation-session decision only. It does not change the current renderer default or the V1.34-compatible selected/default-channel behavior.
- If any track fails to respond on the expected per-track channel, stop the validation and fall back to a separate selected/default-channel investigation.
- Do not treat the passive input observation as proof of outbound receive behavior until the armed outbound validation confirms it.
```

- [ ] **Step 2: Add a status entry**

At the top of `docs/STATUS.md` under `## Recent Cleanup`, add:

```markdown
- 2026-05-26: First outbound 12-track CC validation plan created. The plan
  selects the per-track channel model for the first validation pass while
  preserving the existing selected/default-channel runtime behavior. It
  requires mock-only channel tests before any disposable-kit armed hardware
  pass.
```

- [ ] **Step 3: Verify the docs mention the unresolved output boundary**

Run:

```powershell
rg -n "outbound receive|per-track channel|selected/default channel|First outbound" docs/MANUAL_HARDWARE_VALIDATION.md docs/STATUS.md
```

Expected:

- The manual validation doc contains the receive-model decision text.
- `docs/STATUS.md` contains the first outbound validation plan entry.

- [ ] **Step 4: Commit the docs decision**

```powershell
git add docs/MANUAL_HARDWARE_VALIDATION.md docs/STATUS.md docs/superpowers/plans/2026-05-26-first-outbound-12-track-cc-validation.md
git commit -m "Document first outbound Rytm validation plan"
```

---

### Task 2: Add Mock-Only Low-Level Channel Matrix Test

**Files:**
- Create: `tests/test_rytm_outbound_channel_matrix.py`

- [ ] **Step 1: Write the failing low-level mock test**

Create `tests/test_rytm_outbound_channel_matrix.py`:

```python
"""Mock-only outbound Rytm channel matrix tests.

These tests prove the low-level CC sender can represent channels 0..11 without
opening real MIDI ports. They do not validate hardware receive behavior.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def _no_sleep(_seconds: float) -> None:
    return None


def test_send_cc_records_track_channel_matrix_with_mock_sender() -> None:
    from rytm_randomizer.midi_io import send_cc
    from rytm_randomizer.mock_midi import MockMidiSender

    for channel in range(12):
        sender = MockMidiSender()

        send_cc(sender, 17, 64, channel=channel, sleep=_no_sleep)

        assert len(sender.messages) == 1
        message = sender.messages[0]
        assert message.type == "control_change"
        assert message.channel == channel
        assert message.control == 17
        assert message.value == 64


def test_send_cc_mock_channel_matrix_imports_no_real_midi_library() -> None:
    import sys

    sys.modules.pop("mido", None)

    from rytm_randomizer.midi_io import send_cc
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    send_cc(sender, 17, 64, channel=11, sleep=_no_sleep)

    assert "mido" not in sys.modules
```

- [ ] **Step 2: Run the new test**

Run:

```powershell
python -m pytest tests/test_rytm_outbound_channel_matrix.py -n 0
```

Expected:

- The tests pass if `send_cc` already preserves explicit channels through `MockMidiSender`.
- If a test fails, stop and inspect the failure before changing code.

- [ ] **Step 3: Commit the mock-only low-level proof**

```powershell
git add tests/test_rytm_outbound_channel_matrix.py
git commit -m "Add mock outbound Rytm channel matrix test"
```

---

### Task 3: Add Mock-Only Renderer Channel Matrix Test

**Files:**
- Modify: `tests/test_devices_strategies_message_renderer.py`

- [ ] **Step 1: Add a renderer channel-preservation test**

Add this test near the existing `AnalogRytmMessageRenderer` channel tests:

```python
def test_renderer_preserves_explicit_track_channels_zero_through_eleven() -> None:
    """Renderer can emit CC triples on every observed Rytm track channel."""

    from rytm_randomizer.devices.strategies import AnalogRytmMessageRenderer

    _snap, event, plan = _make_fixtures()

    for channel in range(12):
        renderer = AnalogRytmMessageRenderer(channel=channel)

        assert renderer.to_cc_triple(event, plan) == (channel, 74, 42)
        message = renderer.to_mock_message(event, plan)
        assert message.channel == channel
        assert message.control == 74
        assert message.value == 42
        assert message.metadata["pad"] == 1
        assert message.metadata["profile_key"] == "2"
        assert message.metadata["parameter"] == "FLT Frequency"
```

- [ ] **Step 2: Run the renderer test file**

Run:

```powershell
python -m pytest tests/test_devices_strategies_message_renderer.py -n 0
```

Expected:

- Existing tests still pass.
- New channel matrix test passes.
- No real MIDI library is imported.
- No port opens.

- [ ] **Step 3: Commit the renderer proof**

```powershell
git add tests/test_devices_strategies_message_renderer.py
git commit -m "Add renderer channel matrix proof"
```

---

### Task 4: Write The Manual Armed Hardware Validation Runbook

**Files:**
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`

- [ ] **Step 1: Add the manual runbook section**

Add this section after the passive USB input validation section:

```markdown
## First Outbound 12-Track CC Validation

This runbook is only for a deliberate hardware-validation session. Do not run it
during normal development. It must be performed on a disposable kit after the
mock-only channel matrix tests pass.

Preconditions:

- Full test suite passes locally.
- Git status is clean except for the validation evidence file being written.
- Analog Rytm MKII is connected over USB.
- Analog Four MKII remains off or unused.
- Current Rytm kit/project is saved.
- A disposable validation kit is loaded.
- Monitoring volume is low.
- Operator explicitly confirms the validation phase.

Validation command path:

- Use the supported `rytm-randomizer --arm` path.
- Do not run ad hoc Python one-liners that open ports.
- Do not bypass the app's arming prompt.

Per-track pass:

| Track | Target mido channel | Operator action | Expected result |
|---:|---:|---|---|
| 1 | 0 | Send one tiny CC movement | Only Track 1 changes |
| 2 | 1 | Send one tiny CC movement | Only Track 2 changes |
| 3 | 2 | Send one tiny CC movement | Only Track 3 changes |
| 4 | 3 | Send one tiny CC movement | Only Track 4 changes |
| 5 | 4 | Send one tiny CC movement | Only Track 5 changes |
| 6 | 5 | Send one tiny CC movement | Only Track 6 changes |
| 7 | 6 | Send one tiny CC movement | Only Track 7 changes |
| 8 | 7 | Send one tiny CC movement | Only Track 8 changes |
| 9 | 8 | Send one tiny CC movement | Only Track 9 changes |
| 10 | 9 | Send one tiny CC movement | Only Track 10 changes |
| 11 | 10 | Send one tiny CC movement | Only Track 11 changes |
| 12 | 11 | Send one tiny CC movement | Only Track 12 changes |

Stop immediately if:

- More than one track changes.
- The wrong track changes.
- The parameter jump is larger than expected.
- Any pattern, kit, project, transport, clock, or SysEx behavior appears.
- The operator is unsure what changed.
- Monitoring level feels unsafe.
- The current app cannot send one tiny explicit-channel CC through the
  supported `--arm` path. In that case, add and review a dedicated mock-first
  validation command before opening an output port.

2026-05-26 result: the current app exposes dedicated dry-run and armed one-CC
explicit-channel validation helpers. Hardware validation must still proceed one
track at a time, with Jose observing the Rytm and stopping on any wrong-track
or unexpected mutation.
```

- [ ] **Step 2: Run the doc test**

Run:

```powershell
python -m pytest tests/test_manual_hardware_validation_doc.py -n 0
```

Expected: PASS.

- [ ] **Step 3: Commit the manual runbook**

```powershell
git add docs/MANUAL_HARDWARE_VALIDATION.md
git commit -m "Add first outbound Rytm validation runbook"
```

---

### Task 5: Run Mock-Only Verification Gate

**Files:**
- No file changes.

- [ ] **Step 1: Run focused tests**

```powershell
python -m pytest tests/test_rytm_outbound_channel_matrix.py tests/test_devices_strategies_message_renderer.py tests/test_manual_hardware_validation_doc.py -n 0
```

Expected: PASS.

- [ ] **Step 2: Run architecture gate**

```powershell
python -m pytest tests/architecture/ -q
```

Expected: PASS.

- [ ] **Step 3: Run full suite if time allows**

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 4: Confirm no accidental hardware behavior was introduced**

```powershell
rg -n "import mido|open_output|open_port|send_messages|--hardware-test|send-command|execute-command" rytm_randomizer tests docs
```

Expected:

- No new top-level `import mido`.
- No new active CLI command.
- No new hardware-test command.
- Existing `--arm` and real MIDI boundary references may appear.

---

### Task 6: Manual Hardware Validation Evidence, Only After Explicit Approval

**Files:**
- Create: `docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md`

- [ ] **Step 1: Create the evidence document**

Create `docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md`:

```markdown
# Outbound 12-Track CC Validation Results - 2026-05-26

## Preconditions

- Disposable kit loaded: yes
- Rytm kit/project saved first: yes
- Monitoring volume lowered: yes
- Analog Four unused/off: yes
- Full test suite green before hardware: yes
- Operator explicitly armed validation: yes

## Results

| Track | Target mido channel | CC | Value movement | Expected track changed | Observed track changed | Pass |
|---:|---:|---:|---|---:|---:|---|
| 1 | 0 | 17 | tiny reversible movement | 1 | 1 | yes |
| 2 | 1 | 17 | tiny reversible movement | 2 | 2 | yes |
| 3 | 2 | 17 | tiny reversible movement | 3 | 3 | yes |
| 4 | 3 | 17 | tiny reversible movement | 4 | 4 | yes |
| 5 | 4 | 17 | tiny reversible movement | 5 | 5 | yes |
| 6 | 5 | 17 | tiny reversible movement | 6 | 6 | yes |
| 7 | 6 | 17 | tiny reversible movement | 7 | 7 | yes |
| 8 | 7 | 17 | tiny reversible movement | 8 | 8 | yes |
| 9 | 8 | 17 | tiny reversible movement | 9 | 9 | yes |
| 10 | 9 | 17 | tiny reversible movement | 10 | 10 | yes |
| 11 | 10 | 17 | tiny reversible movement | 11 | 11 | yes |
| 12 | 11 | 17 | tiny reversible movement | 12 | 12 | yes |

## Stop Conditions Encountered

- None.

## Decision

- Outbound 12-track CC channel validation passed for this disposable-kit run.
- Broader mutation behavior remains separately gated.
```

If any row fails, replace the matching `Pass` cell with `no`, record the observed track, and stop the validation. Do not continue through the rest of the tracks after a wrong-track event.

- [ ] **Step 2: Commit evidence only after the run**

```powershell
git add docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md
git commit -m "Record outbound Rytm hardware validation results"
```

---

## Self-Review

- Spec coverage: the plan separates passive input proof from outbound send proof, includes mock-only gates, defines the real hardware runbook, and preserves the safety boundary.
- Placeholder scan: the plan contains no open-ended implementation placeholders. The only branch is an explicit stop condition: if wrong-track behavior appears, stop and record the failure.
- Type and API consistency: referenced APIs exist today: `midi_io.send_cc`, `MockMidiSender`, `AnalogRytmMessageRenderer`, `RytmPlanEvent`, `RytmMutationPlan`, and `RytmKitSnapshot`.

## Execution Recommendation

Implement Tasks 1-5 before any real outbound hardware validation. Run Task 6 only after Jose explicitly confirms a disposable-kit hardware validation session.

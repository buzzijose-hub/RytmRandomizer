# Analog Four First Outbound Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` where tasks are independent, or
> `superpowers:executing-plans` for serial execution. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Prepare the first safe Analog Four MKII outbound validation path
without guessing CC values, widening the Rytm command helper, or touching
hardware before the operator is present.

**Architecture:** Follow the existing Device + Strategy seam. Analog Four work
belongs under `rytm_randomizer/devices/analog_four.py`,
`rytm_randomizer/devices/strategies/analog_four_*.py`, and passive reports
under `rytm_randomizer/reports/`. The current slice is documentation-only; any
future code must be mock-first and device-explicit.

**Tech Stack:** Python 3.11, pytest, existing `Device` Protocol, existing
`MockMidiSender`, existing passive CLI/report registry, official Analog Four
manual or observed A4 input messages for CC/channel facts.

---

## Current Evidence

- Rytm outbound 12-track one-CC validation passed on 2026-05-26.
- Analog Four device registration and passive strategies already exist.
- Analog Four has not been outbound hardware-validated.
- The current `--validate-one-cc` helper is Rytm-shaped and must not be reused
  as an A4 helper without a separate gate.
- No exact Analog Four CC is approved by this plan.

## Workstream Shape

This is intentionally serial until the candidate facts are known:

1. Review this plan.
2. Observe/manual-confirm A4 channel and CC facts.
3. Add mock-only A4 candidate proof.
4. Add an A4-specific dry-run helper only if needed.
5. Run manual A4 hardware validation only with Jose present.

Do not dispatch parallel implementation until Gate 2 has exact facts. Parallel
work before that point would just produce confident guesses, which is the wrong
failure mode for hardware.

---

### Task 1: Review And Accept The Design

**Files:**

- Read: `docs/superpowers/specs/2026-05-27-analog-four-first-outbound-validation-design.md`
- Read: `docs/MANUAL_HARDWARE_VALIDATION.md`

- [ ] **Step 1: Confirm the design stays planning-only**

Verify:

- no code files are changed,
- no tests are changed,
- no real MIDI is imported,
- no ports are opened,
- no hardware is required.

- [ ] **Step 2: Confirm the current A4 code surface**

Run:

```powershell
python -m pytest tests/test_analog_four_device.py -n 0 -q
```

Expected:

- Analog Four device registration tests pass.
- This does not open MIDI ports or send MIDI.

- [ ] **Step 3: Commit the docs-only planning slice**

```powershell
git add docs/superpowers/specs/2026-05-27-analog-four-first-outbound-validation-design.md `
        docs/superpowers/plans/2026-05-27-analog-four-first-outbound-validation.md `
        docs/MANUAL_HARDWARE_VALIDATION.md `
        docs/STATUS.md

git commit -m "Add Analog Four first outbound validation plan"
```

---

### Task 2: Passive A4 Input Observation Plan

**Files:**

- Future create: `docs/hardware-validation/YYYY-MM-DD-a4-passive-input-observation.md`

- [ ] **Step 1: Prepare hardware manually**

Operator actions:

- connect Analog Four MKII over USB,
- keep Rytm unused or disconnected for this pass,
- lower monitoring volume,
- confirm no external clock/transport control is being tested,
- set A4 MIDI settings so track output can be observed if available.

- [ ] **Step 2: Open input only**

Use an input-listener path that opens only the Analog Four input port. Do not
open output ports.

Expected:

- A4 input port is visible.
- No output port is opened.
- No MIDI is sent by the software.

- [ ] **Step 3: Observe one track at a time**

For tracks 1 through 4:

- select/focus the track manually on the A4,
- move one known hardware control slowly,
- record the observed mido channel,
- record the observed CC number if present,
- record whether the observation is stable.

- [ ] **Step 4: Stop on ambiguity**

Stop if:

- the track/channel mapping is not stable,
- the CC number is not visible,
- multiple tracks appear to report at once,
- the A4 settings are unclear.

---

### Task 3: Mock-Only A4 Candidate Proof

**Files:**

- Future modify/create only after Task 2:
  - `tests/test_analog_four_outbound_candidate_matrix.py`
  - optional passive report under `rytm_randomizer/reports/`

- [ ] **Step 1: Lock candidate facts from Task 2**

Record:

- target device: `analog_four_mk2`,
- approved tracks,
- approved mido channels,
- approved CC,
- approved value range,
- blocked actions.

- [ ] **Step 2: Add tests before runtime changes**

Tests must prove:

- the candidate message shape is deterministic,
- tracks outside the approved A4 range are rejected,
- unapproved CCs are rejected,
- `MockMidiSender` records messages in order,
- no real MIDI library is imported,
- no ports are opened,
- no MIDI is sent.

- [ ] **Step 3: Add passive report if useful**

If operator visibility is needed, add a passive A4 outbound-candidate report.
It may print the candidate matrix and replay instructions, but it must not send
anything.

---

### Task 4: A4 Dry-Run Helper

**Files:**

- Future modify only after Task 3:
  - `rytm_randomizer/app.py`
  - focused tests for dry-run behavior

- [ ] **Step 1: Keep A4 separate from the Rytm helper**

Do not widen the current Rytm-shaped `--validate-one-cc` behavior casually.
Either:

- add a device-explicit validation mode, or
- add a separate A4-specific validation helper.

- [ ] **Step 2: Enforce safe dry-run behavior**

The dry-run helper must:

- require `--dry-run`,
- use `MockMidiSender`,
- reject missing device,
- reject non-A4 device ids,
- reject channels outside approved A4 channels,
- reject unapproved CCs,
- open no ports,
- send no MIDI.

- [ ] **Step 3: Verify passive defaults**

Run:

```powershell
python -m pytest tests/architecture/test_real_midi_passive_cli_safety.py -q
python -m pytest tests/test_analog_four_device.py -n 0 -q
```

Expected:

- passive CLI remains read-only,
- A4 device tests still pass.

---

### Task 5: Manual A4 Armed Validation

**Files:**

- Future create only during an approved hardware session:
  - `docs/hardware-validation/YYYY-MM-DD-a4-first-outbound-cc-results.md`

- [ ] **Step 1: Confirm explicit approval**

Do not run this task unless Jose is present and explicitly starts the A4
hardware-validation phase.

- [ ] **Step 2: Pre-hardware checklist**

Confirm:

- full tests pass,
- git status is clean,
- exact A4 output port is known,
- exact track/channel/CC/value candidate is known,
- current A4 project/sound state is disposable or saved,
- monitoring volume is low,
- Rytm is not targeted by this pass.

- [ ] **Step 3: Validate one track at a time**

For tracks 1 through 4:

- send exactly one approved CC to exactly one target channel,
- wait for operator confirmation,
- record pass/fail evidence before moving to the next track.

- [ ] **Step 4: Stop conditions**

Stop immediately if:

- wrong track changes,
- more than one track changes,
- nothing changes and the reason is unclear,
- any pattern, kit, project, transport, clock, or SysEx behavior appears,
- the operator is unsure what changed.

---

## Done Criteria

- The A4 design and plan are reviewed.
- Any future A4 implementation remains mock-first.
- No A4 hardware send happens without Jose present.
- No exact CC is selected until manual-backed or observed.
- Rytm V1.34 parity remains untouched.
- Passive commands remain passive.

## Recommended Next Step

Review and accept this A4 first outbound validation plan. Then run the passive
A4 input observation only when Jose is in the studio with the Analog Four ready.

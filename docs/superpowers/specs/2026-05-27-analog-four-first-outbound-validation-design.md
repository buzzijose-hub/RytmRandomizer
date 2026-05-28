# Analog Four First Outbound Validation Design

## Purpose

Define the first safe path toward Analog Four MKII outbound validation without
implementing it in this slice.

This design is planning-only. It does not add an Analog Four hardware command,
does not open MIDI ports, does not send MIDI, and does not select an exact CC
number by guesswork.

## Current Baseline

- Branch: `codex/a4-first-outbound-validation-plan`
- Base: `origin/modularize-v1.34`
- Current Rytm outbound evidence:
  `docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md`
- Current Analog Four status: passive/device-strategy support exists, but no
  Analog Four hardware validation has been run.
- Hardware status for this design: hardware is not required.

## Existing Code Facts

The current codebase already has an Analog Four device surface:

- `rytm_randomizer/devices/analog_four.py`
  - `device_id = "analog_four_mk2"`
  - `display_name = "Elektron Analog Four MKII"`
  - `default_midi_channel = 0`
  - `track_count = 4`
  - `report_header = "RytmRandomizer Analog Four MK2 Guarded Send"`
- `rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py`
- `rytm_randomizer/devices/strategies/analog_four_mutation_planner.py`
- `rytm_randomizer/devices/strategies/analog_four_message_renderer.py`
- `rytm_randomizer/devices/strategies/analog_four_offset_manifest.py`
- `rytm_randomizer/devices/strategies/analog_four_style_snapshot_routing.py`
- `rytm_randomizer/devices/strategies/analog_four_style_mutation_intent.py`
- `rytm_randomizer/devices/strategies/analog_four_style_mutation_mock_preview.py`

The existing one-CC validation helper in `rytm_randomizer/app.py` is currently
Rytm-shaped. Its help text and validation range are written around Rytm tracks
0 through 11. It must not be treated as an approved Analog Four validation
surface without a separate design and implementation gate.

## What The Rytm Pass Proved

The 2026-05-26 Rytm pass proved that one explicit CC can be sent to each of the
12 Rytm track channels in this studio setup:

- mido channel 0 targeted Rytm track 1.
- mido channel 1 targeted Rytm track 2.
- This continued through mido channel 11 targeting Rytm track 12.
- The operator confirmed only the intended pad changed in each pass.

That result does not prove Analog Four behavior. Analog Four must get its own
manual-backed channel and CC candidate validation.

## Open Analog Four Questions

These must be answered before any A4 outbound send:

- Which USB MIDI output port name is the correct Analog Four output on Jose's
  Windows studio machine?
- Which receive-channel setup is active on the Analog Four?
- Does track 1 through track 4 map to mido channels 0 through 3 in the current
  A4 settings?
- Which single CC is safe, reversible, and easy for the operator to observe?
- Does moving the matching hardware control produce a useful input message that
  can confirm the CC number before outbound testing?
- Does the chosen test avoid patterns, transport, clock, project writes, kit
  saves, SysEx, and any broad mutation behavior?

If any answer is uncertain, the validation blocks.

## Candidate CC Rule

Do not invent an Analog Four CC number.

The first Analog Four CC candidate must come from at least one of:

- the official Analog Four MKII manual,
- an observed inbound message from the A4 while the operator moves a known
  control, or
- a current code/data table that is already documented as Analog Four-specific
  and is reviewed before hardware use.

If the manual and observation disagree, stop and write a separate decision note.

## Validation Ladder

### Gate 0: Documentation Approval

Create and review this design plus the implementation plan. No code or hardware
behavior is added in Gate 0.

### Gate 1: Passive A4 Input Observation

With the operator present:

- open only the A4 MIDI input port,
- select or focus A4 tracks manually on the hardware,
- move one known low-risk control per track,
- record observed channels and control numbers,
- send no MIDI.

This proves observation only. It does not authorize outbound sends.

### Gate 2: Mock-Only A4 Candidate Proof

After Gate 1, add tests and passive reports that prove the intended candidate
message shape in memory only:

- device id: `analog_four_mk2`
- tracks: 1 through 4
- mido channels: only the manually observed or manual-backed channels
- control: only the approved candidate CC
- value: a small deterministic value
- sender: `MockMidiSender` only

No real MIDI library import, port opening, or hardware send is allowed.

### Gate 3: A4 Dry-Run Helper

Only after Gate 2, add an A4-specific dry-run validation surface if needed.
It must:

- be device-explicit,
- reject non-A4 device ids,
- reject channels outside the approved A4 range,
- reject unapproved CCs,
- use `MockMidiSender`,
- open no ports,
- send no MIDI.

The current Rytm one-CC helper should not be widened casually.

### Gate 4: Manual A4 Armed Validation

Only after Gate 3 and explicit user approval:

- use a disposable A4 sound/kit/project state,
- lower monitoring volume,
- select the exact A4 output port,
- send exactly one approved CC to one A4 track at a time,
- wait for the operator to confirm the intended track changed,
- stop immediately on any ambiguity.

## First Hardware Candidate Constraints

The first A4 outbound candidate must be:

- tiny,
- isolated,
- reversible,
- obvious to the operator,
- limited to one track at a time,
- limited to one CC,
- limited to one value,
- blocked unless the exact A4 port, channel, and CC are known.

## Explicit Non-Goals

- No Analog Four hardware test in this slice.
- No Rytm hardware test in this slice.
- No real MIDI import changes.
- No port opening.
- No MIDI sending.
- No active CLI command.
- No scene execution.
- No transport, clock, pattern, project, or kit-save behavior.
- No SysEx.
- No GUI change.
- No profile expansion.
- No 12-pad Rytm expansion.

## Stop Conditions

Stop immediately if:

- the A4 channel model is unclear,
- the A4 CC candidate is not manual-backed or observed,
- the output port is unclear,
- more than one track changes,
- the wrong track changes,
- nothing changes and the reason is unclear,
- a parameter jump feels too large,
- any pattern, transport, clock, project, kit-save, or SysEx behavior appears,
- the operator is unsure what changed,
- monitoring level feels unsafe.

## Decision

Analog Four outbound validation should start with a planning and observation
gate, not with an immediate hardware send.

The next implementation branch should be mock-only unless Jose explicitly
starts an A4 hardware-validation session and is present to observe the result.

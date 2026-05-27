# Second Outbound CC Validation Design

## Purpose

Define the next hardware-facing validation step after PR #133 without running
hardware. The first outbound pass proved that the existing one-CC helper can
target Rytm tracks 1 through 12 with CC 17 / value 64. The second pass should
prove repeatability before we widen the parameter or musical mutation scope.

This document is a planning and passive-readiness gate only. It does not
authorize an immediate hardware run, open ports, send MIDI, touch Analog Four,
add SysEx, or add unattended active behavior.

## Current Baseline

- Base branch: `modularize-v1.34`
- Current merged milestone: PR #133, `Add first outbound Rytm CC validation`
- Latest baseline commit when this design was written: `8bd211af`
- Existing validation helper:
  `python -m rytm_randomizer.app --arm --validate-one-cc --channel N --control 17 --value 64`
- Existing dry-run helper:
  `python -m rytm_randomizer.app --dry-run --validate-one-cc --channel N --control 17 --value 64`
- Passive repeatability readiness report:
  `python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report --json`
- Hardware evidence already recorded:
  `docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md`

## Recommended Next Hardware Pass

Use a second all-12-track repeatability pass with the same known helper and the
same CC shape:

- mido channels: `0..11`
- Rytm tracks: `1..12`
- control: `17`
- value: `64`
- send count: exactly one CC per track
- observation: expected pad changes, no other pad changes, no weird behavior

This keeps the next hardware pass small and lets us answer the most important
question first: was the successful all-12 mapping stable, or was it a one-off
studio result?

## Deferred Options

The following are intentionally not part of the second pass:

- Testing a new CC number across all 12 tracks.
- Testing multiple values for one CC.
- Testing any full mutation command.
- Testing scene or group mutation.
- Testing SysEx, kit save, project writes, pattern changes, clock, or transport.
- Testing Analog Four.

A new CC number should require a separate candidate note that identifies the
source of truth, expected parameter meaning, safe value range, and stop
conditions. The second validation pass should not mix repeatability testing with
new-parameter discovery.

## Safety Model

The existing app boundary remains the only real MIDI path:

- Passive CLI remains read-only.
- `rytm-outbound-cc-repeatability-report` emits text/JSON checklist metadata
  only.
- Dry-run path records to `MockMidiSender`.
- Armed path prompts for the output port.
- Armed path sends exactly one CC and exits.
- No unattended loop is introduced.
- Hardware validation remains one track at a time with operator observation.

## What This Pass Would Prove

- The first outbound channel result is repeatable in the current studio setup.
- Track N still responds to mido channel N - 1 for the one-CC helper.
- The one-message armed path still opens the selected port, sends one CC,
  closes the port, and exits.
- No cross-pad mutation appears during a repeated validation pass.

## What This Pass Would Not Prove

- It does not prove every Rytm CC parameter.
- It does not prove every machine engine.
- It does not prove full mutation behavior.
- It does not prove scene, group, pattern, transport, clock, kit-save, project,
  or SysEx behavior.
- It does not prove Analog Four behavior.
- It does not authorize live performance use.

## Acceptance Criteria

The planning slice is accepted when:

- The repeatability pass is documented as the recommended next hardware test.
- The passive CLI can emit the 12-step repeatability checklist as text or JSON.
- Any new CC/parameter testing is explicitly parked behind a separate candidate
  approval.
- Manual hardware validation docs include the second-pass runbook.
- Project status records that this is passive/report-only.
- Tests/verification pass without requiring hardware.

## Decision

Proceed with a passive second outbound CC validation readiness report and
manual-test plan. Do not run hardware as part of this slice. Do not expand
parameter scope yet.

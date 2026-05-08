# Passive CLI Safety Regression Sweep Plan Review

## Purpose

Review and accept `Docs/PASSIVE_CLI_SAFETY_REGRESSION_SWEEP_PLAN.md` as the
Packet 4 planning gate.

This is a documentation-only review checkpoint. It adds no tests, runtime
behavior, CLI behavior, MIDI behavior, port opening, package metadata, active
execution, or hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 6aca34f Add passive CLI safety regression sweep plan

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 active-boundary metadata strengthening complete and reviewed
- Packet 2 active-boundary report alignment complete and reviewed
- Packet 3 fake-provider adapter guard strengthening complete and reviewed
- Packet 4 passive CLI safety regression sweep plan created
- Packet 4 plan now being reviewed
- hardware not required

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off

## Review Decision

`Docs/PASSIVE_CLI_SAFETY_REGRESSION_SWEEP_PLAN.md` is accepted as the current
Packet 4 planning gate.

The accepted plan does not authorize implementation by itself. Packet 4
remains unimplemented until a separate tiny test-only implementation slice is
explicitly started.

The accepted plan does not authorize turning hardware on.

## Accepted Test-Only Scope

Future Packet 4 implementation may add or strengthen passive CLI safety
regression tests proving:

- representative passive CLI commands remain read-only
- passive CLI commands do not import `mido`
- passive CLI commands do not import `rtmidi`
- passive CLI commands do not import `pythonrtmidi`
- passive CLI commands do not import `rytm_randomizer.real_midi_adapter`
- passive CLI commands do not construct `RealMidiPortProvider`
- passive CLI commands do not construct `RealMidiSender`
- passive CLI commands do not call `build_real_midi_sender`
- passive CLI commands do not open output ports
- passive CLI commands do not send MIDI
- passive CLI commands do not dispatch commands
- passive CLI commands do not execute scenes
- passive CLI commands do not expose `execute-command`
- passive CLI commands do not expose `send-command`
- passive CLI commands do not expose `hardware-test`

The first implementation slice should remain small and test-only.

## Accepted Future Ownership

Allowed future implementation files remain:

- `tests/test_real_midi_passive_cli_safety.py`
- `tests/test_cli.py`

Only update `Scripts/closeout_check.ps1` if a new test file is created and not
already included in closeout.

## Confirmed Frozen Scope

This review keeps the following frozen:

- new CLI commands
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- command dispatch
- command execution
- scene execution
- active-boundary evaluation from passive CLI commands
- sender construction from passive CLI commands
- real MIDI dependencies
- `mido`
- `rtmidi`
- package metadata changes
- MIDI port discovery
- MIDI port opening
- MIDI sending
- hardware validation
- hardware behavior
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- profile `"3"` active-boundary support
- profile `"4"` implementation

## Preconditions Before Implementation

Before any Packet 4 implementation slice:

- Git status must be clean.
- Full closeout must pass.
- V1.34 reference diff must be empty.
- Package metadata diff must be empty.
- Package metadata files must remain absent unless separately approved.
- This review checkpoint must be committed.
- Implementation must remain tests-only.
- Passive CLI must remain read-only.
- No real MIDI libraries may be added.
- No MIDI ports may open.
- No hardware may be required.

## Safe Next Options

- Option A: pause at this clean Packet 4 review checkpoint.
- Option B: implement a tiny Packet 4 test-only passive CLI safety regression
  slice.
- Option C: create a more detailed micro-implementation plan if needed.
- Option D: return to broader project-level documentation.

## Recommendation

Proceed next with a tiny Packet 4 test-only implementation slice only if it
stays limited to passive CLI safety regression tests.

Do not add real MIDI. Do not add active CLI commands. Do not open ports. Do
not turn on hardware.

## Decision

Packet 4 passive CLI safety regression sweep plan is accepted.

Hardware remains off. Runtime behavior remains unchanged.

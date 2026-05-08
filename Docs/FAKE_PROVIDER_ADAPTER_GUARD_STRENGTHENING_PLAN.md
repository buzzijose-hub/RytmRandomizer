# Fake-Provider Adapter Guard Strengthening Plan

## Purpose

Define Packet 3 from the mock/fake-provider active-boundary strengthening
sequence: fake-provider adapter guard strengthening.

This document is planning-only. It does not add tests, edit runtime code,
change CLI behavior, send MIDI, open ports, add active execution, add real MIDI
dependencies, change package metadata, or authorize hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 3715730 Add active boundary report metadata alignment review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 active-boundary metadata strengthening complete and reviewed
- Packet 2 active-boundary report metadata alignment complete and reviewed
- Packet 3 fake-provider adapter guard strengthening now being planned
- fake-provider-only real MIDI adapter boundary remains isolated
- hardware not required

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off

## Current Adapter State

Current module:

- `rytm_randomizer/real_midi_adapter.py`

Current tests:

- `tests/test_real_midi_adapter_boundary.py`

Current closeout label:

- `=== Test: Real MIDI Adapter Boundary ===`

Current adapter behavior:

- imports no real MIDI library at module import time
- exposes `RealMidiPortProvider`
- exposes `RealMidiSender`
- exposes `build_real_midi_sender(provider, port_name)`
- requires an explicit injected provider
- requires an explicit port name
- uses injected fake output ports in tests
- translates supported mock `MidiMessage` objects into backend-shaped dicts
- rejects unsupported message types
- reports `sent_real_midi=False`
- records fake-provider metadata
- does not discover hardware
- does not open real ports
- does not send real MIDI

## Packet 3 Goal

Packet 3 should make the fake-provider-only adapter boundary harder to misuse
without moving toward real MIDI.

The implementation should remain a tiny test-first slice. It should strengthen
safe-failure behavior and fake-provider-only guarantees around the existing
adapter surface.

The adapter must remain fake-provider-only. It must not import `mido`, `rtmidi`,
or any real MIDI library. It must not add package metadata. It must not discover
hardware, open ports, send MIDI, or require hardware.

## Allowed Ownership

Allowed implementation files for Packet 3:

- `rytm_randomizer/real_midi_adapter.py`
- `tests/test_real_midi_adapter_boundary.py`

Do not edit unless separately approved:

- `rytm_randomizer/active_boundary.py`
- `rytm_randomizer/active_boundary_report.py`
- `rytm_randomizer/cli.py`
- `Scripts/closeout_check.ps1`
- `rytm_hybrid_randomizer_v134.py`
- package metadata files
- docs, except for the later checkpoint/review after implementation

## Proposed Test-First Scope

Packet 3 implementation should add tests before code for a small subset of the
following guardrails.

Recommended first test additions:

- provider copies injected `output_names` and `ports` so caller mutation cannot
  change the provider after construction
- `list_output_names()` returns a tuple and cannot be used to mutate provider
  state
- configured but missing fake port fails with
  `unavailable_midi_output_port: <name>`
- empty or non-string port name fails safely with `midi_output_port_required`
- a sequence containing an unsupported message type emits no fake messages
  before failing
- send result metadata remains copied and immutable
- translated message metadata is copied so later source-message mutation cannot
  mutate fake-port records

Keep the first implementation small. If this list is too large for one clean
slice, split it and implement only the highest-value two or three tests first.

## Proposed Future Assertions

Future tests should continue to assert:

- importing `rytm_randomizer.real_midi_adapter` prints nothing
- importing the adapter imports no `mido`, `rtmidi`, or `pythonrtmidi`
- `build_real_midi_sender(provider=None, ...)` fails safely
- unknown ports fail safely
- unavailable fake ports fail safely
- unsupported message types fail safely
- no fake messages are recorded when validation fails
- passive imports do not load the adapter or real MIDI modules
- passive CLI commands do not load the adapter or real MIDI modules
- passive source files do not reference adapter or port affordances
- profiles `"3"` and `"4"` remain unsupported by the active boundary
- V1.34 reference diff remains empty
- package metadata files remain absent

## Behavior That Must Stay Frozen

Packet 3 must not add:

- profile `"3"` active-boundary support
- profile `"4"` implementation
- scenes
- global mutations
- command dispatch
- command execution
- scene execution
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
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

## Required TDD Flow

Packet 3 implementation should follow TDD:

1. Add one failing fake-provider guard test.
2. Run `python .\tests\test_real_midi_adapter_boundary.py` and confirm the
   expected failure.
3. Add the minimal adapter change needed to pass.
4. Run `python .\tests\test_real_midi_adapter_boundary.py` again.
5. Repeat only while the slice remains small.
6. Run full closeout before commit.

Do not write adapter code before the failing test exists.

## Required Verification

Packet 3 implementation must run:

```powershell
python .\tests\test_real_midi_adapter_boundary.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected state:

- targeted adapter boundary tests pass
- full closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- package metadata files remain absent
- git status is clean after commit

## Parallelization Position

Parallel implementation is not recommended for the first Packet 3 slice.

The allowed ownership is concentrated in one adapter module and one test file.
Parallel agents would likely collide on the same files.

Safe parallel review may be useful later only if split into independent lanes:

- one agent reviews fake-provider adapter guard tests
- one agent reviews passive CLI/source import safety after implementation

Do not run parallel implementation against the same files.

## Recommendation

Review and accept this Packet 3 plan next.

After acceptance, implement a tiny test-first fake-provider adapter guard
strengthening slice only if the selected tests remain small and fake-provider
only.

Do not widen active-boundary support. Do not add real MIDI. Do not turn on
hardware.

## Decision

Packet 3 should strengthen fake-provider adapter guard coverage before any
future real dependency decision.

No implementation is added in this slice.

Hardware remains off. Runtime behavior remains unchanged.

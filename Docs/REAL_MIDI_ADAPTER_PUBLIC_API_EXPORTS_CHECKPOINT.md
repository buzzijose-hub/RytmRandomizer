# Real MIDI Adapter Public API Exports Checkpoint

## Purpose

Record the tiny real MIDI adapter boundary API alignment slice.

This adds an explicit public API export list to the import-safe adapter
boundary. It does not add a real MIDI dependency, open ports, send MIDI, wire
active execution, or require hardware.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `6a5cc5a Add Pad 4 lane API checkpoint`

Implementation milestone:

- `e32defc Add real MIDI adapter public API exports`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Files Changed

Implementation files:

- `rytm_randomizer/real_midi_adapter.py`
- `tests/test_real_midi_adapter_boundary.py`

No closeout script update was needed because `tests/test_real_midi_adapter_boundary.py`
is already covered by:

- `=== Test: Real MIDI Adapter Boundary ===`

## Behavior

Added an explicit public API export list to the adapter boundary:

- `RealMidiDependencyError`
- `RealMidiOutputPort`
- `RealMidiPortError`
- `RealMidiPortProvider`
- `RealMidiSendError`
- `RealMidiSendResult`
- `RealMidiSender`
- `build_real_midi_sender`

The adapter remains fake-provider-only in tests and import-safe. Existing
behavior is unchanged:

- no real MIDI library import
- no `mido`
- no `rtmidi`
- no hardware discovery
- no automatic port opening
- no real MIDI sending
- passive imports do not load the adapter
- passive CLI commands do not load the adapter

## TDD Evidence

Red:

- `python .\tests\test_real_midi_adapter_boundary.py` failed because
  `rytm_randomizer.real_midi_adapter` did not expose `__all__`.

Green:

- added the minimal `__all__` list to `rytm_randomizer/real_midi_adapter.py`
- `python .\tests\test_real_midi_adapter_boundary.py` passed
- `python .\tests\test_real_midi_import_safety.py` passed
- `python .\tests\test_real_midi_passive_cli_safety.py` passed

## Confirmed Boundaries

This milestone adds no:

- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- runtime execution
- dispatch
- command execution
- mutation execution
- active CLI command
- package metadata change
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- hardware behavior

## Verification

Verified before the implementation commit:

- targeted real MIDI adapter boundary test passed
- real MIDI import safety test passed
- real MIDI passive CLI safety test passed
- full closeout passed
- V1.34 reference diff was empty
- package metadata diff was empty

## Decision

The import-safe real MIDI adapter boundary now exposes an explicit public API
without changing behavior or crossing into real MIDI/hardware execution.

Next recommended task:

- continue with another concrete passive/mock-only alignment or visibility
  slice, or pause at this clean checkpoint.

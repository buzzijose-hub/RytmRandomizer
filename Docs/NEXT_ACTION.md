# Next Action

## Current Branch

modularize-v1.34

## Current HEAD

d1df975 Add mock message mapping design spec

## Current Phase

Passive CLI / dry-run foundation.

## Current Safety State

- V1.34 reference untouched
- no MIDI
- no ports
- no dispatch
- no command execution
- no scene execution
- no hardware mutation
- no SysEx
- no GUI
- no capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion

## Hardware Status

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required for current phase

## Current Passive CLI Capability

- report
- list commands/scenes/group profiles
- search commands/scenes/group profiles
- inspect commands/scenes/group profiles
- preview commands/scenes/group profiles

## Known Safe Passive Commands

```powershell
python -m rytm_randomizer.cli report
python -m rytm_randomizer.cli list-commands
python -m rytm_randomizer.cli list-scenes
python -m rytm_randomizer.cli list-group-profiles
python -m rytm_randomizer.cli search-commands BD
python -m rytm_randomizer.cli search-scenes Wild
python -m rytm_randomizer.cli inspect-command J
python -m rytm_randomizer.cli inspect-scene S1A
python -m rytm_randomizer.cli inspect-group-profile 2
python -m rytm_randomizer.cli preview-command J
python -m rytm_randomizer.cli preview-scene S1A
python -m rytm_randomizer.cli preview-group-profile 2
```

## Next Recommended Task

Create a test-only mock message mapper scaffold for group profile 2 only,
after the accepted mock message mapping review:

- `Docs/PASSIVE_TO_ACTIVE_BOUNDARY.md`
- `Docs/PASSIVE_TO_ACTIVE_BOUNDARY_REVIEW.md`
- `Docs/ACTIVE_LAYER_DESIGN_SPEC.md`
- `Docs/ACTIVE_LAYER_DESIGN_SPEC_REVIEW.md`
- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN.md`
- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN_REVIEW.md`
- `Docs/MOCK_MIDI_SCAFFOLD_REVIEW.md`
- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md`
- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC_REVIEW.md`

The mock MIDI scaffold review accepts the test-only mock MIDI scaffold and
records that no real MIDI behavior exists:

- `rytm_randomizer/mock_midi.py`
- `tests/test_mock_midi.py`

The mapping spec defines future mock-only mapping from passive metadata to mock
MidiMessage objects. No mapper exists yet. No real MIDI, no hardware, no active
CLI command, and no port opening.

The mapping spec review accepts the design/spec for planning and sets the next
recommended task as a tiny test-only mock mapper scaffold for group profile 2
only. The scaffold must remain mock-only and must not open ports, send MIDI,
wire into active CLI behavior, or require hardware.

## Do-Not-Touch Files

- `rytm_hybrid_randomizer_v134.py`

## Closeout Command

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

## Stop Condition

- closeout passes
- `git diff -- rytm_hybrid_randomizer_v134.py` is empty
- `git status --short` is clean

## Reminder

Do not turn on Analog Rytm or Analog Four until explicitly entering a
hardware-facing validation phase.

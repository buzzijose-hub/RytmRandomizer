# Passive CLI Safety Regression Sweep Plan

## Purpose

Define Packet 4 from the mock/fake-provider active-boundary strengthening
sequence: passive CLI safety regression sweep.

This document is planning-only. It does not add tests, edit runtime code,
change CLI behavior, send MIDI, open ports, add active execution, add real MIDI
dependencies, change package metadata, or authorize hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- ee7c497 Add active-boundary strengthening progress review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 active-boundary metadata strengthening complete and reviewed
- Packet 2 active-boundary report alignment complete and reviewed
- Packet 3 fake-provider adapter guard strengthening complete and reviewed
- Packet 4 passive CLI safety regression sweep now being planned
- fake-provider-only real MIDI adapter boundary remains isolated
- hardware not required

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off

## Packet 4 Goal

Packet 4 should add focused regression coverage proving representative passive
CLI commands remain passive after the active-boundary and fake-provider adapter
strengthening work.

The goal is not to add new CLI commands. The goal is to prove existing passive
commands do not accidentally cross into active-boundary evaluation, sender
construction, real MIDI imports, port opening, MIDI sending, dispatch, or
hardware behavior.

## Current Passive CLI Commands In Scope

Representative passive commands for future coverage:

- `python -m rytm_randomizer.cli --help`
- `python -m rytm_randomizer.cli report`
- `python -m rytm_randomizer.cli list-commands`
- `python -m rytm_randomizer.cli list-scenes`
- `python -m rytm_randomizer.cli list-group-profiles`
- `python -m rytm_randomizer.cli search-commands BD`
- `python -m rytm_randomizer.cli search-scenes Wild`
- `python -m rytm_randomizer.cli search-group-profiles BD`
- `python -m rytm_randomizer.cli inspect-command J`
- `python -m rytm_randomizer.cli inspect-scene S1A`
- `python -m rytm_randomizer.cli inspect-group-profile 2`
- `python -m rytm_randomizer.cli preview-command J`
- `python -m rytm_randomizer.cli preview-scene S1A`
- `python -m rytm_randomizer.cli preview-group-profile 2`
- `python -m rytm_randomizer.cli mock-mapper-report`
- `python -m rytm_randomizer.cli active-boundary-report`

These commands must remain read-only.

## Current Safety Coverage

Closeout already includes:

- passive CLI tests
- active boundary tests
- active boundary report tests
- real MIDI import safety tests
- real MIDI passive CLI safety tests
- real MIDI adapter boundary tests

Existing coverage proves important pieces individually. Packet 4 should make
the representative passive CLI sweep clearer and more explicit after the
recent boundary strengthening sequence.

## Proposed Test-Only Scope

Future Packet 4 implementation should add or strengthen tests for:

- representative passive CLI commands exit safely
- representative passive CLI commands print deterministic passive output
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

Keep the first implementation small. If this list is too large for one clean
slice, prefer representative coverage over exhaustive duplication.

## Allowed Future Ownership

Allowed implementation files for Packet 4:

- `tests/test_real_midi_passive_cli_safety.py`
- `tests/test_cli.py`

Only update `Scripts/closeout_check.ps1` if a new test file is created and not
already included in closeout.

Do not edit unless separately approved:

- `rytm_randomizer/cli.py`
- `rytm_randomizer/active_boundary.py`
- `rytm_randomizer/active_boundary_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_hybrid_randomizer_v134.py`
- package metadata files
- runtime execution/dispatch logic

## Proposed Test Strategy

Recommended future test shape:

- run passive CLI commands in a fresh Python process
- inspect `sys.modules` after each command or command group
- assert forbidden modules are absent
- assert passive commands return expected safe exit codes
- assert stderr remains empty for successful passive commands
- assert active command names are not exposed in help or passive output
- assert passive CLI source does not reference real MIDI adapter affordances
- assert closeout still includes real MIDI passive CLI safety coverage

The test should prefer deterministic assertions over broad text scraping.

## Forbidden Runtime Changes

Packet 4 must not add:

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

## Required TDD Flow For Future Implementation

Packet 4 implementation should follow TDD:

1. Add one failing passive CLI safety regression test.
2. Run the targeted test and confirm the expected failure.
3. Add the minimal test-support or assertion adjustment needed.
4. Run the targeted test again.
5. Repeat only while the slice remains small.
6. Run full closeout before commit.

Do not write runtime code for Packet 4 unless a separately approved plan
changes the scope.

## Required Verification For Future Implementation

Any Packet 4 implementation must run:

```powershell
python .\tests\test_real_midi_passive_cli_safety.py
python .\tests\test_cli.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected state:

- targeted passive CLI safety tests pass
- passive CLI tests pass
- full closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- package metadata files remain absent
- git status is clean after commit

## Parallelization Position

Parallel implementation is not recommended for the first Packet 4 slice.

The likely ownership is concentrated in existing CLI safety tests and passive
CLI tests. Parallel review may be useful later, but implementation should stay
single-threaded unless the work is split into clearly independent test files.

## Safe Next Options

- Option A: review and accept this Packet 4 plan.
- Option B: pause at this clean planning checkpoint.
- Option C: implement a tiny Packet 4 test-only slice after review.
- Option D: return to broader project-level roadmap/progress documentation.

## Recommendation

Review and accept this Packet 4 plan next.

Do not add real MIDI. Do not add active CLI commands. Do not open ports. Do not
turn on hardware.

## Decision

Packet 4 passive CLI safety regression sweep is planned but unimplemented.

Hardware remains off. Runtime behavior remains unchanged.

# Active Boundary Public API Exports Checkpoint

## Purpose

Record the tiny active-boundary API alignment slice.

This checkpoint documents an explicit public API export list for the existing
mock-only active boundary. It does not add execution behavior, MIDI behavior,
port opening, active CLI behavior, or hardware behavior.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Implementation milestone:

- `d7cd39f Add active boundary public API exports`

Previous checkpoint:

- `0e05430 Add real MIDI adapter API checkpoint`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Files Changed By The Milestone

- `rytm_randomizer/active_boundary.py`
- `tests/test_active_boundary.py`

## Public API Now Exported

`rytm_randomizer.active_boundary` now exposes an explicit `__all__` list:

- `ACTIVE_BOUNDARY_NAME`
- `SUPPORTED_CANDIDATE`
- `SUPPORTED_SOURCE_KEY`
- `SUPPORTED_SOURCE_KIND`
- `ActiveBoundaryError`
- `ActiveBoundaryRequest`
- `ActiveBoundaryResult`
- `evaluate_mock_active_boundary`

## Behavior

- The active boundary remains mock-only.
- The accepted candidate remains `group_profile:2`.
- Missing arming still fails safely.
- Missing dry-run confirmation still fails safely.
- Unsupported source kinds still fail safely.
- Unknown or unsupported keys still fail safely.
- Profile `3` remains unsupported by the active boundary.
- Profile `4` remains unsupported/safe.
- Sender behavior remains `MockMidiSender` only.
- No CLI command was added.
- No execution path was added.

## TDD Evidence

Red check:

- `python .\tests\test_active_boundary.py`
- failed because `rytm_randomizer.active_boundary` had no `__all__`

Green checks:

- `python .\tests\test_active_boundary.py`
- `python .\tests\test_active_boundary_report.py`
- `python .\tests\test_real_midi_adapter_boundary.py`

Full closeout:

- `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`
- passed

## Safety Boundaries

- no real MIDI
- no `mido`
- no `rtmidi`
- no MIDI port opening
- no MIDI sending
- no dispatch
- no command execution
- no runtime execution
- no active CLI command
- no hardware behavior
- no package metadata changes
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Decision

The active boundary public API is now explicit and test-covered.

This is an API hygiene milestone only. It does not move the project closer to
hardware execution by itself.

## Next Recommended Task

Continue with another concrete passive/mock-only alignment or visibility slice,
or pause at this clean checkpoint.

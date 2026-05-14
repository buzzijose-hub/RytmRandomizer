# Runtime Plan Report Public API Exports Checkpoint

## Purpose

Record the tiny runtime plan report API alignment slice.

This checkpoint documents an explicit public API export list for the existing
read-only runtime plan report. It does not add runtime execution, command
dispatch, MIDI behavior, port opening, active CLI behavior, or hardware
behavior.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Implementation milestone:

- `313375c Add runtime plan report public API exports`

Previous checkpoint:

- `8cd8113 Add active boundary report API checkpoint`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Files Changed By The Milestone

- `rytm_randomizer/runtime_plan_report.py`
- `tests/test_runtime_plan_report.py`

## Public API Now Exported

`rytm_randomizer.runtime_plan_report` now exposes an explicit `__all__` list:

- `PARKED_REPORT_INPUTS`
- `RUNTIME_PLAN_REPORT_BOUNDARY`
- `SUPPORTED_REPORT_INPUTS`
- `UNSUPPORTED_REPORT_INPUTS`
- `build_runtime_plan_report`
- `format_runtime_plan_report`
- `summarize_runtime_plan_report`

## Behavior

- The runtime plan report remains read-only.
- The report remains in-memory only.
- The report still does not execute runtime plans.
- The report still does not dispatch commands.
- The report still does not open ports.
- The report still does not send MIDI.
- Supported planning inputs remain group profiles `2` and `3`.
- Profile `4` remains parked.
- Unsupported key/source-kind handling remains unchanged.
- Report output remains deterministic.
- No CLI command was added.
- No execution path was added.

## TDD Evidence

Red check:

- `python .\tests\test_runtime_plan_report.py`
- failed because `rytm_randomizer.runtime_plan_report` had no `__all__`

Green checks:

- `python .\tests\test_runtime_plan_report.py`
- `python .\tests\test_runtime_plan.py`
- `python .\tests\test_active_runtime_report_alignment.py`

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

The runtime plan report public API is now explicit and test-covered.

This is an API hygiene milestone only. It does not move the project closer to
hardware execution by itself.

## Next Recommended Task

Continue with another concrete passive/mock-only alignment or visibility slice,
or pause at this clean checkpoint.

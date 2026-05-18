# Runtime Plan Public API Exports Checkpoint

## Purpose

Record the final useful public API hardening slice for the mock-only runtime
planning surface.

This checkpoint documents an explicit public API export list for the existing
inert runtime plan primitives. It does not add runtime execution, command
dispatch, MIDI behavior, port opening, active CLI behavior, or hardware
behavior.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Implementation milestone:

- `77402b2 Add runtime plan public API exports`

Previous checkpoint:

- `d57abce Add public API hardening progress checkpoint`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Files Changed By The Milestone

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`

## Public API Now Exported

`rytm_randomizer.runtime_plan` now exposes an explicit `__all__` list:

- `MockRuntimeProvider`
- `REASON_EXECUTION_NOT_IMPLEMENTED`
- `REASON_MISSING_ARMING`
- `REASON_PROFILE_4_PARKED`
- `REASON_UNSUPPORTED_KEY`
- `REASON_UNSUPPORTED_SOURCE_KIND`
- `RuntimeIntent`
- `RuntimePlanPreview`
- `RuntimeSafetyEnvelope`
- `SUPPORTED_GROUP_PROFILE_KEYS`
- `create_blocked_runtime_preview`
- `validate_runtime_intent_scope`

## Behavior

- The runtime plan remains mock-only and inert.
- Runtime previews remain blocked.
- Supported planning inputs remain group profiles `2` and `3`.
- Profile `4` remains parked.
- Unsupported key/source-kind handling remains unchanged.
- `MockRuntimeProvider` remains in-memory only.
- No CLI command was added.
- No execution path was added.

## TDD Evidence

Red check:

- `python .\tests\test_runtime_plan.py`
- failed because `rytm_randomizer.runtime_plan` had no `__all__`

Green checks:

- `python .\tests\test_runtime_plan.py`
- `python .\tests\test_runtime_plan_report.py`
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

## API Hardening Decision

This completes the current useful runtime/active API hardening mini-run.

Do not continue adding `__all__` exports unless a concrete module boundary is
worth locking down with a test.

## Next Recommended Task

Switch away from API-hardening repetition and return to one of:

- behavior-parity visibility
- project status/reporting refinement
- roadmap/progress documentation
- another small passive/mock-only software slice

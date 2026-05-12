# V1.34 Behavior Parity Next Branch Selection After Runtime Plan Preview Metadata Review

## 1. Purpose

Select the next safe branch after accepting the metadata-only runtime plan
preview metadata checkpoint.

This is a documentation-only selection checkpoint.

It does not implement the selected branch.

It does not add tests, fixture changes, closeout script changes, CLI changes,
CLI execution wiring, runtime execution, dispatch, command execution, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `d6d9d16 Add runtime plan preview metadata checkpoint review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- mock-only runtime plan scaffold implemented and accepted
- metadata-only runtime plan preview metadata implemented and accepted
- next branch after runtime preview metadata acceptance now being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Baseline

Accepted runtime preview metadata review:

- `Docs/V134_BEHAVIOR_PARITY_METADATA_ONLY_RUNTIME_PLAN_PREVIEW_METADATA_CHECKPOINT_REVIEW.md`

Accepted runtime preview metadata checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_METADATA_ONLY_RUNTIME_PLAN_PREVIEW_METADATA_CHECKPOINT.md`

Accepted implementation milestone:

- `0e902a8 Add metadata-only runtime plan preview metadata`

Accepted checkpoint review milestone:

- `d6d9d16 Add runtime plan preview metadata checkpoint review`

## 4. Current Runtime Plan Baseline

The accepted runtime plan baseline is:

- mock-only
- metadata-only
- blocked by default
- copied immutable preview metadata
- stable reason codes
- no runtime execution
- no CLI execution wiring
- no MIDI
- no ports
- no hardware requirement

Every preview still records:

- `would_execute: False`
- `mock_only: True`
- `sends_real_midi: False`
- `ports_allowed: False`
- `hardware_required: False`

## 5. Next Branch Options

Safe next branch options:

- Option A: create a docs-only read-only runtime plan report design.
- Option B: pause at the accepted runtime preview metadata baseline.
- Option C: write a broader behavior-parity progress report.
- Option D: create a docs-only runtime plan report implementation plan later.
- Option E: return to behavior-parity packet implementation planning.

## 6. Selected Next Branch

Selected next branch:

- docs-only read-only runtime plan report design

This selection is for design only.

It does not authorize implementation by itself.

## 7. Why This Branch

A read-only runtime plan report design is the smallest useful visibility layer
after metadata-only runtime preview support.

It can define how a future report might summarize:

- supported planning inputs
- parked planning inputs
- unknown/unsupported safe-failure behavior
- stable reason codes
- mock-only safety flags
- no-execution status
- no-MIDI status
- no-port status
- no-hardware status

This improves operator and developer visibility without moving toward runtime
execution.

## 8. Likely Future Design Scope

The selected design may discuss a future report layer that summarizes existing
runtime plan metadata.

Possible future concepts, for design discussion only:

- runtime plan report title
- supported source summary
- parked source summary
- unsupported source summary
- reason-code summary
- safety-flag summary
- deterministic text formatter
- no-execution status

Possible future implementation files, only after a separate accepted
implementation plan:

- `rytm_randomizer/runtime_plan_report.py`
- `tests/test_runtime_plan_report.py`

No implementation is authorized by this selection checkpoint.

## 9. Required Future Design Boundaries

The future design must preserve:

- no runtime execution
- no dispatch
- no command execution
- no scene execution
- no MIDI
- no ports
- no CLI execution wiring
- no package metadata changes
- no active behavior
- no hardware behavior

If a later report implementation is proposed, it must remain:

- read-only
- in-memory
- deterministic
- mock-only
- side-effect free on import
- disconnected from MIDI
- disconnected from ports
- disconnected from hardware

## 10. Parked Scope

Still parked:

- runtime plan report implementation
- runtime plan report CLI command
- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- active CLI commands
- real MIDI
- hardware validation

## 11. Confirmed Absent Behavior

This selection checkpoint adds no:

- implementation
- tests
- fixture changes
- closeout script changes
- CLI changes
- CLI execution wiring
- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI execution
- `execute-command`
- `send-command`
- `hardware-test`
- runtime mutation
- dispatch
- command execution
- scene execution
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- active behavior
- hardware behavior

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 12. Recommendation

Create the docs-only read-only runtime plan report design next.

Do not implement the report yet.

Do not add CLI execution wiring.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 13. Decision

The next branch after accepted runtime preview metadata is selected:

- docs-only read-only runtime plan report design

Hardware remains off.

No implementation in this slice.

## 14. Follow-Up Status

The selected next branch is now documented by:

- `Docs/V134_BEHAVIOR_PARITY_READ_ONLY_RUNTIME_PLAN_REPORT_DESIGN.md`

The design remains documentation-only.

It does not add implementation, tests, CLI changes, CLI execution wiring,
dispatch, command execution, runtime mutation, MIDI, ports, package metadata
changes, active behavior, or hardware behavior.

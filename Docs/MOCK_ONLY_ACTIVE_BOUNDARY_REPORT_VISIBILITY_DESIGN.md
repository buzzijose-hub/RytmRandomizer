# Mock-Only Active Boundary Report Visibility Design

## 1. Purpose

Define a future read-only report/summary layer for the current mock-first
active boundary state.

This is a documentation-only design.

It does not implement a report module, CLI command, MIDI behavior, active
execution, dispatch, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 65ca950 Add mock-only active boundary safety coverage progress review

Current phase:

- Passive/Mock Foundation Phase
- first mock-first active boundary implemented
- mock-only active boundary safety coverage reviewed
- active boundary report/summary visibility now being designed
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Problem

The project has a mock-first active boundary and closeout-protected safety
coverage, but the active boundary state is currently visible mostly through
tests and documentation.

A future read-only report would make the boundary easier to inspect before any
future expansion.

The report must increase visibility without expanding scope.

## 4. Design Goal

Design a future in-memory, read-only summary of the active boundary state.

The report should summarize:

- accepted active-boundary candidate
- unsupported active-boundary profiles
- required arming and dry-run confirmation
- mock-only status
- safe-failure behavior
- absent real MIDI
- absent port opening
- absent active CLI behavior
- absent hardware behavior
- closeout coverage

The report must not emit messages, execute commands, open ports, or touch
hardware.

## 5. Current Boundary Facts To Report

Accepted active-boundary candidate:

- group profile `"2"` / My BD Hard

Unsupported active-boundary scope:

- group profile `"3"` / My BD Classic
- group profile `"4"` / My BD Acoustic
- unknown group profile keys
- unsupported source kinds

Required conditions for mock emission:

- explicit arming
- dry-run confirmation
- supported source kind
- supported source key
- injected `MockMidiSender`

Profile `"3"` remains mock-mapper/report scope only.

Profile `"4"` remains parked and unsupported unless separately approved.

## 6. Proposed Future Report Shape

Documented as design only, not implementation:

- `rytm_randomizer/active_boundary_report.py`

Possible future functions:

- `build_active_boundary_report()`
- `format_active_boundary_report(report=None)`
- `summarize_active_boundary_report(report=None)`

The future report should return deterministic copied data.

The future formatter should produce deterministic human-readable text.

The future module should print nothing during import.

## 7. Proposed Future Report Fields

Possible report fields:

- title
- mock_only
- hardware_required
- active_cli_behavior
- real_midi
- port_opening
- dispatch
- command_execution
- scene_execution
- accepted_candidate
- unsupported_profiles
- unsupported_source_kinds
- required_conditions
- safe_failure_summary
- closeout_coverage
- safety_boundaries

The report should clearly show:

- profile `"2"` is accepted as the only active-boundary candidate
- profile `"3"` is unsupported by the active boundary
- profile `"4"` is unsupported/parked
- real MIDI is absent
- ports are absent
- active CLI behavior is absent
- hardware is not required

## 8. Relationship To Existing Reports

The existing passive mock mapper report summarizes mock mapper support:

- profiles `"2"` and `"3"` supported in the mock mapper
- profile `"4"` unsupported/safe
- no real MIDI
- no ports
- no active behavior

The future active boundary report would summarize a different boundary:

- profile `"2"` accepted by the active boundary
- profiles `"3"` and `"4"` unsupported by the active boundary
- arming and dry-run confirmation required
- mock emission possible only through injected `MockMidiSender`

The future report must not call active execution paths for side effects.

It may inspect static boundary facts or deterministic report data only.

## 9. CLI Position

No CLI command is added in this design slice.

A future CLI preview may be considered only after:

- this design is reviewed and accepted
- a read-only report module exists
- tests prove imports are side-effect free
- tests prove no real MIDI libraries are imported
- tests prove no ports are opened
- passive CLI remains read-only

If a future CLI command is approved, it should print formatted report output
only.

It must not evaluate active requests or send mock messages.

## 10. Future Tests

Future tests should verify:

- importing the report module prints nothing
- report output is deterministic
- returned data is copied/mutation-safe
- accepted candidate is profile `"2"` / My BD Hard
- profile `"3"` is reported unsupported by the active boundary
- profile `"4"` is reported unsupported/parked
- arming and dry-run confirmation are reported as required
- real MIDI is reported absent
- port opening is reported absent
- active CLI behavior is reported absent
- dispatch/execution behavior is reported absent
- hardware is reported not required
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched

## 11. Forbidden Scope

This design does not authorize:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI command
- CLI wiring to active behavior
- dispatch
- command execution
- scene execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- execute-command
- send-command
- hardware-test
- hardware validation
- profile `"4"` implementation
- profile `"3"` active-boundary support

## 12. Safe Next Options

Safe next options:

- review and accept this report visibility design
- pause at this clean design checkpoint
- implement a tiny read-only active boundary report only after review
- keep active planning frozen and return to project-level documentation

Unsafe next moves:

- adding real MIDI
- opening ports
- adding active CLI commands
- wiring passive CLI to active execution
- turning on hardware
- implementing profile `"4"` without separate approval
- adding profile `"3"` active-boundary support without separate approval

## 13. Recommendation

This design is accepted in:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_REPORT_VISIBILITY_DESIGN_REVIEW.md`

If accepted, the next implementation slice should be tiny, read-only,
in-memory, and test-backed.

Do not add CLI wiring in the first report implementation unless separately
approved.

## 14. Decision

Active boundary report/summary visibility is designed as a future read-only
layer.

Hardware remains off.

No implementation is added in this slice.

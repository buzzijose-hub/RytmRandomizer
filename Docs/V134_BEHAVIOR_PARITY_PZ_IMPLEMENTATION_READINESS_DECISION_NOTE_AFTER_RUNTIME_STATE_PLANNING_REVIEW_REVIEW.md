# V1.34 Behavior Parity PZ Implementation Readiness Decision Note After Runtime-State Planning Review Review

## 1. Purpose

Review and accept the `PZ` implementation readiness decision note after the
accepted runtime-state planning progress report review.

This is a documentation-only review gate.

It accepts the readiness decision that `PZ` is not ready for implementation
yet.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `b8e0160 Add PZ implementation readiness decision`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state plan accepted for planning
- anchor state plan accepted for planning
- selected isolated pad runtime-state plan accepted for planning
- runtime-state planning progress report accepted
- `PZ` implementation readiness decision note created
- `PZ` implementation readiness decision note now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted readiness decision note:

- `Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_READINESS_DECISION_NOTE_AFTER_RUNTIME_STATE_PLANNING_REVIEW.md`

Accepted readiness decision milestone:

- `b8e0160 Add PZ implementation readiness decision`

Decision:

- accept that `PZ` is not ready for implementation yet
- accept that `PZ` is not ready for test-only implementation yet
- keep `PZ` parked
- keep runtime state unimplemented
- keep selected target state unimplemented
- keep anchor state unimplemented
- keep selected isolated pad runtime state unimplemented
- require separate planning before any runtime-state implementation
- require separate planning before any `PZ` implementation

This review accepts planning only.

It does not authorize implementation.

## 4. Accepted Readiness Finding

Accepted finding:

- the project now has enough planning vocabulary to understand why `PZ`
  matters
- the project does not yet have enough implemented runtime-state foundation to
  make `PZ` safe to build

`PZ` still cannot safely answer:

- what selected isolated pad is active
- whether that target is defaulted or explicit
- what anchor belongs to the selected target
- whether selected target and anchor match
- whether the selected isolated pad runtime context is stale or invalid

## 5. Accepted Ready Foundations

The following foundations are accepted as ready for planning:

- shared runtime-state vocabulary
- `PZ` behavior meaning
- selected target state vocabulary
- anchor state vocabulary
- selected isolated pad runtime-state vocabulary
- safe failure expectations
- passive command read-only boundary
- no-MIDI/no-port/no-hardware boundary
- closeout discipline

These foundations support the next planning branch.

They do not authorize `PZ` implementation.

## 6. Accepted Not-Ready Scope

The following remain not ready:

- `PZ` implementation
- `PZ` test-only implementation
- selected pad anchor return behavior
- selected pad switching behavior
- runtime state mutation
- CLI execution wiring
- dispatch
- MIDI
- ports
- hardware behavior

`PZ` remains parked.

## 7. Accepted Prerequisites Before Any PZ Implementation Plan

Before any future `PZ` implementation plan:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this readiness decision reviewed and accepted
- selected target state implementation plan exists
- anchor state implementation plan exists
- selected isolated pad runtime-state implementation plan exists
- safe failure cases are specified in test-first form
- passive CLI behavior remains read-only
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- explicit statement that `PZ` remains non-hardware-facing

## 8. Accepted Minimum Future Test Categories Before PZ

Before any future `PZ` implementation, tests should exist or be planned for:

- unset selected target safe failure
- default selected target behavior
- explicit selected target behavior
- unknown anchor safe failure
- unsupported anchor safe failure
- target-anchor mismatch safe failure
- stale selected isolated pad runtime context safe failure
- invalid selected isolated pad runtime context safe failure
- `PZ` remains parked until explicitly approved
- passive CLI commands remain unchanged
- no real MIDI imports
- no port opening
- no MIDI sending
- V1.34 reference remains untouched
- package metadata remains untouched

No tests are added by this review.

## 9. Accepted Next Planning Branch

Accepted next recommended branch:

- docs-only selected isolated pad runtime-state implementation plan

Reason:

- `PZ` depends on selected isolated pad runtime state
- selected isolated pad runtime state depends on selected target state and
  anchor state
- planning the small runtime-state implementation surface first is safer than
  planning `PZ` behavior directly

This next branch must remain planning-only unless a later implementation slice
is explicitly approved.

## 10. Confirmed Absent Behavior

This review confirms no:

- code changes
- test changes
- closeout script changes
- package metadata changes
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- dispatch
- command execution
- scene execution
- mutation execution
- runtime state implementation
- selected target state implementation
- anchor state implementation
- selected isolated pad runtime state implementation
- selected pad switching execution
- selected pad anchor return execution
- `PZ` implementation
- profile `4` mock mapper support
- direct behavior helper execution from CLI
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- true hardware capture
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 11. Passive Commands Remain Read-Only

Existing passive CLI commands remain read-only:

- `report`
- `list-commands`
- `list-scenes`
- `list-group-profiles`
- `search-commands`
- `search-scenes`
- `search-group-profiles`
- `inspect-command`
- `inspect-scene`
- `inspect-group-profile`
- `preview-command`
- `preview-scene`
- `preview-group-profile`
- `mock-mapper-report`
- `behavior-menu-report`
- `anchor-profile-report`

They must not construct runtime state, dispatch behavior, open ports, or send
MIDI.

## 12. Safe Next Options

Safe next options:

- docs-only selected isolated pad runtime-state implementation plan
- docs-only selected target state implementation plan
- docs-only anchor state implementation plan
- user-facing progress/timeline update
- pause at this clean accepted checkpoint

## 13. Recommendation

Proceed with a docs-only selected isolated pad runtime-state implementation
plan.

Do not implement selected isolated pad runtime state yet.

Do not implement selected target state yet.

Do not implement anchor state yet.

Do not implement `PZ`.

Do not add runtime state yet.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 14. Decision Summary

`Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_READINESS_DECISION_NOTE_AFTER_RUNTIME_STATE_PLANNING_REVIEW.md`
is accepted for planning.

`PZ` is not ready for implementation yet.

`PZ` remains parked.

Runtime state remains unimplemented.

Selected target state remains unimplemented.

Anchor state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

Hardware remains off.

No implementation in this review slice.

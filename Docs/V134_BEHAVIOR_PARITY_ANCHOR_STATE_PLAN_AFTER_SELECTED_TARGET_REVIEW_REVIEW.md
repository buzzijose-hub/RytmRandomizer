# V1.34 Behavior Parity Anchor State Plan After Selected Target Review Review

## 1. Purpose

Review and accept the anchor state plan after the accepted selected target
state plan review.

This is a documentation-only review gate.

It accepts anchor state as a planning boundary only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `84c0e6b Add anchor state plan after selected target review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state plan accepted for planning
- anchor state plan created
- anchor state plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted anchor state plan:

- `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_PLAN_AFTER_SELECTED_TARGET_REVIEW.md`

Accepted anchor state plan milestone:

- `84c0e6b Add anchor state plan after selected target review`

Decision:

- accept anchor state as the current planning boundary
- keep anchor state unimplemented
- keep selected target state unimplemented
- keep runtime state unimplemented
- keep `PZ` parked
- require separate planning before any anchor state implementation
- require separate planning before any selected isolated pad runtime-state
  implementation
- require separate planning before any `PZ` implementation

This review accepts planning only.

It does not authorize implementation.

## 4. Accepted Anchor State Boundary

Accepted anchor state boundary:

- anchor state is future in-memory session state
- the current scope is selected isolated pad anchor only
- anchor state answers what known anchor belongs to the selected target
- anchor state does not answer what target is selected
- anchor state is required before future `PZ` implementation can be planned
  safely
- anchor state must remain non-hardware-facing unless a later active boundary
  is accepted

The current project may describe this boundary.

The current project may not execute it.

## 5. Accepted Anchor State Values

The accepted planning vocabulary for future anchor state values is:

- unknown
- static
- software-known
- soft-captured
- unsupported
- stale
- invalid

These are planning values only.

No enum, dataclass, runtime state object, storage, capture behavior, or anchor
return behavior is added by this review.

## 6. Accepted Anchor Source Boundary

The accepted source boundary distinguishes future anchor knowledge from:

- passive metadata source
- read-only behavior intent source
- future software-known source
- future soft-capture source
- future true hardware capture source

True hardware capture remains later scope.

No hardware capture is authorized by this review.

## 7. Relationship To Selected Target State

This review accepts that anchor state is not selected target state.

Selected target state answers:

- what is selected?

Anchor state answers:

- what known anchor belongs to that selected target?

`PZ` requires both before any implementation can be planned safely.

## 8. Relationship To PZ

This review accepts that `PZ` depends on anchor state because `PZ` means:

- return selected isolated pad to anchor only

Before `PZ` can become anything more than parked behavior, the project must be
able to answer:

- what anchor belongs to the selected isolated pad?
- is that anchor known?
- is that anchor supported?
- is the anchor static, software-known, soft-captured, stale, or invalid?
- can the anchor be paired with the current selected target?

`PZ` remains parked.

## 9. Accepted Safe Failure Requirements

The review accepts that any future anchor state implementation plan must fail
safely for:

- unknown anchor
- unsupported anchor
- stale anchor
- invalid anchor
- anchor outside supported pad range
- anchor outside selected isolated pad scope
- selected target and anchor mismatch
- attempt to use anchor for `PZ` without accepted selected target state
- accidental active path
- accidental hardware-facing path

Safe failure must mean:

- no state mutation unless explicitly allowed by a later runtime-state design
- no dispatch
- no command execution
- no anchor return execution
- no MIDI
- no ports
- no hardware mutation
- deterministic explanatory result

## 10. Accepted Future Test Planning Requirements

Before any future anchor state implementation, tests should be planned for:

- unknown anchor safe failure
- static anchor behavior
- software-known anchor behavior
- soft-captured anchor behavior
- unsupported anchor safe failure
- stale anchor safe failure
- invalid anchor safe failure
- selected target and anchor mismatch safe failure
- `PZ` remains parked until implementation is approved
- passive CLI behavior remains unchanged
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- V1.34 reference remains untouched
- package metadata remains untouched

No tests are added by this review.

## 11. Confirmed Absent Behavior

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
- selected profile runtime state
- selected isolated pad runtime state
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

## 12. Passive Commands Remain Read-Only

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

## 13. Preconditions Before Any Future Anchor State Implementation Plan

Before any future anchor state implementation plan:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this anchor state plan reviewed and accepted
- anchor state values accepted
- selected target state plan accepted
- safe failure behavior accepted
- tests planned before implementation
- explicit statement that anchor state remains non-hardware-facing
- explicit statement that `PZ` remains parked unless separately approved

## 14. Safe Next Options

Safe next options:

- docs-only selected isolated pad runtime-state plan
- broader behavior-parity progress report after anchor state planning
- pause at this clean accepted checkpoint

## 15. Recommendation

Prefer a broader behavior-parity progress report next, or a docs-only selected
isolated pad runtime-state plan if continuing toward future `PZ` planning.

Do not implement anchor state yet.

Do not implement selected target state yet.

Do not implement `PZ`.

Do not add runtime state yet.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 16. Decision Summary

`Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_PLAN_AFTER_SELECTED_TARGET_REVIEW.md`
is accepted for planning.

Anchor state remains unimplemented.

Selected target state remains unimplemented.

Runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this review slice.

## 17. Follow-Up Status

This accepted review is now followed by:

- `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_PLAN_AFTER_ANCHOR_STATE_REVIEW.md`

That plan describes the future selected isolated pad runtime-state boundary
while keeping selected isolated pad runtime state unimplemented, selected
target state unimplemented, anchor state unimplemented, and `PZ` parked.

# V1.34 Behavior Parity Anchor State Plan After Selected Target Review

## 1. Purpose

Define the future anchor state boundary after the accepted selected target
state plan review.

This is a documentation-only planning slice.

It describes what "anchor state" should mean before any future `PZ`, selected
isolated pad runtime work, or selected pad anchor return behavior.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `8bda84b Add selected target state plan review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state plan accepted for planning
- anchor state now being planned at documentation level

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Prior Accepted Context

Relevant prior documents:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_VOCABULARY_DECISION_NOTE.md`
- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_VOCABULARY_DECISION_NOTE_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PZ_BEHAVIOR_PLAN_AFTER_RUNTIME_STATE_VOCABULARY.md`
- `Docs/V134_BEHAVIOR_PARITY_PZ_BEHAVIOR_PLAN_AFTER_RUNTIME_STATE_VOCABULARY_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_PLAN_AFTER_PZ_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_PLAN_AFTER_PZ_REVIEW_REVIEW.md`

Accepted current state:

- runtime-state vocabulary is accepted for planning
- `PZ` behavior plan is accepted for planning
- selected target state plan is accepted for planning
- `PZ` remains parked
- runtime state remains unimplemented
- selected target state remains unimplemented
- selected isolated pad runtime state remains unimplemented
- selected pad anchor return execution remains unimplemented
- profile `4` mock mapper support remains parked

## 4. Anchor State Definition

Anchor state is future in-memory session state representing the known anchor
associated with a target.

For the current planning branch, the relevant anchor is:

- selected isolated pad anchor

Future anchor state may answer:

- whether an anchor is known for the selected target
- where that anchor knowledge came from
- whether the anchor is static, software-known, soft-captured, stale,
  unsupported, or invalid
- whether the anchor is safe to preview
- whether the anchor is safe to use for a future `PZ` anchor-return plan

This plan does not implement anchor state.

## 5. Current Passive Anchor Equivalents

The current project already has read-only anchor/profile intent and reporting.

Examples:

- direct anchor/profile intent:
  - `BH`
  - `BC`
  - `BS`
  - `BF`
- current-anchor intent:
  - `B` / back to current anchor
  - `E` / commit current state as new anchor
  - `H` / show current anchor
- selected-profile anchor intent:
  - `M` / load selected profile anchor
- lane or group anchor intent:
  - `P2Z`
  - `P3A`
  - `P4A`
  - `O`
  - `Z`
- parked selected isolated pad anchor return intent:
  - `PZ`

These current surfaces describe anchor intent only.

They do not create, store, update, restore, or validate runtime anchor state.

## 6. Relationship To Selected Target State

Anchor state is not selected target state.

Selected target state answers:

- what is selected?

Anchor state answers:

- what known anchor belongs to that selected target?

For `PZ`, selected target state and anchor state must agree before any future
runtime behavior can be planned safely.

## 7. Relationship To PZ

`PZ` depends on anchor state because it means:

- return selected isolated pad to anchor only

Before `PZ` can become anything more than parked behavior, the project must be
able to answer:

- what anchor belongs to the selected isolated pad?
- is that anchor known?
- is that anchor supported?
- is the anchor static, software-known, soft-captured, stale, or invalid?
- can the anchor be paired with the current selected target?

Until those questions have a reviewed answer, `PZ` remains parked.

## 8. Anchor State Values

Future anchor state should distinguish these planning values:

- unknown:
  - no anchor is known for the selected target
- static:
  - anchor knowledge comes from accepted passive metadata or accepted behavior
    intent
- software-known:
  - anchor knowledge comes from a future software action that the modular
    system performed or tracked
- soft-captured:
  - anchor knowledge comes from future software-known state capture
- unsupported:
  - an anchor exists conceptually but is outside current supported scope
- stale:
  - anchor knowledge may no longer match current runtime context
- invalid:
  - anchor data is malformed or impossible

These are future planning values only.

No enum, dataclass, runtime state object, storage, or behavior is added by this
plan.

## 9. Anchor Source Boundary

Future anchor state should distinguish source types:

- passive metadata source
- read-only behavior intent source
- future software-known source
- future soft-capture source
- future true hardware capture source

True hardware capture remains much later scope.

No hardware capture is authorized by this plan.

## 10. Anchor Scope Boundary

For the current anchor state planning branch, scope should remain:

- selected isolated pad anchor only
- no Pads 5-12
- no Analog Four
- no machine/profile universe expansion
- no scene anchor execution
- no group anchor execution
- no hardware anchor state

Future scope widening must be separately reviewed.

## 11. Safe Failure Requirements

Any future anchor state implementation plan must fail safely for:

- unknown anchor
- unsupported anchor
- stale anchor
- invalid anchor
- anchor outside supported pad range
- anchor outside selected isolated pad scope
- selected target and anchor mismatch
- attempt to use anchor for `PZ` without accepted selected target state
- accidental active or hardware-facing path

Safe failure must mean:

- no state mutation unless explicitly allowed by a later runtime-state design
- no dispatch
- no command execution
- no anchor return execution
- no MIDI
- no ports
- no hardware mutation
- deterministic explanatory result

## 12. Relationship To Hardware State

Anchor state is not hardware state.

Hardware state is the actual state of the Analog Rytm or another device.

The modular project does not currently read, capture, mutate, or trust hardware
state.

This plan does not authorize true hardware capture, MIDI, ports, or hardware
validation.

## 13. Relationship To Runtime State

Anchor state is a future runtime-state concept.

It may eventually become a small, isolated in-memory runtime concept.

That is not implemented here.

Any future anchor state implementation must remain non-hardware-facing unless a
later active boundary is accepted.

## 14. Relationship To CLI

No CLI changes are added by this plan.

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

Future anchor state planning must not wire CLI to runtime execution without a
separate accepted implementation plan.

## 15. Future Test Planning Requirements

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

No tests are added by this plan.

## 16. Confirmed Absent Behavior

This plan confirms no:

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

## 17. Preconditions Before Any Anchor State Implementation Plan

Before any anchor state implementation plan:

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

## 18. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this anchor state plan
- docs-only selected isolated pad runtime-state plan
- broader behavior-parity progress report after anchor state planning
- pause at this clean checkpoint

## 19. Recommendation

Review and accept this anchor state plan next.

After that, prefer a docs-only selected isolated pad runtime-state plan, or a
broader progress report if we want a larger checkpoint first.

Do not implement anchor state yet.

Do not implement selected target state yet.

Do not implement `PZ`.

Do not add runtime state yet.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 20. Decision Summary

The future anchor state boundary is now described.

Anchor state remains unimplemented.

Selected target state remains unimplemented.

`PZ` remains parked.

Runtime state remains unimplemented.

Hardware remains off.

No implementation in this planning slice.

## 21. Follow-Up Status

This anchor state plan is now followed by:

- `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_PLAN_AFTER_SELECTED_TARGET_REVIEW_REVIEW.md`

That review accepts the anchor state boundary for planning while keeping
anchor state unimplemented, selected target state unimplemented, runtime state
unimplemented, and `PZ` parked.

# V1.34 Behavior Parity Selected Isolated Pad Runtime-State Plan After Anchor State Review

## 1. Purpose

Define the future selected isolated pad runtime-state boundary after the
accepted selected target state plan and accepted anchor state plan.

This is a documentation-only planning slice.

It describes what "selected isolated pad runtime state" should mean before any
future `PZ`, selected pad mutation, selected pad anchor return, selected pad
switching, or runtime mutation behavior.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `3e75dfc Add anchor state plan review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state plan accepted for planning
- anchor state plan accepted for planning
- selected isolated pad runtime state now being planned at documentation level

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
- `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_PLAN_AFTER_SELECTED_TARGET_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_PLAN_AFTER_SELECTED_TARGET_REVIEW_REVIEW.md`

Accepted current state:

- runtime-state vocabulary is accepted for planning
- `PZ` behavior plan is accepted for planning
- selected target state plan is accepted for planning
- anchor state plan is accepted for planning
- `PZ` remains parked
- runtime state remains unimplemented
- selected target state remains unimplemented
- anchor state remains unimplemented
- selected isolated pad runtime state remains unimplemented
- selected pad switching execution remains unimplemented
- selected pad anchor return execution remains unimplemented
- profile `4` mock mapper support remains parked

## 4. Selected Isolated Pad Runtime-State Definition

Selected isolated pad runtime state is future in-memory session state for the
single-pad isolated workflow.

It may eventually combine:

- selected target state:
  - what isolated pad is selected
- anchor state:
  - what known anchor belongs to that selected target
- operation context:
  - what selected-pad operation is being described or requested
- validation state:
  - whether the selected target and anchor are safe to use together

This plan does not implement selected isolated pad runtime state.

## 5. Current Passive Selected Isolated Pad Surfaces

The current project already has read-only selected isolated pad intent and
reporting.

Examples:

- `L`:
  - select isolated single-pad mutation target, default Pad 3
- `PM`:
  - mutate selected isolated pad only using its group default zone/depth
- `PS`:
  - mutate selected isolated pad SRC only, choose depth
- `PF`:
  - mutate selected isolated pad Filter only, choose depth
- `PA`:
  - mutate selected isolated pad Amp only, choose depth
- `PL`:
  - mutate selected isolated pad LFO only, choose depth
- `PO`:
  - mutate selected isolated pad Morph only, choose depth
- `PB`:
  - mutate selected isolated pad Body only, choose depth
- `PG`:
  - mutate selected isolated pad Grit only, choose depth
- `PZ`:
  - return selected isolated pad to anchor only
- `PR`:
  - show selected isolated pad

These current surfaces describe intent only.

They do not create, store, update, switch, mutate, restore, or validate
runtime selected isolated pad state.

## 6. Relationship To Selected Target State

Selected isolated pad runtime state includes selected target state, but it is
not the same thing.

Selected target state answers:

- what isolated pad is selected?

Selected isolated pad runtime state answers a larger future question:

- what is the current selected isolated pad workflow context?

For future `PZ`, selected target state must be present before selected
isolated pad runtime state can safely route to anchor-return planning.

## 7. Relationship To Anchor State

Selected isolated pad runtime state includes anchor state, but it is not the
same thing.

Anchor state answers:

- what known anchor belongs to the selected target?

Selected isolated pad runtime state answers:

- can the selected target and its known anchor be used together for a future
  selected-pad operation?

For future `PZ`, selected isolated pad runtime state must pair target and
anchor state safely before any selected pad anchor return can be planned.

## 8. Relationship To PZ

`PZ` depends on selected isolated pad runtime state because `PZ` means:

- return selected isolated pad to anchor only

Before `PZ` can become anything more than parked behavior, the project must be
able to answer:

- what isolated pad is selected?
- is the selected pad supported?
- what anchor belongs to that selected pad?
- is that anchor known and valid?
- does the selected target match the anchor scope?
- is the selected isolated pad context stale?
- can the operation fail safely without touching hardware?

Until those questions have a reviewed runtime-state answer, `PZ` remains
parked.

## 9. Future Runtime-State Values

Future selected isolated pad runtime state should distinguish these planning
values:

- uninitialized:
  - no selected isolated pad runtime context exists
- passive-default:
  - context is inferred from read-only behavior intent such as default Pad 3
- explicit-target:
  - context was explicitly selected by a future approved runtime path
- target-anchor-matched:
  - selected target and known anchor agree
- target-anchor-mismatched:
  - selected target and known anchor do not agree
- unsupported:
  - selected isolated pad context is outside current supported scope
- stale:
  - runtime context may no longer reflect current session assumptions
- invalid:
  - runtime context is malformed or impossible

These are future planning values only.

No enum, dataclass, runtime state object, storage, or behavior is added by this
plan.

## 10. Future Runtime-State Fields

If implementation is approved later, selected isolated pad runtime state may
need conceptual fields such as:

- target pad
- target source
- target state
- anchor source
- anchor state
- anchor identity
- operation kind
- selected isolated pad command key
- validation status
- stale status
- explanatory reason

These are design vocabulary only.

No field, object, storage layer, module, or test is added by this plan.

## 11. Scope Boundary

For the current selected isolated pad runtime-state planning branch, scope
should remain:

- selected isolated pad workflow only
- Pads 1-4 only as already represented in accepted passive behavior
- no Pads 5-12
- no Analog Four
- no machine/profile universe expansion
- no scene execution
- no group execution
- no hardware runtime state
- no hardware capture

Future scope widening must be separately reviewed.

## 12. Relationship To Hardware State

Selected isolated pad runtime state is not hardware state.

Hardware state is the actual state of the Analog Rytm or another device.

The modular project does not currently read, capture, mutate, or trust
hardware state.

This plan does not authorize true hardware capture, MIDI, ports, or hardware
validation.

## 13. Relationship To CLI

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

Future selected isolated pad runtime-state planning must not wire CLI to
runtime execution without a separate accepted implementation plan.

## 14. Safe Failure Requirements

Any future selected isolated pad runtime-state implementation plan must fail
safely for:

- uninitialized runtime context
- unset selected target
- unsupported selected target
- stale selected target
- invalid selected target
- unknown anchor
- unsupported anchor
- stale anchor
- invalid anchor
- target and anchor mismatch
- selected isolated pad command outside supported scope
- attempt to use `PZ` without accepted target and anchor state
- accidental active path
- accidental hardware-facing path

Safe failure must mean:

- no state mutation unless explicitly allowed by a later runtime-state design
- no dispatch
- no command execution
- no selected pad switching execution
- no selected pad anchor return execution
- no MIDI
- no ports
- no hardware mutation
- deterministic explanatory result

## 15. Future Test Planning Requirements

Before any future selected isolated pad runtime-state implementation, tests
should be planned for:

- uninitialized context safe failure
- passive-default selected target behavior
- explicit selected target behavior
- target and anchor matched behavior
- target and anchor mismatch safe failure
- unsupported selected target safe failure
- unknown anchor safe failure
- stale context safe failure
- invalid context safe failure
- `L` behavior remains read-only until implementation is approved
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

## 17. Preconditions Before Any Implementation Plan

Before any selected isolated pad runtime-state implementation plan:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- selected target state plan reviewed and accepted
- anchor state plan reviewed and accepted
- this selected isolated pad runtime-state plan reviewed and accepted
- runtime-state values accepted
- safe failure behavior accepted
- tests planned before implementation
- explicit statement that runtime state remains non-hardware-facing
- explicit statement that `PZ` remains parked unless separately approved

## 18. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this selected isolated pad
  runtime-state plan
- broader behavior-parity progress report after selected target, anchor, and
  selected isolated pad runtime-state planning
- docs-only `PZ` implementation readiness decision note
- pause at this clean checkpoint

## 19. Recommendation

Review and accept this selected isolated pad runtime-state plan next.

After that, prefer a broader behavior-parity progress report before deciding
whether `PZ` is ready for any future test-only implementation planning.

Do not implement selected isolated pad runtime state yet.

Do not implement selected target state yet.

Do not implement anchor state yet.

Do not implement `PZ`.

Do not add runtime state yet.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 20. Decision Summary

The future selected isolated pad runtime-state boundary is now described.

Selected isolated pad runtime state remains unimplemented.

Selected target state remains unimplemented.

Anchor state remains unimplemented.

`PZ` remains parked.

Runtime state remains unimplemented.

Hardware remains off.

No implementation in this planning slice.

## 21. Follow-Up Status

This selected isolated pad runtime-state plan is now followed by:

- `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_PLAN_AFTER_ANCHOR_STATE_REVIEW_REVIEW.md`

That review accepts the selected isolated pad runtime-state boundary for
planning while keeping selected isolated pad runtime state unimplemented,
selected target state unimplemented, anchor state unimplemented, runtime state
unimplemented, and `PZ` parked.

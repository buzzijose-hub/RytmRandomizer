# V1.34 Behavior Parity Selected Target State Plan After PZ Review

## 1. Purpose

Define the future selected target state boundary after the accepted `PZ`
behavior plan review.

This is a documentation-only planning slice.

It describes what "selected target state" should mean before any future `PZ`
or selected isolated pad runtime work.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `87b11b4 Add PZ behavior plan review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state now being planned at documentation level

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

Accepted current state:

- runtime-state vocabulary is accepted for planning
- `PZ` behavior plan is accepted for planning
- `PZ` remains parked
- runtime state remains unimplemented
- selected isolated pad runtime state remains unimplemented
- selected pad anchor return execution remains unimplemented
- profile `4` mock mapper support remains parked

## 4. Selected Target State Definition

Selected target state is future in-memory session state representing what the
operator or program currently intends to act on.

For the current planning branch, the relevant selected target is:

- selected isolated pad target

Future selected target state may answer:

- which pad is selected
- how that pad was selected
- whether the selection is defaulted, explicit, unset, unsupported, or stale
- whether the selected target is safe to preview
- whether the selected target is safe to use for a future anchor-return plan

This plan does not implement selected target state.

## 5. Current Passive Equivalent

The current project already has read-only selected isolated pad target intent:

- command key:
  - `L`
- current meaning:
  - select isolated single-pad mutation target, default Pad 3
- current behavior:
  - read-only selected isolated pad target intent
  - no selected isolated pad state is created
  - no selected pad switch executes
  - no runtime state mutates

This passive intent is not runtime selected target state.

## 6. Relationship To PZ

`PZ` depends on selected target state because it means:

- return selected isolated pad to anchor only

Before `PZ` can become anything more than parked behavior, the project must be
able to answer:

- what isolated pad is selected?
- is the selected pad known?
- is the selected pad supported?
- was the selected pad explicitly selected or defaulted?
- can the selected pad be paired with a known anchor?

Until those questions have a reviewed answer, `PZ` remains parked.

## 7. Selected Target State Values

Future selected target state should distinguish these states:

- unset:
  - no selected isolated pad target exists
- defaulted:
  - a target is assumed from a safe default such as Pad 3
- explicit:
  - a target was selected by a future operator-facing path
- unsupported:
  - a target exists but is outside current supported scope
- stale:
  - a target was once known but may no longer match current runtime context
- invalid:
  - a target value is malformed or impossible

These are future planning values only.

No enum, dataclass, runtime state object, or storage is added by this plan.

## 8. Target Scope Boundary

For the current selected target state planning branch, scope should remain:

- selected isolated pad target only
- no Pads 5-12
- no Analog Four
- no machine/profile universe expansion
- no scene target state
- no group target state
- no hardware target state

Future scope widening must be separately reviewed.

## 9. Safe Failure Requirements

Any future selected target state implementation plan must fail safely for:

- unset target
- unsupported target
- stale target
- invalid target
- target outside supported pad range
- target outside selected isolated pad scope
- attempt to use target for `PZ` without accepted anchor state
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

## 10. Relationship To Anchor State

Selected target state is not anchor state.

Selected target state answers:

- what is selected?

Anchor state answers:

- what known anchor belongs to that selected target?

`PZ` requires both concepts before implementation can be planned safely.

This plan defines only the selected target side of that boundary.

Anchor state remains a future docs-only planning branch.

## 11. Relationship To Runtime State

Selected target state is a future runtime-state concept.

It may eventually become a small, isolated in-memory runtime concept.

That is not implemented here.

Any future selected target implementation must remain non-hardware-facing
unless a later active boundary is accepted.

## 12. Relationship To CLI

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

Future selected target planning must not wire CLI to runtime execution without
a separate accepted implementation plan.

## 13. Future Test Planning Requirements

Before any future selected target state implementation, tests should be planned
for:

- defaulted selected target behavior
- explicit selected target behavior
- unset target safe failure
- unsupported target safe failure
- stale target safe failure
- invalid target safe failure
- `L` behavior remains read-only until implementation is approved
- `PZ` remains parked until implementation is approved
- passive CLI behavior remains unchanged
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- V1.34 reference remains untouched
- package metadata remains untouched

No tests are added by this plan.

## 14. Confirmed Absent Behavior

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
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 15. Preconditions Before Any Selected Target Implementation Plan

Before any selected target implementation plan:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this selected target state plan reviewed and accepted
- target state values accepted
- safe failure behavior accepted
- tests planned before implementation
- explicit statement that selected target state remains non-hardware-facing
- explicit statement that `PZ` remains parked unless separately approved

## 16. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this selected target state plan
- docs-only anchor state plan
- docs-only selected isolated pad runtime-state plan
- broader behavior-parity progress report after selected target planning
- pause at this clean checkpoint

## 17. Recommendation

Review and accept this selected target state plan next.

After that, prefer a docs-only anchor state plan.

Do not implement selected target state yet.

Do not implement `PZ`.

Do not add runtime state yet.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 18. Decision Summary

The future selected target state boundary is now described.

Selected target state remains unimplemented.

`PZ` remains parked.

Runtime state remains unimplemented.

Hardware remains off.

No implementation in this planning slice.

## 19. Review Status

This selected target state plan is now followed by:

- `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_PLAN_AFTER_PZ_REVIEW_REVIEW.md`

That review accepts the selected target state plan for planning while keeping
selected target state unimplemented, `PZ` parked, and anchor state as future
planning scope.

# V1.34 Behavior Parity Selected Isolated Pad Runtime-State Implementation Plan After Selected Target And Anchor State Reviews

## 1. Purpose

Update the selected isolated pad runtime-state implementation plan after the
selected target state and anchor state implementation plans have both been
reviewed and accepted.

This is a documentation-only implementation planning slice.

It describes the future integration surface that may eventually combine:

- selected target state
- anchor state
- selected isolated pad runtime-state validation

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `9eab2c5 Add anchor state implementation plan review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state implementation plan accepted
- anchor state implementation plan accepted
- selected isolated pad runtime-state implementation plan now being updated
  after those accepted smaller state boundaries

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Planning Context

Accepted upstream implementation planning documents:

- selected target state implementation plan:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_SEQUENCING_REVIEW.md`
- selected target state implementation plan review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_SEQUENCING_REVIEW_REVIEW.md`
- anchor state implementation plan:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_IMPLEMENTATION_REVIEW.md`
- anchor state implementation plan review:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_IMPLEMENTATION_REVIEW_REVIEW.md`

These documents establish planning boundaries only.

They do not implement selected target state, anchor state, selected isolated
pad runtime state, `PZ`, dispatch, MIDI, ports, active behavior, or hardware
behavior.

## 4. Updated Decision

Decision:

- keep selected target state planned as the smaller future layer that answers
  what selected isolated pad is active
- keep anchor state planned as the smaller future layer that answers what
  known anchor belongs to the selected target
- update selected isolated pad runtime-state planning as the future layer that
  may validate those two state objects together
- keep selected isolated pad runtime-state implementation unstarted
- keep selected target state implementation unstarted
- keep anchor state implementation unstarted
- keep `PZ` parked
- require a separate approved implementation slice before any code or tests

This plan update does not authorize implementation by itself.

## 5. Future Ownership

Future implementation, if separately approved, should remain isolated in a
dedicated module:

- `rytm_randomizer/selected_isolated_pad_runtime_state.py`

Future tests, if separately approved, should remain isolated in:

- `tests/test_selected_isolated_pad_runtime_state.py`

Existing read-only behavior helpers should remain passive intent surfaces:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

The selected target and anchor state modules, if implemented later, should
remain separate:

- `rytm_randomizer/selected_target_state.py`
- `tests/test_selected_target_state.py`
- `rytm_randomizer/anchor_state.py`
- `tests/test_anchor_state.py`

No future implementation should turn any of these modules into MIDI senders,
dispatchers, active CLI commands, or hardware interfaces.

## 6. Future Module Responsibility

The selected isolated pad runtime-state module should answer one integration
question only:

- is the selected isolated pad target context safe and internally consistent
  with the known anchor context?

It may eventually combine selected target state and anchor state data.

It should not:

- decide what MIDI should be sent
- execute `PZ`
- execute anchor return
- execute selected pad switching
- mutate runtime state unless separately approved
- dispatch commands
- inspect connected hardware
- open ports
- send MIDI
- make hardware-facing decisions

This keeps selected isolated pad runtime-state validation separate from active
execution.

## 7. Future Inputs From Smaller State Layers

The future runtime-state layer may eventually receive selected target state
data such as:

- target pad
- target state
- target source
- command key
- supported status
- stale status
- valid status
- explanatory reason
- safe failure code

The future runtime-state layer may eventually receive anchor state data such
as:

- anchor pad
- anchor state
- anchor source
- anchor identity
- source profile key
- source profile name
- source machine value
- supported status
- stale status
- valid status
- explanatory reason
- safe failure code

These inputs remain conceptual.

No selected target state object or anchor state object exists yet.

## 8. Future Runtime-State Object Shape

A future selected isolated pad runtime-state object may be dataclass-like and
immutable-ish.

Accepted conceptual fields may include:

- target pad
- target state
- target source
- anchor pad
- anchor state
- anchor source
- anchor identity
- selected isolated pad command key
- target-anchor status
- operation kind
- validation status
- stale status
- supported status
- valid status
- explanatory reason
- safe failure code

The object should contain no MIDI object, port object, hardware handle,
dispatch callback, execution callback, CLI callback, `PZ` executor, or mutable
hardware-facing state.

## 9. Accepted Runtime-State Values

The plan keeps the previously accepted selected isolated pad runtime-state
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

These remain planning values only.

No enum, dataclass, runtime object, storage, or behavior is added by this
document.

## 10. Updated Smallest Future Behavior Surface

The first implementation, if separately approved, should stay smaller than
`PZ`.

Accepted future scope may include:

- construct an uninitialized selected isolated pad runtime state
- construct a passive-default selected isolated pad runtime state from the
  accepted default Pad 3 planning context
- combine a separately created selected target state with a separately created
  anchor state
- validate target-anchor match or mismatch
- classify unsupported target or anchor scope deterministically
- classify stale/invalid target or anchor context deterministically
- return deterministic safe failure results
- expose data for tests only

The accepted first scope must not:

- implement selected target state
- implement anchor state
- execute `L`
- execute `PZ`
- execute anchor return
- switch selected pad
- mutate runtime or hardware state
- dispatch commands
- open ports
- send MIDI
- wire into active CLI behavior

## 11. Safe Failure Requirements

Any future implementation must fail safely for:

- uninitialized selected isolated pad runtime context
- missing selected target state
- missing anchor state
- unsupported selected target
- unsupported anchor
- target outside selected isolated pad scope
- anchor outside selected isolated pad scope
- target outside currently supported pad scope
- anchor outside currently supported pad scope
- Pads 5-12
- Analog Four target or anchor scope
- missing anchor identity
- unknown anchor identity
- target-anchor mismatch
- stale target context
- stale anchor context
- invalid target context
- invalid anchor context
- attempt to use selected isolated pad runtime state for `PZ` before `PZ` is
  approved
- accidental active path
- accidental hardware-facing path

Safe failure means:

- no dispatch
- no command execution
- no scene execution
- no selected pad switch
- no anchor return
- no runtime mutation unless explicitly allowed by a later implementation
- no MIDI
- no ports
- no hardware mutation
- deterministic explanatory result

## 12. Future Test-First Requirements

Before any implementation, tests should be planned and then written first.

Future tests should verify:

- importing the module prints nothing
- uninitialized state is deterministic and safe
- passive-default Pad 3 context is deterministic
- missing selected target state fails safely
- missing anchor state fails safely
- unsupported selected target fails safely
- unsupported anchor fails safely
- Pads 5-12 fail safely
- Analog Four scope fails safely
- target-anchor matched state is deterministic, if separately approved
- target-anchor mismatched state fails safely
- stale target context fails safely
- stale anchor context fails safely
- invalid target context fails safely
- invalid anchor context fails safely
- runtime-state objects are copied/immutable-ish
- repeated evaluations are deterministic
- `PZ` remains parked
- passive CLI behavior remains unchanged
- no active command names are exposed
- no real MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- V1.34 reference remains untouched
- package metadata remains untouched

These tests are not added by this document.

## 13. Relationship To Selected Target State

Selected target state should remain the smaller future layer.

It answers:

- what selected isolated pad is active?

Selected isolated pad runtime state should not duplicate target selection
ownership.

It should consume target state only after a separate approved implementation
exists.

## 14. Relationship To Anchor State

Anchor state should remain the smaller future layer.

It answers:

- what known anchor belongs to the selected target?

Selected isolated pad runtime state should not duplicate anchor ownership.

It should consume anchor state only after a separate approved implementation
exists.

## 15. Relationship To PZ

`PZ` remains parked.

This runtime-state plan update does not execute `PZ`.

This runtime-state plan update does not authorize `PZ`.

Future `PZ` reconsideration should require:

- selected target state implemented and reviewed
- anchor state implemented and reviewed
- selected isolated pad runtime state implemented and reviewed
- closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- passive CLI still read-only
- no MIDI, ports, active behavior, or hardware behavior unless separately
  approved in a much later slice

## 16. Relationship To Passive CLI

Passive CLI commands must remain read-only:

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

No passive CLI command should construct selected isolated pad runtime state
unless a later review explicitly allows read-only report/preview visibility.

No passive CLI command should dispatch commands, open ports, send MIDI, or
touch hardware.

## 17. Confirmed Absent Behavior

This plan confirms no:

- code changes
- test changes
- closeout script changes
- package metadata changes
- selected target state implementation
- anchor state implementation
- selected isolated pad runtime-state implementation
- runtime state implementation
- selected pad switching execution
- selected pad anchor return execution
- `PZ` implementation
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- dispatch
- command execution
- scene execution
- mutation execution
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

## 18. Preconditions Before Any Implementation

Before any future selected isolated pad runtime-state implementation:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this updated implementation plan reviewed and accepted
- selected target state implementation plan reviewed and accepted
- anchor state implementation plan reviewed and accepted
- future tests specified in test-first form
- passive CLI behavior remains read-only
- no active CLI behavior is added
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- no hardware is required

## 19. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this updated implementation plan:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_AND_ANCHOR_STATE_REVIEWS_REVIEW.md`
- docs-only implementation readiness decision for selected target, anchor, and
  selected isolated pad runtime-state modules
- docs-only progress/timeline update
- pause at this clean planning checkpoint

## 20. Follow-On Review

The follow-on docs-only review gate is:

- `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_AND_ANCHOR_STATE_REVIEWS_REVIEW.md`

It accepts this updated selected isolated pad runtime-state implementation plan
as the current planning boundary.

It keeps selected target state unimplemented.

It keeps anchor state unimplemented.

It keeps selected isolated pad runtime state unimplemented.

It keeps `PZ` parked.

It authorizes no implementation, tests, CLI commands, runtime state, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 21. Recommendation

Proceed with a docs-only implementation readiness decision for the selected
target, anchor, and selected isolated pad runtime-state modules.

Do not implement selected target state yet.

Do not implement anchor state yet.

Do not implement selected isolated pad runtime state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 22. Decision Summary

Selected isolated pad runtime-state implementation planning is updated after
selected target state and anchor state implementation plan reviews.

Selected target state remains unimplemented.

Anchor state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this planning slice.

# V1.34 Behavior Parity Selected Target State Implementation Review After Runtime-State Modules Readiness Review

## 1. Purpose

Review and accept the selected target state implementation after the accepted
runtime-state modules readiness review.

This is a documentation-only review gate.

It accepts the selected target state implementation as the current first
runtime-state module implementation milestone.

It adds no implementation, tests, CLI commands, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `af5859d Add local dev tooling notes`

Implementation being reviewed:

- `12869c3 Add selected target state implementation`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- runtime-state modules readiness accepted
- selected target state implemented as the first runtime-state module
- selected target state implementation now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted implementation:

- `rytm_randomizer/selected_target_state.py`

Accepted tests:

- `tests/test_selected_target_state.py`

Accepted closeout update:

- `Scripts/closeout_check.ps1`
- closeout label:
  - `Selected Target State`

Accepted implementation milestone:

- `12869c3 Add selected target state implementation`

Decision:

- accept selected target state as the first implemented runtime-state module
- accept that selected target state answers only what selected isolated pad
  target is known
- accept default Pad 3 target state from passive `L` context
- accept unset, unsupported, stale, and invalid safe-failure states
- keep anchor state unimplemented
- keep selected isolated pad runtime state unimplemented
- keep `PZ` parked
- require a separate approved implementation slice before anchor state code or
  tests

This review accepts the selected target state implementation only.

It does not authorize anchor state implementation.

## 4. Accepted Module Responsibility

`rytm_randomizer/selected_target_state.py` is accepted as the small
runtime-state module that answers:

- what selected isolated pad target is known?

It does not answer:

- what anchor belongs to the target
- whether target and anchor match
- whether selected isolated pad runtime context is valid
- whether `PZ` can execute
- whether hardware is connected
- what MIDI should be sent

## 5. Accepted Behavior Surface

The accepted selected target state behavior includes:

- unset selected target state
- defaulted Pad 3 selected isolated pad target state from passive `L` context
- unsupported selected target safe failure
- stale selected target safe failure
- invalid selected target safe failure
- deterministic explanatory result data
- immutable-ish/copy-safe metadata
- deterministic repeated evaluation
- import side-effect safety

The accepted selected target state behavior does not include:

- explicit target selection execution
- selected pad switching
- anchor state
- selected isolated pad runtime state
- `PZ`
- anchor return
- runtime mutation
- CLI wiring
- dispatch
- MIDI
- ports
- hardware behavior

## 6. Accepted Tests

The accepted test coverage verifies:

- importing `rytm_randomizer.selected_target_state` prints nothing
- unset selected target state is deterministic and safe
- default selected target state uses passive Pad 3 context
- unsupported selected target fails safely
- stale selected target fails safely
- invalid selected target fails safely
- selected target metadata is copied/immutable-ish
- repeated selected target state evaluations are deterministic
- no active command names are exported
- passive CLI behavior remains unchanged
- no real MIDI library is imported

The tests are accepted as the current coverage for this first runtime-state
module.

## 7. Closeout Coverage

Closeout now includes:

- `Selected Target State`

The closeout update is accepted because a new test file was added.

No other closeout behavior is changed.

## 8. Confirmed Safety Boundaries

The selected target state implementation confirms:

- no selected pad switching
- no selected isolated pad runtime state
- no anchor state
- no `PZ`
- no CLI wiring
- no dispatch
- no command execution
- no scene execution
- no mutation execution
- no real MIDI dependency
- no `mido`
- no `rtmidi`
- no port discovery
- no port opening
- no MIDI sending
- no hardware behavior
- no hardware validation
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Relationship To Anchor State

Anchor state remains the next planned runtime-state module.

Anchor state should start only after this selected target state implementation
review is accepted.

Future anchor state should remain smaller than selected isolated pad runtime
state and should answer only:

- what known anchor belongs to the selected target?

Anchor state must not implement:

- selected target ownership
- selected isolated pad runtime state
- `PZ`
- anchor return execution
- hardware capture
- dispatch
- MIDI
- ports
- hardware behavior

## 10. Relationship To Selected Isolated Pad Runtime State

Selected isolated pad runtime state remains unimplemented.

It should start only after selected target state and anchor state are both
implemented, reviewed, and accepted.

It may later validate target and anchor state together.

It must not be introduced by this review.

## 11. Relationship To PZ

`PZ` remains parked.

This review does not authorize `PZ`.

This review does not authorize selected pad anchor return.

Future `PZ` reconsideration still requires:

- selected target state implemented and reviewed
- anchor state implemented and reviewed
- selected isolated pad runtime state implemented and reviewed
- closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- passive CLI still read-only
- no MIDI, ports, active behavior, runtime execution, or hardware behavior
  unless separately approved in a later slice

## 12. Preconditions Before Anchor State Implementation

Before anchor state implementation begins:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- selected target state implementation reviewed and accepted
- anchor state implementation plan reviewed and accepted
- future anchor state tests written first
- passive CLI behavior remains read-only
- no active CLI behavior is added
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- no hardware is required

## 13. Safe Next Options

Safe next options:

- first test-first anchor state implementation slice
- docs-only anchor state implementation packet plan
- docs-only selected target state progress checkpoint
- pause at this clean accepted implementation checkpoint

## 14. Recommendation

Proceed with a first test-first anchor state implementation slice, or create a
docs-only anchor state implementation packet plan if one more planning gate is
desired.

Do not implement selected isolated pad runtime state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 15. Decision Summary

`rytm_randomizer/selected_target_state.py` is accepted as the first
runtime-state module implementation.

`tests/test_selected_target_state.py` is accepted as the current selected
target state test coverage.

Anchor state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this review slice.

## 16. Follow-On Anchor State Implementation Slice

After this review checkpoint, the next conservative anchor state
implementation slice adds:

- `rytm_randomizer/anchor_state.py`
- `tests/test_anchor_state.py`

The closeout suite gains:

- `Anchor State`

Current baseline before that implementation slice:

- `08efa9b Add selected target state implementation review`

Implemented follow-on behavior:

- unknown anchor state safe failure
- unsupported anchor safe failure
- stale anchor safe failure
- invalid anchor safe failure
- immutable-ish/copy-safe metadata
- deterministic repeated evaluation
- import side-effect safety

Still absent after that follow-on slice:

- static anchor support
- software-known anchor support
- soft-captured anchor support
- anchor return execution
- selected pad switching
- selected isolated pad runtime state
- `PZ`
- CLI wiring
- dispatch
- MIDI
- ports
- package metadata changes
- active behavior
- hardware behavior

The next recommended task after the follow-on implementation is a docs-only
review/acceptance gate for the anchor state implementation.

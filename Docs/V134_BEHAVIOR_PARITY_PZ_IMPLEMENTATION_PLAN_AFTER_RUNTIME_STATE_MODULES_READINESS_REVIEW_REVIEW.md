# V1.34 Behavior Parity PZ Implementation Plan Review After Runtime-State Modules Readiness Review

## 1. Purpose

Review and accept the `PZ` implementation plan after the runtime-state modules
readiness review.

This is a documentation-only review gate.

It accepts the current `PZ` implementation plan as the current future
implementation boundary.

It adds no implementation, tests, CLI commands, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `1781b13 Add PZ implementation plan after runtime-state readiness`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- selected target state implemented and reviewed
- anchor state implemented and reviewed
- selected isolated pad runtime state implemented and reviewed
- `PZ` readiness decision reviewed and accepted
- `PZ` implementation plan documented
- `PZ` implementation plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted implementation plan:

- `Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_MODULES_READINESS_REVIEW.md`

Accepted implementation plan milestone:

- `1781b13 Add PZ implementation plan after runtime-state readiness`

Decision:

- accept future `PZ` as a read-only/inert runtime-readiness helper
- accept that future `PZ` must not execute anchor return
- accept that future `PZ` must not switch pads
- accept that future `PZ` must not mutate runtime state
- accept that future `PZ` must not dispatch commands
- accept that future `PZ` must not open ports
- accept that future `PZ` must not send MIDI
- accept that future `PZ` must not require hardware
- accept expected future file ownership
- keep implementation unstarted in this review slice

This review accepts planning only.

It does not implement `PZ`.

## 4. Accepted Future Ownership

Accepted future implementation files:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

Accepted closeout expectation:

- no closeout script update is expected because `tests/test_behavior_selected_isolated_pad.py`
  is already covered by:
  - `Behavior Selected Isolated Pad`

Package metadata must remain untouched.

## 5. Accepted Future Behavior Boundary

Accepted future `PZ` behavior boundary:

- inspect conservative selected isolated pad runtime-state context
- report whether anchor return readiness is available
- fail safely when target or anchor context is unavailable
- expose deterministic read-only result data
- keep `anchor_return_intent` descriptive only
- keep `anchor_return_executed` false
- keep `selected_pad_switch_executed` false
- keep `state_changed` false
- keep `mutates_runtime_state` false
- keep `dispatches_command` false
- keep `executes_command` false
- keep `sends_real_midi` false
- keep `opens_ports` false
- keep `hardware_required` false
- keep `active_behavior` false

The accepted future implementation is an inert behavior helper, not active
anchor return.

## 6. Accepted Future API Boundary

Accepted preserved public helper:

- `evaluate_selected_isolated_pad_behavior(command_key)`

Accepted possible future extension:

- `evaluate_selected_isolated_pad_behavior(command_key, runtime_state=None)`

The optional runtime-state argument must not require CLI input, prompt loops,
hardware, ports, or MIDI libraries.

If omitted for `PZ`, the helper may use the conservative passive default
selected isolated pad runtime-state builder.

## 7. Accepted Future Test Requirements

Accepted future tests must cover:

- import side-effect safety
- existing `L` behavior remains unchanged
- `PZ` read-only anchor return readiness
- default `PZ` context fails safely because anchor is unavailable
- `PZ` consumes selected isolated pad runtime-state data without mutating it
- missing selected target safe failure
- missing anchor safe failure
- unsupported target safe failure
- unsupported anchor safe failure
- stale target safe failure
- stale anchor safe failure
- invalid target safe failure
- invalid anchor safe failure
- metadata copied/immutable-ish
- deterministic repeated `PZ` evaluation
- no selected pad switch execution
- no anchor return execution
- no runtime state mutation
- passive CLI behavior remains unchanged
- no real MIDI library import
- no port opening
- no MIDI sending
- no active command names exposed
- package metadata remains untouched
- V1.34 reference remains untouched

## 8. Confirmed Absent Behavior

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
- selected pad switching execution
- selected pad anchor return execution
- runtime mutation
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

## 9. Safe Next Options

Safe next options:

- tiny TDD `PZ` implementation slice for read-only/inert runtime-readiness
  behavior
- docs-only implementation readiness checkpoint before code, if one more gate
  is desired
- progress/timeline update
- pause at this clean accepted plan checkpoint

## 10. Recommendation

Proceed next with a tiny TDD `PZ` implementation slice only if continuing.

That implementation must stay inside the accepted future ownership files and
must remain read-only, inert, and non-hardware-facing.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 11. Decision Summary

The `PZ` implementation plan is accepted.

`PZ` remains unimplemented in this review slice.

The next implementation, if approved, should make `PZ` a read-only/inert
runtime-readiness helper.

Hardware remains off.

No implementation in this review slice.

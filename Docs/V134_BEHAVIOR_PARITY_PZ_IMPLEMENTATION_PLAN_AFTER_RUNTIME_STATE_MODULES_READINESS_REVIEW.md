# V1.34 Behavior Parity PZ Implementation Plan After Runtime-State Modules Readiness Review

## 1. Purpose

Define the smallest safe future implementation plan for `PZ` after the
accepted `PZ` readiness decision review.

This is a documentation-only implementation plan.

It describes a future test-first implementation shape only.

It does not implement `PZ`.

It adds no implementation, tests, CLI commands, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `f35d716 Add PZ readiness decision review after runtime-state modules`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- selected target state implemented and reviewed
- anchor state implemented and reviewed
- selected isolated pad runtime state implemented and reviewed
- `PZ` readiness decision reviewed and accepted
- `PZ` implementation plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Context

Accepted upstream context:

- `PZ` readiness decision:
  - `Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_READINESS_DECISION_AFTER_RUNTIME_STATE_MODULES_PROGRESS_REVIEW.md`
- `PZ` readiness decision review:
  - `Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_READINESS_DECISION_AFTER_RUNTIME_STATE_MODULES_PROGRESS_REVIEW_REVIEW.md`
- runtime-state modules progress checkpoint review:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_MODULES_IMPLEMENTATION_PROGRESS_CHECKPOINT_AFTER_SELECTED_TARGET_ANCHOR_AND_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATIONS_REVIEW.md`
- selected isolated pad runtime-state implementation review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_REVIEW_AFTER_READINESS_REVIEW.md`

These documents make `PZ` eligible for planning only.

They do not authorize implementation by themselves.

## 4. Current Decision

Decision:

- plan a tiny future `PZ` read-only implementation
- keep `PZ` non-executable
- keep `PZ` non-hardware-facing
- keep the future implementation test-first
- keep `PZ` behavior conservative and inert
- do not implement `PZ` in this slice

The future implementation should treat `PZ` as a runtime-readiness and
safe-failure helper, not as anchor return execution.

## 5. Future Ownership

Future implementation, if approved later, should stay in the existing selected
isolated pad behavior helper.

Expected future files:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

No new closeout label is expected because `tests/test_behavior_selected_isolated_pad.py`
is already covered by:

- `Behavior Selected Isolated Pad`

No closeout script changes are planned.

Package metadata must remain untouched.

## 6. Future PZ Behavior Meaning

Future `PZ` behavior should mean:

- inspect the conservative selected isolated pad runtime-state context
- report whether `PZ` could safely return the selected isolated pad to its
  anchor
- fail safely when target or anchor context is unavailable
- expose deterministic read-only result data
- never execute anchor return
- never switch selected pads
- never mutate runtime state
- never dispatch commands
- never send MIDI
- never open ports
- never require hardware

The first future implementation should not attempt real anchor return.

## 7. Proposed Future API Shape

Preserve the existing public helper:

- `evaluate_selected_isolated_pad_behavior(command_key)`

Possible future optional extension:

- `evaluate_selected_isolated_pad_behavior(command_key, runtime_state=None)`

If `runtime_state` is omitted for `PZ`, the helper may use the conservative
passive default selected isolated pad runtime-state builder.

The default `PZ` result should remain safe because current default anchor
context is unavailable.

The future implementation must not require CLI input, prompt loops, hardware,
ports, or MIDI libraries.

## 8. Proposed Future Result Shape

Future `PZ` should continue returning:

- `SelectedIsolatedPadBehaviorResult`

Future `PZ` result should include:

- `command_key`: `PZ`
- `behavior_family`: `selected-isolated-pad/anchor-return-readiness`
- `utility_action`: `describe_selected_isolated_pad_anchor_return_readiness`
- `intent_kind`: `selected_isolated_pad_anchor_return_readiness`
- `anchor_return_intent`: `True`
- `anchor_return_executed`: `False`
- `selected_pad_switch_executed`: `False`
- `state_changed`: `False`
- `mutates_runtime_state`: `False`
- `dispatches_command`: `False`
- `executes_command`: `False`
- `sends_real_midi`: `False`
- `opens_ports`: `False`
- `hardware_required`: `False`
- `active_behavior`: `False`

Future metadata should include copied runtime-state fields such as:

- `runtime_state`
- `target_pad`
- `target_state`
- `target_anchor_status`
- `anchor_state`
- `anchor_identity`
- `pz_ready`
- `pz_executed`
- `safe_failure_code`

## 9. Proposed Future Default Outcome

With no injected runtime state, `PZ` should likely evaluate the conservative
passive default context.

Expected default outcome:

- selected target context: default Pad 3
- anchor context: unknown or unavailable
- `anchor_return_intent`: `True`
- `anchor_return_executed`: `False`
- `pz_ready`: `False`
- `state_changed`: `False`
- `reason`: anchor unavailable for selected target
- safe failure is deterministic and explanatory

This keeps the helper useful while preserving the hardware-off boundary.

## 10. Future Safe Failure Requirements

Any future `PZ` implementation must fail safely for:

- missing selected target runtime state
- missing anchor runtime state
- unsupported selected target
- unsupported anchor
- stale selected target
- stale anchor
- invalid selected target
- invalid anchor
- unsupported target-anchor status
- unknown command key
- any active or hardware-facing path

Safe failure means:

- no state mutation
- no selected pad switch
- no anchor return execution
- no dispatch
- no command execution
- no MIDI
- no ports
- no hardware mutation
- deterministic result and metadata

## 11. Future Test Plan

Future tests should be added to `tests/test_behavior_selected_isolated_pad.py`.

Required future tests:

- importing `rytm_randomizer.behavior_selected_isolated_pad` prints nothing
- existing `L` behavior remains unchanged
- `PZ` no longer reports as merely deferred after implementation approval
- `PZ` reports read-only anchor return readiness
- default `PZ` context fails safely because anchor is unavailable
- `PZ` consumes selected isolated pad runtime-state data without mutating it
- missing selected target safe failure is preserved
- missing anchor safe failure is preserved
- unsupported target safe failure is preserved
- unsupported anchor safe failure is preserved
- stale target safe failure is preserved
- stale anchor safe failure is preserved
- invalid target safe failure is preserved
- invalid anchor safe failure is preserved
- metadata is copied/immutable-ish
- repeated `PZ` evaluation is deterministic
- no selected pad switch executes
- no anchor return executes
- no runtime state mutates
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active command names are exposed
- package metadata remains untouched
- V1.34 reference remains untouched

## 12. Future TDD Sequence

If implementation is later approved, use a tiny TDD sequence:

1. Add failing tests for default read-only `PZ` readiness behavior.
2. Verify the new tests fail while existing tests still describe current
   deferred behavior.
3. Implement the smallest behavior helper change.
4. Run `python -m pytest tests/test_behavior_selected_isolated_pad.py -v`.
5. Run full closeout.
6. Confirm V1.34 reference diff is empty.
7. Confirm package metadata diff is empty.
8. Commit only the approved implementation files.

This plan does not execute that sequence.

## 13. Explicit Non-Goals

No:

- implementation in this slice
- test changes in this slice
- closeout script changes in this slice
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

## 14. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this `PZ` implementation plan
- tiny TDD `PZ` implementation only after this plan is reviewed and accepted
- progress/timeline update
- pause at this clean planning checkpoint

## 15. Recommendation

Proceed next with a docs-only review/acceptance gate for this `PZ`
implementation plan.

After that review, decide whether to run the tiny TDD `PZ` implementation
slice.

Do not implement `PZ` yet.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 16. Decision Summary

The future `PZ` implementation should be a read-only/inert runtime-readiness
helper.

It should not execute anchor return.

It should not switch pads.

It should not mutate runtime state.

It should not touch MIDI, ports, or hardware.

Hardware remains off.

No implementation in this planning slice.

## 17. Review Status

This implementation plan is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_MODULES_READINESS_REVIEW_REVIEW.md`

The review keeps `PZ` unimplemented in its slice and recommends a tiny TDD
implementation slice only if continuing.

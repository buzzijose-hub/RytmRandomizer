# V1.34 Behavior Parity PZ Implementation Readiness Decision After Runtime-State Modules Progress Review

## 1. Purpose

Decide whether `PZ` is ready to move beyond parked status after the accepted
runtime-state modules implementation progress checkpoint review.

This is a documentation-only readiness decision.

It decides planning readiness only.

It does not implement `PZ`.

It adds no implementation, tests, CLI commands, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this decision slice:

- `0e43e8d Add runtime-state modules progress checkpoint review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- selected target state implemented and reviewed
- anchor state implemented and reviewed
- selected isolated pad runtime state implemented and reviewed
- runtime-state modules implementation progress checkpoint reviewed
- `PZ` readiness now being evaluated

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Runtime-State Context

Accepted upstream context:

- selected target state implementation review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_IMPLEMENTATION_REVIEW_AFTER_RUNTIME_STATE_MODULES_READINESS_REVIEW.md`
- anchor state implementation review:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_IMPLEMENTATION_REVIEW_AFTER_SELECTED_TARGET_STATE_IMPLEMENTATION_REVIEW.md`
- selected isolated pad runtime-state implementation review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_REVIEW_AFTER_READINESS_REVIEW.md`
- runtime-state modules implementation progress checkpoint review:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_MODULES_IMPLEMENTATION_PROGRESS_CHECKPOINT_AFTER_SELECTED_TARGET_ANCHOR_AND_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATIONS_REVIEW.md`

The accepted runtime-state modules provide conservative, inert validation
support.

They do not execute `PZ`.

They do not mutate runtime state.

They do not send MIDI or touch hardware.

## 4. Current PZ Readiness Decision

Decision:

- `PZ` is still not ready for implementation in this slice.
- `PZ` is still not authorized for anchor return execution.
- `PZ` is now ready for a separate docs-only implementation plan.
- That future plan must remain test-first, conservative, and non-hardware-facing.

This means `PZ` moves from:

- parked because runtime-state prerequisites were missing

to:

- eligible for a later separately approved planning slice because the
  conservative runtime-state prerequisites now exist

It does not mean `PZ` is implemented.

It does not mean `PZ` is active.

## 5. Why Readiness Has Changed

Earlier `PZ` readiness decisions kept `PZ` parked because these prerequisites
were missing:

- selected target state implementation
- anchor state implementation
- selected isolated pad runtime-state implementation
- test coverage for those state modules
- closeout coverage for those state modules

Those prerequisites now exist and have been reviewed.

The project can now safely plan `PZ` behavior against known conservative state
objects instead of planning against vocabulary alone.

## 6. What Is Ready

Ready for planning:

- docs-only `PZ` implementation plan
- test-first `PZ` safe-failure contract
- `PZ` relationship to selected target state
- `PZ` relationship to anchor state
- `PZ` relationship to selected isolated pad runtime state
- deterministic inert result shape
- no-MIDI/no-port/no-hardware guardrails

Ready implementation prerequisites:

- `rytm_randomizer/selected_target_state.py`
- `rytm_randomizer/anchor_state.py`
- `rytm_randomizer/selected_isolated_pad_runtime_state.py`
- `tests/test_selected_target_state.py`
- `tests/test_anchor_state.py`
- `tests/test_selected_isolated_pad_runtime_state.py`

## 7. What Is Not Ready

Still not ready:

- `PZ` implementation
- selected pad anchor return execution
- selected pad switching execution
- runtime mutation
- CLI execution wiring
- dispatch
- MIDI
- ports
- hardware behavior

The next step is planning only.

## 8. Required Shape Of Any Future PZ Implementation Plan

Any future `PZ` implementation plan must specify:

- implementation files before editing
- test files before editing
- exact result shape for safe failure
- exact result shape for unavailable anchor context
- exact result shape for unsupported target or anchor context
- how selected target state is consumed
- how anchor state is consumed
- how selected isolated pad runtime state is consumed
- that `PZ` remains non-hardware-facing
- that `PZ` does not open ports
- that `PZ` does not send MIDI
- that `PZ` does not mutate hardware

The first future implementation should prefer a conservative inert behavior
helper, not active anchor return.

## 9. Required Future Test Categories

Before any `PZ` implementation can be accepted, tests must cover:

- import side-effect safety
- `PZ` remains absent from active command names
- unset selected target safe failure
- missing selected target safe failure
- unknown anchor safe failure
- missing anchor safe failure
- unsupported selected target safe failure
- unsupported anchor safe failure
- stale selected target safe failure
- stale anchor safe failure
- invalid selected target safe failure
- invalid anchor safe failure
- no selected pad switching
- no anchor return execution
- no runtime mutation
- passive CLI behavior remains unchanged
- no real MIDI library import
- no port opening
- no MIDI sending
- V1.34 reference remains untouched
- package metadata remains untouched

## 10. Confirmed Absent Behavior

This decision confirms no:

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

## 11. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this `PZ` readiness decision
- docs-only `PZ` implementation plan after this decision is reviewed
- progress/timeline update
- pause at this clean readiness checkpoint

## 12. Recommendation

Proceed next with a docs-only review/acceptance gate for this `PZ`
implementation readiness decision.

After that review, create a docs-only `PZ` implementation plan if continuing.

Do not implement `PZ` yet.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 13. Decision Summary

`PZ` remains unimplemented.

`PZ` remains non-executable.

`PZ` remains non-hardware-facing.

`PZ` is now eligible for a separate docs-only implementation plan because the
conservative runtime-state prerequisites exist and have been reviewed.

Hardware remains off.

No implementation in this decision slice.

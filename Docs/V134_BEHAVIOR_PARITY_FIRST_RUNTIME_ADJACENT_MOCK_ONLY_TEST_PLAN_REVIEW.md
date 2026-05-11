# V1.34 Behavior Parity First Runtime-Adjacent Mock-Only Test Plan Review

## 1. Purpose

Review and accept
`Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_ADJACENT_MOCK_ONLY_TEST_PLAN.md`
as the current first runtime-adjacent mock-only test planning gate.

This is a documentation-only review gate.

It adds no implementation, tests, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `6766c51 Add first runtime adjacent mock-only test plan`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime/execution boundary reviewed and accepted
- first runtime-adjacent mock-only test plan created and now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

The first runtime-adjacent mock-only test plan is accepted.

Accepted test plan:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_ADJACENT_MOCK_ONLY_TEST_PLAN.md`

Accepted test-plan milestone:

- `6766c51 Add first runtime adjacent mock-only test plan`

This review accepts the test plan only as planning and safety language.

It does not authorize execution.

It does not authorize active behavior.

It does not authorize real MIDI.

It does not authorize hardware validation.

## 4. Accepted Candidate

The accepted first runtime-adjacent mock-only candidate is:

- `PZ`: return selected isolated pad to anchor only

Accepted meaning:

- `PZ` remains read-only runtime-adjacent readiness
- `PZ` remains a safe-failure candidate
- `PZ` remains non-executable
- `PZ` remains non-hardware-facing

This candidate is accepted because it can exercise runtime-adjacent safety
vocabulary without switching pads, returning anchors, mutating state, sending
MIDI, or touching hardware.

## 5. Accepted Future Test Direction

Future test-only work may prove:

- import safety
- default `PZ` readiness fails safely
- missing selected target context fails safely
- missing anchor context fails safely
- unsupported target or anchor context fails safely
- stale or invalid target/anchor context fails safely
- repeated readiness checks are deterministic
- returned metadata is copy-safe
- no mock messages are emitted for failed readiness
- no real MIDI libraries are imported
- no ports are opened
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata remains untouched

Any future test implementation must remain mock-only and test-only.

## 6. Confirmed Absent Behavior

The following remain intentionally absent:

- new tests in this slice
- implementation
- CLI wiring
- command dispatch
- command execution
- scene execution
- selected pad switching execution
- selected pad anchor return execution
- runtime mutation
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware validation
- package metadata changes
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 7. Preconditions Before Any Future Test-Only Implementation

Before any test-only implementation based on this plan:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- this review is accepted
- future scope is limited to test-only safe-failure coverage
- passive CLI remains read-only
- no real MIDI libraries are required
- no hardware is required
- no ports are opened

## 8. Expected Future Implementation Boundary

If separately approved, a future test-only slice may create:

- `tests/test_runtime_adjacent_mock_only_pz.py`

That future slice may exercise existing read-only modules:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `rytm_randomizer/selected_isolated_pad_runtime_state.py`
- `rytm_randomizer/selected_target_state.py`
- `rytm_randomizer/anchor_state.py`
- `rytm_randomizer/mock_midi.py`

It must not implement `PZ` execution.

It must not add CLI execution behavior.

It must not add real MIDI behavior.

It must not require hardware.

## 9. Safe Next Options

Safe next branches:

- Option A: create the tiny test-only `PZ` runtime-adjacent safe-failure test
  slice
- Option B: create a more detailed implementation plan for that test-only
  slice
- Option C: pause at this accepted planning checkpoint
- Option D: create a broader progress report before implementation

## 10. Recommendation

Proceed next with the tiny test-only `PZ` runtime-adjacent safe-failure test
slice if continuing implementation.

That slice should add tests only, plus a closeout label if a new test file is
created.

Do not implement execution.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 11. Decision

The first runtime-adjacent mock-only test plan is accepted.

`PZ` is accepted as the first test-only safe-failure candidate.

Execution remains outside the current project phase.

The next recommended task is a tiny test-only `PZ` runtime-adjacent
safe-failure test slice, if explicitly approved.

Hardware remains off.

No implementation in this slice.

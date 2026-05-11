# V1.34 Behavior Parity B Runtime-Adjacent Mock-Only Safe-Failure Test Plan

## 1. Purpose

Define a docs-only test plan for future runtime-adjacent mock-only
safe-failure coverage for `B`: back to current anchor.

This plan defines what future tests should prove before any `B`
runtime-adjacent implementation or execution-facing behavior can be considered.

This is a documentation-only test plan.

It adds no implementation, tests, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this test-plan slice:

- `f7c133b Add runtime adjacent next branch selection review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime/execution boundary accepted
- first runtime-adjacent mock-only `PZ` safe-failure test milestone accepted
- runtime-adjacent next branch selection accepted
- docs-only `B` safe-failure test plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_ADJACENT_NEXT_BRANCH_SELECTION_AFTER_PZ_TESTS_REVIEW.md`

Accepted upstream decision:

- the next selected planning branch is a docs-only `B` runtime-adjacent
  mock-only safe-failure test plan
- `B` is selected for planning only
- `B` is not accepted as a runtime-adjacent mock-only test candidate yet
- `PZ` remains the only accepted runtime-adjacent mock-only safe-failure
  candidate
- active execution, real MIDI, ports, package metadata changes, and hardware
  validation remain absent

This plan stays inside that boundary.

## 4. Candidate Under Plan

Candidate for future mock-only safe-failure testing:

- `B`: back to current anchor

Current passive meaning:

- read-only current-anchor return intent
- behavior family: `undo-commit-state/current-anchor-return`
- state action: `describe_current_anchor_return_intent`
- intent kind: `anchor_return`
- anchor concept: `current anchor`

Current source ownership:

- `rytm_randomizer/behavior_undo_commit_state.py`

Current test ownership:

- `tests/test_behavior_undo_commit_state.py`

This plan does not change current `B` behavior.

This plan does not authorize current-anchor return execution.

## 5. Relationship To PZ

`PZ` remains the only accepted runtime-adjacent mock-only safe-failure
candidate at this checkpoint.

`B` is planned next because it is adjacent to anchor return vocabulary, but it
is not accepted for implementation by this document.

Important separation:

- `PZ` describes selected isolated pad anchor-return readiness
- `B` describes current-anchor return intent
- neither command executes anchor return
- neither command sends MIDI
- neither command opens ports
- neither command touches hardware

## 6. What Future Mock-Only B Tests Should Prove

Future mock-only tests for `B` should prove:

- importing relevant modules prints nothing
- `B` remains read-only
- `B` readiness defaults to safe failure if required current-anchor context is
  unavailable
- missing current-anchor context fails safely
- unsupported current-anchor context fails safely
- stale current-anchor context fails safely
- invalid current-anchor context fails safely
- repeated readiness checks are deterministic
- returned metadata is copy-safe
- no current anchor return is executed
- no runtime state is mutated
- no dispatch happens
- no command execution happens
- no MIDI messages are emitted
- no ports are opened
- no real MIDI libraries are imported
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata remains untouched

## 7. Proposed Future Test Ownership

Future test-only implementation, if separately approved, should stay in a
small mock-only scope.

Likely future test file:

- `tests/test_runtime_adjacent_mock_only_b.py`

Likely existing source files to exercise:

- `rytm_randomizer/behavior_undo_commit_state.py`
- `rytm_randomizer/anchor_state.py`
- `rytm_randomizer/mock_midi.py`

Likely passive CLI command to guard:

- `python -m rytm_randomizer.cli preview-command B`

Files that should not be changed by the future test-only slice unless a
separate review explicitly approves it:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- package metadata files

If a new test file is created later, `Scripts/closeout_check.ps1` may need a
new closeout label such as:

- `=== Test: Runtime-Adjacent Mock-Only B ===`

This plan does not make that closeout update.

## 8. Proposed Future Test Cases

Future tests should cover these exact behaviors:

- import safety for the runtime-adjacent `B` test path
- default `B` readiness remains unavailable and safe
- injected anchor state is required before readiness can become available
- missing anchor state remains unavailable and safe
- unsupported anchor state remains unavailable and safe
- stale anchor state remains unavailable and safe
- invalid anchor state remains unavailable and safe
- repeated readiness checks are deterministic
- returned readiness metadata is copy-safe
- `MockMidiSender` remains empty for failed readiness
- passive CLI `preview-command B` remains read-only
- no active command names are exposed by the runtime-adjacent `B` path
- no real MIDI libraries are imported
- package metadata remains untouched

The future tests should not require hardware.

The future tests should not require real MIDI libraries.

## 9. MockMidiSender Position

`MockMidiSender` may be used in future tests only to prove that no messages
are emitted by the runtime-adjacent `B` path when readiness fails.

For this candidate, the safest expected result is:

- zero real MIDI sends
- zero mock sends for failed readiness
- no port interaction
- no hardware interaction

If a later test records an inert mock message, that must be separately
reviewed and must remain mock-only.

## 10. Explicit Non-Goals

This plan does not include:

- implementation
- new tests
- CLI wiring
- command dispatch
- command execution
- scene execution
- current anchor return execution
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

## 11. Preconditions Before Future Mock-Only B Implementation

Before implementing this test-only plan:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- this test plan is reviewed and accepted
- future implementation scope is limited to test-only mock behavior
- passive CLI remains read-only
- no real MIDI libraries are required
- no hardware is required
- no ports are opened

## 12. Stop Conditions

Stop immediately if a future slice proposes:

- executing `B`
- returning current anchors
- switching selected pads
- returning selected pad anchors
- mutating runtime state
- dispatching commands
- importing a real MIDI library
- opening a MIDI port
- sending MIDI
- changing package metadata
- touching `rytm_hybrid_randomizer_v134.py`
- requiring hardware
- adding active CLI behavior

## 13. Safe Next Options

Safe next branches:

- Option A: review/accept this `B` runtime-adjacent mock-only safe-failure
  test plan
- Option B: pause at this planning checkpoint
- Option C: create a more detailed test-only implementation plan after
  accepting this test plan
- Option D: return to a broader progress/timeline update before implementation

## 14. Recommendation

Do a docs-only review/acceptance gate for this test plan next.

After that, the safest implementation branch would be a tiny test-only slice
for `B` runtime-adjacent safe-failure coverage.

Do not implement tests yet.

Do not implement execution.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 15. Decision

The next runtime-adjacent mock-only test-plan candidate is `B`.

The plan is documentation-only.

`B` remains planning-only until this plan is reviewed and accepted.

`PZ` remains the only accepted runtime-adjacent mock-only safe-failure
candidate at this checkpoint.

The next recommended task is a docs-only review/acceptance gate for this test
plan.

Hardware remains off.

No implementation in this slice.

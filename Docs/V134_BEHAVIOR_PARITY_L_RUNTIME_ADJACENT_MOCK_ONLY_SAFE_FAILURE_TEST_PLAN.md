# V1.34 Behavior Parity L Runtime-Adjacent Mock-Only Safe-Failure Test Plan

## 1. Purpose

Define a docs-only test plan for future runtime-adjacent mock-only
safe-failure coverage for `L`: select isolated single-pad mutation target,
default Pad 3.

This plan defines what future tests should prove before any `L`
runtime-adjacent implementation or selected pad switching behavior can be
considered.

This is a documentation-only test plan.

It adds no implementation, tests, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this test-plan slice:

- `1bc7469 Add runtime adjacent next branch selection review after PZ and B timeline`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime/execution boundary accepted
- runtime-adjacent mock-only `PZ` safe-failure tests accepted
- runtime-adjacent mock-only `B` safe-failure tests accepted
- `L` selected for docs-only planning after the post-`PZ`/`B` timeline review
- docs-only `L` safe-failure test plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_ADJACENT_NEXT_BRANCH_SELECTION_AFTER_PZ_AND_B_TIMELINE_REVIEW_REVIEW.md`

Accepted upstream decision:

- the next selected planning branch is a docs-only `L` runtime-adjacent
  mock-only safe-failure test plan
- `L` is selected for planning only
- `L` is not accepted as a runtime-adjacent mock-only test surface yet
- accepted runtime-adjacent mock-only safe-failure surfaces remain `PZ` and
  `B`
- selected pad switching execution remains absent
- active execution, real MIDI, ports, package metadata changes, and hardware
  validation remain absent

This plan stays inside that boundary.

## 4. Candidate Under Plan

Candidate for future mock-only safe-failure testing:

- `L`: select isolated single-pad mutation target, default Pad 3

Current passive meaning:

- read-only selected isolated pad target intent
- behavior family: `selected-isolated-pad/target-selection`
- source scope: `isolated_pad_target`
- utility action: `describe_selected_isolated_pad_target_intent`
- intent kind: `selected_isolated_pad_target_selection`
- default target pad: `3`

Current source ownership:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `rytm_randomizer/selected_target_state.py`

Current test ownership:

- `tests/test_behavior_selected_isolated_pad.py`
- `tests/test_selected_target_state.py`

This plan does not change current `L` behavior.

This plan does not authorize selected pad switching execution.

## 5. Relationship To PZ And B

Accepted runtime-adjacent mock-only safe-failure surfaces remain:

- `PZ`: return selected isolated pad to anchor only
- `B`: back to current anchor

`L` is planned next because it describes selected isolated pad target
vocabulary, and `PZ` depends on selected isolated pad context.

Important separation:

- `L` describes target selection intent only
- `PZ` describes selected isolated pad anchor-return readiness
- `B` describes current-anchor return intent readiness
- `L` does not switch selected pads
- `PZ` does not return anchors
- `B` does not return current anchors
- no command executes
- no MIDI is sent
- no ports are opened
- no hardware is touched

## 6. What Future Mock-Only L Tests Should Prove

Future mock-only tests for `L` should prove:

- importing relevant modules prints nothing
- `L` remains read-only
- `L` target-selection intent is deterministic
- `L` reports default target Pad 3 without creating runtime selected pad state
- selected pad switching is not executed
- selected isolated pad runtime state is not created by `L`
- missing selected target context fails safely where future readiness checks
  depend on it
- unsupported selected target context fails safely
- stale selected target context fails safely
- invalid selected target context fails safely
- repeated target-readiness checks are deterministic
- returned metadata is copy-safe
- no selected pad switch is executed
- no anchor return is executed
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

- `tests/test_runtime_adjacent_mock_only_l.py`

Likely existing source files to exercise:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `rytm_randomizer/selected_target_state.py`
- `rytm_randomizer/selected_isolated_pad_runtime_state.py`
- `rytm_randomizer/mock_midi.py`

Likely passive CLI command to guard:

- `python -m rytm_randomizer.cli preview-command L`

Files that should not be changed by the future test-only slice unless a
separate review explicitly approves it:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- package metadata files

If a new test file is created later, `Scripts/closeout_check.ps1` may need a
new closeout label such as:

- `=== Test: Runtime-Adjacent Mock-Only L ===`

This plan does not make that closeout update.

## 8. Proposed Future Test Cases

Future tests should cover these exact behaviors:

- import safety for the runtime-adjacent `L` test path
- default `L` target intent remains passive and deterministic
- default Pad 3 target context is described without switching pads
- unset selected target state remains unavailable and safe
- unsupported selected target state remains unavailable and safe
- stale selected target state remains unavailable and safe
- invalid selected target state remains unavailable and safe
- repeated selected target checks are deterministic
- returned target metadata is copy-safe
- `MockMidiSender` remains empty for failed readiness
- passive CLI `preview-command L` remains read-only
- no active command names are exposed by the runtime-adjacent `L` path
- no real MIDI libraries are imported
- package metadata remains untouched

The future tests should not require hardware.

The future tests should not require real MIDI libraries.

## 9. MockMidiSender Position

`MockMidiSender` may be used in future tests only to prove that no messages
are emitted by the runtime-adjacent `L` path when readiness fails or when
target selection remains descriptive only.

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
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
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

## 11. Preconditions Before Future Mock-Only L Implementation

Before implementing this test-only plan:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- this test plan is reviewed and accepted
- future implementation scope is limited to test-only mock behavior
- passive CLI remains read-only
- no selected pad switching execution is added
- no runtime selected pad state mutation is added
- no real MIDI libraries are required
- no hardware is required
- no ports are opened

## 12. Stop Conditions

Stop immediately if a future slice proposes:

- executing `L`
- switching selected pads
- mutating selected pad state
- returning selected pad anchors
- returning current anchors
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

- Option A: review/accept this `L` runtime-adjacent mock-only safe-failure
  test plan
- Option B: pause at this planning checkpoint
- Option C: create a more detailed test-only implementation plan after
  accepting this test plan
- Option D: return to broader behavior-parity packet work before implementation

## 14. Recommendation

Do a docs-only review/acceptance gate for this test plan next.

After that, the safest implementation branch would be a tiny test-only slice
for `L` runtime-adjacent safe-failure coverage.

Do not implement tests yet.

Do not implement execution.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 15. Decision

The next runtime-adjacent mock-only test-plan candidate is `L`.

The plan is documentation-only.

`L` remains planning-only until this plan is reviewed and accepted.

Accepted runtime-adjacent mock-only safe-failure surfaces remain:

- `PZ`
- `B`

The next recommended task is a docs-only review/acceptance gate for this test
plan.

Hardware remains off.

No implementation in this slice.

# V1.34 Behavior Parity First Runtime-Adjacent Mock-Only Test Plan

## 1. Purpose

Define the first runtime-adjacent mock-only test plan after the accepted
runtime/execution boundary decision.

This plan identifies a tiny candidate for future mock-only testing and records
what must be proven before any implementation work.

This is a documentation-only test plan.

It adds no implementation, tests, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this test-plan slice:

- `ccf410d Add runtime execution boundary decision review after PZ`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime/execution boundary decision reviewed and accepted
- first runtime-adjacent mock-only test plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_EXECUTION_BOUNDARY_DECISION_NOTE_AFTER_PZ_TIMELINE_REVIEW_REVIEW.md`

Accepted upstream decision:

- runtime-readiness vocabulary remains allowed only as read-only safety
  language
- execution remains outside the current project phase
- future runtime-adjacent work must remain documentation-only or mock-only
  until separately approved
- active execution, real MIDI, ports, and hardware validation remain absent

This plan stays inside that boundary.

## 4. First Runtime-Adjacent Candidate

The first candidate for future mock-only runtime-adjacent tests is:

- `PZ`: return selected isolated pad to anchor only

Reason:

- `PZ` is already represented as read-only selected isolated pad
  anchor-return readiness
- `PZ` already models runtime-adjacent readiness without execution
- default `PZ` context fails safely when anchor context is unavailable
- `PZ` is a better first candidate than mutation, scene, MIDI, or hardware
  behavior because it can stay entirely inert

This plan does not select a real hardware candidate.

This plan does not authorize `PZ` execution.

## 5. What Future Mock-Only Tests Should Prove

Future mock-only tests for this candidate should prove:

- importing relevant modules prints nothing
- `PZ` remains read-only
- default `PZ` context fails safely
- missing selected target context fails safely
- missing anchor context fails safely
- unsupported selected target or anchor context fails safely
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

## 6. Proposed Future Test Ownership

Future mock-only implementation, if separately approved, should stay in a
small test-only scope.

Likely future test file:

- `tests/test_runtime_adjacent_mock_only_pz.py`

Likely existing source files to exercise:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `rytm_randomizer/selected_isolated_pad_runtime_state.py`
- `rytm_randomizer/selected_target_state.py`
- `rytm_randomizer/anchor_state.py`
- `rytm_randomizer/mock_midi.py`

Files that should not be changed by the future test-only slice unless a
separate review explicitly approves it:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- package metadata files

If a new test file is created later, `Scripts/closeout_check.ps1` may need a
new closeout label such as:

- `=== Test: Runtime-Adjacent Mock-Only PZ ===`

This plan does not make that closeout update.

## 7. Proposed Future Test Cases

Future tests should cover these exact behaviors:

- import safety for the runtime-adjacent test path
- default `PZ` readiness remains unavailable and safe
- injected selected target without anchor remains unavailable and safe
- injected anchor without selected target remains unavailable and safe
- unsupported selected target remains unavailable and safe
- unsupported anchor remains unavailable and safe
- stale selected target or anchor remains unavailable and safe
- invalid selected target or anchor remains unavailable and safe
- repeated readiness checks are deterministic
- returned metadata is copy-safe
- any `MockMidiSender` used by tests remains empty unless a test explicitly
  records inert mock messages
- passive CLI commands do not construct or use runtime-adjacent execution
  objects

The future tests should not require hardware.

The future tests should not require real MIDI libraries.

## 8. Mock-Only Sender Position

`MockMidiSender` may be used in future tests only to prove that no messages
are emitted by the runtime-adjacent `PZ` path.

For this candidate, the safest expected result is:

- zero real MIDI sends
- zero mock sends for failed readiness
- no port interaction
- no hardware interaction

If a later test records an inert mock message, that must be separately
reviewed and must remain mock-only.

## 9. Explicit Non-Goals

This plan does not include:

- implementation
- new tests
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

## 10. Preconditions Before Future Mock-Only Implementation

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

## 11. Stop Conditions

Stop immediately if a future slice proposes:

- executing `PZ`
- switching selected pads
- returning anchors
- mutating runtime state
- dispatching commands
- importing a real MIDI library
- opening a MIDI port
- sending MIDI
- changing package metadata
- touching `rytm_hybrid_randomizer_v134.py`
- requiring hardware
- adding active CLI behavior

## 12. Safe Next Options

Safe next branches:

- Option A: review/accept this mock-only test plan
- Option B: pause at this planning checkpoint
- Option C: create a more detailed test-only implementation plan after
  accepting this test plan
- Option D: return to a broader roadmap/progress report before implementation

## 13. Recommendation

Do a docs-only review/acceptance gate for this test plan next.

After that, the safest implementation branch would be a tiny test-only slice
for `PZ` runtime-adjacent safe-failure coverage.

Do not implement execution.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 14. Decision

The first runtime-adjacent mock-only test-plan candidate is `PZ`.

The plan is documentation-only.

The next recommended task is a docs-only review/acceptance gate for this test
plan.

Hardware remains off.

No implementation in this slice.

## 15. Review Status

This test plan is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_ADJACENT_MOCK_ONLY_TEST_PLAN_REVIEW.md`

The review accepts `PZ` as the first runtime-adjacent mock-only safe-failure
candidate.

The next recommended task is a tiny test-only `PZ` runtime-adjacent
safe-failure test slice, if explicitly approved.

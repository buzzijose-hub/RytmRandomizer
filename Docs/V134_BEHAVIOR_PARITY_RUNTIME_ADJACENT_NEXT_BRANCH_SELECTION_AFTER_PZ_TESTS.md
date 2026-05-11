# V1.34 Behavior Parity Runtime-Adjacent Next Branch Selection After PZ Tests

## 1. Purpose

Select the next safe branch after the accepted runtime-adjacent mock-only
progress report after `PZ` tests.

This is a documentation-only branch selection note.

It chooses the next planning direction only.

It adds no implementation, tests, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `ebf2d5d Add runtime adjacent mock-only progress report review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime/execution boundary accepted
- first runtime-adjacent mock-only `PZ` safe-failure test milestone accepted
- runtime-adjacent mock-only progress report after `PZ` tests reviewed and
  accepted
- next branch now being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream State

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_ADJACENT_MOCK_ONLY_PROGRESS_REPORT_AFTER_PZ_TESTS_REVIEW.md`

Accepted current runtime-adjacent mock-only candidate:

- `PZ`: return selected isolated pad to anchor only

Current accepted meaning:

- `PZ` remains the only accepted runtime-adjacent mock-only safe-failure
  candidate
- `PZ` remains read-only, inert, non-executable, and non-hardware-facing
- closeout includes `Runtime-Adjacent Mock-Only PZ`
- execution, real MIDI, ports, package metadata changes, active behavior, and
  hardware validation remain absent

## 4. Candidate Options Considered

Option A:

- pause at the accepted `PZ` mock-only safe-failure checkpoint

Option B:

- create a docs-only safe-failure test plan for `B`: back to current anchor

Option C:

- create a docs-only safe-failure test plan for another selected isolated pad
  command

Option D:

- create a broader user-facing behavior-parity progress/timeline update

Option E:

- continue runtime/execution boundary documentation without selecting a
  specific command candidate

## 5. Selected Next Branch

Selected next branch:

- docs-only runtime-adjacent mock-only safe-failure test plan for `B`

Selected candidate for planning:

- `B`: back to current anchor

Important scope boundary:

- `B` is selected for planning only
- `B` is not accepted as a runtime-adjacent mock-only test candidate yet
- no `B` safe-failure tests are added in this slice
- no `B` implementation changes are added in this slice
- no `B` execution path is added in this slice

## 6. Why B Is The Next Planning Candidate

`B` is a good next planning candidate because:

- it already exists in passive command metadata
- it already has read-only behavior helper coverage
- it represents current-anchor return vocabulary
- it is adjacent to future runtime/execution concerns
- it can be planned as safe-failure coverage without executing anchor return
- it does not require real MIDI, ports, hardware, or active CLI behavior
- it complements `PZ` without widening into mutation, scenes, or hardware

`B` is not selected for implementation yet.

The next slice should only plan what a future mock-only `B` safe-failure test
would prove.

## 7. Expected Future B Test-Plan Questions

A future docs-only `B` test plan should answer:

- what does `B` readiness mean without executing anchor return?
- what current-anchor context is required?
- how should missing current-anchor context fail safely?
- how should unsupported current-anchor context fail safely?
- how should stale or invalid current-anchor context fail safely?
- how should `MockMidiSender` remain empty when readiness fails?
- how should passive CLI behavior remain unchanged?
- how should package metadata remain untouched?
- how should V1.34 reference protection remain enforced?

These are planning questions only.

## 8. What Is Not Selected

This note does not select:

- `L` selected isolated pad target switching
- `PM` isolated pad mutation
- `PS` isolated pad SRC mutation
- `PF` isolated pad filter mutation
- `PA` isolated pad amp mutation
- `PL` isolated pad LFO mutation
- `PO` isolated pad morph mutation
- `PB` isolated pad body mutation
- `PG` isolated pad grit mutation
- any scene command
- any group mutation command
- any active CLI command
- any hardware-facing command

Those remain out of scope for this branch selection.

## 9. Confirmed Absent Behavior

The following remain intentionally absent:

- CLI execution wiring
- command dispatch
- command execution
- scene execution
- selected pad switching execution
- selected pad anchor return execution
- current anchor return execution
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

## 10. Preconditions Before Any Future B Test Implementation

Before any future test-only `B` implementation:

- clean Git status
- full closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- docs-only `B` test plan exists
- docs-only `B` test plan is reviewed and accepted
- implementation remains test-only/mock-only
- no execution path is added
- no real MIDI libraries are imported
- no ports are opened
- no hardware is required

## 11. Safe Next Options

Safe next branches:

- Option A: create a docs-only `B` runtime-adjacent mock-only safe-failure
  test plan
- Option B: pause at this branch selection checkpoint
- Option C: create a docs-only review/acceptance gate for this branch
  selection note
- Option D: create a broader behavior-parity progress/timeline update

## 12. Recommendation

Do a docs-only review/acceptance gate for this branch selection note next.

After that, create the docs-only `B` runtime-adjacent mock-only safe-failure
test plan if explicitly continuing.

Do not implement tests yet.

Do not implement execution.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 13. Decision

The next selected branch is:

- docs-only `B` runtime-adjacent mock-only safe-failure test plan

`PZ` remains the only accepted runtime-adjacent mock-only safe-failure
candidate at this checkpoint.

`B` is selected for planning only.

Hardware remains off.

No implementation in this slice.

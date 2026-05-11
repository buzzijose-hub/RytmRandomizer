# V1.34 Behavior Parity Runtime-Adjacent Next Branch Selection After PZ And B Timeline Review

## 1. Purpose

Select the next safe runtime-adjacent planning branch after the accepted
post-`PZ`/`B` behavior-parity progress timeline review.

This is a documentation-only branch selection note.

It chooses the next planning direction only.

It adds no implementation, tests, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `cac71d1 Add behavior parity progress timeline review after PZ and B`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime/execution boundary accepted
- runtime-adjacent mock-only `PZ` safe-failure tests accepted
- runtime-adjacent mock-only `B` safe-failure tests accepted
- post-`PZ`/`B` progress timeline reviewed and accepted
- next runtime-adjacent branch now being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream State

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_PROGRESS_TIMELINE_AFTER_PZ_AND_B_REVIEW.md`

Accepted runtime-adjacent mock-only safe-failure surfaces:

- `PZ`: return selected isolated pad to anchor only
- `B`: back to current anchor

Current accepted meaning:

- `PZ` remains read-only selected isolated pad anchor-return readiness
- `B` remains read-only current-anchor return intent readiness
- both remain safe-failure surfaces only
- both remain inert, non-executable, and non-hardware-facing
- closeout includes `Runtime-Adjacent Mock-Only PZ`
- closeout includes `Runtime-Adjacent Mock-Only B`
- execution, real MIDI, ports, package metadata changes, active behavior, and
  hardware validation remain absent

## 4. Candidate Options Considered

Option A:

- pause at the accepted `PZ`/`B` progress timeline checkpoint

Option B:

- select a third runtime-adjacent mock-only safe-failure planning candidate

Option C:

- return to broader behavior-parity packet work

Option D:

- create a broader user-facing project roadmap

Option E:

- continue documentation-only runtime boundary refinement without selecting a
  specific command candidate

## 5. Selected Next Branch

Selected next branch:

- docs-only `L` runtime-adjacent mock-only safe-failure test plan

Selected candidate for planning:

- `L`: select isolated single-pad mutation target, default Pad 3

Important scope boundary:

- `L` is selected for planning only
- `L` is not accepted as a runtime-adjacent mock-only test candidate yet
- no `L` safe-failure tests are added in this slice
- no `L` implementation changes are added in this slice
- no selected pad switching execution is added in this slice
- no execution path is added in this slice

## 6. Why L Is The Next Planning Candidate

`L` is a good next planning candidate because:

- it already exists in passive command metadata
- it already has read-only behavior helper coverage
- it represents selected isolated pad target vocabulary
- it is adjacent to selected target readiness
- it complements `PZ`, which depends on selected isolated pad context
- it can be planned as safe-failure coverage without switching pads
- it does not require real MIDI, ports, hardware, or active CLI behavior
- it avoids widening immediately into mutation commands, scenes, or hardware

`L` is not selected for implementation yet.

The next slice should only plan what a future mock-only `L` safe-failure test
would prove.

## 7. Expected Future L Test-Plan Questions

A future docs-only `L` test plan should answer:

- what does `L` readiness mean without switching selected pads?
- what selected isolated pad target context is required?
- how should missing target context fail safely?
- how should unsupported target context fail safely?
- how should stale or invalid target context fail safely?
- how should `MockMidiSender` remain empty when readiness fails?
- how should passive CLI behavior remain unchanged?
- how should package metadata remain untouched?
- how should V1.34 reference protection remain enforced?

These are planning questions only.

## 8. What Is Not Selected

This note does not select:

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
- current anchor return execution
- selected pad switching execution
- selected pad anchor return execution
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

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 10. Preconditions Before Any Future L Test Implementation

Before any future test-only `L` implementation:

- clean Git status
- full closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- docs-only `L` test plan exists
- docs-only `L` test plan is reviewed and accepted
- implementation remains test-only/mock-only
- no selected pad switching execution is added
- no execution path is added
- no real MIDI libraries are imported
- no ports are opened
- no hardware is required

## 11. Safe Next Options

Safe next branches:

- Option A: create a docs-only `L` runtime-adjacent mock-only safe-failure
  test plan
- Option B: pause at this branch selection checkpoint
- Option C: create a docs-only review/acceptance gate for this branch
  selection note
- Option D: return to broader behavior-parity packet work

## 12. Recommendation

Do a docs-only review/acceptance gate for this branch selection note next.

After that, create the docs-only `L` runtime-adjacent mock-only safe-failure
test plan if explicitly continuing.

Do not implement tests yet.

Do not implement execution.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 13. Decision

The next selected branch is:

- docs-only `L` runtime-adjacent mock-only safe-failure test plan

Accepted runtime-adjacent mock-only safe-failure surfaces remain:

- `PZ`
- `B`

`L` is selected for planning only.

Hardware remains off.

No implementation in this slice.

## 14. Review Status

This branch selection note is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_ADJACENT_NEXT_BRANCH_SELECTION_AFTER_PZ_AND_B_TIMELINE_REVIEW_REVIEW.md`

The review accepts the docs-only `L` runtime-adjacent mock-only safe-failure
test plan as the next planning branch.

`L` remains planning-only.

No `L` tests, selected pad switching execution, dispatch, MIDI, ports, active
behavior, or hardware behavior are authorized by the review.

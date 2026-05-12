# V1.34 Behavior Parity Runtime-Adjacent Next Branch Selection After L Tests

## 1. Purpose

Select the next safe branch after the accepted runtime-adjacent mock-only
progress report after `L` tests.

This is a documentation-only branch selection note.

It chooses the next planning direction only.

It adds no implementation, tests, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `122fca3 Add runtime adjacent mock-only progress report review after L tests`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime/execution boundary accepted
- runtime-adjacent mock-only `PZ` safe-failure tests accepted
- runtime-adjacent mock-only `B` safe-failure tests accepted
- runtime-adjacent mock-only `L` safe-failure tests accepted
- runtime-adjacent mock-only progress report after `L` tests reviewed and
  accepted
- next branch now being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream State

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_ADJACENT_MOCK_ONLY_PROGRESS_REPORT_AFTER_L_TESTS_REVIEW.md`

Accepted runtime-adjacent mock-only safe-failure surfaces:

- `PZ`: return selected isolated pad to anchor only
- `B`: back to current anchor
- `L`: select isolated single-pad mutation target, default Pad 3

Current accepted meaning:

- `PZ` remains read-only selected isolated pad anchor-return readiness
- `B` remains read-only current-anchor return intent readiness
- `L` remains read-only selected isolated pad target intent
- all three remain safe-failure surfaces only
- all three remain inert, non-executable, and non-hardware-facing
- closeout includes `Runtime-Adjacent Mock-Only PZ`
- closeout includes `Runtime-Adjacent Mock-Only B`
- closeout includes `Runtime-Adjacent Mock-Only L`
- execution, real MIDI, ports, package metadata changes, active behavior, and
  hardware validation remain absent

## 4. Candidate Options Considered

Option A:

- pause at the accepted `PZ`, `B`, and `L` mock-only safe-failure checkpoint

Option B:

- create a user-facing behavior-parity progress/timeline update after `PZ`,
  `B`, and `L`

Option C:

- select a fourth runtime-adjacent mock-only safe-failure candidate

Option D:

- return to broader behavior-parity packet work before selecting another
  runtime-adjacent candidate

Option E:

- continue runtime/execution boundary documentation without selecting a
  specific command candidate

## 5. Selected Next Branch

Selected next branch:

- user-facing behavior-parity progress/timeline update after `PZ`, `B`, and
  `L`

Important scope boundary:

- no fourth runtime-adjacent command candidate is selected in this slice
- no new safe-failure tests are planned in this slice
- no implementation changes are added in this slice
- no execution path is added in this slice

## 6. Why A Progress/Timeline Update Is The Next Branch

A progress/timeline update is the safest next branch because:

- `PZ`, `B`, and `L` now form a meaningful runtime-adjacent trio
- the project has crossed from two safe-failure surfaces to three
- closeout now protects all accepted runtime-adjacent mock-only surfaces
- choosing a fourth candidate immediately could widen scope too quickly
- a user-facing timeline can clarify what this means for the dream project
- the timeline can decide whether to pause, continue candidate planning, or
  return to behavior-parity packet work

This branch keeps the project understandable without adding execution.

## 7. Fourth Candidate Position

No fourth runtime-adjacent mock-only candidate is selected yet.

Candidate selection remains parked until after the progress/timeline update.

Potential later candidates may include selected isolated pad utilities, undo
state helpers, selected profile helpers, or other runtime-adjacent commands,
but they must be separately reviewed before any test plan or implementation.

Any future fourth candidate must remain:

- documentation-only first
- mock-only/test-only if implemented later
- non-executable
- non-hardware-facing
- free of real MIDI libraries
- free of port opening
- free of package metadata changes

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
- `P` selected profile change
- `M` selected profile anchor load
- `E` commit current state as new anchor
- `U` undo previous script-generated state
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

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 10. Preconditions Before Any Future Fourth Candidate Plan

Before any future fourth runtime-adjacent mock-only candidate plan:

- clean Git status
- full closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- post-`PZ`/`B`/`L` progress timeline exists
- the fourth candidate is explicitly selected
- the candidate remains documentation-only first
- no execution path is added
- no real MIDI libraries are imported
- no ports are opened
- no hardware is required

## 11. Safe Next Options

Safe next branches:

- Option A: create a user-facing progress/timeline update after `PZ`, `B`, and
  `L`
- Option B: pause at this branch selection checkpoint
- Option C: create a docs-only review/acceptance gate for this branch
  selection note
- Option D: return to broader behavior-parity packet work after the timeline

## 12. Recommendation

Do a docs-only review/acceptance gate for this branch selection note next.

After that, create the user-facing behavior-parity progress/timeline update
after `PZ`, `B`, and `L` if continuing.

Do not select a fourth candidate yet.

Do not implement tests yet.

Do not implement execution.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 13. Decision

The next selected branch is:

- user-facing behavior-parity progress/timeline update after `PZ`, `B`, and
  `L`

No fourth runtime-adjacent mock-only candidate is selected yet.

Accepted runtime-adjacent mock-only safe-failure surfaces remain:

- `PZ`
- `B`
- `L`

Hardware remains off.

No implementation in this slice.

## 14. Review Status

This branch selection note is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_ADJACENT_NEXT_BRANCH_SELECTION_AFTER_L_TESTS_REVIEW.md`

The review accepts the user-facing behavior-parity progress/timeline update
after `PZ`, `B`, and `L` as the next planning branch.

No fourth runtime-adjacent mock-only candidate is selected by the review.

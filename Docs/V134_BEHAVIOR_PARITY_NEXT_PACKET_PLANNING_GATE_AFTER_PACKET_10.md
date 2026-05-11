# V1.34 Behavior Parity Next Packet Planning Gate After Packet 10

## 1. Purpose

Choose the next safe behavior-parity branch after the accepted broader
progress report review after Packet 10.

This document is a planning gate only. It does not implement anything and does
not authorize implementation by itself.

This document adds no tests, CLI wiring, dispatch, command execution, MIDI,
ports, package metadata changes, active behavior, runtime behavior,
selected-pad runtime state, selected-profile runtime state, anchor loading
execution, mutation execution, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `600b333 Add behavior parity progress report review after Packet 10`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 1 complete
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete
- Packet 4 complete
- Packet 5 accepted as meaningful Pad 1 lane behavior progress
- Packet 6 Pad 2 command-helper scope covered
- Packet 7 complete
- Packet 8 Pad 4 command-helper scope covered
- Packet 9 covered and accepted for the current read-only intent-only behavior
  phase
- Packet 10 covered and accepted for the current read-only intent-only behavior
  phase
- next packet planning gate now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Accepted Behavior-Parity Baseline

Accepted behavior-parity baseline:

- Packet 1 Menu/Utility Behavior Parity complete
- Packet 2 Anchor/Profile Behavior Parity accepted progress
- Packet 3 Mutation-Depth and Guarded Input Behavior Parity complete
- Packet 4 Scene and Group Intent Behavior Parity complete
- Packet 5 Pad 1 Lane Behavior accepted progress
- Packet 6 Pad 2 Lane Behavior command-helper scope covered
- Packet 7 Pad 3 Lane Behavior complete
- Packet 8 Pad 4 Lane Behavior command-helper scope covered
- Packet 9 Undo/Commit/State Behavior Parity covered for the current
  read-only intent-only behavior phase
- Packet 10 Selected Profile Workflow Behavior Parity covered for the current
  read-only intent-only behavior phase

Current behavior helper surface:

- `rytm_randomizer/behavior_menu_utility.py`
- `rytm_randomizer/behavior_anchor_profile.py`
- `rytm_randomizer/behavior_mutation_depth.py`
- `rytm_randomizer/behavior_scene_group.py`
- `rytm_randomizer/behavior_pad1_lane.py`
- `rytm_randomizer/behavior_pad2_lane.py`
- `rytm_randomizer/behavior_pad3_lane.py`
- `rytm_randomizer/behavior_pad4_lane.py`
- `rytm_randomizer/behavior_undo_commit_state.py`
- `rytm_randomizer/behavior_selected_profile.py`

Current behavior closeout coverage:

- `=== Test: Behavior Menu Utility ===`
- `=== Test: Behavior Anchor Profile ===`
- `=== Test: Behavior Mutation Depth ===`
- `=== Test: Behavior Scene Group ===`
- `=== Test: Behavior Pad 1 Lane ===`
- `=== Test: Behavior Pad 2 Lane ===`
- `=== Test: Behavior Pad 3 Lane ===`
- `=== Test: Behavior Pad 4 Lane ===`
- `=== Test: Behavior Undo Commit State ===`
- `=== Test: Behavior Selected Profile ===`

## 4. Candidate Next Branches

Safe next branches:

- Option A: Packet 11 selected isolated pad utility behavior planning
- Option B: remaining anchor/profile widening planning
- Option C: deeper runtime lane-state modeling planning
- Option D: user-facing progress/timeline update
- Option E: broader behavior-parity roadmap update
- Option F: pause at the accepted post-Packet-10 progress checkpoint

All options require a separate docs-only plan and review before any
implementation.

## 5. Recommended Next Branch

Recommended next branch:

- Packet 11 selected isolated pad utility behavior planning

Reasons:

- Packet 10 closed the current selected-profile workflow helper surface.
- Existing passive metadata already includes isolated pad utility commands
  `L` and `PZ`.
- Packet 3 already covers selected isolated pad mutation-depth intent for
  `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG`.
- The selected isolated pad mutation commands depend conceptually on selected
  isolated pad state, but runtime selected-pad state still does not exist.
- Planning `L` and `PZ` next creates a safe vocabulary for selected isolated
  pad selection and selected isolated pad anchor return without implementing
  runtime selection, anchor return execution, mutation execution, dispatch,
  MIDI, ports, active behavior, or hardware behavior.
- This keeps the next move meaningful without crossing into execution.

This gate does not implement Packet 11. It only recommends a docs-only Packet
11 plan next.

## 6. Candidate Packet 11 Planning Surface

A future Packet 11 selected isolated pad utility behavior plan may consider
these existing isolated pad utility commands:

- `L`: select isolated single-pad mutation target, default Pad 3
- `PZ`: return selected isolated pad to anchor only

Existing related behavior remains owned by earlier packets:

- Packet 1 owns selected-pad status/menu behavior for `PR`.
- Packet 3 owns selected isolated pad mutation-depth intent for `PM`, `PS`,
  `PF`, `PA`, `PL`, `PO`, `PB`, and `PG`.
- Packet 5, Packet 6, Packet 7, and Packet 8 own pad lane behavior surfaces.
- Packet 9 owns state utility intent for `B`, `E`, `W`, and `U`.
- Packet 10 owns selected-profile workflow intent for `P` and `M`.

This is planning vocabulary only. The future Packet 11 plan should choose a
tiny first implementation subset instead of implementing the whole selected
isolated pad utility surface at once.

## 7. Recommended First Packet 11 Plan Shape

The next document should be:

- docs-only Packet 11 selected isolated pad utility behavior plan

The plan should decide:

- exact Packet 11 identity
- whether `L`, `PZ`, or both are in the full planning scope
- which tiny first implementation subset is safe
- whether the first slice is limited to read-only selected isolated pad
  selection intent
- how existing passive command metadata is used
- how missing selected isolated pad runtime state is represented safely
- how actual selected-pad switching remains absent
- how actual selected-pad anchor return remains absent
- how actual mutation execution remains absent
- which files a future implementation may touch
- which tests a future implementation must add or update
- how unknown or unsupported selected isolated pad utility keys fail safely
- how Packet 1 through Packet 10 behavior remains stable
- how passive CLI behavior remains unchanged

The plan should not implement code or tests.

## 8. Candidate First Implementation Target

Recommended future first implementation target:

- Packet 11A `L` only

Reasons:

- `L` is narrower than `PZ`.
- `L` can describe selected isolated pad target intent without returning an
  anchor.
- `PZ` depends on a selected isolated pad context and should remain deferred
  until `L` is planned, reviewed, and accepted.
- `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` already have read-only
  mutation-depth intent coverage in Packet 3 and should not move into Packet
  11.

## 9. Boundaries For Future Packet 11 Planning

Future Packet 11 planning must keep out of scope:

- runtime selected isolated pad state
- selected-pad switching execution
- selected-pad anchor return execution
- isolated pad mutation execution
- active depth prompt execution
- prompt/input loop execution
- dispatch
- command execution
- CLI execution wiring
- active CLI behavior
- real MIDI
- MIDI ports
- MIDI sending
- package metadata changes
- hardware behavior
- hardware validation
- Analog Four
- Pads 5-12
- machine/profile universe expansion
- SysEx
- GUI/capture

Any future Packet 11 implementation must remain read-only and intent-only
unless separately approved.

## 10. Preconditions Before Any Packet 11 Implementation

Before any Packet 11 implementation begins:

- Git status must be clean.
- Full closeout must pass.
- V1.34 reference diff must be empty.
- Package metadata diff must be empty.
- This planning gate must be reviewed and accepted.
- A docs-only Packet 11 plan must be created.
- The Packet 11 plan must be reviewed and accepted.
- The first implementation subset must be tiny.
- The implementation must remain read-only and intent-only.
- Runtime selected isolated pad state, selected-pad switching execution,
  anchor return execution, mutation execution, dispatch, command execution,
  MIDI, ports, package metadata, active behavior, and hardware behavior must
  remain out of scope.

## 11. Parallelization Position

Do not parallelize immediate Packet 11 implementation yet.

Packet 11 planning should happen first because selected isolated pad behavior
touches future runtime target state. That boundary needs one clear plan before
any code changes.

Later, independent docs-only branches could be parallelized, such as
user-facing timeline reporting and a separate remaining-gap audit, but the
Packet 11 plan itself should stay linear.

## 12. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this planning gate
- docs-only Packet 11 selected isolated pad utility behavior plan
- user-facing progress/timeline update after Packet 10
- pause at this clean planning checkpoint

## 13. Recommendation

Proceed next with a docs-only review/acceptance gate for this planning gate.

If accepted, create a docs-only Packet 11 selected isolated pad utility
behavior plan. The first future implementation target should likely be Packet
11A `L` only.

## 14. Decision

The recommended next behavior-parity branch is Packet 11 selected isolated pad
utility behavior planning.

Hardware remains off.

No implementation in this slice.

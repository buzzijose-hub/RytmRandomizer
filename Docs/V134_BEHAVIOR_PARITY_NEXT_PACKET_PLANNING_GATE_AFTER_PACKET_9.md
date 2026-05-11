# V1.34 Behavior Parity Next Packet Planning Gate After Packet 9

## 1. Purpose

Choose the next safe behavior-parity branch after the accepted broader
progress report review after Packet 9.

This document is a planning gate only. It does not implement anything and does
not authorize implementation by itself.

This document adds no tests, CLI wiring, dispatch, command execution, MIDI,
ports, package metadata changes, active behavior, runtime behavior, selected
profile runtime state, machine changes, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `1b5665c Add behavior parity progress report review after Packet 9`

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

## 4. Candidate Next Branches

Safe next branches:

- Option A: Packet 10 selected-profile workflow planning
- Option B: remaining anchor/profile widening planning
- Option C: deeper runtime lane-state modeling planning
- Option D: user-facing progress/timeline update
- Option E: broader behavior-parity roadmap update
- Option F: pause at the accepted post-Packet-9 progress checkpoint

All options require a separate docs-only plan and review before any
implementation.

## 5. Recommended Next Branch

Recommended next branch:

- Packet 10 selected-profile workflow planning

Reasons:

- Packet 9 closed the current undo/commit/state helper surface.
- The accepted post-Packet-9 review identifies broader selected-profile
  workflow as not yet implemented.
- Existing command metadata already includes `P` and `M`.
- Selected-profile workflow is a core operator concept before any deeper
  runtime profile behavior can be designed safely.
- A planning gate can separate read-only selected-profile intent from actual
  runtime selected-profile state, machine changes, anchor loading, dispatch,
  MIDI, ports, active behavior, or hardware behavior.
- This keeps the next move meaningful without widening into profile execution
  or hardware-facing behavior.

This gate does not implement Packet 10. It only recommends a docs-only Packet
10 plan next.

## 6. Candidate Packet 10 Planning Surface

A future Packet 10 selected-profile workflow behavior plan may consider these
existing profile workflow commands:

- `P`: select/switch profile and change Rytm machine
- `M`: load selected profile anchor

Existing related behavior remains owned by earlier packets:

- Packet 2 owns direct anchor/profile command intent progress.
- Packet 3 owns legacy single-profile mutation intent for `M1`, `M2`, and
  `M3`.
- Packet 9 owns state utility intent for `B`, `E`, `W`, and `U`.

This is planning vocabulary only. The future Packet 10 plan should choose a
tiny first implementation subset instead of implementing the whole
selected-profile workflow at once.

## 7. Recommended First Packet 10 Plan Shape

The next document should be:

- docs-only Packet 10 selected-profile workflow behavior plan

The plan should decide:

- exact Packet 10 identity
- whether `P`, `M`, or both are in the full planning scope
- which tiny first implementation subset is safe
- whether the first slice is limited to read-only selected-profile intent
- how existing passive command metadata is used
- how missing selected-profile runtime state is represented safely
- how actual profile selection remains absent
- how actual machine change remains absent
- how actual anchor loading remains absent
- which files a future implementation may touch
- which tests a future implementation must add or update
- how unknown or unsupported selected-profile workflow keys fail safely
- how Packet 1 through Packet 9 behavior remains stable
- how passive CLI behavior remains unchanged

The plan should not implement code or tests.

## 8. Boundaries For Future Packet 10 Planning

Future Packet 10 planning must keep out of scope:

- runtime selected-profile state
- runtime current-profile state
- profile switching execution
- machine change execution
- anchor loading execution
- active selected-profile mutation
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

Any future Packet 10 implementation must remain read-only and intent-only
unless separately approved.

## 9. Preconditions Before Any Packet 10 Implementation

Before any Packet 10 implementation begins:

- Git status must be clean.
- Full closeout must pass.
- V1.34 reference diff must be empty.
- Package metadata diff must be empty.
- This planning gate must be reviewed and accepted.
- A docs-only Packet 10 plan must be created.
- The Packet 10 plan must be reviewed and accepted.
- The first implementation subset must be tiny.
- The implementation must remain read-only and intent-only.
- Runtime selected-profile state, profile switching execution, machine changes,
  anchor loading execution, dispatch, command execution, MIDI, ports, package
  metadata, active behavior, and hardware behavior must remain out of scope.

## 10. Parallelization Position

Do not parallelize immediate Packet 10 implementation yet.

Packet 10 planning should happen first because selected-profile workflow sits
between passive metadata and eventual runtime profile state. That boundary
needs one clear plan before any code changes.

Parallel implementation may become useful later if:

- selected-profile intent is split from anchor/profile widening
- runtime-state modeling is split from read-only helper behavior
- file ownership is disjoint
- each sub-slice has its own tests
- closeout remains the synchronization point

## 11. Confirmed Absent Behavior

This planning gate adds no:

- implementation
- tests
- CLI execution wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- selected-profile runtime state
- current-profile runtime state
- profile switching
- machine changes
- anchor loading
- MIDI dependency
- `mido`
- `rtmidi`
- package metadata changes
- MIDI port discovery
- MIDI port opening
- MIDI sending
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware validation
- machine/profile universe expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 12. Safe Next Step

Next recommended task:

- review and accept this planning gate

Then, if accepted:

- create a docs-only Packet 10 selected-profile workflow behavior plan

Hardware remains off.

No implementation in this slice.

## 13. Review Status

Review document:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_PLANNING_GATE_AFTER_PACKET_9_REVIEW.md`

Review decision:

- accepted as the current behavior-parity next-packet planning direction after
  Packet 9

Accepted next branch:

- docs-only Packet 10 selected-profile workflow behavior planning

This review does not authorize implementation, selected-profile runtime state,
profile switching execution, machine changes, anchor loading execution,
dispatch, MIDI, ports, package metadata changes, active behavior, or hardware
behavior.

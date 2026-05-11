# V1.34 Behavior Parity Next Packet Planning Gate After Packet 8C

## 1. Purpose

Choose the next safe behavior-parity branch after the accepted progress report
review after Packet 8C.

This document is a planning gate only. It does not implement anything and does
not authorize implementation by itself.

This document adds no tests, CLI wiring, dispatch, command execution, MIDI,
ports, package metadata changes, active behavior, runtime behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `9247bff Add behavior parity progress report review after Packet 8C`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 1 complete
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete
- Packet 4 complete
- Packet 5 accepted as Pad 1 lane behavior progress
- Packet 6 Pad 2 command-helper scope covered
- Packet 7 complete
- Packet 8 Pad 4 command-helper scope covered
- behavior-parity progress report after Packet 8C accepted
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

Current behavior helper surface:

- `rytm_randomizer/behavior_menu_utility.py`
- `rytm_randomizer/behavior_anchor_profile.py`
- `rytm_randomizer/behavior_mutation_depth.py`
- `rytm_randomizer/behavior_scene_group.py`
- `rytm_randomizer/behavior_pad1_lane.py`
- `rytm_randomizer/behavior_pad2_lane.py`
- `rytm_randomizer/behavior_pad3_lane.py`
- `rytm_randomizer/behavior_pad4_lane.py`

Current behavior closeout coverage:

- `=== Test: Behavior Menu Utility ===`
- `=== Test: Behavior Anchor Profile ===`
- `=== Test: Behavior Mutation Depth ===`
- `=== Test: Behavior Scene Group ===`
- `=== Test: Behavior Pad 1 Lane ===`
- `=== Test: Behavior Pad 2 Lane ===`
- `=== Test: Behavior Pad 3 Lane ===`
- `=== Test: Behavior Pad 4 Lane ===`

## 4. Candidate Next Branches

Safe next branches:

- Option A: Packet 9 undo/commit/state behavior planning
- Option B: remaining anchor/profile widening planning
- Option C: deeper lane-state modeling planning
- Option D: user-facing progress/timeline update
- Option E: pause at the accepted post-Packet-8C progress checkpoint

All options require a separate docs-only plan and review before any
implementation.

## 5. Recommended Next Branch

Recommended next branch:

- Packet 9 undo/commit/state behavior planning

Reasons:

- The four-pad command-helper surface is now covered through Packet 8.
- The accepted matrix already identified undo/commit/state rows as a
  remaining behavior-parity gap.
- The relevant command keys already exist in `STATE_UTILITY_COMMANDS`.
- Undo/commit/state behavior is important for operator trust but carries more
  runtime-state risk than lane intent helpers.
- A docs-only Packet 9 plan can keep that runtime risk explicit before any
  implementation begins.
- Planning first avoids jumping directly into runtime state mutation,
  dispatch, MIDI, ports, active behavior, or hardware behavior.

This gate does not implement Packet 9. It only recommends a docs-only Packet 9
plan next.

## 6. Candidate Packet 9 Planning Surface

A future Packet 9 undo/commit/state behavior plan may consider these existing
state utility commands:

- `B`: back to current anchor
- `E`: commit current state as new anchor
- `W`: waveform exploration only
- `U`: undo previous script-generated state

Existing Packet 1 ownership remains:

- `H`: show current anchor
- `R`: print current script state

This is planning vocabulary only. The future Packet 9 plan should choose a
tiny first implementation subset instead of implementing the whole surface at
once.

## 7. Recommended First Packet 9 Plan Shape

The next document should be:

- docs-only Packet 9 undo/commit/state behavior plan

The plan should decide:

- exact Packet 9 identity
- which state utility keys are in the full planning scope
- which tiny first implementation subset is safe
- which existing passive metadata sources are allowed
- whether the first slice is limited to read-only intent descriptions
- which files a future implementation may touch
- which tests a future implementation must add or update
- how missing runtime state or unsupported keys fail safely
- how Packet 1 through Packet 8 behavior remains stable
- how passive CLI behavior remains unchanged

The plan should not implement code or tests.

## 8. Boundaries For Future Packet 9 Planning

Future Packet 9 planning must keep out of scope:

- runtime anchor restoration
- runtime anchor commit
- runtime undo stack mutation
- runtime waveform exploration
- prompt/input loop execution
- real MIDI
- MIDI ports
- dispatch
- command execution
- active CLI behavior
- hardware behavior
- hardware validation
- package metadata changes
- Analog Four
- Pads 5-12
- SysEx
- GUI/capture

Any future Packet 9 implementation must remain read-only and intent-only
unless separately approved.

## 9. Preconditions Before Any Packet 9 Implementation

Before any Packet 9 implementation begins:

- Git status must be clean.
- Full closeout must pass.
- V1.34 reference diff must be empty.
- Package metadata diff must be empty.
- This planning gate must be reviewed and accepted.
- A docs-only Packet 9 plan must be created.
- The Packet 9 plan must be reviewed and accepted.
- The first implementation subset must be tiny.
- The implementation must remain read-only and intent-only.
- Runtime prompt behavior, dispatch, command execution, MIDI, ports, package
  metadata, active behavior, and hardware behavior must remain out of scope.

## 10. Parallelization Position

Do not parallelize immediate Packet 9 implementation yet.

Packet 9 planning should happen first because undo/commit/state semantics
touch runtime-state vocabulary and need tighter review than the lane helpers.

Parallel implementation may become useful later if:

- undo/commit/state behavior is split from deeper lane-state modeling
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
- group mutation execution
- lane behavior execution
- prompt/input loop
- runtime state mutation
- undo stack mutation
- anchor commit execution
- anchor restore execution
- waveform exploration execution
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata changes
- port discovery
- port opening
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

## 12. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this planning gate
- user-facing progress/timeline update
- pause at this clean planning checkpoint

After a separate review:

- docs-only Packet 9 undo/commit/state behavior plan

## 13. Recommendation

Create the docs-only review/acceptance gate for this planning gate next.

After that, create the docs-only Packet 9 undo/commit/state behavior plan.

Do not implement undo/commit/state behavior, dispatch, MIDI, ports, active
behavior, package metadata changes, runtime execution, or hardware behavior
from this planning gate.

## 14. Decision

The recommended next behavior-parity branch is Packet 9 undo/commit/state
behavior planning.

Hardware remains off.

No implementation in this slice.

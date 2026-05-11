# V1.34 Behavior Parity Next Packet Planning Gate After Packet 7

## 1. Purpose

Choose the next safe behavior-parity branch after the accepted progress report
review after Packet 7.

This document is a planning gate only. It does not implement anything and does
not authorize implementation by itself.

This document adds no tests, CLI wiring, dispatch, command execution, MIDI,
ports, package metadata, active behavior, runtime behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `f25e550 Add behavior parity progress report review after Packet 7`

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
- behavior-parity progress report after Packet 7 accepted
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

Current behavior helper surface:

- `rytm_randomizer/behavior_menu_utility.py`
- `rytm_randomizer/behavior_anchor_profile.py`
- `rytm_randomizer/behavior_mutation_depth.py`
- `rytm_randomizer/behavior_scene_group.py`
- `rytm_randomizer/behavior_pad1_lane.py`
- `rytm_randomizer/behavior_pad2_lane.py`
- `rytm_randomizer/behavior_pad3_lane.py`

Current behavior closeout coverage:

- `=== Test: Behavior Menu Utility ===`
- `=== Test: Behavior Anchor Profile ===`
- `=== Test: Behavior Mutation Depth ===`
- `=== Test: Behavior Scene Group ===`
- `=== Test: Behavior Pad 1 Lane ===`
- `=== Test: Behavior Pad 2 Lane ===`
- `=== Test: Behavior Pad 3 Lane ===`

## 4. Candidate Next Branches

Safe next branches:

- Option A: Packet 8 Pad 4 Lane Behavior planning
- Option B: undo/commit/state behavior planning
- Option C: remaining anchor/profile widening planning
- Option D: user-facing progress/timeline update
- Option E: pause at the accepted post-Packet-7 progress checkpoint

All options require a separate docs-only plan and review before any
implementation.

## 5. Recommended Next Branch

Recommended next branch:

- Packet 8 Pad 4 Lane Behavior planning

Reasons:

- Pad 4 is the remaining captured pad-lane behavior family after Pad 1, Pad 2,
  and Pad 3 progress.
- Pad 4 scope is small and currently limited to existing `PAD4_COMMANDS`
  metadata.
- Completing Pad 4 read-only command-helper planning keeps the project moving
  toward the full four-pad behavior foundation.
- Pad 4 planning avoids jumping into undo/commit/state runtime semantics too
  early.
- Pad 4 planning continues the same read-only, intent-only result pattern used
  by Pad 1, Pad 2, and Pad 3 behavior helpers.

This gate does not implement Packet 8. It only recommends a docs-only Packet
8 plan next.

## 6. Candidate Packet 8 Planning Surface

A future Packet 8 Pad 4 lane behavior plan may consider these existing Pad 4
lane commands:

- `P4A`: return Pad 4 to BD Acoustic body/accent anchor / home
- `P4R`: rotate Pad 4 through BD Acoustic behavior modes
- `P4X`: safely mutate the currently loaded Pad 4 mode

Existing Packet 1 ownership remains:

- `P4M`: show Pad 4 BD Acoustic body / accent menu

This is planning vocabulary only. The future Packet 8 plan should choose a
tiny first implementation subset instead of implementing the whole surface at
once.

## 7. Recommended First Packet 8 Plan Shape

The next document should be:

- docs-only Packet 8 Pad 4 lane behavior plan

The plan should decide:

- exact Packet 8 identity
- which Pad 4 lane keys are in the full planning scope
- which tiny first implementation subset is safe
- which existing passive metadata sources are allowed
- which files a future implementation may touch
- which tests a future implementation must add or update
- how unknown or unsupported Pad 4 lane keys fail safely
- how Packet 1 through Packet 7 behavior remains stable
- how passive CLI behavior remains unchanged

The plan should not implement code or tests.

## 8. Boundaries For Future Packet 8 Planning

Future Packet 8 planning must keep out of scope:

- runtime Pad 4 state
- selected Pad 4 mode runtime state
- runtime Pad 4 anchor loading
- runtime Pad 4 mode rotation
- runtime Pad 4 mutation execution
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

Any future Packet 8 implementation must remain read-only and intent-only
unless separately approved.

## 9. Preconditions Before Any Packet 8 Implementation

Before any Packet 8 implementation begins:

- Git status must be clean.
- Full closeout must pass.
- V1.34 reference diff must be empty.
- package metadata diff must be empty.
- This planning gate must be reviewed and accepted.
- A docs-only Packet 8 plan must be created.
- The Packet 8 plan must be reviewed and accepted.
- The first implementation subset must be tiny.
- The implementation must remain read-only and intent-only.
- Runtime prompt behavior, dispatch, command execution, MIDI, ports, package
  metadata, active behavior, and hardware behavior must remain out of scope.

## 10. Parallelization Position

Do not parallelize immediate Packet 8 implementation yet.

Packet 8 planning should happen first because the Pad 4 result shape and test
expectations need to be explicit before any implementation begins.

Parallel implementation may become useful later if:

- Pad 4 behavior is split from undo/commit/state behavior.
- file ownership is disjoint.
- each sub-slice has its own tests.
- closeout remains the synchronization point.

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
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata
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

- Review and accept this next packet planning gate.
- Create a docs-only Packet 8 Pad 4 lane behavior plan.
- Write a user-facing progress/timeline update.
- Pause at this clean planning checkpoint.

## 13. Recommendation

Review and accept this planning gate next.

After review, create a docs-only Packet 8 Pad 4 lane behavior plan.

Do not implement Pad 4 lane behavior, dispatch, MIDI, ports, active behavior,
or hardware behavior from this gate.

## 14. Decision

The recommended next behavior-parity branch is Packet 8 Pad 4 Lane Behavior
planning.

Hardware remains off.

No real MIDI, ports, active behavior, package metadata, runtime execution, or
hardware behavior exists.

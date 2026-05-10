# V1.34 Behavior Parity Next Packet Planning Gate

## 1. Purpose

Define the safe planning gate for choosing the next behavior-parity packet
after the accepted progress report after Packet 4.

This document is planning-only. It does not choose implementation details
that bypass review, and it adds no code, tests, CLI wiring, dispatch,
execution, MIDI, ports, package metadata, active behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `aa2fa92 Add behavior parity progress report after Packet 4 review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity matrix documented and reviewed
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- behavior-parity progress report after Packet 4 accepted
- next packet planning gate now being documented

Hardware status:

- Analog Rytm MKII off.
- Analog Four MKII off.
- Hardware not required.

## 3. Current Accepted Baseline

Accepted behavior-parity baseline:

- Packet 1: complete for menu/status and utility/session intent
- Packet 2: accepted progress for anchor/profile intent
- Packet 3: complete for mutation-depth and guarded input intent
- Packet 4: complete for scene and group intent

Current behavior helper surface:

- `rytm_randomizer/behavior_menu_utility.py`
- `rytm_randomizer/behavior_anchor_profile.py`
- `rytm_randomizer/behavior_mutation_depth.py`
- `rytm_randomizer/behavior_scene_group.py`

Current behavior closeout coverage:

- `=== Test: Behavior Menu Utility ===`
- `=== Test: Behavior Anchor Profile ===`
- `=== Test: Behavior Mutation Depth ===`
- `=== Test: Behavior Scene Group ===`

## 4. Candidate Next Branches

Safe next branches:

- Option A: Packet 5 Pad 1 Lane Behavior planning
- Option B: remaining anchor/profile widening planning
- Option C: undo/commit/state behavior planning
- Option D: user-facing progress/timeline update
- Option E: pause at the accepted post-Packet-4 progress checkpoint

All options require a separate docs-only plan and review before any
implementation.

## 5. Recommended Next Branch

Recommended next branch:

- Packet 5 Pad 1 Lane Behavior planning

Reasons:

- Pad 1 is the primary musical lane and closest to the fun sound-design loop.
- Pad 1 scope is smaller than full multi-pad behavior.
- Pad 1 lane rows already exist in the accepted behavior parity matrix.
- Packet 1, Packet 2, Packet 3, and Packet 4 now provide stable read-only
  vocabulary that Pad 1 lane planning can build on.
- Remaining anchor/profile widening can stay parked while a lane behavior
  packet is planned carefully.

This gate does not implement Packet 5. It only recommends a docs-only Packet
5 plan next.

## 6. Candidate Packet 5 Planning Surface

A future Packet 5 Pad 1 lane behavior plan may consider these existing
captured Pad 1 lane areas:

- Pad 1 current BD engine status and mutation:
  - `BR`
  - `BM`
- Pad 1 BD FM lane:
  - `FM`
  - `FT`
  - `FK`
  - `FG`
  - `FZ`
- Pad 1 BD Plastic lane:
  - `BP`
  - `PD`
  - `PT`
  - `PK`
  - `PX`
  - `PBH`
- Pad 1 BD Silky lane:
  - `BI`
  - `SM`
  - `ST`
  - `SK`
  - `SC`
  - `SBH`

This is planning vocabulary only. The future Packet 5 plan should choose a
tiny first implementation subset instead of implementing the whole surface at
once.

## 7. Recommended First Packet 5 Plan Shape

The next document should be:

- docs-only Packet 5 Pad 1 lane behavior plan

The plan should decide:

- exact Packet 5 identity
- which Pad 1 lane keys are in the full planning scope
- which tiny first implementation subset is safe
- which existing passive metadata sources are allowed
- which files a future implementation may touch
- which tests a future implementation must add or update
- how unknown or unsupported Pad 1 lane keys fail safely
- how Packet 1 through Packet 4 behavior remains stable
- how passive CLI behavior remains unchanged

The plan should not implement code or tests.

## 8. Boundaries For Future Packet 5 Planning

Future Packet 5 planning must keep out of scope:

- runtime engine rotation
- runtime mutation execution
- runtime discovery execution
- runtime anchor return execution
- selected Pad 1 runtime state mutation
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

Any future Packet 5 implementation must remain read-only and intent-only
unless separately approved.

## 9. Preconditions Before Any Packet 5 Implementation

Before any Packet 5 implementation begins:

- Git status must be clean.
- Full closeout must pass.
- V1.34 reference diff must be empty.
- This planning gate must be reviewed and accepted.
- A docs-only Packet 5 plan must be created.
- The Packet 5 plan must be reviewed and accepted.
- The first implementation subset must be tiny.
- The implementation must remain read-only and intent-only.
- Runtime prompt behavior, dispatch, command execution, MIDI, ports, package
  metadata, active behavior, and hardware behavior must remain out of scope.

## 10. Parallelization Position

Do not parallelize immediate Packet 5 implementation yet.

Pad 1 lane planning should happen first because the behavior vocabulary,
result shape, and test expectations need to be explicit before independent
workers can safely split work.

Parallel implementation may become useful later if:

- Packet 5 is split into independent sub-slices.
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

## 12. Safe Next Options

Safe next options:

- Review and accept this next packet planning gate.
- Create a docs-only Packet 5 Pad 1 lane behavior plan.
- Write a user-facing progress/timeline update.
- Pause at this clean planning checkpoint.

## 13. Recommendation

Review and accept this planning gate next.

After review, create a docs-only Packet 5 Pad 1 lane behavior plan.

Do not implement Pad 1 lane behavior, dispatch, MIDI, ports, active behavior,
or hardware behavior from this gate.

## 14. Decision

The recommended next behavior-parity branch is Packet 5 Pad 1 Lane Behavior
planning.

Hardware remains off.

No real MIDI, ports, active behavior, package metadata, runtime execution, or
hardware behavior exists.

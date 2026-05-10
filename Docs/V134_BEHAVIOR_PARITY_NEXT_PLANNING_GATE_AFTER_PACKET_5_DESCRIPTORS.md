# V1.34 Behavior Parity Next Planning Gate After Packet 5 Descriptors

## 1. Purpose

Choose the next safe behavior-parity branch after the accepted Packet 5 Pad 1
lane-state descriptor progress report, review, and user progress timeline.

This document is a planning gate only. It does not implement anything and does
not authorize implementation by itself.

This document adds no tests, CLI wiring, dispatch, command execution, MIDI,
ports, package metadata, active behavior, runtime behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `9def18b Add behavior parity user progress timeline after Packet 5 descriptors`

Current phase:

- Passive/Mock Foundation Phase is complete enough for current planning.
- Behavior parity implementation is in the read-only intent-helper phase.
- Packet 1 is complete.
- Packet 2 has accepted meaningful progress.
- Packet 3 is complete.
- Packet 4 is complete.
- Packet 5 has accepted progress through Pad 1 lane-state descriptors.
- Packet 5 remains incomplete because runtime Pad 1 lane state and runtime
  execution behavior remain deferred.

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
- Packet 5A current BD engine lane intent accepted
- Packet 5B BD FM lane intent accepted
- Packet 5C BD Plastic lane intent accepted
- Packet 5D BD Silky lane intent accepted
- Packet 5E BD Acoustic anchor intent accepted
- static Pad 1 lane-state descriptors accepted

Packet 5 is meaningful progress, but it is not full runtime behavior parity.

## 4. Decision Question

The current question is what to do next:

- continue deeper into Packet 5 runtime-adjacent Pad 1 lane state
- move to the next read-only behavior-parity matrix area
- pause and write more project-level progress documentation
- stop at the current checkpoint

## 5. Decision

Do not pursue runtime Pad 1 lane state next.

Keep runtime Pad 1 lane state deferred.

Choose the next safe branch as:

- docs-only Packet 6 Pad 2 lane behavior planning

Packet 6 should be planning-only first. It should define a tiny future
read-only intent-helper scope for existing Pad 2 lane commands without
implementation.

## 6. Why Packet 6 Pad 2 Lane Behavior Next

Reasons:

- it continues the behavior-parity matrix in a read-only, intent-only style
- it avoids jumping into runtime Pad 1 state too early
- it avoids dispatch, MIDI, ports, active behavior, and hardware
- it builds toward broader V1.34 behavior coverage
- it keeps the project moving toward the fun parts without crossing safety
  boundaries
- it can be split into tiny implementation packets later

## 7. Candidate Packet 6 Scope

Future Packet 6 planning should inspect existing metadata and choose a tiny
read-only scope from existing Pad 2 behavior only.

Likely candidate command family:

- `P2M`
- `P2B`
- `P2H`
- `P2C`
- `P2F`
- `P2T`
- `P2P`
- `P2G`
- `P2R`
- `P2X`
- `P2Z`

The future plan should not implement all of these at once. It should choose a
small first implementation slice.

Likely first slice candidates:

- Pad 2 menu/status intent:
  - `P2M`
- Pad 2 anchor/home intent:
  - `P2B`
- Pad 2 rotation/mutation intent:
  - `P2R`
  - `P2X`

Final Packet 6A scope should be chosen in a separate Packet 6 plan and review.

## 8. What Packet 6 Must Not Do

Packet 6 planning and any later implementation must not add:

- runtime Pad 2 state
- selected Pad 2 profile runtime state
- runtime anchor loading
- mutation execution
- discovery execution
- command execution
- scene execution
- dispatch
- CLI execution wiring
- active CLI command
- MIDI
- `mido`
- `rtmidi`
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- package metadata changes
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## 9. Deferred Scope

Keep deferred:

- full runtime Pad 1 lane state
- runtime Pad 2 lane state
- runtime selected machine/profile state
- runtime anchor loading
- runtime mutation execution
- runtime discovery execution
- selected profile workflow
- Pad 3 lane behavior
- Pad 4 lane behavior
- undo/commit/state behavior
- active execution behavior
- real MIDI behavior
- hardware behavior

## 10. Preconditions Before Packet 6 Planning

Before creating the Packet 6 plan:

- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this planning gate must be accepted or used as the current decision point
- Packet 6 must remain documentation-only until separately reviewed

## 11. Safe Next Options

Safe next options:

- create a docs-only Packet 6 Pad 2 lane behavior plan
- create a docs-only review gate for this planning decision
- pause at this clean checkpoint
- write another user-facing progress update if needed

## 12. Recommendation

Prefer a docs-only Packet 6 Pad 2 lane behavior plan next.

That plan should choose a tiny Packet 6A implementation scope, likely from
existing Pad 2 menu/status or anchor/home intent, but should not implement
anything by itself.

## 13. Decision

Next recommended branch:

- Packet 6 Pad 2 lane behavior planning

Hardware remains off.

No implementation in this slice.

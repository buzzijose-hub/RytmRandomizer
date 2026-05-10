# V1.34 Behavior Parity Packet 6 Pad 2 Lane Behavior Plan

## 1. Purpose

Define the next docs-only behavior-parity implementation plan for Packet 6:
Pad 2 lane behavior.

This plan chooses a tiny future read-only implementation scope, but it does
not implement anything by itself.

This document adds no tests, CLI wiring, dispatch, command execution, MIDI,
ports, package metadata, active behavior, runtime behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `02fc13a Add next behavior parity planning gate review after Packet 5 descriptors`

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
- The next behavior-parity planning gate has accepted Packet 6 Pad 2 lane
  behavior planning as the next branch.

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Preceding Decision

Accepted preceding planning gate review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PLANNING_GATE_AFTER_PACKET_5_DESCRIPTORS_REVIEW.md`

Accepted decision:

- do not pursue runtime Pad 1 lane state next
- keep runtime Pad 1 lane state deferred
- proceed with docs-only Packet 6 Pad 2 lane behavior planning

## 4. Current Pad 2 Command Surface

Existing Pad 2 command metadata is already captured in:

- `rytm_randomizer/commands.py`

Existing Pad 2 command family:

- `P2M`: show Pad 2 snare / secondary percussion menu
- `P2B`: load Pad 2 BD Classic rolling low percussion / home
- `P2H`: load Pad 2 SD Hard pressure snare
- `P2C`: load Pad 2 SD Classic rolling snare
- `P2F`: load Pad 2 SD FM metallic snare
- `P2T`: Pad 2 tone / snap discovery
- `P2P`: Pad 2 pressure / body discovery
- `P2G`: Pad 2 grit / noise discovery
- `P2R`: rotate Pad 2 through profiled secondary-lane engines
- `P2X`: safely mutate the currently loaded Pad 2 profile
- `P2Z`: return current Pad 2 profile to anchor

Already covered elsewhere:

- `P2M` is already covered as menu/status intent in Packet 1.

Still behavior-parity candidates:

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

## 5. Packet 6 Goal

Packet 6 should begin a read-only Pad 2 lane behavior helper surface that can
describe selected Pad 2 intent without executing it.

The helper must remain:

- deterministic
- read-only
- intent-only
- metadata-based
- import-safe
- non-dispatching
- non-executing
- MIDI-free
- port-free
- hardware-free

## 6. Recommended Tiny Packet 6A Scope

Recommended future Packet 6A implementation scope:

- `P2B` only

Reason:

- `P2B` is the Pad 2 BD Classic rolling low percussion / home anchor intent.
- It is a clear Pad 2 home/anchor behavior.
- It uses existing `PAD2_COMMANDS` metadata.
- It avoids discovery depth behavior.
- It avoids rotation order behavior.
- It avoids current-profile runtime state.
- It avoids return-to-current-profile runtime state.
- It is small enough for a targeted TDD implementation.

Packet 6A should not implement:

- `P2H`
- `P2C`
- `P2F`
- `P2T`
- `P2P`
- `P2G`
- `P2R`
- `P2X`
- `P2Z`

## 7. Proposed Future Implementation Shape

Documented as future implementation shape only:

- `rytm_randomizer/behavior_pad2_lane.py`
- `tests/test_behavior_pad2_lane.py`

Likely future helper names:

- `Pad2LaneBehaviorResult`
- `describe_pad2_lane_behavior(key)`

Future implementation should use existing metadata:

- `PAD2_COMMANDS`
- `COMMANDS`

Future `P2B` metadata should include:

- command key: `P2B`
- label: `load Pad 2 BD Classic rolling low percussion / home`
- target pad: `2`
- lane: `Pad 2 secondary lane`
- behavior family: `pad2-lane/bd-classic-home-anchor`
- lane action: `load_pad2_bd_classic_home_anchor`
- intent kind: `anchor_load`
- anchor concept: `Pad 2 BD Classic home anchor`
- runtime state changed: `False`
- dispatches command: `False`
- executes command: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`

## 8. Expected Future Tests

Future Packet 6A tests should prove:

- importing `rytm_randomizer.behavior_pad2_lane` prints nothing
- `P2B` returns deterministic read-only Pad 2 anchor/home intent
- `P2B` uses existing `PAD2_COMMANDS` metadata
- returned metadata is copied/mutation-safe
- unknown keys fail safely
- unsupported Pad 2 keys fail safely
- `P2M` behavior remains owned by menu/utility behavior
- `P2H`, `P2C`, `P2F`, `P2T`, `P2P`, `P2G`, `P2R`, `P2X`, and `P2Z` remain
  unsupported/deferred in Packet 6A
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no command execution occurs
- no runtime state is mutated
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata remains untouched

If `tests/test_behavior_pad2_lane.py` is created later, closeout should add a
dedicated label such as:

- `=== Test: Behavior Pad 2 Lane ===`

## 9. Deferred Packet 6 Scope

Deferred from Packet 6A:

- `P2H` Pad 2 SD Hard anchor/load intent
- `P2C` Pad 2 SD Classic anchor/load intent
- `P2F` Pad 2 SD FM anchor/load intent
- `P2T` Pad 2 tone/snap discovery intent
- `P2P` Pad 2 pressure/body discovery intent
- `P2G` Pad 2 grit/noise discovery intent
- `P2R` Pad 2 profile rotation intent
- `P2X` Pad 2 current-profile mutation intent
- `P2Z` Pad 2 current-profile anchor return intent

These may require separate Packet 6B/6C plans and reviews before
implementation.

## 10. Broader Deferred Scope

Still deferred:

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

## 11. Non-Goals

This plan does not authorize:

- implementation
- tests
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

## 12. Preconditions Before Packet 6A Implementation

Before any Packet 6A implementation:

- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this Packet 6 plan must be reviewed and accepted
- future implementation must be limited to `P2B` only
- future implementation must remain read-only and intent-only
- no runtime execution, dispatch, MIDI, ports, package metadata, active
  behavior, or hardware behavior may be introduced

## 13. Safe Next Options

Safe next options:

- create a docs-only review/acceptance gate for this Packet 6 plan
- pause at this clean planning checkpoint
- write a user-facing progress update if needed

## 14. Recommendation

Create a docs-only review/acceptance gate for this Packet 6 plan next.

If accepted, the next implementation branch can be a tiny TDD Packet 6A slice
for read-only `P2B` intent only.

## 15. Decision

Packet 6 Pad 2 lane behavior planning is documented.

Recommended future Packet 6A implementation scope:

- `P2B` only

Hardware remains off.

No implementation in this slice.

## 16. Plan Review Follow-Up

This Packet 6 plan has now been reviewed and accepted:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_6_PAD2_LANE_BEHAVIOR_PLAN_REVIEW.md`

The review accepts a future tiny Packet 6A implementation scope limited to
read-only `P2B` intent only.

It adds no implementation, tests, dispatch, command execution, MIDI, ports,
package metadata, active behavior, runtime behavior, or hardware behavior.

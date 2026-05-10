# V1.34 Behavior Parity Packet 6B Pad 2 Lane Behavior Plan

## 1. Purpose

Define the next docs-only Packet 6B Pad 2 lane behavior plan after the
accepted Packet 6A `P2B` checkpoint review.

This plan chooses a tiny future read-only implementation scope, but it does
not implement anything by itself.

This document adds no tests, CLI wiring, dispatch, command execution, MIDI,
ports, package metadata, active behavior, runtime behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `e489ed4 Add Packet 6A Pad 2 lane behavior checkpoint review`

Current phase:

- Passive/Mock Foundation Phase is complete enough for current planning.
- Behavior parity implementation is in the read-only intent-helper phase.
- Packet 1 is complete.
- Packet 2 has accepted meaningful progress.
- Packet 3 is complete.
- Packet 4 is complete.
- Packet 5 has accepted progress through Pad 1 lane-state descriptors.
- Packet 6A is complete and accepted for read-only `P2B` Pad 2 lane intent.
- Packet 6B is now being planned.

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Preceding Decision

Accepted preceding checkpoint review:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_6A_PAD2_LANE_BEHAVIOR_CHECKPOINT_REVIEW.md`

Accepted Packet 6A scope:

- `P2B` only

Accepted next recommendation:

- create a docs-only Packet 6B Pad 2 lane behavior plan
- recommended future Packet 6B scope:
  - `P2H` only

## 4. Packet 6B Goal

Packet 6B should extend the read-only Pad 2 lane helper surface by one more
existing Pad 2 anchor/load intent.

Recommended future Packet 6B implementation scope:

- `P2H` only

Reason:

- `P2H` is an existing Pad 2 SD Hard pressure snare anchor/load command.
- It continues the same safe anchor/load shape as `P2B`.
- It uses existing `PAD2_COMMANDS` metadata.
- It avoids discovery depth behavior.
- It avoids profile rotation behavior.
- It avoids current-profile mutation behavior.
- It avoids current-profile anchor return behavior.
- It is small enough for a targeted TDD implementation.

## 5. Current Packet 6 Baseline

Already implemented and accepted:

- `P2B`: read-only Pad 2 BD Classic rolling low percussion / home intent

Already covered elsewhere:

- `P2M`: Packet 1 menu/status intent

Deferred after Packet 6B plan:

- `P2C`
- `P2F`
- `P2T`
- `P2P`
- `P2G`
- `P2R`
- `P2X`
- `P2Z`

## 6. Proposed Future Implementation Shape

Documented as future implementation shape only:

- update `rytm_randomizer/behavior_pad2_lane.py`
- update `tests/test_behavior_pad2_lane.py`

Future `P2H` behavior should reuse the existing helper surface:

- `Pad2LaneBehaviorResult`
- `evaluate_pad2_lane_behavior(key)`

Future `P2H` metadata should include:

- command key: `P2H`
- label: `load Pad 2 SD Hard pressure snare`
- target pad: `2`
- lane: `Pad 2 secondary lane`
- behavior family: `pad2-lane/sd-hard-anchor`
- lane action: `load_pad2_sd_hard_anchor`
- intent kind: `anchor_load`
- anchor concept: `Pad 2 SD Hard anchor`
- runtime state changed: `False`
- dispatches command: `False`
- executes command: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`

## 7. Expected Future Tests

Future Packet 6B tests should prove:

- `P2B` behavior remains unchanged
- `P2H` returns deterministic read-only Pad 2 SD Hard anchor intent
- `P2H` uses existing `PAD2_COMMANDS` metadata
- returned metadata is copied/mutation-safe
- unknown keys still fail safely
- deferred Pad 2 keys still fail safely
- `P2M` behavior remains owned by menu/utility behavior
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no command execution occurs
- no runtime state is mutated
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata remains untouched

No closeout script update should be needed because `tests/test_behavior_pad2_lane.py`
is already covered by:

- `=== Test: Behavior Pad 2 Lane ===`

## 8. Deferred Packet 6 Scope

Deferred from Packet 6B:

- `P2C` Pad 2 SD Classic anchor/load intent
- `P2F` Pad 2 SD FM anchor/load intent
- `P2T` Pad 2 tone/snap discovery intent
- `P2P` Pad 2 pressure/body discovery intent
- `P2G` Pad 2 grit/noise discovery intent
- `P2R` Pad 2 profile rotation intent
- `P2X` Pad 2 current-profile mutation intent
- `P2Z` Pad 2 current-profile anchor return intent

These require separate plans and reviews before implementation.

## 9. Non-Goals

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

## 10. Preconditions Before Packet 6B Implementation

Before any Packet 6B implementation:

- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this Packet 6B plan must be reviewed and accepted
- future implementation must be limited to `P2H` only
- future implementation must preserve existing `P2B` behavior
- future implementation must remain read-only and intent-only
- no runtime execution, dispatch, MIDI, ports, package metadata, active
  behavior, or hardware behavior may be introduced

## 11. Safe Next Options

Safe next options:

- create a docs-only review/acceptance gate for this Packet 6B plan
- pause at this clean planning checkpoint
- write a broader Packet 6A/6B progress update if needed

## 12. Recommendation

Create a docs-only review/acceptance gate for this Packet 6B plan next.

If accepted, the next implementation branch can be a tiny TDD Packet 6B slice
for read-only `P2H` intent only.

## 13. Decision

Packet 6B Pad 2 lane behavior planning is documented.

Recommended future Packet 6B implementation scope:

- `P2H` only

Hardware remains off.

No implementation in this slice.

## 14. Plan Review Follow-Up

This Packet 6B plan has now been reviewed and accepted:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_6B_PAD2_LANE_BEHAVIOR_PLAN_REVIEW.md`

The review accepts a future tiny Packet 6B implementation scope limited to
read-only `P2H` intent only.

It adds no implementation, tests, dispatch, command execution, MIDI, ports,
package metadata, active behavior, runtime behavior, or hardware behavior.

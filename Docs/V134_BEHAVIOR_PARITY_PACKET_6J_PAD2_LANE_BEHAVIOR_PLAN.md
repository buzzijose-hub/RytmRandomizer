# V1.34 Behavior Parity Packet 6J Pad 2 Lane Behavior Plan

## 1. Purpose

Define the next docs-only Packet 6J Pad 2 lane behavior plan after the
accepted Packet 6I progress report review.

This plan chooses a tiny future read-only implementation scope, but it does
not implement anything by itself.

This document adds no tests, CLI wiring, dispatch, command execution, MIDI,
ports, package metadata, active behavior, runtime behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `4fafe1a Add behavior parity progress report review after Packet 6I`

Current phase:

- Passive/Mock Foundation Phase is complete enough for current planning.
- Behavior parity implementation is in the read-only intent-helper phase.
- Packet 1 is complete.
- Packet 2 has accepted meaningful progress.
- Packet 3 is complete.
- Packet 4 is complete.
- Packet 5 has accepted progress through Pad 1 lane-state descriptors.
- Packet 6A is complete and accepted for read-only `P2B` Pad 2 lane intent.
- Packet 6B is complete and accepted for read-only `P2H` Pad 2 lane intent.
- Packet 6C is complete and accepted for read-only `P2C` Pad 2 lane intent.
- Packet 6D is complete and accepted for read-only `P2F` Pad 2 lane intent.
- Packet 6E is complete and accepted for read-only `P2T` Pad 2 lane intent.
- Packet 6F is complete and accepted for read-only `P2P` Pad 2 lane intent.
- Packet 6G is complete and accepted for read-only `P2G` Pad 2 lane intent.
- Packet 6H is complete and accepted for read-only `P2R` Pad 2 lane intent.
- Packet 6I is complete and accepted for read-only `P2X` Pad 2 lane intent.
- Packet 6 progress after Packet 6I is accepted.
- Packet 6J is now being planned.

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Preceding Decision

Accepted preceding progress report review:

- `Docs/V134_BEHAVIOR_PARITY_PROGRESS_REPORT_AFTER_PACKET_6I_REVIEW.md`

Accepted Packet 6 progress:

- `P2B`
- `P2H`
- `P2C`
- `P2F`
- `P2T`
- `P2P`
- `P2G`
- `P2R`
- `P2X`

Accepted next recommendation:

- create a docs-only Packet 6J Pad 2 lane behavior plan
- keep the future scope tiny
- choose only `P2Z` after review

## 4. Packet 6J Goal

Packet 6J should extend the read-only Pad 2 lane helper surface by one small
existing Pad 2 current-profile anchor return intent.

Recommended future Packet 6J implementation scope:

- `P2Z` only

Reason:

- `P2Z` is an existing Pad 2 current-profile anchor return command.
- It follows the accepted read-only intent-helper shape.
- It uses existing `PAD2_COMMANDS` metadata.
- It can record selected-profile anchor dependency without introducing
  runtime state.
- It avoids actual anchor loading.
- It avoids runtime selected-profile mutation.
- It is the last deferred Pad 2 lane command after Packet 6I.
- It is small enough for a targeted TDD implementation.

## 5. Current Packet 6 Baseline

Already implemented and accepted:

- `P2B`: read-only Pad 2 BD Classic rolling low percussion / home intent
- `P2H`: read-only Pad 2 SD Hard pressure snare intent
- `P2C`: read-only Pad 2 SD Classic rolling snare intent
- `P2F`: read-only Pad 2 SD FM metallic snare intent
- `P2T`: read-only Pad 2 tone/snap discovery intent
- `P2P`: read-only Pad 2 pressure/body discovery intent
- `P2G`: read-only Pad 2 grit/noise discovery intent
- `P2R`: read-only Pad 2 profile rotation intent
- `P2X`: read-only Pad 2 current-profile safe mutation intent

Already covered elsewhere:

- `P2M`: Packet 1 menu/status intent

Deferred after Packet 6J plan:

- none within current Packet 6 Pad 2 lane command scope, if `P2Z` is later
  implemented and accepted

## 6. Proposed Future Implementation Shape

Documented as future implementation shape only:

- update `rytm_randomizer/behavior_pad2_lane.py`
- update `tests/test_behavior_pad2_lane.py`

Future `P2Z` behavior should reuse the existing helper surface:

- `Pad2LaneBehaviorResult`
- `evaluate_pad2_lane_behavior(key)`

Future `P2Z` metadata should include:

- command key: `P2Z`
- label: `return current Pad 2 profile to anchor`
- target pad: `2`
- lane: `Pad 2 secondary lane`
- behavior family: `pad2-lane/current-profile-anchor-return`
- lane action: `describe_pad2_current_profile_anchor_return_intent`
- intent kind: `anchor_return_intent`
- anchor return concept: `Pad 2 current-profile anchor return`
- selected profile dependency: `current_pad2_profile_state`
- runtime state changed: `False`
- dispatches command: `False`
- executes command: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`

Future `P2Z` should remain an intent descriptor only. It must not inspect,
choose, mutate, or persist selected Pad 2 profile runtime state. It must not
load an anchor, run a prompt, dispatch a command, execute anchor-return
behavior, open ports, send MIDI, or touch hardware.

## 7. Expected Future Tests

Future Packet 6J tests should prove:

- `P2B` behavior remains unchanged
- `P2H` behavior remains unchanged
- `P2C` behavior remains unchanged
- `P2F` behavior remains unchanged
- `P2T` behavior remains unchanged
- `P2P` behavior remains unchanged
- `P2G` behavior remains unchanged
- `P2R` behavior remains unchanged
- `P2X` behavior remains unchanged
- `P2Z` returns deterministic read-only Pad 2 current-profile anchor return intent
- `P2Z` uses existing `PAD2_COMMANDS` metadata
- `P2Z` records selected-profile dependency as metadata only
- returned metadata is copied/mutation-safe
- unknown keys still fail safely
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

Deferred from Packet 6J planning:

- no remaining current Packet 6 Pad 2 lane command if `P2Z` is later
  implemented and accepted

`P2M` remains covered by Packet 1 menu/status behavior.

Runtime Pad 2 lane state, runtime anchor loading, mutation execution,
discovery execution, prompt behavior, active execution, real MIDI, and
hardware behavior remain out of scope.

## 9. Non-Goals

This plan does not authorize:

- implementation
- tests
- runtime Pad 2 state
- selected Pad 2 profile runtime state
- runtime anchor loading
- profile rotation execution
- mutation execution
- discovery execution
- anchor-return execution
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

## 10. Preconditions Before Packet 6J Implementation

Before any Packet 6J implementation:

- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this Packet 6J plan must be reviewed and accepted
- future implementation must be limited to `P2Z` only
- future implementation must preserve existing `P2B` behavior
- future implementation must preserve existing `P2H` behavior
- future implementation must preserve existing `P2C` behavior
- future implementation must preserve existing `P2F` behavior
- future implementation must preserve existing `P2T` behavior
- future implementation must preserve existing `P2P` behavior
- future implementation must preserve existing `P2G` behavior
- future implementation must preserve existing `P2R` behavior
- future implementation must preserve existing `P2X` behavior
- future implementation must remain read-only and intent-only
- no runtime execution, dispatch, MIDI, ports, package metadata, active
  behavior, or hardware behavior may be introduced

## 11. Safe Next Options

Safe next options:

- create a docs-only review/acceptance gate for this Packet 6J plan
- pause at this clean planning checkpoint
- write a user-facing progress/timeline update if needed

## 12. Recommendation

Create a docs-only review/acceptance gate for this Packet 6J plan next.

If accepted, the next implementation branch can be a tiny TDD Packet 6J slice
for read-only `P2Z` intent only.

## 13. Decision

Packet 6J Pad 2 lane behavior planning is documented.

Recommended future Packet 6J implementation scope:

- `P2Z` only

Hardware remains off.

No implementation in this slice.

## 14. Plan Review Follow-Up

This Packet 6J plan has now been reviewed and accepted:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_6J_PAD2_LANE_BEHAVIOR_PLAN_REVIEW.md`

The review accepts a future tiny Packet 6J implementation scope limited to:

- `P2Z` only

It adds no implementation, tests, dispatch, command execution, MIDI, ports,
package metadata, active behavior, runtime behavior, or hardware behavior.

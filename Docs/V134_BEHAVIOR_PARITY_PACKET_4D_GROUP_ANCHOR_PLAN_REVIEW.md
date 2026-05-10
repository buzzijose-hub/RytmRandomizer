# V1.34 Behavior Parity Packet 4D Group Anchor Plan Review

## Purpose

Review and accept the Packet 4D group anchor plan as the current planning gate
for the remaining Packet 4 `O` and `Z` scope.

This is a documentation-only review. It adds no implementation, tests, CLI
wiring, dispatch, MIDI, port opening, package metadata, active behavior, or
hardware behavior.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `0eb382e Add Packet 4D group anchor plan`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete
- Packet 2 accepted progress
- Packet 3 complete
- Packet 4A scene intent accepted
- Packet 4B group mutation intent accepted
- Packet 4C lane-aware group mutation intent accepted
- Packet 4D group anchor decision note accepted `O` and `Z` as deferred/safe
- Packet 4D group anchor plan now reviewed and accepted

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Review Decision

Accepted plan document:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_4D_GROUP_ANCHOR_PLAN.md`

Accepted planning milestone:

- `0eb382e Add Packet 4D group anchor plan`

Decision:

- Packet 4D group anchor plan accepted.
- Future implementation scope is limited to read-only intent behavior for
  `O` and `Z`.
- The plan does not authorize runtime execution, MIDI, ports, active CLI
  behavior, or hardware validation.

## Accepted Future Scope

The accepted future Packet 4D implementation scope is limited to:

- `O`: load full 4-pad group anchors
- `Z`: return all 4 group pads to anchors

The future implementation must remain:

- read-only
- metadata-only
- intent-only
- deterministic
- side-effect free

## Accepted Future Behavior

Accepted future `O` semantics:

- accepted as read-only group anchor load intent
- copies existing passive metadata from `GROUP_COMMANDS`
- uses group scope `four_pad_group`
- reports anchor action `load_group_anchors`
- reports behavior family `scene-group/group-anchor-intent`
- reports reason `supported_group_anchor_load_intent`
- executes nothing

Accepted future `Z` semantics:

- accepted as read-only group anchor return intent
- copies existing passive metadata from `GROUP_COMMANDS`
- uses group scope `four_pad_group`
- reports anchor action `return_group_anchors`
- reports behavior family `scene-group/group-anchor-intent`
- reports reason `supported_group_anchor_return_intent`
- executes nothing

## Accepted Future Implementation Surface

Future implementation files:

- `rytm_randomizer/behavior_scene_group.py`
- `tests/test_behavior_scene_group.py`

Expected future constant:

- `PACKET_4D_GROUP_ANCHOR_INTENT_KEYS`

No closeout script update should be needed because `tests/test_behavior_scene_group.py`
is already covered by:

- `=== Test: Behavior Scene Group ===`

## Accepted Future Test Requirements

Future tests must prove:

- importing `rytm_randomizer.behavior_scene_group` prints nothing
- Packet 4A scene intent behavior remains unchanged
- Packet 4B group mutation intent behavior remains unchanged
- Packet 4C lane-aware group mutation intent behavior remains unchanged
- `O` is accepted as read-only group anchor load intent
- `Z` is accepted as read-only group anchor return intent
- `O` and `Z` copy metadata from `GROUP_COMMANDS`
- `O` and `Z` use group scope `four_pad_group`
- `O` has deterministic anchor action `load_group_anchors`
- `Z` has deterministic anchor action `return_group_anchors`
- `O` has reason `supported_group_anchor_load_intent`
- `Z` has reason `supported_group_anchor_return_intent`
- repeated evaluations are deterministic
- unknown keys still fail safely
- no anchor load execution exists
- no anchor return execution exists
- no group mutation execution exists
- no lane-aware group mutation execution exists
- no scene execution exists
- no dispatch exists
- no runtime state mutation exists
- no real MIDI libraries are imported
- package metadata remains absent
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- no Analog Four support is exposed
- no Pads 5-12 support is exposed

## Accepted Future TDD Expectations

Future implementation should use red/green TDD.

Expected red command:

```powershell
python .\tests\test_behavior_scene_group.py
```

Expected red result:

- new `O` and `Z` tests fail before implementation because the commands remain
  deferred/unsupported.

Expected green command:

```powershell
python .\tests\test_behavior_scene_group.py
```

Expected green result:

- new `O` and `Z` tests pass after the tiny read-only implementation.

Expected targeted regression commands:

```powershell
python .\tests\test_behavior_menu_utility.py
python .\tests\test_behavior_anchor_profile.py
python .\tests\test_behavior_mutation_depth.py
python .\tests\test_cli.py
python .\tests\test_behavior_scene_group.py
```

Expected full closeout:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

## Confirmed Non-Goals

This review confirms the plan still does not authorize:

- anchor load execution
- anchor return execution
- group mutation execution
- lane-aware group mutation execution
- scene execution
- command dispatch
- CLI execution wiring
- prompt/input loop
- runtime scene state
- runtime group state
- runtime lane state
- runtime anchor state
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
- machine/profile expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## Safety Boundaries

`rytm_hybrid_randomizer_v134.py` must remain untouched.

Passive CLI behavior must remain unchanged.

Future Packet 4D implementation must only evaluate read-only intent metadata
for `O` and `Z`.

Hardware remains off.

## Packet 4 Status After This Review

Accepted Packet 4 progress:

- Packet 4A scene intent
- Packet 4B group mutation intent
- Packet 4C lane-aware group mutation intent

Accepted future Packet 4D scope:

- `O` group anchor load intent
- `Z` group anchor return intent

Packet 4 remains not complete until the future Packet 4D implementation is
completed or `O` and `Z` are explicitly left deferred in a Packet 4 closeout
decision.

## Next Recommended Task

Next recommended task is the tiny Packet 4D implementation for read-only group
anchor load/return intent behavior for `O` and `Z`, a broader Packet 4
near-completion checkpoint, a more user-facing progress/timeline update, or a
pause at this accepted Packet 4D planning checkpoint.

Do not implement runtime group anchor loading or return behavior.

## Decision

Packet 4D group anchor plan accepted.

Future `O` and `Z` implementation scope is limited to read-only intent-only
behavior.

No implementation is added by this review.

Hardware remains off.

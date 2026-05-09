# V1.34 Behavior Parity Packet 4D Group Anchor Plan

## Purpose

Define the future Packet 4D implementation scope for read-only group anchor
load/return intent behavior.

This is a documentation-only plan. It does not implement `O` or `Z`, does not
add tests, does not wire CLI execution, does not dispatch commands, does not
open MIDI ports, does not send MIDI, and does not add hardware behavior.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `d621c67 Add Packet 4D group anchor decision note`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete
- Packet 2 accepted progress
- Packet 3 complete
- Packet 4A scene intent accepted
- Packet 4B group mutation intent accepted
- Packet 4C lane-aware group mutation intent accepted
- Packet 4D group anchor decision note accepted `O` and `Z` as deferred/safe
- Packet 4D group anchor plan now defines the next tiny future scope

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Planned Future Scope

The planned future Packet 4D implementation should support only these read-only
group anchor intent commands:

- `O`: load full 4-pad group anchors
- `Z`: return all 4 group pads to anchors

The future implementation must remain metadata-only and intent-only.

It must not perform anchor loading, anchor return, mutation, dispatch, MIDI, or
hardware behavior.

## Proposed Future Behavior

Future `O` behavior:

- accepted as read-only group anchor load intent
- copies existing passive metadata from `GROUP_COMMANDS`
- uses group scope `four_pad_group`
- reports anchor action `load_group_anchors`
- reports behavior family `scene-group/group-anchor-intent`
- reports reason `supported_group_anchor_load_intent`
- executes nothing

Future `Z` behavior:

- accepted as read-only group anchor return intent
- copies existing passive metadata from `GROUP_COMMANDS`
- uses group scope `four_pad_group`
- reports anchor action `return_group_anchors`
- reports behavior family `scene-group/group-anchor-intent`
- reports reason `supported_group_anchor_return_intent`
- executes nothing

## Proposed Metadata Vocabulary

Future result metadata should be deterministic and inspectable.

Proposed fields:

- `group_scope`: `four_pad_group`
- `anchor_action`: `load_group_anchors` for `O`
- `anchor_action`: `return_group_anchors` for `Z`
- `behavior_family`: `scene-group/group-anchor-intent`
- `reason`: `supported_group_anchor_load_intent` for `O`
- `reason`: `supported_group_anchor_return_intent` for `Z`
- copied command metadata from `GROUP_COMMANDS`

If the implementation needs a constant, use a narrow name such as:

- `PACKET_4D_GROUP_ANCHOR_INTENT_KEYS`

## Files For Future Implementation

Future implementation files:

- `rytm_randomizer/behavior_scene_group.py`
- `tests/test_behavior_scene_group.py`

Do not update:

- `rytm_randomizer/cli.py`
- `rytm_randomizer/registry_report.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `Scripts/closeout_check.ps1`
- package metadata
- runtime execution or dispatch logic
- `rytm_hybrid_randomizer_v134.py`

No closeout script update should be needed because `tests/test_behavior_scene_group.py`
is already covered by:

- `=== Test: Behavior Scene Group ===`

## Required Future Tests

Future tests should prove:

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

## Future TDD Expectations

Future implementation should use the same red/green style as prior behavior
packets.

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

Do not add:

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

The future Packet 4D implementation must be read-only and deterministic. It
must only evaluate intent metadata for `O` and `Z`.

Hardware remains off.

## Packet 4 Status After This Plan

Accepted Packet 4 progress:

- Packet 4A scene intent
- Packet 4B group mutation intent
- Packet 4C lane-aware group mutation intent

Planned Packet 4D scope:

- `O` group anchor load intent
- `Z` group anchor return intent

Packet 4 remains not complete until this plan is reviewed and the future
Packet 4D implementation is either completed or explicitly left deferred in a
Packet 4 closeout decision.

## Next Recommended Task

Create a docs-only review/acceptance gate for this Packet 4D group anchor
plan.

Do not implement `O` or `Z` until the plan is reviewed and accepted.

## Decision

Packet 4D group anchor load/return behavior is planned as a future tiny
read-only intent-only implementation.

No implementation is added by this document.

Hardware remains off.

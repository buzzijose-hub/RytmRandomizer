# V1.34 Behavior Parity Matrix: Scene And Group Intent Slice

## 1. Purpose

Create the next documentation-only behavior parity matrix slice using the
accepted matrix schema.

This slice covers scene command intent plus four-pad group mutation and
lane-aware group mutation intent.

This document does not implement runtime behavior, tests, command dispatch,
scene execution, MIDI, port opening, package metadata changes, active CLI
commands, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 9b34d22 Add V1.34 behavior parity mutation depth matrix review

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity roadmap accepted
- V1.34 behavior parity matrix plan accepted
- menu/status and utility matrix slice accepted
- anchor/profile matrix slice accepted
- mutation-depth and guarded input matrix slice accepted
- scene and group intent matrix slice now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Slice Scope

Included in this slice:

- scene command rows from `SCENE_COMMANDS`
- four-pad group mutation rows from `GROUP_COMMANDS`
- lane-aware group mutation rows from `GROUP_COMMANDS`

Specifically included command keys:

- `S0`
- `S1`
- `S1A`
- `S1B`
- `S2`
- `S2A`
- `S2B`
- `S3`
- `S3A`
- `S3B`
- `S4`
- `S4A`
- `S4B`
- `S5`
- `X`
- `D`
- `I`
- `4`
- `Y`
- `V`
- `N`

Not included in this slice:

- menu/status rows already covered by the menu/utility slice
- anchor load/return rows already covered by the anchor/profile slice
- profile selection and profile rotation rows already covered by the
  anchor/profile slice
- mutation-depth and guarded numeric input rows already covered by the
  mutation-depth slice
- Pad 1, Pad 2, Pad 3, and Pad 4 lane-specific discovery/current-mode rows
- selected isolated pad mutation rows already covered by the mutation-depth
  slice
- undo/commit/state rows
- waveform exploration rows
- real MIDI behavior
- active CLI behavior
- hardware validation

## 4. Matrix Schema

The accepted matrix columns are:

- command key
- V1.34 label or operator-facing description
- passive metadata source
- passive metadata status
- behavior domain
- command family
- menu or page context
- target pad scope
- target channel scope
- state dependencies
- anchor/profile dependencies
- mutation-depth dependencies
- scene/group intent
- hardware/MIDI implication
- safe failure or no-op expectation
- current modular behavior status
- parity gap summary
- required future artifact
- required future test category
- implementation authorization status
- notes

## 5. Status Values Used

This slice uses only accepted status vocabulary from the matrix plan review.

Passive metadata status:

- captured

Current modular behavior status:

- passive-only

Implementation authorization status:

- documentation-only

Hardware/MIDI implication:

- forbidden-early-scope

The `forbidden-early-scope` value is planning vocabulary only. Scene and
four-pad group mutation behavior may eventually require hardware-facing
execution, but scenes and group/global mutations are explicitly not suitable
for the earliest active/hardware validation phase.

## 6. Matrix Rows

| command key | V1.34 label or operator-facing description | passive metadata source | passive metadata status | behavior domain | command family | menu or page context | target pad scope | target channel scope | state dependencies | anchor/profile dependencies | mutation-depth dependencies | scene/group intent | hardware/MIDI implication | safe failure or no-op expectation | current modular behavior status | parity gap summary | required future artifact | required future test category | implementation authorization status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `S0` | Home / Clean | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | none | action: home; return all four pads to validated anchors | forbidden-early-scope | missing scene or missing group anchor state must fail safely later | passive-only | V1.34 Home / Clean scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | No scene execution exists now. |
| `S1` | Rolling | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined balanced movement only | action: balanced; four-lane rolling movement | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Rolling scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S1A` | Rolling Light | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined light movement only | action: rolling_light; subtle rolling variation | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Rolling Light scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S1B` | Rolling Push | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined push movement only | action: rolling_push; stronger rolling variation | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Rolling Push scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S2` | Deeper | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined deeper movement only | action: deeper; Pads 2-4 pressure with Pad 1 bounded | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Deeper scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S2A` | Deeper Groove | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined deeper groove movement only | action: deeper_groove; groove-first deeper movement | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Deeper Groove scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S2B` | Deeper Pressure | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined pressure movement only | action: deeper_pressure; secondary-lane filter/grit pressure | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Deeper Pressure scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S3` | Intense | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined intense movement only | action: intense; controlled chaos with Pad 3 motion | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Intense scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S3A` | Intense Motion | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined motion intensity only | action: intense_motion; motion-heavy Pad 3 lane | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Intense Motion scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S3B` | Intense Grit | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined grit intensity only | action: intense_grit; grit-forward intensity | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Intense Grit scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Captures intent only. |
| `S4` | Wild | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined wild movement only | action: harder; aggressive discovery scene with Pad 1 bounded | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Wild scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Wild scene remains planning-only. |
| `S4A` | Wild Controlled | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined controlled wild movement only | action: wild_controlled; wide discovery with guardrails | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Wild Controlled scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Wild scene remains planning-only. |
| `S4B` | Wild Maximum | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | scene-defined maximum wild movement only | action: wild_maximum; maximum discovery scene with guardrails | forbidden-early-scope | missing scene or invalid group state must fail safely later | passive-only | V1.34 Wild Maximum scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | Maximum scene is not an early active candidate. |
| `S5` | Back to Clean | `rytm_randomizer/scenes.py:SCENE_COMMANDS` | captured | scene command behavior | scene preset | scene / preset tools | four_pad_group | future group MIDI channels | future scene selection state | four-pad anchor/profile state | none | action: clean; return four-pad group after scene movement | forbidden-early-scope | missing scene or missing anchor state must fail safely later | passive-only | V1.34 Back to Clean scene behavior not implemented | scene/group intent model | future scene-intent parity tests | documentation-only | No scene execution exists now. |
| `X` | balanced four-lane mutate full 4-pad group | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | four-pad group mutation | group mutation | global 4-pad mutation tools | four_pad_group | future group MIDI channels | future four-pad group state | group anchor/profile state | V1.34 balanced group mutation depth | balanced mutation across four lanes | forbidden-early-scope | missing group state must fail safely later | passive-only | V1.34 balanced four-lane mutation behavior not implemented | scene/group intent model | future group-mutation parity tests | documentation-only | Group mutation is not an early active candidate. |
| `D` | deeper four-lane mutation, Pads 2-4 pushed harder | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | four-pad group mutation | group mutation | global 4-pad mutation tools | four_pad_group | future group MIDI channels | future four-pad group state | group anchor/profile state | V1.34 deeper group mutation depth | deeper group mutation with Pads 2-4 pushed harder | forbidden-early-scope | missing group state must fail safely later | passive-only | V1.34 deeper four-lane mutation behavior not implemented | scene/group intent model | future group-mutation parity tests | documentation-only | Group mutation is not an early active candidate. |
| `I` | intense / controlled chaos four-lane mutation | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | four-pad group mutation | group mutation | global 4-pad mutation tools | four_pad_group | future group MIDI channels | future four-pad group state | group anchor/profile state | V1.34 intense group mutation depth | intense controlled-chaos group mutation | forbidden-early-scope | missing group state must fail safely later | passive-only | V1.34 intense four-lane mutation behavior not implemented | scene/group intent model | future group-mutation parity tests | documentation-only | Group mutation is not an early active candidate. |
| `4` | harder / wild four-lane mutation | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | four-pad group mutation | group mutation | global 4-pad mutation tools | four_pad_group | future group MIDI channels | future four-pad group state | group anchor/profile state | V1.34 harder/wild group mutation depth | harder/wild group mutation | forbidden-early-scope | missing group state must fail safely later | passive-only | V1.34 harder/wild four-lane mutation behavior not implemented | scene/group intent model | future group-mutation parity tests | documentation-only | This is command key `4`, not group profile `"4"`. |
| `Y` | lane-aware SRC/morph mutation on all 4 group pads | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | lane-aware group mutation | lane-aware page | global 4-pad mutation tools | four_pad_group | future group MIDI channels | future four-pad group state and lane model | group anchor/profile state | V1.34 lane-aware SRC/morph intent | SRC/morph mutation across all four group pads | forbidden-early-scope | missing lane model or group state must fail safely later | passive-only | V1.34 lane-aware SRC/morph group mutation behavior not implemented | scene/group intent model and lane behavior model | future lane-aware group parity tests | documentation-only | Lane-aware group behavior is planning-only. |
| `V` | lane-aware filter mutation on all 4 group pads | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | lane-aware group mutation | lane-aware page | global 4-pad mutation tools | four_pad_group | future group MIDI channels | future four-pad group state and lane model | group anchor/profile state | V1.34 lane-aware filter intent | filter mutation across all four group pads | forbidden-early-scope | missing lane model or group state must fail safely later | passive-only | V1.34 lane-aware filter group mutation behavior not implemented | scene/group intent model and lane behavior model | future lane-aware group parity tests | documentation-only | Lane-aware group behavior is planning-only. |
| `N` | lane-aware grit mutation on all 4 group pads | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | lane-aware group mutation | lane-aware page | global 4-pad mutation tools | four_pad_group | future group MIDI channels | future four-pad group state and lane model | group anchor/profile state | V1.34 lane-aware grit intent | grit mutation across all four group pads | forbidden-early-scope | missing lane model or group state must fail safely later | passive-only | V1.34 lane-aware grit group mutation behavior not implemented | scene/group intent model and lane behavior model | future lane-aware group parity tests | documentation-only | Lane-aware group behavior is planning-only. |

## 7. Current Matrix Slice Decision

This slice adds the next docs-only behavior parity rows after the accepted
mutation-depth and guarded input slice.

The rows intentionally record scene and group behavior gaps instead of closing
them.

Current modular behavior remains passive-only for every row in this slice.

Scene execution and group mutation execution remain unimplemented.

## 8. Next Recommended Matrix Slice

After review and acceptance of this slice, the next recommended task is one
of:

- docs-only review/acceptance gate for this scene and group intent matrix
  slice
- docs-only Pad 1 lane behavior matrix slice
- pause at this clean checkpoint

Recommendation:

- review and accept this scene and group intent matrix slice before adding
  more rows

## 9. Work Not Authorized By This Slice

This slice does not authorize:

- implementation
- tests
- runtime code changes
- command dispatch
- command execution
- scene execution
- prompt/input loop execution
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata changes
- MIDI port discovery
- MIDI port opening
- MIDI sending
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware mutation
- hardware validation
- profile `"3"` active-boundary support
- profile `"4"` implementation
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- SysEx
- GUI/capture

## 10. Decision

The docs-only V1.34 behavior parity matrix slice is documented for scene and
group intent commands.

Hardware remains off.

No implementation is added in this slice.

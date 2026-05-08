# V1.34 Behavior Parity Matrix: Pad 2 Lane Behavior Slice

## 1. Purpose

Create the next documentation-only behavior parity matrix slice using the
accepted matrix schema.

This slice covers Pad 2 secondary-lane discovery and current-profile mutation
intent.

This document does not implement runtime behavior, tests, command dispatch,
scene execution, MIDI, port opening, package metadata changes, active CLI
commands, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 7628b66 Add V1.34 behavior parity Pad 1 lane matrix review

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity roadmap accepted
- V1.34 behavior parity matrix plan accepted
- menu/status and utility matrix slice accepted
- anchor/profile matrix slice accepted
- mutation-depth and guarded input matrix slice accepted
- scene and group intent matrix slice accepted
- Pad 1 lane behavior matrix slice accepted
- Pad 2 lane behavior matrix slice now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Slice Scope

Included in this slice:

- Pad 2 tone/snap discovery row from `PAD2_COMMANDS`
- Pad 2 pressure/body discovery row from `PAD2_COMMANDS`
- Pad 2 grit/noise discovery row from `PAD2_COMMANDS`
- Pad 2 currently loaded profile mutation row from `PAD2_COMMANDS`

Specifically included command keys:

- `P2T`
- `P2P`
- `P2G`
- `P2X`

Not included in this slice:

- Pad 2 menu/status row already covered by the menu/utility slice
- Pad 2 profile load, rotation, and anchor return rows already covered by the
  anchor/profile slice
- guarded depth input rows already covered by the mutation-depth slice
- selected isolated pad mutation rows already covered by the mutation-depth
  slice
- scene and group intent rows already covered by the scene/group slice
- Pad 1 lane behavior rows already covered by the Pad 1 lane slice
- Pad 3 and Pad 4 lane-specific rows
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

- future-real-midi-risk
- forbidden-early-scope

The `future-real-midi-risk` value is planning vocabulary only. Pad 2 mutation
behavior may eventually influence hardware-facing parameter changes, but this
document does not add MIDI behavior now.

The `forbidden-early-scope` value is also planning vocabulary only. Pad 2
discovery commands are intentionally not treated as earliest active/hardware
validation candidates.

## 6. Matrix Rows

| command key | V1.34 label or operator-facing description | passive metadata source | passive metadata status | behavior domain | command family | menu or page context | target pad scope | target channel scope | state dependencies | anchor/profile dependencies | mutation-depth dependencies | scene/group intent | hardware/MIDI implication | safe failure or no-op expectation | current modular behavior status | parity gap summary | required future artifact | required future test category | implementation authorization status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P2T` | Pad 2 tone / snap discovery | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | Pad 2 secondary-lane discovery | Pad 2 lane | Pad 2 snare / secondary percussion menu | Pad 2 | future selected Pad 2 MIDI channel | current Pad 2 profile state | Pad 2 anchor/profile state | V1.34 Pad 2 tone/snap discovery depth | none | forbidden-early-scope | missing current Pad 2 profile must fail safely later | passive-only | V1.34 Pad 2 tone/snap discovery behavior not implemented | Pad 2 lane behavior model and secondary-lane behavior notes | future Pad 2 lane parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `P2P` | Pad 2 pressure / body discovery | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | Pad 2 secondary-lane discovery | Pad 2 lane | Pad 2 snare / secondary percussion menu | Pad 2 | future selected Pad 2 MIDI channel | current Pad 2 profile state | Pad 2 anchor/profile state | V1.34 Pad 2 pressure/body discovery depth | none | forbidden-early-scope | missing current Pad 2 profile must fail safely later | passive-only | V1.34 Pad 2 pressure/body discovery behavior not implemented | Pad 2 lane behavior model and secondary-lane behavior notes | future Pad 2 lane parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `P2G` | Pad 2 grit / noise discovery | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | Pad 2 secondary-lane discovery | Pad 2 lane | Pad 2 snare / secondary percussion menu | Pad 2 | future selected Pad 2 MIDI channel | current Pad 2 profile state | Pad 2 anchor/profile state | V1.34 Pad 2 grit/noise discovery depth | none | forbidden-early-scope | missing current Pad 2 profile must fail safely later | passive-only | V1.34 Pad 2 grit/noise discovery behavior not implemented | Pad 2 lane behavior model and secondary-lane behavior notes | future Pad 2 lane parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `P2X` | safely mutate the currently loaded Pad 2 profile | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | Pad 2 current-profile mutation | Pad 2 lane | Pad 2 snare / secondary percussion menu | Pad 2 | future selected Pad 2 MIDI channel | current Pad 2 profile state | Pad 2 anchor/profile state | V1.34 safe current-profile mutation depth | none | future-real-midi-risk | missing current Pad 2 profile or anchor state must fail safely later | passive-only | V1.34 Pad 2 current-profile safe mutation behavior not implemented | Pad 2 lane behavior model | future Pad 2 lane parity tests | documentation-only | Captures mutation intent only. |

## 7. Current Matrix Slice Decision

This slice adds the next docs-only behavior parity rows after the accepted Pad
1 lane behavior slice.

The rows intentionally record Pad 2 lane behavior gaps instead of closing
them.

Current modular behavior remains passive-only for every row in this slice.

Pad 2 mutation and discovery execution remain unimplemented.

## 8. Next Recommended Matrix Slice

After review and acceptance of this slice, the next recommended task is one
of:

- docs-only review/acceptance gate for this Pad 2 lane behavior matrix slice
- docs-only Pad 3 lane behavior matrix slice
- pause at this clean checkpoint

Recommendation:

- review and accept this Pad 2 lane behavior matrix slice before adding more
  rows

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

The docs-only V1.34 behavior parity matrix slice is documented for Pad 2 lane
behavior commands.

Hardware remains off.

No implementation is added in this slice.

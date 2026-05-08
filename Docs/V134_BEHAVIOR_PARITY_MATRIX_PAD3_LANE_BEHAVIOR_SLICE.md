# V1.34 Behavior Parity Matrix: Pad 3 Lane Behavior Slice

## 1. Purpose

Create the next documentation-only behavior parity matrix slice using the
accepted matrix schema.

This slice covers Pad 3 SY Raw discovery and currently loaded mode mutation
intent.

This document does not implement runtime behavior, tests, command dispatch,
scene execution, MIDI, port opening, package metadata changes, active CLI
commands, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 9510d01 Add V1.34 behavior parity Pad 2 lane matrix review

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity roadmap accepted
- V1.34 behavior parity matrix plan accepted
- menu/status and utility matrix slice accepted
- anchor/profile matrix slice accepted
- mutation-depth and guarded input matrix slice accepted
- scene and group intent matrix slice accepted
- Pad 1 lane behavior matrix slice accepted
- Pad 2 lane behavior matrix slice accepted
- Pad 3 lane behavior matrix slice now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Slice Scope

Included in this slice:

- Pad 3 SY Raw Wave + Balance discovery row from `PAD3_COMMANDS`
- Pad 3 currently loaded mode mutation row from `PAD3_COMMANDS`

Specifically included command keys:

- `SW`
- `P3X`

Not included in this slice:

- Pad 3 menu/status rows already covered by the menu/utility slice
- Pad 3 mode load, rotation, and anchor return rows already covered by the
  anchor/profile slice
- guarded depth input rows already covered by the mutation-depth slice
- selected isolated pad mutation rows already covered by the mutation-depth
  slice
- scene and group intent rows already covered by the scene/group slice
- Pad 1 and Pad 2 lane behavior rows already covered by prior lane slices
- Pad 4 lane-specific rows
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

The `future-real-midi-risk` value is planning vocabulary only. Pad 3 mutation
behavior may eventually influence hardware-facing parameter changes, but this
document does not add MIDI behavior now.

The `forbidden-early-scope` value is also planning vocabulary only. Pad 3
discovery commands are intentionally not treated as earliest active/hardware
validation candidates.

## 6. Matrix Rows

| command key | V1.34 label or operator-facing description | passive metadata source | passive metadata status | behavior domain | command family | menu or page context | target pad scope | target channel scope | state dependencies | anchor/profile dependencies | mutation-depth dependencies | scene/group intent | hardware/MIDI implication | safe failure or no-op expectation | current modular behavior status | parity gap summary | required future artifact | required future test category | implementation authorization status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SW` | Pad 3 SY Raw Wave + Balance discovery | `rytm_randomizer/commands.py:PAD3_COMMANDS` | captured | Pad 3 SY Raw discovery | Pad 3 lane | Pad 3 SY Raw bass / synth-percussion menu | Pad 3 | future selected Pad 3 MIDI channel | current Pad 3 SY Raw mode state | Pad 3 SY Raw anchor/mode state | V1.34 Pad 3 wave/balance discovery depth | none | forbidden-early-scope | missing current Pad 3 mode must fail safely later | passive-only | V1.34 Pad 3 SY Raw Wave + Balance discovery behavior not implemented | Pad 3 lane behavior model and SY Raw behavior notes | future Pad 3 lane parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `P3X` | safely mutate the currently loaded Pad 3 mode | `rytm_randomizer/commands.py:PAD3_COMMANDS` | captured | Pad 3 current-mode mutation | Pad 3 lane | Pad 3 SY Raw bass / synth-percussion menu | Pad 3 | future selected Pad 3 MIDI channel | current Pad 3 mode state | Pad 3 anchor/mode state | V1.34 safe current-mode mutation depth | none | future-real-midi-risk | missing current Pad 3 mode or anchor state must fail safely later | passive-only | V1.34 Pad 3 current-mode safe mutation behavior not implemented | Pad 3 lane behavior model | future Pad 3 lane parity tests | documentation-only | Captures mutation intent only. |

## 7. Current Matrix Slice Decision

This slice adds the next docs-only behavior parity rows after the accepted Pad
2 lane behavior slice.

The rows intentionally record Pad 3 lane behavior gaps instead of closing
them.

Current modular behavior remains passive-only for every row in this slice.

Pad 3 mutation and discovery execution remain unimplemented.

## 8. Next Recommended Matrix Slice

After review and acceptance of this slice, the next recommended task is one
of:

- docs-only review/acceptance gate for this Pad 3 lane behavior matrix slice
- docs-only Pad 4 lane behavior matrix slice
- pause at this clean checkpoint

Recommendation:

- review and accept this Pad 3 lane behavior matrix slice before adding more
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

The docs-only V1.34 behavior parity matrix slice is documented for Pad 3 lane
behavior commands.

Hardware remains off.

No implementation is added in this slice.

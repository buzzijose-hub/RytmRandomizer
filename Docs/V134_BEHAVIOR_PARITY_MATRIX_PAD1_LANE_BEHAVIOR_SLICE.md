# V1.34 Behavior Parity Matrix: Pad 1 Lane Behavior Slice

## 1. Purpose

Create the next documentation-only behavior parity matrix slice using the
accepted matrix schema.

This slice covers Pad 1 BD current-engine mutation and Pad 1 BD FM, BD
Plastic, and BD Silky discovery/mutation intent.

This document does not implement runtime behavior, tests, command dispatch,
scene execution, MIDI, port opening, package metadata changes, active CLI
commands, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- c1a6c89 Add V1.34 behavior parity scene group matrix review

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity roadmap accepted
- V1.34 behavior parity matrix plan accepted
- menu/status and utility matrix slice accepted
- anchor/profile matrix slice accepted
- mutation-depth and guarded input matrix slice accepted
- scene and group intent matrix slice accepted
- Pad 1 lane behavior matrix slice now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Slice Scope

Included in this slice:

- Pad 1 current BD engine mutation row from `PAD1_COMMANDS`
- Pad 1 BD FM discovery/mutation rows from `PAD1_COMMANDS`
- Pad 1 BD Plastic discovery/mutation rows from `PAD1_COMMANDS`
- Pad 1 BD Silky discovery/mutation rows from `PAD1_COMMANDS`

Specifically included command keys:

- `BM`
- `FT`
- `FK`
- `FG`
- `PT`
- `PK`
- `PX`
- `ST`
- `SK`
- `SC`

Not included in this slice:

- Pad 1 menu/status rows already covered by the menu/utility slice
- Pad 1 profile rotation and anchor load/return rows already covered by the
  anchor/profile slice
- guarded depth input rows already covered by the mutation-depth slice
- current-profile generic mutation rows already covered by the mutation-depth
  slice
- scene and group intent rows already covered by the scene/group slice
- Pad 2, Pad 3, and Pad 4 lane-specific rows
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

- future-real-midi-risk
- forbidden-early-scope

The `future-real-midi-risk` value is planning vocabulary only. Pad 1 mutation
behavior may eventually influence hardware-facing parameter changes, but this
document does not add MIDI behavior now.

The `forbidden-early-scope` value is also planning vocabulary only. Pad 1
discovery commands are intentionally not treated as earliest active/hardware
validation candidates.

## 6. Matrix Rows

| command key | V1.34 label or operator-facing description | passive metadata source | passive metadata status | behavior domain | command family | menu or page context | target pad scope | target channel scope | state dependencies | anchor/profile dependencies | mutation-depth dependencies | scene/group intent | hardware/MIDI implication | safe failure or no-op expectation | current modular behavior status | parity gap summary | required future artifact | required future test category | implementation authorization status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BM` | safely mutate the currently loaded Pad 1 BD engine | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 current-engine mutation | Pad 1 BD lane | BD engine tools | Pad 1 | future selected Pad 1 MIDI channel | current Pad 1 BD engine state | current Pad 1 anchor/profile state | V1.34 safe current-engine mutation depth | none | future-real-midi-risk | missing current Pad 1 engine or anchor state must fail safely later | passive-only | V1.34 Pad 1 current-engine safe mutation behavior not implemented | Pad 1 lane behavior model | future Pad 1 lane parity tests | documentation-only | Captures mutation intent only. |
| `FT` | BD FM tone/FM discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD FM discovery | Pad 1 BD FM lane | BD FM menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD FM mode state | BD FM anchor/profile state | V1.34 BD FM tone/FM discovery depth | none | forbidden-early-scope | missing BD FM state must fail safely later | passive-only | V1.34 BD FM tone/FM discovery behavior not implemented | Pad 1 lane behavior model and BD FM behavior notes | future Pad 1 BD FM parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `FK` | BD FM kick/body discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD FM discovery | Pad 1 BD FM lane | BD FM menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD FM mode state | BD FM anchor/profile state | V1.34 BD FM kick/body discovery depth | none | forbidden-early-scope | missing BD FM state must fail safely later | passive-only | V1.34 BD FM kick/body discovery behavior not implemented | Pad 1 lane behavior model and BD FM behavior notes | future Pad 1 BD FM parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `FG` | BD FM grit discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD FM discovery | Pad 1 BD FM lane | BD FM menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD FM mode state | BD FM anchor/profile state | V1.34 BD FM grit discovery depth | none | forbidden-early-scope | missing BD FM state must fail safely later | passive-only | V1.34 BD FM grit discovery behavior not implemented | Pad 1 lane behavior model and BD FM behavior notes | future Pad 1 BD FM parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `PT` | BD Plastic tone/modulation discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD Plastic discovery | Pad 1 BD Plastic lane | BD Plastic menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD Plastic mode state | BD Plastic anchor/profile state | V1.34 BD Plastic tone/modulation discovery depth | none | forbidden-early-scope | missing BD Plastic state must fail safely later | passive-only | V1.34 BD Plastic tone/modulation discovery behavior not implemented | Pad 1 lane behavior model and BD Plastic behavior notes | future Pad 1 BD Plastic parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `PK` | BD Plastic kick/body discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD Plastic discovery | Pad 1 BD Plastic lane | BD Plastic menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD Plastic mode state | BD Plastic anchor/profile state | V1.34 BD Plastic kick/body discovery depth | none | forbidden-early-scope | missing BD Plastic state must fail safely later | passive-only | V1.34 BD Plastic kick/body discovery behavior not implemented | Pad 1 lane behavior model and BD Plastic behavior notes | future Pad 1 BD Plastic parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `PX` | BD Plastic rubber/experimental discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD Plastic discovery | Pad 1 BD Plastic lane | BD Plastic menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD Plastic mode state | BD Plastic anchor/profile state | V1.34 BD Plastic rubber/experimental discovery depth | none | forbidden-early-scope | missing BD Plastic state must fail safely later | passive-only | V1.34 BD Plastic rubber/experimental discovery behavior not implemented | Pad 1 lane behavior model and BD Plastic behavior notes | future Pad 1 BD Plastic parity tests | documentation-only | Experimental discovery is not an early active candidate. |
| `ST` | BD Silky smooth tone discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD Silky discovery | Pad 1 BD Silky lane | BD Silky menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD Silky mode state | BD Silky anchor/profile state | V1.34 BD Silky smooth tone discovery depth | none | forbidden-early-scope | missing BD Silky state must fail safely later | passive-only | V1.34 BD Silky smooth tone discovery behavior not implemented | Pad 1 lane behavior model and BD Silky behavior notes | future Pad 1 BD Silky parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `SK` | BD Silky kick/body discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD Silky discovery | Pad 1 BD Silky lane | BD Silky menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD Silky mode state | BD Silky anchor/profile state | V1.34 BD Silky kick/body discovery depth | none | forbidden-early-scope | missing BD Silky state must fail safely later | passive-only | V1.34 BD Silky kick/body discovery behavior not implemented | Pad 1 lane behavior model and BD Silky behavior notes | future Pad 1 BD Silky parity tests | documentation-only | Discovery behavior is not an early active candidate. |
| `SC` | BD Silky click/dust discovery | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | Pad 1 BD Silky discovery | Pad 1 BD Silky lane | BD Silky menu/status | Pad 1 | future selected Pad 1 MIDI channel | Pad 1 BD Silky mode state | BD Silky anchor/profile state | V1.34 BD Silky click/dust discovery depth | none | forbidden-early-scope | missing BD Silky state must fail safely later | passive-only | V1.34 BD Silky click/dust discovery behavior not implemented | Pad 1 lane behavior model and BD Silky behavior notes | future Pad 1 BD Silky parity tests | documentation-only | Discovery behavior is not an early active candidate. |

## 7. Current Matrix Slice Decision

This slice adds the next docs-only behavior parity rows after the accepted
scene and group intent slice.

The rows intentionally record Pad 1 lane behavior gaps instead of closing
them.

Current modular behavior remains passive-only for every row in this slice.

Pad 1 mutation and discovery execution remain unimplemented.

## 8. Next Recommended Matrix Slice

After review and acceptance of this slice, the next recommended task is one
of:

- docs-only review/acceptance gate for this Pad 1 lane behavior matrix slice
- docs-only Pad 2 lane behavior matrix slice
- pause at this clean checkpoint

Recommendation:

- review and accept this Pad 1 lane behavior matrix slice before adding more
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

The docs-only V1.34 behavior parity matrix slice is documented for Pad 1 lane
behavior commands.

Hardware remains off.

No implementation is added in this slice.

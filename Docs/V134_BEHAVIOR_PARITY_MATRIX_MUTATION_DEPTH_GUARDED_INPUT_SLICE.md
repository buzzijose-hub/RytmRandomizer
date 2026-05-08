# V1.34 Behavior Parity Matrix: Mutation Depth And Guarded Input Slice

## 1. Purpose

Create the next documentation-only behavior parity matrix slice using the
accepted matrix schema.

This slice covers guarded main-prompt numeric depth inputs, legacy
single-profile mutation depths, current-profile page mutation commands that
choose depth, and selected isolated pad mutation commands that either choose
depth or use group default zone/depth.

This document does not implement runtime behavior, tests, command dispatch,
scene execution, MIDI, port opening, package metadata changes, active CLI
commands, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- e9f54de Add V1.34 behavior parity anchor profile matrix review

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity roadmap accepted
- V1.34 behavior parity matrix plan accepted
- menu/status and utility matrix slice accepted
- anchor/profile matrix slice accepted
- mutation-depth and guarded input matrix slice now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Slice Scope

Included in this slice:

- guarded main-prompt depth input rows generated from
  `GUARDED_MAIN_PROMPT_DEPTH_COMMANDS`
- legacy single-profile mutation rows from
  `LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS`
- current-profile page mutation rows from
  `CURRENT_PROFILE_PAGE_MUTATION_COMMANDS`
- selected isolated pad mutation rows from `ISOLATED_PAD_MUTATION_COMMANDS`

Specifically included command keys:

- `1`
- `2`
- `3`
- `M1`
- `M2`
- `M3`
- `S`
- `F`
- `A`
- `G`
- `K`
- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

Not included in this slice:

- group mutation rows
- lane-aware group mutation rows
- Pad 1 BD lane discovery/mutation rows
- Pad 2 discovery/current-profile mutation rows
- Pad 3 discovery/current-mode mutation rows
- Pad 4 current-mode mutation rows
- scene execution rows
- anchor load/return rows already covered by the prior slice
- undo/commit rows
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

- none
- future-real-midi-risk

The `future-real-midi-risk` value is planning vocabulary only. Mutation depth
commands may eventually influence hardware-facing parameter changes, but this
document does not add MIDI behavior now.

## 6. Matrix Rows

| command key | V1.34 label or operator-facing description | passive metadata source | passive metadata status | behavior domain | command family | menu or page context | target pad scope | target channel scope | state dependencies | anchor/profile dependencies | mutation-depth dependencies | scene/group intent | hardware/MIDI implication | safe failure or no-op expectation | current modular behavior status | parity gap summary | required future artifact | required future test category | implementation authorization status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1` | guarded depth input 1, requires lane/mode prefix | generated from `rytm_randomizer/commands.py:GUARDED_MAIN_PROMPT_DEPTH_COMMANDS` | captured | depth selection and guarded numeric input | guarded depth inputs | main prompt numeric input guard | none unless prompted by active depth flow | none | pending depth prompt context | none | depth value 1 only valid inside a future depth prompt | none | none | bare main-prompt input must fail safely and send no MIDI | passive-only | V1.34 guarded numeric handling not implemented | mutation depth model | future guarded-depth parity tests | documentation-only | Bare main-prompt number is intentionally guarded. |
| `2` | guarded depth input 2, requires lane/mode prefix | generated from `rytm_randomizer/commands.py:GUARDED_MAIN_PROMPT_DEPTH_COMMANDS` | captured | depth selection and guarded numeric input | guarded depth inputs | main prompt numeric input guard | none unless prompted by active depth flow | none | pending depth prompt context | none | depth value 2 only valid inside a future depth prompt | none | none | bare main-prompt input must fail safely and send no MIDI | passive-only | V1.34 guarded numeric handling not implemented | mutation depth model | future guarded-depth parity tests | documentation-only | Bare main-prompt number is intentionally guarded. |
| `3` | guarded depth input 3, requires lane/mode prefix | generated from `rytm_randomizer/commands.py:GUARDED_MAIN_PROMPT_DEPTH_COMMANDS` | captured | depth selection and guarded numeric input | guarded depth inputs | main prompt numeric input guard | none unless prompted by active depth flow | none | pending depth prompt context | none | depth value 3 only valid inside a future depth prompt | none | none | bare main-prompt input must fail safely and send no MIDI | passive-only | V1.34 guarded numeric handling not implemented | mutation depth model | future guarded-depth parity tests | documentation-only | Bare main-prompt number is intentionally guarded. |
| `M1` | Legacy single-profile full micro mutation | `rytm_randomizer/commands.py:LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS` | captured | single-profile mutation | legacy mutation | selected profile full mutation | selected profile target | future selected MIDI channel | selected profile state | selected profile anchor context | fixed depth: micro | none | future-real-midi-risk | missing selected profile must fail safely later | passive-only | V1.34 legacy micro mutation behavior not implemented | mutation depth model | future mutation-depth parity tests | documentation-only | Captures fixed-depth legacy intent only. |
| `M2` | Legacy single-profile full groove mutation | `rytm_randomizer/commands.py:LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS` | captured | single-profile mutation | legacy mutation | selected profile full mutation | selected profile target | future selected MIDI channel | selected profile state | selected profile anchor context | fixed depth: groove | none | future-real-midi-risk | missing selected profile must fail safely later | passive-only | V1.34 legacy groove mutation behavior not implemented | mutation depth model | future mutation-depth parity tests | documentation-only | Captures fixed-depth legacy intent only. |
| `M3` | Legacy single-profile full strong mutation | `rytm_randomizer/commands.py:LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS` | captured | single-profile mutation | legacy mutation | selected profile full mutation | selected profile target | future selected MIDI channel | selected profile state | selected profile anchor context | fixed depth: strong | none | future-real-midi-risk | missing selected profile must fail safely later | passive-only | V1.34 legacy strong mutation behavior not implemented | mutation depth model | future mutation-depth parity tests | documentation-only | Captures fixed-depth legacy intent only. |
| `S` | SRC-only mutation, choose depth | `rytm_randomizer/commands.py:CURRENT_PROFILE_PAGE_MUTATION_COMMANDS` | captured | current-profile mutation | profile selection and anchors | current profile SRC page mutation | current profile target | future selected MIDI channel | current profile state and pending depth prompt | current profile anchor context | requires depth selection | none | future-real-midi-risk | missing current profile or depth must fail safely later | passive-only | V1.34 current-profile SRC mutation behavior not implemented | mutation depth model | future prompt/depth parity tests | documentation-only | No depth prompt exists now. |
| `F` | Filter-only mutation, choose depth | `rytm_randomizer/commands.py:CURRENT_PROFILE_PAGE_MUTATION_COMMANDS` | captured | current-profile mutation | profile selection and anchors | current profile Filter page mutation | current profile target | future selected MIDI channel | current profile state and pending depth prompt | current profile anchor context | requires depth selection | none | future-real-midi-risk | missing current profile or depth must fail safely later | passive-only | V1.34 current-profile filter mutation behavior not implemented | mutation depth model | future prompt/depth parity tests | documentation-only | No depth prompt exists now. |
| `A` | Amp-only mutation, choose depth | `rytm_randomizer/commands.py:CURRENT_PROFILE_PAGE_MUTATION_COMMANDS` | captured | current-profile mutation | profile selection and anchors | current profile Amp page mutation | current profile target | future selected MIDI channel | current profile state and pending depth prompt | current profile anchor context | requires depth selection | none | future-real-midi-risk | missing current profile or depth must fail safely later | passive-only | V1.34 current-profile amp mutation behavior not implemented | mutation depth model | future prompt/depth parity tests | documentation-only | No depth prompt exists now. |
| `G` | Grit-only mutation, choose depth | `rytm_randomizer/commands.py:CURRENT_PROFILE_PAGE_MUTATION_COMMANDS` | captured | current-profile mutation | profile selection and anchors | current profile Grit page mutation | current profile target | future selected MIDI channel | current profile state and pending depth prompt | current profile anchor context | requires depth selection | none | future-real-midi-risk | missing current profile or depth must fail safely later | passive-only | V1.34 current-profile grit mutation behavior not implemented | mutation depth model | future prompt/depth parity tests | documentation-only | No depth prompt exists now. |
| `K` | Kick body mutation, choose depth | `rytm_randomizer/commands.py:CURRENT_PROFILE_PAGE_MUTATION_COMMANDS` | captured | current-profile mutation | profile selection and anchors | current profile kick body mutation | current profile target | future selected MIDI channel | current profile state and pending depth prompt | current profile anchor context | requires depth selection | none | future-real-midi-risk | missing current profile or depth must fail safely later | passive-only | V1.34 current-profile kick/body mutation behavior not implemented | mutation depth model | future prompt/depth parity tests | documentation-only | No depth prompt exists now. |
| `PM` | mutate selected isolated pad only using its group default zone/depth | `rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS` | captured | selected isolated pad mutation | isolated pad mutation | selected isolated pad full/default mutation | selected isolated pad | future selected MIDI channel | selected isolated pad state | selected isolated pad anchor/profile context | uses group default zone/depth | none | future-real-midi-risk | missing selected isolated pad must fail safely later | passive-only | V1.34 selected isolated pad default mutation behavior not implemented | mutation depth model | future selected-pad mutation parity tests | documentation-only | Uses default zone/depth rather than prompting. |
| `PS` | mutate selected isolated pad SRC only, choose depth | `rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS` | captured | selected isolated pad mutation | isolated pad mutation | selected isolated pad SRC mutation | selected isolated pad | future selected MIDI channel | selected isolated pad state and pending depth prompt | selected isolated pad anchor/profile context | requires depth selection | none | future-real-midi-risk | missing selected isolated pad or depth must fail safely later | passive-only | V1.34 selected isolated pad SRC mutation behavior not implemented | mutation depth model | future selected-pad mutation parity tests | documentation-only | No depth prompt exists now. |
| `PF` | mutate selected isolated pad Filter only, choose depth | `rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS` | captured | selected isolated pad mutation | isolated pad mutation | selected isolated pad Filter mutation | selected isolated pad | future selected MIDI channel | selected isolated pad state and pending depth prompt | selected isolated pad anchor/profile context | requires depth selection | none | future-real-midi-risk | missing selected isolated pad or depth must fail safely later | passive-only | V1.34 selected isolated pad filter mutation behavior not implemented | mutation depth model | future selected-pad mutation parity tests | documentation-only | No depth prompt exists now. |
| `PA` | mutate selected isolated pad Amp only, choose depth | `rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS` | captured | selected isolated pad mutation | isolated pad mutation | selected isolated pad Amp mutation | selected isolated pad | future selected MIDI channel | selected isolated pad state and pending depth prompt | selected isolated pad anchor/profile context | requires depth selection | none | future-real-midi-risk | missing selected isolated pad or depth must fail safely later | passive-only | V1.34 selected isolated pad amp mutation behavior not implemented | mutation depth model | future selected-pad mutation parity tests | documentation-only | No depth prompt exists now. |
| `PL` | mutate selected isolated pad LFO only, choose depth | `rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS` | captured | selected isolated pad mutation | isolated pad mutation | selected isolated pad LFO mutation | selected isolated pad | future selected MIDI channel | selected isolated pad state and pending depth prompt | selected isolated pad anchor/profile context | requires depth selection | none | future-real-midi-risk | missing selected isolated pad or depth must fail safely later | passive-only | V1.34 selected isolated pad LFO mutation behavior not implemented | mutation depth model | future selected-pad mutation parity tests | documentation-only | No depth prompt exists now. |
| `PO` | mutate selected isolated pad Morph only, choose depth | `rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS` | captured | selected isolated pad mutation | isolated pad mutation | selected isolated pad Morph mutation | selected isolated pad | future selected MIDI channel | selected isolated pad state and pending depth prompt | selected isolated pad anchor/profile context | requires depth selection | none | future-real-midi-risk | missing selected isolated pad or depth must fail safely later | passive-only | V1.34 selected isolated pad morph mutation behavior not implemented | mutation depth model | future selected-pad mutation parity tests | documentation-only | No depth prompt exists now. |
| `PB` | mutate selected isolated pad Body only, choose depth | `rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS` | captured | selected isolated pad mutation | isolated pad mutation | selected isolated pad Body mutation | selected isolated pad | future selected MIDI channel | selected isolated pad state and pending depth prompt | selected isolated pad anchor/profile context | requires depth selection | none | future-real-midi-risk | missing selected isolated pad or depth must fail safely later | passive-only | V1.34 selected isolated pad body mutation behavior not implemented | mutation depth model | future selected-pad mutation parity tests | documentation-only | No depth prompt exists now. |
| `PG` | mutate selected isolated pad Grit only, choose depth | `rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS` | captured | selected isolated pad mutation | isolated pad mutation | selected isolated pad Grit mutation | selected isolated pad | future selected MIDI channel | selected isolated pad state and pending depth prompt | selected isolated pad anchor/profile context | requires depth selection | none | future-real-midi-risk | missing selected isolated pad or depth must fail safely later | passive-only | V1.34 selected isolated pad grit mutation behavior not implemented | mutation depth model | future selected-pad mutation parity tests | documentation-only | No depth prompt exists now. |

## 7. Current Matrix Slice Decision

This slice adds the next docs-only behavior parity rows after the accepted
anchor/profile slice.

The rows intentionally record behavior gaps instead of closing them.

Current modular behavior remains passive-only for every row in this slice.

## 8. Next Recommended Matrix Slice

After review and acceptance of this slice, the next recommended task is one of:

- docs-only review/acceptance gate for this mutation-depth and guarded input
  matrix slice
- docs-only scene and group intent matrix slice
- pause at this clean checkpoint

Recommendation:

- review and accept this mutation-depth and guarded input matrix slice before
  adding more rows

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

The docs-only V1.34 behavior parity matrix slice is documented for
mutation-depth and guarded numeric input commands.

Hardware remains off.

No implementation is added in this slice.

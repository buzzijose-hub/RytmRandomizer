# V1.34 Behavior Parity Matrix: Anchor And Profile Slice

## 1. Purpose

Create the next documentation-only behavior parity matrix slice using the
accepted matrix schema.

This slice covers anchor load, anchor return, profile selection, profile
rotation, mode load, and four-pad group anchor commands.

This document does not implement runtime behavior, tests, command dispatch,
scene execution, MIDI, port opening, package metadata changes, active CLI
commands, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 892d9b6 Add V1.34 behavior parity menu utility matrix review

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity roadmap accepted
- V1.34 behavior parity matrix plan accepted
- menu/status and utility matrix slice accepted
- anchor/profile matrix slice now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Slice Scope

Included in this slice:

- profile workflow commands from `PROFILE_WORKFLOW_COMMANDS`
- anchor load and return rows from `GROUP_COMMANDS`
- Pad 1 BD anchor load, return, and rotation rows from `PAD1_COMMANDS`
- Pad 2 profile load, return, and rotation rows from `PAD2_COMMANDS`
- selected isolated pad anchor return row from `ISOLATED_PAD_UTILITY_COMMANDS`
- Pad 3 mode load, return, and rotation rows from `PAD3_COMMANDS`
- Pad 4 return and rotation rows from `PAD4_COMMANDS`

Specifically included command keys:

- `P`
- `M`
- `O`
- `Z`
- `BR`
- `BH`
- `BS`
- `BC`
- `BA`
- `BF`
- `FZ`
- `BP`
- `PBH`
- `BI`
- `SBH`
- `P2B`
- `P2H`
- `P2C`
- `P2F`
- `P2R`
- `P2Z`
- `PZ`
- `SL`
- `SB`
- `SX`
- `SA`
- `P3R`
- `P3A`
- `P4R`
- `P4A`

Not included in this slice:

- mutation commands
- scene execution rows
- menu/status rows already covered by the first slice
- undo/commit rows
- waveform exploration rows
- guarded numeric depth rows
- lane-specific mutation rows
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

The `future-real-midi-risk` value is planning vocabulary only. Anchor and
profile commands may eventually affect hardware-facing machine/profile state,
but this document does not add MIDI behavior now.

## 6. Matrix Rows

| command key | V1.34 label or operator-facing description | passive metadata source | passive metadata status | behavior domain | command family | menu or page context | target pad scope | target channel scope | state dependencies | anchor/profile dependencies | mutation-depth dependencies | scene/group intent | hardware/MIDI implication | safe failure or no-op expectation | current modular behavior status | parity gap summary | required future artifact | required future test category | implementation authorization status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P` | select/switch profile and change Rytm machine | `rytm_randomizer/commands.py:PROFILE_WORKFLOW_COMMANDS` | captured | profile selection | profile selection and anchors | profile selection workflow | selected profile target | future selected MIDI channel | selected profile state | selected profile and machine intent | none | none | future-real-midi-risk | missing/unsupported profile selection must fail safely later | passive-only | V1.34 profile selection and machine-change behavior not implemented | state and selection model | future profile-selection parity tests | documentation-only | No real machine change exists now. |
| `M` | load selected profile anchor | `rytm_randomizer/commands.py:PROFILE_WORKFLOW_COMMANDS` | captured | anchor load and return | profile selection and anchors | selected profile anchor workflow | selected profile target | future selected MIDI channel | selected profile state | selected profile anchor context | none | none | future-real-midi-risk | missing selected profile must fail safely later | passive-only | V1.34 selected-profile anchor load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Depends on future selected profile model. |
| `O` | load full 4-pad group anchors | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | group layout and group anchors | four-pad group layout and anchors | full group anchor load | Pads 1-4 | future selected MIDI channels | group anchor state | group profile anchors for Pads 1-4 | none | four-pad group anchor intent | future-real-midi-risk | unsupported group load must fail safely later | passive-only | V1.34 full group anchor load behavior not implemented | scene and group intent model | future group-anchor parity tests | documentation-only | Does not authorize hardware group loading. |
| `Z` | return all 4 group pads to anchors | `rytm_randomizer/commands.py:GROUP_COMMANDS` | captured | group layout and group anchors | four-pad group layout and anchors | full group anchor return | Pads 1-4 | future selected MIDI channels | group anchor state | group profile anchors for Pads 1-4 | none | four-pad group return intent | future-real-midi-risk | unsupported group return must fail safely later | passive-only | V1.34 full group anchor return behavior not implemented | scene and group intent model | future group-anchor parity tests | documentation-only | Does not authorize hardware group return. |
| `BR` | rotate Pad 1 to the next profiled BD engine | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | BD engine navigation | Pad 1 BD anchors and mutation | Pad 1 BD profile rotation | Pad 1 | future selected MIDI channel | current Pad 1 BD profile state | profiled BD engine order | none | none | future-real-midi-risk | missing profile order must fail safely later | passive-only | V1.34 Pad 1 profile rotation behavior not implemented | state and selection model | future profile-rotation parity tests | documentation-only | Rotation order must be documented before implementation. |
| `BH` | load Pad 1 BD Hard anchor, primary default | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | Pad 1 BD anchors and mutation | Pad 1 BD Hard anchor | Pad 1 | future selected MIDI channel | Pad 1 anchor state | BD Hard primary default anchor | none | none | future-real-midi-risk | missing anchor metadata must fail safely later | passive-only | V1.34 Pad 1 BD Hard anchor load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Primary Pad 1 home anchor. |
| `BS` | load Pad 1 BD Sharp anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | Pad 1 BD anchors and mutation | Pad 1 BD Sharp anchor | Pad 1 | future selected MIDI channel | Pad 1 anchor state | BD Sharp anchor | none | none | future-real-midi-risk | missing anchor metadata must fail safely later | passive-only | V1.34 Pad 1 BD Sharp anchor load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Anchor name is captured as passive command label only. |
| `BC` | load Pad 1 BD Classic anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | Pad 1 BD anchors and mutation | Pad 1 BD Classic anchor | Pad 1 | future selected MIDI channel | Pad 1 anchor state | BD Classic anchor | none | none | future-real-midi-risk | missing anchor metadata must fail safely later | passive-only | V1.34 Pad 1 BD Classic anchor load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Anchor name is captured as passive command label only. |
| `BA` | load Pad 1 BD Acoustic anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | Pad 1 BD anchors and mutation | Pad 1 BD Acoustic anchor | Pad 1 | future selected MIDI channel | Pad 1 anchor state | BD Acoustic anchor | none | none | future-real-midi-risk | missing anchor metadata must fail safely later | passive-only | V1.34 Pad 1 BD Acoustic anchor load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Does not implement profile 4. |
| `BF` | load Pad 1 BD FM profiled anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | BD FM lane | Pad 1 BD FM anchor | Pad 1 | future selected MIDI channel | Pad 1 BD FM state | BD FM profiled anchor | none | none | future-real-midi-risk | missing profile anchor must fail safely later | passive-only | V1.34 BD FM anchor load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Does not authorize BD FM execution. |
| `FZ` | return Pad 1 BD FM to anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | BD FM lane | Pad 1 BD FM anchor return | Pad 1 | future selected MIDI channel | Pad 1 BD FM state | current BD FM anchor | none | none | future-real-midi-risk | missing BD FM anchor must fail safely later | passive-only | V1.34 BD FM anchor return behavior not implemented | anchor lifecycle model | future anchor-return parity tests | documentation-only | Return behavior remains absent. |
| `BP` | load Pad 1 BD Plastic profiled anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | BD Plastic lane | Pad 1 BD Plastic anchor | Pad 1 | future selected MIDI channel | Pad 1 BD Plastic state | BD Plastic profiled anchor | none | none | future-real-midi-risk | missing profile anchor must fail safely later | passive-only | V1.34 BD Plastic anchor load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Does not authorize BD Plastic execution. |
| `PBH` | return Pad 1 BD Plastic to anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | BD Plastic lane | Pad 1 BD Plastic anchor return | Pad 1 | future selected MIDI channel | Pad 1 BD Plastic state | current BD Plastic anchor | none | none | future-real-midi-risk | missing BD Plastic anchor must fail safely later | passive-only | V1.34 BD Plastic anchor return behavior not implemented | anchor lifecycle model | future anchor-return parity tests | documentation-only | Return behavior remains absent. |
| `BI` | load Pad 1 BD Silky profiled anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | BD Silky lane | Pad 1 BD Silky anchor | Pad 1 | future selected MIDI channel | Pad 1 BD Silky state | BD Silky profiled anchor | none | none | future-real-midi-risk | missing profile anchor must fail safely later | passive-only | V1.34 BD Silky anchor load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Does not authorize BD Silky execution. |
| `SBH` | return Pad 1 BD Silky to anchor | `rytm_randomizer/commands.py:PAD1_COMMANDS` | captured | anchor load and return | BD Silky lane | Pad 1 BD Silky anchor return | Pad 1 | future selected MIDI channel | Pad 1 BD Silky state | current BD Silky anchor | none | none | future-real-midi-risk | missing BD Silky anchor must fail safely later | passive-only | V1.34 BD Silky anchor return behavior not implemented | anchor lifecycle model | future anchor-return parity tests | documentation-only | Return behavior remains absent. |
| `P2B` | load Pad 2 BD Classic rolling low percussion / home | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | anchor load and return | Pad 2 lane | Pad 2 BD Classic home | Pad 2 | future selected MIDI channel | Pad 2 profile state | Pad 2 BD Classic home anchor | none | none | future-real-midi-risk | missing Pad 2 anchor must fail safely later | passive-only | V1.34 Pad 2 BD Classic load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Pad 2 execution remains absent. |
| `P2H` | load Pad 2 SD Hard pressure snare | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | anchor load and return | Pad 2 lane | Pad 2 SD Hard anchor | Pad 2 | future selected MIDI channel | Pad 2 profile state | Pad 2 SD Hard anchor | none | none | future-real-midi-risk | missing Pad 2 anchor must fail safely later | passive-only | V1.34 Pad 2 SD Hard load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Pad 2 execution remains absent. |
| `P2C` | load Pad 2 SD Classic rolling snare | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | anchor load and return | Pad 2 lane | Pad 2 SD Classic anchor | Pad 2 | future selected MIDI channel | Pad 2 profile state | Pad 2 SD Classic anchor | none | none | future-real-midi-risk | missing Pad 2 anchor must fail safely later | passive-only | V1.34 Pad 2 SD Classic load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Pad 2 execution remains absent. |
| `P2F` | load Pad 2 SD FM metallic snare | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | anchor load and return | Pad 2 lane | Pad 2 SD FM anchor | Pad 2 | future selected MIDI channel | Pad 2 profile state | Pad 2 SD FM anchor | none | none | future-real-midi-risk | missing Pad 2 anchor must fail safely later | passive-only | V1.34 Pad 2 SD FM load behavior not implemented | anchor lifecycle model | future anchor-load parity tests | documentation-only | Pad 2 execution remains absent. |
| `P2R` | rotate Pad 2 through profiled secondary-lane engines | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | profile selection | Pad 2 lane | Pad 2 profile rotation | Pad 2 | future selected MIDI channel | Pad 2 profile state | profiled secondary-lane order | none | none | future-real-midi-risk | missing profile order must fail safely later | passive-only | V1.34 Pad 2 profile rotation behavior not implemented | state and selection model | future profile-rotation parity tests | documentation-only | Rotation order must be documented before implementation. |
| `P2Z` | return current Pad 2 profile to anchor | `rytm_randomizer/commands.py:PAD2_COMMANDS` | captured | anchor load and return | Pad 2 lane | Pad 2 current profile anchor return | Pad 2 | future selected MIDI channel | Pad 2 current profile state | current Pad 2 profile anchor | none | none | future-real-midi-risk | missing current Pad 2 profile must fail safely later | passive-only | V1.34 Pad 2 current-profile return behavior not implemented | anchor lifecycle model | future anchor-return parity tests | documentation-only | Return behavior remains absent. |
| `PZ` | return selected isolated pad to anchor only | `rytm_randomizer/commands.py:ISOLATED_PAD_UTILITY_COMMANDS` | captured | anchor load and return | isolated pad mutation | selected isolated pad anchor return | selected isolated pad | future selected MIDI channel | selected isolated pad state | selected isolated pad anchor | none | none | future-real-midi-risk | missing selected isolated pad must fail safely later | passive-only | V1.34 selected isolated pad anchor return behavior not implemented | state and selection model | future anchor-return parity tests | documentation-only | Does not authorize isolated pad mutation. |
| `SL` | Pad 3 SY Raw LP1 bassline mode | `rytm_randomizer/commands.py:PAD3_COMMANDS` | captured | profile selection | Pad 3 lane | Pad 3 SY Raw LP1 mode load | Pad 3 | future selected MIDI channel | Pad 3 mode state | Pad 3 SY Raw LP1 mode | none | none | future-real-midi-risk | missing Pad 3 mode metadata must fail safely later | passive-only | V1.34 Pad 3 LP1 mode load behavior not implemented | state and selection model | future mode-load parity tests | documentation-only | Mode load remains passive metadata only. |
| `SB` | Pad 3 SY Raw Bandpass mid-bass mode | `rytm_randomizer/commands.py:PAD3_COMMANDS` | captured | profile selection | Pad 3 lane | Pad 3 SY Raw Bandpass mode load | Pad 3 | future selected MIDI channel | Pad 3 mode state | Pad 3 SY Raw Bandpass mode | none | none | future-real-midi-risk | missing Pad 3 mode metadata must fail safely later | passive-only | V1.34 Pad 3 Bandpass mode load behavior not implemented | state and selection model | future mode-load parity tests | documentation-only | Mode load remains passive metadata only. |
| `SX` | Pad 3 SY Raw sci-fi motion accent mode | `rytm_randomizer/commands.py:PAD3_COMMANDS` | captured | profile selection | Pad 3 lane | Pad 3 SY Raw sci-fi mode load | Pad 3 | future selected MIDI channel | Pad 3 mode state | Pad 3 SY Raw sci-fi mode | none | none | future-real-midi-risk | missing Pad 3 mode metadata must fail safely later | passive-only | V1.34 Pad 3 sci-fi mode load behavior not implemented | state and selection model | future mode-load parity tests | documentation-only | Mode load remains passive metadata only. |
| `SA` | return Pad 3 SY Raw to anchor | `rytm_randomizer/commands.py:PAD3_COMMANDS` | captured | anchor load and return | Pad 3 lane | Pad 3 SY Raw anchor return | Pad 3 | future selected MIDI channel | Pad 3 mode state | Pad 3 SY Raw anchor | none | none | future-real-midi-risk | missing Pad 3 anchor must fail safely later | passive-only | V1.34 Pad 3 SY Raw anchor return behavior not implemented | anchor lifecycle model | future anchor-return parity tests | documentation-only | Return behavior remains absent. |
| `P3R` | rotate Pad 3 through SY Raw behavior modes | `rytm_randomizer/commands.py:PAD3_COMMANDS` | captured | profile selection | Pad 3 lane | Pad 3 SY Raw mode rotation | Pad 3 | future selected MIDI channel | Pad 3 mode state | SY Raw behavior mode order | none | none | future-real-midi-risk | missing mode order must fail safely later | passive-only | V1.34 Pad 3 mode rotation behavior not implemented | state and selection model | future profile-rotation parity tests | documentation-only | Rotation order must be documented before implementation. |
| `P3A` | return Pad 3 to SY Raw Mid Bass anchor / home | `rytm_randomizer/commands.py:PAD3_COMMANDS` | captured | anchor load and return | Pad 3 lane | Pad 3 SY Raw Mid Bass home return | Pad 3 | future selected MIDI channel | Pad 3 mode state | Pad 3 SY Raw Mid Bass home anchor | none | none | future-real-midi-risk | missing Pad 3 home anchor must fail safely later | passive-only | V1.34 Pad 3 home return behavior not implemented | anchor lifecycle model | future anchor-return parity tests | documentation-only | Return behavior remains absent. |
| `P4R` | rotate Pad 4 through BD Acoustic behavior modes | `rytm_randomizer/commands.py:PAD4_COMMANDS` | captured | profile selection | Pad 4 lane | Pad 4 BD Acoustic mode rotation | Pad 4 | future selected MIDI channel | Pad 4 mode state | BD Acoustic behavior mode order | none | none | future-real-midi-risk | missing mode order must fail safely later | passive-only | V1.34 Pad 4 mode rotation behavior not implemented | state and selection model | future profile-rotation parity tests | documentation-only | Does not implement profile 4 support. |
| `P4A` | return Pad 4 to BD Acoustic body/accent anchor / home | `rytm_randomizer/commands.py:PAD4_COMMANDS` | captured | anchor load and return | Pad 4 lane | Pad 4 BD Acoustic home return | Pad 4 | future selected MIDI channel | Pad 4 mode state | Pad 4 BD Acoustic home anchor | none | none | future-real-midi-risk | missing Pad 4 home anchor must fail safely later | passive-only | V1.34 Pad 4 home return behavior not implemented | anchor lifecycle model | future anchor-return parity tests | documentation-only | Does not implement profile 4 support. |

## 7. Current Matrix Slice Decision

This slice adds the next docs-only behavior parity rows after the accepted
menu/status and utility slice.

The rows intentionally record behavior gaps instead of closing them.

Current modular behavior remains passive-only for every row in this slice.

## 8. Next Recommended Matrix Slice

After review and acceptance of this slice, the next recommended task is one of:

- docs-only review/acceptance gate for this anchor/profile matrix slice
- docs-only mutation-depth and guarded numeric input rows
- pause at this clean checkpoint

Recommendation:

- review and accept this anchor/profile matrix slice before adding more rows

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
anchor/profile commands.

Hardware remains off.

No implementation is added in this slice.

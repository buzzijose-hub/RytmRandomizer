# V1.34 Behavior Parity Matrix: Menu And Utility Slice

## 1. Purpose

Create the first documentation-only behavior parity matrix slice using the
accepted matrix schema.

This slice covers menu/status display commands and core utility/session
commands only.

This document does not implement runtime behavior, tests, command dispatch,
scene execution, MIDI, port opening, package metadata changes, active CLI
commands, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 0a9b8f5 Add V1.34 behavior parity matrix plan review

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity roadmap accepted
- V1.34 behavior parity matrix plan accepted
- first docs-only matrix slice now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Slice Scope

Included in this first slice:

- menu/status display commands from `MENU_COMMANDS`
- core utility/session commands from `UTILITY_COMMANDS`

Specifically included command keys:

- `BD`
- `FM`
- `PD`
- `SM`
- `P2M`
- `J`
- `GM`
- `SCN`
- `PR`
- `SR`
- `P3M`
- `P4M`
- `H`
- `R`
- `T`
- `C`
- `Q`

Not included in this slice:

- mutation commands
- scene execution rows
- anchor load/return rows
- undo/commit rows
- isolated pad mutation rows
- group mutation rows
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

- none
- future-real-midi-risk

The `future-real-midi-risk` value is used only for target/channel selection
commands because future runtime behavior could influence later hardware output
targets. It does not imply any MIDI behavior exists now.

## 6. First Matrix Rows

| command key | V1.34 label or operator-facing description | passive metadata source | passive metadata status | behavior domain | command family | menu or page context | target pad scope | target channel scope | state dependencies | anchor/profile dependencies | mutation-depth dependencies | scene/group intent | hardware/MIDI implication | safe failure or no-op expectation | current modular behavior status | parity gap summary | required future artifact | required future test category | implementation authorization status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BD` | show BD engine tools | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | Pad 1 BD anchors and mutation | main prompt BD engine tools | Pad 1 | none | display context only | none for display | none | none | none | display/no-op; no MIDI | passive-only | V1.34 menu text and routing behavior not implemented | menu/status behavior notes | future display/routing parity tests | documentation-only | Lower-risk display row. |
| `FM` | show BD FM menu/status | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | BD FM lane | BD FM menu/status | Pad 1 | none | future current BD FM status may matter | BD FM profile context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 BD FM status display behavior not implemented | menu/status behavior notes | future display/status parity tests | documentation-only | Status wording may later depend on current profile state. |
| `PD` | show BD Plastic menu/status | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | BD Plastic lane | BD Plastic menu/status | Pad 1 | none | future current BD Plastic status may matter | BD Plastic profile context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 BD Plastic status display behavior not implemented | menu/status behavior notes | future display/status parity tests | documentation-only | Status wording may later depend on current profile state. |
| `SM` | show BD Silky menu/status | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | BD Silky lane | BD Silky menu/status | Pad 1 | none | future current BD Silky status may matter | BD Silky profile context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 BD Silky status display behavior not implemented | menu/status behavior notes | future display/status parity tests | documentation-only | Status wording may later depend on current profile state. |
| `P2M` | show Pad 2 snare / secondary percussion menu | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | Pad 2 lane | Pad 2 secondary percussion menu | Pad 2 | none | display context only | Pad 2 profile context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 Pad 2 menu behavior not implemented | menu/status behavior notes | future display/routing parity tests | documentation-only | Does not authorize Pad 2 execution. |
| `J` | show 4-pad group layout | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | four-pad group layout and anchors | group layout print | Pads 1-4 | none | display context only | group anchor context | none | four-pad layout intent | none | display/no-op; no MIDI | passive-only | V1.34 group layout print behavior not implemented | group intent model | future display/routing parity tests | documentation-only | Read-only group layout visibility only. |
| `GM` | show global 4-pad mutation tools | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | four-pad group mutation | global mutation tools menu | Pads 1-4 | none | display context only | group mutation context | none | four-pad mutation intent | none | display/no-op; no MIDI | passive-only | V1.34 global mutation menu behavior not implemented | group intent model | future display/routing parity tests | documentation-only | Does not authorize group mutation. |
| `SCN` | show scene / preset tools | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | scenes | scene/preset tools menu | four-pad group | none | display context only | scene anchor context | none | scene selection intent | none | display/no-op; no MIDI | passive-only | V1.34 scene menu behavior not implemented | scene and group intent model | future display/routing parity tests | documentation-only | Does not authorize scene execution. |
| `PR` | show selected isolated pad | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | isolated pad mutation | selected isolated pad print | selected isolated pad | none | selected isolated pad state | selected isolated pad profile context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 selected pad display behavior not implemented | state and selection model | future display/status parity tests | documentation-only | Depends on future selected isolated pad state model. |
| `SR` | show Pad 3 SY Raw discovery menu/status | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | Pad 3 lane | Pad 3 SY Raw discovery menu/status | Pad 3 | none | future Pad 3 mode/status may matter | Pad 3 SY Raw context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 Pad 3 SY Raw status behavior not implemented | menu/status behavior notes | future display/status parity tests | documentation-only | Does not authorize Pad 3 mutation. |
| `P3M` | show Pad 3 SY Raw bass / synth-percussion menu | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | Pad 3 lane | Pad 3 bass/synth-percussion menu | Pad 3 | none | display context only | Pad 3 SY Raw context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 Pad 3 menu behavior not implemented | menu/status behavior notes | future display/routing parity tests | documentation-only | Does not authorize Pad 3 execution. |
| `P4M` | show Pad 4 BD Acoustic body / accent menu | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | menu/status display | Pad 4 lane | Pad 4 body/accent menu | Pad 4 | none | display context only | Pad 4 BD Acoustic context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 Pad 4 menu behavior not implemented | menu/status behavior notes | future display/routing parity tests | documentation-only | Does not authorize profile 4 or Pad 4 execution. |
| `H` | show current anchor | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | current anchor reporting | utility and state | current anchor print | current target/profile | none | current anchor state | current profile anchor context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 current anchor reporting behavior not implemented | anchor lifecycle model | future state-report parity tests | documentation-only | Runtime anchor state remains absent. |
| `R` | print current script state | `rytm_randomizer/commands.py:MENU_COMMANDS` | captured | script state reporting | utility and state | script state print | current script scope | current configured channel | current script state | current profile/anchor context | none | none | none | display/no-op; no MIDI | passive-only | V1.34 script state reporting behavior not implemented | state and selection model | future state-report parity tests | documentation-only | Runtime script state remains absent. |
| `T` | select target pad/channel | `rytm_randomizer/commands.py:UTILITY_COMMANDS` | captured | target pad and channel selection | utility and state | target selection prompt | future selected target pad | future selected target channel | target selection state | none | none | none | future-real-midi-risk | missing/unsupported selection must fail safely later | passive-only | V1.34 target selection prompt and state transition not implemented | state and selection model | future prompt/state transition parity tests | documentation-only | Selection may affect later hardware targets, so it remains blocked. |
| `C` | change MIDI channel | `rytm_randomizer/commands.py:UTILITY_COMMANDS` | captured | target pad and channel selection | utility and state | MIDI channel selection prompt | current target pad | future selected MIDI channel | channel selection state | none | none | none | future-real-midi-risk | missing/unsupported channel must fail safely later | passive-only | V1.34 MIDI channel prompt and state transition not implemented | state and selection model | future prompt/state transition parity tests | documentation-only | No real MIDI or channel mutation exists now. |
| `Q` | quit | `rytm_randomizer/commands.py:UTILITY_COMMANDS` | captured | quit/back/no-op behavior | quit | operator session quit | none | none | operator session state | none | none | none | none | safe session exit/no-op; no MIDI | passive-only | V1.34 session loop exit behavior not implemented | session lifecycle model | future session-loop parity tests | documentation-only | No runtime command loop exists now. |

## 7. Current Matrix Slice Decision

This slice establishes the accepted matrix schema in document form and adds the
first rows for lower-risk menu/status and utility commands.

The rows intentionally record behavior gaps instead of closing them.

Current modular behavior remains passive-only for every row in this slice.

## 8. Next Recommended Matrix Slice

After review and acceptance of this first matrix slice, the next recommended
task is one of:

- docs-only review/acceptance gate for this matrix slice
- docs-only anchor/profile command rows
- pause at this clean checkpoint

Recommendation:

- review and accept this first matrix slice before adding more rows

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

The first docs-only V1.34 behavior parity matrix slice is documented for
menu/status and utility commands.

Hardware remains off.

No implementation is added in this slice.

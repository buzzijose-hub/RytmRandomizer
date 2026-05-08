# V1.34 L PZ Next Passive Metadata Gap Decision Note

## 1. Purpose

Decide the next passive registry gap category after the completed `B`, `E`,
`W`, and `U` metadata checkpoint.

This is a documentation-only decision note.

This document does not add command metadata.

This document does not add tests.

This document does not edit runtime code.

This document does not add MIDI, ports, dispatch, active behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 50e776f Update checkpoint after B E W U passive metadata

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review accepted
- `T`, `C`, and `Q` implemented as passive scaffold-only metadata
- `B`, `E`, `W`, and `U` implemented as passive scaffold-only metadata
- next passive metadata gap now being decided

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Passive Metadata Position

Completed passive gap categories:

- `T` / select target pad/channel
- `C` / change MIDI channel
- `Q` / quit
- `B` / back to current anchor
- `E` / commit current state as new anchor
- `W` / waveform exploration only
- `U` / undo previous script-generated state

Current passive command count:

- 89

Captured V1.34 operator command entries:

- 106

Captured operator command entries now modeled as passive command metadata:

- 86

Captured operator command entries still not modeled as passive command
metadata:

- 20

## 4. Candidate Next Gap Categories

Remaining broad gap categories include:

- isolated single-pad selection/status and return:
  - `L`, `PZ`
- isolated single-pad mutation:
  - `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, `PG`
- profile selection and anchor loading:
  - `P`, `M`
- generic current-profile page mutation:
  - `S`, `F`, `A`, `G`, `K`
- legacy single-profile mutation:
  - `M1`, `M2`, `M3`

All remaining categories must stay passive/scaffold-only unless a later
reviewed plan explicitly says otherwise.

## 5. Decision

The next recommended planning target is:

- isolated single-pad selection/status and return metadata

Candidate commands:

- `L` / select isolated single-pad mutation target, default Pad 3
- `PZ` / return selected isolated pad to anchor only

Do not implement these commands in this slice.

Do not add metadata in this slice.

Do not add tests or fixture changes in this slice.

The next slice should be a docs-only passive metadata expansion plan for
`L` and `PZ`.

## 6. Why This Category Is Next

Reasons to plan `L` and `PZ` next:

- the original gap review listed isolated single-pad selection/status and
  return immediately after anchor/state utilities
- the category is compact enough for a tiny planning slice
- `L` captures selected isolated-pad target vocabulary without mutating
  anything
- `PZ` captures selected isolated-pad return vocabulary without adding active
  return behavior
- keeping `L` and `PZ` separate from `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`,
  and `PG` avoids widening into isolated mutation metadata too soon
- documenting this split preserves V1.34 language while keeping execution
  absent

## 7. Why Not Implement Yet

`L` and `PZ` reference selected isolated-pad behavior in the V1.34 operator
surface.

Even as passive metadata, their labels and scopes should make clear that no
selected-pad runtime state is changed and no anchor return is executed.

They should be planned first, then reviewed, then implemented only after
explicit approval.

## 8. Safe Alternatives

Safe alternatives remain:

- pause at the completed `B`, `E`, `W`, and `U` checkpoint
- update a broader project progress report
- keep passive metadata expansion frozen and return to project-level planning
- create a larger remaining-gap roadmap before more metadata expansion

The current recommendation remains `L` and `PZ` planning first.

## 9. Safety Boundaries

This decision note confirms:

- no command metadata changes
- no tests changed
- no fixtures changed
- no runtime code changes
- no CLI command changes
- no package metadata changes
- no dependency selection
- no `mido`
- no real MIDI dependency
- no MIDI port opening
- no MIDI sending
- no active CLI command
- no execute-command
- no send-command
- no hardware-test
- no dispatch
- no command execution
- no scene execution
- no selected-pad runtime state mutation
- no isolated-pad mutation execution
- no anchor return execution
- no hardware behavior
- no hardware detection
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no profile `"4"` implementation
- no hardware validation

`rytm_hybrid_randomizer_v134.py` remains untouched.

Analog Rytm MKII remains off.

Analog Four MKII remains off.

## 10. Next Recommended Task

Create a docs-only passive metadata expansion plan for:

- `L`
- `PZ`

That future plan should define exact passive scaffold-only metadata, expected
command count movement, expected fixture changes, tests to update, and safety
boundaries.

Do not implement metadata until the plan is reviewed and explicitly approved.

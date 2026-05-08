# V1.34 Isolated Pad Mutation Next Passive Metadata Gap Decision Note

## 1. Purpose

Decide the next passive registry gap category after the completed `L` and
`PZ` metadata checkpoint.

This is a documentation-only decision note.

This document does not add command metadata.

This document does not add tests.

This document does not edit runtime code.

This document does not add MIDI, ports, dispatch, active behavior, selected-pad
runtime mutation, isolated-pad mutation execution, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 0e7a80a Update checkpoint after L PZ passive metadata

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review accepted
- `T`, `C`, and `Q` implemented as passive scaffold-only metadata
- `B`, `E`, `W`, and `U` implemented as passive scaffold-only metadata
- `L` and `PZ` implemented as passive scaffold-only metadata
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
- `L` / select isolated single-pad mutation target, default Pad 3
- `PZ` / return selected isolated pad to anchor only

Current passive command count:

- 91

Captured V1.34 operator command entries:

- 106

Captured operator command entries now modeled as passive command metadata:

- 88

Captured operator command entries still not modeled as passive command
metadata:

- 18

## 4. Candidate Next Gap Categories

Remaining broad gap categories include:

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

- isolated single-pad mutation metadata

Candidate commands:

- `PM` / mutate selected isolated pad only using its group default zone/depth
- `PS` / mutate selected isolated pad SRC only, choose depth
- `PF` / mutate selected isolated pad Filter only, choose depth
- `PA` / mutate selected isolated pad Amp only, choose depth
- `PL` / mutate selected isolated pad LFO only, choose depth
- `PO` / mutate selected isolated pad Morph only, choose depth
- `PB` / mutate selected isolated pad Body only, choose depth
- `PG` / mutate selected isolated pad Grit only, choose depth

Do not implement these commands in this slice.

Do not add metadata in this slice.

Do not add tests or fixture changes in this slice.

The next slice should be a docs-only passive metadata expansion plan for
`PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG`.

## 6. Why This Category Is Next

Reasons to plan isolated single-pad mutation metadata next:

- `L` and `PZ` now capture the selected isolated-pad vocabulary boundary
  without changing selected-pad runtime state
- the mutation commands are the natural continuation of that isolated-pad
  operator surface
- the category is coherent and can be planned as a single passive metadata
  group
- the group preserves V1.34 language for selected isolated-pad mutation
  controls without enabling execution
- documenting this category before metadata changes helps prevent accidental
  active mutation semantics from creeping into passive scaffolding

## 7. Why Not Implement Yet

These commands refer directly to mutation behavior in the V1.34 operator
surface.

Even as passive metadata, their labels, scopes, and safety fields must make
clear that no selected pad is mutated and no mutation is executed.

They should be planned first, then reviewed, then implemented only after
explicit approval.

## 8. Safe Alternatives

Safe alternatives remain:

- pause at the completed `L` and `PZ` checkpoint
- update a broader project progress report
- choose profile selection and anchor loading metadata for a later plan
- choose generic current-profile page mutation metadata for a later plan
- keep passive metadata expansion frozen and return to project-level planning

The current recommendation remains isolated single-pad mutation planning first.

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

- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

That future plan should define exact passive scaffold-only metadata, expected
command count movement, expected fixture changes, tests to update, and safety
boundaries.

Do not implement metadata until the plan is reviewed and explicitly approved.

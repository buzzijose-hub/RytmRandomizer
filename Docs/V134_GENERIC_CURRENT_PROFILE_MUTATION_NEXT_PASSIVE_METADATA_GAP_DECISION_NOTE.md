# V1.34 Generic Current-Profile Mutation Next Passive Metadata Gap Decision Note

## Purpose

Select the next passive metadata planning target after the completed legacy
single-profile mutation passive metadata checkpoint.

This note is documentation-only. It does not add metadata, tests, fixtures,
runtime code, CLI wiring, dispatch, MIDI, ports, package metadata, active
behavior, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- f1d8735 Update checkpoint after legacy single-profile mutation passive metadata

Current passive command count:

- 104

Captured V1.34 operator entries modeled as passive command metadata:

- 101

Remaining captured command-surface gaps:

- 5

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Current Decision

Select the remaining generic current-profile page mutation commands as the next
passive metadata planning target:

- `S` / SRC-only mutation, choose depth
- `F` / Filter-only mutation, choose depth
- `A` / Amp-only mutation, choose depth
- `G` / Grit-only mutation, choose depth
- `K` / Kick body mutation, choose depth

Do not implement the metadata in this slice. A separate expansion plan and
review should come before any tests, fixtures, or metadata are edited.

## Why This Is The Next Gap

- These are the only remaining captured V1.34 command-surface gaps.
- They form one coherent category: generic current-profile page mutation.
- They are already documented in the V1.34 operator command surface.
- They should remain passive scaffold metadata only until separately planned.
- They must not trigger depth prompts, selected-profile mutation, dispatch,
  MIDI, ports, or hardware behavior.

## Future Metadata Direction

A future implementation plan may introduce a passive metadata dictionary such
as:

- `CURRENT_PROFILE_PAGE_MUTATION_COMMANDS`

The future metadata should remain scaffold-only and non-executable. It should
capture command intent, mutation area, depth-selection requirement, and safety
flags as data only.

Suggested future metadata scope:

- `S`: SRC-only mutation
- `F`: Filter-only mutation
- `A`: Amp-only mutation
- `G`: Grit-only mutation
- `K`: Kick body mutation

## Expected Future Count Movement

If later implemented as passive metadata only:

- passive command count would move from 104 to 109
- captured modeled count would move from 101 to 106
- remaining captured command-surface gaps would move from 5 to 0

This would complete the currently captured V1.34 operator command surface as
passive command metadata.

## Required Future Plan Coverage

A future expansion plan should cover:

- exact passive metadata fields
- scaffold-only / non-executable safety flags
- command lookup expectations
- scaffold validation expectations
- passive list-command fixture updates
- registry report fixture updates
- expected command count movement from 104 to 109
- expected captured modeled movement from 101 to 106
- expected remaining captured gap movement from 5 to 0
- confirmation that no runtime behavior is added

## Confirmed Safety Boundaries

- no command metadata is added in this slice
- no tests are added in this slice
- no fixtures are updated in this slice
- no new CLI command
- no handler
- no dispatch
- no depth prompt execution
- no current-profile mutation execution
- no selected-profile runtime mutation
- no command execution
- no scene execution
- no MIDI
- no MIDI port opening
- no MIDI sending
- no real MIDI dependency
- no package metadata change
- no active behavior
- no hardware behavior
- no hardware validation
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Safe Next Options

- pause at this clean decision checkpoint
- create a docs-only passive metadata expansion plan for `S`, `F`, `A`, `G`,
  and `K`
- write a broader V1.34 passive metadata progress report before planning the
  final captured gap implementation
- keep all remaining gap work parked until explicitly approved

## Decision

The next passive metadata planning target is the generic current-profile page
mutation command set:

- `S`
- `F`
- `A`
- `G`
- `K`

Hardware remains off. Implementation remains parked until a separate plan,
review, and explicit approval.

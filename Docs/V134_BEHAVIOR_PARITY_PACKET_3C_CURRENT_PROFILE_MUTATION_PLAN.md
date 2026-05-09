# V1.34 Behavior Parity Packet 3C Current-Profile Mutation Plan

## Purpose

Define the next tiny mutation-depth behavior packet after accepted Packet 3A
and Packet 3B progress.

This is a documentation-only planning slice. It does not implement behavior,
add tests, wire the CLI, dispatch commands, execute commands, open ports, send
MIDI, add package metadata, mutate state, or require hardware.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this documentation slice:

- e703b57 Add Packet 3 progress checkpoint review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3A guarded numeric input behavior accepted
- Packet 3B legacy mutation-depth behavior accepted
- Packet 3 progress checkpoint reviewed and accepted
- Packet 3C current-profile mutation-depth behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Planning Sources

Use these sources for any future Packet 3C implementation:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_3_MUTATION_DEPTH_GUARDED_INPUT_PLAN.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_3_MUTATION_DEPTH_GUARDED_INPUT_PLAN_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_3_PROGRESS_CHECKPOINT.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_3_PROGRESS_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_MUTATION_DEPTH_GUARDED_INPUT_SLICE.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_MUTATION_DEPTH_GUARDED_INPUT_SLICE_REVIEW.md`
- passive command metadata in `rytm_randomizer/commands.py`
- protected V1.34 reference behavior, read-only only

## Packet Identity

Packet 3C:

- Current-Profile Page Mutation-Depth Behavior Parity

Planned command scope:

- `S`
- `F`
- `A`
- `G`
- `K`

## Packet 3C Intent

Packet 3C should add deterministic read-only intent behavior for generic
current-profile page mutation commands that require a future depth selection:

- `S`: SRC-only mutation, choose depth
- `F`: Filter-only mutation, choose depth
- `A`: Amp-only mutation, choose depth
- `G`: Grit-only mutation, choose depth
- `K`: Kick body mutation, choose depth

This packet should not model current-profile state, perform mutation, ask for
depth, dispatch to runtime handlers, execute commands, or touch hardware. It
should only describe the passive intent represented by existing metadata.

## Recommended Implementation Scope

Future implementation should support only:

- `S`
- `F`
- `A`
- `G`
- `K`

Future implementation should leave these Packet 3 keys deferred:

- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

Accepted Packet 3A guarded numeric inputs `1`, `2`, and `3` must remain
unchanged.

Accepted Packet 3B legacy single-profile mutation intents `M1`, `M2`, and
`M3` must remain unchanged.

## Existing Passive Metadata

Packet 3C should use existing passive metadata from
`CURRENT_PROFILE_PAGE_MUTATION_COMMANDS` in `rytm_randomizer/commands.py`.

Existing metadata for `S`:

- type: `mutation`
- scope: `current_profile`
- command_family: `generic_current_profile_page_mutation`
- mutation_area: `src`
- requires_depth_selection: `True`
- sends_midi: `False`
- label: `SRC-only mutation, choose depth`
- executable: `False`
- scaffold_only: `True`

Existing metadata for `F`:

- type: `mutation`
- scope: `current_profile`
- command_family: `generic_current_profile_page_mutation`
- mutation_area: `filter`
- requires_depth_selection: `True`
- sends_midi: `False`
- label: `Filter-only mutation, choose depth`
- executable: `False`
- scaffold_only: `True`

Existing metadata for `A`:

- type: `mutation`
- scope: `current_profile`
- command_family: `generic_current_profile_page_mutation`
- mutation_area: `amp`
- requires_depth_selection: `True`
- sends_midi: `False`
- label: `Amp-only mutation, choose depth`
- executable: `False`
- scaffold_only: `True`

Existing metadata for `G`:

- type: `mutation`
- scope: `current_profile`
- command_family: `generic_current_profile_page_mutation`
- mutation_area: `grit`
- requires_depth_selection: `True`
- sends_midi: `False`
- label: `Grit-only mutation, choose depth`
- executable: `False`
- scaffold_only: `True`

Existing metadata for `K`:

- type: `mutation`
- scope: `current_profile`
- command_family: `generic_current_profile_page_mutation`
- mutation_area: `kick_body`
- requires_depth_selection: `True`
- sends_midi: `False`
- label: `Kick body mutation, choose depth`
- executable: `False`
- scaffold_only: `True`

Do not invent new current-profile metadata, runtime mutation output,
selected-profile state, current profile state, machine values, pad state,
depth values, or hardware state.

## Future File Ownership

Future Packet 3C implementation should be limited to:

- `rytm_randomizer/behavior_mutation_depth.py`
- `tests/test_behavior_mutation_depth.py`

No `Scripts/closeout_check.ps1` update is expected because
`tests/test_behavior_mutation_depth.py` is already covered by:

- `=== Test: Behavior Mutation Depth ===`

## Expected Future Behavior Semantics

For `S`, `F`, `A`, `G`, and `K`, future behavior should return deterministic
read-only current-profile page mutation intent:

- accepted: `True`
- behavior family: mutation-depth current-profile page intent
- command key: matching key
- label: copied from passive metadata
- mutation area: copied from passive metadata
- scope: `current_profile`
- command family: `generic_current_profile_page_mutation`
- requires depth selection: `True`
- prompt required: `True` as recorded future intent only
- prompt available: `False`
- current-profile dependency recorded only
- state changed: `False`
- dispatches command: `False`
- executes command: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

Recommended future display lines should communicate:

- command key and label
- read-only current-profile page mutation intent
- mutation area
- current-profile dependency is recorded only
- future depth selection is required
- no active depth prompt exists now
- no current-profile state exists in this helper
- no prompt would run
- no state would change
- no command would dispatch
- no command would execute
- no MIDI would be sent
- no ports would be opened

## Expected Safe Failure Behavior

After future Packet 3C implementation:

- `S`, `F`, `A`, `G`, and `K` should no longer return
  `deferred_mutation_depth_command`
- unknown keys should still fail safely with `unknown_command`
- non-Packet-3 commands should still fail safely with
  `unsupported_mutation_depth_command`
- selected isolated pad Packet 3 keys should still fail safely with
  `deferred_mutation_depth_command`

Deferred Packet 3 keys after Packet 3C should include:

- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

## Future Test Plan

Future `tests/test_behavior_mutation_depth.py` changes should verify:

- importing `rytm_randomizer.behavior_mutation_depth` prints nothing
- existing Packet 3A behavior for `1`, `2`, and `3` remains unchanged
- existing Packet 3B behavior for `M1`, `M2`, and `M3` remains unchanged
- `S` returns deterministic read-only current-profile mutation intent
- `F` returns deterministic read-only current-profile mutation intent
- `A` returns deterministic read-only current-profile mutation intent
- `G` returns deterministic read-only current-profile mutation intent
- `K` returns deterministic read-only current-profile mutation intent
- each accepted Packet 3C result records `current_profile` scope
- each accepted Packet 3C result records
  `generic_current_profile_page_mutation` command family
- each accepted Packet 3C result records its existing metadata mutation area:
  `src`, `filter`, `amp`, `grit`, or `kick_body`
- each accepted Packet 3C result records that future depth selection is
  required
- each accepted Packet 3C result records that no active prompt is available
  now
- no current-profile state is mutated
- no prompt runs
- no command dispatches
- no command executes
- no scene executes
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- unknown keys still fail safely
- selected isolated pad Packet 3 keys still fail safely
- Packet 1 behavior remains unchanged
- Packet 2 behavior remains unchanged
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata files remain absent
- no Analog Four support is exposed
- no Pads 5-12 support is exposed
- no active command names are introduced

## Implementation Task Outline

When separately approved, implement Packet 3C in these small steps:

1. Add failing tests for `S`, `F`, `A`, `G`, and `K` accepted current-profile
   page mutation intent.
2. Run the focused behavior mutation-depth test and confirm the new tests
   fail because the keys are still deferred.
3. Extend `behavior_mutation_depth.py` to import
   `CURRENT_PROFILE_PAGE_MUTATION_COMMANDS`.
4. Add a Packet 3C supported-key tuple for only `S`, `F`, `A`, `G`, and `K`.
5. Update `DEFERRED_PACKET_3_MUTATION_DEPTH_KEYS` to leave only `PM`, `PS`,
   `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` deferred.
6. Add a helper that returns deterministic read-only current-profile page
   mutation intent using copied passive metadata.
7. Preserve Packet 3A behavior for `1`, `2`, and `3`.
8. Preserve Packet 3B behavior for `M1`, `M2`, and `M3`.
9. Preserve safe deferred behavior for selected isolated pad Packet 3 keys.
10. Run the focused behavior mutation-depth tests.
11. Run full closeout.
12. Confirm V1.34 reference diff is empty.
13. Confirm package metadata files remain absent.
14. Confirm git status shows only the intended implementation files.
15. Commit with a Packet 3C implementation message.

## Parallelization Decision

Do not parallelize Packet 3C implementation.

Reason:

- the write set is one behavior helper and one test file
- Packet 3A and Packet 3B behavior must remain stable
- Packet 3C changes share the same result shape and deferred-key list
- parallel workers would increase merge and semantic-coordination risk

Parallel work can be reconsidered for a later Packet 3D plan or for separate
documentation/reporting tasks with disjoint files.

## Explicitly Not In Scope

Packet 3C must not add:

- behavior for `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, or `PG`
- prompt/depth context runtime
- current-profile state model
- selected-profile state model
- selected-isolated-pad state model
- runtime mutation result model
- mutation execution
- command dispatch
- scene execution
- CLI wiring
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI imports
- `mido`
- `rtmidi`
- package metadata
- port discovery
- port opening
- MIDI sending
- hardware validation
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## Stop Conditions

Stop before implementation or commit if any future Packet 3C work introduces:

- scope beyond `S`, `F`, `A`, `G`, and `K`
- prompt loops or blocking input
- runtime state mutation
- current-profile state mutation
- selected-profile state mutation
- mutation execution
- CLI wiring
- command dispatch
- real MIDI imports
- package metadata files
- port opening
- MIDI sending
- V1.34 reference diff
- Analog Four scope
- Pads 5-12 scope
- uncertainty about current-profile semantics

## Next Safe Options

- review and accept this Packet 3C plan
- pause at this clean Packet 3C planning checkpoint
- create a broader Packet 3 progress checkpoint only after Packet 3C is
  reviewed or implemented

## Recommendation

Review and accept this Packet 3C plan next. If accepted, implement only `S`,
`F`, `A`, `G`, and `K` as deterministic read-only current-profile page
mutation-depth intent.

Do not implement selected isolated pad mutation-depth behavior yet.

## Decision

Packet 3C is planned only. Hardware remains off. No implementation, tests,
runtime behavior, CLI wiring, dispatch, execution, real MIDI, ports, package
metadata, active behavior, machine/profile expansion, or hardware validation
is added by this document.

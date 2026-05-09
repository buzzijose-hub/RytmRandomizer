# V1.34 Behavior Parity Packet 3B Legacy Mutation-Depth Plan

## Purpose

Define the next tiny mutation-depth behavior packet after accepted Packet 3A.

This is a documentation-only planning slice. It does not implement behavior,
add tests, wire the CLI, dispatch commands, execute commands, open ports, send
MIDI, add package metadata, mutate state, or require hardware.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this documentation slice:

- 99fcd42 Add Packet 3A mutation depth review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 mutation-depth and guarded input plan accepted
- Packet 3A guarded numeric input behavior accepted
- Packet 3B legacy mutation-depth behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Planning Sources

Use these sources for any future Packet 3B implementation:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_3_MUTATION_DEPTH_GUARDED_INPUT_PLAN.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_3_MUTATION_DEPTH_GUARDED_INPUT_PLAN_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_3A_MUTATION_DEPTH_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_MUTATION_DEPTH_GUARDED_INPUT_SLICE.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_MUTATION_DEPTH_GUARDED_INPUT_SLICE_REVIEW.md`
- passive command metadata in `rytm_randomizer/commands.py`
- protected V1.34 reference behavior, read-only only

## Packet Identity

Packet 3B:

- Legacy Single-Profile Mutation-Depth Behavior Parity

Planned command scope:

- `M1`
- `M2`
- `M3`

## Packet 3B Intent

Packet 3B should add deterministic read-only intent behavior for legacy
single-profile fixed-depth mutation commands:

- `M1`: Legacy single-profile full micro mutation
- `M2`: Legacy single-profile full groove mutation
- `M3`: Legacy single-profile full strong mutation

This packet should not model selected-profile state, perform mutation,
dispatch to runtime handlers, execute commands, prompt the operator, or touch
hardware. It should only describe the passive intent represented by the
existing metadata.

## Recommended Implementation Scope

Future implementation should support only:

- `M1`
- `M2`
- `M3`

Future implementation should leave these Packet 3 keys deferred:

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

Bare guarded numeric inputs `1`, `2`, and `3` must remain unchanged from
Packet 3A.

## Existing Passive Metadata

Packet 3B should use existing passive metadata from
`LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS` in `rytm_randomizer/commands.py`.

Existing metadata for `M1`:

- type: `mutation`
- scope: `selected_profile`
- command_family: `legacy_single_profile_mutation`
- mutation_area: `full`
- mutation_depth: `micro`
- uses_selected_profile: `True`
- sends_midi: `False`
- label: `Legacy single-profile full micro mutation`
- executable: `False`
- scaffold_only: `True`

Existing metadata for `M2`:

- type: `mutation`
- scope: `selected_profile`
- command_family: `legacy_single_profile_mutation`
- mutation_area: `full`
- mutation_depth: `groove`
- uses_selected_profile: `True`
- sends_midi: `False`
- label: `Legacy single-profile full groove mutation`
- executable: `False`
- scaffold_only: `True`

Existing metadata for `M3`:

- type: `mutation`
- scope: `selected_profile`
- command_family: `legacy_single_profile_mutation`
- mutation_area: `full`
- mutation_depth: `strong`
- uses_selected_profile: `True`
- sends_midi: `False`
- label: `Legacy single-profile full strong mutation`
- executable: `False`
- scaffold_only: `True`

Do not invent new metadata for selected profiles, runtime mutation output,
machine values, pad state, or hardware state.

## Future File Ownership

Future Packet 3B implementation should be limited to:

- `rytm_randomizer/behavior_mutation_depth.py`
- `tests/test_behavior_mutation_depth.py`

No `Scripts/closeout_check.ps1` update is expected because
`tests/test_behavior_mutation_depth.py` is already covered by:

- `=== Test: Behavior Mutation Depth ===`

## Expected Future Behavior Semantics

For `M1`, `M2`, and `M3`, future behavior should return deterministic
read-only legacy mutation intent:

- accepted: `True`
- behavior family: mutation-depth legacy single-profile intent
- command key: matching key
- label: copied from passive metadata
- mutation area: `full`
- mutation depth: copied from passive metadata
- scope: `selected_profile`
- uses selected profile: `True`
- prompt required: `False`
- prompt available: `False`
- state changed: `False`
- dispatches command: `False`
- executes command: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

Recommended future display lines should communicate:

- command key and label
- read-only legacy single-profile mutation intent
- fixed depth value
- full mutation area
- selected-profile dependency is recorded only
- no selected-profile state exists in this helper
- no prompt would run
- no state would change
- no command would dispatch
- no command would execute
- no MIDI would be sent
- no ports would be opened

## Expected Safe Failure Behavior

After future Packet 3B implementation:

- `M1`, `M2`, and `M3` should no longer return
  `deferred_mutation_depth_command`
- unknown keys should still fail safely with `unknown_command`
- non-Packet-3 commands should still fail safely with
  `unsupported_mutation_depth_command`
- deferred Packet 3 keys should still fail safely with
  `deferred_mutation_depth_command`

Deferred Packet 3 keys after Packet 3B should include:

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

## Future Test Plan

Future `tests/test_behavior_mutation_depth.py` changes should verify:

- importing `rytm_randomizer.behavior_mutation_depth` prints nothing
- existing Packet 3A behavior for `1`, `2`, and `3` remains unchanged
- `M1` returns deterministic read-only legacy mutation intent
- `M2` returns deterministic read-only legacy mutation intent
- `M3` returns deterministic read-only legacy mutation intent
- `M1` records fixed mutation depth `micro`
- `M2` records fixed mutation depth `groove`
- `M3` records fixed mutation depth `strong`
- all three record mutation area `full`
- all three record `selected_profile` scope
- all three record `uses_selected_profile` as `True`
- no prompt is required or available
- no selected-profile state is mutated
- no command dispatches
- no command executes
- no scene executes
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- unknown keys still fail safely
- remaining Packet 3 keys still fail safely
- Packet 1 behavior remains unchanged
- Packet 2 behavior remains unchanged
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata files remain absent
- no Analog Four support is exposed
- no Pads 5-12 support is exposed
- no active command names are introduced

## Implementation Task Outline

When separately approved, implement Packet 3B in these small steps:

1. Add failing tests for `M1`, `M2`, and `M3` accepted legacy mutation intent.
2. Run the focused behavior mutation-depth test and confirm the new tests fail.
3. Extend `behavior_mutation_depth.py` to recognize only `M1`, `M2`, and `M3`.
4. Copy existing passive metadata into immutable result metadata.
5. Preserve Packet 3A behavior for `1`, `2`, and `3`.
6. Preserve safe deferred behavior for the remaining Packet 3 keys.
7. Run the focused behavior mutation-depth tests.
8. Run full closeout.
9. Confirm V1.34 reference diff is empty.
10. Confirm package metadata files remain absent.
11. Confirm git status shows only the intended implementation files.
12. Commit with a Packet 3B implementation message.

## Parallelization Decision

Do not parallelize Packet 3B implementation.

Reason:

- the write set is one behavior helper and one test file
- result-shape changes must stay coordinated
- Packet 3A behavior must remain stable
- parallel workers would add coordination overhead without meaningful speedup

## Explicitly Not In Scope

Packet 3B must not add:

- behavior for `S`, `F`, `A`, `G`, or `K`
- behavior for `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, or `PG`
- prompt/depth context model
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

Stop before implementation or commit if any future Packet 3B work introduces:

- scope beyond `M1`, `M2`, and `M3`
- prompt loops or blocking input
- runtime state mutation
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
- uncertainty about the selected-profile semantics

## Next Safe Options

- review and accept this Packet 3B plan
- pause at this clean Packet 3A and Packet 3B planning checkpoint
- create a broader Packet 3 progress checkpoint

## Recommendation

Review and accept this Packet 3B plan next. If accepted, implement only
`M1`, `M2`, and `M3` as deterministic read-only legacy single-profile
mutation-depth intent.

Do not implement the rest of Packet 3 yet.

## Decision

Packet 3B is planned only. Hardware remains off. No implementation, tests,
runtime behavior, CLI wiring, dispatch, execution, real MIDI, ports, package
metadata, active behavior, machine/profile expansion, or hardware validation
is added by this document.

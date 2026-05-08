# V1.34 Legacy Single-Profile Mutation Passive Metadata Expansion Plan Review

## Purpose

Review and accept the legacy single-profile mutation passive metadata
expansion plan before any metadata, tests, or fixtures are implemented.

This is a documentation-only review gate. It does not add metadata, tests,
fixtures, runtime behavior, CLI wiring, dispatch, MIDI, ports, package
metadata, active behavior, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `f3511d4 Add legacy single-profile mutation metadata expansion plan`

Current passive command count:

- `101`

Captured V1.34 operator command entries modeled as passive command metadata:

- `98`

Remaining captured command-surface gaps:

- `8`

## Review Decision

`Docs/V134_LEGACY_SINGLE_PROFILE_MUTATION_PASSIVE_METADATA_EXPANSION_PLAN.md`
is accepted as the current implementation plan for a future passive
metadata-only slice.

The accepted target commands are:

- `M1` / Legacy single-profile full micro mutation
- `M2` / Legacy single-profile full groove mutation
- `M3` / Legacy single-profile full strong mutation

The plan remains implementation guidance only until a later approved
implementation packet.

## Accepted Future Metadata Shape

The review accepts the planned future passive dictionary:

- `LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS`

It accepts the planned metadata for `M1`:

- `type`: `mutation`
- `scope`: `selected_profile`
- `command_family`: `legacy_single_profile_mutation`
- `mutation_area`: `full`
- `mutation_depth`: `micro`
- `uses_selected_profile`: `True`
- `sends_midi`: `False`
- `label`: `Legacy single-profile full micro mutation`
- `executable`: `False`
- `v134_reference_command`: `True`
- `scaffold_only`: `True`

It accepts the planned metadata for `M2`:

- `type`: `mutation`
- `scope`: `selected_profile`
- `command_family`: `legacy_single_profile_mutation`
- `mutation_area`: `full`
- `mutation_depth`: `groove`
- `uses_selected_profile`: `True`
- `sends_midi`: `False`
- `label`: `Legacy single-profile full groove mutation`
- `executable`: `False`
- `v134_reference_command`: `True`
- `scaffold_only`: `True`

It accepts the planned metadata for `M3`:

- `type`: `mutation`
- `scope`: `selected_profile`
- `command_family`: `legacy_single_profile_mutation`
- `mutation_area`: `full`
- `mutation_depth`: `strong`
- `uses_selected_profile`: `True`
- `sends_midi`: `False`
- `label`: `Legacy single-profile full strong mutation`
- `executable`: `False`
- `v134_reference_command`: `True`
- `scaffold_only`: `True`

## Accepted Future Files

The implementation should be limited to:

- `rytm_randomizer/commands.py`
- `tests/test_scaffold.py`
- `tests/test_command_lookup.py`
- `tests/fixtures/cli_list_commands_expected.txt`
- `tests/fixtures/registry_report_expected.txt`

No closeout script update is expected because the existing test files are
already included in closeout.

## Accepted Future Count Movement

If later implemented:

- passive command count moves from `101` to `104`
- registry report command count moves from `commands: 101` to `commands: 104`
- captured modeled count moves from `98` to `101`
- remaining captured gaps move from `8` to `5`

## Required Future Implementation Method

The future implementation should use the same TDD flow as the prior passive
metadata slices:

1. Update scaffold, command lookup, and deterministic fixture expectations
   first.
2. Run targeted tests and confirm they fail because
   `LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS` does not exist yet.
3. Add the minimal passive metadata in `rytm_randomizer/commands.py`.
4. Run targeted tests until green.
5. Run full closeout.
6. Confirm V1.34 reference diff is empty.
7. Confirm package metadata remains absent/unchanged.
8. Commit the implementation files.
9. Create a matching documentation checkpoint.

## Confirmed Safety Boundaries

- No real MIDI
- No `mido`
- No MIDI port opening
- No MIDI sending
- No active execution
- No CLI active command
- No runtime dispatch
- No command execution
- No scene execution
- No selected-profile runtime mutation
- No legacy mutation execution
- No depth execution
- No selected profile persistence
- No hardware behavior
- No SysEx
- No GUI/capture
- No Analog Four support
- No Pads 5-12 support
- No machine/profile universe expansion
- No package metadata changes
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Rejected / Forbidden Next Moves

- Do not implement `M1`, `M2`, or `M3` without an approved implementation
  packet.
- Do not implement `S`, `F`, `A`, `G`, or `K` yet.
- Do not add selected-profile mutation execution.
- Do not add depth execution.
- Do not add runtime selected-profile state mutation.
- Do not add active CLI behavior.
- Do not add real MIDI or ports.
- Do not add package metadata.
- Do not turn on hardware.

## Decision

The legacy single-profile mutation passive metadata expansion plan is
accepted.

The next safe move is a bounded implementation packet for `M1`, `M2`, and
`M3`, or a pause at this clean planning checkpoint.

Implementation remains parked until explicitly approved.

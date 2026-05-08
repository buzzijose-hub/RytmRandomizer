# V1.34 Profile Selection Anchor Passive Metadata Expansion Plan Review

## Purpose

Review and accept the profile selection / anchor loading passive metadata
expansion plan before any metadata, tests, or fixtures are implemented.

This is a documentation-only review gate. It does not add metadata, tests,
fixtures, runtime behavior, CLI wiring, dispatch, MIDI, ports, package
metadata, active behavior, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `1d7a919 Add profile selection anchor metadata expansion plan`

Current passive command count:

- `99`

Captured V1.34 operator command entries modeled as passive command metadata:

- `96`

Remaining captured command-surface gaps:

- `10`

## Review Decision

`Docs/V134_PROFILE_SELECTION_ANCHOR_PASSIVE_METADATA_EXPANSION_PLAN.md` is
accepted as the current implementation plan for a future passive metadata-only
slice.

The accepted target commands are:

- `P` / select/switch profile and change Rytm machine
- `M` / load selected profile anchor

The plan remains implementation guidance only until a later approved
implementation packet.

## Accepted Future Metadata Shape

The review accepts the planned future passive dictionary:

- `PROFILE_WORKFLOW_COMMANDS`

It accepts the planned metadata for `P`:

- `type`: `selection`
- `scope`: `profile_machine`
- `command_family`: `profile_workflow`
- `selects_profile`: `True`
- `machine_change_intent`: `True`
- `sends_midi`: `False`
- `label`: `select/switch profile and change Rytm machine`
- `executable`: `False`
- `v134_reference_command`: `True`
- `scaffold_only`: `True`

It accepts the planned metadata for `M`:

- `type`: `anchor_load`
- `scope`: `selected_profile`
- `command_family`: `profile_workflow`
- `uses_selected_profile`: `True`
- `anchor_load_intent`: `True`
- `sends_midi`: `False`
- `label`: `load selected profile anchor`
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

- passive command count moves from `99` to `101`
- registry report command count moves from `commands: 99` to `commands: 101`
- captured modeled count moves from `96` to `98`
- remaining captured gaps move from `10` to `8`

## Required Future Implementation Method

The future implementation should use the same TDD flow as the prior passive
metadata slices:

1. Update scaffold, command lookup, and deterministic fixture expectations
   first.
2. Run targeted tests and confirm they fail because `PROFILE_WORKFLOW_COMMANDS`
   does not exist yet.
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
- No profile runtime state mutation
- No machine change execution
- No anchor loading execution
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

- Do not implement `P` or `M` without an approved implementation packet.
- Do not implement `M1`, `M2`, or `M3` yet.
- Do not implement `S`, `F`, `A`, `G`, or `K` yet.
- Do not add runtime profile switching.
- Do not add machine change execution.
- Do not add anchor loading execution.
- Do not add active CLI behavior.
- Do not add real MIDI or ports.
- Do not add package metadata.
- Do not turn on hardware.

## Decision

The profile selection / anchor loading passive metadata expansion plan is
accepted.

The next safe move is a bounded implementation packet for `P` and `M`, or a
pause at this clean planning checkpoint.

Implementation remains parked until explicitly approved.

# V1.34 Legacy Single-Profile Mutation Passive Metadata Expansion Plan

## Purpose

Define a future passive metadata-only expansion for legacy single-profile
mutation commands from the captured V1.34 command surface.

This is a planning document only. It does not add metadata, tests, fixtures,
runtime behavior, CLI wiring, dispatch, MIDI, ports, package metadata, active
behavior, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `b0abf1a Add legacy single-profile mutation metadata decision note`

Current passive command count:

- `101`

Captured V1.34 operator command entries modeled as passive command metadata:

- `98`

Remaining captured command-surface gaps:

- `8`

## Target Commands

The future implementation target is:

- `M1` / Legacy single-profile full micro mutation
- `M2` / Legacy single-profile full groove mutation
- `M3` / Legacy single-profile full strong mutation

## Proposed Future Metadata Shape

Add a passive metadata dictionary in `rytm_randomizer/commands.py`:

```python
LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS = {
    "M1": {
        "type": "mutation",
        "scope": "selected_profile",
        "command_family": "legacy_single_profile_mutation",
        "mutation_area": "full",
        "mutation_depth": "micro",
        "uses_selected_profile": True,
        "sends_midi": False,
        "label": "Legacy single-profile full micro mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "M2": {
        "type": "mutation",
        "scope": "selected_profile",
        "command_family": "legacy_single_profile_mutation",
        "mutation_area": "full",
        "mutation_depth": "groove",
        "uses_selected_profile": True,
        "sends_midi": False,
        "label": "Legacy single-profile full groove mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "M3": {
        "type": "mutation",
        "scope": "selected_profile",
        "command_family": "legacy_single_profile_mutation",
        "mutation_area": "full",
        "mutation_depth": "strong",
        "uses_selected_profile": True,
        "sends_midi": False,
        "label": "Legacy single-profile full strong mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}
```

Then merge it into `COMMANDS` after profile workflow metadata and before
group/pad command families:

```python
COMMANDS = {
    ...
    **ISOLATED_PAD_MUTATION_COMMANDS,
    **PROFILE_WORKFLOW_COMMANDS,
    **LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS,
    **GROUP_COMMANDS,
    ...
}
```

The exact placement is for deterministic organization only. It must not add
handlers or execution behavior.

## Expected Future Count Movement

If implemented:

- passive command count moves from `101` to `104`
- registry report command count moves from `commands: 101` to `commands: 104`
- captured modeled count moves from `98` to `101`
- remaining captured gaps move from `8` to `5`

## Expected Future Files To Update

Implementation should be limited to:

- `rytm_randomizer/commands.py`
- `tests/test_scaffold.py`
- `tests/test_command_lookup.py`
- `tests/fixtures/cli_list_commands_expected.txt`
- `tests/fixtures/registry_report_expected.txt`

No new test file is expected. `Scripts/closeout_check.ps1` should not need an
update because the existing test files are already in closeout.

## Expected Future Scaffold Tests

Extend `tests/test_scaffold.py` to import
`LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS` and add coverage equivalent to:

```python
def test_legacy_single_profile_mutation_commands_match_v134_metadata_only_set():
    expected = {"M1", "M2", "M3"}

    assert set(LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_legacy_single_profile_mutation_commands_are_scaffold_only_and_not_executable():
    for metadata in LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS.values():
        assert_sends_no_midi(metadata)
        assert_protocol_command_metadata(metadata)
        assert metadata["scope"] == "selected_profile"
        assert metadata["command_family"] == "legacy_single_profile_mutation"
        assert metadata["mutation_area"] == "full"
        assert metadata["uses_selected_profile"] is True


def test_representative_legacy_single_profile_mutation_labels_match_v134_intent():
    assert LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS["M1"] == {
        "type": "mutation",
        "scope": "selected_profile",
        "command_family": "legacy_single_profile_mutation",
        "mutation_area": "full",
        "mutation_depth": "micro",
        "uses_selected_profile": True,
        "sends_midi": False,
        "label": "Legacy single-profile full micro mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS["M2"]["mutation_depth"] == "groove"
    assert LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS["M3"]["mutation_depth"] == "strong"
```

## Expected Future Command Lookup Tests

Extend `tests/test_command_lookup.py` with coverage equivalent to:

```python
def test_known_legacy_single_profile_mutation_command_lookups_return_existing_metadata():
    expected = {
        "M1": ("micro", "Legacy single-profile full micro mutation"),
        "M2": ("groove", "Legacy single-profile full groove mutation"),
        "M3": ("strong", "Legacy single-profile full strong mutation"),
    }

    for command_key, (mutation_depth, label) in expected.items():
        report = describe_command(command_key)

        assert_passive_command_report(report, command_key)
        assert report["type"] == "mutation"
        assert report["scope"] == "selected_profile"
        assert report["label"] == label
        assert report["metadata"] == COMMANDS[command_key]
        assert report["metadata"]["command_family"] == "legacy_single_profile_mutation"
        assert report["metadata"]["mutation_area"] == "full"
        assert report["metadata"]["mutation_depth"] == mutation_depth
        assert report["metadata"]["uses_selected_profile"] is True
```

## Expected Future Fixture Updates

Update `tests/fixtures/cli_list_commands_expected.txt`:

- change `Count: 101` to `Count: 104`
- add `- M1: Legacy single-profile full micro mutation`
- add `- M2: Legacy single-profile full groove mutation`
- add `- M3: Legacy single-profile full strong mutation`

Update `tests/fixtures/registry_report_expected.txt`:

- change `- commands: 101` to `- commands: 104`

## Required TDD Flow For Future Implementation

1. Write the scaffold, command lookup, and fixture expectations first.
2. Run the targeted tests and confirm they fail because
   `LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS` is not implemented yet.
3. Add the minimal passive metadata in `rytm_randomizer/commands.py`.
4. Run targeted tests until green.
5. Run full closeout.
6. Confirm V1.34 reference diff is empty.
7. Confirm package metadata remains absent/unchanged.
8. Commit only the implementation files.
9. Create a matching docs checkpoint.

## Safety Boundaries

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

## Non-Goals

- Do not implement `M1`, `M2`, or `M3` in this planning slice.
- Do not implement `S`, `F`, `A`, `G`, or `K`.
- Do not add selected-profile mutation execution.
- Do not add depth execution.
- Do not add runtime selected-profile state mutation.
- Do not add active CLI behavior.
- Do not add real MIDI or ports.
- Do not turn on hardware.

## Next Recommended Task

Review and accept this plan. If accepted, a later implementation packet may
add the passive metadata for `M1`, `M2`, and `M3` using the TDD flow above.

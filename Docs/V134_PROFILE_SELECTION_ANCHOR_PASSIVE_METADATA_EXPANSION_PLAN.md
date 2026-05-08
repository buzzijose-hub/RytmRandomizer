# V1.34 Profile Selection Anchor Passive Metadata Expansion Plan

## Purpose

Define a future passive metadata-only expansion for profile selection and
anchor loading commands from the captured V1.34 command surface.

This is a planning document only. It does not add metadata, tests, fixtures,
runtime behavior, CLI wiring, dispatch, MIDI, ports, package metadata, active
behavior, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `b3fe516 Add profile selection anchor metadata decision note`

Current passive command count:

- `99`

Captured V1.34 operator command entries modeled as passive command metadata:

- `96`

Remaining captured command-surface gaps:

- `10`

## Target Commands

The future implementation target is:

- `P` / select/switch profile and change Rytm machine
- `M` / load selected profile anchor

## Proposed Future Metadata Shape

Add a passive metadata dictionary in `rytm_randomizer/commands.py`:

```python
PROFILE_WORKFLOW_COMMANDS = {
    "P": {
        "type": "selection",
        "scope": "profile_machine",
        "command_family": "profile_workflow",
        "selects_profile": True,
        "machine_change_intent": True,
        "sends_midi": False,
        "label": "select/switch profile and change Rytm machine",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "M": {
        "type": "anchor_load",
        "scope": "selected_profile",
        "command_family": "profile_workflow",
        "uses_selected_profile": True,
        "anchor_load_intent": True,
        "sends_midi": False,
        "label": "load selected profile anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}
```

Then merge it into `COMMANDS` after state/isolated utility metadata and before
group/pad command families:

```python
COMMANDS = {
    ...
    **STATE_UTILITY_COMMANDS,
    **ISOLATED_PAD_UTILITY_COMMANDS,
    **ISOLATED_PAD_MUTATION_COMMANDS,
    **PROFILE_WORKFLOW_COMMANDS,
    **GROUP_COMMANDS,
    ...
}
```

The exact placement is for deterministic organization only. It must not add
handlers or execution behavior.

## Expected Future Count Movement

If implemented:

- passive command count moves from `99` to `101`
- registry report command count moves from `commands: 99` to `commands: 101`
- captured modeled count moves from `96` to `98`
- remaining captured gaps move from `10` to `8`

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

Extend `tests/test_scaffold.py` to import `PROFILE_WORKFLOW_COMMANDS` and add
coverage equivalent to:

```python
def test_profile_workflow_commands_match_v134_metadata_only_set():
    expected = {"P", "M"}

    assert set(PROFILE_WORKFLOW_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_profile_workflow_commands_are_scaffold_only_and_not_executable():
    for metadata in PROFILE_WORKFLOW_COMMANDS.values():
        assert_sends_no_midi(metadata)
        assert_protocol_command_metadata(metadata)
        assert metadata["command_family"] == "profile_workflow"


def test_representative_profile_workflow_labels_match_v134_intent():
    assert PROFILE_WORKFLOW_COMMANDS["P"] == {
        "type": "selection",
        "scope": "profile_machine",
        "command_family": "profile_workflow",
        "selects_profile": True,
        "machine_change_intent": True,
        "sends_midi": False,
        "label": "select/switch profile and change Rytm machine",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert PROFILE_WORKFLOW_COMMANDS["M"] == {
        "type": "anchor_load",
        "scope": "selected_profile",
        "command_family": "profile_workflow",
        "uses_selected_profile": True,
        "anchor_load_intent": True,
        "sends_midi": False,
        "label": "load selected profile anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
```

## Expected Future Command Lookup Tests

Extend `tests/test_command_lookup.py` with coverage equivalent to:

```python
def test_known_profile_workflow_command_lookups_return_existing_metadata():
    expected = {
        "P": (
            "selection",
            "profile_machine",
            "select/switch profile and change Rytm machine",
        ),
        "M": (
            "anchor_load",
            "selected_profile",
            "load selected profile anchor",
        ),
    }

    for command_key, (command_type, scope, label) in expected.items():
        report = describe_command(command_key)

        assert_passive_command_report(report, command_key)
        assert report["type"] == command_type
        assert report["scope"] == scope
        assert report["label"] == label
        assert report["metadata"] == COMMANDS[command_key]
        assert report["metadata"]["command_family"] == "profile_workflow"
```

## Expected Future Fixture Updates

Update `tests/fixtures/cli_list_commands_expected.txt`:

- change `Count: 99` to `Count: 101`
- add `- M: load selected profile anchor`
- add `- P: select/switch profile and change Rytm machine`

Update `tests/fixtures/registry_report_expected.txt`:

- change `- commands: 99` to `- commands: 101`

## Required TDD Flow For Future Implementation

1. Write the scaffold, command lookup, and fixture expectations first.
2. Run the targeted tests and confirm they fail because `P` and `M` metadata
   is not implemented yet.
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

## Non-Goals

- Do not implement `P` or `M` in this planning slice.
- Do not implement `M1`, `M2`, or `M3`.
- Do not implement `S`, `F`, `A`, `G`, or `K`.
- Do not add runtime profile switching.
- Do not add machine change execution.
- Do not add anchor loading execution.
- Do not add active CLI behavior.
- Do not add real MIDI or ports.
- Do not turn on hardware.

## Next Recommended Task

Review and accept this plan. If accepted, a later implementation packet may
add the passive metadata for `P` and `M` using the TDD flow above.

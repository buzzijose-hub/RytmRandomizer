# B E W U Passive Metadata Expansion Plan

> For future implementation workers: this is a planning document only. Do not
> edit command metadata, tests, CLI fixtures, package metadata, or runtime code
> until this plan is separately reviewed and explicitly approved for
> implementation.

**Goal:** Define the exact future passive/scaffold-only metadata expansion for
the accepted next V1.34 registry gap category: `B`, `E`, `W`, and `U`.

**Architecture:** Add four anchor/state utility commands as inert passive
metadata inside the existing command registry flow. The commands should become
visible through existing passive list/search/inspect/preview/report paths only
because they are part of `COMMANDS`, not because any new CLI behavior is
added.

**Tech Stack:** Existing Python metadata dictionaries, existing passive
registry helpers, existing fixture-backed CLI tests, and the existing closeout
suite.

---

## 1. Purpose

Plan a future metadata-only expansion for:

- `B` / back to current anchor
- `E` / commit current state as new anchor
- `W` / waveform exploration only
- `U` / undo previous script-generated state

This document does not implement the expansion.

This document does not edit metadata.

This document does not add tests.

This document does not add CLI commands.

This document does not add runtime behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 4f7d519 Add next passive metadata gap decision note

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review accepted
- `T`, `C`, and `Q` implemented as passive scaffold-only metadata
- next passive metadata gap decision selects `B`, `E`, `W`, and `U`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Scope

Future implementation scope:

- add passive metadata for `B`
- add passive metadata for `E`
- add passive metadata for `W`
- add passive metadata for `U`
- keep all four scaffold-only and non-executable
- expose them through existing passive registry surfaces
- update tests and fixtures that naturally reflect command count/list changes

Out of scope:

- active anchor loading
- active anchor committing
- active undo behavior
- waveform exploration execution
- isolated single-pad mutation metadata
- profile selection metadata
- legacy mutation metadata
- generic current-profile page mutation metadata
- active CLI behavior
- runtime dispatch
- MIDI sending
- port opening
- hardware behavior

## 4. Proposed Metadata Location

Future implementation should modify:

- `rytm_randomizer/commands.py`

Recommended shape:

- add a new `STATE_UTILITY_COMMANDS` dictionary near the existing passive
  command category dictionaries
- merge `STATE_UTILITY_COMMANDS` into `COMMANDS`
- keep the commands metadata-only and non-executable

Do not add a new module for this tiny slice.

Do not add handlers.

Do not add callbacks.

Do not add dispatch wiring.

Do not connect these commands to runtime state mutation.

## 5. Proposed Exact Metadata

Future metadata should be:

```python
STATE_UTILITY_COMMANDS = {
    "B": {
        "type": "anchor_state",
        "scope": "current_anchor",
        "sends_midi": False,
        "label": "back to current anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "E": {
        "type": "anchor_state",
        "scope": "current_state_anchor",
        "sends_midi": False,
        "label": "commit current state as new anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "W": {
        "type": "exploration",
        "scope": "waveform",
        "sends_midi": False,
        "label": "waveform exploration only",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "U": {
        "type": "state_history",
        "scope": "script_generated_state",
        "sends_midi": False,
        "label": "undo previous script-generated state",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}
```

Future `COMMANDS` merge should include:

```python
    **STATE_UTILITY_COMMANDS,
```

Place it after `UTILITY_COMMANDS` and before group/pad command categories
unless there is a strong local reason to choose another order.

## 6. Expected Passive Surface Changes

After a future implementation, these command keys should exist in `COMMANDS`:

- `B`
- `E`
- `W`
- `U`

Expected passive command count:

- current: 85
- after future implementation: 89

Expected captured V1.34 operator entries modeled as passive command metadata:

- current: 82
- after future implementation: 86

Expected captured V1.34 operator entries still not modeled as passive command
metadata:

- current: 24
- after future implementation: 20

Expected passive registry report command count:

- current: `commands: 85`
- after future implementation: `commands: 89`

Expected passive CLI list changes:

- `B` appears before `BA`
- `E` appears after `D` and before `FG`
- `U` appears after `T` and before `V`
- `W` appears after `V` and before `X`

These changes should appear only because existing passive list/report paths
read from `COMMANDS`.

No new top-level CLI command should be added.

## 7. Future Files To Modify

Future implementation files:

- `rytm_randomizer/commands.py`
- `tests/test_scaffold.py`
- `tests/test_command_lookup.py`
- `tests/fixtures/cli_list_commands_expected.txt`
- `tests/fixtures/registry_report_expected.txt`

Possible future fixture updates if command search behavior is explicitly
tested:

- `tests/fixtures/cli_search_commands_known_expected.txt`

Do not update `Scripts/closeout_check.ps1` because the relevant tests are
already included in closeout.

Do not edit `rytm_hybrid_randomizer_v134.py`.

## 8. Future Test Plan

### Task 1: Scaffold Metadata

Files:

- Modify: `rytm_randomizer/commands.py`
- Modify: `tests/test_scaffold.py`

Future test assertions:

```python
from rytm_randomizer.commands import STATE_UTILITY_COMMANDS


def test_state_utility_commands_match_v134_metadata_only_set():
    expected = {"B", "E", "W", "U"}

    assert set(STATE_UTILITY_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_state_utility_commands_are_scaffold_only_and_not_executable():
    for metadata in STATE_UTILITY_COMMANDS.values():
        assert_sends_no_midi(metadata)
        assert_protocol_command_metadata(metadata)


def test_representative_state_utility_command_labels_match_v134_intent():
    assert STATE_UTILITY_COMMANDS["B"] == {
        "type": "anchor_state",
        "scope": "current_anchor",
        "sends_midi": False,
        "label": "back to current anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert STATE_UTILITY_COMMANDS["E"]["label"] == (
        "commit current state as new anchor"
    )
    assert STATE_UTILITY_COMMANDS["W"]["label"] == "waveform exploration only"
    assert STATE_UTILITY_COMMANDS["U"]["label"] == (
        "undo previous script-generated state"
    )
```

Expected command:

```powershell
python -m pytest tests/test_scaffold.py -q
```

Expected result after implementation:

- pass

### Task 2: Passive Command Lookup

Files:

- Modify: `tests/test_command_lookup.py`

Future test assertions:

```python
def test_known_state_utility_command_lookups_return_existing_metadata():
    expected = {
        "B": ("anchor_state", "current_anchor", "back to current anchor"),
        "E": (
            "anchor_state",
            "current_state_anchor",
            "commit current state as new anchor",
        ),
        "W": ("exploration", "waveform", "waveform exploration only"),
        "U": (
            "state_history",
            "script_generated_state",
            "undo previous script-generated state",
        ),
    }

    for command_key, (command_type, scope, label) in expected.items():
        report = describe_command(command_key)

        assert_passive_command_report(report, command_key)
        assert report["type"] == command_type
        assert report["scope"] == scope
        assert report["label"] == label
        assert report["metadata"] == COMMANDS[command_key]
```

Expected command:

```powershell
python -m pytest tests/test_command_lookup.py -q
```

Expected result after implementation:

- pass

### Task 3: Fixture Updates

Files:

- Modify: `tests/fixtures/cli_list_commands_expected.txt`
- Modify: `tests/fixtures/registry_report_expected.txt`

Expected fixture changes:

- passive CLI command count moves from `Count: 85` to `Count: 89`
- passive registry report command count moves from `commands: 85` to
  `commands: 89`
- passive CLI list output includes:
  - `- B: back to current anchor`
  - `- E: commit current state as new anchor`
  - `- U: undo previous script-generated state`
  - `- W: waveform exploration only`

Expected command:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected result after implementation:

- pass

## 9. Import And Runtime Safety

Future implementation must preserve:

- importing `rytm_randomizer.commands` prints nothing
- importing `rytm_randomizer.cli` prints nothing
- passive CLI commands remain read-only
- no handlers are added
- no callbacks are added
- no dispatch is added
- no command execution is added
- no runtime state mutation is added
- no files are written at runtime
- no hardware is required

## 10. Safety Boundaries

Future implementation must add no:

- real MIDI
- `mido`
- MIDI port opening
- MIDI sending
- active execution
- new CLI command
- CLI wiring to active behavior
- dispatch
- command execution
- scene execution
- hardware behavior
- hardware mutation
- hardware detection
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- profile `"4"` implementation
- package metadata
- dependency selection
- hardware validation

`rytm_hybrid_randomizer_v134.py` must remain untouched.

Analog Rytm MKII must remain off.

Analog Four MKII must remain off.

## 11. Closeout For Future Implementation

After future implementation, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected results:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- git status shows only the intended implementation files before commit
- git status is clean after commit

## 12. Review Gate

This plan must be reviewed and accepted before implementation.

The review should confirm:

- `STATE_UTILITY_COMMANDS` is the accepted future metadata dictionary
- `B`, `E`, `W`, and `U` are the only future commands in scope
- expected command count movement is 85 to 89
- expected captured modeled count movement is 82 to 86
- expected remaining captured gap movement is 24 to 20
- tests and fixtures remain existing-file updates only
- no closeout script update is expected
- no runtime behavior is authorized
- no real MIDI, ports, active behavior, or hardware behavior is authorized

## 13. Next Recommended Task

Create a documentation-only review gate for this plan.

Do not implement metadata until that review is committed and implementation is
explicitly requested.

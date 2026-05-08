# L PZ Passive Metadata Expansion Plan

> For future implementation workers: this is a planning document only. Do not
> edit command metadata, tests, CLI fixtures, package metadata, or runtime code
> until this plan is separately reviewed and explicitly approved for
> implementation.

**Goal:** Define the exact future passive/scaffold-only metadata expansion for
the accepted next V1.34 registry gap category: `L` and `PZ`.

**Architecture:** Add two isolated single-pad utility commands as inert passive
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

- `L` / select isolated single-pad mutation target, default Pad 3
- `PZ` / return selected isolated pad to anchor only

This document does not implement the expansion.

This document does not edit metadata.

This document does not add tests.

This document does not add CLI commands.

This document does not add runtime behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 5dd459b Add L PZ next passive metadata gap decision note

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review accepted
- `T`, `C`, and `Q` implemented as passive scaffold-only metadata
- `B`, `E`, `W`, and `U` implemented as passive scaffold-only metadata
- next passive metadata gap decision selects `L` and `PZ`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Scope

Future implementation scope:

- add passive metadata for `L`
- add passive metadata for `PZ`
- keep both commands scaffold-only and non-executable
- expose both through existing passive registry surfaces
- update tests and fixtures that naturally reflect command count/list changes

Out of scope:

- selected-pad runtime state mutation
- isolated-pad mutation execution
- selected-pad anchor return execution
- isolated single-pad mutation commands `PM`, `PS`, `PF`, `PA`, `PL`, `PO`,
  `PB`, and `PG`
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

- add a new `ISOLATED_PAD_UTILITY_COMMANDS` dictionary near the existing
  passive command category dictionaries
- merge `ISOLATED_PAD_UTILITY_COMMANDS` into `COMMANDS`
- keep both commands metadata-only and non-executable

Do not add a new module for this tiny slice.

Do not add handlers.

Do not add callbacks.

Do not add dispatch wiring.

Do not connect these commands to selected-pad runtime state.

Do not connect `PZ` to active anchor return behavior.

## 5. Proposed Exact Metadata

Future metadata should be:

```python
ISOLATED_PAD_UTILITY_COMMANDS = {
    "L": {
        "type": "selection",
        "scope": "isolated_pad_target",
        "sends_midi": False,
        "label": "select isolated single-pad mutation target, default Pad 3",
        "default_pad": 3,
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PZ": {
        "type": "anchor_return",
        "scope": "selected_isolated_pad",
        "sends_midi": False,
        "label": "return selected isolated pad to anchor only",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}
```

Future `COMMANDS` merge should include:

```python
    **ISOLATED_PAD_UTILITY_COMMANDS,
```

Place it after `STATE_UTILITY_COMMANDS` and before group/pad command
categories unless there is a strong local reason to choose another order.

## 6. Expected Passive Surface Changes

After a future implementation, these command keys should exist in `COMMANDS`:

- `L`
- `PZ`

Expected passive command count:

- current: 89
- after future implementation: 91

Expected captured V1.34 operator entries modeled as passive command metadata:

- current: 86
- after future implementation: 88

Expected captured V1.34 operator entries still not modeled as passive command
metadata:

- current: 20
- after future implementation: 18

Expected passive registry report command count:

- current: `commands: 89`
- after future implementation: `commands: 91`

Expected passive CLI list changes:

- `L` appears after `J` and before `N`
- `PZ` appears after `PX` and before `Q`

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
from rytm_randomizer.commands import ISOLATED_PAD_UTILITY_COMMANDS


def test_isolated_pad_utility_commands_match_v134_metadata_only_set():
    expected = {"L", "PZ"}

    assert set(ISOLATED_PAD_UTILITY_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_isolated_pad_utility_commands_are_scaffold_only_and_not_executable():
    for metadata in ISOLATED_PAD_UTILITY_COMMANDS.values():
        assert_sends_no_midi(metadata)
        assert_protocol_command_metadata(metadata)


def test_representative_isolated_pad_utility_labels_match_v134_intent():
    assert ISOLATED_PAD_UTILITY_COMMANDS["L"] == {
        "type": "selection",
        "scope": "isolated_pad_target",
        "sends_midi": False,
        "label": "select isolated single-pad mutation target, default Pad 3",
        "default_pad": 3,
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert ISOLATED_PAD_UTILITY_COMMANDS["PZ"] == {
        "type": "anchor_return",
        "scope": "selected_isolated_pad",
        "sends_midi": False,
        "label": "return selected isolated pad to anchor only",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
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
def test_known_isolated_pad_utility_command_lookups_return_existing_metadata():
    expected = {
        "L": (
            "selection",
            "isolated_pad_target",
            "select isolated single-pad mutation target, default Pad 3",
        ),
        "PZ": (
            "anchor_return",
            "selected_isolated_pad",
            "return selected isolated pad to anchor only",
        ),
    }

    for command_key, (command_type, scope, label) in expected.items():
        report = describe_command(command_key)

        assert_passive_command_report(report, command_key)
        assert report["type"] == command_type
        assert report["scope"] == scope
        assert report["label"] == label
        assert report["metadata"] == COMMANDS[command_key]

    assert describe_command("L")["metadata"]["default_pad"] == 3
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

- passive CLI command count moves from `Count: 89` to `Count: 91`
- passive registry report command count moves from `commands: 89` to
  `commands: 91`
- passive CLI list output includes:
  - `- L: select isolated single-pad mutation target, default Pad 3`
  - `- PZ: return selected isolated pad to anchor only`

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
- no selected-pad runtime target is changed
- no anchor return is executed
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
- selected-pad runtime state mutation
- isolated-pad mutation execution
- anchor return execution
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
- git status shows only the approved implementation files before commit
- git status is clean after commit

## 12. Review Gate

This plan must be reviewed and accepted before implementation.

The review should confirm:

- `ISOLATED_PAD_UTILITY_COMMANDS` is the accepted future metadata dictionary
- `L` and `PZ` are the only future commands in scope
- expected command count movement is 89 to 91
- expected captured modeled count movement is 86 to 88
- expected remaining captured gap movement is 20 to 18
- tests and fixtures remain existing-file updates only
- no closeout script update is expected
- no runtime behavior is authorized
- no selected-pad runtime state mutation is authorized
- no active anchor return is authorized
- no real MIDI, ports, active behavior, or hardware behavior is authorized

## 13. Next Recommended Task

Create a documentation-only review gate for this plan.

Do not implement metadata until that review is committed and implementation is
explicitly requested.

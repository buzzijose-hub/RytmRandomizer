# Isolated Pad Mutation Passive Metadata Expansion Plan

> For future implementation workers: this is a planning document only. Do not
> edit command metadata, tests, CLI fixtures, package metadata, or runtime code
> until this plan is separately reviewed and explicitly approved for
> implementation.

**Goal:** Define the exact future passive/scaffold-only metadata expansion for
the accepted V1.34 isolated single-pad mutation gap category:
`PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG`.

**Architecture:** Add eight selected isolated-pad mutation commands as inert
passive metadata inside the existing command registry flow. The commands should
become visible through existing passive list/search/inspect/preview/report
paths only because they are part of `COMMANDS`, not because any new CLI
behavior is added.

**Tech Stack:** Existing Python metadata dictionaries, existing passive
registry helpers, existing fixture-backed CLI tests, and the existing closeout
suite.

---

## 1. Purpose

Plan a future metadata-only expansion for:

- `PM` / mutate selected isolated pad only using its group default zone/depth
- `PS` / mutate selected isolated pad SRC only, choose depth
- `PF` / mutate selected isolated pad Filter only, choose depth
- `PA` / mutate selected isolated pad Amp only, choose depth
- `PL` / mutate selected isolated pad LFO only, choose depth
- `PO` / mutate selected isolated pad Morph only, choose depth
- `PB` / mutate selected isolated pad Body only, choose depth
- `PG` / mutate selected isolated pad Grit only, choose depth

This document does not implement the expansion.

This document does not edit metadata.

This document does not add tests.

This document does not add CLI commands.

This document does not add runtime behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 2c095a7 Add isolated pad mutation metadata decision note

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review accepted
- `T`, `C`, and `Q` implemented as passive scaffold-only metadata
- `B`, `E`, `W`, and `U` implemented as passive scaffold-only metadata
- `L` and `PZ` implemented as passive scaffold-only metadata
- next passive metadata gap decision selects isolated single-pad mutation
  metadata

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Scope

Future implementation scope:

- add passive metadata for `PM`
- add passive metadata for `PS`
- add passive metadata for `PF`
- add passive metadata for `PA`
- add passive metadata for `PL`
- add passive metadata for `PO`
- add passive metadata for `PB`
- add passive metadata for `PG`
- keep all eight commands scaffold-only and non-executable
- expose all eight through existing passive registry surfaces
- update tests and fixtures that naturally reflect command count/list changes

Out of scope:

- selected-pad runtime state mutation
- isolated-pad mutation execution
- mutation depth prompts
- mutation depth selection behavior
- page-specific mutation behavior
- selected-pad anchor return execution
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

- add a new `ISOLATED_PAD_MUTATION_COMMANDS` dictionary near the existing
  passive isolated-pad command category dictionaries
- merge `ISOLATED_PAD_MUTATION_COMMANDS` into `COMMANDS`
- keep all eight commands metadata-only and non-executable

Do not add a new module for this tiny slice.

Do not add handlers.

Do not add callbacks.

Do not add dispatch wiring.

Do not connect these commands to selected-pad runtime state.

Do not connect these commands to active mutation behavior.

## 5. Proposed Exact Metadata

Future metadata should be:

```python
ISOLATED_PAD_MUTATION_COMMANDS = {
    "PM": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "full",
        "uses_group_default_zone_depth": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad only using its group default zone/depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PS": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "src",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad SRC only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PF": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "filter",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Filter only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PA": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "amp",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Amp only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PL": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "lfo",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad LFO only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PO": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "morph",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Morph only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PB": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "body",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Body only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PG": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "grit",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Grit only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}
```

Future `COMMANDS` merge should include:

```python
    **ISOLATED_PAD_MUTATION_COMMANDS,
```

Place it after `ISOLATED_PAD_UTILITY_COMMANDS` and before `GROUP_COMMANDS`
unless there is a strong local reason to choose another order.

## 6. Expected Passive Surface Changes

After a future implementation, these command keys should exist in `COMMANDS`:

- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

Expected passive command count:

- current: 91
- after future implementation: 99

Expected captured V1.34 operator entries modeled as passive command metadata:

- current: 88
- after future implementation: 96

Expected captured V1.34 operator entries still not modeled as passive command
metadata:

- current: 18
- after future implementation: 10

Expected passive registry report command count:

- current: `commands: 91`
- after future implementation: `commands: 99`

Expected passive CLI list changes, using the existing sorted key order:

- `PA` appears after `P4X` and before `PB`
- `PB` appears after `PA` and before `PBH`
- `PF` appears after `PD` and before `PG`
- `PG` appears after `PF` and before `PL`
- `PL` appears after `PG` and before `PM`
- `PM` appears after `PL` and before `PO`
- `PO` appears after `PM` and before `PR`
- `PS` appears after `PR` and before `PT`

No new top-level CLI command should be added.

## 7. Future Files To Modify

Future implementation files:

- `rytm_randomizer/commands.py`
- `tests/test_scaffold.py`
- `tests/test_command_lookup.py`
- `tests/fixtures/cli_list_commands_expected.txt`
- `tests/fixtures/registry_report_expected.txt`

No `tests/test_cli.py` change is expected unless the future implementation
adds a new explicit assertion around the existing passive list output.

No search fixture update is expected because the current deterministic
`search-commands` fixture uses the `guarded` query, which is not affected by
these labels.

Do not update `Scripts/closeout_check.ps1` because the relevant tests are
already included in closeout.

Do not edit `rytm_hybrid_randomizer_v134.py`.

## 8. Future Test Plan

### Task 1: Scaffold Metadata

Files:

- Modify: `rytm_randomizer/commands.py`
- Modify: `tests/test_scaffold.py`

Future import update:

```python
from rytm_randomizer.commands import (
    COMMANDS,
    FORBIDDEN_ACTIONS,
    GROUP_COMMANDS,
    ISOLATED_PAD_MUTATION_COMMANDS,
    ISOLATED_PAD_UTILITY_COMMANDS,
    MAIN_PROMPT_DEPTH_GUARDRAIL,
    MENU_COMMANDS,
    PAD1_COMMANDS,
    PAD2_COMMANDS,
    PAD3_COMMANDS,
    PAD4_COMMANDS,
    STATE_UTILITY_COMMANDS,
    UTILITY_COMMANDS,
    is_guarded_main_prompt_depth,
)
```

Future test assertions:

```python
def test_isolated_pad_mutation_commands_match_v134_metadata_only_set():
    expected = {"PM", "PS", "PF", "PA", "PL", "PO", "PB", "PG"}

    assert set(ISOLATED_PAD_MUTATION_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_isolated_pad_mutation_commands_are_scaffold_only_and_not_executable():
    for metadata in ISOLATED_PAD_MUTATION_COMMANDS.values():
        assert_sends_no_midi(metadata)
        assert_protocol_command_metadata(metadata)
        assert metadata["scope"] == "selected_isolated_pad"
        assert metadata["command_family"] == "isolated_pad_mutation"


def test_representative_isolated_pad_mutation_labels_match_v134_intent():
    assert ISOLATED_PAD_MUTATION_COMMANDS["PM"] == {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "full",
        "uses_group_default_zone_depth": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad only using its group default zone/depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert ISOLATED_PAD_MUTATION_COMMANDS["PS"] == {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "src",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad SRC only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert ISOLATED_PAD_MUTATION_COMMANDS["PF"]["mutation_area"] == "filter"
    assert ISOLATED_PAD_MUTATION_COMMANDS["PA"]["mutation_area"] == "amp"
    assert ISOLATED_PAD_MUTATION_COMMANDS["PL"]["mutation_area"] == "lfo"
    assert ISOLATED_PAD_MUTATION_COMMANDS["PO"]["mutation_area"] == "morph"
    assert ISOLATED_PAD_MUTATION_COMMANDS["PB"]["mutation_area"] == "body"
    assert ISOLATED_PAD_MUTATION_COMMANDS["PG"]["mutation_area"] == "grit"
```

Expected red command before production metadata:

```powershell
python .\tests\test_scaffold.py
```

Expected red result:

- import failure because `ISOLATED_PAD_MUTATION_COMMANDS` does not exist yet

Expected green result after implementation:

- direct test file exits 0

### Task 2: Passive Command Lookup

Files:

- Modify: `tests/test_command_lookup.py`

Future test assertions:

```python
def test_known_isolated_pad_mutation_command_lookups_return_existing_metadata():
    expected = {
        "PM": (
            "mutation",
            "selected_isolated_pad",
            "mutate selected isolated pad only using its group default zone/depth",
        ),
        "PS": (
            "mutation",
            "selected_isolated_pad",
            "mutate selected isolated pad SRC only, choose depth",
        ),
        "PF": (
            "mutation",
            "selected_isolated_pad",
            "mutate selected isolated pad Filter only, choose depth",
        ),
        "PA": (
            "mutation",
            "selected_isolated_pad",
            "mutate selected isolated pad Amp only, choose depth",
        ),
        "PL": (
            "mutation",
            "selected_isolated_pad",
            "mutate selected isolated pad LFO only, choose depth",
        ),
        "PO": (
            "mutation",
            "selected_isolated_pad",
            "mutate selected isolated pad Morph only, choose depth",
        ),
        "PB": (
            "mutation",
            "selected_isolated_pad",
            "mutate selected isolated pad Body only, choose depth",
        ),
        "PG": (
            "mutation",
            "selected_isolated_pad",
            "mutate selected isolated pad Grit only, choose depth",
        ),
    }

    for command_key, (command_type, scope, label) in expected.items():
        report = describe_command(command_key)

        assert_passive_command_report(report, command_key)
        assert report["type"] == command_type
        assert report["scope"] == scope
        assert report["label"] == label
        assert report["metadata"] == COMMANDS[command_key]

    assert COMMANDS["PM"]["uses_group_default_zone_depth"] is True
    for command_key in ("PS", "PF", "PA", "PL", "PO", "PB", "PG"):
        assert COMMANDS[command_key]["requires_depth_selection"] is True
```

Also update the `if __name__ == "__main__":` block to call the new test.

Expected red command before production metadata:

```powershell
python .\tests\test_command_lookup.py
```

Expected red result:

- command lookup fails because `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and
  `PG` are not yet present

Expected green result after implementation:

- direct test file exits 0

### Task 3: Fixture Updates

Files:

- Modify: `tests/fixtures/cli_list_commands_expected.txt`
- Modify: `tests/fixtures/registry_report_expected.txt`

Expected fixture changes:

- passive CLI command count moves from `Count: 91` to `Count: 99`
- passive registry report command count moves from `commands: 91` to
  `commands: 99`
- passive CLI list output includes:
  - `- PM: mutate selected isolated pad only using its group default zone/depth`
  - `- PS: mutate selected isolated pad SRC only, choose depth`
  - `- PF: mutate selected isolated pad Filter only, choose depth`
  - `- PA: mutate selected isolated pad Amp only, choose depth`
  - `- PL: mutate selected isolated pad LFO only, choose depth`
  - `- PO: mutate selected isolated pad Morph only, choose depth`
  - `- PB: mutate selected isolated pad Body only, choose depth`
  - `- PG: mutate selected isolated pad Grit only, choose depth`

Expected red command before production metadata:

```powershell
python .\tests\test_cli.py
python .\tests\test_registry_report.py
```

Expected red result:

- list/report fixtures fail because production metadata has not been added yet

Expected green result after implementation:

- direct test files exit 0

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
- no selected isolated pad is mutated
- no depth prompt is executed
- no page-specific mutation is executed
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
- depth prompt execution
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
python .\tests\test_scaffold.py
python .\tests\test_command_lookup.py
python .\tests\test_cli.py
python .\tests\test_registry_report.py
python .\tests\test_registry_report_cli.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected results:

- targeted direct test files pass
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- git status shows only the approved implementation files before commit
- git status is clean after commit

## 12. Review Gate

This plan must be reviewed and accepted before implementation.

The review should confirm:

- `ISOLATED_PAD_MUTATION_COMMANDS` is the accepted future metadata dictionary
- `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` are the only future
  commands in scope
- expected command count movement is 91 to 99
- expected captured modeled count movement is 88 to 96
- expected remaining captured gap movement is 18 to 10
- tests and fixtures remain existing-file updates only
- no closeout script update is expected
- no runtime behavior is authorized
- no selected-pad runtime state mutation is authorized
- no isolated-pad mutation execution is authorized
- no depth prompt execution is authorized
- no real MIDI, ports, active behavior, or hardware behavior is authorized

## 13. Next Recommended Task

Create a documentation-only review gate for this plan.

Do not implement metadata until that review is committed and implementation is
explicitly requested.

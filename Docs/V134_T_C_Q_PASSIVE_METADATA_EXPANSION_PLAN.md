# T C Q Passive Metadata Expansion Plan

> For future implementation workers: this is a planning document only. Do not
> edit command metadata, tests, CLI fixtures, package metadata, or runtime code
> until this plan is separately reviewed and explicitly approved for
> implementation.

**Goal:** Define the exact future passive/scaffold-only metadata expansion for
the first accepted V1.34 registry gap category: `T`, `C`, and `Q`.

**Architecture:** Add three utility/session commands as inert passive metadata
inside the existing command registry flow. The commands should become visible
through existing passive list/search/inspect/preview/report paths only because
they are part of `COMMANDS`, not because any new CLI behavior is added.

**Tech Stack:** Existing Python metadata dictionaries, existing passive
registry helpers, existing fixture-backed CLI tests, and the existing closeout
suite.

---

## 1. Purpose

Plan a future metadata-only expansion for:

- `T` / select target pad/channel
- `C` / change MIDI channel
- `Q` / quit

This document does not implement the expansion.

This document does not edit metadata.

This document does not add tests.

This document does not add CLI commands.

This document does not add runtime behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 58014d7 Add V1.34 passive registry gap review acceptance

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review accepted
- `T`, `C`, and `Q` accepted as first future planning target

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Scope

Future implementation scope:

- add passive metadata for `T`
- add passive metadata for `C`
- add passive metadata for `Q`
- keep all three scaffold-only and non-executable
- expose them through existing passive registry surfaces
- update tests and fixtures that naturally reflect command count/list changes

Out of scope:

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

- add a new `UTILITY_COMMANDS` dictionary near the existing passive command
  category dictionaries
- merge `UTILITY_COMMANDS` into `COMMANDS`
- keep the commands metadata-only and non-executable

Do not add a new module for this tiny slice.

Do not add handlers.

Do not add callbacks.

Do not add dispatch wiring.

## 5. Proposed Exact Metadata

Future metadata should be:

```python
UTILITY_COMMANDS = {
    "T": {
        "type": "selection",
        "scope": "target_pad_channel",
        "sends_midi": False,
        "label": "select target pad/channel",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "C": {
        "type": "selection",
        "scope": "midi_channel",
        "sends_midi": False,
        "label": "change MIDI channel",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "Q": {
        "type": "session",
        "scope": "operator_session",
        "sends_midi": False,
        "label": "quit",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}
```

Future `COMMANDS` merge should include:

```python
    **UTILITY_COMMANDS,
```

Place it after `MENU_COMMANDS` and before group/pad command categories unless
there is a strong local reason to choose another order.

## 6. Expected Passive Surface Changes

After a future implementation, these command keys should exist in
`COMMANDS`:

- `T`
- `C`
- `Q`

Expected passive command count:

- current: 82
- after future implementation: 85

Expected passive registry report command count:

- current: `commands: 82`
- after future implementation: `commands: 85`

Expected passive CLI list changes:

- `C` appears after `BS` and before `D`
- `Q` appears after `PX` and before `R`
- `T` appears after `SX` and before `V`

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

Possible future fixture updates if command search behavior is explicitly tested:

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
from rytm_randomizer.commands import UTILITY_COMMANDS


def test_utility_commands_match_v134_metadata_only_set():
    expected = {"T", "C", "Q"}

    assert set(UTILITY_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_utility_commands_are_scaffold_only_and_not_executable():
    for metadata in UTILITY_COMMANDS.values():
        assert_sends_no_midi(metadata)
        assert_protocol_command_metadata(metadata)


def test_representative_utility_command_labels_match_v134_intent():
    assert UTILITY_COMMANDS["T"] == {
        "type": "selection",
        "scope": "target_pad_channel",
        "sends_midi": False,
        "label": "select target pad/channel",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert UTILITY_COMMANDS["C"]["label"] == "change MIDI channel"
    assert UTILITY_COMMANDS["Q"]["label"] == "quit"
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
def test_known_utility_command_lookups_return_existing_metadata():
    expected = {
        "T": ("selection", "target_pad_channel", "select target pad/channel"),
        "C": ("selection", "midi_channel", "change MIDI channel"),
        "Q": ("session", "operator_session", "quit"),
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

### Task 3: Passive CLI And Registry Fixtures

Files:

- Modify: `tests/fixtures/cli_list_commands_expected.txt`
- Modify: `tests/fixtures/registry_report_expected.txt`

Expected fixture changes:

- `cli_list_commands_expected.txt` command count changes from `82` to `85`
- add `- C: change MIDI channel`
- add `- Q: quit`
- add `- T: select target pad/channel`
- `registry_report_expected.txt` command count changes from `82` to `85`

Expected command:

```powershell
python -m pytest tests/test_cli.py tests/test_registry_report.py tests/test_registry_report_cli.py -q
```

Expected result after implementation:

- pass

### Task 4: Full Closeout

Expected command:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected result after implementation:

- closeout passes
- V1.34 reference diff is empty
- git status shows only the approved implementation files before commit

## 9. Future Verification Checklist

Any future implementation must verify:

- importing `rytm_randomizer.commands` prints nothing
- `T`, `C`, and `Q` exist in `COMMANDS`
- all three are non-executable
- all three are scaffold-only
- all three send no MIDI
- all three expose no handler/callable/execute/function/callback fields
- passive command lookup works for all three
- passive registry report count updates deterministically
- passive CLI list output updates deterministically
- no new CLI command is added
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no hardware is required
- V1.34 reference diff remains empty
- package metadata remains unchanged

## 10. Safety Boundaries

This plan adds:

- no command metadata
- no tests
- no runtime code
- no CLI wiring
- no package metadata
- no dependency selection
- no `mido`
- no real MIDI dependency
- no port discovery
- no port opening
- no MIDI sending
- no active CLI command
- no execute-command
- no send-command
- no hardware-test
- no dispatch
- no command execution
- no scene execution
- no hardware behavior
- no hardware detection
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no profile `"4"` implementation
- no hardware validation
- no hardware-on authorization

`rytm_hybrid_randomizer_v134.py` remains untouched.

Analog Rytm MKII remains off.

Analog Four MKII remains off.

## 11. Review Requirements Before Implementation

Before implementation, create and accept a review gate for this plan.

The review gate should confirm:

- `T`, `C`, and `Q` are the only planned commands
- metadata shape is accepted
- tests and fixtures are accepted
- no active behavior is authorized
- no real MIDI is authorized
- no package metadata is authorized
- hardware remains off

## 12. Decision

This plan defines the future metadata-only path for `T`, `C`, and `Q`.

No implementation is added by this slice.

The review/acceptance gate now lives in:

- `Docs/V134_T_C_Q_PASSIVE_METADATA_EXPANSION_PLAN_REVIEW.md`

The next recommended task is the tiny passive metadata-only implementation
slice for `T`, `C`, and `Q`, only after explicit approval.

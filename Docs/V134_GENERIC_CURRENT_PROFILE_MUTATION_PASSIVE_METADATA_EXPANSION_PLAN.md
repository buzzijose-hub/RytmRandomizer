# V1.34 Generic Current-Profile Mutation Passive Metadata Expansion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Add passive metadata for the final captured V1.34 generic
current-profile page mutation commands without adding runtime behavior.

**Architecture:** Extend the existing passive command metadata surface with one
new scaffold-only dictionary, merge it into `COMMANDS`, and update only the
existing scaffold, lookup, CLI fixture, and registry report fixture coverage.
The implementation must remain data-only and must not introduce handlers,
dispatch, depth prompts, MIDI, ports, package metadata, or hardware behavior.

**Tech Stack:** Python standard library, existing passive metadata dictionaries,
existing script-style tests, deterministic text fixtures, PowerShell closeout.

---

## Purpose

Define the future passive metadata-only implementation path for the remaining
captured V1.34 generic current-profile page mutation commands:

- `S` / SRC-only mutation, choose depth
- `F` / Filter-only mutation, choose depth
- `A` / Amp-only mutation, choose depth
- `G` / Grit-only mutation, choose depth
- `K` / Kick body mutation, choose depth

This plan is documentation-only. It does not add metadata, tests, fixtures,
runtime code, CLI wiring, dispatch, MIDI, ports, package metadata, active
behavior, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- ae0a772 Add generic current-profile mutation gap decision note

Current passive command count:

- 104

Captured V1.34 operator entries modeled as passive command metadata:

- 101

Remaining captured command-surface gaps:

- 5

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Future Target Commands

The future implementation should add passive metadata for exactly:

- `S` / SRC-only mutation, choose depth
- `F` / Filter-only mutation, choose depth
- `A` / Amp-only mutation, choose depth
- `G` / Grit-only mutation, choose depth
- `K` / Kick body mutation, choose depth

Do not add any other commands in this implementation slice.

## Proposed Future Metadata Dictionary

Future implementation should add one passive dictionary:

- `CURRENT_PROFILE_PAGE_MUTATION_COMMANDS`

Recommended metadata shape for each entry:

- `type`: `mutation`
- `scope`: `current_profile`
- `command_family`: `generic_current_profile_page_mutation`
- `mutation_area`: command-specific area
- `requires_depth_selection`: `True`
- `sends_midi`: `False`
- `label`: V1.34 operator label
- `executable`: `False`
- `v134_reference_command`: `True`
- `scaffold_only`: `True`

Suggested command-specific `mutation_area` values:

- `S`: `src`
- `F`: `filter`
- `A`: `amp`
- `G`: `grit`
- `K`: `kick_body`

The names are metadata labels only. They must not be treated as callable
handlers, runtime pages, depth prompts, dispatch targets, or MIDI behavior.

## Future Files To Update

Future implementation should update:

- `rytm_randomizer/commands.py`
- `tests/test_scaffold.py`
- `tests/test_command_lookup.py`
- `tests/fixtures/cli_list_commands_expected.txt`
- `tests/fixtures/registry_report_expected.txt`

Do not update:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `Scripts/closeout_check.ps1`
- package metadata files
- runtime execution/dispatch/MIDI logic

No closeout script update should be needed because the existing scaffold,
command lookup, CLI, registry, and registry report tests are already included.

## Expected Future Count Movement

If later implemented as passive metadata only:

- passive command count moves from 104 to 109
- passive registry report command count moves from `commands: 104` to
  `commands: 109`
- captured modeled count moves from 101 to 106
- remaining captured command-surface gaps move from 5 to 0

This would complete the currently captured V1.34 operator command surface as
passive command metadata.

## Future Test Plan

### Task 1: Scaffold Tests

**Files:**

- Modify: `tests/test_scaffold.py`

- [ ] Add a failing import for `CURRENT_PROFILE_PAGE_MUTATION_COMMANDS`.
- [ ] Add a test proving the dictionary keys are exactly `S`, `F`, `A`, `G`,
  and `K`.
- [ ] Add a test proving all entries are scaffold-only, non-executable, and
  send no MIDI.
- [ ] Add a representative metadata test for exact labels and
  `mutation_area` values.
- [ ] Run `python .\tests\test_scaffold.py` and verify the new tests fail
  before implementation.

Expected future assertions:

```python
expected = {"S", "F", "A", "G", "K"}
assert set(CURRENT_PROFILE_PAGE_MUTATION_COMMANDS) == expected
assert expected.issubset(COMMANDS)
```

### Task 2: Command Lookup Tests

**Files:**

- Modify: `tests/test_command_lookup.py`

- [ ] Add failing lookup coverage for `S`, `F`, `A`, `G`, and `K`.
- [ ] Assert each command returns existing passive metadata through
  `describe_command`.
- [ ] Assert all entries use `scope: current_profile`,
  `command_family: generic_current_profile_page_mutation`, and
  `requires_depth_selection: True`.
- [ ] Run `python .\tests\test_command_lookup.py` and verify the new tests
  fail before implementation.

### Task 3: Fixture Updates

**Files:**

- Modify: `tests/fixtures/cli_list_commands_expected.txt`
- Modify: `tests/fixtures/registry_report_expected.txt`

- [ ] Update passive list-command fixture with the five new labels in the
  existing deterministic ordering.
- [ ] Update registry report command count from `104` to `109`.
- [ ] Run `python .\tests\test_cli.py` and verify fixture mismatch before
  implementation if the fixture is updated before metadata.
- [ ] Run `python .\tests\test_registry_report.py` and verify fixture mismatch
  before implementation if the fixture is updated before metadata.

### Task 4: Passive Metadata Implementation

**Files:**

- Modify: `rytm_randomizer/commands.py`

- [ ] Add `CURRENT_PROFILE_PAGE_MUTATION_COMMANDS` near related passive
  mutation dictionaries.
- [ ] Merge it into `COMMANDS` in the existing dictionary composition flow.
- [ ] Keep every entry `sends_midi: False`, `executable: False`, and
  `scaffold_only: True`.
- [ ] Do not add callables, handlers, dispatch hooks, depth prompt behavior,
  MIDI imports, port opening, package metadata, or CLI changes.

### Task 5: Verification And Commit

**Files:**

- Verify all changed implementation/test/fixture files.

- [ ] Run targeted tests:

```powershell
python .\tests\test_scaffold.py
python .\tests\test_command_lookup.py
python .\tests\test_cli.py
python .\tests\test_registry_report.py
python .\tests\test_registry_report_cli.py
python .\tests\test_registry.py
```

- [ ] Run full closeout:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

- [ ] Verify protected reference diff is empty:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
```

- [ ] Verify package metadata diff is empty and package metadata files remain
  absent:

```powershell
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
Test-Path .\pyproject.toml
Test-Path .\requirements.txt
Test-Path .\setup.py
Test-Path .\setup.cfg
```

- [ ] Verify status and commit with:

```powershell
git status --short
git add .\rytm_randomizer\commands.py `
        .\tests\test_scaffold.py `
        .\tests\test_command_lookup.py `
        .\tests\fixtures\cli_list_commands_expected.txt `
        .\tests\fixtures\registry_report_expected.txt
git commit -m "Add generic current-profile mutation passive metadata"
```

## Future Documentation Checkpoint

After implementation, create a documentation checkpoint recording:

- implementation commit hash
- `CURRENT_PROFILE_PAGE_MUTATION_COMMANDS`
- `S`, `F`, `A`, `G`, and `K`
- command count movement from 104 to 109
- registry report count movement from `commands: 104` to `commands: 109`
- captured modeled count movement from 101 to 106
- remaining captured gap movement from 5 to 0
- completion of the currently captured V1.34 command surface
- no runtime execution, MIDI, ports, package metadata, active behavior, or
  hardware behavior

Likely docs to update:

- `Docs/NEXT_ACTION.md`
- `Docs/PROJECT_CHECKPOINT_CURRENT.md`
- `Docs/PASSIVE_ARCHITECTURE_SUMMARY.md`

## Confirmed Safety Boundaries

- no metadata is added in this slice
- no tests are added in this slice
- no fixtures are updated in this slice
- no runtime code is changed in this slice
- no new CLI command
- no handler
- no dispatch
- no depth prompt execution
- no current-profile mutation execution
- no selected-profile runtime mutation
- no command execution
- no scene execution
- no MIDI
- no MIDI port opening
- no MIDI sending
- no real MIDI dependency
- no package metadata change
- no active behavior
- no hardware behavior
- no hardware validation
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Decision

This plan defines the future implementation path for the final captured
generic current-profile page mutation metadata gap.

Implementation remains parked until this plan is reviewed, accepted, and
explicitly approved.

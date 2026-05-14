# V1.34 Passive Metadata CLI Import Isolation Checkpoint

## Purpose

Record the completed passive CLI import-isolation hardening for passive
metadata and preview helpers.

This checkpoint documents that plain CLI import no longer loads the passive
metadata stack. It does not add implementation beyond the already committed
lazy-loading change.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Implementation milestone:

- `a38bcdd Lazy-load passive metadata CLI helpers`

Files changed by the milestone:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## What Changed

The passive CLI now lazy-loads passive metadata and preview helpers inside the
commands that need them.

Plain `import rytm_randomizer.cli` no longer loads:

- `rytm_randomizer.commands`
- `rytm_randomizer.scenes`
- `rytm_randomizer.profiles`
- `rytm_randomizer.registry`
- `rytm_randomizer.preview`
- `rytm_randomizer.inspection`
- `rytm_randomizer.validation`

The package-level `rytm_randomizer.constants` module still loads during package
import through `rytm_randomizer.__init__`; this is expected and unchanged.

## Behavior Preserved

Existing passive CLI behavior remains unchanged:

- `report`
- `list-commands`
- `list-scenes`
- `list-group-profiles`
- `search-commands`
- `search-scenes`
- `search-group-profiles`
- `inspect-command`
- `inspect-scene`
- `inspect-group-profile`
- `preview-command`
- `preview-scene`
- `preview-group-profile`
- passive report commands

The list/search/inspect/preview helpers still load the passive registry and
preview code only when their command paths are invoked.

## Verification

Focused CLI verification passed:

- `python -m pytest tests/test_cli.py::test_importing_cli_does_not_load_passive_metadata_modules tests/test_cli.py::test_list_commands_exits_zero_and_matches_fixture tests/test_cli.py::test_inspect_command_known_key_exits_zero_and_matches_fixture tests/test_cli.py::test_preview_command_known_key_exits_zero_and_matches_fixture -q`
- `python -m pytest tests/test_cli.py -q`
- `python tests\test_cli.py`

Full closeout passed after the implementation:

- `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`

Guardrail checks:

- V1.34 reference diff was empty.
- Package metadata diff was empty.
- `git diff --check` reported only line-ending normalization warnings.

## Safety Boundaries

This milestone adds no:

- CLI output change
- fixture change
- runtime execution
- dispatch
- command execution
- mutation execution
- active CLI command
- MIDI
- port opening
- package metadata change
- active behavior
- hardware behavior

## Decision

Passive metadata CLI import isolation is accepted as complete for this slice.

The import-isolation thread should pause unless a new concrete drift appears.
The next best move is a different test-backed behavior-parity alignment slice
or a short progress checkpoint.

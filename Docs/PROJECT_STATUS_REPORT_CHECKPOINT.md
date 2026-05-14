# Project Status Report Checkpoint

## Purpose

Record the passive project status safety-check milestone.

This adds a read-only invariant check for the existing project status report.
It does not add runtime execution, dispatch, command execution, MIDI behavior,
active behavior, or hardware behavior.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `b95ddca Add project status report summary output`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## New Passive Check Output

Existing passive CLI command now supports:

- `python -m rytm_randomizer.cli project-status-report --check`

Updated module:

- `rytm_randomizer/project_status_report.py`

Updated tests:

- `tests/test_project_status_report.py`
- `tests/test_cli.py`

New fixture:

- `tests/fixtures/cli_project_status_report_check_expected.txt`

Updated fixtures:

- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_project_status_report_help_expected.txt`

## Behavior

The check validates passive safety invariants from the in-memory project
status report.

It checks:

- real MIDI remains absent
- port opening remains absent
- active execution remains absent
- command execution remains absent
- dispatch remains absent
- hardware remains not required
- V1.34 reference remains untouched
- package metadata remains untouched
- runtime execution remains absent
- active CLI behavior remains absent
- mock runtime/active bridge emits no messages
- report source remains in-memory only
- report source writes no files
- closeout failure propagation remains guarded

## Confirmed Boundaries

This milestone adds no:

- runtime execution
- dispatch
- command execution
- mutation execution
- active CLI command
- real MIDI
- MIDI dependency
- port discovery
- port opening
- package metadata change
- active behavior
- hardware behavior

## Verification

Targeted TDD evidence:

- `python .\tests\test_project_status_report.py` failed before the passive
  status check function existed.
- `python .\tests\test_cli.py` failed before the CLI help/output accepted
  `project-status-report --check`.
- both targeted tests passed after implementation.

Expected closeout state:

- closeout still includes `Project Status Report`
- V1.34 reference diff remains empty
- package metadata diff remains empty

## Decision

The project status report now has full text, compact summary, machine-readable
JSON, and passive invariant-check output.

Next recommended task:

- continue with another passive/mock-only software slice, or use
  `project-status-report --check` as a quick guard before future planning and
  implementation packets.

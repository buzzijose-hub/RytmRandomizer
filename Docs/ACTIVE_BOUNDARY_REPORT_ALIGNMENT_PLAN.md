# Active Boundary Report Alignment Plan

## Purpose

Define Packet 2 from the mock/fake-provider active-boundary strengthening
sequence: active-boundary report alignment after Packet 1 metadata
strengthening.

This document is planning-only. It does not add tests, edit runtime code,
change CLI behavior, dispatch commands, send MIDI, open ports, add active
execution, or authorize hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 4b41f56 Add active boundary metadata strengthening review

Current phase:

- Passive/Mock Foundation Phase
- captured V1.34 command surface complete as passive metadata
- Packet 1 active-boundary metadata strengthening complete and reviewed
- Packet 2 active-boundary report alignment now being planned
- fake-provider-only real MIDI adapter boundary remains isolated
- hardware not required

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off

## Current Report State

Current report module:

- `rytm_randomizer/active_boundary_report.py`

Current report tests:

- `tests/test_active_boundary_report.py`

Current passive CLI fixtures:

- `tests/fixtures/cli_active_boundary_report_expected.txt`
- `tests/fixtures/cli_active_boundary_report_help_expected.txt`

Current passive CLI command:

- `python -m rytm_randomizer.cli active-boundary-report`

The current report already summarizes:

- accepted active-boundary candidate: group profile `"2"` / My BD Hard
- unsupported active-boundary profiles: `"3"` and `"4"`
- required conditions
- safe-failure summaries
- active-boundary safety fields
- closeout coverage

The current report remains read-only. It does not evaluate active requests,
construct senders, dispatch commands, open ports, send MIDI, or touch hardware.

## Packet 1 Metadata Now Available

Packet 1 added deterministic active-boundary result metadata:

- boundary: `mock_active_boundary`
- supported candidate: `group_profile:2`
- source kind
- source key
- target
- armed state
- dry-run confirmation state
- optional operator intent
- mock-only status
- sends-real-MIDI status
- failure reason on failure paths

Packet 2 should decide how much of this metadata belongs in the read-only
active-boundary report.

## Alignment Goal

Packet 2 should align the report with Packet 1 metadata without making the
report active.

The report should remain a passive summary of the boundary, not an evaluator.

Useful alignment candidates:

- report the active boundary name: `mock_active_boundary`
- report the supported candidate key: `group_profile:2`
- report the result metadata fields now guaranteed by Packet 1
- report that failure result metadata includes a reason
- keep required conditions and safe-failure summaries deterministic
- keep unsupported profiles `"3"` and `"4"` explicitly unsupported

## Proposed Packet 2 Ownership

Allowed files for Packet 2 implementation:

- `rytm_randomizer/active_boundary_report.py`
- `tests/test_active_boundary_report.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_active_boundary_report_expected.txt`

Only update the CLI help fixture if the command help text actually changes:

- `tests/fixtures/cli_active_boundary_report_help_expected.txt`

Do not edit:

- `rytm_randomizer/active_boundary.py`
- `rytm_randomizer/real_midi_adapter.py`
- `rytm_randomizer/cli.py` unless fixture/test evidence requires a passive
  formatting adjustment
- `Scripts/closeout_check.ps1`
- `rytm_hybrid_randomizer_v134.py`
- package metadata files

## Proposed Future Test Expectations

Future tests should verify:

- importing `rytm_randomizer.active_boundary_report` prints nothing
- report includes `boundary: mock_active_boundary`
- report includes `supported_candidate: group_profile:2`
- report lists Packet 1 result metadata fields
- report states failure metadata includes reason
- report keeps profile `"2"` as the only accepted active-boundary candidate
- report keeps profile `"3"` unsupported by active boundary
- report keeps profile `"4"` parked and unsupported
- report remains decoupled from `evaluate_mock_active_boundary`
- report does not construct `MockMidiSender`
- report does not import real MIDI libraries
- passive CLI `active-boundary-report` output is deterministic
- passive CLI `active-boundary-report` remains read-only
- V1.34 reference diff remains empty
- package metadata files remain absent

## Proposed Future Output Shape

The formatted report may add a section such as:

```text
Result Metadata:
- boundary: mock_active_boundary
- supported_candidate: group_profile:2
- fields: source_kind, source_key, target, armed, dry_run_confirmed, operator_intent, mock_only, sends_real_midi
- failure_reason: included on failure paths
```

This is a proposed shape only. Do not implement it in this planning slice.

## Scope That Must Stay Frozen

Packet 2 must not add:

- profile `"3"` active-boundary support
- profile `"4"` implementation
- scenes
- global mutations
- command dispatch
- command execution
- scene execution
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI dependencies
- package metadata changes
- MIDI port opening
- MIDI sending
- hardware validation
- Analog Four support
- Pads 5-12 support
- machine/profile expansion

## Required Verification For Packet 2

Packet 2 must run:

```powershell
python .\tests\test_active_boundary_report.py
python .\tests\test_cli.py
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected state:

- targeted report tests pass
- passive CLI tests pass if fixtures change
- full closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- package metadata files remain absent
- git status is clean after commit

## Parallelization Position

Parallel implementation is not recommended for Packet 2 unless it is split
into two independent lanes:

- report module and report tests
- CLI fixture verification only after report text is finalized

For the first Packet 2 slice, inline single-agent implementation is simpler
because report output and fixture text are tightly coupled.

## Recommendation

This plan has a matching review gate:

- `Docs/ACTIVE_BOUNDARY_REPORT_ALIGNMENT_PLAN_REVIEW.md`

After acceptance, implement a tiny Packet 2 report alignment slice only if the
report text should expose the Packet 1 metadata fields.

Do not widen active-boundary support. Do not add real MIDI. Do not turn on
hardware.

## Decision

Packet 2 should align read-only active-boundary report visibility with the
metadata guarantees added by Packet 1.

No implementation is added in this slice.

Hardware remains off. Runtime behavior remains unchanged.

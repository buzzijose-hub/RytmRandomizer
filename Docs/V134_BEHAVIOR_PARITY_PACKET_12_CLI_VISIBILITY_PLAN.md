# V1.34 Behavior Parity Packet 12 CLI Visibility Plan

## 1. Purpose

Plan passive CLI visibility for the existing Packet 12 behavior-parity
coverage report.

This is a documentation-only planning slice.

It adds no implementation, tests, CLI command, CLI wiring, runtime execution,
dispatch, MIDI, ports, package metadata changes, active behavior, or hardware
behavior.

This plan does not authorize implementation by itself.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this plan slice:

- `48bb249 Add behavior parity next phase selection review after Packet 12`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 12 behavior-parity coverage report implemented and accepted
- broader Packet 12 progress report reviewed and accepted
- Packet 12 CLI visibility planning selected and accepted as the next branch
- Packet 12 CLI visibility now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream State

Accepted upstream selection review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PHASE_SELECTION_CHECKPOINT_AFTER_PACKET_12_REVIEW.md`

Accepted upstream selection checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PHASE_SELECTION_CHECKPOINT_AFTER_PACKET_12.md`

Accepted upstream Packet 12 progress report review:

- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_12_REVIEW.md`

Accepted Packet 12 coverage report checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_12_COVERAGE_REPORT_CHECKPOINT.md`

Accepted Packet 12 implementation milestone:

- `95bf4c6 Add behavior parity coverage report`

Accepted current state:

- Packet 12 behavior-parity coverage report exists
- report data is deterministic and in-memory
- formatted report output exists
- closeout covers the report
- Packet 12 CLI visibility remains unimplemented
- no CLI command has been added yet
- no active behavior is authorized

## 4. Plan Goal

The future CLI visibility slice should expose the existing formatted Packet 12
coverage report from the passive CLI.

The future CLI command should improve operator visibility only.

It should show:

- accepted behavior-parity packet coverage
- `PZ`, `B`, and `L` runtime-adjacent safe-failure coverage
- parked scope
- intentionally absent behavior
- protected-file state

It must not execute, dispatch, send, mutate, arm, or validate hardware.

## 5. Proposed Future CLI Command

Recommended future command name:

- `behavior-parity-report`

Possible future command:

```powershell
python -m rytm_randomizer.cli behavior-parity-report
```

Possible future help command:

```powershell
python -m rytm_randomizer.cli behavior-parity-report --help
```

Alternative command name considered:

- `behavior-parity-coverage-report`

Recommendation:

- Prefer `behavior-parity-report` because it is shorter and follows the
  existing passive report command style.

This command is not implemented in this slice.

## 6. Future CLI Behavior

If later reviewed and approved, the future command should:

- call only `format_behavior_parity_coverage_report()`
- print the existing formatted report output
- exit `0`
- add no options beyond `--help`
- write no files
- open no ports
- send no MIDI
- require no hardware
- invoke no dispatch path
- invoke no execution path
- invoke no active boundary path
- import safely without printing during import

The future command must remain passive/read-only.

## 7. Future Test Expectations

If later implemented, tests should verify:

- importing `rytm_randomizer.cli` prints nothing
- top-level CLI help lists `behavior-parity-report`
- `python -m rytm_randomizer.cli behavior-parity-report --help` exits `0`
- help output is deterministic and fixture-backed
- `python -m rytm_randomizer.cli behavior-parity-report` exits `0`
- report output is deterministic and fixture-backed
- output shows accepted Packet 12 behavior-parity coverage
- output shows `PZ`, `B`, and `L` runtime-adjacent safe-failure coverage
- output shows parked scope
- output shows intentionally absent behavior
- output shows protected-file state
- existing passive CLI behavior remains unchanged
- no real MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- no active CLI behavior is introduced
- V1.34 reference remains untouched
- package metadata remains untouched

Likely future fixture files:

- `tests/fixtures/cli_behavior_parity_report_help_expected.txt`
- `tests/fixtures/cli_behavior_parity_report_expected.txt`

This plan adds no tests or fixture files.

## 8. Future Closeout Expectations

`tests/test_cli.py` is already part of closeout.

If the future implementation only updates `tests/test_cli.py`, no closeout
script update should be needed.

Any future implementation must pass:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected future verification state:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- git status is clean

## 9. Out Of Scope

This plan does not add:

- implementation
- tests
- fixture files
- closeout script changes
- package metadata changes
- Packet 12 CLI command
- CLI execution wiring
- command dispatch
- command execution
- scene execution
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- fourth runtime-adjacent candidate
- profile `4` mock mapper support
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## 10. Preconditions Before Implementation

Before any Packet 12 CLI visibility implementation:

- clean Git status
- full closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- this plan is reviewed and accepted
- implementation remains passive and read-only
- implementation calls only `format_behavior_parity_coverage_report()`
- output is deterministic and fixture-backed
- existing passive CLI behavior remains unchanged
- no execution path is added
- no real MIDI libraries are imported
- no ports are opened
- no hardware is required

## 11. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this plan
- pause at this planning checkpoint
- broader user-facing progress/timeline report

## 12. Recommendation

Review and accept this Packet 12 CLI visibility plan next.

After review, implement the tiny passive CLI visibility slice only if explicitly
approved.

Do not implement Packet 12 CLI visibility in this slice.

Do not select a fourth runtime-adjacent candidate yet.

Do not add profile `4` mock mapper support yet.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 13. Decision

Packet 12 CLI visibility is planned as a future passive report command.

Selected future command name:

- `behavior-parity-report`

The next selected branch is:

- docs-only review/acceptance gate for this plan

Hardware remains off.

No implementation in this slice.

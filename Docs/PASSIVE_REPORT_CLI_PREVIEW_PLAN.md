# Passive Report CLI Preview Plan

## Purpose

This document defines the read-only CLI preview/report command concept for
RytmRandomizer and records the implemented passive CLI preview milestone. It
does not approve runtime wiring, command execution, MIDI behavior, or hardware
behavior.

The implemented command exposes the existing passive registry report in a
convenient operator-facing form while preserving the current passive safety
boundary.

Implemented milestone:

- 915b7a2 Add passive registry report CLI preview
- 52e7477 Add passive report-only CLI entrypoint
- 935d24a Add passive CLI help contract
- 73ee027 Add passive CLI command inspection
- eeba082 Add passive CLI scene inspection

## Current Passive Foundation

Current clean baseline before this planning slice:

- 0ae33ef Update checkpoint after registry report golden text contract

The current closeout suite includes:

- scaffold
- validation
- inspection
- preview
- audit
- profile lookup
- scene lookup
- command lookup
- registry
- registry report
- registry report CLI
- passive CLI

The passive foundation includes:

- `rytm_randomizer/registry.py`
- `rytm_randomizer/registry_report.py`
- `tests/fixtures/registry_report_expected.txt`

`rytm_hybrid_randomizer_v134.py` remains the protected V1.34 behavior
reference.

## Implemented Command Shape

Implemented passive module command:

```powershell
python -m rytm_randomizer.registry_report
```

Implemented passive report-only CLI entrypoint:

```powershell
python -m rytm_randomizer.cli report
```

Implemented passive CLI help commands:

```powershell
python -m rytm_randomizer.cli --help
python -m rytm_randomizer.cli report --help
```

Implemented passive CLI command inspection:

```powershell
python -m rytm_randomizer.cli inspect-command <key>
python -m rytm_randomizer.cli inspect-command --help
```

Implemented passive CLI scene inspection:

```powershell
python -m rytm_randomizer.cli inspect-scene <key>
python -m rytm_randomizer.cli inspect-scene --help
```

The report commands print the same deterministic golden-format passive registry
report.

Manual verification showed both commands report:

- commands: 82
- scenes: 14
- group_profiles: 4

The report confirms:

- dispatches_commands: False
- executes_commands: False
- mutates_hardware: False
- opens_ports: False
- sends_midi: False
- writes_sysex: False
- In-memory only: True

Manual verification showed top-level help prints passive CLI usage, report help
prints passive report usage, and report prints the passive registry report.

Manual verification also showed:

- `python -m rytm_randomizer.cli --help` prints updated passive CLI help with
  report, inspect-command, and inspect-scene.
- `python -m rytm_randomizer.cli inspect-command --help` prints passive
  inspect-command usage.
- `python -m rytm_randomizer.cli inspect-command J` prints passive metadata:
  Command: J, Found: True, Type: print, Label: show 4-pad group layout,
  Executable: False, Scaffold only: True, and V1.34 reference command: True.
- `python -m rytm_randomizer.cli inspect-command DOES_NOT_EXIST` fails safely
  with: "Command metadata not found. No MIDI was sent. No command executed."
- `python -m rytm_randomizer.cli inspect-scene --help` prints passive
  inspect-scene usage.
- `python -m rytm_randomizer.cli inspect-scene S1A` prints passive scene
  metadata: Scene: S1A, Found: True, Name: Rolling Light, Description:
  Lower-risk rolling movement for subtle live variation, Action:
  rolling_light, Scope: four_pad_group, Executable: False, Scaffold only:
  True, and V1.34 reference command: True.
- `python -m rytm_randomizer.cli inspect-scene DOES_NOT_EXIST` fails safely
  with: "Scene metadata not found. No MIDI was sent. No command executed."

## Allowed Behavior

The passive CLI preview command may:

- import the passive registry report module
- build the existing passive registry report
- format the existing passive registry report
- display the report to standard output only when explicitly invoked as a CLI
- exit without requiring hardware
- remain deterministic against the existing golden text contract
- fail safely for missing or unknown arguments
- show deterministic passive help and usage text
- inspect existing passive command metadata without executing it
- inspect existing passive scene metadata without executing it

## Prohibited Behavior

The passive CLI preview/report command must not:

- send MIDI
- open MIDI ports
- dispatch commands
- execute commands
- call command handlers
- add command handlers
- mutate hardware
- write report files by default
- print during import
- require hardware to be connected
- mutate runtime state
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

The passive CLI help contract must remain passive/read-only and must not add new
functional commands.

The passive CLI command inspection path must remain passive/read-only. It must
not reinterpret command metadata as executable behavior.

The passive CLI scene inspection path must remain passive/read-only. It must
not reinterpret scene metadata as executable behavior.

## Safety Boundaries

The CLI preview/report concept remains behind these boundaries:

- no MIDI sending
- no port opening
- no dispatch
- no command execution
- no hardware mutation
- no SysEx
- no GUI
- no capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile universe expansion

## Relationship To registry_report.py

The future CLI preview/report command should sit on top of
`rytm_randomizer/registry_report.py`.

It should only call passive report functions such as:

- `build_registry_report()`
- `format_registry_report()`
- `summarize_registry_report()`

It must not reinterpret report data as executable instructions.

## Relationship To tests/fixtures/registry_report_expected.txt

The fixture `tests/fixtures/registry_report_expected.txt` defines the current
golden text contract for the formatted passive registry report.

Any future CLI preview/report command should preserve this formatted output
unless a deliberate documentation and test update is approved.

Line endings should continue to be normalized in tests so Windows CRLF/LF
differences do not create false failures.

## Preconditions Before Implementation

Before expanding any CLI preview/report command:

- user approval must be explicit
- the expansion must be a small isolated step
- no runtime dispatch or command execution may be introduced
- no MIDI import, send, or port opening may be introduced
- no file-writing behavior may be introduced by default
- import-time output must remain prohibited
- the golden text contract must remain passing
- the closeout suite must remain passing

## Closeout Requirements For Future Implementation

Future implementation must run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

The V1.34 reference diff must remain empty.

Additional direct-runnable CLI tests should be added only if CLI behavior is
expanded with explicit approval.

## Non-Goals

This plan does not approve:

- additional CLI commands or options
- runtime command dispatch
- MIDI behavior
- hardware interaction
- state capture
- SysEx parsing or writing
- GUI work
- Analog Four support
- Pads 5-12 support
- machine/profile universe expansion

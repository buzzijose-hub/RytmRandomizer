# RytmRandomizer Current Project Checkpoint

Date: May 4, 2026
Status: Active branch is modularize-v1.34

## Current Stable Reference

The protected stable reference is V1.34 expanded scene layer.

Git tag:

v1.34-stable-expanded-scene-layer

V1.34 remains the behavior reference until the modular version is fully validated.

## Current Git State

Current branch:

modularize-v1.34

Recent checkpoint history:

- 73ee027 Add passive CLI command inspection
- 935d24a Add passive CLI help contract
- 52e7477 Add passive report-only CLI entrypoint
- 915b7a2 Add passive registry report CLI preview
- 97ecf09 Add registry report golden text contract
- e387f66 Add passive registry report generator
- f6b10ca Add passive architecture summary
- e7b0755 Add passive command lookup helpers
- 748c320 Add passive scene lookup helpers
- 02bd056 Add passive group profile lookup helpers
- 54aca99 Add closeout check workflow
- 55342e7 Add behavior-preserving extraction plan
- dc1ecfc Add passive registry audit reports
- eab5898 Add passive command preview reports
- be92ab4 Add passive command inspection helpers
- 68b16e1 Harden passive metadata validation tests
- 1b4aee3 Add passive metadata validation helpers
- c926719 Add constants scaffold coverage
- d56ff2f Update checkpoint after PAD_PROFILES coverage
- 03b6a8e Add PAD_PROFILES scaffold coverage
- a4a0170 Update checkpoint after command metadata refinement
- c7d5489 Refine command metadata consistency
- a87f7bb Add Codex modularization protocol
- e3a37e3 Add individual pad command metadata scaffold
- 90f1677 Refine scene command metadata scaffold
- 556a7ba Add group command metadata scaffold
- 1130205 Clean up scaffold metadata tests
- 35e598f Add menu command metadata scaffold
- a0f5005 Add forbidden action guardrail metadata
- defbf43 Add out-of-scope pad guardrail metadata
- 8be1dfa Add validated constants metadata scaffold
- 57d3502 Add group profile metadata scaffold
- ae112cf Add main prompt depth guardrail metadata
- 0b94806 Add group layout metadata scaffold
- 3222200 Expand scene metadata scaffold
- b1d04e6 Add initial modular scaffold and tests
- 7de1691 Add Codex modularization task brief
- 50b83f9 Add modularization rules
- a762bd0 Add capture tools and project docs
- cc5ce71 Baseline V1.34 expanded scene layer checkpoint

## Current Priority

Finish behavior-preserving modularization of V1.34.

No new features should be added until the modular version behaves exactly like V1.34.

## Current Modular Scaffold

The modular scaffold is still metadata-only. Current scaffold coverage includes:

- constants / pad scope guardrails
- out-of-scope Pads 5-12 guardrails
- scene command metadata
- group layout / profile metadata
- menu / status command metadata
- forbidden / no-touch action metadata
- four-lane group command metadata
- individual Pad 1-4 command metadata
- command metadata consistency checks
- passive command registry validation
- passive command inspection
- passive command preview reports
- passive registry audit reports
- passive group profile lookup helpers
- passive scene lookup helpers
- passive command lookup helpers
- unified passive registry view
- passive registry report generator
- registry report golden text contract
- passive report CLI preview plan
- passive registry report CLI preview
- passive report-only CLI entrypoint
- passive CLI help contract
- passive CLI command inspection
- passive architecture summary
- behavior-preserving extraction plan
- closeout check workflow
- scaffold metadata tests
- Codex modularization protocol

The closeout check workflow includes:

- Scripts/closeout_check.ps1
- Docs/Session_Logs/

The closeout script runs the standard passive test suite and safety checks:

- python .\tests\test_scaffold.py
- python .\tests\test_validation.py
- python .\tests\test_inspection.py
- python .\tests\test_preview.py
- python .\tests\test_audit.py
- python .\tests\test_profile_lookup.py
- python .\tests\test_scene_lookup.py
- python .\tests\test_command_lookup.py
- python .\tests\test_registry.py
- python .\tests\test_registry_report.py
- python .\tests\test_registry_report_cli.py
- python .\tests\test_cli.py
- git diff -- rytm_hybrid_randomizer_v134.py
- git status --short

The closeout script now includes "Test: Profile Lookup" as part of the standard
passive test suite.

The closeout script now includes "Test: Scene Lookup" as part of the standard
passive test suite.

The closeout script now includes "Test: Command Lookup" as part of the standard
passive test suite.

The closeout script now includes "Test: Registry" as part of the standard
passive test suite.

The closeout script now includes "Test: Registry Report" as part of the
standard passive test suite.

The closeout script now includes "Test: Registry Report CLI" as part of the
standard passive test suite.

The closeout script now includes "Test: Passive CLI" as part of the standard
passive test suite.

The latest clean closeout confirmed that scaffold, validation, inspection,
preview, audit, profile lookup, scene lookup, command lookup, registry,
registry report, registry report CLI, and passive CLI tests passed silently; the
V1.34 reference diff was empty; and git status was clean.

The passive CLI help contract includes:

- rytm_randomizer/cli.py
- tests/test_cli.py
- tests/fixtures/cli_help_expected.txt
- tests/fixtures/cli_report_help_expected.txt

The help contract adds deterministic tested help and usage output for the
passive CLI. It locks down top-level help with
`python -m rytm_randomizer.cli --help`, report command help with
`python -m rytm_randomizer.cli report --help`, and keeps report behavior
unchanged for `python -m rytm_randomizer.cli report`. Manual verification showed
top-level help prints passive CLI usage, report help prints passive report
usage, and report prints the passive registry report. Closeout already includes
passive CLI testing, so no closeout script update was needed for this milestone.

Current passive CLI commands:

- `python -m rytm_randomizer.cli --help`
- `python -m rytm_randomizer.cli report --help`
- `python -m rytm_randomizer.cli report`
- `python -m rytm_randomizer.cli inspect-command --help`
- `python -m rytm_randomizer.cli inspect-command <key>`
- `python -m rytm_randomizer.registry_report`

The passive CLI command inspection milestone includes:

- rytm_randomizer/cli.py
- tests/test_cli.py
- tests/fixtures/cli_help_expected.txt
- tests/fixtures/cli_inspect_command_help_expected.txt
- tests/fixtures/cli_inspect_command_known_expected.txt
- tests/fixtures/cli_inspect_command_unknown_expected.txt

The new passive CLI paths are:

```powershell
python -m rytm_randomizer.cli inspect-command <key>
python -m rytm_randomizer.cli inspect-command --help
```

Existing passive CLI paths continue to work:

```powershell
python -m rytm_randomizer.cli --help
python -m rytm_randomizer.cli report --help
python -m rytm_randomizer.cli report
python -m rytm_randomizer.registry_report
```

Manual verification showed:

- `python -m rytm_randomizer.cli --help` printed updated passive CLI help with
  report and inspect-command.
- `python -m rytm_randomizer.cli inspect-command --help` printed passive
  inspect-command usage.
- `python -m rytm_randomizer.cli inspect-command J` printed passive metadata:
  Command: J, Found: True, Type: print, Label: show 4-pad group layout,
  Executable: False, Scaffold only: True, and V1.34 reference command: True.
- `python -m rytm_randomizer.cli inspect-command DOES_NOT_EXIST` failed safely
  with: "Command metadata not found. No MIDI was sent. No command executed."

Inspect-command reads existing passive command metadata only. It does not call
handlers, add handlers, dispatch commands, execute commands, open MIDI ports,
send MIDI, write files, require hardware, or mutate runtime or hardware state.
Unknown or missing keys fail safely.

The passive report-only CLI entrypoint includes:

- rytm_randomizer/cli.py
- tests/test_cli.py
- Scripts/closeout_check.ps1

The new passive CLI command is:

```powershell
python -m rytm_randomizer.cli report
```

The existing passive module command remains:

```powershell
python -m rytm_randomizer.registry_report
```

Both commands print the same deterministic golden-format passive registry
report. Manual verification showed both commands report commands: 82, scenes:
14, and group_profiles: 4. The report confirms dispatches_commands: False,
executes_commands: False, mutates_hardware: False, opens_ports: False,
sends_midi: False, writes_sysex: False, and In-memory only: True. The report
command exits with code 0, importing the CLI prints nothing, and missing or
unknown arguments fail safely.

The passive registry report CLI preview includes:

- rytm_randomizer/registry_report.py
- tests/test_registry_report_cli.py
- Scripts/closeout_check.ps1

The user-facing passive command is:

```powershell
python -m rytm_randomizer.registry_report
```

The command prints the existing golden-format passive registry report to stdout
and exits with code 0. It prints nothing during import, writes no files, requires
no hardware, opens no MIDI ports, sends no MIDI, dispatches no commands,
executes no commands, and mutates no runtime or hardware state.

The passive registry report generator includes:

- rytm_randomizer/registry_report.py
- tests/test_registry_report.py

The registry report golden text contract includes:

- tests/test_registry_report.py
- tests/fixtures/registry_report_expected.txt

The golden text contract locks down the formatted passive registry report
output, adds snapshot-style golden text coverage, and ensures future CLI, UI,
and reporting work has a stable deterministic report structure. The test
normalizes line endings so Windows CRLF/LF differences do not cause false
failures. Closeout already includes registry report testing, so no duplicate
closeout entry was needed.

The passive report CLI preview plan includes:

- Docs/PASSIVE_REPORT_CLI_PREVIEW_PLAN.md

The plan is documentation-only and records baseline HEAD 0ae33ef before the
planning slice. It defines how a future read-only CLI preview/report command
could display the already-passive registry report without implementing a CLI.
Potential future command shapes include `python -m rytm_randomizer.registry_report`
or `python -m rytm_randomizer.cli report`, but no command is implemented or
approved by the plan.

The report generator sits on top of the unified passive registry view. It
generates in-memory, read-only report data for registry sections, per-section
item counts, known sections commands/scenes/group_profiles, passive safety
boundary summary, unsupported scope summary, and active behavior status. The
formatted report is intended for inspection, documentation, future UI, and
future CLI preview work only. It does not write report files, create a CLI
command, or print during import.

The unified passive registry view includes:

- rytm_randomizer/registry.py
- tests/test_registry.py

The registry currently exposes copied read-only views for these sections:

- commands
- scenes
- group_profiles

The registry is passive/read-only from the caller perspective. It returns copied
data, does not allow caller mutation of source metadata, and uses passive
not-found behavior for unknown sections or items. It is intended for inspection,
reporting, preview, documentation, and future UI work only.

The passive architecture summary includes:

- Docs/PASSIVE_ARCHITECTURE_SUMMARY.md

The summary documents the current passive scaffold, lookup helpers, closeout
suite, safety boundaries, and conditions required before any hardware-facing
layer.

The passive command lookup helper includes:

- rytm_randomizer/command_lookup.py
- tests/test_command_lookup.py

The helper is passive/read-only. It only reads existing COMMANDS metadata.
Returned metadata is copied to prevent source mutation, and unknown command
keys return passive not-found behavior. No execution/handler/callable fields are
exposed. Pads 5-12 remain absent.

The passive scene lookup helper includes:

- rytm_randomizer/scene_lookup.py
- tests/test_scene_lookup.py

The helper is passive/read-only. It only reads existing SCENE_COMMANDS
metadata. Returned metadata is copied to prevent source mutation, and unknown
scene keys return passive not-found behavior. Pads 5-12 remain absent.

The passive group profile lookup helper includes:

- rytm_randomizer/profile_lookup.py
- tests/test_profile_lookup.py

The helper is passive/read-only. It only looks up existing
GROUP_PROFILE_METADATA keys "2", "3", "4", and "5". Returned metadata is copied
to prevent source mutation, and unknown keys return passive not-found behavior.
Pads 5-12 remain absent.

The behavior-preserving extraction plan includes:

- Docs/BEHAVIOR_PRESERVING_EXTRACTION_PLAN.md

The plan defines the transition from passive scaffold/reporting work toward
future pure extraction slices while keeping runtime wiring and MIDI/hardware
behavior out of scope until separately approved.

The passive registry audit/report layer includes:

- rytm_randomizer/audit.py
- tests/test_audit.py

The audit layer is passive/read-only and returns registry reports only. Audit
reports include validation status, command count, category/type counts, scope
counts, pad counts, all_non_executable, all_scaffold_only, and the fixed safety
summary: "No MIDI would be sent. No command would execute."

tests/test_audit.py covers:

- real COMMANDS registry audit
- validation ok
- all_non_executable
- all_scaffold_only
- scene/group/pad scope counts
- Pads limited to 1-4 where present
- synthetic invalid registry validation errors
- source metadata is not mutated

The passive command preview/report layer includes:

- rytm_randomizer/preview.py
- tests/test_preview.py

The preview layer sits on top of passive inspection and returns dry-run command
reports only. It includes the fixed safety summary: "No MIDI would be sent. No
command would execute."

tests/test_preview.py covers:

- known scene command
- group command
- pad command
- unknown command
- synthetic invalid registry validation errors
- metadata/report safety behavior

The passive command inspection layer includes:

- rytm_randomizer/inspection.py
- tests/test_inspection.py

inspect_command() returns a dry-run report only. It deep-copies metadata so
reports cannot mutate COMMANDS, calls the passive validator, and does not
dispatch, execute, send MIDI, read input, mutate state, or touch hardware.

tests/test_inspection.py covers:

- known scene command S1A
- unknown command
- group command O
- pad command P3A
- synthetic invalid registry errors
- metadata copy isolation

The passive validation layer includes:

- rytm_randomizer/validation.py
- tests/test_validation.py

The validator is read-only/passive and validates command registry safety. It
checks for executable: True, forbidden execution fields, missing scaffold_only /
v134_reference_command flags, and forbidden Pads 5-12 references.

Passive metadata validation hardening:

- nested forbidden pad tests exposed and fixed a TypeError
- validation now handles nested containers before direct forbidden-pad membership checks
- tests/test_validation.py covers nested pad lists containing forbidden Pads 5-12
- tests/test_validation.py covers forbidden pad text such as Pad 5
- tests/test_validation.py covers forbidden pad scope metadata such as pad_5

Scaffold metadata tests now include PAD_PROFILES coverage:

- exact key set {1, 3}
- no Pads 5-12
- Pad 1 links to existing PAD_1_DEFAULT_PROFILE
- Pad 3 remains SY Raw
- Pad 3 uses existing PAD_3_SY_RAW_CC_MAP

Scaffold metadata tests now also cover constants:

- MACHINE_CC == 15
- PAD1_DEFAULT_HOME == "BD Hard"
- Pad 1 default profile remains aligned with PAD1_DEFAULT_HOME

Command metadata consistency now covers:

- MENU_COMMANDS protocol fields
- full passive SCENE_COMMANDS metadata preserved inside COMMANDS
- guarded main-prompt 1/2/3 protocol fields
- all applicable command metadata remains executable: False
- no forbidden execution fields or runtime hooks

All metadata registries are passive. They do not dispatch commands, send MIDI,
read input, open ports, mutate state, or call runtime functions.

V1.34 remains protected. No runtime execution, MIDI sending, input handling,
command dispatch, Pads 5-12 expansion, GUI, capture, SysEx, or Analog Four
work has been added.

The passive validation layer added no MIDI sending, command dispatch, input
handling, SysEx, capture/state, GUI, Analog Four, or hardware behavior.

The passive validation hardening added no MIDI, runtime dispatch, input
handling, hardware state changes, SysEx, capture, GUI, Analog Four, or Pads
5-12 support.

The passive inspection layer added no MIDI, runtime execution, dispatch, input
handling, SysEx, capture, GUI, Analog Four, or Pads 5-12 support.

The passive preview layer added no MIDI, port opening, live randomizer, command
execution, dispatch, input handling, state mutation, SysEx, capture, GUI,
Analog Four, Pads 5-12 support, mutation behavior, handlers/callables, or
runtime hooks.

The passive audit layer added no MIDI, port opening, live randomizer, command
execution, dispatch, input handling, state mutation, SysEx, capture, GUI,
Analog Four, Pads 5-12 support, mutation behavior, handlers/callables, or
runtime hooks.

The passive group profile lookup helper added no MIDI, ports, dispatch,
hardware mutation, SysEx, GUI, capture, Analog Four, or Pads 5-12 support.

The passive scene lookup helper added no MIDI, ports, dispatch, command
execution, hardware mutation, SysEx, GUI, capture, Analog Four, or Pads 5-12
support.

The passive command lookup helper added no MIDI, ports, dispatch, command
execution, hardware mutation, SysEx, GUI, capture, Analog Four, or Pads 5-12
support.

The passive architecture summary added no MIDI, ports, dispatch, command
execution, hardware mutation, SysEx, GUI, capture, Analog Four, or Pads 5-12
support.

The unified passive registry view added no MIDI sending, port opening,
dispatch, command execution, hardware mutation, SysEx, GUI, capture, Analog Four
support, or Pads 5-12 support. The protected V1.34 reference remains untouched.

The passive registry report generator added no MIDI sending, port opening,
dispatch, command execution, hardware mutation, SysEx, GUI, capture, Analog Four
support, Pads 5-12 support, or machine/profile universe expansion. The
protected V1.34 reference remains untouched.

The registry report golden text contract was test-only/passive hardening. It
added no CLI behavior, report file writing at runtime, import-time printing,
MIDI sending, port opening, dispatch, command execution, hardware mutation,
SysEx, GUI, capture, Analog Four support, Pads 5-12 support, or machine/profile
universe expansion. The protected V1.34 reference remains untouched.

The passive report CLI preview plan added no code, tests, CLI behavior, runtime
behavior, MIDI sending, port opening, dispatch, command execution, hardware
mutation, SysEx, GUI, capture, Analog Four support, Pads 5-12 support, or
machine/profile universe expansion. The protected V1.34 reference remains
untouched.

The passive registry report CLI preview added no MIDI sending, port opening,
dispatch, command execution, hardware mutation, SysEx, GUI, capture, Analog Four
support, Pads 5-12 support, or machine/profile universe expansion. The
protected V1.34 reference remains untouched. Analog Rytm and Analog Four are
not needed and should remain off for this phase.

The passive report-only CLI entrypoint added no MIDI sending, port opening,
dispatch, command execution, hardware mutation, SysEx, GUI, capture, Analog Four
support, Pads 5-12 support, or machine/profile universe expansion. It writes no
report files, requires no hardware, mutates no runtime or hardware state, and
leaves the protected V1.34 reference untouched. Analog Rytm and Analog Four
remain off for this phase.

The passive CLI help contract added no new functional commands, MIDI sending,
port opening, dispatch, command execution, hardware mutation, SysEx, GUI,
capture, Analog Four support, Pads 5-12 support, or machine/profile universe
expansion. It added no report file writing at runtime and no import-time
printing. The protected V1.34 reference remains untouched. Analog Rytm and
Analog Four remain off for this phase.

The passive CLI command inspection milestone added no MIDI sending, port
opening, dispatch, command execution, hardware mutation, SysEx, GUI, capture,
Analog Four support, Pads 5-12 support, or machine/profile universe expansion.
It added no report file writing at runtime and no import-time printing. The
protected V1.34 reference remains untouched. Analog Rytm and Analog Four remain
off for this phase.

## Validated Rytm Scope

Current validated system focuses on Analog Rytm MKII Pads 1-4.

- Pad 1 = main kick / BD engine lane
- Pad 2 = secondary percussion / snare lane
- Pad 3 = SY Raw bass / synth-percussion lane
- Pad 4 = BD Acoustic body / accent lane

## Validated Scene Layer

V1.34 includes the expanded scene system:

- S1A = Rolling Light
- S1B = Rolling Push
- S2A = Deeper Groove
- S2B = Deeper Pressure
- S3A = Intense Motion
- S3B = Intense Grit
- S4A = Wild Controlled
- S4B = Wild Maximum
- S5 = return to clean anchors

## Permanent Safety Principle

Load anchors remain permanent.

Capture features may be added later, but capture does not replace validated anchors.

Validated anchors remain the safety net.

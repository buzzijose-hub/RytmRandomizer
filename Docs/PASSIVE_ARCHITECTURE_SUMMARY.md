# RytmRandomizer Passive Architecture Summary

Date: May 4, 2026

Current branch:

modularize-v1.34

Current HEAD:

75a2afd

## Protected Reference

`rytm_hybrid_randomizer_v134.py` remains the protected V1.34 behavior
reference. It must not be edited during passive scaffold, lookup, reporting, or
documentation work.

## Current Closeout Suite

The standard closeout suite currently includes:

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
- mock MIDI
- mock message mapper
- mock mapper report

The closeout workflow also checks:

- `git diff -- rytm_hybrid_randomizer_v134.py`
- `git status --short`

## Next Action Handoff

`Docs/NEXT_ACTION.md` records the current session handoff for future sessions.

It captures:

- current branch: modularize-v1.34
- current HEAD: 75a2afd Add future active test plan review
- current phase: passive CLI / dry-run foundation
- current safety state
- hardware-off reminder
- current passive CLI capability
- known safe passive commands
- next recommended task: roadmap review/acceptance
- closeout command
- stop condition

The handoff is for clean session resumption, safety state recall, next-task
orientation, and hardware-off reminders. It adds no runtime behavior and does
not expand project scope.

## Passive-To-Active Boundary Design

`Docs/PASSIVE_TO_ACTIVE_BOUNDARY.md` defines the future boundary between the
current passive CLI/dry-run foundation and any later hardware-facing execution
layer.

It records:

- current passive foundation
- strict current safety boundary
- future active layer concept
- required preconditions before any hardware-facing test
- proposed future command model as design only
- arming model
- early hardware-phase forbidden actions
- testing requirements
- operator checklist before turning hardware on

The boundary document preserves passive CLI behavior, keeps hardware off for
the current phase, and documents preconditions before any future MIDI/hardware
test. It is documentation-only and adds no runtime behavior.

## Passive-To-Active Boundary Review

`Docs/PASSIVE_TO_ACTIVE_BOUNDARY_REVIEW.md` records the review/acceptance
checkpoint for the passive-to-active boundary.

It confirms:

- `Docs/PASSIVE_TO_ACTIVE_BOUNDARY.md` is accepted as the current planning boundary
- the project remains passive/read-only
- no active or hardware-facing behavior exists yet
- passive commands must never accidentally reach hardware execution
- future active execution must require explicit operator intent and arming
- the next recommended task is active-layer design/spec only
- hardware remains off

The review is documentation-only and adds no runtime behavior.

## Passive Mock MIDI Progress Checkpoint

`Docs/PASSIVE_MOCK_MIDI_PROGRESS_CHECKPOINT.md` records a progress checkpoint
after the passive CLI, test-only mock MIDI scaffold, test-only mock message
mapper, and mapper review milestones.

It summarizes:

- current branch and HEAD
- current passive CLI capability
- current mock MIDI capability
- current mock message mapper capability
- closeout suite coverage
- confirmed safety boundaries
- safe next decision options

The checkpoint records this as a clean decision point before any additional
mapper scope, active execution, or hardware-facing work.

It is documentation-only and adds no runtime behavior.

## Test-Only Mock Message Mapper

The test-only mock message mapper milestone is:

- 4a590c8 Add test-only mock message mapper

It includes:

- `rytm_randomizer/mock_message_mapper.py`
- `tests/test_mock_message_mapper.py`
- `Scripts/closeout_check.ps1`

It adds a mock-only mapper from existing passive group profile metadata to
inert mock MidiMessage objects.

Current behavior:

- supports group profile key `"2"` / My BD Hard
- supports group profile key `"3"` / My BD Classic
- keeps group profile key `"4"` unsupported with safe failure behavior
- returns deterministic mock message data
- uses the existing `mock_midi.py` scaffold
- records cleanly through MockMidiSender
- fails safely for unknown or unsupported keys
- is not wired into CLI
- is not wired into runtime execution
- imports no real MIDI library
- opens no ports
- sends no MIDI
- adds no active behavior
- adds no hardware behavior

The closeout suite now includes "Test: Mock Message Mapper".

Analog Rytm and Analog Four remain off for this phase.

## Mock Mapper Profile 3 Progress Checkpoint

`Docs/MOCK_MAPPER_PROFILE_3_PROGRESS_CHECKPOINT.md` records a progress
checkpoint after adding and documenting test-only mock mapping support for
group profile key `"3"` / My BD Classic.

It summarizes:

- current branch and HEAD
- supported mock mapper profiles `"2"` and `"3"`
- group profile `"4"` remaining intentionally unsupported and safe
- current mapper behavior
- current safety boundaries
- the next decision point

The checkpoint records that no next mapper expansion is approved yet.

It is documentation-only and adds no runtime behavior.

## Mock Mapper Profile 4 Decision Note

`Docs/MOCK_MAPPER_PROFILE_4_DECISION_NOTE.md` records the decision for
existing group profile `"4"` / My BD Acoustic before any mapper expansion.

Current decision:

- profile `"4"` / My BD Acoustic remains unsupported for now
- no profile 4 mapping is implemented
- future profile 4 support requires explicit approval as a tiny mock-only expansion

The decision note keeps the project at a safe planning boundary before any
additional mapper scope.

It is documentation-only and adds no runtime behavior.

## Mock Mapper Progress Review

`Docs/MOCK_MAPPER_PROGRESS_REVIEW.md` records the current mock mapper boundary
after the profile 4 decision note.

It summarizes:

- profiles `"2"` / My BD Hard and `"3"` / My BD Classic are supported
- profile `"4"` / My BD Acoustic remains unsupported/safe
- profile `"4"` requires separate approval before any mock-only expansion
- Mock MIDI and Mock Message Mapper tests are part of closeout
- no implementation is added in the progress review

The original next options were:

- keep mapper scope frozen
- plan profile 4 mock-only support
- build a passive mock mapper report/summary layer, now completed by `f7c14f2`
- pause mapper work

The review is documentation-only and adds no runtime behavior.

## Passive Mock Mapper Report

The passive mock mapper report milestone is:

- f7c14f2 Add passive mock mapper report

It includes:

- `rytm_randomizer/mock_mapper_report.py`
- `tests/test_mock_mapper_report.py`
- `Scripts/closeout_check.ps1`

It adds a read-only, in-memory report for the current test-only mock mapper
support state.

Current report boundary:

- supported mock mapper profiles: `"2"` / My BD Hard and `"3"` / My BD Classic
- unsupported/safe profile: `"4"` / My BD Acoustic
- mock-only status: true
- real MIDI: absent
- port opening: absent
- CLI wiring: absent
- active behavior: absent
- hardware required: false
- Analog Four support: absent
- Pads 5-12 support: absent

The closeout suite now includes "Test: Mock Mapper Report".

The report does not add CLI wiring, real MIDI, mido, MIDI ports, MIDI sending,
active execution, dispatch, hardware behavior, SysEx, GUI/capture, Analog Four
support, Pads 5-12 support, or machine/profile expansion.

Analog Rytm and Analog Four remain off for this phase.

## Passive Mock Mapper Report CLI Preview

The passive mock mapper report CLI preview milestone is:

- 19659e5 Add passive mock mapper report CLI preview

It includes:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_mock_mapper_report_help_expected.txt`
- `tests/fixtures/cli_mock_mapper_report_expected.txt`

It adds these read-only passive CLI paths:

- `python -m rytm_randomizer.cli mock-mapper-report`
- `python -m rytm_randomizer.cli mock-mapper-report --help`

The command prints the existing formatted passive mock mapper report only.
Manual verification confirmed:

- top-level help lists `mock-mapper-report`
- command help prints passive/mock-only usage
- command output shows profiles `"2"` and `"3"` supported
- command output shows profile `"4"` unsupported/safe

It does not wire CLI to the mapper itself, invoke active execution, open ports,
send MIDI, require hardware, add profile 4 support, or add active behavior.

Analog Rytm and Analog Four remain off for this phase.

## Passive Mock Mapper CLI Preview Phase Review

`Docs/PASSIVE_MOCK_MAPPER_CLI_PREVIEW_PHASE_REVIEW.md` records the end-of-phase
checkpoint for the passive mock mapper CLI preview work.

It confirms:

- passive CLI visibility includes report, list, search, inspect, preview, and mock-mapper-report
- mock MIDI scaffold is complete and test-only/inert
- mock message mapper is complete for supported profiles
- mock mapper report is complete
- mock mapper report CLI preview is complete
- profiles `"2"` / My BD Hard and `"3"` / My BD Classic are supported
- profile `"4"` / My BD Acoustic remains unsupported/safe
- real MIDI, mido, ports, MIDI sending, active execution, CLI wiring to the mapper itself, dispatch, hardware behavior, SysEx, GUI/capture, Analog Four, Pads 5-12, machine/profile expansion, execute-command, send-command, and hardware-test remain absent
- hardware remains off

Safe next branches are freezing scope, creating a profile 4 plan, writing a
broader project milestone report, drafting a future active test-plan document,
or creating a mock-only active command test plan with no real MIDI and no
hardware.

The review is documentation-only and adds no runtime behavior.

## Passive Mock Foundation Progress Report

`Docs/PASSIVE_MOCK_FOUNDATION_PROGRESS_REPORT.md` consolidates the full current
passive/mock foundation in one place before any future active test-plan work.

It records:

- passive CLI foundation complete enough for report/list/search/inspect/preview
- mock MIDI scaffold complete and test-only/inert
- mock message mapper complete for profiles `"2"` and `"3"`
- profile `"4"` / My BD Acoustic unsupported/safe
- mock mapper report complete
- mock mapper report CLI preview complete
- real MIDI absent
- mido absent
- ports absent
- active behavior absent
- hardware off and not required

The report documents current closeout coverage, guardrails, intentionally
absent scope, and safe next branches. Its recommendation is to create a
docs-only future active test-plan document next. It is documentation-only and
adds no runtime behavior.

## Future Active Test Plan

`Docs/FUTURE_ACTIVE_TEST_PLAN.md` defines what must be proven before any
active/hardware-facing behavior can be implemented or validated.

It records:

- mock-only proof requirements before implementation
- passive commands that must remain read-only
- future meaning of armed mode as a concept only
- first real-hardware candidate constraints without selecting a final candidate
- required pre-hardware checklist
- exact stop conditions
- forbidden first-active scope
- required future test categories
- hardware-off requirement

The test-plan adds no implementation, active CLI command, MIDI code, port
opening, hardware validation, execution, dispatch, SysEx, GUI/capture, Analog
Four support, Pads 5-12 support, or profile 4 implementation. Its next
recommended task is review/acceptance of the test plan.

## Future Active Test Plan Review

`Docs/FUTURE_ACTIVE_TEST_PLAN_REVIEW.md` accepts
`Docs/FUTURE_ACTIVE_TEST_PLAN.md` as the current planning gate.

It confirms:

- the plan remains documentation-only
- no implementation exists
- the plan does not authorize hardware being turned on by itself
- no real MIDI, mido, ports, MIDI sending, active execution, CLI wiring to active behavior, dispatch, hardware behavior, SysEx, GUI/capture, Analog Four support, Pads 5-12 support, machine/profile expansion, execute-command, send-command, hardware-test, or hardware validation exists
- passive commands remain read-only
- hardware remains off

Safe next options are pausing, writing a broader roadmap/timeline update,
creating a first-candidate mock-only active test design document, adding more
mock-only safety tests after a separate approved design, or returning to
passive/project documentation.

## Passive Mock Foundation Roadmap

`Docs/PASSIVE_MOCK_FOUNDATION_ROADMAP.md` records the current roadmap/timeline
after the passive/mock foundation work.

It names the current phase:

- Passive/Mock Foundation Phase

It confirms:

- the phase is complete enough for future planning
- the phase does not include real MIDI
- the phase does not include active execution
- the phase does not include hardware validation
- group profiles `"2"` and `"3"` are supported in the mock mapper
- group profile `"4"` / My BD Acoustic remains parked as unsupported/safe
- roadmap review/acceptance is the next recommended gate

The roadmap lists next planning gates through first-candidate mock-only active
test design, mock-only active candidate tests, later active boundary review,
later real MIDI boundary design, later hardware validation checklist, and much
later real hardware validation only after explicit approval. It is
documentation-only and adds no runtime behavior.

## Passive Mock Foundation Decision Checkpoint

`Docs/PASSIVE_MOCK_FOUNDATION_DECISION_CHECKPOINT.md` records the current
passive/mock foundation decision point after the passive mock mapper report
checkpoint.

It summarizes:

- passive CLI foundation complete enough for report/list/search/inspect/preview
- passive registry/report layer
- test-only mock MIDI scaffold
- test-only mock message mapper
- passive mock mapper report
- closeout coverage for Mock MIDI, Mock Message Mapper, and Mock Mapper Report
- supported mock mapper profiles `"2"` / My BD Hard and `"3"` / My BD Classic
- unsupported/safe profile `"4"` / My BD Acoustic
- intentionally absent real MIDI, mido, ports, MIDI sending, active execution, CLI wiring, dispatch, hardware behavior, SysEx, GUI/capture, Analog Four, Pads 5-12, machine/profile expansion, execute-command, send-command, and hardware-test

Safe next branches are:

- freeze mock mapper scope here and stop/pause
- create a profile 4 mock-only support plan, not implementation
- build a passive mock mapper report CLI preview, now completed by `19659e5`
- write a larger project progress report, now completed by `Docs/PASSIVE_MOCK_FOUNDATION_PROGRESS_REPORT.md`
- create a docs-only future active test-plan document

The checkpoint is documentation-only and adds no runtime behavior.

## Test-Only Mock Mapping For Group Profile 3

The test-only mock mapping for group profile 3 milestone is:

- 4507647 Add mock mapping for group profile 3

It includes:

- `rytm_randomizer/mock_message_mapper.py`
- `tests/test_mock_message_mapper.py`

It adds support for existing group profile key `"3"` / My BD Classic in the
test-only mock mapper.

Current behavior:

- existing group profile key `"2"` / My BD Hard behavior remains unchanged
- group profile key `"3"` / My BD Classic maps to deterministic inert mock MidiMessage data
- group profile key `"4"` remains unsupported and fails safely
- mapped messages record cleanly through MockMidiSender
- the mapper is not wired into CLI
- the mapper is not wired into runtime execution
- the mapper imports no real MIDI library
- the mapper opens no ports
- the mapper sends no MIDI
- the mapper adds no active behavior
- the mapper adds no hardware behavior

Analog Rytm and Analog Four remain off for this phase.

## Mock Message Mapper Review

`Docs/MOCK_MESSAGE_MAPPER_REVIEW.md` records the review/acceptance checkpoint
for the test-only mock message mapper.

It confirms:

- `rytm_randomizer/mock_message_mapper.py` is accepted as the current test-only mapper scaffold
- `tests/test_mock_message_mapper.py` is accepted as current test coverage
- the mapper supports group profile keys `"2"` / My BD Hard and `"3"` / My BD Classic
- group profile key `"4"` remains unsupported and fails safely
- the mapper returns deterministic inert MidiMessage data
- the mapper records through MockMidiSender
- the mapper fails safely for unknown or unsupported keys
- the mapper is not wired into CLI or runtime execution
- the mapper imports no real MIDI library
- the mapper opens no ports
- the mapper sends no MIDI
- the mapper adds no hardware behavior
- future mapper expansion must remain mock-only unless separately reviewed
- hardware remains off

The review is documentation-only and adds no runtime behavior.

## Mock Message Mapping Design Spec

`Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md` defines future mock-only mapping
from passive metadata to mock MidiMessage objects.

It records:

- current passive/mock pieces
- mapping concept
- group profile metadata as the preferred first mapping source
- group profile key 2 / My BD Hard as the likely first mock-only candidate
- conceptual output metadata for a future mock message
- required safeguards
- scope that must not be mapped yet
- proposed future module shape as design only
- proposed future tests
- relationship to the unimplemented active layer
- stop conditions

The spec keeps hardware off, keeps real MIDI absent, and sets the next
recommended task as review/acceptance before any mapper scaffold. It is
documentation-only and adds no runtime behavior.

## Mock Message Mapping Design Spec Review

`Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC_REVIEW.md` records the
review/acceptance checkpoint for the mock message mapping design/spec.

It confirms:

- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md` is accepted as the current planning spec
- the project remains passive/mock-only
- no mapper implementation exists yet
- no real MIDI, active execution, port opening, or hardware-facing behavior exists
- future mapping must remain mock-only first
- group profile 2 / My BD Hard is the first likely mock-only candidate
- the next recommended task is a tiny test-only mock mapper scaffold for group profile 2 only
- hardware remains off

The review is documentation-only and adds no runtime behavior.

## Test-Only Mock MIDI Scaffold

The test-only mock MIDI scaffold includes:

- `rytm_randomizer/mock_midi.py`
- `tests/test_mock_midi.py`
- `Scripts/closeout_check.ps1`

It adds:

- mock-only/test-only MIDI-like message representation
- MockMidiSender that records intended messages in memory only
- direct-runnable tests for import safety, message representation, sender recording, ordering, clearing, metadata isolation, no real MIDI imports, passive CLI preservation, no out-of-scope support, and no active behavior names
- closeout coverage under "Test: Mock MIDI"

It does not add:

- real MIDI backend
- real MIDI library import
- mido dependency
- port provider
- hardware detection
- hardware send
- active CLI command
- execute-command
- send-command
- hardware-test command
- dispatch
- execution
- hardware mutation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion

Analog Rytm and Analog Four remain off for this phase.

## Mock MIDI Scaffold Review

`Docs/MOCK_MIDI_SCAFFOLD_REVIEW.md` records the review/acceptance checkpoint
for the test-only mock MIDI scaffold.

It confirms:

- `rytm_randomizer/mock_midi.py` is accepted as the current test-only mock MIDI scaffold
- `tests/test_mock_midi.py` is accepted as the current mock MIDI test coverage
- mock MIDI remains in-memory only
- no real MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- mock MIDI is not wired to CLI or active execution
- the test-only mock message mapper now supports group profiles 2 / My BD Hard and 3 / My BD Classic
- the closeout suite includes Mock Message Mapper and Mock Mapper Report
- hardware remains off

The review is documentation-only and adds no runtime behavior.

## Mock MIDI Boundary Test Plan

`Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN.md` defines the future mock MIDI boundary
before implementation.

It records:

- mock MIDI boundary concept
- proposed conceptual interfaces as design only
- test-only design rules
- future message verification expectations
- arming and mock execution checks
- passive-to-active separation
- first mock test candidate constraints
- forbidden scope for this phase
- future closeout expectations
- hardware-off reminder

The plan keeps all MIDI behavior test-only and mockable, prevents real port
opening in tests, and keeps hardware off. It is documentation-only and adds no
runtime behavior.

## Mock MIDI Boundary Test Plan Review

`Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN_REVIEW.md` records the review/acceptance
checkpoint for the mock MIDI boundary test plan.

It confirms:

- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN.md` is accepted as the current mock MIDI testing plan
- the project remains passive/read-only
- no mock MIDI code, real MIDI code, active execution, or hardware-facing behavior exists yet
- future MIDI behavior must be mockable before any real port opening exists
- unit tests must never open real MIDI ports
- passive CLI commands must remain read-only and separate from MIDI senders
- the next recommended task is test-only mock MIDI scaffold/design
- hardware remains off

The review is documentation-only and adds no runtime behavior.

## Active-Layer Design Spec

`Docs/ACTIVE_LAYER_DESIGN_SPEC.md` designs the future active/hardware-facing
layer without implementation.

It preserves passive behavior, keeps hardware off, and defines:

- active layer non-negotiables
- proposed active-layer architecture
- mockable MIDI boundary
- arming model
- first active test candidate constraints
- forbidden early active scope
- possible future active CLI names as design only
- required tests before implementation
- operator checklist before first hardware validation
- stop conditions

The spec is documentation-only. It adds no MIDI code, port opening, active CLI
command, dispatch, execution, hardware testing, GUI, capture, Analog Four
support, Pads 5-12 support, or machine/profile universe expansion.

## Active-Layer Design Spec Review

`Docs/ACTIVE_LAYER_DESIGN_SPEC_REVIEW.md` records the review/acceptance
checkpoint for the active-layer design/spec.

It confirms:

- `Docs/ACTIVE_LAYER_DESIGN_SPEC.md` is accepted as the current planning spec
- the project remains passive/read-only
- no active or hardware-facing behavior exists yet
- future active behavior must remain behind an explicit boundary
- future active behavior must require explicit operator intent, arming, target confirmation, and mockable MIDI testing before real hardware validation
- the next recommended task is mock MIDI boundary planning/test-only design
- hardware remains off

The review is documentation-only and adds no runtime behavior.

## Passive Lookup Helpers

Current passive lookup helpers:

- `rytm_randomizer/profile_lookup.py`
- `rytm_randomizer/scene_lookup.py`
- `rytm_randomizer/command_lookup.py`

## Unified Passive Registry View

`rytm_randomizer/registry.py` exposes a unified read-only registry view over the
currently scaffolded passive metadata surfaces.

Current registry sections:

- commands
- scenes
- group_profiles

It exposes:

- copied registry data
- copied section data
- copied item metadata
- passive not-found behavior for unknown sections
- passive not-found behavior for unknown items
- a passive section/count summary

It is intended for:

- inspection
- reporting
- preview
- documentation
- future UI work

It does not:

- execute commands
- dispatch commands
- send MIDI
- open ports
- mutate state or hardware
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support

The registry view returns copied data so callers cannot mutate source metadata.

## Passive Registry Report Generator

`rytm_randomizer/registry_report.py` sits on top of the unified passive registry
view and generates in-memory, read-only report data.

It reports:

- registry sections
- per-section item counts
- known sections: commands, scenes, group_profiles
- passive safety boundary summary
- unsupported scope summary
- active behavior status

The formatted report is intended for:

- inspection
- documentation
- future UI work
- future CLI preview work

It does not:

- write report files
- create a CLI command
- print during import
- execute commands
- dispatch commands
- send MIDI
- open ports
- mutate state or hardware
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

### Passive Registry Report CLI Preview

The passive registry report CLI preview adds the first user-facing read-only
command for displaying the passive registry report:

```powershell
python -m rytm_randomizer.registry_report
```

It uses:

- `rytm_randomizer/registry_report.py`
- `tests/test_registry_report_cli.py`
- `Scripts/closeout_check.ps1`

It does:

- print the existing golden-format passive registry report to stdout
- exit with code 0
- preserve the registry report golden text contract
- require no hardware

It does not:

- print during import
- write report files
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four are not needed and should remain off for this phase.

### Passive Report-Only CLI Entrypoint

The passive report-only CLI entrypoint adds a minimal report command:

```powershell
python -m rytm_randomizer.cli report
```

The existing passive module command remains:

```powershell
python -m rytm_randomizer.registry_report
```

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `Scripts/closeout_check.ps1`

Both commands print the same deterministic golden-format passive registry
report. Manual verification showed both commands report:

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

It does:

- exit with code 0 for `report`
- print nothing during import
- fail safely for missing or unknown arguments
- require no hardware

It does not:

- write report files
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Help Contract

The passive CLI help contract adds deterministic tested help and usage output
for the passive CLI.

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_report_help_expected.txt`

Current passive CLI commands:

- `python -m rytm_randomizer.cli --help`
- `python -m rytm_randomizer.cli report --help`
- `python -m rytm_randomizer.cli report`
- `python -m rytm_randomizer.cli inspect-command --help`
- `python -m rytm_randomizer.cli inspect-command <key>`
- `python -m rytm_randomizer.cli inspect-scene --help`
- `python -m rytm_randomizer.cli inspect-scene <key>`
- `python -m rytm_randomizer.cli inspect-group-profile --help`
- `python -m rytm_randomizer.cli inspect-group-profile <key>`
- `python -m rytm_randomizer.cli list-commands`
- `python -m rytm_randomizer.cli list-scenes`
- `python -m rytm_randomizer.cli list-group-profiles`
- `python -m rytm_randomizer.cli search-commands <query>`
- `python -m rytm_randomizer.cli search-scenes <query>`
- `python -m rytm_randomizer.cli search-group-profiles <query>`
- `python -m rytm_randomizer.cli preview-command --help`
- `python -m rytm_randomizer.cli preview-command <key>`
- `python -m rytm_randomizer.cli preview-scene --help`
- `python -m rytm_randomizer.cli preview-scene <key>`
- `python -m rytm_randomizer.cli preview-group-profile --help`
- `python -m rytm_randomizer.cli preview-group-profile <key>`
- `python -m rytm_randomizer.registry_report`

It locks down:

- top-level passive CLI usage
- report command passive usage
- unchanged report output behavior
- deterministic help text fixtures

Manual verification showed:

- top-level help prints passive CLI usage
- report help prints passive report usage
- report prints the passive registry report

Closeout already includes passive CLI testing, so no closeout script update was
needed for this milestone.

It does not:

- add new functional commands
- write report files at runtime
- print during import
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Command Inspection

The passive CLI command inspection milestone adds a read-only command metadata
inspection path:

```powershell
python -m rytm_randomizer.cli inspect-command <key>
python -m rytm_randomizer.cli inspect-command --help
```

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_inspect_command_help_expected.txt`
- `tests/fixtures/cli_inspect_command_known_expected.txt`
- `tests/fixtures/cli_inspect_command_unknown_expected.txt`

It does:

- read existing passive command metadata only
- display deterministic human-readable metadata for known command keys
- fail safely for unknown or missing keys
- preserve existing passive CLI report behavior
- require no hardware

Manual verification showed:

- top-level help prints report and inspect-command.
- inspect-command help prints passive inspect-command usage.
- `python -m rytm_randomizer.cli inspect-command J` prints Command: J, Found:
  True, Type: print, Label: show 4-pad group layout, Executable: False,
  Scaffold only: True, and V1.34 reference command: True.
- `python -m rytm_randomizer.cli inspect-command DOES_NOT_EXIST` fails safely
  with: "Command metadata not found. No MIDI was sent. No command executed."

It does not:

- call handlers
- add handlers
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- write files
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Scene Inspection

The passive CLI scene inspection milestone adds a read-only scene metadata
inspection path:

```powershell
python -m rytm_randomizer.cli inspect-scene <key>
python -m rytm_randomizer.cli inspect-scene --help
```

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_inspect_scene_help_expected.txt`
- `tests/fixtures/cli_inspect_scene_known_expected.txt`
- `tests/fixtures/cli_inspect_scene_unknown_expected.txt`

It does:

- read existing passive scene metadata only
- display deterministic human-readable metadata for known scene keys
- fail safely for unknown or missing keys
- preserve existing passive CLI report and inspect-command behavior
- require no hardware

Manual verification showed:

- top-level help prints report, inspect-command, and inspect-scene.
- inspect-scene help prints passive inspect-scene usage.
- `python -m rytm_randomizer.cli inspect-scene S1A` prints Scene: S1A, Found:
  True, Name: Rolling Light, Description: Lower-risk rolling movement for
  subtle live variation, Action: rolling_light, Scope: four_pad_group,
  Executable: False, Scaffold only: True, and V1.34 reference command: True.
- `python -m rytm_randomizer.cli inspect-scene DOES_NOT_EXIST` fails safely
  with: "Scene metadata not found. No MIDI was sent. No command executed."

It does not:

- call handlers
- add handlers
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- write files
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Group Profile Inspection

The passive CLI group profile inspection milestone adds a read-only group
profile metadata inspection path:

```powershell
python -m rytm_randomizer.cli inspect-group-profile <key>
python -m rytm_randomizer.cli inspect-group-profile --help
```

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_inspect_group_profile_help_expected.txt`
- `tests/fixtures/cli_inspect_group_profile_known_expected.txt`
- `tests/fixtures/cli_inspect_group_profile_unknown_expected.txt`

It does:

- read existing passive group profile metadata only
- display deterministic human-readable metadata for known group profile keys
- fail safely for unknown or missing keys
- preserve existing passive CLI report, inspect-command, and inspect-scene behavior
- require no hardware

Manual verification showed:

- top-level help prints report, inspect-command, inspect-scene, and
  inspect-group-profile.
- inspect-group-profile help prints passive inspect-group-profile usage.
- `python -m rytm_randomizer.cli inspect-group-profile 2` prints Group profile:
  2, Found: True, Name: My BD Hard, Machine value: 0, and Group pad: 1.
- `python -m rytm_randomizer.cli inspect-group-profile DOES_NOT_EXIST` fails
  safely with: "Group profile metadata not found. No MIDI was sent. No command
  executed."

CLI inspection coverage now includes:

- passive command inspection
- passive scene inspection
- passive group profile inspection

It does not:

- call handlers
- add handlers
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- write files
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI List Commands

The passive CLI list commands milestone adds read-only registry browsing paths:

```powershell
python -m rytm_randomizer.cli list-commands
python -m rytm_randomizer.cli list-scenes
python -m rytm_randomizer.cli list-group-profiles
```

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_list_commands_help_expected.txt`
- `tests/fixtures/cli_list_commands_expected.txt`
- `tests/fixtures/cli_list_scenes_help_expected.txt`
- `tests/fixtures/cli_list_scenes_expected.txt`
- `tests/fixtures/cli_list_group_profiles_help_expected.txt`
- `tests/fixtures/cli_list_group_profiles_expected.txt`

It does:

- read existing passive registry metadata only
- list existing passive command keys and labels
- list existing passive scene keys and names
- list existing passive group profile keys and names
- preserve existing passive report and inspect behavior
- require no hardware

Manual verification showed:

- top-level help prints report, inspect-command, inspect-scene,
  inspect-group-profile, list-commands, list-scenes, and list-group-profiles.
- `python -m rytm_randomizer.cli list-commands` prints 82 passive command keys
  and labels.
- `python -m rytm_randomizer.cli list-scenes` prints 14 passive scene keys and
  names.
- `python -m rytm_randomizer.cli list-group-profiles` prints 4 passive group
  profile keys and names: 2: My BD Hard, 3: My BD Classic, 4: My BD Acoustic,
  and 5: Pad 3 SY Raw Mid Bass.

It does not:

- call handlers
- add handlers
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- write files
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Search Commands

The passive CLI search commands milestone adds read-only registry search paths:

```powershell
python -m rytm_randomizer.cli search-commands <query>
python -m rytm_randomizer.cli search-scenes <query>
python -m rytm_randomizer.cli search-group-profiles <query>
```

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_search_commands_help_expected.txt`
- `tests/fixtures/cli_search_commands_known_expected.txt`
- `tests/fixtures/cli_search_commands_none_expected.txt`
- `tests/fixtures/cli_search_scenes_help_expected.txt`
- `tests/fixtures/cli_search_scenes_known_expected.txt`
- `tests/fixtures/cli_search_scenes_none_expected.txt`
- `tests/fixtures/cli_search_group_profiles_help_expected.txt`
- `tests/fixtures/cli_search_group_profiles_known_expected.txt`
- `tests/fixtures/cli_search_group_profiles_none_expected.txt`

It does:

- read copied passive registry metadata only
- search commands, scenes, and group profiles case-insensitively
- produce deterministic human-readable match lists
- return passive no-match output safely
- preserve existing passive report, inspect, and list behavior
- require no hardware

Manual verification showed:

- top-level help prints the passive search commands.
- `python -m rytm_randomizer.cli search-commands BD` returns 29 passive command
  matches.
- `python -m rytm_randomizer.cli search-commands Pad` returns 72 passive
  command matches.
- `python -m rytm_randomizer.cli search-scenes Wild` returns 3 passive scene
  matches: S4: Wild, S4A: Wild Controlled, and S4B: Wild Maximum.
- `python -m rytm_randomizer.cli search-group-profiles Hard` returns 2: My BD
  Hard.
- `python -m rytm_randomizer.cli search-commands DOES_NOT_EXIST` returns:
  "no matches found. No MIDI was sent. No command executed."

It does not:

- call handlers
- add handlers
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- write files
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Command Preview

The passive CLI command preview milestone adds a read-only command preview
path:

```powershell
python -m rytm_randomizer.cli preview-command <key>
python -m rytm_randomizer.cli preview-command --help
```

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_preview_command_help_expected.txt`
- `tests/fixtures/cli_preview_command_known_expected.txt`
- `tests/fixtures/cli_preview_command_unknown_expected.txt`

It does:

- use the existing passive preview helper
- display deterministic human-readable dry-run preview metadata
- clearly state that no MIDI would be sent
- clearly state that no command would execute
- clearly state that no hardware would be mutated
- fail safely for unknown or missing keys
- preserve existing passive report, inspect, list, and search behavior
- require no hardware

Manual verification showed:

- top-level help prints preview-command.
- preview-command help prints passive preview-command usage.
- `python -m rytm_randomizer.cli preview-command J` prints Command: J, Found:
  True, Category: print, Scaffold only: True, Executable: False,
  Forbidden/no-touch: False, Validation ok: True, Validation errors: 0, and
  Safety summary: No MIDI would be sent. No command would execute.
- `python -m rytm_randomizer.cli preview-command DOES_NOT_EXIST` fails safely
  with: "Command preview not found. No MIDI was sent. No command executed. No
  hardware was mutated."

It does not:

- call handlers
- add handlers
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- write files
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Scene Preview

The passive CLI scene preview milestone adds a read-only scene preview path:

```powershell
python -m rytm_randomizer.cli preview-scene <key>
python -m rytm_randomizer.cli preview-scene --help
```

It uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_preview_scene_help_expected.txt`
- `tests/fixtures/cli_preview_scene_known_expected.txt`
- `tests/fixtures/cli_preview_scene_unknown_expected.txt`

It does:

- use existing copied scene registry metadata
- display deterministic human-readable dry-run scene preview metadata
- clearly state that no MIDI would be sent
- clearly state that no scene would execute
- clearly state that no command would execute
- clearly state that no hardware would be mutated
- fail safely for unknown or missing keys
- preserve existing passive report, inspect, list, search, and command preview behavior
- require no hardware

Manual verification showed:

- top-level help prints preview-scene.
- preview-scene help prints passive preview-scene usage.
- `python -m rytm_randomizer.cli preview-scene S1A` prints Scene: S1A, Found:
  True, Name: Rolling Light, Description: Lower-risk rolling movement for
  subtle live variation, Action: rolling_light, Scope: four_pad_group,
  Scaffold only: True, Executable: False, V1.34 reference command: True, and
  explicit no-MIDI, no-scene, no-command, and no-hardware-mutation statements.
- `python -m rytm_randomizer.cli preview-scene DOES_NOT_EXIST` fails safely
  with: "Scene preview not found. No MIDI was sent. No scene executed. No
  command executed. No hardware was mutated."

It does not:

- call handlers
- add handlers
- open MIDI ports
- send MIDI
- dispatch scenes or commands
- execute scenes or commands
- write files
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Preview Trio Complete

The passive CLI preview trio is complete.

Recent preview commits:

- 813cc0a Add passive CLI command preview
- 28b4f79 Add passive CLI scene preview
- a96c039 Add passive CLI group profile preview

The preview trio includes:

```powershell
python -m rytm_randomizer.cli preview-command <key>
python -m rytm_randomizer.cli preview-scene <key>
python -m rytm_randomizer.cli preview-group-profile <key>
```

The latest milestone uses:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_preview_group_profile_help_expected.txt`
- `tests/fixtures/cli_preview_group_profile_known_expected.txt`
- `tests/fixtures/cli_preview_group_profile_unknown_expected.txt`

Preview behavior:

- preview-command uses the existing passive preview helper
- preview-scene uses copied passive scene registry metadata
- preview-group-profile uses copied passive group profile registry metadata
- unknown or missing keys fail safely
- no hardware is required

Manual verification showed:

- top-level help prints preview-group-profile.
- preview-group-profile help prints passive preview-group-profile usage.
- `python -m rytm_randomizer.cli preview-group-profile 2` prints Group profile:
  2, Found: True, Name: My BD Hard, Machine value: 0, Group pad: 1, and
  explicit no-MIDI, no-command, and no-hardware-mutation statements.
- `python -m rytm_randomizer.cli preview-group-profile DOES_NOT_EXIST` fails
  safely with: "Group profile preview not found. No MIDI was sent. No command
  executed. No hardware was mutated."

The preview trio does not:

- call handlers
- add handlers
- open MIDI ports
- send MIDI
- dispatch commands or scenes
- execute commands or scenes
- write files
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Passive CLI Operator Quickstart

`Docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md` documents how to use the current
passive CLI safely during the V1.34 modularization phase.

It covers:

- purpose
- current safe baseline
- how to run the passive CLI
- report command
- list commands
- inspect commands
- search commands
- safe no-match behavior
- what the CLI does not do
- hardware status
- closeout checklist

It documents these representative passive CLI commands:

```powershell
python -m rytm_randomizer.cli --help
python -m rytm_randomizer.cli report
python -m rytm_randomizer.cli list-commands
python -m rytm_randomizer.cli list-scenes
python -m rytm_randomizer.cli list-group-profiles
python -m rytm_randomizer.cli inspect-command J
python -m rytm_randomizer.cli inspect-scene S1A
python -m rytm_randomizer.cli inspect-group-profile 2
python -m rytm_randomizer.cli search-commands BD
python -m rytm_randomizer.cli search-scenes Wild
python -m rytm_randomizer.cli search-group-profiles Hard
python -m rytm_randomizer.cli preview-command J
python -m rytm_randomizer.cli preview-scene S1A
python -m rytm_randomizer.cli preview-group-profile 2
```

The quickstart states that the CLI is passive/read-only and does not send MIDI,
open ports, execute commands, mutate hardware, or require Analog Rytm or Analog
Four hardware to be powered on. Analog Rytm and Analog Four should remain off
during this phase.

The quickstart is documentation-only. It does not add CLI behavior, runtime
behavior, MIDI sending, port opening, dispatch, command execution, hardware
mutation, SysEx, GUI, capture, Analog Four support, Pads 5-12 support, or
machine/profile universe expansion.

Analog Rytm and Analog Four remain off for this phase.

### Guarded Passive Depth Command Labels

The guarded passive depth command label milestone improves passive
`list-commands` readability for guarded main-prompt depth entries:

```text
1: guarded depth input 1, requires lane/mode prefix
2: guarded depth input 2, requires lane/mode prefix
3: guarded depth input 3, requires lane/mode prefix
```

It uses:

- `rytm_randomizer/commands.py`
- `tests/test_scaffold.py`
- `tests/fixtures/cli_list_commands_expected.txt`

It does:

- label existing guarded depth command metadata for 1, 2, and 3
- keep the entries non-executable
- keep the entries scaffold-only/passive
- keep the entries as V1.34 reference command metadata
- keep sends_midi: False
- improve passive CLI list readability

It does not:

- call handlers
- add handlers
- add callables
- open MIDI ports
- send MIDI
- dispatch commands
- execute commands
- mutate runtime state
- mutate hardware state
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

Analog Rytm and Analog Four remain off for this phase.

### Registry Report Golden Text Contract

The registry report golden text contract locks down the formatted passive
registry report output.

It uses:

- `tests/test_registry_report.py`
- `tests/fixtures/registry_report_expected.txt`

Purpose:

- keep the formatted report deterministic
- provide snapshot-style golden text coverage
- make future CLI, UI, and reporting work safer
- normalize line endings so Windows CRLF/LF differences do not cause false failures

Closeout already includes registry report testing, so no duplicate closeout
entry was needed.

It does not:

- add CLI behavior
- write report files at runtime
- print during import
- execute commands
- dispatch commands
- send MIDI
- open ports
- mutate state or hardware
- write SysEx
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

### Profile Lookup

`rytm_randomizer/profile_lookup.py` exposes read-only lookup helpers for the
existing V1.34 `GROUP_PROFILE_METADATA` entries.

It exposes:

- existing group profile keys
- passive profile descriptions
- machine values for existing group profile keys
- group pad values for existing group profile keys
- passive not-found behavior for unknown keys
- copied metadata to prevent source mutation

It does not:

- add new profiles
- add new machines
- add new MIDI mappings
- add Pads 5-12
- execute commands
- dispatch runtime behavior
- send MIDI or open ports

### Scene Lookup

`rytm_randomizer/scene_lookup.py` exposes read-only lookup helpers for the
existing V1.34 `SCENE_COMMANDS` metadata.

It exposes:

- existing scene keys
- passive scene descriptions
- scene names
- scene action metadata as data only
- passive not-found behavior for unknown keys
- copied metadata to prevent source mutation

It does not:

- execute scene actions
- dispatch scene commands
- treat action metadata as callable behavior
- send MIDI or open ports
- mutate state or hardware
- add Pads 5-12

### Command Lookup

`rytm_randomizer/command_lookup.py` exposes read-only lookup helpers for the
existing V1.34 `COMMANDS` metadata.

It exposes:

- existing command keys
- passive command descriptions
- command type metadata
- command label or scene name metadata
- passive not-found behavior for unknown keys
- copied metadata to prevent source mutation

It does not:

- execute commands
- dispatch commands
- add handlers, callables, callbacks, or runtime hooks
- treat metadata fields as executable behavior
- send MIDI or open ports
- mutate state or hardware
- add Pads 5-12

## Current Safety Boundaries

Current modularization work remains behind these boundaries:

- no MIDI
- no ports
- no runtime dispatch
- no command execution
- no hardware mutation
- no SysEx writes
- no GUI
- no capture
- no Analog Four
- no Pads 5-12

## Recommended Next Passive Layers

Recommended passive layers before runtime work:

- roadmap review/acceptance
- after roadmap review, create a first-candidate mock-only active test design document
- add more mock-only safety tests only after a separate approved design
- keep active planning frozen and return to passive/project documentation
- keep profile `"4"` unsupported unless separately approved
- stop/pause at the clean checkpoint if no next planning slice is needed
- keep any future mapping work mock-only without real MIDI or hardware behavior and separately reviewed
- do not expand beyond supported group profiles `"2"` and `"3"` without a new explicit design/review step
- keep hardware off during mock MIDI boundary work

These layers should continue to return passive data only and must not wire into
runtime command execution.

## Passive Report CLI Preview Plan

`Docs/PASSIVE_REPORT_CLI_PREVIEW_PLAN.md` defined the read-only CLI
preview/report command concept before implementation. The implemented passive
CLI preview now follows that plan.

Implemented passive command shapes include:

- `python -m rytm_randomizer.cli --help`
- `python -m rytm_randomizer.cli report --help`
- `python -m rytm_randomizer.cli inspect-command --help`
- `python -m rytm_randomizer.cli inspect-command <key>`
- `python -m rytm_randomizer.cli inspect-scene --help`
- `python -m rytm_randomizer.cli inspect-scene <key>`
- `python -m rytm_randomizer.cli inspect-group-profile --help`
- `python -m rytm_randomizer.cli inspect-group-profile <key>`
- `python -m rytm_randomizer.cli list-commands`
- `python -m rytm_randomizer.cli list-scenes`
- `python -m rytm_randomizer.cli list-group-profiles`
- `python -m rytm_randomizer.cli search-commands <query>`
- `python -m rytm_randomizer.cli search-scenes <query>`
- `python -m rytm_randomizer.cli search-group-profiles <query>`
- `python -m rytm_randomizer.cli preview-command --help`
- `python -m rytm_randomizer.cli preview-command <key>`
- `python -m rytm_randomizer.cli preview-scene --help`
- `python -m rytm_randomizer.cli preview-scene <key>`
- `python -m rytm_randomizer.cli preview-group-profile --help`
- `python -m rytm_randomizer.cli preview-group-profile <key>`
- `python -m rytm_randomizer.registry_report`
- `python -m rytm_randomizer.cli report`

The command only formats and displays the already-passive registry report. It is
useful for inspection, documentation, future UI, and future safe operator
workflows.

The plan requires that any future CLI preview preserve:

- the passive registry report generator boundary
- the registry report golden text contract
- no import-time printing
- no report file writing by default
- no hardware requirement

It prohibits:

- MIDI sending
- MIDI port opening
- command dispatch
- command execution
- hardware mutation
- SysEx
- GUI behavior
- capture behavior
- Analog Four support
- Pads 5-12 support
- machine/profile universe expansion

## Conditions Before Hardware-Facing Work

Before any hardware-facing layer is considered, the project should require:

- V1.34 behavior parity plan
- explicit dry-run mode
- isolated MIDI adapter
- no automatic port opening
- manual user confirmation before hardware send
- tests proving no accidental execution

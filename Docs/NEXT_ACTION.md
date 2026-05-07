# Next Action

## Current Branch

modularize-v1.34

## Current HEAD

75a2afd Add future active test plan review

## Current Phase

Passive CLI / dry-run foundation.

## Current Safety State

- V1.34 reference untouched
- no MIDI
- no ports
- no dispatch
- no command execution
- no scene execution
- no hardware mutation
- no SysEx
- no GUI
- no capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion

## Hardware Status

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required for current phase

## Current Passive CLI Capability

- report
- list commands/scenes/group profiles
- search commands/scenes/group profiles
- inspect commands/scenes/group profiles
- preview commands/scenes/group profiles
- mock-mapper-report

## Known Safe Passive Commands

```powershell
python -m rytm_randomizer.cli report
python -m rytm_randomizer.cli list-commands
python -m rytm_randomizer.cli list-scenes
python -m rytm_randomizer.cli list-group-profiles
python -m rytm_randomizer.cli search-commands BD
python -m rytm_randomizer.cli search-scenes Wild
python -m rytm_randomizer.cli inspect-command J
python -m rytm_randomizer.cli inspect-scene S1A
python -m rytm_randomizer.cli inspect-group-profile 2
python -m rytm_randomizer.cli preview-command J
python -m rytm_randomizer.cli preview-scene S1A
python -m rytm_randomizer.cli preview-group-profile 2
python -m rytm_randomizer.cli mock-mapper-report
```

## Next Recommended Task

Next recommended task is roadmap review/acceptance for:

- `Docs/PASSIVE_MOCK_FOUNDATION_ROADMAP.md`

Safe alternatives are:

- stop/pause at this clean checkpoint
- create a docs-only profile 4 support plan
- freeze mock mapper scope and focus on project-level documentation
- prepare a broader roadmap/timeline update

- `Docs/PASSIVE_TO_ACTIVE_BOUNDARY.md`
- `Docs/PASSIVE_TO_ACTIVE_BOUNDARY_REVIEW.md`
- `Docs/ACTIVE_LAYER_DESIGN_SPEC.md`
- `Docs/ACTIVE_LAYER_DESIGN_SPEC_REVIEW.md`
- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN.md`
- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN_REVIEW.md`
- `Docs/MOCK_MIDI_SCAFFOLD_REVIEW.md`
- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md`
- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC_REVIEW.md`
- `Docs/MOCK_MESSAGE_MAPPER_REVIEW.md`
- `Docs/PASSIVE_MOCK_MIDI_PROGRESS_CHECKPOINT.md`
- `Docs/MOCK_MAPPER_PROFILE_3_PROGRESS_CHECKPOINT.md`
- `Docs/MOCK_MAPPER_PROFILE_4_DECISION_NOTE.md`
- `Docs/MOCK_MAPPER_PROGRESS_REVIEW.md`
- `Docs/PASSIVE_MOCK_FOUNDATION_DECISION_CHECKPOINT.md`
- `Docs/PASSIVE_MOCK_MAPPER_CLI_PREVIEW_PHASE_REVIEW.md`
- `Docs/PASSIVE_MOCK_FOUNDATION_PROGRESS_REPORT.md`
- `Docs/FUTURE_ACTIVE_TEST_PLAN.md`
- `Docs/FUTURE_ACTIVE_TEST_PLAN_REVIEW.md`
- `Docs/PASSIVE_MOCK_FOUNDATION_ROADMAP.md`

The mock MIDI scaffold review accepts the test-only mock MIDI scaffold and
records that no real MIDI behavior exists:

- `rytm_randomizer/mock_midi.py`
- `tests/test_mock_midi.py`

The test-only mock message mapper milestone adds:

- `rytm_randomizer/mock_message_mapper.py`
- `tests/test_mock_message_mapper.py`
- `Scripts/closeout_check.ps1`

The mapper supports only group profile key `"2"` / My BD Hard, returns
deterministic inert mock MidiMessage objects, records cleanly through
MockMidiSender, and fails safely for unknown or unsupported keys.

The latest test-only mock mapper expansion adds support for existing group
profile key `"3"` / My BD Classic. Group profile key `"2"` behavior remains
unchanged, and group profile key `"4"` remains unsupported and fails safely.

No real MIDI, no hardware, no active CLI command, no runtime execution, no port
opening, and no CLI wiring exists.

The mock message mapper review accepts the current test-only mapper scaffold
and records that future expansion must remain mock-only, separately reviewed,
limited to existing passive metadata, and unwired from CLI or runtime
execution.

The passive mock MIDI progress checkpoint summarizes the current passive CLI,
mock MIDI, and mock message mapper state after `32006f4`. It records that this
is a clean decision point before any additional mapper scope, active execution,
or hardware-facing work.

The mock mapper profile 3 progress checkpoint records the current mock mapper
state after `c961dbf`: group profiles `"2"` and `"3"` are supported, group
profile `"4"` remains intentionally unsupported/safe, and no next mapper
expansion is approved yet.

The mock mapper profile 4 decision note records the current decision: profile
`"4"` / My BD Acoustic remains unsupported for now. Future profile 4 support
requires explicit approval as a tiny mock-only expansion.

The mock mapper progress review records the current mock mapper boundary:
profiles `"2"` and `"3"` are supported, profile `"4"` remains
unsupported/safe, and the next options are to keep mapper scope frozen, plan
profile 4 support, build a passive mock mapper report/summary, or pause mapper
work.

The passive mock mapper report milestone adds:

- `rytm_randomizer/mock_mapper_report.py`
- `tests/test_mock_mapper_report.py`
- `Scripts/closeout_check.ps1`

The report summarizes the current mock mapper boundary in memory only:
profiles `"2"` / My BD Hard and `"3"` / My BD Classic are supported, profile
`"4"` / My BD Acoustic remains unsupported/safe, mock-only status is true, real
MIDI is absent, port opening is absent, CLI wiring is absent, active behavior
is absent, and hardware is not required.

The passive mock foundation decision checkpoint records the current state in
one place: the passive CLI foundation is complete enough for report/list/search
/inspect/preview, mock MIDI and mock message mapper remain test-only/inert,
the mock mapper report is in closeout, profiles `"2"` and `"3"` are supported,
profile `"4"` remains unsupported/safe, and the safe next branches are to
freeze scope, plan profile 4 support, build a passive mock mapper report CLI
preview, write a larger progress report, or review future active-layer test
planning without implementation.

The passive mock mapper report CLI preview milestone adds:

- `python -m rytm_randomizer.cli mock-mapper-report`
- `python -m rytm_randomizer.cli mock-mapper-report --help`

Manual verification confirmed top-level help lists `mock-mapper-report`, the
command help prints passive/mock-only usage, and the command prints the mock
mapper report showing profiles `"2"` and `"3"` supported with profile `"4"`
unsupported/safe. The command prints the existing formatted passive mock
mapper report only. It does not wire CLI to the mapper itself, invoke active
execution, open ports, send MIDI, require hardware, add profile 4 support, or
add active behavior.

The passive mock mapper CLI preview phase review records that the passive/mock
visibility layer is complete through `mock-mapper-report`. It confirms the
current CLI visibility layer, supported profiles `"2"` and `"3"`, unsupported
/safe profile `"4"`, absent real MIDI and ports, absent active behavior, and
hardware-off status. Safe next branches are freezing scope, creating a profile
4 plan, writing a broader milestone report, or drafting future active/mock-only
test plans without implementation.

The passive mock foundation progress report consolidates the full current
passive/mock foundation into one milestone reference. It records that the
passive CLI foundation is complete enough for report/list/search/inspect
/preview, the mock MIDI scaffold is test-only/inert, the mock message mapper
supports profiles `"2"` and `"3"`, profile `"4"` remains unsupported/safe, the
mock mapper report and CLI preview exist, real MIDI and ports remain absent,
active behavior remains absent, and hardware remains off. The next recommended
branch is a docs-only future active test-plan document.

The future active test-plan defines what must be proven before any active or
hardware-facing behavior can be implemented or validated. It is planning-only:
no active execution, MIDI code, port opening, hardware validation, active CLI
command, or profile 4 implementation is added. It keeps hardware off and sets
the next recommended task as review/acceptance of the test plan.

The future active test-plan review accepts `Docs/FUTURE_ACTIVE_TEST_PLAN.md`
as the current planning gate. It confirms no implementation exists, hardware
remains off, passive commands remain read-only, and future active-facing work
must remain mock-only and documentation/test-gated until explicitly approved.

The passive/mock foundation roadmap names the current phase as the
Passive/Mock Foundation Phase. It records that the foundation is complete
enough for planning, not active, not hardware-facing, and still has no real
MIDI, ports, active behavior, or hardware validation. It keeps profile `"4"`
parked and sets the next recommended task as roadmap review/acceptance.

## Do-Not-Touch Files

- `rytm_hybrid_randomizer_v134.py`

## Closeout Command

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

## Stop Condition

- closeout passes
- `git diff -- rytm_hybrid_randomizer_v134.py` is empty
- `git status --short` is clean

## Reminder

Do not turn on Analog Rytm or Analog Four until explicitly entering a
hardware-facing validation phase.

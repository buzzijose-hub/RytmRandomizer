# Next Action

## Current Branch

modularize-v1.34

## Current HEAD

8289003 Add read-only active boundary report CLI preview design

## Current Phase

Passive/Mock Foundation Phase with the first mock-first active boundary
implemented for test-only evaluation.

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

Next recommended task is either a tiny fixture-backed implementation of the
read-only active boundary report CLI preview, or a pause at this clean design
review checkpoint.

The latest read-only active boundary report CLI preview design review is:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CLI_PREVIEW_DESIGN_REVIEW.md`

The review accepts:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CLI_PREVIEW_DESIGN.md`

The review accepts a future passive CLI command shape only:

- `python -m rytm_randomizer.cli active-boundary-report`
- `python -m rytm_randomizer.cli active-boundary-report --help`

The future command must print `format_active_boundary_report()` output only.
It must add no active request evaluation, mock message emission, real MIDI,
ports, active CLI behavior, dispatch, hardware behavior, profile `"4"`
implementation, or profile `"3"` active-boundary support.

The latest read-only active boundary report CLI preview design is:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CLI_PREVIEW_DESIGN.md`

The design proposes a future passive CLI command:

- `python -m rytm_randomizer.cli active-boundary-report`
- `python -m rytm_randomizer.cli active-boundary-report --help`

The command would print `format_active_boundary_report()` output only. This
design adds no CLI implementation, real MIDI, ports, active CLI behavior,
dispatch, hardware behavior, profile `"4"` implementation, or profile `"3"`
active-boundary support.

The latest read-only active boundary report review is:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_REVIEW.md`

The review accepts:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CHECKPOINT.md`

The review accepts the read-only active boundary report as the current
visibility checkpoint. It does not authorize CLI wiring, real MIDI, ports,
active CLI behavior, dispatch, hardware behavior, profile `"4"`
implementation, or profile `"3"` active-boundary support.

The latest read-only active boundary report checkpoint is:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CHECKPOINT.md`

The latest implementation milestone is:

- f1fb91e Add read-only active boundary report

The milestone adds:

- `rytm_randomizer/active_boundary_report.py`
- `tests/test_active_boundary_report.py`
- `Scripts/closeout_check.ps1`

The closeout suite now includes:

- `=== Test: Active Boundary Report ===`

The report module exposes:

- `build_active_boundary_report()`
- `format_active_boundary_report(report=None)`
- `summarize_active_boundary_report(report=None)`

It remains read-only, in-memory, not wired to CLI, and adds no real MIDI,
ports, active CLI behavior, dispatch, hardware behavior, profile `"4"`
implementation, or profile `"3"` active-boundary support.

The latest active boundary report visibility design review is:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_REPORT_VISIBILITY_DESIGN_REVIEW.md`

The review accepts:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_REPORT_VISIBILITY_DESIGN.md`

The review accepts future ownership for:

- `rytm_randomizer/active_boundary_report.py`

It accepts a future read-only, in-memory report module only. It does not
authorize CLI wiring, real MIDI, ports, active CLI behavior, dispatch,
hardware behavior, profile `"4"` implementation, or profile `"3"`
active-boundary support.

The latest active boundary report visibility design is:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_REPORT_VISIBILITY_DESIGN.md`

The design defines a future read-only report/summary layer for the current
mock-first active boundary state. It is documentation-only and adds no report
module, CLI command, real MIDI, ports, active CLI behavior, dispatch, hardware
behavior, profile `"4"` implementation, or profile `"3"` active-boundary
support.

The latest active boundary safety coverage progress report review is:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_COVERAGE_PROGRESS_REPORT_REVIEW.md`

The review accepts:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_COVERAGE_PROGRESS_REPORT.md`

The review confirms the broader progress report is accepted as the current
mock-only active boundary safety coverage checkpoint. It adds no
implementation, real MIDI, ports, active CLI behavior, dispatch, hardware
behavior, profile `"4"` implementation, or profile `"3"` active-boundary
support.

The latest active boundary safety coverage progress report is:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_COVERAGE_PROGRESS_REPORT.md`

The report summarizes:

- current mock-first active boundary surface
- accepted group profile `"2"` / My BD Hard candidate
- profile `"3"` remaining unsupported by the active boundary
- profile `"4"` remaining parked and unsupported
- accepted safety test coverage
- closeout coverage
- absent real MIDI, ports, active CLI behavior, dispatch, and hardware
  behavior
- safe next branches

The latest mock-only active boundary safety tests review is:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_TESTS_REVIEW.md`

The review accepts:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_TESTS_CHECKPOINT.md`

The review confirms the completed safety tests are accepted as the current
mock-only active boundary safety coverage checkpoint. It adds no
implementation, real MIDI, ports, active CLI behavior, dispatch, hardware
behavior, profile `"4"` implementation, or profile `"3"` active-boundary
support.

The latest mock-only active boundary safety tests checkpoint is:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_TESTS_CHECKPOINT.md`

The latest test-only implementation milestone is:

- 51b1a8f Add mock-only active boundary safety tests

The milestone updates:

- `tests/test_active_boundary.py`

It adds safety coverage for metadata copy/immutability, unsupported source
kind, profile `"3"` remaining unsupported by the active boundary, profile
`"4"` remaining parked, deterministic accepted and failed evaluations, sender
state after failure paths, invalid input type failures before message
emission, and no real-MIDI or active-CLI affordances exposed.

The mock-only active boundary safety test design review is:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_TEST_DESIGN_REVIEW.md`

The review accepts:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_TEST_DESIGN.md`

The accepted test-only implementation was completed in:

- `tests/test_active_boundary.py`

No closeout update was needed because `tests/test_active_boundary.py` was
already included in closeout.

The mock-only active boundary safety test design is:

- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_TEST_DESIGN.md`
- `Docs/MOCK_ONLY_ACTIVE_BOUNDARY_SAFETY_TESTS_CHECKPOINT.md`

The design proposes a future test-only slice that should prefer extending:

- `tests/test_active_boundary.py`

It does not implement tests or code in this slice.

The broader mock-first active boundary progress report is:

- `Docs/MOCK_FIRST_ACTIVE_BOUNDARY_PROGRESS_REPORT.md`

The morning handoff refresh milestone is:

- ccfc2e3 Refresh handoff after mock-first active boundary review

The mock-first active boundary review is:

- `Docs/MOCK_FIRST_ACTIVE_BOUNDARY_REVIEW.md`

The mock-first active boundary review milestone is:

- 1307fab Add mock-first active boundary review

The review accepts:

- `Docs/MOCK_FIRST_ACTIVE_BOUNDARY_CHECKPOINT.md`

The accepted implementation milestone remains:

- 565770e Add mock-first active boundary

The accepted documentation checkpoint remains:

- ae55174 Update checkpoint after mock-first active boundary

The review confirms no real MIDI, ports, active CLI behavior, dispatch,
hardware behavior, or profile `"4"` implementation exists.

The latest mock-first active boundary checkpoint is:

- `Docs/MOCK_FIRST_ACTIVE_BOUNDARY_CHECKPOINT.md`

The latest implementation milestone is:

- 565770e Add mock-first active boundary

The milestone adds:

- `rytm_randomizer/active_boundary.py`
- `tests/test_active_boundary.py`
- `Scripts/closeout_check.ps1`

The implemented boundary defines:

- `ActiveBoundaryRequest`
- `ActiveBoundaryResult`
- `ActiveBoundaryError`
- `evaluate_mock_active_boundary(request, sender)`

It supports only group profile `"2"` / My BD Hard through inert mock messages
and an injected `MockMidiSender`. Missing arming, missing dry-run
confirmation, unknown keys, unsupported keys, and profile `"4"` / My BD
Acoustic fail safely with no emitted messages.

It is not wired into CLI, does not import real MIDI libraries, opens no ports,
sends no MIDI, dispatches no commands, executes no commands, and requires no
hardware.

The implementation plan is:

- `Docs/ACTIVE_BOUNDARY_IMPLEMENTATION_PLAN.md`

The active boundary implementation design/spec review is:

- `Docs/ACTIVE_BOUNDARY_IMPLEMENTATION_DESIGN_SPEC_REVIEW.md`

The accepted design/spec uses the mock-only proof for:

- group profile `"2"` / My BD Hard

It remains mock-first, candidate-specific, and not wired to CLI or real MIDI.

The active boundary implementation design/spec is:

- `Docs/ACTIVE_BOUNDARY_IMPLEMENTATION_DESIGN_SPEC.md`

The active boundary implementation planning gate is:

- `Docs/ACTIVE_BOUNDARY_IMPLEMENTATION_PLANNING_GATE.md`

The mock-only active candidate tests review is:

- `Docs/MOCK_ONLY_ACTIVE_CANDIDATE_TESTS_REVIEW.md`

The latest mock-only test checkpoint is:

- `Docs/MOCK_ONLY_ACTIVE_CANDIDATE_TESTS_CHECKPOINT.md`

The implementation plan is now:

- `Docs/MOCK_ONLY_ACTIVE_TEST_IMPLEMENTATION_PLAN.md`

The first-candidate design review is now:

- `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN_REVIEW.md`

The safe parallel workstream plan is:

- `Docs/PASSIVE_MOCK_PARALLEL_WORKSTREAM_PLAN.md`

It preserves the knowledge acquired after the first-candidate mock-only active
test design:

- use parallel thinking to organize work, not to rush scope
- split future work into independent passive/mock lanes
- keep closeout as the synchronization point
- use planning, TDD, verification, and debugging workflows deliberately
- use subagents only for independent work after explicit approval

The latest knowledge checkpoint is:

- `Docs/PASSIVE_MOCK_KNOWLEDGE_CHECKPOINT.md`

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
- `Docs/ACTIVE_BOUNDARY_IMPLEMENTATION_PLANNING_GATE.md`
- `Docs/ACTIVE_BOUNDARY_IMPLEMENTATION_DESIGN_SPEC.md`
- `Docs/ACTIVE_BOUNDARY_IMPLEMENTATION_DESIGN_SPEC_REVIEW.md`
- `Docs/ACTIVE_BOUNDARY_IMPLEMENTATION_PLAN.md`
- `Docs/MOCK_FIRST_ACTIVE_BOUNDARY_CHECKPOINT.md`
- `Docs/PASSIVE_MOCK_FOUNDATION_ROADMAP.md`
- `Docs/PASSIVE_MOCK_FOUNDATION_ROADMAP_REVIEW.md`
- `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN.md`
- `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN_REVIEW.md`
- `Docs/MOCK_ONLY_ACTIVE_TEST_IMPLEMENTATION_PLAN.md`
- `Docs/MOCK_ONLY_ACTIVE_CANDIDATE_TESTS_CHECKPOINT.md`
- `Docs/MOCK_ONLY_ACTIVE_CANDIDATE_TESTS_REVIEW.md`
- `Docs/PASSIVE_MOCK_KNOWLEDGE_CHECKPOINT.md`
- `Docs/PASSIVE_MOCK_PARALLEL_WORKSTREAM_PLAN.md`

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

The passive/mock foundation roadmap review accepts
`Docs/PASSIVE_MOCK_FOUNDATION_ROADMAP.md` as the current roadmap. It confirms
the Passive/Mock Foundation Phase, keeps profile `"4"` parked, keeps hardware
off, and sets the next recommended task as first-candidate mock-only active
test design.

The first-candidate mock-only active test design selects group profile `"2"` /
My BD Hard as the first mock-only candidate. It uses existing passive/mock
metadata and the existing test-only mock mapper boundary. It does not implement
tests, active behavior, MIDI, port opening, CLI execution, or hardware
validation. The next recommended task is review/acceptance of the candidate
design.

The passive mock knowledge checkpoint records the strategy learned after the
first-candidate design: maximize clarity before concurrency, split future work
into independent passive/mock lanes, keep closeout as the synchronization
point, and create a docs-only safe parallel workstream plan next. It adds no
implementation, tests, real MIDI, port opening, active behavior, or hardware
behavior.

The passive mock parallel workstream plan records how to parallelize safely:
docs/roadmap, mock-only test design, mock-only test implementation, passive
CLI/report visibility, safety/closeout, and future active planning are separate
lanes. It keeps closeout as the synchronization point, recommends no subagents
yet, keeps profile `"4"` parked, and sets the next task as review/acceptance
of the first-candidate mock-only active test design.

The first-candidate mock-only active test design review accepts group profile
`"2"` / My BD Hard as the current mock-only planning candidate. It confirms no
tests, active behavior, real MIDI, port opening, CLI execution, hardware
validation, or profile `"4"` implementation exists. The next recommended task
is a mock-only active test implementation plan.

The mock-only active test implementation plan defines the future test-only
slice for group profile `"2"` / My BD Hard. It plans one new test file,
`tests/test_mock_only_active_candidate.py`, and one closeout update. It keeps
the implementation coverage-only, uses existing `MockMidiSender` and
`map_group_profile_to_mock_messages`, keeps profile `"4"` parked, and adds no
real MIDI, ports, active behavior, CLI command, or hardware behavior in this
planning slice.

The mock-only active candidate tests checkpoint records completion of that
coverage-only slice. It confirms `tests/test_mock_only_active_candidate.py` and
the closeout label `=== Test: Mock-Only Active Candidate ===` are in place.
The tests prove profile `"2"` maps to inert mock messages, records through
`MockMidiSender`, keeps profile `"4"` unsupported/safe, preserves passive CLI
report behavior, imports no real MIDI libraries, and exposes no active behavior
names.

The mock-only active candidate tests review accepts the completed tests as the
current mock-only proof checkpoint. It confirms the project has moved from
mock-only planning to mock-only proof without adding real MIDI, ports, active
CLI behavior, hardware behavior, or profile `"4"` support. The next recommended
task is a docs-only active boundary implementation planning gate.

The active boundary implementation planning gate records that active boundary
implementation may not begin yet. It allows only a docs-only active boundary
implementation design/spec next. That future spec must remain mock-first,
preserve passive CLI behavior, avoid real MIDI libraries and ports, keep
profile `"4"` parked, and keep hardware off.

The active boundary implementation design/spec defines the future mock-first
boundary shape for group profile `"2"` / My BD Hard. It proposes future
conceptual request/result shapes, arming semantics, passive CLI separation,
real MIDI separation, expected future tests, and file ownership. It adds no
implementation, tests, real MIDI, ports, CLI commands, or hardware behavior.

The active boundary implementation design/spec review accepts that spec as the
current mock-first active boundary design. It confirms the next task is an
implementation plan only, limited to future `active_boundary.py`,
`test_active_boundary.py`, and closeout coverage. It does not authorize CLI
wiring, real MIDI, ports, hardware behavior, or profile `"4"` implementation.

The active boundary implementation plan defines the future mock-first active
boundary implementation slice. It plans `rytm_randomizer/active_boundary.py`,
`tests/test_active_boundary.py`, and a closeout label `=== Test: Active
Boundary ===`. The planned boundary remains candidate-specific for group
profile `"2"` / My BD Hard, uses `MockMidiSender` only, keeps passive CLI
separate, keeps real MIDI absent, and keeps profile `"4"` parked.

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

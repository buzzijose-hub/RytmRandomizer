# Passive Mock Parallel Workstream Plan

## 1. Purpose

Define how future RytmRandomizer work can be parallelized safely after the
passive/mock foundation and first-candidate mock-only active test design.

This plan is documentation-only. It does not implement tests, MIDI behavior,
port opening, active execution, CLI execution, dispatch, or hardware behavior.

The goal is not maximum speed at any cost. The goal is maximum safe clarity:
small independent lanes, explicit dependencies, and closeout as the shared
synchronization point.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 9a3dc06 Add passive mock knowledge checkpoint

Current phase:

- Passive/Mock Foundation Phase
- first-candidate mock-only active test design created
- parallel workstream planning now documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Foundation

The current foundation includes:

- passive CLI report/list/search/inspect/preview paths
- passive `mock-mapper-report` CLI visibility
- test-only mock MIDI scaffold
- test-only mock message mapper
- passive mock mapper report
- first-candidate mock-only active test design for group profile `"2"` / My BD Hard
- profile `"4"` / My BD Acoustic parked as unsupported/safe
- closeout coverage for Mock MIDI, Mock Message Mapper, and Mock Mapper Report

## 4. Parallelization Principle

Parallel work is allowed only when lanes are independent.

Safe parallelization means:

- no two lanes edit the same files in the same slice
- each lane has a narrow purpose
- each lane keeps passive/mock safety boundaries intact
- each lane can be reviewed independently
- closeout passes before results are treated as complete
- git status returns clean before starting the next slice

Parallelization must not be used to sneak in active behavior, real MIDI, port
opening, or hardware-facing work.

## 5. Workstream Lanes

### Lane A: Docs And Roadmap

Responsibility:

- roadmap updates
- progress reports
- review/acceptance gates
- handoff updates
- safety summaries

Allowed files:

- `Docs/*.md`

Forbidden:

- code changes
- tests
- closeout script edits
- runtime behavior
- active behavior

### Lane B: Mock-Only Test Design

Responsibility:

- design documents for future mock-only tests
- acceptance criteria before test implementation
- failure-mode planning

Allowed files:

- `Docs/*.md`

Forbidden:

- actual test files unless a later implementation slice explicitly approves them
- real MIDI libraries
- ports
- hardware behavior
- active CLI commands

### Lane C: Mock-Only Test Implementation

Responsibility:

- future mock-only tests after a design is accepted
- tests that use `MockMidiSender` only
- tests that prove passive commands remain passive

Allowed files, only after explicit approval:

- `tests/test_*.py`
- mock-only modules under `rytm_randomizer/`
- `Scripts/closeout_check.ps1` only if a new test file must enter closeout

Forbidden:

- real MIDI libraries
- port opening
- MIDI sending
- active execution
- hardware requirements
- CLI active commands

### Lane D: Passive CLI And Reporting Visibility

Responsibility:

- future read-only CLI/report visibility
- existing passive report formatting
- fixture-backed deterministic output

Allowed files, only after explicit approval:

- `rytm_randomizer/cli.py`
- passive report modules
- `tests/test_cli.py`
- CLI fixtures

Forbidden:

- wiring CLI to active execution
- wiring CLI directly to hardware behavior
- opening ports
- sending MIDI
- adding `execute-command`, `send-command`, or `hardware-test`

### Lane E: Safety And Closeout

Responsibility:

- closeout coverage reviews
- no-port/no-MIDI safety assertions
- V1.34 reference checks
- import side-effect checks

Allowed files, only after explicit approval:

- tests
- `Scripts/closeout_check.ps1`
- docs

Forbidden:

- active behavior
- hardware behavior
- broad refactors
- changing V1.34 reference

### Lane F: Future Active Planning

Responsibility:

- documentation-only active planning
- arming design
- first-candidate mock-only active test review
- future hardware checklist planning

Allowed files:

- `Docs/*.md`

Forbidden:

- implementation
- real MIDI
- ports
- hardware validation
- active CLI command creation

## 6. Dependencies

Recommended order:

1. Docs-only review/acceptance for `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN.md`
2. Mock-only active test implementation plan
3. Mock-only tests for group profile `"2"` / My BD Hard
4. Safety/closeout review after mock-only tests
5. Later active boundary review before any real MIDI design

Profile `"4"` remains parked unless a separate docs-only support plan is
approved.

## 7. When Subagents Are Useful

Subagents may be useful later when tasks are genuinely independent, for
example:

- one agent drafts a docs-only review gate while another inspects mock-only test requirements
- one agent updates passive documentation while another runs read-only codebase exploration
- one agent prepares a mock-only test plan while another audits closeout coverage

Subagents should be given disjoint file ownership and narrow outputs.

## 8. When Subagents Should Not Be Used

Do not use subagents when:

- the next step is a blocker on the critical path
- two tasks touch the same files
- the work involves active behavior design decisions that need one coherent review
- the scope is small enough to handle directly
- the user has not explicitly approved subagent/delegated work

Current recommendation:

- do not use subagents yet
- write and review the next small planning slice directly

## 9. Skill Use Guidance

Use skills deliberately:

- use planning workflows before multi-step implementation
- use test-driven development before mock-only behavior changes
- use verification before completion before claiming success
- use systematic debugging if closeout fails
- use subagent-driven development only after explicit approval and only for independent lanes

Do not introduce new tooling or skills just to increase speed. Add workflow
support only when it reduces risk or clarifies the next slice.

## 10. Hard Stop Conditions

Stop immediately if any slice introduces or proposes:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- active execution
- active CLI commands
- CLI wiring to active behavior
- dispatch
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- profile `"4"` implementation without separate approval
- V1.34 reference diff
- unclear file ownership across parallel lanes

## 11. Closeout Requirements

Every slice must end with:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

Completion means:

- closeout passes
- V1.34 reference diff is empty
- git status is clean after commit
- hardware remains off

## 12. Recommended Next Slice

The first-candidate review/acceptance gate is:

- `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN_REVIEW.md`

The mock-only active test implementation plan is:

- `Docs/MOCK_ONLY_ACTIVE_TEST_IMPLEMENTATION_PLAN.md`

Do not implement tests until that plan is explicitly approved for execution.

## 13. Decision

Parallel work is approved as an organizing strategy, not as a scope expansion.

The next recommended task is implementation of the accepted mock-only active
candidate tests, if the plan is approved for execution.

Hardware remains off.

No implementation in this slice.

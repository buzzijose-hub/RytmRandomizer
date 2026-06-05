# OXI Live Set Strategy Report

Status: draft

## Intent

Add a passive, deterministic report that turns the merged OXI-style macro vocabulary into an operator-facing live set strategy. The report explains how OXI, Analog Rytm, and Analog Four divide responsibilities during performance, how the named Rytm macros can be used as set chapters, operator cues, and rehearsal checkpoints, how Jose's current pad-lane discipline should be represented without removing Pad 12 from the product, which Rytm/A4 validation passes should come next, and what evidence must exist before Analog Four moves from review-only to active macro behavior.

## Scope

- Add `rytm_randomizer.reports.oxi_live_set_strategy`.
- Add passive CLI command `oxi-live-set-strategy-report [--json]`.
- Include a hardware-validation runway for the next operator-present Rytm and A4 passes.
- Include A4 promotion criteria that keep outbound macros blocked until input labels, passive macro review, explicit arm gates, and recovery paths are validated.
- Include an operator cue sheet that maps every chapter to OXI action, Rytm staging, inspection, fire, recovery, expected result, and blocked actions.
- Include rehearsal checkpoints for capture, first macro staging, pre-send review, manual fire, anchor recovery, A4 gating, and after-set notes.
- Update passive CLI help, README, tests, and status docs.
- Keep all behavior report-only: no MIDI send, no port opening, no active hardware action, no GUI launch, no SysEx write.

## Out Of Scope

- No hardware send path changes.
- No Analog Four outbound macro execution.
- No snapshot mutation renderer changes.
- No cockpit UI implementation in this slice.
- No audio analyzer behavior.

## Architecture Fit

This uses the existing passive report pattern: frozen dataclasses, JSON-ready payload builder, deterministic formatter, and `cli_registry.CliCommand`. The report consumes the already-merged OXI macro vocabulary conceptually rather than duplicating active shell behavior or renderer code.

## Workstream Graph

| Workstream | Dependency | Files Owned |
| --- | --- | --- |
| WS1 passive report and CLI | none | `rytm_randomizer/reports/oxi_live_set_strategy.py`, `rytm_randomizer/cli.py`, `rytm_randomizer/help_text.py` |
| WS2 tests and docs | WS1 | `tests/test_oxi_live_set_strategy_report.py`, `tests/test_cli.py`, `tests/fixtures/cli_help_expected.txt`, `README.md`, `docs/STATUS.md` |

## Verification Plan

- `python -m pytest tests/test_oxi_live_set_strategy_report.py -q`
- `python -m pytest tests/test_oxi_live_set_strategy_report.py --cov=rytm_randomizer.reports.oxi_live_set_strategy --cov-branch --cov-fail-under=100 --cov-report=term-missing -q`
- `python -m pytest tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q`
- `python -m pytest tests/test_real_midi_passive_cli_safety.py tests/architecture/test_cli_no_inline_arms.py -q`
- `python -m pytest tests/architecture/ -q`
- `python -m pytest -m fast`
- `python -m ruff check .`
- `python -m black --check --target-version=py311 .`
- `python -m isort --profile black --check-only .`

## Plan-Requirements Conformance

Per `docs/PLAN_REQUIREMENTS.md`, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) - report module coverage run.
- [x] Gate 2 (V1.34 parity fixtures byte-identical) - no V1.34 engine/group/scene changes.
- [x] Gate 3 (lint/format/type clean) - ruff, black, and isort before commit.
- [x] Gate 4 (dead-code purge) - vulture/ruff dead-code checks for touched report code when needed.
- [x] Gate 5 (docs updated before PR open) - README and STATUS updated.
- [x] Gate 6 (type-system hygiene) - frozen dataclasses and explicit payload conversion.
- [x] Gate 7 (observability adoption) - N/A: passive formatting only, no state transition or guardrail decision.
- [x] Gate 8 (test hygiene) - source-mirrored focused tests.
- [x] Gate 9 (module-organization hygiene) - new module lives under existing `reports/` subpackage.
- [x] Gate 10 (string-literal dispatch hygiene) - CLI option parsing only; no runtime mode dispatch.
- [x] Gate 11 (shared test fixtures) - no new shared fixtures.
- [x] Gate 12 (module-level constants use `Final`) - new constants annotated.
- [x] Gate 13 (env vars: docs + safe default) - no env vars.
- [x] Gate 14 (maintainability review) - small passive report reusing existing abstractions.
- [x] Gate 15 (learning phase) - N/A for this narrow follow-up; no new process lesson expected.
- [x] Gate 16 (execution shape) - isolated worktree branch with autonomous verification.
- [x] Gate 17 (abstraction reuse and genericization) - reuses `CliCommand` and passive report formatter patterns.
- [x] Gate 18 (architecture-doc and diagram freshness) - N/A: passive report command only, no new architecture boundary.

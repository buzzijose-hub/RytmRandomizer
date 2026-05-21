# Analog Four Style Routing Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the passive Analog Four style snapshot routing strategy as an operator-facing report and CLI command without sending MIDI or claiming A4 offsets are mutation-ready.

**Architecture:** Keep the behavior inside the existing passive report/CLI-registry boundary. The report module consumes the A4 style routing strategy, the shared SysEx file reader, and the existing `PassiveReportHeader` formatter. `cli.py` only lazy-registers the `CliCommand`; `help_text.py` carries the static operator help.

**Tech Stack:** Python dataclasses from the A4 strategy layer, `CliCommand`, passive report formatter, `snapshot.sysex_file`, pytest, and architecture safety tests.

---

## Scope

This slice is a report surface only. It reads local SysEx files, decodes supported Analog Four kit snapshots, and renders style-routing readiness. It does not render mutation values, promote A4 parameter offsets, open MIDI ports, or send hardware messages.

## File Structure

- Create `rytm_randomizer/reports/analog_four_style_snapshot_routing.py`: passive report builder, file decoder helper, slot selector, CLI parser, and registered `CliCommand`.
- Modify `rytm_randomizer/cli.py`: add lazy command registration for `analog-four-style-snapshot-routing-report`.
- Modify `rytm_randomizer/help_text.py`: add usage/help text and safety block wiring.
- Modify `tests/test_analog_four_style_snapshot_routing.py`: report formatting, parser, handler, and error tests.
- Modify `tests/test_cli.py`: command help, subprocess execution, safe error, and README freshness tests.
- Modify `tests/fixtures/cli_help_expected.txt`: top-level CLI help fixture.
- Modify `README.md`, `docs/STATUS.md`, and `docs/ARCHITECTURE_DIAGRAMS.md`: document the passive A4 report surface.
- Modify `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`: include the new report in the prepared PR body.

## Tasks

### Task 1: Report and CLI Tests

**Files:**
- Modify: `tests/test_analog_four_style_snapshot_routing.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Write failing tests**

Cover:
- Operator-facing report includes kit, style, A4 focus, track roles, candidate-only readiness, and safety lines.
- CLI parser accepts default slot and explicit `--slot`.
- CLI parser rejects missing/bad args safely.
- CLI handler reads a local framed SysEx file and reports safely.
- CLI handler reports file/style errors without tracebacks.
- Top-level CLI help and README mention the command.

- [x] **Step 2: Verify red**

Run:

```bash
python -m pytest tests/test_analog_four_style_snapshot_routing.py -n 0
python -m pytest tests/test_cli.py -n 0 -k "analog_four_style_snapshot_routing or cli_help"
```

Expected before implementation: missing report module/CLI command/help fixture failures.

### Task 2: Passive Report Module and CLI Wiring

**Files:**
- Create: `rytm_randomizer/reports/analog_four_style_snapshot_routing.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Implement passive report surface**

Add:
- `format_analog_four_style_snapshot_routing_report(snapshot_or_plan, *, style_key)`
- `decode_supported_analog_four_snapshots_from_path(path)`
- `select_supported_analog_four_snapshot(path, slot, snapshots)`
- CLI parser/handler/error formatter.
- `ANALOG_FOUR_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND`.

The command:
- Reads a local `.syx` file.
- Selects a supported A4 kit snapshot by slot.
- Applies the requested style target.
- Prints metadata-only readiness with explicit candidate-only offset safety.

- [x] **Step 2: Verify green**

Run:

```bash
python -m pytest tests/test_analog_four_style_snapshot_routing.py -n 0
python -m pytest tests/test_cli.py -n 0 -k "analog_four_style_snapshot_routing or cli_help"
```

Expected: focused tests pass.

### Task 3: Documentation and Closeout

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`
- Modify: `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`

- [x] **Step 1: Update operator docs and architecture map**

Document:
- Example command invocation.
- Passive/no-MIDI safety.
- A4 candidate-only mutation block.
- Report module and CLI registry surfaces.

- [x] **Step 2: Focused and closeout verification**

Run:

```bash
python -m pytest tests/test_analog_four_style_snapshot_routing.py --cov=rytm_randomizer.reports.analog_four_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
```

Expected: focused report coverage reaches 100%, architecture/lint/test/coverage/review gates pass.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 - 100% branch coverage on touched report file.
- [x] Gate 2 - V1.34 parity remains untouched; final closeout will run parity through `scripts/code_review_gate.py --mode cli`.
- [x] Gate 3 - lint/format/import checks pass.
- [x] Gate 4 - no new dead code; final closeout includes vulture on touched style/A4 files.
- [x] Gate 5 - README, status, architecture diagrams, and plan docs updated.
- [x] Gate 6 - explicit types and no `Any`.
- [ ] Gate 7 - N/A: passive report only, no hot MIDI send/state-transition path.
- [x] Gate 8 - focused intent-named tests.
- [x] Gate 9 - no new top-level modules; report lives under `reports/`.
- [x] Gate 10 - no new legacy mode/intensity/page dispatch.
- [x] Gate 11 - no duplicate shared fixtures beyond a tiny local A4 SysEx helper.
- [x] Gate 12 - module constants use `Final`.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: report A4 style readiness only.
- [ ] Gate 15 - N/A: no reusable learned skill/rule needed.
- [x] Gate 16 - isolated local worktree; no push/PR while PR #56 is open.
- [x] Gate 17 - reuses style data, A4 snapshot strategy, report formatter, SysEx reader, and CLI registry.
- [x] Gate 18 - architecture diagrams refreshed for the new report and CLI surface.

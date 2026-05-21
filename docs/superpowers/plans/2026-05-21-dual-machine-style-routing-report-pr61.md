# Dual-Machine Style Routing Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive report and CLI command that summarizes style-aware snapshot routing across one Analog Rytm kit dump and one Analog Four kit dump, with optional machine-readable JSON output for future GUI/analyzer consumers.

**Architecture:** Keep this as a report-layer composition over the existing Rytm and A4 style routing strategies. The new report decodes each local SysEx file, selects one supported snapshot per machine, asks the existing strategy layer for per-machine routing plans, and renders a compact rig-level readiness summary as text or JSON. It does not render parameter values, promote A4 offsets, open MIDI ports, or send hardware messages.

**Tech Stack:** Existing `CliCommand`, passive report formatter, Rytm/A4 SysEx decode helpers, Rytm/A4 style-routing strategy plans, pytest, architecture tests, and CLI help fixtures.

---

## Scope

This slice gives operators one command to answer: "If I aim this captured Rytm kit and this captured A4 kit at a style target, what is ready and what remains blocked?" It intentionally stays metadata-only, delegates detailed per-pad/per-track rows to the existing single-machine reports, and exposes JSON for downstream UI/audio-analysis tools without forcing them to scrape text.

## File Structure

- Create `rytm_randomizer/reports/dual_machine_style_snapshot_routing.py`: passive dual-machine report builder, JSON serializer, CLI parser, handler, and registered `CliCommand`.
- Modify `rytm_randomizer/cli.py`: lazy-load the new command.
- Modify `rytm_randomizer/help_text.py`: top-level usage/help text and safety block.
- Modify `tests/test_dual_machine_style_snapshot_routing_report.py`: report, parser, handler, and branch coverage.
- Modify `tests/test_cli.py`: subprocess-level command/help/error tests and README freshness.
- Modify `tests/fixtures/cli_help_expected.txt`: top-level CLI fixture.
- Modify `README.md`, `docs/STATUS.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, and `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`: document the new passive rig-level report.

## Tasks

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_dual_machine_style_snapshot_routing_report.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Write failing tests**

Cover:
- Formatting a combined Rytm/A4 plan shows style, selected kits, ready/blocked counts, rig readiness, and safety lines.
- CLI parser accepts default slots and explicit `--rytm-slot` / `--a4-slot`.
- CLI parser rejects missing/bad args safely.
- CLI handler reads local Rytm and A4 SysEx files and prints the combined report.
- CLI handler reports bad files/styles without tracebacks.
- Top-level CLI help and README mention the command.

- [x] **Step 2: Verify red**

Run:

```bash
python -m pytest tests/test_dual_machine_style_snapshot_routing_report.py -n 0
python -m pytest tests/test_cli.py -n 0 -k "dual_machine_style_snapshot_routing or cli_help"
```

Expected before implementation: missing module/command/help fixture failures.

### Task 2: Passive Report and CLI Command

**Files:**
- Create: `rytm_randomizer/reports/dual_machine_style_snapshot_routing.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Implement report composition**

Add:
- `format_dual_machine_style_snapshot_routing_report(rytm_plan, analog_four_plan, *, style_key)`
- `build_dual_machine_style_snapshot_routing_report(rytm_snapshot, analog_four_snapshot, *, style_key)`
- `_parse_cli_args(argv)`
- `_handle_cli_report(...)`
- `DUAL_MACHINE_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND`

The report:
- Uses existing single-machine style routing strategies.
- Counts Rytm ready/blocked pads and A4 ready/blocked tracks.
- Reports rig-level readiness as "partial", "blocked", or "ready".
- States that A4 offsets are still candidate-only when relevant.

- [x] **Step 2: Verify green**

Run:

```bash
python -m pytest tests/test_dual_machine_style_snapshot_routing_report.py -n 0
python -m pytest tests/test_cli.py -n 0 -k "dual_machine_style_snapshot_routing or cli_help"
```

Expected: focused tests pass.

### Task 3: Docs and Closeout

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`
- Modify: `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`

- [x] **Step 1: Update docs**

Document:
- Example command invocation.
- Passive/no-MIDI safety.
- Relationship to the single-machine reports.
- A4 candidate-only limitation.

- [x] **Step 2: Verification**

Run:

```bash
python -m pytest tests/test_dual_machine_style_snapshot_routing_report.py --cov=rytm_randomizer.reports.dual_machine_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
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

### Task 4: Machine-Readable JSON Payload

**Files:**
- Modify: `rytm_randomizer/reports/dual_machine_style_snapshot_routing.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `tests/test_dual_machine_style_snapshot_routing_report.py`
- Modify: `tests/test_cli.py`
- Modify: `README.md`, `docs/STATUS.md`, and this plan.

- [x] **Step 1: Write failing tests**

Cover:
- A deterministic JSON contract with style key, rig readiness, per-machine kit/slot/ready/blocked counts, A4 candidate-only state, and safety metadata.
- CLI parser support for `--json`.
- CLI handler and subprocess command output valid JSON without text headers.

Red run:

```bash
python -m pytest tests/test_dual_machine_style_snapshot_routing_report.py tests/test_cli.py -n 0 -k "dual_machine_style_snapshot_routing or cli_help"
```

Expected before implementation: 4 failures for missing serializer, parser flag, handler argument, and JSON output.

- [x] **Step 2: Implement `--json`**

Add:
- `to_dual_machine_style_snapshot_routing_json(plan)`
- `--json` parser flag.
- JSON branch in `_handle_cli_report(...)` using sorted, indented output.

- [x] **Step 3: Focused verification**

Run:

```bash
python -m pytest tests/test_dual_machine_style_snapshot_routing_report.py tests/test_cli.py -n 0 -k "dual_machine_style_snapshot_routing or cli_help"
```

Expected: focused text + JSON command coverage passes.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 - 100% branch coverage on touched report file.
- [x] Gate 2 - V1.34 parity remains untouched; final closeout runs parity through `scripts/code_review_gate.py --mode cli`.
- [x] Gate 3 - lint/format/import checks pass.
- [x] Gate 4 - no new dead code; final closeout includes vulture on touched dual-machine report/test files.
- [x] Gate 5 - README, status, architecture diagrams, and plan docs updated.
- [x] Gate 6 - explicit types and no `Any`.
- [ ] Gate 7 - N/A: passive report only, no hot MIDI send/state-transition path.
- [x] Gate 8 - focused intent-named tests.
- [x] Gate 9 - no new top-level modules; report lives under `reports/`.
- [x] Gate 10 - no new legacy mode/intensity/page dispatch.
- [x] Gate 11 - test helpers reuse existing Rytm fixture payloads and tiny local A4 framed payloads.
- [x] Gate 12 - module constants use `Final`.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: rig-level report/JSON only, no mutation rendering.
- [ ] Gate 15 - N/A: no reusable learned skill/rule needed.
- [x] Gate 16 - isolated local worktree; no push/PR while PR #56 is open.
- [x] Gate 17 - reuses existing Rytm/A4 routing strategies, report formatter, SysEx readers, JSON stdlib, and CLI registry.
- [x] Gate 18 - architecture diagrams refreshed for the new report and CLI surface.

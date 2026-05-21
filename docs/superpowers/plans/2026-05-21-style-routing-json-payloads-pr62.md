# Style Routing JSON Payloads Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic `--json` output to the Rytm and Analog Four style-routing reports so GUI/audio-analyzer consumers can read structured per-pad and per-track routing data without scraping text.

**Architecture:** Keep JSON serialization inside the existing passive report modules. Reuse existing style-routing plan dataclasses and CLI command registration; do not add mutation rendering, MIDI output, new top-level modules, or hardware behavior.

**Tech Stack:** Existing passive CLI registry, Rytm/A4 style-routing report modules, stdlib `json`, pytest, architecture tests, and CLI help fixtures.

---

## Scope

This slice turns the existing single-machine style-routing reports into dual-purpose operator/API surfaces:

- Text remains the default operator-facing report.
- `--json` emits stable machine-readable payloads with style key, selected kit/slot, readiness counts, favored zones, per-pad/per-track details, candidate summaries, and safety metadata.
- Dual-machine JSON already exists in the previous local checkpoint and remains the rig-level summary surface.

## File Structure

- Modify `rytm_randomizer/reports/rytm_style_snapshot_routing.py`: add JSON serializer, parser flag, and handler output branch.
- Modify `rytm_randomizer/reports/analog_four_style_snapshot_routing.py`: add JSON serializer, parser flag, and handler output branch.
- Modify `rytm_randomizer/help_text.py` and `tests/fixtures/cli_help_expected.txt`: document `--json`.
- Modify `tests/test_rytm_style_snapshot_routing.py`, `tests/test_analog_four_style_snapshot_routing.py`, and `tests/test_cli.py`: cover serializers, parsers, handler JSON, and subprocess JSON output.
- Modify `README.md`, `docs/STATUS.md`, and `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`: document the structured output.

## Tasks

### Task 1: Failing Tests

- [x] **Step 1: Write failing tests**

Cover:
- Rytm JSON serializer exposes per-pad route readiness and candidate lists.
- Analog Four JSON serializer exposes per-track role/readiness details.
- Both parsers accept `--json`.
- Both handlers and subprocess commands output valid JSON without text report headers.

- [x] **Step 2: Verify red**

Run:

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py tests/test_analog_four_style_snapshot_routing.py tests/test_cli.py -n 0 -k "style_snapshot_routing or rytm_style_snapshot_routing or analog_four_style_snapshot_routing or cli_help"
```

Expected before implementation: failures for missing serializers, missing parser flags, and unsupported handler JSON args.

### Task 2: Implement JSON Output

- [x] **Step 1: Add serializers and CLI branches**

Add:
- `to_rytm_style_snapshot_routing_json(plan)`
- `to_analog_four_style_snapshot_routing_json(plan)`
- `--json` support in both parsers.
- Sorted, indented JSON output in both handlers.

- [x] **Step 2: Focused verification**

Run:

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py tests/test_analog_four_style_snapshot_routing.py tests/test_cli.py -n 0 -k "style_snapshot_routing or rytm_style_snapshot_routing or analog_four_style_snapshot_routing or cli_help"
```

Expected: focused text + JSON coverage passes.

### Task 3: Closeout

- [x] **Step 1: Final verification**

Run:

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py --cov=rytm_randomizer.reports.rytm_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
python -m pytest tests/test_analog_four_style_snapshot_routing.py --cov=rytm_randomizer.reports.analog_four_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
python -m vulture rytm_randomizer\reports\rytm_style_snapshot_routing.py rytm_randomizer\reports\analog_four_style_snapshot_routing.py tests\test_rytm_style_snapshot_routing.py tests\test_analog_four_style_snapshot_routing.py --min-confidence 80
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

- [x] Gate 1 - 100% branch coverage expected on touched report files.
- [x] Gate 2 - V1.34 parity remains untouched; closeout runs parity through `scripts/code_review_gate.py --mode cli`.
- [x] Gate 3 - lint/format/import checks required before commit.
- [x] Gate 4 - vulture clean on touched report/test files.
- [x] Gate 5 - README, status, plan docs, and CLI help fixtures updated.
- [x] Gate 6 - explicit typed dict payloads with no `Any`.
- [ ] Gate 7 - N/A: passive report output only, no hot MIDI path.
- [x] Gate 8 - focused tests cover parser, serializer, handler, and subprocess output.
- [x] Gate 9 - no new top-level modules.
- [x] Gate 10 - no legacy string-literal mode/intensity dispatch.
- [x] Gate 11 - existing fixture helpers reused.
- [x] Gate 12 - existing module constants remain `Final`.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: JSON output only, no mutation rendering.
- [ ] Gate 15 - N/A: no reusable learned skill/rule needed.
- [x] Gate 16 - local-only checkpoint while PR #56 is open; no push/stacked PR.
- [x] Gate 17 - reuses existing Rytm/A4 plan dataclasses, report modules, stdlib JSON, and CLI registry.
- [x] Gate 18 - no new architecture surface; existing report/CLI surfaces documented.

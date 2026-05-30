# Style Selection Snapshot Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive bridge from dual-machine style kit selection to mock preview so a live operator can choose a style, let the software pick the ranked Rytm/A4 kit candidate, and inspect the resulting mock mutation rows without manually copying kit slots between reports.

**Architecture:** Reuse the existing dual-machine style kit selection report plus the existing single-machine Rytm and Analog Four mock preview builders. Keep the new behavior in `rytm_randomizer/reports/`; do not add a new device family surface, MIDI rendering path, port opening, or hardware mutation.

**Tech Stack:** Existing passive CLI registry, saved-kit SysEx report layers, style target catalog, single-machine mock preview strategies, stdlib `json`, pytest, architecture tests, and README/status documentation.

---

## Scope

This slice makes the saved-kit live workflow feel like one operation:

- `dual-machine-style-selection-mock-preview-report` selects the best ranked style kit candidate by default.
- `--rank N` auditions lower-ranked candidates without manually copying Rytm/A4 slots into another command.
- `--scope rytm-only` and `--scope analog-four-only` support snapshot workflows where one machine is mutated and the other stays unchanged.
- `--events`, `--limit N`, and `--json` expose the same operator/API affordances as the existing mock preview reports.
- The path remains passive and mock-only; decoded A4 SysEx rows stay candidate-only until offset promotion.

## File Structure

- Add `rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py`: selection-to-preview builder, formatter, JSON serializer, and CLI command.
- Modify `rytm_randomizer/cli.py`: lazy-register the new passive command.
- Modify `rytm_randomizer/help_text.py` and `tests/fixtures/cli_help_expected.txt`: document usage and command help.
- Modify `tests/test_dual_machine_style_selection_mock_preview_report.py`, `tests/test_cli.py`, `tests/test_cli_coverage.py`, and `tests/test_real_midi_passive_cli_safety.py`: cover builder, formatter, JSON, CLI help, lazy import, and passive safety.
- Modify `README.md` and `docs/STATUS.md`: document the operator-facing command.

## Tasks

### Task 1: Failing Tests

- [x] **Step 1: Write failing tests**

Cover:
- Dual-machine best-ranked candidate produces Rytm and A4 preview sections.
- Rytm-only scope omits A4 preview and reports the A4 machine unchanged.
- Analog Four-only scope omits Rytm preview and reports the Rytm unchanged.
- `--rank N` selects a lower-ranked candidate.
- JSON exposes selection metadata, totals, machine previews, and safety metadata.
- CLI help, lazy import, README mention, and passive real-MIDI safety include the new command.

- [x] **Step 2: Verify red**

Run:

```bash
python -m pytest tests/test_dual_machine_style_selection_mock_preview_report.py -n 0
python -m pytest tests/test_dual_machine_style_selection_mock_preview_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected before implementation: missing module, then missing CLI/help/docs wiring.

### Task 2: Implement Selection Mock Preview

- [x] **Step 1: Add the passive report module**

Add:
- `build_dual_machine_style_selection_mock_preview_report(...)`
- `format_dual_machine_style_selection_mock_preview_report(...)`
- `to_dual_machine_style_selection_mock_preview_json(...)`
- CLI parser/handler with `--rank`, `--scope`, `--events`, `--limit`, and `--json`.

- [x] **Step 2: Wire public CLI surface**

Add lazy CLI registration, static help text, top-level help fixture rows, README example, and status note.

### Task 3: Closeout

- [x] **Step 1: Final verification**

Run:

```bash
python -m pytest tests/test_dual_machine_style_selection_mock_preview_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/test_dual_machine_style_selection_mock_preview_report.py --cov=rytm_randomizer.reports.dual_machine_style_selection_mock_preview --cov-branch --cov-report=term-missing -n 0
python -m vulture rytm_randomizer\reports\dual_machine_style_selection_mock_preview.py tests\test_dual_machine_style_selection_mock_preview_report.py --min-confidence 80
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
```

Expected: focused report coverage reaches 100%, architecture/lint/test/coverage/review gates pass, and the PR is ready for human review.

## Plan-Requirements Conformance

- [x] Gate 1 - 100% branch coverage expected on touched report files.
- [x] Gate 2 - V1.34 parity remains untouched; closeout runs parity through `scripts/code_review_gate.py --mode cli`.
- [x] Gate 3 - lint/format/import checks required before commit.
- [x] Gate 4 - vulture clean on touched report/test files.
- [x] Gate 5 - README, status, plan docs, and CLI help fixtures updated.
- [x] Gate 6 - explicit dataclasses/typed payload dictionaries with no `Any`.
- [ ] Gate 7 - N/A: passive report output only, no hot MIDI path.
- [x] Gate 8 - focused tests cover builder, formatter, parser, handler, JSON, and subprocess output.
- [x] Gate 9 - no new top-level modules.
- [x] Gate 10 - no legacy string-literal mode/intensity dispatch.
- [x] Gate 11 - existing fixture helpers reused.
- [x] Gate 12 - module constants use existing report patterns.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: selection-to-preview bridge only, no real renderer.
- [ ] Gate 15 - N/A: no reusable learned skill/rule needed.
- [x] Gate 16 - clean-base branch from `origin/modularize-v1.34`; no stacked PR.
- [x] Gate 17 - reuses existing kit selection, Rytm mock preview, and A4 mock preview abstractions.
- [x] Gate 18 - no new architecture surface; existing report/CLI surfaces documented.

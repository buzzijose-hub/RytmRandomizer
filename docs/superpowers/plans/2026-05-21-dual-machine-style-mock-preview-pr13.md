# Dual-Machine Style Mock Preview PR13

## Goal

Add one passive rig-level report that combines the existing Rytm style mutation mock preview and Analog Four style mutation mock preview into a single operator-facing view. This gives the future GUI/live engine one place to ask: "for this Rytm kit, this A4 kit, and this style target, what would the rig try to move?"

## Scope

- Add `dual-machine-style-mutation-mock-preview-report`.
- Accept one Rytm SysEx path, one Analog Four SysEx path, a style key, optional Rytm/A4 slots, discovery amount, event preview flag, event limit, and JSON mode.
- Reuse the existing Rytm and Analog Four single-machine mock preview builders.
- Stay passive/mock-only: no MIDI port opening, no real senders, no hardware mutation.
- Surface rig readiness, per-machine readiness, mock-message totals, deferred Analog Four rows, and capped event previews.

## Non-Goals

- No live hardware path.
- No new device family abstraction.
- No A4 offset promotion.
- No NRPN rendering.
- No V1.34 parity fixture regeneration.

## Architecture

- New report module lives under `rytm_randomizer/reports/`.
- CLI registration goes through `cli_registry` lazy loading in `rytm_randomizer/cli.py`.
- Help text remains static in `rytm_randomizer/help_text.py`.
- Data comes from:
  - `build_rytm_style_mutation_mock_preview`
  - `build_analog_four_style_mutation_mock_preview`
  - existing Rytm/A4 SysEx snapshot selectors

## TDD Plan

1. RED: add focused tests for the new report builder, formatter, JSON payload, parser, CLI handler, and passive help/dispatch coverage.
2. GREEN: implement the smallest report module and CLI/help wiring to satisfy those tests.
3. REFACTOR: keep formatting deterministic and avoid duplicating single-machine report internals beyond row labels.
4. VERIFY: run focused tests, architecture tests, fast/full suite, coverage, lint, and review gates before commit/push.

## Verification Commands

```bash
python -m pytest tests/test_dual_machine_style_mutation_mock_preview_report.py -n 0
python -m pytest tests/test_dual_machine_style_mutation_mock_preview_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python scripts/code_review_gate.py --mode cli
```

## Review Notes

- Existing checkout line-ending noise is unrelated and must not be staged.
- This is intentionally a larger PR than the last few slices, but it remains one logical passive report.

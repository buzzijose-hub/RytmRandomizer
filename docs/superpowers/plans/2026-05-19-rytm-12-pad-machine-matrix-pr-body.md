# Summary

Adds a passive Analog Rytm MK2 12-pad machine compatibility matrix. The new data/report/CLI surface validates 33 selectable machines, 12 pads, and 116 legal pad-machine slots from the OS 1.72 pad table. Pad 10 is explicitly represented as OH / Open Hihat; XT Classic remains limited to pads 6-8.

## What changed

- Added `rytm_randomizer/data/rytm_machine_catalog.py` as the passive Rytm OS 1.72 machine/pad compatibility source of truth.
- Added `rytm_randomizer/reports/rytm_machine_matrix.py` for the passive operator report.
- Added `python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report`.
- Updated README/status docs and passive CLI safety coverage.

## Why this matters

This is the safe foundation for 12-pad Rytm mutation, snapshot-mode mutation, and audio-analyzer machine selection. It gives the software an auditable legality map before any armed 12-pad runtime sends are enabled.

## Test plan

```bash
python -m pytest tests/test_data_rytm_machine_catalog.py tests/test_rytm_machine_matrix_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [x] Local pytest passes (full suite).
- [x] `tests/architecture/` passes.
- [x] Lint trio (ruff + black + isort) clean.
- [x] Coverage stays >=95 percent pure-branch.
- [x] 685/685 V1.34 parity items byte-identical.
- [x] No new dead code.
- [ ] CI matrix green on all 3 OSes.

## Plan-requirements conformance

- [x] **Gate 1** - 100 percent branch coverage on touched files; project >=95 percent pure-branch.
- [x] **Gate 2** - V1.34 parity byte-identical; no fixtures regenerated.
- [x] **Gate 3** - lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [x] **Gate 4** - no new dead code.
- [x] **Gate 5** - docs updated: `README.md`, `docs/STATUS.md`, design doc, implementation plan.
- [x] **Gate 6** - type-system hygiene: frozen dataclasses, `Final` constants, no bare `Any`.
- [ ] **Gate 7** - N/A: passive report/data path, no hot runtime path.
- [x] **Gate 8** - test hygiene: focused fast tests with clear behavior names.
- [x] **Gate 9** - module organization: data/report subpackages only, no new top-level package.
- [ ] **Gate 10** - N/A: no string-literal runtime dispatch refactor.
- [ ] **Gate 11** - N/A: no shared fixture additions.
- [x] **Gate 12** - `Final` constants on module-level constants.
- [ ] **Gate 13** - N/A: no env var reads.
- [x] **Gate 14** - maintainability: scope bounded to one passive data/report/CLI surface.
- [ ] **Gate 15** - N/A: no new reusable learned rule extracted.
- [x] **Gate 16** - one branch/one PR against `modularize-v1.34`; no stacked PR.

## Strict rules - non-negotiables

- [x] **No hardware in tests** - no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** - no new eager `mido` or `python-rtmidi` imports.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** - `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** - this PR's base is `modularize-v1.34`.
- [x] **No `--no-verify`** - pre-commit hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-05-19-rytm-12-pad-machine-matrix.md`

Design doc: `docs/superpowers/specs/2026-05-19-rytm-12-pad-machine-matrix-design.md`

## Reviewer notes

- Passive/read-only only.
- No hardware sends.
- No V1.34 parity fixture regeneration.
- No new top-level package.

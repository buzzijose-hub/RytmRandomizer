# Summary

Adds a mock-safe operator package apply acknowledgement to the Cockpit WebSocket bridge. This follows the merged apply-preview work by letting the UI rehearse "accepting" an operator package while still proving that no MIDI port opens, no MIDI is sent, no files are written, no send plan is applied, and no snapshot is mutated.

## What changed

- Added the typed `mock_apply_operator_package` Cockpit WebSocket command and
  `operator_package_mock_apply` ack payload.
- Reused the current operator-package validation path for package id, selected
  step keys, package export-key bindings, snapshot id, and `mock_safe: true`.
- Returned deterministic mock-apply evidence for selected package steps,
  readiness checks, recovery requirements, blocked actions, safety lines, and
  a dry-run summary.
- Proved the mock apply path does not open a MIDI port, send MIDI, write files,
  mutate snapshots, apply send plans, or emit events.
- Added the Performance Console button, local operator-log handling, and
  mock-apply review panel beside the existing sequence rehearsal/apply-preview
  controls.
- Updated README, CLI reference, project status, and this plan/PR package.

## Why this matters

The live-performance cockpit is becoming the operator surface for Jose's OXI + RytmRandomizer workflow. The apply preview showed what would happen; this bundle adds the next mock-only acknowledgement step so the UI can separate "reviewed" from "mock accepted" before any future real SEND path is designed.

## Test plan

```bash
python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py tests/cockpit/test_integration_protocol_roundtrip.py tests/cockpit/test_ws_wizard_protocol.py -q -n 0
npm.cmd test -- --run tests/ws-client.test.ts tests/cockpit/PerformanceConsole.test.tsx
python -m pytest tests/architecture/ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

- [x] Focused Cockpit backend tests: `167 passed in 1.82s`.
- [x] Focused Cockpit web tests: `2 passed (2 files), 123 passed (123 tests)`.
- [x] Local pytest passes: `5781 passed, 3 skipped`.
- [x] `tests/architecture/` passes: `622 passed` with the existing warn-only duplicate `main` note.
- [x] Lint trio clean: ruff, black, and isort exit 0.
- [x] Coverage stays >=95% pure-branch: normal coverage run reached 98.80%; touched `rytm_randomizer.cockpit.ws.handlers` is 100% branch-covered.
- [x] V1.34 parity stays byte-identical via the full pytest suite; no parity fixture regeneration.
- [x] No new dead code: `python -m vulture rytm_randomizer/ tests/ --min-confidence 80` exits 0.
- [ ] CI matrix green on all 3 OSes: pending GitHub Actions after PR creation.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md` - every non-trivial PR must satisfy all 18 gates. Mark each `[x]`, or `[ ] N/A - <reason>`.

- [x] **Gate 1** - 100% branch coverage on touched Python handler file; project coverage floor passes at 98.80%.
- [x] **Gate 2** - V1.34 parity byte-identical (full pytest suite passes; no fixture regeneration).
- [x] **Gate 3** - lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [x] **Gate 4** - no new dead code (vulture --min-confidence 80 exits 0).
- [x] **Gate 5** - docs updated (`README.md`, `docs/CLI_REFERENCE.md`, `docs/STATUS.md`, plan/PR body).
- [x] **Gate 6** - type-system hygiene (TypedDict-style protocol additions, `Final` constants, no new `Any` escape hatch).
- [x] **Gate 7** - N/A: this adds a mock-safe ack bridge and GUI receipt, not a metrics hot path.
- [x] **Gate 8** - test hygiene (focused backend/frontend tests cover success, validation, no-side-effect, rejection, and transport failure paths).
- [x] **Gate 9** - module-organization hygiene (no new top-level modules).
- [x] **Gate 10** - string-literal dispatch hygiene (command constants added to existing protocol registry).
- [x] **Gate 11** - shared fixtures (uses existing test helpers; no duplicated shared fixture introduced).
- [x] **Gate 12** - `Final` constants on module-level constants.
- [x] **Gate 13** - N/A: no new environment variables.
- [x] **Gate 14** - maintainability review (bounded extension of existing operator-package bridge; no new architecture surface).
- [x] **Gate 15** - N/A: no new reusable learned skill/rule required.
- [x] **Gate 16** - execution shape (single clean-base branch and one bundled PR).
- [x] **Gate 17** - abstraction reuse: reused Cockpit WS protocol/handler/session, operator-package helpers, Performance Console, and existing validation patterns.
- [x] **Gate 18** - N/A: no new architecture surface or diagram-count change; docs/status/CLI references updated.

## Strict rules - non-negotiables

Per `CONTRIBUTING.md` Strict rules - confirm each:

- [x] **No hardware in tests** - no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** - `mido` and `python-rtmidi` imported only inside `real_midi_adapter.py` / `mido_provider.py`.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** - `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** - this PR's base is `modularize-v1.34`.
- [x] **No `--no-verify`** - pre-commit hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-06-22-operator-package-mock-apply-bundle.md`

## Reviewer notes

This is intentionally mock-only. It does not add a real hardware apply path and does not promote any Cockpit UI control into SEND authority.

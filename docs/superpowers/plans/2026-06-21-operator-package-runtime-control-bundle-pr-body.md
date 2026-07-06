# Summary

Adds the next mock-safe Operator Package runtime-control layer. The Cockpit
can now rehearse the whole current operator package sequence through a typed
WebSocket command while staying passive: no MIDI port opened, no MIDI sent, no
files written, no snapshot mutation, and no hardware arm behavior changed.

## What changed

- Added the `rehearse_operator_package_sequence` WebSocket command, typed
  payload, and `CommandAck.operator_package_sequence_rehearsal` response
  contract.
- Reused the passive Live Kit Operator Package report as the source of truth
  for sequence validation: package id, selected step keys, package export-key
  bindings, and `mock_safe: true`.
- Tightened the existing `rehearse_operator_package_step` command so stale
  `package_export_key` values are rejected instead of silently ignored.
- Wired the Performance Console with a mock-safe "Rehearse operator package
  sequence" control that sends all package steps and logs the sidecar ack or
  rejection in the local operator log.
- Added frontend and backend tests for protocol shape, command routing,
  validation failures, side-effect boundaries, and UI command/log behavior.
- Updated `README.md`, `docs/STATUS.md`, and added the plan doc at
  `docs/superpowers/plans/2026-06-21-operator-package-runtime-control-bundle.md`.

## Why this matters

The operator package now has a runtime preflight at the same shape Jose would
use live: "validate this whole package of staged moves." That gives the future
active apply/send work a stable contract without jumping ahead to hardware
behavior.

## Test plan

```bash
python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py tests/cockpit/test_integration_protocol_roundtrip.py -q -n 0
npm.cmd test -- --run tests/ws-client.test.ts tests/cockpit/PerformanceConsole.test.tsx
python -m pytest tests/architecture/ -q
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
npm.cmd run build
npm.cmd test -- --run
npm.cmd run test:coverage
```

- [x] Focused Python cockpit protocol/handler/round-trip tests pass: 122 passed.
- [x] Focused web protocol/Performance Console tests pass: 103 passed.
- [x] Local pytest passes (full suite): 5755 passed, 3 skipped.
- [x] `tests/architecture/` passes: 622 passed.
- [x] Lint trio (ruff + black + isort) clean.
- [x] Coverage stays >=95% pure-branch; touched behavior covered by focused tests (`python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing` -> 5755 passed, 3 skipped, 98.77% total coverage).
- [x] V1.34 parity items byte-identical via full pytest.
- [x] `npm.cmd run build` passes.
- [x] `npm.cmd test -- --run` passes: 437 passed.
- [x] `npm.cmd run test:coverage` passes: 437 passed with 100% statements/branches/functions/lines.
- [x] `git diff --check` clean.
- [ ] CI matrix green on all 3 OSes: N/A until GitHub Actions runs on this PR.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md` -- every non-trivial PR must satisfy all 18
gates. Mark each `[x]`, or `[ ] N/A -- <reason>`.

- [x] **Gate 1** -- 100% branch coverage on touched files; project >=95% pure-branch.
- [x] **Gate 2** -- V1.34 parity byte-identical (505 goldens / 685 pytest items).
- [x] **Gate 3** -- lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [x] **Gate 4** -- no new dead code (vulture --min-confidence 80).
- [x] **Gate 5** -- docs updated (`README.md`, `docs/STATUS.md`, relevant `docs/` reflect the change).
- [x] **Gate 6** -- type-system hygiene (Protocol over ABC, `Final` constants, no bare `Any`).
- [x] **Gate 7** -- observability adoption (no new hot-path hardware/state transition; ack-only validation path).
- [x] **Gate 8** -- test hygiene (`test_<unit>_<behavior>_when_<condition>` naming; shared fixtures reused).
- [x] **Gate 9** -- module-organization hygiene (no new top-level modules).
- [x] **Gate 10** -- string-literal dispatch hygiene (no new mode/intensity dispatch).
- [x] **Gate 11** -- shared fixtures (existing cockpit fixtures reused).
- [x] **Gate 12** -- `Final` constants on module-level constants.
- [x] **Gate 13** -- env var docs (no new env vars).
- [x] **Gate 14** -- maintainability review (captured in the plan doc).
- [x] **Gate 15** -- learning capture (no new reusable learned-skill pattern required).
- [x] **Gate 16** -- execution shape (single clean-base branch/PR; no stacked PR).
- [x] **Gate 17** -- abstraction reuse: reused Cockpit WS protocol, handler registry, passive package report, and Performance Console callback seam.
- [x] **Gate 18** -- architecture-doc + diagram freshness: no new architecture boundary; existing Cockpit WS/package bridge documented in README/status/plan.

## Strict rules -- non-negotiables

Per `CONTRIBUTING.md` section Strict rules -- confirm each:

- [x] **No hardware in tests** -- no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** -- `mido` and `python-rtmidi` imported only inside `real_midi_adapter.py` / `mido_provider.py`.
- [x] **Hardware-pinned packages** -- `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** -- `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** -- this PR's base is `modularize-v1.34`, not another open PR's head.
- [x] **No `--no-verify`** -- pre-commit hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-06-21-operator-package-runtime-control-bundle.md`

## Reviewer notes

- The new sequence command is intentionally ack-only and mock-safe.
- The handler validates export-key bindings so stale UI/package state is caught
  before active package apply/send work exists.
- Frontend local staging remains separate; the sequence rehearsal control only
  records sidecar evidence in the local operator log.

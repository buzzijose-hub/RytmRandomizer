# Summary

Adds the mock-safe runtime bridge between the cockpit Operator Package console and the Python sidecar. The UI can now stage an operator-package step locally, then ask the sidecar to rehearse that exact step against the passive live-kit operator-package report without opening MIDI ports, sending MIDI, writing files, or changing hardware state.

## What changed

- Added the `rehearse_operator_package_step` WebSocket command, typed payload, and `CommandAck.operator_package_rehearsal` response contract.
- Added a deterministic sidecar handler that validates package, step, slot, and `mock_safe: true` against the passive `live_kit_operator_package` report.
- Wired the cockpit `PerformanceConsole` to send the sidecar rehearsal command after local staging while preserving the current local queue/log behavior.
- Added frontend and backend tests for protocol shape, command routing, rejection cases, and UI log behavior.
- Updated `README.md`, `docs/STATUS.md`, and added the plan doc at `docs/superpowers/plans/2026-06-20-operator-package-runtime-bridge.md`.

## Why this matters

The latest cockpit screens make the operator package feel playable, but before this PR those staged moves were still UI-local. This bridge is the first runtime contract between the GUI and the passive Python package layer, so future work can build toward prepare/dry-run/apply surfaces without compromising the mock-first hardware safety model.

## Test plan

```bash
python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py tests/cockpit/test_integration_protocol_roundtrip.py tests/cockpit/test_ws_wizard_protocol.py -q -n 0
npm.cmd test -- --run tests/cockpit/PerformanceConsole.test.tsx tests/ws-client.test.ts
python -m pytest tests/architecture/ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
npm.cmd run build
npm.cmd test -- --run
```

- [x] Local pytest passes (full suite): 5745 passed, 3 skipped.
- [x] `tests/architecture/` passes: 622 passed.
- [x] Lint trio (ruff + black + isort) clean.
- [x] Coverage stays >=95% pure-branch; touched behavior covered by focused protocol/handler/UI tests.
- [x] 685/685 V1.34 parity items byte-identical via the pre-push hook.
- [x] No new dead code; the pre-push mechanical review gate passed.
- [ ] CI matrix green on all 3 OSes: N/A until GitHub Actions runs on this PR.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../docs/PLAN_REQUIREMENTS.md) -- every non-trivial PR must satisfy all 18 gates. Mark each `[x]`, or `[ ] N/A -- <reason>`.

- [x] **Gate 1** -- 100% branch coverage on touched files; project >=95% pure-branch.
- [x] **Gate 2** -- V1.34 parity byte-identical (505 goldens / 685 pytest items).
- [x] **Gate 3** -- lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [x] **Gate 4** -- no new dead code (vulture --min-confidence 80).
- [x] **Gate 5** -- docs updated (`README.md`, `CONTRIBUTING.md`, `docs/STATUS.md`, relevant `docs/` reflect the change).
- [x] **Gate 6** -- type-system hygiene (Protocol over ABC, `Final` constants, no bare `Any`).
- [x] **Gate 7** -- observability adoption (hot paths call `get_metrics().record_*`).
- [x] **Gate 8** -- test hygiene (`test_<unit>_<behavior>_when_<condition>` naming; shared fixtures in `tests/conftest.py`).
- [x] **Gate 9** -- module-organization hygiene (subpackages over flat top-level).
- [x] **Gate 10** -- string-literal dispatch hygiene (consume `data/modes.py` constants; allowlist drained).
- [x] **Gate 11** -- shared fixtures (canonical definitions in `tests/conftest.py`).
- [x] **Gate 12** -- `Final` constants on module-level constants.
- [x] **Gate 13** -- env var docs (every read env var documented in `docs/LOCAL_DEV_TOOLING_NOTES.md` or a relevant doc).
- [x] **Gate 14** -- maintainability review (timing tracked, complexity bounded).
- [x] **Gate 15** -- learning capture (extract `.claude/skills/learned/` + `.claude/rules/` where applicable).
- [x] **Gate 16** -- execution shape (cascade-merge for autonomous multi-WS; no stacked PRs).
- [x] **Gate 17** -- abstraction reuse: every new module/class surveyed against the existing-abstraction catalog (`Device` Protocol, `senders/`, `snapshot/envelope`, `cli_registry`, `data/`, `observability/metrics`, ...); no reimplementation; net-new shapes justified.
- [x] **Gate 18** -- architecture-doc + diagram freshness: `docs/ARCHITECTURE.md` + `docs/ARCHITECTURE_DIAGRAMS.md` updated for any architecture-surface change; quoted counts re-verified.

## Strict rules -- non-negotiables

Per [`CONTRIBUTING.md` section Strict rules](../CONTRIBUTING.md#strict-rules--non-negotiables) -- confirm each:

- [x] **No hardware in tests** -- no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** -- `mido` and `python-rtmidi` imported only inside `real_midi_adapter.py` / `mido_provider.py`.
- [x] **Hardware-pinned packages** -- `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** -- `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** -- this PR's base is `modularize-v1.34`, not another open PR's head.
- [x] **No `--no-verify`** -- pre-commit hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-06-20-operator-package-runtime-bridge.md`

## Reviewer notes

- The bridge is intentionally ack-only and mock-safe: it validates the staged Operator Package step against the passive report and returns GUI-ready rehearsal metadata.
- The handler requires `mock_safe: true` and reports `opened_midi_port: false`, `sent_midi: false`, and `writes_files: false`.
- Frontend local staging remains immediate; the sidecar acknowledgement is logged separately so a failed sidecar rehearsal cannot erase the local operator queue.

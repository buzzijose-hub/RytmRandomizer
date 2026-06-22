# Summary

Adds the next mock-safe Operator Package runtime-control layer: the Cockpit can ask the Python sidecar for a whole-package Apply Preview ack before any real package apply/send path exists. The ack is deterministic evidence only: ordered apply steps with validated export keys, readiness checks, recovery requirements, blocked real-send actions, safety lines, dry-run summary, and proof that no MIDI port opened, no MIDI was sent, and no package file was written.

Local verification is complete; CI remains the post-push confirmation gate.

## What changed

- Add the `preview_operator_package_apply` WebSocket command and the `operator_package_apply_preview` ack contract.
- Reuse the PR #193 Operator Package runtime-control validation seam: current package id, selected step keys, package export-key bindings, and `mock_safe: true`.
- Return deterministic apply-preview evidence for the whole package without opening ports, sending MIDI, writing files, mutating snapshots, applying send plans, or arming hardware.
- Render a Performance Console Apply Preview control that asks the sidecar for the package-level preview and logs either the ack or categorical rejection.
- Add backend and frontend tests for protocol shape, command routing, validation failures, side-effect boundaries, and UI command/log behavior.
- Update `README.md`, `docs/CLI_REFERENCE.md`, `docs/STATUS.md`, and the plan doc at `docs/superpowers/plans/2026-06-22-operator-package-apply-preview-bundle.md`.

## Why this matters

PR #193 proved the runtime-control bridge can validate the current Operator Package sequence as one unit. This PR prepares the next active path safely by previewing the apply plan shape before any hardware apply/send behavior is promoted.

## Test plan

Verified local commands:

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

- [x] Focused Python cockpit protocol/handler/round-trip tests pass (`151 passed`).
- [x] Focused web protocol/Performance Console tests pass (`113 passed`).
- [x] Local pytest passes (full suite: `5765 passed, 3 skipped`).
- [x] `tests/architecture/` passes (`622 passed`).
- [x] Lint trio (ruff + black + isort) clean.
- [x] Coverage stays >=95% pure-branch, with 100% branch coverage on touched production files (`98.77%` Python total, `100%` frontend statements/branches/functions/lines).
- [x] V1.34 parity items byte-identical via full pytest; no fixture regeneration.
- [x] `npm.cmd run build` passes.
- [x] `npm.cmd test -- --run` passes (`442 passed` before the coverage-only defensive tests; coverage run reports `447 passed`).
- [x] `npm.cmd run test:coverage` passes (`100%` frontend coverage).
- [x] `git diff --check` clean.
- [ ] CI matrix green on all required jobs after push.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md` -- every non-trivial PR must satisfy all 18 gates. Mark each item only after implementation evidence exists, or convert to explicit N/A with a one-line reason.

- [x] **Gate 1** -- 100% branch coverage on touched files; project >=95% pure-branch.
- [x] **Gate 2** -- V1.34 parity byte-identical (505 goldens / 685 pytest items); no fixture regeneration.
- [x] **Gate 3** -- lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [x] **Gate 4** -- no new dead code (covered by architecture/full-suite gates for touched surfaces).
- [x] **Gate 5** -- docs updated (`README.md`, `docs/CLI_REFERENCE.md`, `docs/STATUS.md`, relevant `docs/` reflect the change).
- [x] **Gate 6** -- type-system hygiene (Protocol/TypedDict/frozen DTO patterns, `Final` constants, no bare `Any`).
- [x] **Gate 7** -- observability adoption (no new active hot path; categorical handler rejections remain visible through existing command ack/log patterns).
- [x] **Gate 8** -- test hygiene (`test_<unit>_<behavior>_when_<condition>` naming; shared fixtures reused).
- [x] **Gate 9** -- module-organization hygiene (no new top-level modules).
- [x] **Gate 10** -- string-literal dispatch hygiene (no new mode/intensity/page string dispatch).
- [x] **Gate 11** -- shared fixtures (existing cockpit/web fixtures reused).
- [x] **Gate 12** -- `Final` constants on module-level constants where new constants are added.
- [x] **Gate 13** -- env var docs (no new env vars).
- [x] **Gate 14** -- maintainability review (captured in the plan doc).
- [x] **Gate 15** -- learning capture (no new reusable learned-skill pattern needed).
- [x] **Gate 16** -- execution shape (single clean-base branch/PR against `modularize-v1.34`; no stacked PR).
- [x] **Gate 17** -- abstraction reuse: reuse Cockpit WS protocol, handler registry, passive package report payload, PR #193 validation helpers, and Performance Console callback seam.
- [x] **Gate 18** -- architecture-doc + diagram freshness: no new architecture boundary beyond the existing WS command family.

## Strict rules -- non-negotiables

Per `CONTRIBUTING.md` section Strict rules -- confirm each before marking ready for review:

- [x] **No hardware in tests** -- no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** -- `mido` and `python-rtmidi` imported only inside `real_midi_adapter.py` / `mido_provider.py`.
- [x] **Hardware-pinned packages** -- `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** -- `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** -- this PR's base is `modularize-v1.34`, not another open PR's head.
- [x] **No `--no-verify`** -- pre-commit hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-06-22-operator-package-apply-preview-bundle.md`

## Risks / follow-ups

- This is intentionally not real hardware apply/send. A later active apply/send PR needs a separate plan, explicit arm/confirm gates, hardware validation, and safety review.
- The apply-preview ack must stay deterministic and evidence-only; it should not write package files, mutate snapshots, apply send plans, arm hardware, or touch MIDI adapters.
- Command and ack names must stay synchronized across Python, TypeScript, tests, README, CLI reference, and the PR body.

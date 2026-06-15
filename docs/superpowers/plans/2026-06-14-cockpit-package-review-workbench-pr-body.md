# Summary

Adds a passive, browser-local package review workbench on top of the local Cockpit rehearsal package export/import flow. Operators can now compare imported package evidence against the current Performance Console packet, see crate/move/snapshot/depth/set-plan/journal/blocked-action/recovery differences, and stage the review into the local operator log without touching the sidecar, project files, WebSocket transport, MIDI ports, or hardware.

# What Changed

- Added typed local rehearsal package review rows/helpers in `PerformanceConsole.tsx`.
- Rendered a visible `Package review workbench` under local package evidence with compatible vs needs-review summaries.
- Added local-only staging so the package review lands in the operator log and persistence summary.
- Kept raw snapshot imports separate: importing raw JSON clears the package workbench instead of reusing stale package evidence.
- Styled the compact package review rows and status treatments.
- Added focused cockpit tests for compatible package review, missing-reference needs-review, and raw-import clearing behavior.
- Updated README, STATUS, and the implementation plan doc.

# Test Plan

- [x] `npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx` — 21 passed.
- [x] `npm.cmd run test:coverage` — 413 tests passed, 100% statements/branches/functions/lines.
- [x] `npm.cmd run typecheck`
- [x] `npm.cmd run build`
- [x] `npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx`
- [x] `python -m pytest` — 5698 passed, 3 skipped.
- [x] `python -m pytest tests\architecture\ -q` — 608 passed, 1 existing warn-only Gate 17 warning.
- [x] `python -m ruff check .`
- [x] `python -m black --check --target-version=py311 .`
- [x] `python -m isort --profile black --check-only .`
- [x] `git diff --check`
- [x] Hardware not run: this is a passive frontend-local review surface and does not touch MIDI or device I/O.

# Plan Requirements

- [x] Gate 1 — Coverage ratchet: web coverage is 100%; no Python source files were touched; full Python suite passed.
- [x] Gate 2 — V1.34 parity: no parity fixtures were changed; full pytest passed.
- [x] Gate 3 — Lint/type/format: web lint/typecheck/build and Python ruff/black/isort passed.
- [x] Gate 4 — Dead-code prevention: new helpers are exercised by focused cockpit tests; no new Python source.
- [x] Gate 5 — Docs freshness: README, STATUS, and plan docs updated.
- [x] Gate 6 — Type discipline: typed local review interfaces are used; no `Any` escape hatches added.
- [x] Gate 7 — Performance: N/A, browser-local review state only; no hot-path send/guardrail behavior changed.
- [x] Gate 8 — Behavior tests: compatible package, needs-review package, and raw import clearing paths are covered.
- [x] Gate 9 — Package organization: no package module layout changes.
- [x] Gate 10 — Mode dispatch: no CLI or app dispatch changes.
- [x] Gate 11 — Fixture discipline: no fixtures added or regenerated.
- [x] Gate 12 — Constants/data discipline: local UI labels and review rows stay inside the cockpit component surface.
- [x] Gate 13 — Environment discipline: no new environment variables or config knobs.
- [x] Gate 14 — Bounded scope: work is limited to the cockpit package review surface and docs.
- [x] Gate 15 — Learned skill reuse: N/A, no new repeatable repo skill emerged.
- [x] Gate 16 — PR bundling: one clean-base bundled PR; no stacked PR.
- [x] Gate 17 — Abstraction reuse: reuses the existing local rehearsal package, compatibility checks, cockpit packet, and operator log surfaces.
- [x] Gate 18 — Architecture docs: no architecture-boundary change; README/STATUS cover the user-facing behavior.

# Strict Rules Confirmation

- [x] No real MIDI port opens in passive/default paths.
- [x] No top-level `mido` imports added.
- [x] No hardware-pinned dependency changes.
- [x] No V1.34 parity fixture regeneration.
- [x] No new top-level package modules.
- [x] No stacked PR base.

# Plan Doc

- `docs/superpowers/plans/2026-06-14-cockpit-package-review-workbench.md`

# Reviewer Notes

This is frontend/browser-local only. The package review rows are recomputed from the imported package plus the current cockpit packet; missing crate/move/snapshot references are shown as `needs review`, and staging only writes to local component state/operator log.

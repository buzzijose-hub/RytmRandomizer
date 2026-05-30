# Live GUI Snapshot Compatibility Model

> Status: in-flight (PR pending)

Per docs/PLAN_REQUIREMENTS.md, this plan scopes one passive GUI-ready model for
the future desktop "Snapshot Compatibility" panel.

## Intent

Jose wants the app to move toward a full 12-pad desktop workflow. The existing
passive Rytm snapshot-pad compatibility report already knows which pads are
currently V1.34-backed and which are planned/locked. This slice adapts that
source into a compact GUI payload suitable for the right-side compatibility
panel without adding any active runtime behavior.

## Scope

- Add an immutable `LiveGuiSnapshotCompatibilityModel` report under
  `rytm_randomizer.reports`.
- Compose the existing `RytmSnapshotPadCompatibilityReport`.
- Emit deterministic panel status, badge, summary, per-pad rows, required
  actions, replay commands, blocked actions, and safety flags.
- Preserve the current truth: 4 pads are snapshot-mutable on the clean base and
  8 pads remain planned/locked until the remaining engine work exists.
- Keep the model passive: no snapshot file parsing, no GUI launch, no MIDI port
  opening, no MIDI sending, no command dispatch, no file writing, and no
  hardware mutation.

## Verification

- Red-first focused tests for the missing module.
- Focused unit tests for current 12-pad state, all-compatible fixture state,
  validation, JSON, and formatting.
- Touched-file coverage plus architecture/lint/full-suite gates before push.

## 18-Gate Notes

- Gate 1 coverage: touched Python must stay at 100% branch coverage.
- Gate 2 parity: no runtime/parity behavior changes.
- Gate 3 lint: ruff/black/isort on changed files and repo.
- Gate 4 dead code: vulture on changed Python files.
- Gate 5 docs: this plan documents scope and verification.
- Gate 6 type hygiene: frozen dataclasses and explicit types only.
- Gate 7 observability: pure metadata surface; no hot path.
- Gate 8 test realism: unit tests exercise GUI payload shape.
- Gate 9 module organization: existing `reports` subpackage.
- Gate 10 string dispatch: no active command dispatch.
- Gate 11 fixtures: no generated fixtures.
- Gate 12 constants: module constants use `Final`.
- Gate 13 env vars: no env vars read.
- Gate 14 maintainability: one bounded pure adapter over the existing report.
- Gate 15 learning: no new skill/rule needed.
- Gate 16 PR shape: clean-base, non-stacked feature PR.
- Gate 17 abstraction reuse: reuses `RytmSnapshotPadCompatibilityReport`.
- Gate 18 architecture docs: no architecture boundary change.

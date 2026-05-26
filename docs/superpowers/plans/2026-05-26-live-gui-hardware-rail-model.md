# Live GUI Hardware Rail Model

> Status: in-flight (PR pending)

Per docs/PLAN_REQUIREMENTS.md, this plan scopes one passive GUI-ready model for
the future desktop right rail: mock/dry-run status, MIDI-port selection status,
hardware-arm lock state, and safety checklist summary.

## Intent

Jose's manual test surfaced a confusing UI state: the cockpit said the port was
`none`, hardware was effectively locked, and the screen did not clearly explain
what had to happen before real hardware could be armed. This slice gives the
future desktop GUI a deterministic right-rail contract without opening ports or
touching hardware.

## Scope

- Add an immutable `LiveGuiHardwareRailModel` report under
  `rytm_randomizer.reports`.
- Accept an operator/session label, a device label, passive available-port
  labels, an optional selected-port label, dry-run state, hardware-request state,
  and safety-check booleans.
- Emit deterministic cards for `Mock / Dry Run`, `MIDI Port`, and
  `Arm Hardware`.
- Emit required actions, blocked actions, replay commands, and safety flags.
- Keep the model passive: no GUI launch, no MIDI port enumeration/opening, no
  MIDI sending, no command dispatch, no file writing, and no hardware mutation.

## Verification

- Red-first focused tests for the missing module.
- Focused unit tests for default mock-safe state, ready state, safety failures,
  missing selected ports, JSON, formatting, and validation.
- Touched-file coverage plus architecture/lint/full-suite gates before push.

## 18-Gate Notes

- Gate 1 coverage: touched Python must stay at 100% branch coverage.
- Gate 2 parity: no runtime/parity behavior changes.
- Gate 3 lint: ruff/black/isort on changed files and repo.
- Gate 4 dead code: vulture on changed Python files.
- Gate 5 docs: this plan documents scope and verification.
- Gate 6 type hygiene: frozen dataclasses and explicit types only.
- Gate 7 observability: pure metadata surface; no hot path.
- Gate 8 test realism: unit tests exercise GUI payload shape and lock reasons.
- Gate 9 module organization: existing `reports` subpackage.
- Gate 10 string dispatch: no active command dispatch.
- Gate 11 fixtures: no generated fixtures.
- Gate 12 constants: module constants use `Final`.
- Gate 13 env vars: no env vars read.
- Gate 14 maintainability: one bounded pure builder.
- Gate 15 learning: no new skill/rule needed.
- Gate 16 PR shape: clean-base, non-stacked feature PR.
- Gate 17 abstraction reuse: reuses passive report formatter helpers.
- Gate 18 architecture docs: no architecture boundary change.

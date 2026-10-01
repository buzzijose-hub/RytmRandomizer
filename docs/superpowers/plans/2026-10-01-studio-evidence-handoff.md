# Studio Evidence Handoff

> Status: in-flight (software implemented and locally verified; review, CI and physical acceptance pending).

## Why

Jose requested a software-only advance before physical studio testing. Eddie's
review of PR #252 asks that shared Studio safety fixes ship independently from
the Pi touchscreen and packaging groundwork. This work targets
`modularize-v1.34` directly; it does not depend on another open PR.

## Scope And Ownership

| Workstream | Owner | Files | Dependencies |
| --- | --- | --- | --- |
| Shared Studio safety | Safety worker | Cockpit capture, send planning, WebSocket lifecycle, provider and their tests; narrowly related frontend state | Existing #252 fixes, adapted without appliance dependencies |
| Evidence inventory | Coordinator | Passive reports, tests and reproducible inventory documentation | Canonical catalogs, codecs, calibration and current policy |
| Studio guidance | Documentation worker | Existing quickstart, studio checklist, architecture prose/diagrams and learned safety guidance | Current shared implementation and explicit safety boundaries |

Keep implementation ownership disjoint. Run at most one heavy verification
process, using `pytest -n 2`. No MIDI/USB access, enumeration, arming or writes.

## Architectural Shape

Reuse the existing capture-service provider Protocol, canonical parameter maps,
Device strategies, passive report formatter/CLI registry and guarded send seam.
The support report describes evidence and blockers; it never grants readiness.
Catalog coverage, native saved-file mutation, MIDI conversion and physical proof
remain independent dimensions. Preserve source identity, unknown bytes and
all unverified precision restrictions. Leave Pi deployment code in #252.

## Verification

Focused regression tests cover capture cancellation/stale result rejection,
ambiguous input refusal through fake providers, whole-plan paired-control
refusal, passive disconnect retention and rejected DISARM identity. Inventory
tests tie rows to canonical data and forbid hardware imports/access. Existing
mutation, native precision, persistence and recovery tests run in the broader
suite. Run architecture, frozen parity, lint, typing, dead-code and coverage
gates. Report actual results and limitations, never substitute software fixtures
for hardware validation.

### Local Receipts

- Full formatted-source suite: `pytest -n 2 --cov=rytm_randomizer --cov-branch
  --cov-report=xml --cov-report=term-missing:skip-covered`: 9,794 passed, five
  skipped, six existing warnings, 263.45 seconds; combined coverage 99.65%.
- All 15 touched production modules have 100% line/branch coverage. Project
  pure-branch coverage remains above the 99% ratchet floor. Architecture and
  frozen parity are included in the full suite and checked again by pre-push.
- Strict touched-module Pyright: zero errors/warnings; Ruff, Black, isort,
  Vulture at confidence 80 and `git diff --check` pass.
- Frontend coverage: 1,045 tests / 73 files pass; statements, branches,
  functions and lines all 100%. ESLint, TypeScript and production build pass.
- Playwright with disabled MIDI, one worker and zero retries: 32 passed, two
  existing skips in 52.4 seconds. Wide/narrow Forge screenshots inspected.
- Local tools: Python 3.12.14, Pyright 1.1.407, Node 24.16.0, cached Vite
  8.0.14. No shared dependency changes; clean pinned-toolchain CI is pending.
- No real MIDI/USB enumeration, open, arm or write occurred. Test providers
  are fake, and no physical observation is marked complete.

## Plan-Requirement Conformance

1. Gate 1: full branch coverage on touched production files; retain project floor.
2. Gate 2: no frozen fixture changes; run parity.
3. Gate 3: lint, formatting and typing.
4. Gate 4: dead-code checks.
5. Gate 5: existing operator and architecture docs updated.
6. Gate 6: typed immutable reports, no import side effects or Any.
7. Gate 7: reuse structured logs and metrics for refusals.
8. Gate 8: deterministic focused tests, no hardware tests run.
9. Gate 9: existing layers and canonical data only.
10. Gate 10: use existing dispatch constants/registry.
11. Gate 11: reuse shared test fixtures.
12. Gate 12: immutable Final constants.
13. Gate 13: no new environment variables.
14. Gate 14: targeted maintainability review.
15. Gate 15: update existing targeted-mutation learned guidance.
16. Gate 16: one coherent direct-base PR, no stack.
17. Gate 17: reuse catalog, codec and policy abstractions.
18. Gate 18: architecture prose and diagrams reflect actual boundaries.

## Rollback And Done Criteria

The bundled change reverts independently of #252. Done means actionable shared
software fixes implemented, a reproducible truthful inventory delivered, gates
run and reported, one focused PR available for review, and an ordered studio
handoff. Physical acceptance, general A4/BOTH sending, Pi readiness and show
readiness remain explicitly unproven until their required evidence exists.

# Live Control Closure - 2026-10-15

Status: in-flight (bounded local software verified; integration and hardware held).

## Scope And Evidence

Close demonstrated software gaps without promoting reference addresses into
physical validation. Base: b613c7052fce08b8794a838af299a90e8ac7959e. The existing
d563 Windows delivery is preserved. No hardware, provider enumeration, firmware
changes, persistent writes, parity regeneration, dependency changes or merges.

The audit found one unnecessary Rytm capture exclusion (Sample Bit Reduction),
25 reversible A4 scalar native/CC7 bindings, and inventory rows that omitted
mandatory protection or unavailable captured-source projections. A4 native
enum ordinals, six conflicting display contracts and paired precision must not
be guessed from MIDI Guide. Exact mapping is not channel or acoustic acceptance.

## Workstreams

| Workstream | Worktree / Branch | Owner And Files | Dependencies |
| --- | --- | --- | --- |
| Rytm sample bit | managed `rytm-sample-bit` / `codex/rytm-sample-bit-closure` | Dewey: snapshot shell and focused tests | None |
| A4 scalar mapping | managed `a4-native-transport` / `codex/a4-native-transport-closure` | Pauli: data bindings, device strategy, exports and focused tests | None |
| Composition | managed `live-control-closure` / `codex/live-control-closure` | Main: inventory, A4 preparation DTO/builder, frontend report contract/view, integration tests and docs | Producers above for final integration |
| Projection metadata | managed `rytm-projection-version` / `codex/rytm-projection-version` | Gauss: immutable capture versions, recipe parser/serializer and focused tests | Rytm audit; main owns version-aware replay and recall integration |

Each owner performs implementation, targeted TDD, cleanup and coverage in its
isolated worktree. Main reviews real producer code at first import, runs composed
tests and maintains documentation. No competing writes to shared files.

## Contracts

`preview_analog_four_native_cc_transport(source_frame, mutations)` canonically
renders selected fields, retains before/after native values and exact CC7
evidence, and reports unresolved rows. It never returns an executable send plan,
verified channels, readiness or output authority. Mixed unsupported changes are
not silently reduced to an executable subset. The A4 preparation builder calls
it only after canonical candidate/source verification. Existing session,
selection, scope, reload, capture and permanent output refusals remain intact.

Rytm capture exposes only Sample Bit Reduction through its established native
primary byte and CC26. Other SAMPLE exclusions and source/plan guards remain.
Inventory distinguishes address knowledge from composed capture/send support.

Compatibility audit reproduced a b613 favorite failure after adding a captured
key: PRNG inputs and semantic fingerprints had changed. Persisted recipes now
bind their capture projection. Unversioned V1 retains exact prior serialization;
new V2 includes Sample Bit. Main integrates recorded-version views across forge,
replay, recall, audition and recapture without changing raw captures. Actual
old-source manifests are regression witnesses; current-only round trips are not
sufficient. This is part of the closure, not a waiver for broken favorites.

## Maintainability Audit

1. Onboarding: reuse indexed architecture and existing capture/preparation seams.
2. Naming: native transport preview is explicitly not a send plan.
3. Coupling: device conversion stays in strategies; no engine import in reports.
4. Constants: bindings remain immutable data, not duplicated address literals.
5. Configuration: no new environment variables or assumed verified channels.
6. Tests: canonical retained fixtures and existing mocks, no hardware fakes as proof.
7. Dev loop: one heavy test process, at most two pytest workers.
8. Errors: per-field blockers preserve the specific missing evidence.
9. Release: no installer replacement or version bump in this bounded patch.
10. Extension: a verified mapping is added to one data table plus evidence tests.

## Gates

- Gate 1: 100% touched production line/branch coverage; record actual gaps.
- Gate 2: frozen V1.34 tests pass unchanged; never capture fixtures.
- Gate 3: Ruff/Black/isort and strict touched typing.
- Gate 4: Vulture80 and unused-code checks on touched production modules.
- Gate 5: STATUS, architecture and operator studio matrix updated in place.
- Gate 6: frozen DTOs/TypedDict, explicit types and relative imports; no Any.
- Gate 7: structured decision logging; no new hardware transition.
- Gate 8: intent-named focused tests and real producer/consumer composition.
- Gate 9: no new package-root modules or device-family packages.
- Gate 10: typed blocker vocabulary, no new mode-string dispatch.
- Gate 11: existing shared fixtures; local one-file helpers only where needed.
- Gate 12: immutable Final facts and frozen records.
- Gate 13: N/A, no environment variables introduced.
- Gate 14: pre-audit above; post-audit in closure report before handoff.
- Gate 15: capture bounded lessons and exact verification in closure report.
- Gate 16: isolated disjoint parallel workstreams, one composed local branch;
  do not stack a PR on open PR254 or bypass required human approval.
- Gate 17: reuse existing native renderer, catalog and source validation.
- Gate 18: update architecture responsibilities and the A4 preparation diagram;
  keep docs aligned with passive numeric evidence and unchanged output holds.

## Verification And Completion

Exhaustive 128-value conversion checks for each A4 scalar binding; retained
source/candidate re-render and unknown/protected byte isolation; unsupported and
mixed changes, strict boolean/type checks, explicit-empty and target-minus-lock
selection, current-source refusal, and passive no-authority composition. Rytm
CC26 capture through the real mock proposal/send-plan pipeline. Frontend contract
and report view consume Python output. Run architecture and parity, bounded full
Python/frontend suites, lint and coverage before claiming completion.

Uncertainty never enables output. Test failures trigger repair, not weakened
gates. Hardware acceptance remains a separate operator-present studio procedure.
Rollback is omission/revert of these owned changes, not resetting other work.
Local source handoff is not an installed or show-certified release.

## Local Verification Checkpoint

Source `20e82194` completes the bounded mapping/compatibility implementation.
The fresh complete run passes 12762 Python tests with 6 skips and 6 warnings in
1100.88 seconds, including unchanged frozen parity. The canonical Gate 1 checker
proves all 14 touched production modules at 100% lines/branches; project pure
branch coverage is 99.44%, with the 99% floor unchanged. Strict touched typing,
Ruff/Black/isort and Vulture80 pass. Frontend 1328 tests across 81 files have
100% coverage in all four metrics, with TypeScript, affected ESLint, production
build and desktop/mobile Edge journey checks passing.

Eight targeted review dimensions are complete. Canonical UI fixture drift and
historical recapture coverage findings are repaired without weakening gates.
All three worker worktrees are archived after their commits were integrated.
The source remains local: no push, protected merge, installer replacement or
hardware action occurred. General A4 armed transport and physical acceptance
remain unfinished; the [closure report](../../LIVE_CONTROL_CLOSURE_REPORT.md)
records their exact boundaries and studio matrix.

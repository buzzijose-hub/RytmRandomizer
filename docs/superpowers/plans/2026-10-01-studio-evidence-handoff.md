# Studio Evidence Handoff

> Status: in-flight (software implemented and locally verified; review, CI and physical acceptance pending).

## Why

Jose requested a software-only advance before physical studio testing. Eddie's
review of PR #252 asks that shared Studio safety fixes ship independently from
the Pi touchscreen and packaging groundwork. This work targets
`modularize-v1.34` directly; it does not depend on another open PR.

Delivery: [PR #254](https://github.com/buzzijose-hub/RytmRandomizer/pull/254),
branch `codex/studio-evidence-handoff`. Maintainer review requested; no merge.

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
  --cov-report=xml --cov-report=term-missing:skip-covered`: 9,795 passed, five
  skipped, six existing warnings, 284.43 seconds; combined coverage 99.65%.
- All 15 touched production modules have 100% line/branch coverage. Project
  pure-branch coverage is 99.37% above the 99% ratchet floor. Pre-push passed
  860 architecture and 697 not-fast/parity tests, including all 685 frozen
  V1.34 cases. No hook bypass, fixture rewrite or allowlist widening occurred.
- Strict touched-module Pyright: zero errors/warnings; Ruff, Black, isort,
  Vulture at confidence 80 and `git diff --check` pass.
- Frontend coverage: 1,053 tests / 73 files pass; statements, branches,
  functions and lines all 100%. ESLint, TypeScript and production build pass.
- Playwright with disabled MIDI, one worker and zero retries: 33 passed, two
  existing skips in 54.6 seconds. Wide/narrow Forge screenshots inspected.
- Local tools: Python 3.12.14, Pyright 1.1.407, Node 24.16.0, cached Vite
  8.0.14. No shared dependency changes; clean pinned-toolchain CI is pending.
- No real MIDI/USB enumeration, open, arm or write occurred. Test providers
  are fake, and no physical observation is marked complete.

### Review Followup

The inventory now exposes typed nested schemas and consumes the public A4
fixed-point/pitch converters. Recovery rows explicitly require manual saved-KIT
reload and fresh capture; local UNDO cannot restore hardware. Cancelled capture
dispatch records RED/error metrics and preserves cancellation propagation.
An always-running browser contract reaches production handlers and ArmedApply
with an isolated in-memory output, verifies exact confirmed plan packets, and
closes once on DISARM. It is not hardware-send evidence. The CI-only timeout in
the monolithic malformed-import test is addressed by splitting its independent
cases without extending timeouts, retrying, skipping or changing assertions.

## Maintainability Audit

Recorded on 2026-10-01 during review, against integration baseline
`892aaffca2484d1939ba3e133263aaadde2f22de` and software revision `4dc43489`.
This ten-question receipt was not committed before PR #254 opened. That
Gate 14 ordering requirement was missed; this is an explicitly retrospective
audit, not a backdated pre-plan receipt. Maintainer acknowledgment of this
timing deviation is still required before merge. No exception has been granted.

| Question | Baseline Assessment | Delivery Assessment / Evidence |
| --- | --- | --- |
| 1. Onboarding curve | AGENTS, contribution guides, task recipes and Architecture section 6 identify ownership. No timed fresh-contributor trial was performed; the under-30-minute target is unmeasured. | Inventory/quickstart/physical checklist links add one route to the support boundaries without a parallel handbook. Navigation remains in the existing layers. |
| 2. Naming hygiene | Capture, send-plan, stage and provider names describe their existing responsibilities; device abbreviations follow canonical data. | `device-support-inventory-report` is descriptive, and `CancellableSysexCaptureProvider` explicitly names the optional contract. Native components are not mislabeled independent controls. |
| 3. Coupling / boundaries | Canonical data, Device strategies, codec/envelope helpers and Cockpit orchestration already define the dependency boundaries. | The report consumes those owners; cancellation remains in provider/session orchestration. All 860 architecture checks pass; no layer/authority allowlist is widened. |
| 4. Magic values / dispatch | Modes, parameter addresses, layout locations and immutable constants already have canonical owners. | Builders derive rows from those owners and public converters. Strict typing, Final/dispatch checks and abstraction review pass; no guessed encoding/location is introduced. |
| 5. Configuration / convention | Exact port/channel metadata and explicit armed boundaries are existing runtime choices. | No new production environment hook is added. Ambiguous exact input names refuse; the memory-output harness is test-only and cannot select a production backend. |
| 6. Test maintainability | Shared capture/snapshot fixtures and the bounded `pytest -n 2` loop are available. | Focused cancellation/ownership/paired-plan regressions reuse shared fixtures. The positive browser contract verifies exact packets; malformed-import cases retain assertions in smaller tests. |
| 7. Build / dev friction | Existing hooks and check scripts are the verification path. A clean-install baseline and same-machine baseline runtime were not measured. | Full Python run: 284.43 seconds with two workers; frontend coverage: 42.03 seconds with two workers; explicit-Python browser run: 54.8 seconds with one worker and zero retries. Clean pinned CI remains a separate gate; these are not baseline speedup claims. |
| 8. Error messages | Capture/send failures already use categorical refusals and source-linked artifacts. | Duplicate capture, ambiguous input, stale/late results and paired precision identify the actual blocking condition. Cancellation RED metrics are recorded before propagation; sensitive token/port text is not added. |
| 9. Version / release | Root `VERSION` is canonical; `scripts/sync_version.py` propagates it to Python, web and Tauri metadata. The installer workflow records build provenance. | No version, dependency pin or release path is changed. The older portable build is not represented as containing this revision; exact source/binary receipts remain required. |
| 10. Future extension | Evidence-backed additions belong in canonical data, the relevant codec/strategy, regression tests and operator docs. | Already-cataloged rows require no new report dispatch. A new native mapping still requires its evidence, canonical mapping/validation and tests; exact file count depends on that field, not a new per-device package. No universal extension-cost claim is made. |

No concrete code-complexity regression was found by the scoped review. The
preexisting large WebSocket handler remains outside this change's refactor
scope. Unmeasured onboarding/install/runtime baselines stay unmeasured.

**Post-merge reassessment:** after this software PR merges, the coordinator
must compare all ten rows with the actual merged tree and record the merge SHA,
observed deltas and any missing measurements in
`docs/STUDIO_EVIDENCE_HANDOFF_MAINTAINABILITY_REPORT.md`. This report has not
been performed or created. Any net-negative delta requires a corrective change
before further learning closeout; software checks cannot fill physical results.

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
14. Gate 14: scoped audit above; retrospective timing deviation requires
    maintainer acknowledgment, and the post-merge reassessment remains due.
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

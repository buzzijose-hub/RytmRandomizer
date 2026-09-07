# Show Kit Forge run report

Date: 2026-09-07 (resumed September 4 implementation)

Plan: [`2026-09-04-show-kit-forge.md`](2026-09-04-show-kit-forge.md)

Branch: `codex/show-kit-forge-complete`

Base: `origin/modularize-v1.34` at
`0b77f9fef019dbfe1da943019b339bd446f95725`

Status: in-flight — the local feature bundle and learning artifacts are
assembled. Final serialized gate counts, hosted CI, and the pull-request URL
are pending root closeout. Operator-present hardware validation remains
blocked.

Pull request: **PENDING — root closeout**

## Outcome

The working tree contains one paired show-preparation workflow built around
immutable, round-trip-verified Rytm and Analog Four source captures. It can
forge deterministic candidate pairs, keep candidate selection separate from
favorite designation, record manual-save attestations, compare semantic
recaptures, and require a later fresh whole-capture-fingerprint preflight for
show readiness.

The hardware authority boundary is unchanged:

- Rytm audition reuses the existing Preview -> PREPARE -> exact confirmed
  `ArmedApply` SEND route and is explicitly live/unsaved afterward.
- A4 Filter 1 Frequency is rendered only as an offline saved-KIT-format
  artifact. There is no A4 SEND route and every candidate result reports
  `hardware_send_validated = false`.
- Cockpit does not persistently SAVE either instrument. The operator must save
  the selected favorite on each instrument and then recapture it.
- OXI project, pattern, and chapter values are metadata only. Direct OXI
  control remains disabled and OXI remains the sequencing owner.

## Run timeline and decisions

1. The plan fixed one clean integration worktree, one branch, disjoint
   workstream ownership, and one non-stacked PR delivery shape.
2. The August 28 A4 captures were promoted narrowly: Filter 1 Frequency uses
   native Track 1 offset 128, a 350-byte track stride, and unsigned big-endian
   Q8.8 values from `0x0000` through `0x7F00`. Three source fixtures are
   hash-pinned.
3. A distinct offline candidate renderer was retained instead of widening the
   existing hardware-write-validated saved-KIT writer. Filter 2 Resonance kept
   its existing behavior; every other A4 field remains blocked.
4. The show-bank domain separated selection, Rytm live audition, favorite,
   manual save attestation, semantic recapture, and fresh preflight. Favorite
   replacement requires an explicit replacement request.
5. Recapture evidence was split into candidate and immutable-source semantic
   comparisons. Candidate matching advances the lifecycle; source matching is
   independently retained for recovery evidence.
6. Retained SysEx and bank revisions were made content-addressed, canonical,
   and fail-closed. Paired frame retention is atomic, and imported history is
   catalog-only rather than current-session readiness or SEND authority.
7. Cockpit and the WebSocket boundary were connected to authoritative store
   revisions. Rytm post-SEND live-audition state is recorded only after the
   existing send contract succeeds; A4 has no analogous live state.
8. Documentation, the safety rule, and the learned mutation skill were updated
   to preserve fresh-capture provenance, manual-save-before-dump ordering,
   catalog-only imports, and atomic paired retention.

## Verification

The integration uses Python 3.12.14 from the repository development environment.
Heavy Python/frontend runs are serialized with two Python workers; focused tests
use `-n 0`. No test accesses physical MIDI.

| Gate | Result |
| --- | --- |
| Full Python suite | 8,788 passed, 5 skipped in 315.98 seconds. |
| Whole-package coverage | 99.358% pure branch; 99.646% blended. Existing unrelated gaps remain above the 99% ratchet. |
| Touched production coverage | All 22 modules: 1,434 branches, 100%. Final fast run enforces the 100% threshold on 5,540 statements in 19 executable modules; three package initializers were covered in the full run. |
| Cockpit Python aggregate | 2,676 passed, 4 skipped in 19.15 seconds. |
| Frontend | 774 tests in 61 files; statements, branches, functions, and lines all 100%; typecheck/lint/build pass. |
| Browser journey | One mocked WebSocket Playwright journey passes at 1440px and 600px; desktop, candidate, and narrow screenshots inspected. |
| Fast suite | 8,103 passed, 5 skipped in 279.02 seconds after the final type/data-placement corrections. |
| Architecture | 801 cases included in the successful full suite; pre-push repeats the separate gate. |
| Frozen V1.34 parity | All 685 cases included in the successful full suite; all 505 JSON fixtures untouched. |
| Static checks | Ruff; new-module PLR/ERA/ARG; Black; isort; whole-package Vulture at confidence 70; strict Pyright 1.1.411 on all 22 modules; diff checks pass. |
| Resumable state | Draft 2020-12 schema and instance validate with format checks. |
| Hosted CI / PR | Pending publication. |
| Physical MIDI / SysEx transfer | Not performed. |

The initial diagnostics exposed stale export dependency metadata, a duplicated
calibration constant, and missing safety edge coverage. These were repaired;
no frozen parity output was regenerated. The AL02 blocked manifest changed only
its dependency hash, with no alteration to mapping gaps or hardware authority.

## Review outcome

Targeted reviews covered architecture, house style/types, parity/test hygiene,
hardware safety/side effects, observability, abstraction reuse, documentation,
and maintainability/string/env/learning/execution shape. All Critical and
Important findings were repaired. Review fixes include canonical imported A4
semantics, exact nested numeric types, source-slot protection, live-source reload
and provenance guards, removed-cue plan revocation, shared test fixtures,
bounded runtime observability, and corrected operator/architecture documentation.

One Minor readability risk remains: the large Forge panel component. Shared
SEND controls and pure view logic are extracted; the
[maintainability report](2026-09-04-show-kit-forge_MAINTAINABILITY_REPORT.md)
records the remaining size/cohesion tradeoff. Pure math/DTO functions remain
logger-free; workspace, store, export, and WS boundaries own decision telemetry.
The consolidated verdict will be posted on the PR after the push gates.

## Change size

The staged implementation checkpoint contains 107 paths, including four binary
SysEx fixtures, with approximately 23,000 text lines added and 300 removed.
This comprehensive feature remains one reviewed bundle under this plan. Test,
schema, and operator evidence account for a substantial part of the change;
size alone is not treated as a maintainability result.

## Escalations and lessons retained

- An offline mutation-validated A4 mapping is not hardware-send authority. A
  separately named renderer and explicit false authority bit keep that
  distinction reviewable.
- The A4 evidence shows unsaved front-panel edits can be absent from a KIT
  dump. A dump does not prove live RAM state or a persistent save. The
  documented order is manual save, then recapture; live Rytm audition also
  requires an explicit manual source-reload acknowledgment.
- Semantic candidate equivalence, semantic source equivalence, and exact full
  capture identity answer different questions and remain separate evidence.
- Persisted or imported preflight records are historical evidence. A fresh
  runtime capture is required before a session can become show-ready.
- Retaining one member of a paired source/favorite record before the other can
  publish is an unsafe partial state; the learned guidance now requires atomic
  paired retention.

Those lessons are durable in the updated
[`targeted-live-kit-mutation` skill](../../../.claude/skills/learned/targeted-live-kit-mutation/SKILL.md),
[`targeted-mutation-safety` rule](../../../.claude/rules/targeted-mutation-safety.md),
and root [`CLAUDE.md`](../../../CLAUDE.md). The existing
[`AUTONOMOUS_RUN_PLAYBOOK.md`](../../AUTONOMOUS_RUN_PLAYBOOK.md) remains the
single replay procedure; this report does not duplicate it.

## Fresh-clone handoff answers

These five answers use only repository artifacts:

1. **Where is the implementation plan and current resumable state?** The
   sibling [plan](2026-09-04-show-kit-forge.md),
   [state](2026-09-04-show-kit-forge_STATE.json), and
   [schema](2026-09-04-show-kit-forge_STATE.schema.json) are the entry point.
2. **What may Cockpit send?** It may audition Rytm only through the existing
   armed exact-plan path. The A4 lane is an offline saved-KIT artifact only;
   A4 SEND is blocked.
3. **What makes a favorite verified and show-ready?** The operator first saves
   on both instruments, then records semantically matching recaptures. A later
   fresh exact paired full-fingerprint preflight alone grants show-ready.
4. **How is the next run resumed?** Read the state and dated
   [run log](../../2026-09-04-show-kit-forge_RUN_LOG.md), follow the existing
   [autonomous playbook](../../AUTONOMOUS_RUN_PLAYBOOK.md), inspect current git
   and PR state, and reconcile before running the next eligible closeout step.
5. **What remains a physical blocker?** Complete the blank
   [studio checklist](../../hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md):
   validate the A4 scratch round trip, exercise one Rytm pad and restore the
   source fingerprint, then manually save/recapture favorites and run fresh
   preflight for actual cues.

No collaborator rebase guide is required: this plan does not integrate an
external collaborator's open PR.

## Resume and closeout

The machine-readable resume source is
[`2026-09-04-show-kit-forge_STATE.json`](2026-09-04-show-kit-forge_STATE.json).
Root closeout must run the remaining serialized gates, replace every pending
aggregate and PR placeholder in that state and this report, then preserve the
hardware-blocked state until real observations are entered. Automated checks
must not turn blank studio evidence into a validation claim.

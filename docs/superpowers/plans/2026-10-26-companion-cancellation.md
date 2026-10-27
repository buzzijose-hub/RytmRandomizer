# Companion Cancellation Repair

Status: in-flight

Composed repair, fresh regression/review and exact-source package pending.

## Mission And Budget

Repair the two cancellation findings on PR254 at e420c30e, then verify and
package the existing bounded companion. Start: 2026-10-27 01:09 UTC
(October 26, 21:09 America/New_York). Fresh budget: six productive hours,
including 90 minutes repair, 90 minutes regression/coverage, 60 minutes review
corrections and 120 minutes CI/package/acceptance. Finish early when complete;
at the cap retain exact unfinished gates rather than claim acceptance.

## Ownership And Dependencies

| Workstream | Worktree / Branch | Owned Files | Dependencies |
| --- | --- | --- | --- |
| Transport / orchestrator | dependency-review / codex/studio-evidence-handoff | cockpit/ws/server.py, handlers.py, A4 studio WS tests, docs and receipts | none |
| Shared cleanup / implementation worker | managed companion-cancellation-cleanup / detached e420c30e | senders/armed_apply.py, sender cancellation tests | none |
| Composition / orchestrator | dependency-review | integrated tests, verification and package receipts | both repairs |
| Review / targeted agents in pairs | read-only composed source | one dimension each, all 18 gates | composed repair |

The orchestrator owns planning, transport TDD and implementation, composition,
cleanup/dead-code checks, coverage, docs, normal push and package acceptance.
The implementation worker owns sender TDD and repair; no overlapping writes.
Use at most two pytest workers in aggregate and one heavy job. Commit the
worker's assigned files, integrate, then archive its managed worktree. One PR,
no stack, force push, protected merge or automatic hardware work.

## Maintainability And Reuse Audit

Reuse the shared ArmedApply generator/drivers, immutable delivery progress,
HandlerResult, session queue, ConnectionQueue and EventEmitter. No new sender,
registry, DTO family or authority surface. Revocations must reach the connected
client through the real transport; cleanup must preserve original control flow
while exposing the secondary fault. Survey existing cancellation, outcome,
logging and transport tests before editing. Keep canonical 25-control scope,
manual reload and persistent-write refusal. Architecture prose/diagram must
describe exceptional completion as well as normal ACK-before-events.

## Tests And Acceptance

First demonstrate failures: actual authenticated WS, fake port cancellation
after a known accepted count; shared sync/async cancellation plus close KeyError.
Cover later commands and teardown races, exactly-once journals/metrics and
revoked readiness. Focused and complete architecture gates precede the full
Python branch-coverage suite. Enforce all PR-touched production modules at 100%
lines/branches, canonical ratchet, strict typing, lint trio, Vulture and version.
Frozen V1.34 fixtures and hardware dependency pins remain unchanged. Run web
tests/type/lint/build and relevant actual-backend browser/native journeys.

Build the exact verified commit through studio_windows installers dispatch.
Download into a new source-identified folder. Verify manifest/binary hashes,
bundled-child identity, health/authenticated WS, offline KIT/favorite/reopen and
owned shutdown with MIDI disabled. Preserve d563 fallback and user processes.
Physical scratch-kit checks are NOT PERFORMED; software acceptance is neither
protected approval nor hardware/show readiness.

## Conformance And Decision Rules

Gates 1-13: canonical coverage, frozen parity, typing/lint/dead-code, docs,
typed boundaries, observability, shared fixtures, existing modules/constants,
no new environment knobs. Gate14: focused pre/post maintainability audit;
historic PR254 exception remains held. Gate15: record reusable cancellation
lesson in existing project memory if the repair establishes one. Gate16:
bounded disjoint workers and one PR; historic exception is not retroactively
cleared and protected approval is never bypassed. Gates17-18: existing shared
abstractions and accurate architecture prose/diagram.

On a failed test diagnose and repair, then rerun affected gates. On remote
movement reconcile without overwriting concurrent work. On missing external
build service retain verified source and precise pending package gate. Do not
retry sends, unlock controls or consume production user state. Stop only when
software/package/handoff is complete, budget expires, user stops, or external
block prevents independent progress. No timer or automatic sends are scheduled.

## Recovery And Rollback

Read this plan, its sibling checkpoint and git/PR state; verify runtime import
points at this worktree. Resume the first incomplete gate using retained logs.
Revert only this repair's commits when explicitly requested; preserve all user
changes and the untouched installed fallback. Stop only owned test processes.

## Checkpoint

2026-10-27 01:09 UTC: published e420c30e confirmed, 33 successful checks,
one skipped, CHANGES_REQUESTED. Primary checkout dirty and untouched. The
dependency-review checkout was clean at the exact PR head. Python imports this
worktree. Approximately 17 GB free memory; no hardware access.

01:26 UTC: transport TDD reproduces the missing wire revocation after one
accepted packet. Shared cleanup worker acc6697c merged at 248c6c59. An initial
architecture pass found a missing plan-index row and variable re-raise rejected
by the taxonomy gate; a second pass exposed the status marker's formatting.
All repaired without changing assertions or allowlists. The composed backend
and full architecture gate pass 1702 cases, four warnings, 91.36 seconds.
Focused earlier gate: 854 passed, three warnings, 15.04 seconds.
Preliminary observability/safety reviews report no new findings within the
unchanged explicit failure contract. Strict typing: 99 modules, zero errors.
Ruff, Black py311, isort, Vulture80 and version checks pass.

The first 1412-case web run used a pre-existing dependency junction whose Vite
was older than package-lock. Retained that junction outside the worktree without
touching its target, then installed the unchanged lockfile into an independent
local node_modules. Repeating web acceptance with Vite 8.0.16; earlier results
are diagnostic only. The primary checkout and fallback hashes are unchanged.
Worker cleanup is integrated; app-managed archival is currently refused because
the app treats that worker as this task's primary checkout. No forced removal.
Full Python coverage, final review/publication and package acceptance are next.

01:34 UTC: independent lockfile web acceptance passes 1412 cases / 82 files,
100% all four coverage dimensions in 111.05s. TypeScript, ESLint and Vite8.0.16
build pass. Four Chromium journeys pass (12.8s): actual-backend scoped favorite
restart, fake-port confirmed SEND, whole-plan paired refusal, and separately
labeled mocked A4 routing/confirmation at desktop/mobile sizes. Canonical
tool checks use isolated Ruff0.15.13, Black26.3.1 and Pyright1.1.411 rather than
the shared environment's drifting dev-tool versions; no shared install or pins
were changed. The build carries no native Controlled Mutate, FM6, ACID303 or Pi
increment. Freeze the composed source next for the full coverage run.

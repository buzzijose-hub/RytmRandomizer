# Companion Cancellation Repair

Status: in-flight

Source software verification complete; publication/review, exact-source binary
acceptance and protected/hardware requirements have separate receipts.

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

Before source freeze: independent lockfile web acceptance passes 1412 cases / 82 files,
100% all four coverage dimensions in 111.05s. TypeScript, ESLint and Vite8.0.16
build pass. Four Chromium journeys pass (12.8s): actual-backend scoped favorite
restart, fake-port confirmed SEND, whole-plan paired refusal, and separately
labeled mocked A4 routing/confirmation at desktop/mobile sizes. Canonical
tool checks use isolated Ruff0.15.13, Black26.3.1 and Pyright1.1.411 rather than
the shared environment's drifting dev-tool versions; no shared install or pins
were changed. This increment adds no native Controlled Mutate, FM6, ACID303 or
Pi work. Frozen source bee04ddbaa7ae25f9f49c49bd258b6edb384effd passes the fresh
full branch-coverage run: 13,575 passed, six skipped, six warnings, zero failures,
1159.86 seconds. All 99 touched production modules are 100% lines/branches;
canonical ratchet remains 99.44% pure branch at floor99. Publication and binary
acceptance are recorded on PR254 and the source-identified delivery receipt,
not inferred from this implementation checkpoint.

October 28 resume, 17:18 UTC: prior review agents exhausted account usage before
the final review/package gates. No package was dispatched or accepted. The
published head is still 80c5b53d, with protected CHANGES_REQUESTED. Its Python3.11
CI failed 56 combined-fault cases because the test enabled package-to-root
logging propagation and captured one record twice; inherited closed-stream
handlers also produced logging diagnostics. Native/browser/security lanes passed.
The previous local Python3.12 full-suite result did not establish CI acceptance.

Reproduced duplicate capture locally in four sync/async eager/lazy-render cases
by attaching the capture handler to the ancestor logger. Capture now occurs
directly at the emitting logger with ancestor propagation disabled, following
existing WS test fixtures. All original exactly-once/context/privacy assertions
remain. Both ancestor configurations pass all 286 shared-driver tests (0.73s).
No production code changed for this test isolation repair. Fresh composed
architecture, full coverage, renewed dimensional review and current-head CI
remain required. The resumed budget is six productive hours; the interruption
is not counted as work. Retained toolchain advisory disposition is in
`docs/security/2026-10-28-companion-toolchain-audit.md`; it is not a dependency
upgrade, alert dismissal or a general security-clearance claim.

October28 17:51UTC: frozen61 full coverage completes with13,631 passed, six
existing skips/six warnings and zero failures in1717.68s. Canonical99-file
touched coverage is100% lines/branches; pure branch99.44%, floor99 unchanged.
Strict pinned typing again reports99 modules/no diagnostics. Prior80c5 remote
failures remain failed evidence, not retroactively accepted.

Eight independent review dimensions found two Important guidance conflicts:
older Quickstart/checklist entry points still permitted four controls first,
and the portable README sent the operator to an obsolete blanket A4 prohibition.
While full61 stayed frozen, disjoint clean worker branch
`codex/companion-handoff-closure` committed1569a4ea and57c18d8b. All first-trial
entry points now restrict Pad2 to`flt`/CC74; the preset's other three controls
are later expansion. The generated README points to the current separate
Rytm/A4 procedure and matching receipt, with regression assertions. Closure
review reports no remaining finding. Merged without a new PR; production,
frontend, pins and goldens remain identical to full61. Affected final gates,
normal push, fresh current-source CI and actual binary acceptance are next.

Integrated final architecture/driver/transport/packaging gate:1326 passed,
four known warnings,124.28s. All updated portable README assertions pass.

October28 publication690f72f0 and Windows studio build40740606085 are retained
as diagnostic evidence, not accepted delivery. The actual copied binaries pass
disarmed/authenticated launcher startup, plan inspection/invalidation/restart,
and both-device reference generation/comparison/refinement/favorite/reopen.
These are bounded software smoke journeys, not endurance or physical evidence.
The first launcher attempt exposed null environment entries becoming empty
strings; the artifact launcher now removes absent entries explicitly and the
second isolated launcher trial passes caller-state restoration and owned cleanup.
The first trial's pinned test processes were stopped; no user app was touched.

Current-source CI still blocks acceptance: native hydrate_reload can navigate
before the Python sidecar authenticates, and a POSIX-only publication-lock test
supplies incomplete simulated stat metadata. The former has five reproduced
red/green synchronization regressions and now awaits a passive authenticated
session before reload without retries, skips or increased time limits. The
categorical bootstrap failure's exact trigger remains unproven until fresh
native CI passes. The POSIX test repair and replacement exact-source delivery
remain pending. No production, device policy, precision, pins or frozen output
changed in these test-harness repairs. Latest local details remain in the
ignored active-run checkpoint; final acceptance belongs to the matching receipt.

The POSIX test now scopes invalid namespace metadata to its refusal assertion
and retains the full stat result. A controlled cross-platform fixture reproduces
the former missing-st_size teardown fault and verifies descriptor closure,
unlock on body failure and reentry. All74 foundation cases pass on the primary
Python3.12 runtime. The source690 packaged ShowBank smoke passes four cue cycles
over120.006s, exact source/scope/favorite export/import and disarmed restart
recall; missing-package refusal preserves the bank. It is explicitly not the
older timed-endurance mission. The QA driver now accepts explicit retained
fixture priming, with failure-before-launch/privacy regressions. Fresh web
coverage passes1417 tests/82files with100% all four measures;45 Node QA cases
pass. These diagnostic binary results do not replace final-source CI, package
identity checks or the separate physical rehearsal.

# Pi performance appliance implementation

> Status: in-flight

Implementation and integrated verification are ongoing; hardware acceptance is unverified.

Per docs/PLAN_REQUIREMENTS.md. Starting integration SHA:
`892aaffc` (`origin/modularize-v1.34`, fetched 2026-09-30).
Original checkout `a73aded6` and all dirty research/calibration/docs are preserved.

## Why and done criteria

Turn the existing Cockpit into an offline touchscreen instrument on Linux ARM64
without a second engine, device registry, output seam or desktop shell. Deliver
one branch and one PR with integrated touch UI, revision-bound scope/history,
evidence matrix, private kiosk bootstrap, reproducible deployment, operator docs,
screenshots and actual verification receipts. Physical Pi and unsupported MIDI
authority are explicit evidence gaps, never successful simulated acceptance.

## Ownership, dependencies and fan-out

| Workstream | Owner/worktree branch | Owns | Depends on |
|---|---|---|---|
| Integration/state | root / pi-performance-appliance | backend contract/session, scope/history/persistence, docs, verification | all |
| Touch | touch_ui / pi-appliance-ui | frontend route/components/types | state contract |
| Runtime | runtime / pi-appliance-runtime | runtime host, scripts, deployment docs/tests | existing FastAPI factory hook |
| Capability | capabilities / pi-appliance-capabilities | catalog matrix, optional controls, docs/tests | existing device evidence |

No shared-schema/index/lockfile edits concurrently. Root serializes integration
via `git merge --no-ff`, cleans only its own integrated worktrees, and owns the
single heavy-job queue. Four agents maximum, no recursive fan-out. Agents may
reason/edit independently. Initial budget: one expensive job, pytest four workers,
browser one worker, compiler two jobs. Measured host: 24 logical CPUs, 31.75 GiB
RAM, 17.5 GiB free, 432 GiB disk free; no unrelated process cancellation.

## Execution state, transitions and recovery

`2026-09-30-pi-performance-appliance_STATE.json` is the durable ledger. States:
preflight -> implementation -> integrated -> verification -> review -> repaired
-> committed -> published, or interrupted with exact resumption instructions.
Record commands, exit/count receipts, owner SHAs and blockers. Work budget is
bounded by current session; checkpoint before interruption, never declare done
on budget exhaustion. Resume by reading state, inspecting dirty diff and agent
branches, then continue the pending queue item; do not reset or ask where we were.

## Presentation and abstraction survey

Use same production React bundle and authenticated FastAPI WebSocket on loopback;
local Chromium kiosk avoids duplicating Tauri supervisor or cross-compiling its
desktop updater. Reuse registered Device/catalogs, deterministic Cockpit PRNG and
engine, immutable Snapshot/PadDelta, HistoryStore, ProfileRegistry, capture service,
canonical atomic_write and ArmedApply. New orchestration is justified for explicit
empty selection, per-page/track depth, revision-bound action and kiosk bootstrap;
none replaces the corresponding existing core. Secrets use private files/cookies,
never URLs or command arguments. Installation does not change this host's boot.

## Parity, safety, verification and rollback

No V1.34 engine/fixture or hardware pin changes. Zero depth/all locked have no
mutation effects. Explicit targets normalize empty to no eligible targets in this
new UI while legacy empty continues meaning all. A4 offline rendering grants no
live authority. Saved-KIT captures grant no unsaved-state synchronization. Hardware
APPLY retains explicit arm and exact per-action confirmation; unsupported restore
remains visible with its reason. BOTH preflights both lanes before any action.

Verify focused refusal/normal tests, touched coverage, full bounded pytest, frozen
parity, architecture, lint/types, Vitest/build, browser sizes and runtime packaging.
Independent reviews cover architecture, safety, security/persistence, tests and
visuals. Failures are repaired without gate exclusions. Rollback removes versioned
runtime links/services while retaining user profiles; code reverts as one bundle.

## Publication, interruption and termination

Open one PR against fetched integration target after checks, request required
review, never merge/self-approve/change protections. STOP interrupts jobs owned
by this run and writes INTERRUPTED. No periodic monitors or external messages.
Terminate when software done criteria pass and remaining external evidence is
listed truthfully; publication failures retain complete local branch + PR body.

## Conformance commitments

- [x] Gate 1 — meaningful touched branch coverage; preserve project ratchet.
- [x] Gate 2 — frozen V1.34 parity unchanged.
- [x] Gate 3 — lint, format and type checks.
- [x] Gate 4 — remove abandoned code after review.
- [x] Gate 5 — operator, deployment and contribution docs updated.
- [x] Gate 6 — typed DTOs/Protocols, no Any escapes.
- [x] Gate 7 — existing structured observability and receipts.
- [x] Gate 8 — intent tests for normal/refusal states.
- [x] Gate 9 — existing subpackages, no root module/framework.
- [x] Gate 10 — shared literal constants and validated discriminants.
- [x] Gate 11 — reuse shared fixtures.
- [x] Gate 12 — Final constants and immutable DTOs.
- [x] Gate 13 — new environment configuration documented, passive defaults.
- [x] Gate 14 — preflight and independent final maintainability review.
- [x] Gate 15 — durable lessons and handoff in operator/deployment docs.
- [x] Gate 16 — isolated parallel worktrees, one bundle, durable state.
- [x] Gate 17 — abstraction survey above; no duplicated transport/core.
- [x] Gate 18 — architecture prose and diagrams updated together.

These are commitments, not claims that unrun checks or physical tests passed.

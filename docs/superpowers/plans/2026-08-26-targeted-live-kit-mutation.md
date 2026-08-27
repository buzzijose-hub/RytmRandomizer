# Targeted live-kit mutation plan

Date: 2026-08-26

Status: in-flight — implementation and local verification complete; no PR opened

Phase 2 status: explicitly armed Rytm Cockpit output composition implemented;
operator-present hardware rehearsal remains intentionally manual.

## Why

The live-kit path already has Rytm lock/depth guardrails, a passive A4
single-track Patch Genome compiler, and verified input-only current-KIT capture
for both machines. It does not yet have an authoritative include-list that can
say “mutate only these pads/tracks,” and a verified Rytm capture is retained in
memory without becoming the Cockpit mutation anchor.

This slice adds one typed target model and carries it through session state,
WebSocket state, inert planning, and the existing Cockpit UI. Rytm captures are
projected only through the promoted snapshot-shell rows. A4 capture remains
fail-closed because its saved-kit semantic offsets are still candidate-level;
the existing manual-backed live parameter map is not evidence that those same
parameters may be rewritten at guessed saved-kit offsets.

The implementation extends the current dirty Cockpit/capture WIP in place. The
same files contain the uncommitted capture milestone, so splitting this run into
parallel worktrees would discard that baseline or create overlapping edits.
Independent verification commands still run in parallel where safe.

## What changes

### WS-1 — target model and Rytm planning

Owns:

- `rytm_randomizer/cockpit/data/`
- `rytm_randomizer/cockpit/mutation_targets.py`
- `rytm_randomizer/snapshot/mutation_scope.py`
- `rytm_randomizer/cockpit/engine/`
- focused data/engine tests under `tests/cockpit/`

Changes:

1. Add a frozen `MutationTargets` model with Rytm pad ids `1..12` and A4
   track ids `1..4`. Empty sets mean no explicit include filter, preserving
   the existing all-scope default.
2. Resolve effective Rytm scope as explicit targets (or all candidate pads)
   minus locks. Keep locks as a deny-list and targets as an include-list.
3. Carry explicit target evidence on `CockpitSendPlan`; include target state in
   its deterministic id and filter packets at preflight even if a stale or
   externally-created candidate contains wider deltas.
4. Filter mutation candidates to explicit Rytm targets while preserving the
   byte-identical no-target engine-conformance behavior.

### WS-2 — session and WebSocket contract

Owns:

- `rytm_randomizer/cockpit/ws/{session,protocol,handlers}.py`
- focused handler/protocol/integration tests under `tests/cockpit/`

Changes:

1. Add `rytm_pad_targets`, `a4_track_targets`, and A4 track locks to the
   declared session state.
2. Add typed set/clear target commands and a whole-state
   `mutation_targets_changed` event emitted at bootstrap and after changes.
3. Add a dedicated A4 track-lock command; the existing Rytm pad-lock command
   remains backward compatible.
4. Recompute/invalidate Rytm candidates and send plans on Rytm target changes.
   Passive A4 Patch Genome analysis rejects a requested track outside an
   explicit A4 target set.

### WS-3 — verified capture bridge and A4 fail-closed planning

Owns:

- `rytm_randomizer/cockpit/capture/`
- `rytm_randomizer/cockpit/device/`
- `rytm_randomizer/devices/strategies/analog_four_mutation_planner.py`
- focused capture/device/strategy tests

Changes:

1. Project a round-trip-verified `RytmKitSnapshot` through the existing
   `build_snapshot_shell_anchor` promotion rules into a Cockpit `Snapshot`.
   No raw offset is invented and unmapped rows are omitted.
2. Adopt the projected snapshot as the adapter/session anchor without opening
   a port, append it to in-memory history as `via="capture"`, and recompute the
   preview from that exact source id.
3. Make adapter snapshot adoption an explicit Protocol method. Mock adoption
   replaces only in-memory state; real-adapter adoption caches the verified
   anchor and performs no I/O.
4. Thread the device-neutral `MutationScope` through the public
   `MutationPlanner`/`Device` seam and both registered devices, while preserving
   A4's `offsets_promoted=False` blocker. Capture plus targets cannot produce A4
   events or a sendable plan.

### WS-4 — Cockpit controls and state

Owns:

- `desktop/web/src/ws/protocol.ts`
- `desktop/web/src/state/`
- focused files under `desktop/web/src/cockpit/`
- Vitest coverage under `desktop/web/tests/`

Changes:

1. Mirror target commands/events and plan evidence in TypeScript/Zustand.
2. Replace per-card isolated lock state with shared authoritative UI state.
3. Add compact multi-select target controls to Rytm pad cards and the A4 Patch
   Genome workspace. Explicit targets use the existing cyan selection language;
   locks stay amber/denied; untargeted items become visibly inactive.
4. Keep the existing layout and disabled A4 hardware action. Clearing targets
   returns the device to its current default all-scope behavior.

### WS-5 — docs and verification

Owns:

- `docs/STATUS.md`
- `docs/COCKPIT_QUICKSTART.md`
- `docs/ARCHITECTURE.md`
- `docs/ARCHITECTURE_DIAGRAMS.md`

Changes:

1. Document include targets, deny locks, effective scope, captured Rytm anchor
   promotion, and A4 mapping-pending behavior.
2. Update the Cockpit SEND and current-KIT capture diagrams.
3. Record exact A4 evidence still required: promoted unpacked offsets per
   semantic field, typed raw-value conversions, second-track stride evidence,
   fixture-backed decode/mutate/re-encode round trips, and hardware validation.

## Architecture shape

```text
MutationTargets (empty = existing all-scope default)
    -> CockpitSession target fields
    -> mutation_targets_changed
    -> Zustand + multi-select controls
    -> candidate include filter
    -> send-plan include filter
    -> minus Rytm pad locks / A4 track locks

verified Rytm KIT capture
    -> canonical codec round trip
    -> registered Rytm snapshot decoder
    -> existing snapshot-shell promoted anchor rows
    -> Cockpit Snapshot adoption (no I/O)
    -> targeted candidate -> explicit inert send plan

verified A4 KIT capture
    -> exact bytes retained
    -> target/lock state retained
    -> AnalogFourMutationPlan ready=False while offsets_promoted=False
```

No new top-level package, device registry, envelope implementation, hardware
sender, or SysEx offset table is introduced. The Rytm/A4 target and wire facade
lives inside Cockpit; the device-neutral `MutationScope` lives at the existing
snapshot/planner seam. Capture consumes the existing codec, decoder,
snapshot-shell promotion, adapter, history, and strategy seams.

## Parity and safety impact

- V1.34 engines/runners and all 505 parity fixtures remain untouched.
- The no-target Cockpit mutation path remains output-identical to existing
  conformance fixtures.
- Capture adoption is in-memory and input-only; it does not enumerate or open
  an output port and does not send a dump request.
- SEND still requires an explicit ready plan. Target and lock changes make old
  plans stale.
- A4 hardware SEND stays disabled. Candidate offsets are never promoted or
  guessed by this work.
- Hardware-pinned package versions and lazy MIDI imports remain unchanged.

## Maintainability audit

1. Onboarding: the target equation and one model are documented in Cockpit
   architecture/quickstart rather than repeated per device.
2. Naming: `targets` always means include-list; `locks` always means deny-list.
3. Coupling: WebSocket/session/UI consume the Cockpit model; device-specific
   capture decoding stays in registered strategies.
4. Magic values: pad/track bounds are `Final`; wire strings are Literal-backed.
5. Configuration: no new environment variables.
6. Tests: existing Cockpit fixtures are extended rather than duplicated.
7. Dev loop: focused Python and Vitest suites precede broad gates.
8. Errors: invalid target ids and mapping-pending A4 plans fail categorically.
9. Versioning: no file format or version field changes.
10. Future-proofing: a later device can add one bounded target dimension to the
    model without creating a sender or registry fork.

The post-implementation re-audit is recorded in
`docs/2026-08-26-targeted-live-kit-mutation_MAINTAINABILITY_REPORT.md`; review
regressions were fixed before handoff.

## Workstream graph and execution

| Workstream | Depends on | Execution / ownership |
|---|---|---|
| WS-1 target model/planning | none | current worktree; core model first |
| WS-2 session/WS | WS-1 | current worktree; overlaps live capture handlers |
| WS-3 capture/A4 | WS-1 | current worktree; overlaps uncommitted capture WIP |
| WS-4 frontend | WS-2 | current worktree; overlaps uncommitted Cockpit WIP |
| WS-5 docs/verification | WS-1..4 | current worktree; verification commands parallelized |

Normal repo plans assign disjoint worktrees and parallel agents. This run uses
one worktree because every eligible workstream depends on the same uncommitted
capture/Cockpit baseline and multiple worktrees cannot faithfully inherit it.
No PR cascade is created. The kickoff is this user-approved autonomous Codex
run; the stop signal is a user message replacing the task. The wall-clock cap
is the active Codex session. Recovery reads this plan plus `git status` and the
latest test output; no force-push, base-branch mutation, fixture regeneration,
or external PR action is authorized.

## Self-driving decision rules

- Invalid target input: reject without changing prior target state.
- Rytm capture projection failure: leave adapter/history/candidate unchanged.
- A4 `offsets_promoted=False`: return a blocked plan with zero events.
- Focused test failure: fix the first attributable regression and rerun.
- Unrelated pre-existing failure: record exact evidence and continue with
  remaining in-scope checks.
- V1.34 parity failure or fixture diff: stop implementation and report; never
  regenerate fixtures.

## Plan-requirements conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 — focused branch coverage for every touched Python branch.
- [x] Gate 2 — V1.34 parity remains byte-identical; no capture mode.
- [x] Gate 3 — Python and frontend lint/format/type gates.
- [x] Gate 4 — no dead or duplicate target/envelope surface.
- [x] Gate 5 — STATUS, Quickstart, architecture, and diagrams updated.
- [x] Gate 6 — frozen dataclasses/TypedDicts/Literals; no `Any` escape hatch.
- [x] Gate 7 — structured logs on target/capture state transitions.
- [x] Gate 8 — intent-named focused tests reuse current fixtures.
- [x] Gate 9 — additions remain in existing subpackages.
- [x] Gate 10 — Literal-backed wire discriminators; no ad hoc mode dispatch.
- [x] Gate 11 — shared Cockpit fixtures extended in place.
- [x] Gate 12 — all new constants use `Final`.
- [x] Gate 13 — no new environment variables.
- [x] Gate 14 — maintainability audit above and paired durable re-audit.
- [x] Gate 15 — repo-scoped skill/rule, run report/log, architecture diff,
  replay playbook, state schema, and project guidance landed locally.
- [ ] Gate 16 — documented local-run deviation: the required capture baseline
  was already uncommitted and overlapped every code workstream, so isolated
  worktrees could not inherit it safely. No PR/cascade is claimed.
- [x] Gate 17 — reuse MutationCandidate/CockpitSendPlan, DeviceAdapter,
  HistoryStore, snapshot-shell promotion, Device strategies, and codecs.
- [x] Gate 18 — architecture prose and both relevant diagrams refreshed.

Exceptions: Gate 16’s normal per-WS worktree fan-out is not safe because the
required baseline is uncommitted and overlapping; all work remains in one
reversible worktree and no external actions are taken.

## Test plan

1. Target model/engine: bounds, empty-default behavior, explicit filtering,
   target-plus-lock intersection, deterministic plan id/evidence.
2. WebSocket/session: set, replace, clear, invalid fail-closed, bootstrap event,
   stale-plan invalidation, A4 analysis target enforcement.
3. Capture: promoted-row Rytm projection, adapter adoption, history/candidate
   rebase, wrong-device/unstable fail-closed behavior.
4. A4 strategy: default all-track behavior when promotion is explicitly
   simulated, target-minus-lock filtering, and zero-event blocked captured-kit
   behavior when offsets remain candidate-only.
5. Frontend: store/event guard, Rytm/A4 multi-select controls, targeted/locked/
   inactive classes, rollback on rejected commands, clear-target behavior.
6. Gates: focused Python tests, all Cockpit Python tests, frontend coverage,
   typecheck, ESLint/build, architecture tests, frozen V1.34 parity, lint trio,
   and broad pytest as time permits.

## Rollback plan

The model, wire fields, adapter adoption method, and UI controls are additive.
Reverting this logical change returns empty targets to implicit all-scope and
leaves captured raw frames/profile files untouched. There is no persisted
target schema, no device write, no offset promotion, and no fixture migration.

## Done criteria

- Explicit Rytm pad targets and A4 track targets round-trip through the server
  and render as multi-select state.
- Rytm candidates and prepared packets contain only target-minus-lock scope;
  empty targets preserve current behavior.
- A verified Rytm capture becomes the mutation source using only promoted
  snapshot-shell rows.
- A4 target/lock planning is modeled, but captured-kit planning remains blocked
  with zero events until mapping evidence is promoted.
- Docs state the exact A4 evidence gap and all required safety/parity gates pass
  or are reported with attributable blockers.

## Phase 2 — explicitly armed Rytm output composition

This follow-on keeps the shipped Tauri command input-only and adds one separate
manual rehearsal composition. It requires `--arm`, an exact selected output
port, and a feature-specific launch confirmation. Port discovery validates the
name without opening it. PREPARE produces the same inert, target-minus-lock
packet plan; live UI confirmation displays the exact port, plan id, sendable
pads, and message count. Armed SEND must echo that current plan id before the
adapter opens output lazily. Tests use injected providers/adapters only and do
not touch MIDI. A4 captured-kit output remains outside this phase and blocked
on the semantic evidence listed above.

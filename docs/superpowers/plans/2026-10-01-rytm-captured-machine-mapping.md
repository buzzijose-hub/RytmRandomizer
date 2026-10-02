# Captured Rytm machine mapping correction

> Status: in-flight — combined Studio software verification passed;
> software published and local capture verified; protected review and post-merge assessment remain pending.

The retained OS 1.72 RIO target-return KIT contains XT Classic on pads 6–8.
Its machine IDs and seven non-level SRC values already round-trip through the
native codec and canonical field tables. The capture decoder nevertheless keeps
all tom machine facts pending. Separately, snapshot anchors identify machine SRC
sections by their canonical machine key, while the Cockpit reverse lookup accepts
only `SRC`; this drops already mapped machine parameters from every capture.

## Scope

1. Promote XT Classic tom facts using its existing canonical machine ID, retaining
   pending status for other unverified tom facts and preserving raw payload bytes.
2. Accept an exact owning machine section as well as `SRC` in the Cockpit reverse
   lookup. Require a promoted, matching machine fact for machine SRC projection;
   the snapshot shell's raw-ID fallback does not grant mutation authority. Retain
   known common-page values, the exact control match and omission of unknown rows.
3. Exercise the retained hardware-return frame through capture, snapshot anchor,
   Cockpit projection, target/lock handling and send planning for XT, BD and SD.
   Cover paired precision refusal and unsupported rows without opening MIDI.
   Include composed retained-frame cases for unverified tom IDs and raw `0x88`,
   which the shell can label as XT but the capture bridge must keep out of SRC.
4. Address the outstanding PR #254 registry review: enumerate `all_devices()`
   in the passive support report, preserve family-specific evidence and show
   unknown registry IDs explicitly with zero evidence. Test JSON/text registry
   equality and a newly registered unsupported device; retain existing counts.
5. Repair the existing A4 one-CC helper's output-wrapper composition defect,
   found during the operator-approved PWM Depth probe. `midi_io.send_cc` builds
   a message with public `type='control_change'`; the neutral wire wrapper only
   recognizes `message_type`. Accept the public CC shape at that existing
   boundary, validate all fields and reconstruct the backend message there.
   Unsupported kinds and invalid fields must still fail before backend send.
   Exercise the actual public app, MIDI helper and provider composition against
   a fake backend whose message exposes only the real public `type` spelling.
6. Resolve the inherited native updater/beacon TLS initialization race exposed
   by hosted checks at this exact head. The plugin initializes its ring provider
   asynchronously while the independent beacon may construct a client first.
   Declare the already locked rustls provider as a direct dependency and ensure
   a process provider before beacon-client construction. Preserve an existing
   provider, tolerate a concurrent installation winner, and change no package
   versions, TLS checks, timeout, retry or update policy. Add a cold client-build
   regression and require the hosted native acceptance job to verify it.

The fifth workstream was added before its implementation, after the first
approved A4 attempt failed with `midi_wire_unsupported_message: Message` and
reported 0/1 messages sent. The operator confirmed PWM Depth remained 0.
It uses the isolated `a4-wire-compat` worktree at `2f0f5be0`; one implementer
owns only `mido_provider.py` and its two affected test files. The coordinator
integrates it into this same PR and verifies each runtime before retrying the
same approved integer CC. No A4 candidate SEND or paired conversion is unlocked.

The sixth workstream was added before its implementation, after inspection of
both same-head hosted runs: one passed all 32 native scenarios, while the other
failed `journal_ui` with a missing TLS provider panic and 31 passes. Source
inspection identifies scheduling-dependent initialization, rather than package
resolution drift. One implementer owns `desktop/shell/Cargo.toml`, its existing
lockfile and `src/update_transport.rs` in the isolated `studio-tls-init` checkout
at `2f0f5be0`. The local machine has no Cargo toolchain; source/lock inspection
and hosted Rust/native checks must remain distinct from local Python validation.

This fourth workstream was identified from Eddie's October 1 review while
preparing delivery. It uses a separate `studio-inventory-registry` worktree at
`941643c5`, with report/data/test ownership held by one agent before integration.
The report also removes changeable PR prose from its fact table and normalizes
one count key to lowercase. Non-cancellable provider reservation behavior is
documented. Unexpected off-reader task errors and the browser harness's private
test-factory import remain the review's minor follow-up items; this correction
does not claim they are fixed.

Eddie's [review](https://github.com/buzzijose-hub/RytmRandomizer/pull/254#pullrequestreview-5379158634)
acknowledges the prior handoff's retrospective Gate 14 timing receipt. This
mapping audit is also retrospective; new-head review and the actual post-merge
ten-question reassessment remain pending. Gate 14 stays unchecked.

No offsets, CC addresses, legacy V1.34 support statuses, frozen parity
fixtures or hardware saves change. Missing aliases, omitted fields and physical
calibration beyond the retained fixture remain explicit gaps. A saved KIT fixture
proves captured encoding; it does not prove every live control on this unit.

## Workstream graph and ownership

The original dirty user checkout and the running studio checkout are protected.
The prototype is isolated at
`C:/Users/Jose Buzzi/.codex/worktrees/rytm-tom-mapping/RytmRandomizer`, branch
`codex/rytm-tom-mapping`, starting at `8cfa6f7b`. The delivery checkout is
`C:/Users/Jose Buzzi/.codex/worktrees/rytm-studio-mapping/RytmRandomizer`,
starting at PR254 head `941643c5`. The coordinator will update existing
PR254, `codex/studio-evidence-handoff`, directly against `modularize-v1.34`.
PR252's Pi implementation is not a PR base or a dependency to publish.

| Work | Owner and files | Depends on | Parallel work |
| --- | --- | --- | --- |
| Mapping correction | Capture implementer: decoder, capture bridge, reverse map and their tests; shared frame helpers in `tests/conftest.py`. Prototype checkout. | Existing retained frames and canonical catalogs. | Read-only inventory and hardware configuration intake. |
| Registry evidence summaries | Maintainability agent acting as report/data implementer: the eight files listed below, in the isolated `studio-inventory-registry` checkout at detached `941643c5`. | Existing canonical registry and family-specific report rows. | Mapping correction and read-only dimension reviews. |
| A4 CC wrapper compatibility | Boundary implementer: `rytm_randomizer/mido_provider.py`, `tests/test_mido_provider.py`, `tests/test_app_validate_one_cc.py`, isolated `a4-wire-compat` checkout at `2f0f5be0`. | Operator-reported zero-send failure and existing public CC helper/provider. | Disjoint documentation receipt updates. |
| Native TLS initialization | Native implementer: `desktop/shell/Cargo.toml`, `Cargo.lock`, `src/update_transport.rs`, isolated `studio-tls-init` checkout at `2f0f5be0`. | Same-head hosted failure and checked-in updater/beacon initialization flow. | A4 compatibility tests and documentation. |
| Inventory and review | Inventory agent and one reviewer per dimension; read-only source inspection. Coordinator owns indexes, status and architecture documentation, and coordinates `docs/RYTM_MAPPING_STATUS.md` with a scoped final Studio adaptation delegated to the capabilities agent. | Inventory can start from the unchanged baseline; final review needs the composed patch. | Implementation and independent review dimensions. |
| Plan records | Maintainability reviewer: this plan and its `_STATE.json`, `_RUN_LOG.md`, `_MAINTAINABILITY_AUDIT.md` and `_MAINTAINABILITY_REPORT.md` companions only. Prototype checkout. | Observed implementation and runner results. | Coordinator's disjoint documentation corrections. |
| Delivery and verification | Coordinator: transplant into the delivery checkout, adapt Pi-only documentation, run composed checks, update PR254 and request review. | Mapping correction, registry evidence summaries, inventory, records and scoped reviews. | Independent static checks; resource-heavy runs are scheduled by the coordinator. |

The report/data implementer's registry checkout is
`C:/Users/Jose Buzzi/.codex/worktrees/studio-inventory-registry/RytmRandomizer`,
isolated at detached HEAD `941643c5`; no feature branch is claimed for that
checkout. Its eight owned files are `rytm_randomizer/data/__init__.py`,
`rytm_randomizer/data/device_support_inventory.py`,
`rytm_randomizer/reports/device_support_inventory.py`,
`tests/test_data_layer.py`, `tests/test_device_support_inventory.py`,
`tests/fixtures/data_layer/DEVICE_SUPPORT_EVIDENCE_FAMILIES.json`,
`tests/fixtures/data_layer/DEVICE_SUPPORT_OMISSIONS.json` and
`tests/fixtures/report_goldens/device-support-inventory-report.txt`.
The coordinator integrates this disjoint increment before the final composed
checks; an isolated registry result does not certify the delivery tree.

These are coordinated phases of one narrow correction, not independently
published workstream PRs. Prototype writers used declared disjoint file scopes
in one isolated checkout; do not retrospectively claim separate worktrees for
each writing phase. The delivery checkout separates the published shared Studio
change from the Pi prototype. Planner/implementer, test/refactor review,
coverage verification, dimension reviewers, documentation and PR delivery are
explicit responsibilities; there is no new generic orchestrator or registry.
The final record repair is also disjoint: the maintainability reviewer owns
this ownership section and the current reassessment report; the coordinator
owns state, run log, conformance and verification receipts.

## Validation

- Focused decoder, reverse-map, capture, snapshot-shell and planner tests with
  the repository virtualenv and `-n 0`.
- Real RIO fixture round-trip and deterministic recipe tests remain unchanged.
- Architecture and lint gates; whole-package branch coverage on touched files
  before integration. The root agent coordinates the broader gate run.
- Inspect the diff to confirm the running integration checkout and retained
  fixtures remain untouched during this offline correction. The prototype
  implementer and reviewers open no real providers, ports or sends.
- Re-run the composed correction on the direct-base delivery checkout. Prototype
  results do not certify its final source or hosted checks.
- For A4 wrapper compatibility, prove one backend CC and deterministic close
  through the public armed helper with fake discovery/backend, preserving
  rejection of unsupported explicit primary kinds despite a supported fallback
  spelling, noninteger fields
  and out-of-range channel/control/value. Run focused tests and touched-module
  coverage, then composed verification before an approved physical retry.

The following paragraph is historical prototype evidence. Final Studio and
separate installed-runtime checks are recorded in the
[run report](2026-10-01-rytm-captured-machine-mapping_RUN_REPORT.md).

The first prototype full run reported **5 failed, 10,670 passed, 5 skipped in
204.98 seconds**. Three seed-dependent test assumptions were then repaired;
their focused recheck reported **22 passed**. Two plan lifecycle/index failures
were assigned to the coordinator and their recheck is pending at this recording.
The mapping-focused run reported **306 passed**. Public decode/bridge checks of
the retained original October 1 source and the RIO initialized/returned frames
each produced **324 keys, including 60 SRC keys**, with XT Classic ready.
Those are offline receipts, not hardware observations or a passing final suite.

## Maintainability and learning

The [baseline audit](2026-10-01-rytm-captured-machine-mapping_MAINTAINABILITY_AUDIT.md)
and [current reassessment](2026-10-01-rytm-captured-machine-mapping_MAINTAINABILITY_REPORT.md)
answer Gate14's ten questions. Both were recorded after implementation began;
the baseline is reconstructed from the actual defect and source, not a timely
pre-plan audit. PR254 already leaves Gate14 unchecked for a retrospective audit
limitation. Preserve that unchecked status: maintainer acknowledgment and an
actual post-merge ten-row reassessment are pending. No acknowledgment or merge
is assumed.

The existing `targeted-live-kit-mutation` learned skill now records the actual
producer/consumer bug: compose a retained hardware-return frame through the
anchor and consumer, accept only the owning machine section, and retain exact
control checks. Its reusable lesson is supported by executable composed tests.
Final verification receipts and delivery links must be added to the tracked log
and state before reporting delivery; no user-home-only learning is required.

Learning outputs now include the architecture comparison, replay playbook,
state schema, run report/log and existing skill/rule/agent-guidance updates.
The [repository-only onboarding exercise](2026-10-01-rytm-captured-machine-mapping_ONBOARDING.md)
answers five questions from an isolated document snapshot and scores the
four-line skill lesson 4/5 on every in-repo learn-eval dimension. It is a
documentation simulation of proposed content, not a fresh installation or
published clone. Committing these outputs completes local learning capture;
protected merge and post-merge assessment remain plan termination conditions.

## Execution, recovery and termination

Kickoff is the user's direct studio mapping request, executed in this local
conversation. No recurring automation, scheduled job or monitor is created.
There is no auto-merge: required maintainer/CODEOWNERS review remains a protected
merge condition. The local work completes when the correction is included in
PR254 with final source-specific checks and review findings recorded. The plan
remains in-flight until protected merge and the post-merge reassessment are
recorded; it does not wait actively or schedule itself for that external state.

The local implementation/validation budget is **90 minutes from the recorded
23:38:16 UTC checkpoint on October 1**, ending at **01:08:16 UTC on October 2**.
Earlier elapsed implementation time was not retained, so this record makes no
claim that historical work satisfied that cap. At the cap, preserve the patch
and receipts, write `BUDGET_EXCEEDED` to the state/log and report remaining work.
Waiting for protected review or operator hardware input is outside this local
implementation window; it does not grant approval or a new output action.

On resume, read the [state](2026-10-01-rytm-captured-machine-mapping_STATE.json)
and [log](2026-10-01-rytm-captured-machine-mapping_RUN_LOG.md), inspect both
worktree statuses, and refresh PR254's head/base/checks/review state. Reconcile
actual runner summaries with their source checkpoint; select the next pending
eligible step. New source changes invalidate affected check receipts. A failed
check leads to investigation and a bounded correction, followed by its focused
recheck and the relevant composed gate. Collection errors, skipped cross-seam
tests or absent inputs are failures, not successful evidence. Unfamiliar
conflicts go to the coordinator/reviewer; preserve concurrent work and never
reset a checkout to resolve uncertainty.

Use only the local read/write/command permissions needed for this correction.
Refuse force-pushes to base branches, deletion/reset/clean of user or concurrent
work, hooks bypass, architecture allowlist widening, dependency pin changes,
parity regeneration, collaborator PR closure, self-approval and protected merges.
No real MIDI action is part of this plan. Operator-guided A4 work is a separate
hardware acceptance task; this patch grants it no output authority. A user STOP
interrupts local work and records `INTERRUPTED`; resuming requires the user's
continuation. Rollback reverts only the correction's committed files and keeps
retained frames and hardware saves unchanged. The coordinator separately verified
and installed the mapping-only local runtime at `2a19b094`; its unchanged frontend
uses the hash-verified `8cfa6f7b` bundle. Outputs remain disarmed. A fresh
operator KIT 01 capture now projects 324 parameters and exposes XT Classic
controls; it does not prove live SRC conversion or unsaved RAM. This runtime
does not include the registry increment.

## Conformance

The change stays within existing strategy and Cockpit seams, uses canonical data,
adds no public top-level modules, resolved packages or version changes, and retains typed immutable
snapshot facts. Regressions cover new branches and safety refusals; shared fixture
loading belongs in `tests/conftest.py` if reused across test modules. The final PR
will carry the repository's full 18-gate and strict-rule checklist.

Per `docs/PLAN_REQUIREMENTS.md`, this is an **expected/pending checklist**, not
a declaration that all gates passed. Checked rows below reflect the final local
Studio receipt (9,836 tests); hosted Rust/native and post-merge evidence remain separate.

- [x] **Gate 1** — 18 touched production modules at 100% lines/branches; pure branch 99.37%.
- [x] **Gate 2** — Frozen fixtures unchanged; full suite includes all V1.34 parity cases.
- [x] **Gate 3** — Whole-tree lint trio and strict Pyright on 18 touched modules pass.
- [x] **Gate 4** — Vulture on production/tests at confidence80 passes.
- [x] **Gate 5** — Inventory, operator recovery, indexes and source-specific status/report are updated; scoped links checked.
- [x] **Gate 6** — Typed immutable facts and TypedDict summaries; no Any escapes or new side effects.
- [x] **Gate 7** — Existing structured promotion/omission log and capture metrics retained; passive report emits no fictitious sends.
- [x] **Gate 8** — Genuine retained-frame/public-pipeline and future-registry refusal regressions pass in the full suite.
- [x] **Gate 9** — Existing subpackages only; no new production modules or registry.
- [x] **Gate 10** — Established source vocabulary and canonical machine keys; no new identity dispatch.
- [x] **Gate 11** — Shared frame helpers remain in tests/conftest.py.
- [x] **Gate 12** — Canonical machine constant and immutable evidence mapping use Final.
- [x] **Gate 13** — New test-only Rust child marker documented in CONTRIBUTING and local tooling notes; no new runtime environment knob.
- [ ] **Gate 14** — Pending: retrospective ten-question baseline/current assessment recorded; timely pre-plan audit was missed, maintainer acknowledgment and actual post-merge reassessment required.
- [x] **Gate 15** — Learning capture: existing skill/rule/guidance, report/log, architecture comparison, replay/schema and five-question repository-only onboarding exercise are included. The earlier capture lesson scored 4/5; the new wire-boundary lesson scored 4/5/4/4/4 on the same five dimensions, recorded separately in the run report. Protected plan termination remains pending. No separate learning PR or scheduler framework is introduced.
- [ ] **Gate 16** — Pending: local parallel roles, disjoint ownership, state/log and recovery are recorded; original per-phase worktree and retrospective timing limitations are disclosed. One existing direct-base PR is updated; protected merge cannot be automated.
- [x] **Gate 17** — Scoped abstraction review confirms canonical codec/catalog/Device/registry/Cockpit reuse.
- [x] **Gate 18** — Architecture and diagram describe the exact guarded SRC and registry-report boundaries; counts source-bound.

### Resumed execution checkpoint

The user resumed eligible software work at **2026-10-02T01:13:47Z**. The prior
90-minute window and `BUDGET_EXCEEDED` receipt remain historical. This resumed
90-minute window ends **2026-10-02T02:43:47Z**. First publish the preserved
native readiness fixture fix and verify its exact-head review/hosted gates; a
parallel read-only mapping audit prepares any next bounded implementation
scope. Protected approval, post-merge assessment and additional hardware
authority are not inferred.

### Eighth scope: remaining SRC aliases and conservative projection

Recorded before code at source `2a3789c6faae4f393f1aeb2ae5d7d046b9f20878`.
The user requested completion of the remaining mappings. This offline increment
completes descriptive bindings for the eleven missing families (68 rows), using
the existing 224-row SRC catalog and saved-slot bindings. Existing compact keys
keep precedence; canonical profile labels resolve SY Dual VCO correctly.
Descriptive completeness is separate from mutation or physical evidence.

One implementer owns the isolated managed `rytm-alias-closure` checkout:
existing canonical MIDI facts/re-exports, Cockpit parameter map, capture bridge,
mutation/planner consumers, passive inventory and their tests/documentation.
An independent reviewer inspects that composition read-only. The coordinator
owns integration, full-suite coverage, final documentation and PR publication;
the active delivery checkout and running studio server are not edited here.

One shared conservative eligibility policy omits disputed/guarded SRC values
from captured mutation parameters, freezes protected values in generic mutation
and refuses a manually constructed changed protected row at plan preparation.
This includes the six audited semantic/guarded exclusions, Level, SY Raw Noise
Level and newly exposed pitch/categorical controls. Exact raw canonical machine
identity and existing pad compatibility/tom gates remain required. The changed
paired-LFO whole-plan refusal remains unchanged. Original saved bytes remain
immutable; synthetic fixtures establish software contracts only.

Focused tests must exercise retained init/return frames and explicitly synthetic
remaining-family frames through capture, anchor, bridge, mutation and planning;
also test all 224 descriptive row round trips, unknown/high-bit identity refusal,
target-minus-locks, protected mixed proposals and inventory-policy agreement.
The implementer records actual runner summaries; the coordinator verifies the
integrated source with full coverage, typing, lint and unchanged frozen parity.
No dependency/config/allowlist changes, MIDI action or calibration promotion is
authorized. Rollback reverts only this increment's commits. Done means alias
bindings and fail-closed composition are reviewed and verified, with remaining
native/live calibration and hardware acceptance explicitly pending.

The [eighth-scope baseline](2026-10-01-rytm-captured-machine-mapping_MAINTAINABILITY_AUDIT.md#eighth-scope-pre-code-baseline)
was recorded before this increment. It does not repair historical Gate 14/16
timing exceptions or constitute the required post-merge reassessment. The
resumed deadline remains `2026-10-02T02:43:47Z`.

### Eighth-scope integration correction: fixture/demo truth and import boundary

Recorded before correction code at leaf source `9603d20d`. The coordinator's
integrated checkpoint reported 29 failed, 9,885 passed and five skipped in
731.31 seconds. Three stalled workers did not return complete coverage, so the
partial coverage percentage is not a valid final measurement. Reported failures
identify a new engine-to-canonical-data import and a shared integration snapshot
that places several machines on incompatible pads. The production demo factory
repeats those assignments and needs the same truthful correction.

The leaf implementer owns a bounded correction: reuse the Cockpit data facade
for pad eligibility, correct production demo/shared fixture identities and
parameters using catalog-compatible unprotected controls, and make successful
send helpers fail promptly if preparation is blocked. Survey and reuse existing
public snapshot/facts helpers before adding any helper. An independent reviewer
checks composition read-only. The coordinator owns integration, state/run-log,
coverage, strict typing, final review and publication. No architecture allowlist,
frozen fixture, hardware authority or eligibility rule may be weakened.

Verification covers every reported integration file, import-direction matrix,
parameter-map and protected capture/planner regressions, plus production demo
behavior. Actual runner output is retained. Existing mutation/history/lock/send
assertions remain meaningful. Rollback reverts only this correction's commits.
Done requires focused checks/review plus the coordinator's full composed gate.
Historical Gate 14/16 exceptions and post-merge requirements remain pending;
this pre-code amendment does not retroactively satisfy them. The resumed
deadline remains `2026-10-02T02:43:47Z`.

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

### October 5 review repair and Studio candidate

Per docs/PLAN_REQUIREMENTS.md, this continuation remains in PR #254 on remote
`codex/studio-evidence-handoff`, assembled in `codex/studio-rytm-mapping`,
starting at `0138d00b`. Before implementation,
Eddie's October 3 review and the clean delivery checkout were inspected.
The original checkout is dirty and is not an editing or launch destination.

The bounded dependency graph is: canonical policy repair and UI metadata repair
in disjoint files -> composed regression gates -> identified Studio build ->
software-only smoke/review -> operator-present rehearsal. At most two workers
and one heavy verification/build job may run; no MIDI enumeration, input, output
or device access is permitted in this software pass. Pi deployment stays separate.

The backend worker owns the Rytm policy, support inventory and their tests at
`C:/Users/Jose Buzzi/Documents/RytmRandomizer-worktrees/studio-cy-ride-guard`,
branch `codex/studio-cy-ride-guard`. The UI worker owns dynamic machine control
metadata/rendering and its tests at
`C:/Users/Jose Buzzi/Documents/RytmRandomizer-worktrees/studio-src-ui`, branch
`codex/studio-src-ui`. Both start at `0138d00b`; the coordinator integrates their
disjoint diffs into the existing delivery worktree before composed verification.
The coordinator owns native-driver reconciliation with #240, build, operator
guidance, plan records, architecture diagrams and PR delivery. No new sender,
codec, tuning value, native conversion, registry or hardware grant is planned.

Pre-code maintainability audit (10 questions; historical gate deviations above
remain disclosed, and the post-merge reassessment remains due):

| Question | Baseline observation | Continuation constraint |
| --- | --- | --- |
| Onboarding curve | Public contribution/architecture guides locate all owners; no fresh-clone timing measured. | One ordered operator handoff and file links. |
| Naming hygiene | Fixed frontend groups omit descriptive SRC keys. | Canonical labels, no machine catalog retyped in TypeScript. |
| Coupling/module boundaries | Shared policy and Device registry/codecs already own evidence and encoding. | Reuse public seams; document the report-to-registry edge. |
| Magic numbers/strings | CY Ride pending cases do not cover neighbours; keys derive canonical NRPN slots. | One family-wide categorical refusal, no invented constants. |
| Configuration/convention | Ports/slots are operator-selected; source reload is manual. | No hardcoded hardware destination or restore automation. |
| Test maintainability | Constructed proposals can bypass capture omissions; harness uses private fixture factory. | All SRC rows tested at actual planning; use a public shared helper. |
| Build/dev-loop friction | About 9 GiB RAM free; 860 baseline architecture cases pass in87.64s; shared Vite8.0.14 differs from lock. | One heavy job, two pytest workers, isolated lockfile cache, hosted Windows packaging. |
| Error messages | Readiness receipts contain categorical requirements. | Preserve/expose exact CY Ride and paired precision reasons. |
| Versioning/release | VERSION and identified installer manifest already exist. | Record exact source commit, version, binary hashes; no show-ready inference. |
| Future-proofing | Existing DTO/protocol/store lifecycle can carry canonical metadata. | Extend existing contract, no new registry/sender/codec or Any. |

Acceptance: every CY Ride SRC key refuses SEND; the 29 newly eligible rows are
audited with the remaining eligible rows explicitly documented-only; named SRC
values appear in Studio; #240's robust stale-token probe is reused without
weakening its rejection assertion. All mandatory tests, lint, typing, coverage
and dimensional reviews precede delivery. Hardware observations are separate;
the candidate is not show-ready until its full bounded workflow/recovery is
rehearsed. Resource/tool/platform limitations must be recorded, not hidden.

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
# October 5 Continuation: Parameter Scopes And Local Favorites

Baseline is PR #254 at `b0f01dbed579f8b7cbdefcb91747192a544ad7bd`, with portable
production `fa43f863`. This phase adds one coherent supported Studio workflow,
not another hardware mapping program. The previous portable folder is immutable.
The current head's hosted checks completed successfully; Eddie's October 3
requested-changes review still controls merge approval.

## Pre-Code Scope And Maintainability Assessment

| Dimension | Baseline / planned response |
| --- | --- |
| Onboarding | Existing Cockpit scope, library and protocol owners are discoverable; document the per-cell flow alongside them. |
| Naming | Use parameter cell identities (device/item/canonical key), not labels or raw CC numbers as mutation authority. |
| Coupling | Extend the existing engine and session; no appliance runtime activation, parallel sender or persistence framework. |
| Constants | Preset identities resolve through the canonical catalog; frozen records and typed event DTOs. |
| Configuration | Existing ports, config paths and build workflow unchanged; MIDI remains off for this session. |
| Tests | Existing shared snapshots, fake ports and native harness; one composition checkpoint and one heavy process at a time. |
| Build loop | Baseline architecture gate is running with two workers; previous source full suite took 324.94 seconds. New actual durations will be recorded. |
| Errors | Categorical scope/persistence refusal, exact plan rows, no silent reset or removal of blocked packets. |
| Versioning | Preserve 1.34.0 product version and pins; version the changed library record through the canonical persisted-state migration registry. |
| Extension | Adding another supported field consumes canonical metadata; field eligibility and physical proof remain separate. |

The earlier Gate 14/16 historical exceptions remain disclosed. This pre-code
continuation assessment does not cure them or claim the outstanding post-merge audit.

## Workstreams And Ownership

| Stream | Worktree / branch | Files owned | Dependencies |
| --- | --- | --- | --- |
| Scope authority (orchestrator) | existing `rytm-studio-mapping` / `codex/studio-rytm-mapping` | Python scope DTO/catalog, engine, session/handlers/protocol, integration tests, docs | immediate critical path |
| Studio UI | isolated `studio-parameter-ui` / `codex/studio-parameter-ui` | frontend protocol/store, scope and local-favorite UI, frontend tests and browser journey | frozen wire contract below |
| Local persistence | isolated `studio-local-favorites` / `codex/studio-local-favorites` | existing library store, persisted-state migration, typed local favorite record, focused tests | shared immutable scope DTO |

Two implementation workers maximum; neither starts a heavy test/build without
coordination. Integrate the disjoint branches into this existing PR with normal
merges. No competing PR or stacked PR. Required dimensional reviewers run in
batches of at most two after composition. Routine repairs continue autonomously.

## Contract And Invariants

- `ParameterSelection`: `cells=None` preserves the legacy all-control default;
  `cells=()` explicitly selects no controls. A cell is `{item_id, parameter_key}`.
  IDs, duplicates, canonical ownership and mutable source availability are
  validated on the server before session changes.
- `mutation_parameters_changed`: `rytm_parameters`, `a4_parameters` are null or
  cell arrays; `controls` contains canonical item/page/name/key/value/domain,
  evidence, native-precision, protection and blocker metadata. No label or
  imported display metadata is authority.
- `set_mutation_parameters`: `device_id`, `parameter_cells` (null or cell array).
  `set_rehearsal_preset`: applies only the conservative Rytm Pad 2 common-control
  preset, locks other pads/all A4, and labels the new-build physical gate pending.
- Scope is resolved before PRNG proposals; excluded cells retain exact original
  values, including out-of-CC/native fractional encodings. Locks/protection win.
  Preserve draw ordering, legacy conformance and full-plan paired refusal.
- Scope changes revoke candidates/plans/confirmation contexts. SEND independently
  rejects out-of-scope proposed changes; never trim an already blocked plan.
- A4 selection exposes only supported saved-KIT offline fields. General A4/BOTH
  transmission, CY Ride SRC, paired precision and automatic restore remain held.
- Local favorite retention reuses `LibraryStore` atomic writes with a versioned
  immutable rehearsal record: source/profile/candidate, target/parameter scopes,
  locks, seed/depth and a checked identity. Recall restores exact offline values,
  revokes output/plan authority and requires new preparation. Hardware uses fresh
  capture and manual reload, never persisted favorite authority.

## Execution, Verification And Delivery

Software execution budget: four hours before reassessing remaining work, not a
promise to stop unfinished verification. State/recovery use this existing plan,
STATE and RUN_REPORT plus ignored raw receipts. After interruption inspect HEAD,
dirty files, worker branches and runner summaries; resume the next incomplete
step without repeating hardware work. STOP pauses owned jobs and records state.
No hardware/USB/MIDI access, pin changes, parity regeneration, force-push,
approval bypass or external worktree deletion is permitted.

Verify zero depth, per-cell isolation, lock/protection precedence, native source
preservation, malformed/forged scope, stale preparation, local retention/recall,
restart/disarmed behavior, write/load failure and migration/downgrade refusal.
Run full Python coverage, architecture/frozen parity, strict typing, lint/dead
code, frontend coverage/build and the actual browser journey. Build Windows on
the existing hosted installer lane; smoke the exact downloaded executable with
MIDI off, record source and both binary hashes, preserve the previous delivery.

Rollback is reverting this phase on the PR branch and launching the unchanged
old portable copy; newer favorite records must refuse downgrade rather than be
silently rewritten. Existing older records migrate only through explicit policy.
Done means scoped candidate and favorite survive the actual offline UI/restart
journey, all required software gates pass, a reviewed source-bound portable copy
is delivered and one focused physical audition/manual-reload test is documented.
No software result labels this build show-ready.

# October 6 Continuation: Complete Offline Kit Preparation

Recorded before implementation at `0aaf9f3dbaa20ec5743805e2a5e377583ad3330b`.
Production baseline is `8b6b2ce0`; prior deliveries are immutable. PR #254 is
open against `modularize-v1.34`, 31 successful checks/three explicit skips,
Eddie's October 3 requested-changes review still controls approval. Already
completed scopes, Pad 2 preset and local semantic favorite recall are reused.

Working interval: **2026-10-06 12:24:24 through 20:24:24 America/New_York**
(`2026-10-06T16:24:24Z` through `2026-10-07T00:24:24Z`). This is an eight-hour
development deadline, not permission to create filler or promote hardware
evidence. On interruption inspect this plan, state/run report, ignored
`output/local/OCT06-OFFLINE-PREPARATION-RESUME.md`, actual branches and runner
receipts. Finish useful independent work; stop rather than wait for hardware.

## Remaining Demonstrated Gaps And Architecture

Studio exposes only Filter 1 Frequency despite existing native A4 field codecs.
Audit each candidate field's canonical offset, width, converter, legal domain,
coupling and executable retained evidence before exposing offline mutation.
Do not infer native locations from MIDI addresses, normalize unknown selectors,
mutate FIN independently or drop hidden precision. OXI-related AMP protection
and include-minus-deny locks win over requested scope.

Library records already retain decoded payloads and semantic favorites;
ShowBankStore/ShowPackService already retain framed artifacts and verify
packages. Inspect actual loss/validation/export gaps before extending them.
No second library, envelope codec, sender, package root or device registry.
Original frames, semantic favorites and generated candidates remain different
artifact kinds. An imported original is codec-verified file evidence, not a
fresh physical observation. Import/restart must revoke output/confirmation.

Complete one path: source files/retained capture -> canonical precise scope ->
small/large local candidates -> exact differences -> named favorite -> ordered
bank -> bounded export/import -> exact disarmed recall. Preview-only status
must stay explicit; software packages cannot manufacture hardware readiness.
Retain source identity, exact frames where available, scope, locks, seed/depth,
recipe/profile association and candidate values. Any schema change has an
explicit supported legacy read/migration and fails closed on newer versions.

## Pre-Code Ten-Row Assessment

| Dimension | Baseline / intended change |
| --- | --- |
| Onboarding | Existing scope/library/Forge owners documented; connect actual source import and offline bank path with one operator entry point. |
| Naming | Canonical field identity is separate from native/display/normalized values; original frame is not semantic favorite or hardware backup. |
| Coupling | Core Device/native capability, Cockpit integration and existing atomic stores; disjoint workers, one composed checkpoint at first real import. |
| Constants | Derive widths/domains/enums from canonical facts/converters; no invented offsets, selectors or TypeScript copies. |
| Configuration | Existing roots, path policies, runtime/backend and hosted installer lane; backend off, no new arbitrary wire paths. |
| Tests | Reuse retained fixtures/shared fakes; source-specific byte isolation, coupled precision, corruption/rollback and real producer/consumer tests. |
| Build loop | Prior accepted Python 305.67s, browser 59.2s; resource preflight about 17GB free. Two pytest workers, one browser worker, one heavy local job. |
| Errors | Specific field/source/schema/size/integrity refusal, bounded logs, no path leakage or silent replacement with demo data. |
| Versioning | Product version/pins unchanged; source-bound Windows manifest/hashes; preserve both earlier portable deliveries. |
| Extension | Use existing catalogs, DTOs, atomic library/artifact/pack machinery; future fields require their own evidence, not inheritance from a neighbour. |

This continuation does not cure historical Gate 14/16 timing exceptions or
claim the outstanding post-merge audit. Reassess these ten rows after integration.

## Ownership And Composition Contracts

| Stream | Owner / branch | Write ownership |
| --- | --- | --- |
| A4 native capability | worker A / `codex/offline-a4-native-oct06` | `data/analog_four_*` native facts only as needed, `devices/` native capability/strategies, focused native tests, field-evidence inventory; no Cockpit/web/store changes |
| Retention and packs | worker B / `codex/offline-retention-oct06` | `cockpit/library/`, `cockpit/show_bank/store.py`, `export.py`, `workspace.py`, persistence registry/migration if needed and focused retention/export tests; no shared ShowBank DTO, Forge/A4 preparation, WS or web changes |
| Integrated workflow | coordinator / existing delivery checkout | shared Cockpit DTOs, source import/Forge generation/A4 review, WS/session/protocol, existing frontend, full journey tests, docs and delivery |

Workers begin by surveying evidence/interfaces and report a small concrete API
contract before changing a cross-owner boundary. Native capability returns typed
field metadata and selected-field candidate render/readback, always without live
authority. Retention exposes validated original frames/package results through
public store/workspace methods, not caller filesystem paths. WS commands use
existing authenticated dispatch and canonical events; frontend invokes real
command call forms. Source import invokes registered family codecs, not synthetic
capture construction. All consumers test the real collaborator on composition.

Security examples must reject bool ids, foreign families, mismatched frame/hash,
duplicate JSON keys, unsupported schemas, truncation, malformed native values,
unselected/protected/coupled changes, stale revisions and interrupted publication.
Rehashed metadata cannot grant live authority. One paired manifest is published
last only after both required frame sets are durable; failed writes preserve the
previous complete generation. Bound bytes, files, history, queues and caches.

## Verification, Checkpoints And Delivery

Two implementers maximum. Focused tests during implementation, coordinated
`-n 0`; one integrated source-frozen Python coverage run with `-n 2`, canonical
touched coverage, architecture/parity, strict typing, lint/dead code. Frontend
coverage/type/lint/build and browser use one worker, zero retries. Do not repeat
unchanged accepted suites; inspect runner summaries rather than worker prose.
At first cross-owner import run the composed native/retention/WS consumer cases
with real artifacts before broad acceptance. Checkpoint before each long job.

Publish one coherent increment to existing direct-base PR #254, no stacked or
competing PR. Normal hooks and eight bounded review dimensions remain required.
Build Windows on existing hosted installer workflow, preserve earlier deliveries,
verify source commit and binary hashes, and exercise the actual package with MIDI
off: import, scope, repeated small/large previews/recalls, named ordered favorites,
export/import, stale/cancel/error handling, backend loss/restart and exact disarmed
recall. Stop only owned processes/listeners; no hardware/USB/MIDI access, arming,
device writes, dependency/pin changes, parity regeneration or policy bypass.

Rollback reverts only this phase and uses the unchanged earlier package; new
records cannot be silently downgraded. Done is the complete evidence-backed
offline preparation journey, passing source/build receipts and concise handoff.
Remaining native gaps and all physical/transport restrictions are explicit.
The first physical gate stays one scoped Pad 2 audition, manual KIT reload and
fresh exact baseline comparison; no software result grants show readiness.

## October 6 Post-Integration Reassessment

Recorded after source088f3eec integration, before protected merge. This is not
the historical retrospective baseline or the still-required post-merge audit.

| Dimension | Actual integrated outcome |
| --- | --- |
| Onboarding | Existing Studio/Device/store owners retained; one ordered offline file-to-bank guide and separate physical gate. Actual packaged acceptance still required. |
| Naming | Native encodings, screen values, original framed bytes, semantic favorites and hardware SAVE stay distinct; legacy F1 alias is canonical and shared. |
| Coupling | Optional Device capabilities and shape-only DTOs; shared reader below both stores; one-way validated Library lookup, shared source/recipe verification before local publication. |
| Constants | Native protection/evidence/count facts moved to immutable data; no new offsets, enums, tuning or MIDI precision guesses. |
| Configuration | No new shipped environment reads; writer privacy is an opt-in API. Previous Windows copies/pins/fixtures stay unchanged. |
| Tests | Retained-fixture journeys, consumer faults, redacted rollback, corruption, source/precision/locks and exact restart; 49 touched modules measured100%, frontend1172 tests100%. Final full-suite receipt remains separate. |
| Build loop | One bounded heavy acceptance job, two pytest workers/one browser worker. Full source attempts351.40s and369.86s retained as failed checkpoints; focused repairs/coverage do not relabel them green. |
| Errors | Strict source reads preserve bounded hash/codec/access categories; IDs/paths redacted through Library and sensitive writer rollback; populated success counters exposed deterministically. |
| Versioning | Existing v1/v2 records read explicitly into v3 without rewriting; immutable profile/algorithm replay; unsigned source-bound1.34.0 package pending, no production release inferred. |
| Extension | Exact native-domain grids and sparse selectors are justified shapes; original retention/recall reuse existing atomic and package machinery. Default-only or unknown values remain read-only. |

One nonblocking review suggestion remains: generation validates its original
pair and immediately rereads the frames through existing helpers. Reuse within
that request could reduce duplicate reads, but no latency measurement or
behavioral defect was found; avoid coupling this cleanup to acceptance fixes.
Historical Gate14/16 exceptions, human approval and post-merge review stay open.

## October 6 Reliability And Sustained Offline Rehearsal

Pre-code scope recorded for the new user mission at2026-10-06T21:41:19Z;
eight-hour ceiling2026-10-07T05:41:19Z. Starting receiptaf5a2b40, production6eb,
Windows37523755117 and preserved delivery6eb. Coordinator is clean; PR254 is
direct-base modularize-v1.34 with31successful checks/three skips. Eddie's
October3 review remains changes requested. Resource preflight:16.93GiB free of
31.75GiB. Primary dirty checkout and unrelated worktrees are not edited.

### Boundaries And Ownership

| Stream | Disjoint ownership / intended outcome |
| --- | --- |
| Failure reporting worker | Existing ShowPack export/reader and WS ShowBank adapters/handler error seam, focused failure tests. Reproduce missing-package generic error; return categorical actionable path-free reasons without echoing arbitrary exception messages or granting authority. No Library/workspace/write-engine/web changes. |
| Adversarial retention worker | Library and ShowBank workspace/store or atomic writer only when a demonstrated failure requires it; new focused composed tests. Multi-cue source associations, immutable-profile recall, migration, duplicates, missing/corrupt/mismatched data, interrupted publication and exact protected bytes. No ShowPack exporter, WS handler, web or new error schema changes. |
| Coordinator | Existing frontend consumer if required, rapid scope/backend-loss journeys, reproducible endurance driver/measurements, source composition, docs/checkpoints/review/build/delivery. |

Workers branch from the pre-code scope commit in isolated managed worktrees;
no sibling PRs. Agree a public producer/consumer call contract before crossing
ownership. First real composition checkpoint executes the actual error handler
and retention/import/recall producer-consumer tests, not mocked collaborators.
Use existing DataError taxonomy, canonical JSON/readers, atomic writer, library,
ShowBank, registered codecs/native capability and authenticated WS dispatch.
Cancellation/refusal must preserve previous bank/source/favorite and publish no
partial destination. Missing/corrupt/unsupported-schema/source-mismatch reasons
must explain recovery without paths, secrets or raw exception chains.

### Verification And Endurance Contract

Two implementation workers initially; focused tests coordinated -n0, composed
full coverage -n2; browser1/retries0 and only one heavy local job. No real
MIDI/USB enumeration/open/arming/write, capture command, firmware/device change,
pin/fixture/gate change, A4/BOTH/CYRide/paired/restore promotion or Pi activation.
Every source/precision/selector claim stays on existing evidence and protection.

The measured packaged-app run is90-120actual wall-clock minutes after any
required repairs/new package. Use one isolated MIDI-off test-owned app/backend
and retained representative files, legal bounded multi-cue banks and candidate
counts. Cycle real UI generation/inspection/favorites/order/export/import/recall;
include controlled owned-backend loss/restart and commands around reconnect.
Keep bounded telemetry (latency, process working/private memory, handles/process
count, client command/ack queues and server histories/caches through existing
diagnostics), periodic durable progress, source/candidate/lock/precision identity
assertions, a declared minimum duration and explicit pass/fail stop reason.
Never call a shorter interrupted run an endurance pass. Optimize repeated reads
only if measured evidence justifies it; preserve validation and byte checks.
Stop only owned processes/listeners and keep QA credentials outside delivery.

Production changes require a new exact-source unsigned Windows build through
the existing hosted installer lane, manifest/hash verification and actual-binary
acceptance. Preserve old copies. Source-frozen focused/full/architecture/parity,
canonical touched100%coverage, strict typing, lint/dead-code, frontend coverage
and actual journeys precede final acceptance. Required dimensional reviews and
protected human approval remain separate; update only existing direct-basePR254.

### Pre-Code Maintainability Assessment

| Dimension | Intended contained change |
| --- | --- |
| Onboarding | One existing offline/studio handoff with exact tested build and four-field Pad2 first gate. |
| Naming | Typed failure categories distinguish missing/corrupt/incompatible/mismatch from cancellation and hardware protection. |
| Coupling | Existing export-reader/WS seam and Library/workspace/writer; public call contract and one integration checkpoint. |
| Constants | Existing size/cue/candidate/cache/history bounds; no invented native or MIDI facts. |
| Configuration | Existing MIDI-off launch and isolated state; QA duration/paths are explicit driver inputs, not a shipped bypass. |
| Tests | Meaningful retained-frame/fake-port adversarial tests plus actual binary endurance; fixtures never grant physical evidence. |
| Build loop | Prior full250.49s/front100.51s/browser1.1m; one heavy process, two pytest workers/one browser. |
| Errors | Specific actionable messages, stable taxonomy and bounded path-free diagnostic context; previous complete artifacts survive failure. |
| Versioning | Preserve source6eb delivery; new source commit/hashes if production changes, explicit supported legacy migration and newer-schema refusal. |
| Extension | Reuse existing mechanisms; no parallel dashboard, workflow/store, exporter or sender. |

All18gate definitions/checklists above remain binding. Reassess after integration;
historical Gate14/16 exceptions are not retroactively cleared. Track actual
start/end, interruptions, phase durations and stop reason in the run report and
compact resume checkpoint. Rollback uses unchanged6eb and reverts only this
contained phase; no user data/old delivery rollback or destructive cleanup.
Done: specific safe failures, verified adversarial journeys, completed measured
endurance, source-bound usable delivery/handoff, no independent software task
left. First physical gate remains backed-up fresh capture, four-control Pad2 at
10%, exact approved audition, DISARM, manual KIT reload and fresh comparison.
Offline acceptance is not show readiness.

Coordinator pre-code observability contract: add aggregate read-only outbound
queue counts to existing GET /health through ConnectionRegistry, not another
dashboard or command. Counts include capacity, active connections, queued frames,
active-connection high-water and drops; never frame contents, paths, tokens or
connection IDs. Preserve drop-oldest/closing/FIFO and authentication exactly.
The endurance driver samples this existing health surface and records backend
restart segments; history reuse is observed without inventing a global history
eviction policy. Source/store/WS repairs remain in their declared ownership.

### October 7 Interrupted-Run Continuation

Resume at 2026-10-07T15:37:39Z with a fresh eight-hour ceiling of
2026-10-07T23:37:39Z. Preserve published db2daf6c and both pending edits.
Finish categorical QA diagnostics, creation-ordered process ownership and
scope-refusal input logging. Diagnose the native hydrate_reload failure from
run37544839205 with actual logs/artifacts before repairing its cause; retain
strict assertions and existing deadlines. Freeze and review the corrected
source, build through the existing Windows lane, verify the exact executable,
then run a real90-120minute offline endurance exercise. Prior100second trials
remain smoke only. Parent owns native startup and delivery; a disjoint worker
owns the QA driver/verifier repair. No MIDI authority or dependency changes.

Packaged1c093 smoke exposed a pending-preset/device-selector race before timed
acceptance. A controlled delayed-response regression fails because device/item
selectors remain enabled while the preset later resets their view. The contained
repair owns only the existing MutationParametersPanel and its canonical-fixture
tests: hold those selectors during presetPending, then restore normal selection
after success/refusal. Server locks, generation authority and protections remain
unchanged. Rebuild the exact reviewed source and rerun actual package setup before
the full timed rehearsal. The unrelated hosted macOS numba/librosa segmentation
fault is investigated separately without dependency bumps, skips or retries.

Bounded macOS follow-up (not executed or accepted): preserve1c093, its exact
librosa0.11.0/Numba0.68.0/llvmlite0.50.0/NumPy2.4.6 environment and canonical
two-second440Hz mono input. Collect the native crash report and bounded cache
trace using NUMBA_DEBUG_CACHE=1. Compare two-process shared-cache cold/warm
execution with two-process individually isolated-cache cold/warm execution;
eight fixed observations total, no retry-to-green. Compare input SHA, complete
onset arrays and canonical feature outputs, retaining failed exit statuses.
Do not alter extractors, dependency pins, parity or required-check semantics
without causal evidence. A manual diagnostic must not emit required-checks
success through skipped suites or reuse the installer as an unrelated runner.
The unchanged environment previously passed on the same macOS image, so a new
green run cannot by itself prove the native defect repaired. This remains a
separate platform follow-up, not Windows offline-bank or hardware acceptance.

Containment for the repeated1784 macOS fault: add a bounded diagnostic script
and fake-process regression tests, with no production extractor edits. Run it
only after a failed macOS required pytest step, retaining the original failing
job and aggregate result. It must collect fixed cold/warm shared/isolated cache
observations and available crash metadata, not retry the suite until green.
Parent owns the existing workflow post-failure step/docs; one disjoint worker
owns scripts/diagnose_native_audio_cache.py and its tests. Keep the running
1784 Windows rehearsal frozen. Only lightweight fake-process tests may overlap
it; normal publication/architecture gates wait until owned endurance completes.

Measured Windows endurance failed after81cycles/2413seconds, not acceptance.
The last generation acknowledged successfully, but no final favorite command
was sent: the QA controller snapshots confirmation visibility immediately.
Replace that snapshot with an authoritative replacement decision and awaited
confirmation; preserve deadlines and strict favorite checks. Separately,
favorite acknowledgements rose to4.818seconds, while a read-only90candidate
bank context verification measured1.370seconds and the WS action repeats that
full validation three times. Contained production optimization may reuse one
verified immutable recall context within that action only, preserving whole-bank
byte/profile replay before publication, fresh validation on each new action,
stale-source rejection, cancellation and disarmed recall. No long-lived authority
cache, skipped unrelated artifacts, packet filtering or timeout increase.

### October 7 Measured Generation Deadline Continuation

The exact84 Windows attempt failed after140cycles/4187.123seconds. Both owned
backend recoveries passed and cleanup passed; this is not endurance acceptance.
The last complete export proved148candidates. A subsequent manifest contains
the149thcandidate with seed3240, published after the five-second UI deadline.
No bank or source loss is observed. Diagnose actual generation latency and
publication/response ordering using an isolated copy of the retained failed
state. Preserve that state as evidence.

Survey and reuse canonical generation, whole-bank verification, action-local
source contexts, native capabilities and Store publication. Optimize only
measured redundant proof/decoding/source reads. Every requested source,
previous selected/favorite candidate, unrelated retained artifact, exclusion,
lock and new candidate must remain validated before publication. Use immutable
action-local data; no persistent authorization cache, guessed encoding, skipped
checks, timeout increase, retries or partial-packet manufacture. Preserve the
existing public generation return shape and disarmed adoption.

One implementation worker owns workspace/generation tests; parent owns this
plan, QA diagnostics, verification and packaging. Only one heavy process runs.
Add meaningful regression coverage for the reproduced late path and fresh
proof/refusal/publication invariants, then run the frozen source gates and
review. Rebuild only if production changes. Start a new90-100minute packaged
attempt from zero; do not combine40/70minute failures or smoke. If the fresh
eight-hour ceiling23:37:39UTC prevents acceptance, preserve the exact pending
checkpoint and report the uncompleted gate rather than granting readiness.

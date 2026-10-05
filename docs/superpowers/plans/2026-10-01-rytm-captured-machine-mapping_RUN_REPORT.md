# Captured Rytm mapping software report

> Status: in-flight — October 5 review repairs integrated, final software/build
> acceptance in progress; protected review and physical rehearsal remain pending.

## October 5 continuation

Current assembly checkout is `codex/studio-rytm-mapping`; the existing PR #254
head is `codex/studio-evidence-handoff`, updated by a fast-forward, continuing from
`0138d00b`. All eight CY Ride SRC rows are held, including compact aliases and
constructed mixed proposals. The audited 29 fallback rows now comprise 25
documented-only guarded-CC7 eligible controls and four blocked CY Ride controls.
The exact initialized/RIO frames project 328/325 values, with source bytes
unchanged. Studio pad cards derive SRC labels, addresses, values and blockers
from the canonical Python catalog; display metadata conveys no SEND authority.

The #240 stale-handshake outcome driver replaces the prior stale-store check;
the shared beacon TLS repair is retained. The shared test snapshot factory is
public. Detached failures are promptly observed, and dispatcher failures reuse
the categorical ack builder. Fresh mutation orchestration records bounded
pad/blocker preservation outcomes without changing pure mutation math or adding
another RED command count. Frozen legacy `lev` arithmetic is tracked in issue
[#256](https://github.com/buzzijose-hub/RytmRandomizer/issues/256).

The first combined run had 10,036 passes, three failures, five skips and six
warnings. Two non-parity inventory fixtures were intentionally updated; a facade
construction test now explicitly clears the launch-only MIDI-off environment.
Its focused recheck passed 294 cases without importing a MIDI backend or opening
a port. The frontend has 1,070 passing tests and 100% measured coverage; typing,
lint and the production web build pass. Final Python/coverage, browser and binary
smoke receipts will be recorded before handoff. No listener remained on the usual
Studio ports at preflight, and no MIDI access or new physical observation occurred.

The second combined run had 10,042 passes and one architecture failure: an
added broad exception catch was rejected. Its coverage was invalid because
source changed during the run. The catch was removed; the task-completion
observer now gives pre-ack failures one categorical RED result and post-ack
failures a separate counter without duplicate acknowledgement. Completed failed
tasks are not re-awaited during teardown. The focused 177-case recheck passed,
and the targeted static observability re-review cleared both findings.

The final source-frozen composition passed **10,044 tests, five skips and six
warnings in 338.60 seconds**. Combined coverage is 99.6557048%; pure branch
coverage is 99.3693402%. Coverage JSON independently confirms all 22 production
modules in the full PR diff have zero missing lines or branches; the canonical
committed-diff check follows the commit. No frozen parity fixture, dependency
pin, safety gate or hardware observation changed. One-worker browser acceptance
passed 33 scenarios with two explicit skips in 1.2 minutes. It covered the
memory-output exact confirmation contract, paired-control refusal, input-file
library persistence, wizard cancellation and reconnect/fresh-token behavior;
it performed no physical send. Strict typing of 22 production modules reports
zero errors/warnings. Whole-tree Ruff, Black (895 files), isort and Vulture
pass; four version declarations remain at 1.34.0. The Windows binary will be
built on the hosted runner rather than
installing or compiling a Rust toolchain on the operator's computer.

The committed-diff coverage gate passes for all 22 production modules. Normal
pre-push verification passed lint/strict typing, 860 architecture cases in
59.50 seconds and 697 not-fast cases (including all 685 V1.34 goldens) in 6.62
seconds. A delivery-branch-only installer dispatch was cancelled before using
it as evidence; the final portable build follows the actual PR head. No new
PR, merge, auto-merge or protection bypass is introduced.

## Historical receipts through October 2

Delivery starts at Studio PR #254 head `941643c5`, directly based on
`modularize-v1.34`. The separate local runtime checkout at `2a19b094` contains
only the mapping correction and its tests on the prior Pi source. Its software
checks passed, and at that historical checkpoint the studio server ran that backend with outputs disarmed.
The existing `8cfa6f7b` frontend bundle is reused after exact hash verification
and confirmation that frontend sources are unchanged between those commits.
No new Pi package or frontend build is claimed. The operator reconnected and
sent saved KIT 01; its fingerprint matches `5f75b9fb4856e8c7`, the bridge logs
324 promoted parameters, and XT Classic cards 6–8 expose captured controls.
No new raw-frame SHA was retained, so no new exact-byte comparison is claimed.
This is input/projection evidence only. The registry increment is PR #254 work.

The correction changes three existing mapping modules. Exact XT Classic ID 8
can be promoted on tom pads 6–8. Canonical owning machine sections survive
reverse lookup, while the bridge requires promoted matching identity and exact
CC agreement. Retained raw `0x88` and other unverified tom values cannot acquire
SRC mutation authority. The existing paired-control whole-plan refusal remains.

The registry follow-up changes three existing report/data modules, introduces
one report-specific TypedDict and one generic summary helper, and adds no
production module or registry. `all_devices()` supplies identity metadata;
canonical evidence labels supply existing family rows. Unknown registered
devices appear with zero rows and `no_support_evidence`.

The mapping/registry increment published at `2f0f5be0`, compared with the
starting Studio head `941643c5`, changes six
existing production modules (**95 lines added, nine removed**) and eight
test/helper modules (**427 added, eleven removed**). Fact-table/report fixtures
and documentation are additional; no production module is added or renamed.
The final PR retains the earlier shared Studio safety work and subsequently
adds the existing MIDI-provider compatibility change and three native files.

Verification, using the original Windows virtualenv and two pytest workers.
The earlier runs below precede the A4 compatibility change:

- First prototype: 5 failed, 10,670 passed, five skipped. Three seed assumptions
  and two plan-record failures were investigated; the focused seed repair passed
  22 tests. This is failed historical evidence.
- First Studio run: one plan status-format failure, 9,819 passed, five skipped in
  286.42 seconds. The status marker was corrected; eight plan checks passed.
- Final combined Studio run: **9,823 passed, five skipped, six existing warnings
  in 269.56 seconds**. Combined coverage 99.65%; pure branch 99.37%, above the
  99% floor. All 18 touched production modules have 100% lines and branches.
- Strict typing: all 18 touched production modules, zero errors or warnings.
  Ruff, Black, isort, Vulture and version consistency passed.
- Public offline decode/bridge of the retained studio KIT and both RIO KIT
  fixtures: each has 324 keys, 60 SRC keys and three ready XT rows. Original
  frame bytes remain exact. This opened no MIDI ports.
- Separate local runtime `2a19b094`: **10,678 passed, five skipped, six existing
  warnings in 305.83 seconds**. Combined coverage 99.66%; pure branch 99.39%.
  The canonical touched-coverage check against `8cfa6f7b` confirms 100% lines
  and branches on all three changed production modules. Strict typing and
  whole-tree lint passed. The server restart was verified healthy; it opened
  no output and started no capture. Restart alone does not prove recovery.

The Studio and Pi engines differ in their optional mutation arguments. The
transplanted tests initially used a Pi-only argument; they now exercise genuine
Studio all-parameter candidates with fixed supported/refused seeds. Those
public acceptance cases do not rewrite candidates or source data to obtain a
passing plan; older isolated unit harnesses may inject candidates deliberately.

The initial scoped registry architecture check briefly overlapped a full run;
subsequent heavy runs are sequential. Do not claim the whole execution used
one heavy process at every instant. Scoped dimension reviews found no remaining
production issue; final source receipts and post-push review still govern delivery.

Published the software increment at `2f0f5be021079bfb78922a6d20b66d0bb5b44825`.
The canonical touched-coverage checker confirms all 18 modules. Actual pre-push
lint, strict typing, 860 architecture and 697 not-fast checks passed, including
685 frozen parity cases. Eight separate scoped post-push reviews found no new
production blocker. The review retains one Important process exception for
retrospective audit/isolation acknowledgment, and the prior task-error timing
and private browser-factory import minors. A pre-existing architecture anchor
was repaired in the documentation receipt update. Eddie's review was requested;
protected approval and final documentation-head checks remain pending.

At the historical `2f0f5be0` checkpoint, the inventory retained eleven missing
alias families. The later scoped closure binds all 224 SRC rows; semantic,
precision and Studio display gaps remain explicit in the current
[inventory](../../RYTM_MAPPING_STATUS.md). The earlier October 1
Rytm trial checked four common controls and manual recovery; it did not audition
this SRC repair. General A4/BOTH, automatic restore, Pi hardware and touring
acceptance remain unvalidated. The later one-control A4 observations are scoped
separately below and do not establish SRC transmission.

The subsequent approved A4 helper attempt failed before backend send with
`midi_wire_unsupported_message: Message`, reporting 0/1 messages. The operator
confirmed PWM Depth remained 0. The existing lazy provider wrapper did not
recognize the legacy helper's public message `type` spelling. Compatibility
repair and composed source verification are required before the same approved
one-integer-CC retry; neither this failure nor the saved KIT capture grants
general A4/BOTH SEND.

Hosted checks at software head `2f0f5be0` exposed a separate inherited native
TLS initialization race. Push run `36944994908` passed, while PR run
`36944998820` failed `journal_ui` with a missing-provider panic (31 passed,
one failed). Both used the same locked versions. Native provider initialization
repair and new-head hosted verification are pending; no local Rust build is
claimed because Cargo is unavailable.

The final composed Python source at `0130f5c5` passed **9,836 tests, five skips,
six existing warnings in 270.32 seconds**. Combined coverage is 99.65%; pure
branch coverage is 99.37%. The canonical checker confirms all 18 touched Python
production modules at 100% lines/branches. Strict touched typing, whole-tree
Ruff/Black/isort and Vulture passed. These checks do not compile Rust.

The separately installed helper source `76634665` passed **10,691 tests, five
skips, six warnings in 286.21 seconds**, with 99.66% combined and 99.39% pure
branch coverage. All four changed modules versus `8cfa6f7b` have 100% lines and
branches; strict typing and lint passed. The running server process retains
the mapping backend loaded at `2a19b094` and unchanged `8cfa6f7b` frontend;
the standalone helper is a fresh process using `76634665`. It did not require
another server restart or private login.

That helper accepted one authorized channel-1 CC74/value1 on the exact A4
output, with an operator report of PWM Depth 1 and manual KIT 01 reload to 0.
The operator explicitly requested a repeat, reloaded saved KIT 01 and confirmed
PWM Depth 0 before another separately requested one-message action. The
repeat's physical value was checked at 1 before reload, then at 0 after
manual NO + KIT. Thus two successful one-CC actions were observed; the original
attempt remained a zero-send failure. No hardware save or new saved-frame
capture was performed. This proves one integer control and manual recovery,
not general A4/BOTH SEND, paired conversion, automatic restore or Pi readiness.

The new wire-boundary lesson, skill invariant 19, received a separate reviewer
evaluation using the existing `docs/SIMPLIFICATION_PLAN.md` five-dimension
rubric (minimum 3/5). This is not a rerun of the earlier document-copy simulation
or an external learning plugin:

| Dimension | Score | Evidence |
| --- | --- | --- |
| Specificity | 4 | Names the actual lazy provider and fake-message attributes that concealed the mismatch. |
| Actionability | 5 | Requires public helper/provider composition, field validation and boundary reconstruction. |
| Scope Fit | 4 | Fits the existing hardware-send safety skill. |
| Non-redundancy | 4 | Covers a wire representation defect absent from the earlier captured-anchor lesson. |
| Coverage | 4 | Public CC/NRPN composition plus unsupported primary kind, boolean and range refusal regressions; no general live-send claim. |

Gate 14's timely baseline and actual post-merge assessment remain limitations;
Eddie's prior acknowledgment applies to the earlier handoff receipt. Gate 15
learning capture includes the architecture comparison, replay/state schema,
existing rule/guidance updates and composed capture-seam lesson. The
[independent onboarding exercise](2026-10-01-rytm-captured-machine-mapping_ONBOARDING.md)
answers five questions using an isolated repository-document snapshot; its
reviewer scores are 4/5 on every documented rubric dimension. It ran no tests
or installation and does not claim a published clone. Commit/publication
receipts and protected plan termination remain separate. Historical phase-isolation
limits remain disclosed under Gate 16. No automatic merge or scheduler exists.

Resume using the [state](2026-10-01-rytm-captured-machine-mapping_STATE.json),
[log](2026-10-01-rytm-captured-machine-mapping_RUN_LOG.md) and
[plan](2026-10-01-rytm-captured-machine-mapping.md). Re-run source-specific checks
after any production change; preserve the original dirty user checkout and
the retained hardware frames. Rehearsal output requires a separately reviewed
concrete target/value/port and operator confirmation.

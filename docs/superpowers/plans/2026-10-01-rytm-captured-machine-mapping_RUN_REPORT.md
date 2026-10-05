# Captured Rytm mapping software report

> Status: in-flight — October 5 software candidate packaged and MIDI-off smoke
> passed; protected review and physical rehearsal remain pending.

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

Hosted Python 3.11 checks at `4b29c971` exposed three log-count assertions that
attached the same capture handler both locally and through logger propagation.
The test-only repair isolates the module handler and explicitly covers package
propagation both enabled and disabled; the focused recheck passed 165 cases.
The clean full rerun passed **10,048 tests, five skips and six warnings in
324.94 seconds**. No production source changed from the identified binary's
`4b29c971` source. The execution checkpoint's two new descriptive properties are
now declared in its closed schema, and Draft 2020-12 validation passes. Historical
Gate 14/16 timing exceptions remain disclosed, not retroactively satisfied.

The packaged `4b29c971` executable starts disarmed with its bundled sidecar
and MIDI disabled. A fresh isolated WebView profile permits native CDP testing;
no registry, security policy or runtime installation was changed. The first
exercise correctly refused a 90% candidate with `candidate_high_risk`, but the
UI showed only "Blocked" for that reason. The bounded SafetyRail repair now
renders every existing closed readiness reason without changing any planner,
arming or output rule. Frontend verification passes **1,075 tests in 42.20
seconds**, with 100% statements, branches, functions and lines; typecheck,
ESLint and production build pass. The final identified package must include
this presentation repair, so the earlier binary is not the final handoff.

Final docs review also corrected stale checkpoint publication/Studio-label
claims and documented the optional cancellation Protocol, legacy fallback and
reservation lifetime. Operator instructions now acknowledge that scope selects
whole pads/tracks, not a common-controls-only subset; a full-capture candidate
may be blocked by changed paired LFO Depth. Rytm Filter Frequency is single CC74,
not the paired A4 Filter 1 Frequency boundary. No paired conversion was unlocked.

## Identified Windows candidate

Production source: `fa43f86399394bd44ae97e2d48510f8b85a9fe7a`, version 1.34.0,
remote branch `codex/studio-evidence-handoff`, existing PR #254. Later receipt-only
commits do not change the packaged production source. Hosted Windows-only
[installer run 37341458245](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/37341458245)
succeeded. No local Rust toolchain or heavyweight native build was used.

Local portable folder:
`C:\Users\Jose Buzzi\Documents\ShowKitForgeStudio\show-kit-forge-studio-fa43f8639939`.
Keep the executable and `binaries/rytm-sidecar.exe` together. The unsigned Studio
copy requires WebView2, not a Python installation. `BUILD-MANIFEST.json` records
the source, workflow, toolchains, resource/config overrides and these independently
matched binary hashes:

- Shell: `ffb1f9c0030bf620e539223e9bbf122dbe6453a49554e45be9a2d2c3b746dee3`.
- Sidecar: `8c32b273f0aa4357e89b088f3bcb6ed78e08dccec2b9bf5a4940c42db9f58916`.

The actual Tauri executable, bundled sidecar and embedded WebView passed an
isolated MIDI-off smoke: disarmed startup, Pad 2 targeting/Pad 1 lock, 10%/90%
previews, exact plan observation, specific paired/high-risk refusals, disabled
capture without a backend, capture-panel close, local bank creation, missing-source
adoption and empty-export refusal. Desktop/600px screenshots show readable SRC
metadata with no horizontal overflow. The 10% candidate was refused for paired
LFO precision; the 90% candidate was high-risk. Neither plan was transmitted.

Only the owned bundled sidecar process tree was terminated for recovery testing.
The shell restarted it, rotated credentials and reconnected while preserving
local bank metadata and remaining disarmed. Full shutdown/relaunch also retained
the bank, adopted the fresh token and stayed disarmed. This tests backend/socket
recovery, not MIDI disconnect/reconnect, hardware restore, favorite audition or
actual KIT capture. Those remain operator-present tests. Unit/browser fixtures
cover candidate/favorite persistence; the binary smoke proves bank metadata only.

The first CDP port did not open; a bounded isolated-profile/port retry succeeded.
The bank smoke locator initially assumed an exact label despite option text
being included in its accessible name; the corrected role locator passed.
These failed harness attempts are not passing receipts or physical observations.
No OS registry/security setting or runtime installation changed. All owned smoke
processes and test listeners were stopped; QA browser profiles and credentials
were retained outside the delivery folder, in ignored local output.

Final receipts: Python 10,048 passed / 5 skipped / 6 warnings (324.94s),
22 touched production modules 100% lines/branches, project 99.3693402% pure
branch coverage; frontend 1,075 passed with 100% across four metrics; browser
33 passed / 2 explicit skips (56.9s). Final ordinary pre-push gates passed
860 architecture and 697 not-fast cases, including 685 frozen parity items;
strict typing, lint, dead-code and version checks passed. Eight scoped reviews
and production-head delta confirmations found no remaining code findings.
Hosted native/full-platform outcomes and protected approval are separate gates.

Offline launch (MIDI and updater disabled; clears a development sidecar override):

```powershell
Set-Location "C:\Users\Jose Buzzi\Documents\ShowKitForgeStudio\show-kit-forge-studio-fa43f8639939"
.\Launch-Offline.ps1
```

The folder's `studio-procedure/STUDIO-FIRST-PASS.md` is the concise handoff.
First physical step: back up operator-chosen spare KITs and input-capture their
saved states while disarmed. Then target only Pad 2 at 10%, protect Pad 1/lock A4
and inspect the full plan. Whole-pad scope is not a common-controls-only mode;
stop on any blocker, never trim or bypass a refused plan. Only a separately
approved ready exact plan may proceed to one audition, manual saved-KIT reload
and fresh full fingerprint comparison. That can unlock a limited rehearsal,
not general SRC/A4/BOTH output or show use. Local **Mark favorite**/**Save bank
details** are not hardware saves; action-bar **SAVE** remains refused and
local **UNDO**/**Reset Cockpit audition to source** cannot restore hardware.

**READY for offline practice. NOT READY for shows.** No MIDI/USB port was
enumerated, opened or written during this continuation. Historical Gate 14/16
exceptions, Eddie's requested-changes state and merge protections remain intact.

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

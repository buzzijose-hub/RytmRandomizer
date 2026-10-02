# Captured Rytm mapping current maintainability reassessment

> Status: in-flight — prototype and composed-increment assessments recorded;
> mapping published; wire/native follow-up source checked and two bounded A4
> probes observed; final publication, protected review and post-merge assessment pending.

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gate14. Compare the
[retrospective baseline](2026-10-01-rytm-captured-machine-mapping_MAINTAINABILITY_AUDIT.md).
The historical assessment below describes the uncommitted prototype on
`8cfa6f7b`. The subsequent assessment covers the composed PR254 increment in
the delivery checkout starting at `941643c5`. Neither is an assessment of the
running studio app, and no merge has occurred in this record.

## Historical prototype assessment

| Required question | Before → current | Evidence and remaining work |
| --- | --- | --- |
| Onboarding curve | 3 → 3 | Plan, inventory, state and log explain facts versus readiness. Contributor timing and final direct-base link checks remain unmeasured/pending. |
| Naming hygiene | 3 → 3 | Exact owning machine section and generic SRC both resolve through one lookup; no new competing naming system. |
| Coupling / boundaries | 2 → 3 | Composed retained-frame tests cover XT, BD/SD and unverified machine refusal; 306 mapping-focused tests passed. Final delivery composition and architecture gate remain pending. |
| Magic numbers / strings | 4 → 4 | Existing canonical source token consumed; XT identity read from the machine catalog through a `Final` constant. Final static checks remain pending. |
| Configuration vs convention | 3 → 3 | No new env reads, MIDI channels or transport choices. Runtime configuration is unchanged. |
| Test maintainability | 2 → 3 | Shared retained-frame helpers, real consumer/planner checks and negative cases replace decoder-only confidence. Three newly exposed seed assumptions were repaired with 22 focused passes; final full suite remains pending. |
| Build / dev loop friction | 3 → 3 | First full run retained its failed verdict: 5 failed, 10,670 passed, 5 skipped in 204.98s. Two documentation failures were assigned for repair. No clean-install performance or final passing delivery receipt claimed. |
| Error messages / provenance | 2 → 3 | Offline frames now expose 324 keys / 60 SRC keys and XT readiness while unsupported facts still omit SRC. Inventory preserves alias, semantic and precision gaps; the live app has not yet received the correction. |
| Versioning / release | 3 → 3 | Existing PR254 against `modularize-v1.34` is the delivery path; final source, hosted checks and protected review are pending. No Pi or touring release. |
| Future-proofing | 3 → 3 | Correction uses three existing production modules. Missing aliases can use canonical data only when semantics are established; no new renderer or registry is introduced. |

## Composed PR254 increment assessment

This assessment includes the three captured-Rytm correction modules plus the
canonical evidence-family table, its data re-export and the existing passive
report's typed registry summaries. The report/data increment was implemented
in the separate `studio-inventory-registry` checkout at `941643c5` and then
integrated into the delivery checkout. Family-specific parameter rows remain
the existing evidence; `all_devices()` supplies registered identities, while
unknown identities receive an explicit zero-evidence summary. No new device
registry, renderer, send path or environment setting is introduced.

The coordinator supplied these scoped receipts: **23 passed** for capture API
compatibility, **286 passed** for the registry-focused checks, **567 passed**
for the selected architecture checks, one report golden check passed and
strict typing passed on the three report/data modules. These are software
checks, not physical captures. The coordinator's prior full coverage run
(`51572`) subsequently passed 9,823 tests, with five skips and six existing
warnings in 269.56 seconds. All 18 touched production modules have 100% lines
and branches; pure branch coverage is 99.37%. Strict typing passed on all 18
modules; lint and Vulture passed. These results do not establish physical readiness.

The mapping/learning increment is now published in existing PR #254 at
`2f0f5be021079bfb78922a6d20b66d0bb5b44825`. Actual pre-push checks passed
860 architecture and 697 not-fast cases, including all 685 frozen parity cases;
canonical touched coverage confirms the 18-module receipt. Eight targeted
post-push reviewers found no new production Critical or Important issue at
that SHA. The new retrospective Gate 14 acknowledgment and historical Gate 16
isolation/timing remain Important process exceptions. Prior off-reader exception
timing and private browser-factory import remain minor follow-ups. Final
changed-head checks, review, publication receipt and consolidated PR comment
remain source-specific. This published mapping receipt does not certify the
subsequent wire/native source by itself.

The fifth and sixth plan scopes were recorded before isolated implementation.
The historical wire/native Studio code checkpoint was
`0130f5c5841f6e9fb830ee8e3d395fc5bb2c89af`, containing the wire repair at
`648ae888`, native follow-up at `d698d62e`, and `0130f5c5` formatting. Its fresh
full Studio run passed **9,836 tests, five skipped, six existing warnings in
270.32 seconds**. Pure branch coverage is **99.3669858789% (99.37% rounded)**;
combined coverage is **99.65%**. Canonical touched coverage confirms all 18
production modules at 100% lines and branches. Strict typing on all 18 reports
zero errors/warnings; whole-tree Ruff, Black py311, isort and Vulture pass.
Frozen parity fixtures and production dependency pins remain unchanged. Six
source review dimensions are clean with the prior observability minor retained;
Docs/Maintainability confirmation, final receipt/push, post-push confirmation
and consolidated comment are pending at this metadata checkpoint.

Native validation has a separate boundary: Cargo is absent locally, so no
rustfmt, native tests, Clippy or native executable run is claimed. All 504
locked package versions and checksums remain unchanged. Historical CI at
`2f0f5be0` had one passing and one failing result, with the failure reporting a
missing TLS provider. New-head hosted native gates remain pending. The separate
runtime checkout `76634665a719eed661724dfa31cca004a5cbe75a` passed **10,691 tests,
five skipped, six existing warnings in 286.21 seconds**, with four touched
production modules at 100% lines/branches, 99.39% pure branch, 99.66% combined
coverage and passing strict typing/lint. The fresh standalone helper uses that
source; the running server process remains `2a19b094`, with unchanged `8cfa6f7b`
frontend. Neither a native run nor a server restart is inferred.

| Required question | Baseline → composed increment | Evidence and remaining work |
| --- | --- | --- |
| Onboarding curve | 3 → 3 | The plan now names the registry writer's actual isolated checkout, eight owned files and integration dependency. Inventory and architecture links explain identities versus evidence. The contributor timing target remains unmeasured. |
| Naming hygiene | 3 → 3 | Exact owning machine sections retain the established compact keys. `registered_devices`, `evidence_family`, `evidence_row_count` and `no_support_evidence` describe report coverage without granting device readiness; the normalized count key uses lowercase casing. |
| Coupling / boundaries | 2 → 3 | The bridge consumes canonical promoted facts and exact CC matching. The report consumes public `all_devices()` plus immutable data bindings and introduces no competing registry. The wire follow-up uses the existing provider boundary. The fresh 9,836-pass Studio suite covers Python architecture; native gates remain separate and unavailable locally. |
| Magic numbers / strings | 4 → 4 | XT identity derives from its canonical catalog through `Final`; source dispatch uses the established typed vocabulary. Registered identity-to-evidence bindings live in the data layer, with no duplicated MIDI addresses or guessed mappings. Strict typing passed on the three report/data modules. |
| Configuration vs convention | 3 → 3 | No production environment setting, port assumption or MIDI-channel choice was added by the correction. `RYTM_TEST_BEACON_CLIENT_STARTUP` is a new test-child switch; its Gate 13 documentation is recorded in CONTRIBUTING/LOCAL_DEV_TOOLING_NOTES. Canonical registry identity and explicit absence of evidence remain intact. |
| Test maintainability | 2 → 3 | Retained frames exercise the real capture/anchor/bridge/planner seam with shared helpers. Earlier 23 capture/286 registry passes remain scoped evidence. Fresh full Studio composition has 9,836 passes and 18 touched modules at 100% lines/branches; the separate helper runtime has 10,691 passes and four touched modules at 100%. These do not substitute for missing native gates. |
| Build / dev loop friction | 3 → 3 | Historical failed runs remain failed evidence. Fresh Studio full coverage passed in 270.32 seconds; separate runtime in 286.21 seconds. Local Cargo/rustfmt/native tests/Clippy are unavailable, and new-head hosted native verification remains pending. Clean-install performance and a baseline speed comparison remain unmeasured. |
| Error messages / provenance | 2 → 3 | The fresh saved KIT 01 projection logs 324 promoted parameters/10 omissions with no new raw-frame SHA or SRC send. The initial A4 helper's 0/1 wire failure remains failed evidence. Two later separately authorized fresh helpers each sent one CC74/channel0/value1, with user-reported physical1 and manual reload0. No hardware SAVE, native offset, automatic restoration or general A4/BOTH proof is inferred. |
| Versioning / release | 3 → 3 | Existing PR254 remains directly against `modularize-v1.34`, separate from Pi PR252. Mapping/learning is published at `2f0f5be0`; follow-up code HEAD `0130f5c5` has fresh source-specific checks but final receipt/publication/post-push confirmation and hosted/protected review remain pending. All 504 locked package versions/checksums and hardware pins remain unchanged; running server process is still `2a19b094`. No Pi or touring release is established. |
| Future-proofing | 3 → 3 | A newly registered identity is listed without a new report dispatch arm or inherited evidence. Established families bind to existing evidence in one immutable data table. New parameter support still requires canonical evidence and tests; the correction adds no parallel registry or universal support promise. |

No code-maintainability regression was found in the scoped mapping-increment
review. Native validation and final follow-up review remain explicit pending
checks. Pending hosted verification and retrospective process timing remain
explicit limitations, not positive scores to average away.

The fresh saved KIT 01 capture on runtime `2a19b094` has backend log timestamp
`2026-10-01 20:21:39,544` with no zone and fingerprint `5f75b9fb4856e8c7`.
The UI displays XT Classic TUN/SWT/DEC values `42/99/39`, `58/66/0` and
`60/83/10` on pads 6, 7 and 8 respectively. This is saved-state input/projection
evidence, not physical SRC control validation or automatic recovery. It does
not raise the maintainability scores or supply a missing raw-frame comparison.

The initial separately approved A4 channel 1 CC 74 OSC1 PWM Depth `0` to `1` attempt
selected A4 MKII 4 output but failed with
`midi_wire_unsupported_message: Message`; the helper reported **0/1 messages
sent**, and the operator observed the control still at `0`. The wire repair is
now source-checked. On **2026-10-02 at 00:40:09 UTC**, a fresh helper from
`76634665` sent exactly one CC74/channel0/value1, exited 0, and the user
reported physical `1` followed by manual source reload returning `0`.

The user explicitly requested a repeat. After fresh **NO+KIT** reload showed
`0`, another fresh helper sent the same one message at **00:42:47 UTC** and
exited 0. The user then separately confirmed physical `1` and manual **NO+KIT**
reload of saved KIT 01 showing `0`. The private JSON probe receipt is retained
locally. No hardware SAVE or new raw capture occurred during either probe.
These two authorized one-message actions support only the named non-paired
integer control and observed manual recovery in that setup. They establish no
general A4/BOTH, paired/fractional conversion, native-offset, automatic-restore
or Pi/touring authority. New source changes still need their own checks/review.

Eddie's [October 1 review](https://github.com/buzzijose-hub/RytmRandomizer/pull/254#pullrequestreview-5379158634)
acknowledges the prior Studio handoff's timing deviation only. It does not
substitute for maintainer review of this new retrospective mapping assessment
or for the actual post-merge reassessment. Gate14 stays unchecked. After merge,
update all ten rows against the merged source and its receipts; any
net-negative delta requires corrective work before declaring the plan complete.
Gate15 learning artifacts now include the five-question repository-only
onboarding exercise and its evidence-based rubric assessment, alongside the
rule/guidance, reports, architecture comparison, replay and schema. Those
learning artifacts are committed and published at `2f0f5be0`. New lesson #19
has reviewer rubric scores **4/5/4/4/4** recorded in the run report; the earlier
13-document, five-question simulation evaluated only the capture lesson and
has not been extended retrospectively. Final receipt publication, post-push
confirmation and protected plan termination remain pending. Gate 16's
historical isolation/timing exception stays unchecked. The local budget
deadline ended at `2026-10-02T01:08:16Z` with a retained budget-exceeded receipt.
The user resumed at `2026-10-02T01:13:47Z`; the current bounded interval ends
`2026-10-02T02:43:47Z`. Historical elapsed execution time remains unmeasured.

## Alias closure and integration-correction local assessment

This inspection covers source `e62bf18a` and the unknown-machine refusal
regression at `4bc21952`, against the two pre-code eighth-scope baselines.
Scores are inspection judgments, not measured contributor performance. The
first corrected full run passed 9,926 tests and exposed two uncovered existing
error-path lines. The new regression passes10 focused cases; final source
`4bc21952` passes9,927 tests with all 21 touched files at 100% lines/branches. This is a local assessment, not the required post-merge
audit or maintainer acknowledgment of historical Gate14/16 deviations.

| Required question | Before → local | Evidence and remaining work |
| --- | --- | --- |
| Onboarding curve | 3 → 3 | Inventory names alias, protected projection, display and physical-evidence boundaries; the historical exercise was not replayed. |
| Naming hygiene | 2 → 3 | All224 SRC rows round-trip;68 missing keys derive canonical machine/slot identity with old-key precedence. |
| Coupling / boundaries | 2 → 3 | Capture, mutation, planning and inventory consume one policy; planner uses the typed Cockpit data facade. |
| Magic numbers / strings | 3 → 4 | Addresses and default pad labels derive from canonical catalog facts; no replacement domain/offset table. |
| Configuration vs convention | 3 → 3 | No new production env, transport, MIDI channel or output-authority setting. |
| Test maintainability | 2 → 3 | Compatible shared fixture, bool/float refusal and immediate PREPARE/SEND assertions replace invalid identities and stalled event waits. |
| Build / dev loop friction | 2 → 3 | Failed29-case composition is retained; final full run completed in 280.92s with no worker loss; canonical touched coverage passes. |
| Error messages / provenance | 2 → 3 | Missing bindings are separated from shared protection reasons; forged proposals refuse whole plans. Optional per-row debug detail remains a review suggestion. |
| Versioning / release | 3 → 3 | Same direct-base PR254; pins/goldens unchanged. Historical2a hosted green does not certify this source or runtime deployment. |
| Future-proofing | 3 → 3 | Reversible catalog fallback and canonical pad facade avoid new family-specific maps. New rows still need eligibility evidence; Studio display remains separate. |

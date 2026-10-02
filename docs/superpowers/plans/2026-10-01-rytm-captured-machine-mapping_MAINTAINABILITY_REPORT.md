# Captured Rytm mapping current maintainability reassessment

> Status: in-flight — prototype and composed-increment assessments recorded;
> local software verified; protected review and actual post-merge reassessment pending.

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
checks, not physical captures. The coordinator's final full coverage run
(`51572`) subsequently passed 9,823 tests, with five skips and six existing
warnings in 269.56 seconds. All 18 touched production modules have 100% lines
and branches; pure branch coverage is 99.37%. Strict typing passed on all 18
modules; lint and Vulture passed. These results do not establish physical readiness.

| Required question | Baseline → composed increment | Evidence and remaining work |
| --- | --- | --- |
| Onboarding curve | 3 → 3 | The plan now names the registry writer's actual isolated checkout, eight owned files and integration dependency. Inventory and architecture links explain identities versus evidence. The contributor timing target remains unmeasured. |
| Naming hygiene | 3 → 3 | Exact owning machine sections retain the established compact keys. `registered_devices`, `evidence_family`, `evidence_row_count` and `no_support_evidence` describe report coverage without granting device readiness; the normalized count key uses lowercase casing. |
| Coupling / boundaries | 2 → 3 | The bridge consumes canonical promoted facts and exact CC matching. The report consumes public `all_devices()` plus immutable data bindings and retains existing family rows; it introduces no competing registry. The 9,823-pass final suite includes architecture checks. |
| Magic numbers / strings | 4 → 4 | XT identity derives from its canonical catalog through `Final`; source dispatch uses the established typed vocabulary. Registered identity-to-evidence bindings live in the data layer, with no duplicated MIDI addresses or guessed mappings. Strict typing passed on the three report/data modules. |
| Configuration vs convention | 3 → 3 | No environment reads, runtime settings, port assumptions or MIDI-channel choices were added. Existing registry registration remains the source of device identity; unknown report evidence is an explicit absence. |
| Test maintainability | 2 → 3 | Retained frames exercise the real capture/anchor/bridge/planner seam with shared helpers. Capture API compatibility has 23 passes; registry-focused checks have 286 passes and exercise public registration of an unsupported future identity. The report golden and final 9,823-test composition pass. |
| Build / dev loop friction | 3 → 3 | The original failed prototype run remains failed historical evidence. Final full coverage passed in 269.56 seconds with two workers; clean-install performance and a baseline speed comparison remain unmeasured. |
| Error messages / provenance | 2 → 3 | Unpromoted facts cannot expose machine SRC values; known common rows remain available. Every registered identity appears in report summaries, and absent family evidence stays `no_support_evidence` with zero rows. Mapping and precision gaps remain explicit. The mapping-only studio backend is separately installed at `2a19b094`; the registry increment remains PR254 work and fresh physical capture is pending. |
| Versioning / release | 3 → 3 | The delivery remains existing PR254 directly against `modularize-v1.34`, separate from Pi PR252. No version or hardware dependency pin changes. Local source-specific receipts passed; publication, hosted checks and protected review remain required. The separately tested local mapping runtime does not establish a Pi or touring release. |
| Future-proofing | 3 → 3 | A newly registered identity is listed without a new report dispatch arm or inherited evidence. Established families bind to existing evidence in one immutable data table. New parameter support still requires canonical evidence and tests; the correction adds no parallel registry or universal support promise. |

No code-maintainability regression was found in this scoped final-increment
review. Pending hosted verification and retrospective process timing remain
explicit limitations, not positive scores to average away.

Eddie's [October 1 review](https://github.com/buzzijose-hub/RytmRandomizer/pull/254#pullrequestreview-5379158634)
acknowledges the prior Studio handoff's timing deviation only. It does not
substitute for maintainer review of this new retrospective mapping assessment
or for the actual post-merge reassessment. Gate14 stays unchecked. After merge,
update all ten rows against the merged source and its receipts; any
net-negative delta requires corrective work before declaring the plan complete.
Gate15 learning artifacts now include the five-question repository-only
onboarding exercise and its evidence-based rubric assessment, alongside the
rule/guidance, reports, architecture comparison, replay and schema. Committed
delivery is required; protected plan termination remains pending.

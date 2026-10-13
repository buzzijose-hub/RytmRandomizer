# Native Integration Dimensional Review

Status: in-flight (source53 offline rehearsal accepted and CodeQL resolved; protected approval and physical evidence pending).

Eight targeted reviews, at most two active workers. Every review is source-only
unless a runner result below explicitly establishes software execution. None
claims physical behavior or protected approval.

| Dimension | Scope / Result |
| --- | --- |
| Architecture / import direction | No findings. Canonical owners, existing subpackages, registered capture and CLI registry reused. Reviewed e726 plus its later passive CLI delta. |
| House style / type hygiene | No findings through486501dd. Frozen typed DTOs, constants and no new Any escape. Later central error/depth/u14 changes pass strict typing and focused tests. |
| Parity / test hygiene | Important: current-generated favorites were not genuine old replay proof. Fixed with immutable actuale30 mutable/protected sessions and verified module/artifact provenance; six composed replay cases pass. |
| Side effects / hardware safety | No findings throughe726. Working responses are passive, source-kind validation protects all-locked readiness paths, no sender/provider/pin change. Later diagnostics/arithmetic reuse do not introduce output authority. |
| Observability | Important: plain ValueError lost source-kind diagnostics. Fixed by central closed WorkingKitSourceRefusalError, preserved store propagation, fixed safe message, journal/log and one bounded counter; ten composed new cases pass. |
| Abstraction reuse | Important: F1 split/join duplicated Elektron u14 helpers. Fixed by canonical encode/decode delegation after strict F1 guards; literal/order vectors pass. Reviewer delta: finding closed, no new issues. |
| Docs / diagram freshness | Important: command maps14/25 omitted new CLI; Minor: active links underHistorical. Both corrected and independently rechecked; findings closed. |
| Dispatch / env / maintainability / execution / learning | No findings through658c8f9f. No new runtime env reads; bounded resources and owned cleanup; learning captured. Historical PR254Gate14/16 exceptions remain unresolved. |

## Abstraction

Separate F1/Rytm contracts are justified by different bounds, centering, CC
semantics and evidence scope. Existing u14, input validators, Device/capture,
envelope/integrity, CLI registry, stores/atomic writes, error taxonomy and
diagnostic infrastructure are reused. Six-stage experiment DTOs are justified
new inspection shapes, not a parallel transport or persistence system.

## Docs

Native words/labels/wire loss and indexed/working identity/authority are distinct.
Both command maps show registry -> adapter -> bounded file report -> capture
capability, with no query/send/restore edge. Acquisition is future supervised
work; recovery is manual. Old package acceptance is not inherited by this build.

## Actual Repair Proof

- Frozen486 full suite:11790 passed/5skipped/6warnings811.98s, before later repairs.
- Genuine old replay/depth/working-policy/diagnostic composition:24 passed/3warnings8.78s.
- Latest boundary/taxonomy/u14/error cases:271 passed/3warnings6.22s.
- Strict pinned typing and whole lint/dead-code checks are clean on frozen658.
- Final658 full coverage passes11813 cases; Gate1 all76 touched files100%line/branch.
  Finalf670 executable/native acceptance passes; see the run report and source-bound receipt.

No unresolved Critical/Important/Minor source findings remain in the completed
reviews. A subsequent CodeQL aggregate check reports five high path-injection
alerts21-25; independent triage is complete, human disposition remains required.
Analysis-job success is not alert
clearance. No alert was dismissed. This is not an overall Ready-to-merge decision:
security disposition, historical Gate14/16 disposition and protected human approval
must be evaluated separately. Hardware precision, freshness, application/save/
reload/recovery and show readiness remain unverified.

## Subsequent CodeQL Triage

Independent read-only review inspected analysis1939595637 and alerts21-25.
Reported WS flows use configured storage roots, strict whole-string library
IDs (`[A-Za-z0-9][A-Za-z0-9_-]{0,127}`) and sound-session IDs
(`sound-[a-f0-9]{32}`) before file access. No reachable WS traversal was found;
guard-model false positives are the review assessment, not an alert dismissal.
The generic bounded reader is not a root-policy sanitizer. Local ancestor/
junction tampering is separate from these validated-ID flows and is not
certified safe by this triage.

The reviewer found a narrower direct-DTO defensive gap: `_record_path` assumed
validation and `_write_record` could perform metadata checks first. Eight red
regressions reproduced it; the valid-record control passed. The helper now
validates every caller and the writer resolves that validated path before any
I/O. The composed reader/library/WS/favorite suite passes375cases/3warnings4.33s.
Twenty-one additional malformed public-ID cases prove rejection before file
lookup. No schema, native representation, source identity or output gate changes.
Independent safety delta review closes the demonstrated gap; test/parity delta
review reports no blockers and one optional negative-input matrix gap, now
corrected with six additional cases. Final focused381cases pass4.25s. Frozen
5db6e6de full11843cases passes817.27s/all76touched100%coverage. Packaged replacement
acceptance remains required;096 stays preserved meanwhile. No suppression,
dismissal, false-green claim or protected merge is authorized by this report.

## Final Post-Push Review And Package

Eight separate scoped dimensions reviewed8d->f670, at most two workers active.
Architecture/house style/parity/safety/observability/reuse/docs/remaining gates
report no unresolved findings. Original8dMinor stale current-status wording is
corrected. Layout test review's numeric-prefix Minor is corrected to exact whole
token detection. Mutation/transport/Pythonsource remain unchanged from5db6.
No diagram edge or new architectural surface is introduced by the scoped tables.

Finalf670 native10checks pass39.745s, including600px16257/11712 one-line/contained
144pxcells. Both-device45.101s/frozen35.579s/normalUI10.014s allpasswithcleanup.
Frontend1294/allcoverage100%, sourceCI38326500759/required-checks and identified
Windowsbuild38326547294 pass. CodeQL aggregate115066896242 stillfails5highalerts;
owner/threat-model disposition, historicalG14/G16 and protected approval remain
pending. Verdict: scoped source fixes closed; NOT READY for protected merge or
hardware/show certification while those separate gates remain. No bypass.

## October13 Security And Rehearsal Closeout

Reviewed current source53a935d0 and the contained QA-only corrections in separate
dimensions, at most two agents active. Architecture, house style, tests/parity,
hardware safety, abstraction reuse, docs and remaining process/string/env gates
have no unresolved Critical/Important source findings. Observability is N/A
for this increment: pure views/list publication/recall reuse introduce no new
backend decision or send path; existing metrics and gates remain unchanged.

The two Important QA defects (packet completeness and restart without a ready
witness), stale evidence-link Important, deadline/freshness minors and UI source
publication/Preview identity defects are corrected with meaningful regressions.
The generation-aware observer requires replacement-socket status plus that
socket's mandatory bootstrap completion before readiness assertions. Initial
hydration now uses the existing30s total readiness budget, not a timeout increase.
Node25 cases and actual packaged journeys corroborate it. One cosmetic Minor
remains: full-width plan inspection adds vertical whitespace in the600px rail.
It is accepted for contained, readable packet values; no safety assertion changed.

### Abstraction

One `ExactRytmPlanInspection` consumes canonical `CockpitSendPlan` in the Safety
Rail and confirmation. Library ACKs use canonical `setLibraryRecords` after
existing success/generation fences. Preview uses existing validated candidate
recall, including disarm/plan clearing. No new planner, Device, codec, sender,
output authority, raw conversion or restore path. QA reuses the owned-process
driver and retained fixture priming; no second runtime harness.

### Docs

Current status/plan/receipt name source53, exact hashes and real acceptance.
CodeQL21-25 disposition is source/flow-specific with local-root limits; actual
source53 aggregate115103503126 and required-checks38338223170 pass. The existing
checklist remains Pad2-first, with exact channel/controls, Forge10% and manual
recovery. No new architectural boundary/registry/CLI/architecture test or
dependency rule; diagram changes are N/A for this contained increment.

### Actual Evidence And Verdict

1306frontend/81files/allfour100%/98.60s, strict76typing/lint/898architecture/
697nonfast including685parity pass. Exact53 Windows11877pass/5skip/6warnings/
1635.61s. Actual source-bound Windows build38338316064 and packaged rehearsal
24.141s/22commands/7checks, native46.195s/22commands/10checks, both-device
reference50.517s/47commands and frozenworker25.078s pass with MIDIoff/cleanup.
All earlier red/failed trials remain retained. This is scoped software acceptance,
not acoustic, live hardware, show readiness or protected merge approval.

Overall PR verdict: **With fixes** pending historical Gate14/Gate16 disposition
and protected human approval. Latest Eddie review is October3 CHANGES_REQUESTED;
no later human approval is inferred. Hardware validation/rehearsal is pending.

# Native Integration Dimensional Review

Status: in-flight (scoped source repairs and offline package accepted; new security triage and protected approval pending).

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
  Exact096 executable/native acceptance passes; see the run report and source-bound receipt.

No unresolved Critical/Important/Minor source findings remain in the completed
reviews. A subsequent CodeQL aggregate check reports five high path-injection
alerts21-25 requiring independent triage; analysis-job success is not alert
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

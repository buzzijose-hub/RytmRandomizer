# Reference-sound reliability update

> Status: in-flight (PR #254; software verification and physical evidence pending).

Per docs/PLAN_REQUIREMENTS.md, this focused update extends PR #254 against
`modularize-v1.34`; it does not create a stacked PR or grant output authority.

## Motivation And Baseline

The October 12 retained exercise reproduced an A4 Noise Fade signed-domain
mismatch, an eleven-feature metric that omits direct pitch, and an extremely
quiet multi-note audition. Baseline receipt is `b9f89c3e`, production delivery
`53a935d08582`. Preserve that delivery, originals, KITs, session identities,
user-owned processes, hardware pins, frozen parity and all sending restrictions.
Fresh GitHub inspection finds no renewed human approval. CodeQL disposition is
unchanged. Tonight's existing four-control Pad 2 procedure remains available.

## Scope And Architecture

Reuse canonical A4 inference/native contracts, the isolated analysis worker,
source-preserving candidate compiler, atomic artifact store and reference UI.
Keep measured pitch/quality diagnostics separate from the unchanged eleven-
feature score and from any physical evidence. Use existing proven DSP libraries.
No automatic note/tuning changes, normalization, silent cropping or MIDI access.
Optional diagnostic metadata must preserve legacy records and exact identities.
Unreliable or unmeasured feedback cannot authorize a new refinement.

## Workstreams

| Workstream | Owner/Checkout | Files | Dependency |
| --- | --- | --- | --- |
| Signed-domain repair | isolated `reference-noise-domain-oct14` | inference facts and focused tests | independent |
| DSP diagnostics | isolated `reference-audio-diagnostics-oct14` | style analysis, worker and focused tests | independent |
| Workflow integration | assembly `rytm-studio-mapping` | session/records/wire, UI, handoff and packaged QA | consumes both |
| Community catalog facts | isolated `midi-catalog-facts-oct14` | canonical descriptive metadata, consumers and tests | after audio workers finish |
| Complete reconciliation ledger | isolated `midi-reconciliation-ledger-oct14` | passive report/script, licensed inputs, all-row ledger and tests | canonical inventory plus facts |

At most two implementation workers; one heavy test/build job and one browser
worker. Use two pytest workers where supported. Workers do not push independently.

## Abstraction Reuse

No new device abstraction or renderer is needed. Diagnostics are device-neutral
measurements, not a synthesis model. Existing worker owns cancellation/timeouts
and dependency isolation; existing records/store own validation/publication.
Known offsets, locks and native precision stay owned by Device strategies.
Shared lazy DSP protocols live in `style_analysis/runtime_types.py`, reused by
the extractor, worker and diagnostics instead of duplicating interfaces.

## MIDI Guide Reconciliation

The October 14 addition uses all 230 A4 and 322 Rytm CSV rows, superseding only
the earlier comparison audit, never independently supported device knowledge.
Original SHA-256 and exact upstream Git blob identities are pinned. Retain
Pencil Research/MIDI Guide attribution and CC-BY-SA-4.0 for supplied/adapted data.
Match addresses in machine/track context, preserving blanks as missing values.
The ledger separates MIDI ranges, display units, saved-native domains, conflicting
labels, protection, software scope and target-unit evidence. Added descriptions
do not grant native authoring, SEND, selector validation or recovery. FX/CV,
sequencing, routing and OXI-owned controls stay protected. All CY Ride SRC,
unverified paired precision, general A4/BOTH and automatic restore remain held.

## Verification

- Reproduce real-input Noise Fade failure and prove signed-domain boundaries.
- Synthetic clean tones, octave/harmonic cases, noise, quiet/clipping, multiple
  notes, exact segments, corrupt metadata and missing diagnostics.
- Refusal/cancellation leaves source, session, favorites and artifacts unchanged.
- Exact segment and original identities survive restart; legacy replay remains
  truthful without granting new diagnostic or hardware evidence.
- UI displays actual analyzed samples, qualified pitch/quality and refusal.
- Packaged import, generate, compare, refine, favorite and reopen for both devices.
- Required architecture, frozen parity, lint, typing, full tests and touched-file
  branch coverage; one targeted review agent per applicable dimension.
- Every supplied CSV row, contextual address reuse, missing cells, conflicting
  machine/selector labels, enum bounds, licensing and unchanged output gates.

## Gates

All eighteen canonical gates remain tracked in the existing PR conformance
checklist. This update must satisfy Gates 1-13, 17-18 before publication; Gate 14
includes dimensional review and the protected human reassessment, Gate 15 captures
the domain/diagnostic lessons, and Gate 16 uses the isolated workstreams above.
Human approval and physical rehearsal remain explicitly pending, not waived.

- [x] Gate 1 - 100% touched branch coverage; project coverage ratchet unchanged.
- [x] Gate 2 - All 685 frozen parity items unchanged.
- [x] Gate 3 - Lint, formatting and strict touched-production typing.
- [x] Gate 4 - No new dead code.
- [x] Gate 5 - Operator/repository records distinguish accepted fallback and pending delivery.
- [x] Gate 6 - Typed immutable DTOs, no escape hatches or hardware side effects.
- [x] Gate 7 - Canonical traces, categorical refusals and metrics.
- [x] Gate 8 - Meaningful isolated regression tests.
- [x] Gate 9 - Existing subpackages and dependency directions.
- [x] Gate 10 - Canonical dispatch/domain identities.
- [x] Gate 11 - Shared fake fixtures in canonical conftest.
- [x] Gate 12 - Immutable Final constants.
- [x] Gate 13 - Existing safe environment controls, no new production variables.
- [ ] Gate 14 - Dimensional review and protected human historical reassessment.
- [x] Gate 15 - Durable domain/quality/replay lessons.
- [ ] Gate 16 - Two isolated workstreams, one bundled PR; historical deviations pending.
- [x] Gate 17 - Reuse worker, codec, store, converters and DSP libraries.
- [x] Gate 18 - Architecture map and relevant diagram reflect diagnostics and ledger.

## Execution And Accounting

Start: 2026-10-14 15:45 UTC (11:45 a.m. America/New_York). Session ceiling: eight
productive hours, finish sooner on software acceptance. Studio arrival expected
9 p.m. October 14 America/New_York; no scheduled hardware action. Checkpoint:
`output/local/OCT14-REFERENCE-RELIABILITY-RESUME.md`. Retain commands, timings,
hashes, review/CI state and exact failures there and in the delivery receipt.

## Recovery And Stop Signals

Use clean isolated commits integrated into the assembly branch. Never reset
user changes. STOP cancels only owned jobs, writes an interruption checkpoint
and leaves retained data unchanged. Resume from that checkpoint, not assumptions.
No force push, protected merge, gate bypass, dependency-pin change or hardware I/O.

## Rollback

The prior verified delivery remains launchable with separate data. Revert only
this update's commits through the normal review process; do not overwrite newer
user session data. Legacy optional metadata remains readable.

## Done Criteria

Evidence-backed fixes, complete regression gates and a new exact-source Windows
build exercised through its real UI/runtime, with a concise tonight handoff.
Software verification is not physical sound matching, hardware save/recovery
validation, full feature completion or show readiness.

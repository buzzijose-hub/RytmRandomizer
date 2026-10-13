# Native Representation Integration

> Status: in-flight (tested offlinef670 delivery; security disposition, hardware and protected approval pending).

## Mission And Baseline

Start 2026-10-12T20:01:07Z (4:01 PM America/New_York). Working-block ceiling
2026-10-13T04:01:07Z; eight hours is a budget, not completion. Assembly branch
`codex/studio-rytm-mapping`, PR254 direct base `modularize-v1.34`, head `e30cc84c`.
CI is green at kickoff; latest human review remains CHANGES_REQUESTED.
Preserve dirty primary checkout, original research/captures and delivered64d5
audio-enabled Windows package. No actual MIDI/USB enumeration, opening, arming,
queries, writes or firmware execution during this block.

Research: `ElektronNativeResearch/2026-09-28-integrated/a4_companion`.
Read REPORT, handoff, typed references, literal vectors, structured contracts and
independent reviews before porting. Original firmware identities are provenance,
not installed-device assertions; no proprietary firmware/disassembly is published.

## Reconciliation Before Code

| Finding | Current Truth / Actual Gap |
| --- | --- |
| A4 header/packing/body | Already9unframed bytes, MSB-first,2410decoded bytes; no repeat repair. |
| F1 offsets | Existing packed-address translation resolves Sound+0x60, KIT+128+350*track; retain coordinates and identities. |
| F1 exact values | Exact native bytes retained; generic mathematical Q8.8 text is not the two-decimal device label. Add F1-specific representation and collision/loss vectors. |
| F1 input/order | No scoped exact CC-preservation/saturation and NRPN-intermediate model; pure helpers only, no event-schema/sender promotion. |
| Working response | Current codec accepts52only and does not validate all supported semantic structures/versions. Extend passive52/58 classification and fail-closed semantic validation. |
| Rytm LFO numeric scale | Existing centered0x4000/128 arithmetic matches; signed screen labels, odd loss, coarse reset/fine merge and partial notifier scope need separate contracts. |
| Source provenance | Raw frame IDs must stay stable; same-body52/58 must remain distinguishable without calling working RAM fresh/atomic. |
| Retention | Audit exact candidate/source identity and old-algorithm replay before modifying sampling bounds or derived labels. |

## Pre-Code Maintainability Audit

| Dimension | Baseline / Planned Constraint |
| --- | --- |
| Onboarding | Existing Device/codec/native-field/capture owners are named; add one integration map and precise bench checklist. |
| Naming | Device-specific F1/LFO contracts; do not call mathematical values screen labels or working responses complete unsaved snapshots. |
| Coupling | Data owns fixed facts; public strategy helpers own conversions; capture and stores consume optional Device capabilities. |
| Magic values | Port literal vectors and evidence hashes; reuse existing addresses/coordinates, no stale offsets or neighbor inference. |
| Configuration | No new hardware switch or automatic query; existing explicit output boundary remains unchanged. |
| Tests | Shared retained frames; independent semantic assertions and failure/migration/source-kind tests, not roundtrip-only proof. |
| Build loop | One heavy local job, two pytest workers, one browser; workers have disjoint ownership and coordinate test slots. |
| Errors | Invalid versions/structures/domains are categorical and preserve committed sources/favorites. |
| Versioning | Raw/decoded coordinate identities unchanged unless coordinates actually change; algorithm/persistence changes need explicit compatibility. |
| Extension | Add another evidenced parameter-specific contract through canonical facts/helpers, not a global fixed-point convention. |

## Workstreams And Ownership

| WS | Ownership | Dependencies |
| --- | --- | --- |
| A4 F1 | Isolated managed worktree; new A4 F1 facts/helper, literal tests only. No shared facade, native fields, codec, stores, UI or sender edits. | Baseline |
| Rytm LFO | Isolated managed worktree; separate Rytm facts/helper, literal tests only. No shared facade, native fields, frame codec, stores, UI or sender edits. | Baseline |
| Main integration | Assembly; semantic52/58 reader/classification, existing native/control/capture/persistence consumers, canonical facades and operator UI labels. | Explicit helper contracts |
| Verification/delivery | Assembly; gates, targeted dimensional review, exact-source Windows package and actual affected journeys with MIDI off. | Integrated source |

At most two independent workers. Each follows planner/TDD/implementation/coverage/
review phases. One coherent existing PR, no stack or protected merge. Baseline
architecture gate runs before code; fixture and pin changes are prohibited.

## Acceptance And Safety

Port literal boundary/collision/order vectors unchanged. Test all four A4 F1
coordinates, protocol1/1, KITversion11, Soundversion6/magic/trailer, exact extents,
checksum/length/padding, invalid/unavailable source structures and52/58 separation.
Preserve exact originals and raw IDs. Software/static evidence does not promote
`validated_runtime`, output precision, current-state freshness or restore.

Audit import, inspection, reference generation/readback/comparison, local favorites,
native export/import and disarmed recall. A screen-label collision never merges
native candidates. Existing seven-bit event schemas and refusal gates remain.
Do not generalize F1 rules to F2 or Rytm; do not borrow A4 NRPN-row behavior for
the unproved Rytm parser. Sampling/replay and derived-label compatibility must be
demonstrated, not assumed. Validate partial observations as partial.

Run focused semantic regressions, full suite/coverage, all architecture/frozen
parity, pinned typing, lint and dead code. Require100% touched production coverage.
Review one dimension per agent in bounded batches and post a consolidated verdict.
Build a new source-bound Windows package, record hashes/launcher, and exercise
affected native UI/runtime journeys without a developer environment or hardware.

## Physical Follow-Up And Rollback

Prepare only the authorized-future quiescent saved-versus-unsaved experiment:
backups/disposableKIT, actual firmware/ports/channels, indexed baselineB, unsaved
panelchangeU, repeated working replies, explicit manual save/indexed comparison,
manual reload/full baseline recovery. Use forward labels, not guessed inverse
words. Retain all unknown differences. No request is sent while Jose is absent.
No pending-edit/atomicity/automatic synchronization or show-ready claim follows
from a static contract or synthetic frame. Software rollback uses prior verified
delivery; never rewrite raw captures, prior fixtures or operator settings.

## Gate Accounting

G1coverage/G2parity/G3lint-type/G4deadcode/G5docs/G6types/G7telemetry/G8tests/
G9architecture/G10dispatch/G11fixtures/G12constants/G13configuration/G14audit/
G15learning/G16single-PR-isolated-work/G17reuse/G18diagrams all have owners above.
Historical PR254 G14/G16 deviations are not retroactively certified. Protected
human approval and physical experiments remain separate requirements.

# A4 Studio Audition Integration

Status: implemented locally; final composed verification/review in progress.
This is an unqualified studio RAM-only experiment, not general A4/BOTH show
readiness, persistent KIT write support or a replacement installer.

## Implementation

- Integrates the prior f7186481 mapping/compatibility bundle as one source line.
- Adds exact current-session routing and a distinct canonical studio plan for
  the 25 reversible native/CC7 bindings. Unknown, protected, paired or disputed
  changed rows refuse the whole executable plan rather than a partial subset.
- Revalidates retained manifests, source/candidate bytes, active cue/revision,
  local provenance, current target/lock/parameter scope and fresh matching input
  capture at preparation and SEND. Exact configured channels and output name
  are bound into the plan ID; no default channels or imported output grants.
- Requires explicit unqualified-studio acknowledgment, manual saved-source
  reload and exact per-action plan confirmation. Rytm plans cannot use an
  A4-armed port. A4-labelled OS route filtering refuses known Rytm/generic
  routes but cannot authenticate physical device identity or cable routing.
- Uses one shared ArmedApply gate/render/send loop. The cooperative async
  driver and owned reader task keep DISARM/watchdog/disconnect reachable
  between packets. A session reservation refuses concurrent mutation.
- Consumes preparation and advances reload evidence before sending. Complete,
  partial and interrupted counts remain in the bounded session journal and UI;
  revoked hardware-readiness labels are published. No automatic retries or
  restore, and no change to persistent-write refusal or general stage holds.

## Verification

The first composed checkpoint found two test-fixture assumptions: the selected
two fields produced only one changed packet, so that fixture could not model a
failure after the first of multiple messages. The fixture now selects a known
multi-message envelope scope without relaxing production guards.

Early hardware review identified blocking pacing, discarded cancellation counts,
stale readiness events and self-declared device routing. The implementation now
uses cooperative delivery with per-message authority checks, retained interruption
outcomes and explicit readiness publication. The supported route is constrained
to an A4-labelled output and a supervised direct-USB procedure; labels still do
not prove physical identity, and that remains an external acceptance boundary.

The frontend Python fixture initially retained a random source snapshot identity.
The producer drift guard now fixes only that identity input and compares the
entire canonical serialized plan. Native rendering, byte checks and replay are
not stubbed. Focused composed tests, including the actual WS reader DISARM
journey, pass 732 cases at the current checkpoint. Final full-suite, coverage,
browser and dimensional review results are pending and must not be inferred
from worker-only results.

## Studio Handoff

Use the [supervised scratch procedure](hardware-validation/2026-10-15-a4-studio-audition.md)
only with a separately packaged and verified exact-source build. All physical
observations remain NOT PERFORMED. Preserve the installed d563 rehearsal delivery,
immutable source kits, original WAVs and hardware backups. Start with one track
and one small envelope control, then DISARM/manual reload/listening/fresh capture.
Local favorites are not hardware saves. No live-show qualification is claimed.

## Integration And Maintainability

The existing PR254 remains the single integration/review vehicle; no stacked PR
or protected merge is authorized by these tests. Sender pacing, pure planning
and frontend workers use disjoint worktrees and are archived after integration.
The source reuses canonical native conversion, preparation validators, packets,
exact output opening and ArmedApply. No environment switch, new device registry,
root module, hardware dependency update or parity regeneration is introduced.
The post-audit and exact final test/review/source checkpoint will be recorded
before publication.

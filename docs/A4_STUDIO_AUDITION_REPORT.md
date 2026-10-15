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
### Maintainability Post-Audit

| Pre-audit item | Post-audit disposition |
| --- | --- |
| 1. Onboarding | Existing workspace/WS/protocol boundaries retained; source-only procedure linked from quickstart. |
| 2. Naming | Explicit studio-only plan/control/outcome types; general stage remains blocked. |
| 3. Coupling | Removed forbidden WS timing import; neutral fact is exposed through the cockpit data boundary, without architecture allowlist growth. |
| 4. Facts | Canonical 25-binding map and unchanged 20 ms interval reused; no copied conversion or CC table. |
| 5. Configuration | Explicit volatile routing and confirmations; no new environment read or persisted grant. |
| 6. Tests | Shared pacing fixture moved to conftest; real canonical producer fixture and actual WS stop/disconnect/overlap regressions added. |
| 7. Dev loop | At most two test workers; composed source checkpoint and runner results recorded, not inferred from worker reports. |
| 8. Errors | Repaired artifact redaction and refusal RED accounting; categorical reasons and accepted-packet counts survive interruption. |
| 9. Release | Existing PR254 only; preserved d563 delivery, no protected merge or physical acceptance claimed. |
| 10. Extension | Async/sync delivery share one gate loop; unsupported changed fields block the whole plan. No additional sender abstraction warranted. |

The first dimensional review found and repaired import ownership, loose receipt
typing, diagnostic redaction/accounting, missing reverse-family regression and
an owned-operation overlap that could delay DISARM. Follow-up targeted reviews
clear those repairs; a missing future-annotations directive in the new neutral
data module was also corrected. Docs reconcile old categorical A4 holds with
the separate studio exception. Historic PR254 Gate14/16 deviations are not
retroactively cleared by this increment's audit/execution record.

Final full-source test/coverage and remote publication results remain pending.

The first full coverage attempt was stopped and is not acceptance evidence.
An architecture-only retry identified relocated broad catches; the repair uses
explicit backend/control-flow failure families and finally-based port cleanup,
with new unknown-collaborator fault tests for both drivers. Two obsolete
line-numbered ArmedApply broad-catch exemptions were removed, not expanded.
The focused 805-test coverage diagnostic passed its tests but intentionally
failed the whole-package 99% floor because it did not run the whole suite; its
XML is diagnostic only. Final package coverage comes from a fresh full run.

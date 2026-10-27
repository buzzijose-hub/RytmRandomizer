# A4 Studio Audition Integration

Status: October 26 cancellation software repair verified on PR254. The e420c30e
review's two combinations are now reproduced and repaired: internally cancelled
dispatch publishes its failure ACK and safety revocations, and recognized
port-close faults no longer replace the original control signal. The actual
authenticated WebSocket test checks one accepted packet, subsequent stale-plan
refusal, exact accounting and disconnect/reconnect races. The existing explicit
failure families remain unchanged; unmodeled collaborator cleanup errors remain
outside the preservation guarantee, with passive state and progress retained.
See the [repair plan](superpowers/plans/2026-10-26-companion-cancellation.md).

## October 26 Verified Source

Frozen production/test source: `bee04ddbaa7ae25f9f49c49bd258b6edb384effd`.
Full run started 2026-10-27 01:33 UTC; 13,575 passed, six skipped, six warnings,
zero failures in 1159.86 seconds, using two workers. Fresh log/JUnit and XML:
ignored `output/local/companion-full-pytest.{log,xml}` and
`output/local/companion-full.coverage.xml`. All 99 PR-touched production modules
reach 100% lines/branches; pure branch 99.44%, unchanged 99% floor. All 921
architecture cases and 685 frozen V1.34 cases pass. The prior composed gate
passed 1702 tests in 91.36s. No frozen fixtures or hardware pins changed.

Pyright1.1.411 checks all 99 modules without diagnostics. Pinned Ruff0.15.13,
Black26.3.1 py311, isort8.0.1, Vulture80 and version checks pass. Independent
unchanged-lockfile web installation passes 1412 tests / 82 files at 100% all
four coverage measures (111.05s), TypeScript, ESLint and Vite8.0.16 build.
Four Chromium journeys pass in 12.8s: actual-backend scoped favorite/restart,
fake-port confirmed SEND, whole-plan paired refusal, and separately labeled
mocked A4 routing/confirmation at desktop/mobile sizes. None is hardware proof.

Publication/review and exact-source binary acceptance have separate receipts:
the current PR254 review/checks and source-identified delivery's
`studio-procedure/DELIVERY-RECEIPT.md`. Do not infer those outcomes from local
tests. The d563 fallback's shell/sidecar/launcher hashes remain unchanged.
Historical Gate14/16 exceptions and protected human approval are not cleared.
This is an unqualified studio RAM-only experiment, not general A4/BOTH show
readiness, persistent KIT write support or a replacement installer.

## Execution Ledger

The October 15 entries below are historical source evidence, not acceptance of
the October 26 changes. All physical observations remain NOT PERFORMED.

Checkpoint 2026-10-15 23:07 UTC. Frozen production/test source:
`b995d0015032cfb78195a8220c6ce7125d95db94`.
Only reporting/docs change after this tested production checkpoint.

Post-push observability review reproduced three faults: omitted shared sender
failure families lost receipts, propagated exceptions lost readiness events,
and cleanup errors could mask accepted-message counts. The repair latches
immutable action/device-bound progress immediately after each accepted message,
collects ordinary delivery failures through an owned task, preserves control-flow
propagation, and journals/publishes terminal state in finally-based cleanup.
The scoped diagnostic passes 680 tests with both affected modules at 100% lines
and branches. The complete architecture gate passes 921 items in 78.89 seconds;
strict typing on 99 modules, Ruff, Black, isort, Vulture80 and version checks pass.
Repair source `b995d001` passes the fresh full coverage run below with two workers.
Independent targeted follow-up review clears all three observability findings
and both documentation findings. Historical Gate14/16 exceptions are unchanged.

Historical published source `63251060` retained production `fa84d7bf` and final
test checkpoint `5032413d`: 13,478 passed / 6 skipped / 6 warnings in 1119.94s.
Its log/JUnit and XML are archived under ignored
`output/local/a4-63251060-pytest.*` and `output/local/a4-63251060.coverage.xml`.
They are not the acceptance evidence for the b995 repair.

At published source 63251060, the [PR-event native updater job](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/38817231609/job/116704939417)
failed one `backend_restart` case (31 passed), while its [push-event duplicate](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/38817224801/job/116704924197)
passed all 32 native cases and both Windows handoffs. The tested trees were identical.
The failure was the bootstrap/report catch; retained diagnostics do not expose
the initiating rejection or prove that the restart action ran. The sidecar's
FastAPI import interruption was caused by report-time shutdown, not evidence
that cold import initiated the failure. No timeout, dependency or retry policy
was changed. Keep the failed PR receipt distinct from the successful duplicate;
current-source CI is still a separate publication gate.

| Gate | Observed State |
| --- | --- |
| Full Python/coverage | 13,500 passed, 6 skipped, 6 warnings, zero failures in 1120.43 seconds; two workers. Fresh log/JUnit: ignored `output/local/a4-full-pytest.*`; coverage: `coverage.xml`. |
| Architecture/parity | 921 architecture items and all 685 frozen V1.34 parity items pass in the full suite. Separate repair architecture gate: 921 passed, one known warning, 78.89 seconds. |
| Strict production typing | All 99 PR-touched modules pass with zero diagnostics. |
| Coverage | Canonical touched-file gate proves all 99 PR-touched modules at 100% lines/branches; whole-project pure branch 99.44%, unchanged 99% floor. Fresh final XML only; no earlier or cancelled-run data used. |
| Frontend | 1,412 tests / 82 files pass in 104.69 seconds; statements/branches/functions/lines all 100%. |
| Browser | Two Edge journeys pass in 4.7 seconds, including exact A4 routing/confirmation at 1440/600/390 pixels and preserved offline review. Screenshots inspected; mocked WS only. |
| Lint/build | Ruff, Black py311, isort, ESLint, TypeScript, Vulture80 and version drift check pass. Vite build passes with existing chunk/dynamic-import warnings. |
| Review | Earlier eight-dimension review identified repairs; independent focused fix reviews are clear. Current publication review is tracked on PR254. Protected human approval remains separate. |
| Integration | Existing PR254 only; remote CI and current publication/review state are tracked on that PR. No protected merge, new package or physical I/O is claimed. Four implementation worker worktrees archived after merge. |

A 21:53 UTC resource spot-check showed approximately 15.38 GB free of 31.75 GB
physical RAM and 19% aggregate CPU use. This is a point-in-time observation,
not a continuous resource or hardware-performance guarantee.

The final verification/publication phase has a 90-minute cap. Stop without a
push on unresolved failures, interruption or remote divergence; preserve source
and this ledger. Historical PR254 Gate14/16 deviations remain unresolved.

The contract repair includes exact native-command set equality, explicit two-
command identifiers and a positive real-WebSocket prepare/deliver journey tied
to the protocol round-trip guard. It does not only raise a count or change any
production behavior. Native rendering, fake-port packets and consumed authority
are asserted through both new wire commands.

The preceding complete coverage run failed: 13,474 passed, 3 failed, 6 skipped,
6 warnings in 1116.73 seconds. All three failures were stale 64-command assertions
after the new surface made 66. Its log/JUnit/coverage are retained under ignored
`output/local/a4-fa84-contract-failed.*`, not used as final acceptance. The
contract/positive-WebSocket repair passed 151 focused cases before the fresh
full run above; no production behavior changed for that repair.

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
- Uses one shared ArmedApply gate/render/send loop. Immutable accepted-message
  progress survives teardown and masked exceptions; it is evidence, not output
  authority. The cooperative async
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
not stubbed. An earlier focused composed checkpoint passed 732 cases, including
the actual WS reader DISARM journey. It is superseded by the fresh full-suite,
coverage, browser and review results above, not treated as composed acceptance
on its own.

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
| 7. Dev loop | Full acceptance runs use two workers; composed checkpoints and runner results are recorded, not inferred from worker reports. One short focused/architecture diagnostic overlap exceeded the intended aggregate two-worker cap; subsequent gates run serially. |
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

Final full-source test/coverage results are recorded above. Current remote CI
and protected review/publication state belong to PR254, not a hardware receipt.

The first full coverage attempt was stopped and is not acceptance evidence.
An architecture-only retry identified relocated broad catches; the repair uses
explicit backend/control-flow failure families and finally-based port cleanup,
with new unknown-collaborator fault tests for both drivers. Two obsolete
line-numbered ArmedApply broad-catch exemptions were removed, not expanded.
The focused 805-test coverage diagnostic passed its tests but intentionally
failed the whole-package 99% floor because it did not run the whole suite; its
XML is diagnostic only. Final package coverage comes from a fresh full run.

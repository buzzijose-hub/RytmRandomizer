# Pi appliance run log

Append-only from formalization on 2026-09-30. Entries below reconstruct the
already-recorded order from Git and the [execution ledger](superpowers/plans/2026-09-30-pi-performance-appliance_STATE.json).
They are not fabricated contemporaneous timestamps. Future entries must append
their observed checkpoint and result; do not rewrite earlier failures as passes.

| Recorded checkpoint | Event and evidence |
| --- | --- |
| `892aaffc` | Started from the fetched integration target; preserved original checkout `a73aded6`. Assigned disjoint touch/runtime/capability worktrees and one heavy-job queue. |
| `59a4bb7b` | Integrated the shared touch route, catalog evidence and loopback kiosk runtime. Focused workstream results were retained as workstream evidence. |
| `a136cd21`, `a925cc45`, `ce81bd4b` | Sealed simulation arm authority, bound the launcher to colocated source and integrated exact captured A4 native values. |
| `c32f6207`, `09b1fe6e` | Kept input capture cancellable, invalidated late capture results and added safe runtime observability. |
| `3d0b3c92` | First combined backend run: 10,502 passed, 40 failed, five skipped. Failures exposed canonical-data drift, wire inventory mismatch, frozen evidence hash/dependency direction and refusal/coverage gaps. |
| `a0db2724`, `3028ea30`, `2e4b32ef`, `c4dbee6a` | Restored frozen source identity, reviewed the narrow canonical target-data edge, repaired data fixtures and cancellation races, and verified the complete wire contract. Architecture: 873 passed. |
| `3f1c2ba1` | Combined backend: 10,608 passed, five skipped; 23 touched modules at 100% coverage. Browser regression: 33 passed, two existing skips. Pixel review still found clipped compact-modal actions. |
| `99a0e419`, `abf0ea61` | Pinned modal header/footer with a scrolling body and strengthened real-browser assertions. Frontend: 1,075 passed at 100%; 80 visual checks and independent corrected-dialog inspection passed. |
| `a685df2d` | Runtime review repaired fresh-wheelhouse certification, exact retained inventory, standalone bytecode refusal, UTF-8 metadata and prior-release service-template rollback. Lifecycle: 90 focused cases passed. |
| `8dd16377`, `34fa5ae0` | Backend checkpoint: 10,620 passed, five existing skips. Updated frontend and browser receipts passed at `34fa5ae0`; wrapper cp1252 printing failed after the exit-zero browser subprocess. |
| `226aa0f0`, `8067387e` | Final type/reuse review repaired fixed-shape records, reused the shared object validator and public A4 sound iterator. Focused checks passed; final backend acceptance required a rerun. |
| `97fd6216` | Final backend rerun launched. Independent Gates 14/15 review identified missing formal committed artifacts; this documentation repair reconstructs the baseline honestly and adds durable records, schema and replay guidance. |

At formalization, publication and final source-bound acceptance were pending.
Physical Pi/ARM64 and live hardware gaps remain as listed in the
[run report](PI_APPLIANCE_RUN_REPORT.md). No successful physical test is inferred.

## 2026-09-30 — backend checkpoint completed during docs repair

At `97fd6216`, the full backend rerun completed with 10,620 passed, five existing
skips and eight warnings in 194.80 seconds pytest / 200.593 seconds wall. All 23
touched package modules had 100% line/branch coverage; whole-package pure branch
coverage was 12,642/12,720. Whole-repository lint, strict typing and touched-module
Vulture checks passed. The final documentation-only release SHA and its generated
artifact identity were still pending. This entry appends the new outcome without
changing the earlier launch/pending record.

## 2026-09-30 — hosted CI incident and local isolation repair

After [PR #252](https://github.com/buzzijose-hub/RytmRandomizer/pull/252) opened,
Python CI at `13b00003` failed the same auth-refusal logging test on Linux,
macOS and Windows: capture contained 14 records where exactly seven were
required. The Windows job reported 10,619 passed and five skipped alongside
that failure. Inherited logger propagation duplicated the capture; a stale
closed ancestor-handler stream also exposed dependence on earlier test order.

The runtime agent reproduced the failure before repair with both ambient
package propagation settings. Test-only commit `e36979a93a925c1886138593b3d7ef364137a330`
uses monkeypatch-restored handlers and disables propagation on the logger under
test. It preserves the exact seven-record, privacy, metric and zero-MIDI
assertions and adds exact refusal-category and clean-stderr assertions. Local
verification reported 19 runtime cases and 48 ordered neighboring cases passed,
with lint clean. No production behavior or coverage threshold was changed.

Hosted CI for the replacement head has not passed yet. A separate desktop-shell
job at `13b00003` reported 31 passed and one failed (`backend_restart`); that
failure remains under investigation. The logging repair is not a claim that all
CI failures are resolved. Earlier `13b00003` software receipts remain historical
checkpoints; the test tree changed in `e36979a9` and must be identified separately
in subsequent verification.

## 2026-09-30 — native readiness diagnosis and integrated backend checkpoint

The capability agent traced the separate `backend_restart` failure to an
existing harness readiness race. `native_update_driver.ts` is unchanged from
baseline `892aaffc`: it waits for rotated credential files, then immediately
probes with the stale token. Python writes those files before uvicorn starts
listening, so the probe can race socket readiness and fail for startup timing.
This evidence does not establish a production regression.

The baseline CI job `109149261285` passed 32 native cases and two installer
cases. At the same appliance source `13b00003`, PR job `109992075623` also
passed 32 plus two, while push job `109991619778` reported 31 native cases
passed and one failed. The differing outcomes and unchanged harness support
the pre-existing race diagnosis. No retry, assertion relaxation or harness
change is claimed as a repair; replacement CI remains pending.

The new integrated backend checkpoint
`5f911385f58fb0453813484df9678ef3797c14a2` passed 10,621 tests with five existing
skips and eight warnings, using four workers: 192.92 seconds pytest and 195.094
seconds wall. This result includes the auth-log isolation regression cases.
These software and desktop CI observations grant no physical Pi, native ARM64
or live-hardware acceptance.

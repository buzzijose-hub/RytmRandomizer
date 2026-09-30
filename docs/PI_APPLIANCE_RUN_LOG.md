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

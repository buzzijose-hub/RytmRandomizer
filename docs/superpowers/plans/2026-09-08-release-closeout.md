# September 8 release closeout

> Status: in-flight — resumed September 21; local and hosted checks passed; owner exceptions/protected review pending

Jose authorized review, repair, pushes, review requests, and normal protected merges of PRs #238–243. Upcoming Rytm/A4 shows take priority. This plan consolidates #239/#241/#242/#243 into one updater PR against `modularize-v1.34`, preserving original commit authorship. Forge (#238) and passive Digitakt support (#240) remain separate changes. No production release is part of this run.

## Ownership and execution

| Workstream | Worktree | Ownership | Dependency |
| --- | --- | --- | --- |
| Forge review/handoff | `../release-closeout-forge` | Forge repairs and studio receipt | Independent |
| Updater bundle | `../autoupdate-complete-bundle` | Shell/frontend updater, release scripts, update docs/tests | Independent |
| Digitakt review | `../release-closeout-digitakt` | Device facts/strategies and tests | Independent |
| Combined validation | Separate integration checkout after repairs | Merge resolution and combined verification | All source repairs |

Root owns builds/tests and shared integration files. At most two implementation agents operate concurrently. Eight scoped review dimensions run in waves of at most three available reviewers; reviewers launch no heavy jobs. File ownership is assigned before edits. Only one heavy job runs across all worktrees: pytest `-n 2`, Cargo jobs 2, frontend workers 2, Playwright workers 1. Check memory before each heavy job and defer below approximately 8 GB free. Reuse environments/caches. Never stop another task's processes.

## Required outcomes

1. Reconcile every current maintainer finding against the reviewed SHA. Reproduce actionable defects; retain valid refusal behavior.
2. Complete startup/periodic update checks, panel command wiring, signed staged-byte validation, consent/install/quit lifecycle, reconnect authentication, and accurate status/privacy reporting. Replace placeholders with executable boundary tests where possible.
3. Verify Digitakt facts against official manuals; keep unsupported mutation/output unavailable.
4. Verify the actual Forge studio package and bundled backend with physical MIDI disabled. Rebuild only when binary inputs change.
5. Run lint, typing, architecture, frozen parity, meaningful coverage, frontend/browser, Rust, and packaging checks; then validate the combined application.
6. Publish honest review verdicts and request Eddie's review. Merge only when GitHub's required checks, code-owner approval, and conversation resolution are satisfied. Never replace human approval with an agent verdict.

## State, recovery, and limits

Durable tracked checkpoint: [state](2026-09-08-release-closeout_STATE.json),
[schema](2026-09-08-release-closeout_STATE.schema.json),
[log](2026-09-08-release-closeout_RUN_LOG.md) and
[run report](2026-09-08-release-closeout_RUN_REPORT.md). Detailed machine-local
command receipts remain in sibling `release-closeout-evidence`; their conclusions
and limits are preserved in these tracked files. On recovery, re-query GitHub
before selecting the next action. The dirty original checkout is preserved;
remote heads may move and must be reconciled without overwriting author commits.
Existing updater PRs close only after a verified replacement exists.

Start was the user's September 8 request; its original same-day/24-hour target
was not met. The user explicitly resumed work September 13 and September 21. Current termination
criteria are the concrete software/PR/handoff outcomes below, with unresolved
external approval and physical evidence identified precisely. A STOP message
interrupts execution and records the checkpoint. Preserve hardware pins and all
V1.34 fixtures. Do not open real MIDI, fabricate observations, bypass hooks or
protection, or publish a production update. Rollback uses ordinary revert commits.

The [maintainability baseline](2026-09-08-release-closeout_MAINTAINABILITY_AUDIT.md)
honestly reconstructs the remaining-closeout preflight; the
[reassessment](2026-09-08-release-closeout_MAINTAINABILITY_REPORT.md),
[architecture delta](2026-09-08-release-closeout_ARCHITECTURE_BEFORE_AFTER.md),
[learning/replay answers](2026-09-08-release-closeout_LEARNING_REPORT.md) and
[collaborator guide](2026-09-08-release-closeout_REBASE_GUIDE.md) retain the review
and handoff without claiming an original pre-code audit occurred.

## Conformance tracking

Per `docs/PLAN_REQUIREMENTS.md`, all 18 gates remain required. Final local checks and scoped reviews complete Gates 1–8 and 10–18; Gate 9 requires owner exception approval. Hosted CI and protected review are still required before merge.

- [x] Gate 1 — touched-file branch coverage and project ratchet verified.
- [x] Gate 2 — V1.34 byte-identical; no fixture regeneration.
- [x] Gate 3 — lint, format, typing and frontend/Rust gates pass.
- [x] Gate 4 — dead code and obsolete placeholders reviewed.
- [x] Gate 5 — product/build/operator documentation accurate.
- [x] Gate 6 — types, immutable DTOs, passive imports preserved.
- [x] Gate 7 — operational decisions emit categorical diagnostics.
- [x] Gate 8 — regression tests exercise outcomes and real boundaries.
- [ ] Gate 9 — existing package and dependency direction reviewed; explicit owner approval remains pending for the inherited `_version.py` top-level exception, `cockpit.ws -> _version` dependency edge and `releases_branch_seed` root-directory exception. Digitakt separately requests approval for its closed stage-discriminator exemption. Passing enforcement tests does not approve these exceptions.
- [x] Gate 10 — dispatch vocabularies remain canonical.
- [x] Gate 11 — shared fixtures reused.
- [x] Gate 12 — constants remain explicitly typed.
- [x] Gate 13 — environment controls documented with safe defaults.
- [x] Gate 14 — maintainability review completed.
- [x] Gate 15 — findings, learning and handoff retained in repo.
- [x] Gate 16 — isolated ownership, bounded parallel reviews, single updater PR.
- [x] Gate 17 — existing abstractions surveyed and reused.
- [x] Gate 18 — architecture prose/diagrams match final implementation.

Done means software repairs and combined checks pass, a precise studio artifact and ordered handoff exist, and protected merges have completed or the exact external blocker is documented. Hardware save/recapture/audition remains human evidence; favoriting is never recorded as a physical save.

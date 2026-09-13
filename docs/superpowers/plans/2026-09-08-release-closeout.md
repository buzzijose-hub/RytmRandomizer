# September 8 release closeout

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

Durable checkpoint/evidence: sibling `release-closeout-evidence/STATE.json`, `RUN_LOG.md`, per-PR snapshots, reviewer reports, and command logs. On recovery, read them and re-query GitHub before selecting the next independent action. The original dirty checkout is preserved. Remote heads may move; fetch and reconcile before publishing, never overwrite concurrent commits. Existing updater PRs close only after a verified replacement exists.

Start is the user's September 8 request. Target completion is today, with a 24-hour execution cap; unresolved external approval or physical evidence is reported precisely. A STOP message interrupts execution and records the checkpoint. Fix ordinary failures autonomously. Preserve hardware dependency pins and all V1.34 fixtures. Do not open real MIDI, fabricate observations, bypass hooks/protection, or publish a production update. Rollback uses ordinary revert commits of this bundle; source kits and installed production artifacts are untouched.

## Conformance tracking

Per `docs/PLAN_REQUIREMENTS.md`, all 18 gates remain required. Unchecked items are pending verification, not claims of completion.

- [ ] Gate 1 — touched-file branch coverage and project ratchet verified.
- [ ] Gate 2 — V1.34 byte-identical; no fixture regeneration.
- [ ] Gate 3 — lint, format, typing and frontend/Rust gates pass.
- [ ] Gate 4 — dead code and obsolete placeholders reviewed.
- [ ] Gate 5 — product/build/operator documentation accurate.
- [ ] Gate 6 — types, immutable DTOs, passive imports preserved.
- [ ] Gate 7 — operational decisions emit categorical diagnostics.
- [ ] Gate 8 — regression tests exercise outcomes and real boundaries.
- [ ] Gate 9 — existing package and dependency direction preserved.
- [ ] Gate 10 — dispatch vocabularies remain canonical.
- [ ] Gate 11 — shared fixtures reused.
- [ ] Gate 12 — constants remain explicitly typed.
- [ ] Gate 13 — environment controls documented with safe defaults.
- [ ] Gate 14 — maintainability review completed.
- [ ] Gate 15 — findings, learning and handoff retained in repo.
- [ ] Gate 16 — isolated ownership, bounded parallel reviews, single updater PR.
- [ ] Gate 17 — existing abstractions surveyed and reused.
- [ ] Gate 18 — architecture prose/diagrams match final implementation.

Done means software repairs and combined checks pass, a precise studio artifact and ordered handoff exist, and protected merges have completed or the exact external blocker is documented. Hardware save/recapture/audition remains human evidence; favoriting is never recorded as a physical save.

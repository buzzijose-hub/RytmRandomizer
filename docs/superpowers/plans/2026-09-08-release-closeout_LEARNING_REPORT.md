# Release closeout learning and replay

> Status: in-flight — replay verified from existing worktree; protected review required

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gate 15. Reuse the
existing [parallel composition rule](../../../.claude/rules/parallel-agent-composition.md)
and [composition memory](../../../agent-memory/feedback_verify_composition_not_agents.md),
rather than duplicating them in another skill.

The concrete lessons are: verify the actual producer/consumer call, not only its
shape; a true acknowledgment must precede consent dismissal; checked metadata,
signed bytes and installer input must retain one identity; a secret existing is
not a signature proof; and diagnostic export cannot depend on an optional panel
having mounted. Record a package's full source/tree and both binary hashes.
Do not transfer a previous build's smoke receipt to a later UI revision.

## Fresh-checkout handoff questions

These answers use tracked project paths and the companion files delivered with
this checkpoint. Relative-file links and state/schema structure pass local
checks. Local combined gates and hosted checks for published updater `e2e46d6e`
passed; the existing updater worktree was clean before the September 21
documentation refresh. This inspection used the existing worktree and receipts,
not a new clone or build. Required protected review remains outstanding.

1. **What is current?** The [plan](2026-09-08-release-closeout.md),
   [state](2026-09-08-release-closeout_STATE.json) and
   [log](2026-09-08-release-closeout_RUN_LOG.md) name the source checkpoint and
   incomplete gates. The [migration guide](2026-09-08-release-closeout_REBASE_GUIDE.md)
   maps the four superseded updater PRs to #248 and records verified latest-head
   inclusion before their closure.
2. **Where do I extend it?** A persisted store starts in
   `rytm_randomizer/data/persisted_state.py` plus its owning I/O guard and drift
   tests. Updater states/details start in native policy/journal and the single
   `desktop/web/src/updateProtocol.ts` contract; extend native acceptance and IPC
   tests together. Manifest rules belong in `scripts/release_lib.py`, with the
   assembly verifier and official signature fixture covering the output.
3. **How do I freeze before a show?** Set `RYTM_RAND_UPDATES=off` before launching
   the shell; restart after changing launch settings. See the shared
   [configuration index](../../LOCAL_DEV_TOOLING_NOTES.md). Freeze prevents checks,
   download, installation and check-ins; it does not change MIDI authority.
4. **How do I replay safely?** Follow [native acceptance](../../../desktop/web/native-e2e/README.md)
   and the [run playbook](../../AUTONOMOUS_RUN_PLAYBOOK.md). Use a temporary root,
   test key, real verifier and MIDI off. Keep the 32-case terminal recorder separate
   from the two actual signed Windows PE handoffs, which replace only a marked
   temporary shell copy. Run one heavy
   job at a time: pytest/Cargo/frontend at two workers; Playwright at one.
5. **What remains human/external?** The [run report](2026-09-08-release-closeout_RUN_REPORT.md)
   identifies the exact c795 studio package. Protect source kits, perform the
   ordered physical checklist and manually save/recapture favorites. Required
   code-owner review, production signing credentials and actual platform install
   evidence cannot be synthesized from automated unit or recorded-terminal tests.

The documentation source review answered these questions from the existing clean
published checkout, tracked paths and recorded local/hosted verification. It did
not create a second clone or run builds, and it does not replace protected review,
production installer evidence or operator-present hardware observations.

# Pi appliance replay and continuation playbook

Use this with the [plan](superpowers/plans/2026-09-30-pi-performance-appliance.md),
[ledger](superpowers/plans/2026-09-30-pi-performance-appliance_STATE.json),
[rule](../.claude/rules/pi-appliance-evidence.md) and
[learned skill](../.claude/skills/learned/pi-appliance-source-evidence/SKILL.md).

1. Read repository instructions and inspect actual HEAD, dirty files, remotes,
   worktrees and open PRs. Preserve unrelated changes. Resolve the current target;
   do not assume this run's `892aaffc` is the next run's base.
2. Before implementation, write the ten-dimension maintainability baseline and
   planned acceptance evidence. This run formalized it late; do not repeat that
   process gap. Keep the ledger and its sibling schema consistent, and append
   observed decisions/failures to the committed run log as they occur.
3. Assign disjoint worktrees and owners for state integration, touch, runtime and
   capabilities. Root owns contracts and one measured heavy-job queue. Start at
   pytest four workers, browser one and frontend two; reduce on resource pressure.
   Override only worker counts, not the repository's whole pytest configuration.
4. Trace existing Snapshot/engine/history/profile/capture/Device/ArmedApply paths
   before adding code. Shared facts belong in the data layer. A readable native
   field, saved capture, mock run or source build grants no live/restore authority.
5. Integrate workstreams into one branch. Run focused semantic/refusal tests,
   strict typing and touched coverage, then serialize full backend, frontend,
   architecture/parity, browser and packaging acceptance. Keep skips, failed
   attempts, source SHA, command, worker count and exit code in each receipt.
6. Use one independent reviewer per dimension. Repair concrete findings and
   rerun affected checks. Test the actual production bundle at all three sizes;
   inspect pixels and modal chrome after scrolling, not just element dimensions.
7. Finish source and documentation commits before building final artifacts.
   Generate source-bound receipts outside versioned source; never put a
   self-referential final SHA into a file whose commit changes that SHA.
   A docs-only follow-up still changes artifact identity: prove unchanged tested
   code/test trees when reusing results, and rebuild the identified package.
8. Run the post-plan ten-dimension comparison, extract reusable lessons and
   answer the five tracked-only onboarding questions in the run report. Preserve
   failures in the append-only log; external physical gaps stay explicit.
9. Push/open or update one PR against the intended integration target with the
   exact conformance checklist and automated-review attribution. Run the post-push
   dimension review and consolidated comment. Never stack workstream PRs,
   self-approve, merge or weaken protections on this user's behalf.

For a resumed run, first reconcile ledger state with Git and actual receipt
files. A status sentence is not evidence that a command ran. Stop only owned
processes on interruption and record the next concrete action. Do not retry
permission-rejected cleanup through another route. Use the
[deployment guide](PI_APPLIANCE_DEPLOYMENT.md) for exact build, preview, package,
install, rollback and uninstall commands; do not reproduce a drifting command
copy here. The [operator guide](PI_APPLIANCE_OPERATOR.md) defines the separate
physical acceptance boundary.

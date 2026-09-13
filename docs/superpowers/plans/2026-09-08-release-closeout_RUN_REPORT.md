# September 8 release closeout — run report

> Status: in-flight — September 13 checkpoint; final composed verification pending

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md).
[Plan](2026-09-08-release-closeout.md) · [State](2026-09-08-release-closeout_STATE.json)
· [Log](2026-09-08-release-closeout_RUN_LOG.md)
· [Maintainability](2026-09-08-release-closeout_MAINTAINABILITY_REPORT.md)
· [Architecture delta](2026-09-08-release-closeout_ARCHITECTURE_BEFORE_AFTER.md).

## Current outcome

The updater replacement preserves #239/#241/#242/#243 authorship. Merge
`59dfb07e` incorporates author head `a270ff11` and merged Forge/main; later
cleanup `a6290de4` removes the retired browser update fixture and `b989d5af`
removes its unconsumed journal helpers. The 505 frozen
parity files match the main index exactly after resolving line-ending-only
merge artifacts, without capture/regeneration. The merged frontend passed 1,009
tests across 71 files with all configured coverage at 100%; the merged targeted
Python suite passed 695 tests. Combined full Python, Rust, native and hosted
checks remain pending. No all-gates PASS is claimed,
and the old stack remains open until a verified replacement is linked.

Forge #238 was approved by Eddie at `2026-09-08T14:53:23Z` and merged at
`14:53:39Z` as `b1d6ff5678f80378176038fb13d6ef78d13c0abc`. Its empty-bank UI
follow-up is [#245](https://github.com/buzzijose-hub/RytmRandomizer/pull/245),
head `38397dbb2a7919d9c144f63a971a26fc66d4edfa`, tree-identical to built source
`c79597b69d055c32b8175fd665c77f20c384677c`; required checks are green and
code-owner review remains required. Digitakt's separate worktree at `35e7a1ce`
retains author merge `502c74db` and corrected manual facts/refusal tests. Its
full suite passed 9,127 tests with six skips in 375.50s; all 42 touched production
files reached 100% line/branch coverage, project pure branch coverage 99.4596%
and combined coverage 99.69%. Its 685 frozen parity cases passed within that
run. Formatting-only `23bc8b41` passed all pre-push mechanical gates and was
pushed. Documentation-only `15484906` records the still-pending owner approval
of the inherited stage-discriminator exemption; its push remains pending.
This does not assert a Digitakt PR merge.

## Coordinator-run evidence

| Boundary | Result | Limit |
| --- | --- | --- |
| Release helper | 277 tests passed at `a8ae340c`; genuine Minisign positive/modified-byte negative self-test passed. | No production keys, OS signing or release publication. |
| Native acceptance | 32 actual Wry/WebView2 cases passed in 53.9s; strict native TypeScript passed. | Real IPC/plugin verifier; terminal install/restart recorded with harmless signed bytes. |
| Native unit checkpoint | 183 tests passed with Cargo jobs 2. | Predates final diagnostic/merge changes; not a final total. |
| Updater frontend checkpoint | 885 tests / 67 files passed in 60.35s, all configured coverage metrics 100%. | Before Doctor and final author/main merge; composed checks pending. |
| Merged updater frontend | 1,009 tests / 71 files passed in 50.72s; 3,519 statements, 2,638 branches, 1,203 functions and 3,155 lines all at 100%. | Includes Doctor and author/main merge; native platform verification remains separate. |
| Merged Python targeted suite | 695 release/fleet/data/CI/store-registry tests passed in 9.46s. | Focused merged source coverage; combined full Python gate remains pending. |
| Forge follow-up | 853 frontend tests / 62 files, all coverage metrics 100%; lint/TypeScript/Vite passed. Mechanical 805 architecture / 685 parity passed. | Python full-suite evidence is inherited; 505 frozen JSON files unchanged. |
| New Forge package | Build 34241625440 succeeded; manifest/hashes verified; actual packaged smoke passed `2026-09-08T15:08:21.444Z`. | MIDI off; no physical observation or update installation. |
| Digitakt + Forge | 9,127 passed / six skips; 42 touched production files at 100%; project pure branch 99.4596%. | Separate Digitakt worktree `35e7a1ce`, not final updater combined coverage. |
| Updater combined coverage/CI | Pending. | Earlier targeted/global coverage receipts are not substituted for this final tree. |

The new studio package `show-kit-forge-studio-c79597b69d05` identifies full
source `c79597b69d055c32b8175fd665c77f20c384677c`:

- Shell SHA-256: `c79e83b2356040b8360f10e2305eedc97d4296ff84d574c39e8a85e4222518d8`.
- Sidecar SHA-256: `9b5a52fe60105b59edce6bea9fa9dbf99ff1fe4bf10e16a110475f20402e6e7b`.

The actual WebView2/bundled-backend smoke verified fresh credentials after
restart, authenticated reconnect, bank persistence, disabled empty export and
blocked adoption without captures. Its screenshot was inspected and owned
processes cleaned up. All 14 handoff-file hashes were verified; handoff manifest
SHA-256 is `15c70c96fe1259fbddd1daf572d036cb7fe9318fa1478f2e21be2c130623acf4`.
This supersedes the older `076ef67a` package as the identified software artifact;
physical checklist observations remain blank.

## Remaining limits and replay

No key means metadata discovery with an explicit unavailable-download message,
not staged bytes or consent. Beacon completion, journal rotation locking and
missing-key history are now repaired in source; final native regression remains
required. Doctor queries the snapshot on export and includes a 50-row native
journal tail, or null when unavailable, independently of Updates panel mounting.
Consent and skips remain process-local. Real OS installation/restart, production
GitHub/CDN delivery, signing credentials and required approvals remain separate.

Gate 9 requires explicit owner approval for the inherited `_version.py`
top-level/import carve-out and `releases_branch_seed` root-directory exception.
Digitakt independently requests approval for its narrow `cockpit/data/stage.py`
identity-gate exemption. Recorded rationale and passing tests do not substitute
for approval.

Fresh-clone handoff answers, using repository files (final clean-checkout check
pending): current plan/state/log are linked above; new stores extend
`data/persisted_state.py` plus their owning I/O guard; updater events extend native
policy and shared `updateProtocol.ts`; freeze requires `RYTM_RAND_UPDATES=off`
before restart; safe native replay follows [native-e2e/README.md](../../../desktop/web/native-e2e/README.md)
and the existing [recovery playbook](../../AUTONOMOUS_RUN_PLAYBOOK.md). The remaining
human work is protected review and A4/Rytm audition/save/recapture, not simulated
by favoriting. The [composition memory](../../../agent-memory/feedback_verify_composition_not_agents.md)
retains timer/transport, authoritative acknowledgment and signature-proof lessons.
Detailed local receipts live in sibling `release-closeout-evidence`; this tracked
checkpoint preserves conclusions without private keys or fabricated final passes.

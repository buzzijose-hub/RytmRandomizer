# September 8 release closeout — run report

> Status: in-flight — all local gates passed; owner exception approval and hosted review pending

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
merge artifacts, without capture/regeneration. Final local validation source
`7cc10e929ece79ec2f67b1342c547597529652f0` preserves the updater, Digitakt
`15484906` and Forge follow-up `38397dbb` histories. Its full Python suite passed
9,922 tests with six skips and six warnings in 278.98s. The touched-file gate
passed all 51 production files at 100% line/branch coverage; project pure branch
coverage is 99.46%, above the unchanged 99% floor. Version sync also passed for
all four declarations at 1.34.0. Frontend passed 1,010 tests across 71 files in
40.58s with every configured coverage metric at 100%; ESLint and build passed.
Browser passed 32 tests with two existing skips in 52.6s. Those skips are the
keyboard skeleton and the armed journey requiring absent virtual MIDI; no
updater or native case is skipped. Current native units, the 32-case recorder
matrix and both actual Windows PE handoffs pass. Final Rust format/test/clippy, Ruff/Black/isort, strict Pyright on 51 production
modules and the required dead-code scan all passed. Updater replacement
publication, hosted checks and protected review remain pending. Production NSIS/macOS/Linux installer evidence
also remains outside the verified PE-fixture scope.
No all-gates PASS is claimed,
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
of the inherited stage-discriminator exemption and is now pushed. All its
hosted checks, including `required-checks` for both push and pull-request events,
passed; GitHub still reports `REVIEW_REQUIRED`. This does not assert a Digitakt
PR merge or approve its architecture exception.

## Coordinator-run evidence

| Boundary | Result | Limit |
| --- | --- | --- |
| Release helper | 277 tests passed at `a8ae340c`; genuine Minisign positive/modified-byte negative self-test passed. | No production keys, OS signing or release publication. |
| Native acceptance | 32 actual Wry/WebView2 cases passed in 53.9s; strict native TypeScript passed. | Real IPC/plugin verifier; terminal install/restart recorded with harmless signed bytes. |
| Native unit checkpoint | 183 tests passed with Cargo jobs 2. | Predates final diagnostic/merge changes; not a final total. |
| Current native units/build | Final Rust formatting, 186 default tests and all-target Clippy with warnings denied passed; native build passed in 15.75s and native TypeScript passed. | Final Rust checks used Cargo-resolved ignored validation lock; plugin/Tauri match the native binary at 2.11.0/2.11.5. Actual Windows handoff has a separate receipt. |
| Current native acceptance | 32 actual Wry/WebView2 cases passed in 53.5s (`native-matrix-final.log`). | Real IPC/plugin verifier with recorded install/restart boundary; actual Windows handoff has a separate receipt below. |
| Actual Windows installer handoff | `install_on_quit` and `install_now` both passed in 8.2s (`native-handoff-final.log`). | Actual plugin handoff to the signed Windows PE fixture; not production NSIS or macOS/Linux installers. |
| Updater frontend checkpoint | 885 tests / 67 files passed in 60.35s, all configured coverage metrics 100%. | Historical pre-Doctor/author-main checkpoint; final combined result is below. |
| Merged updater frontend | 1,009 tests / 71 files passed in 50.72s; 3,519 statements, 2,638 branches, 1,203 functions and 3,155 lines all at 100%. | Includes Doctor and author/main merge; native platform verification remains separate. |
| Merged Python targeted suite | 695 release/fleet/data/CI/store-registry tests passed in 9.46s. | Focused merged checkpoint; final passing full run is below. |
| Forge follow-up | 853 frontend tests / 62 files, all coverage metrics 100%; lint/TypeScript/Vite passed. Mechanical 805 architecture / 685 parity passed. | Python full-suite evidence is inherited; 505 frozen JSON files unchanged. |
| New Forge package | Build 34241625440 succeeded; manifest/hashes verified; actual packaged smoke passed `2026-09-08T15:08:21.444Z`. | MIDI off; no physical observation or update installation. |
| Digitakt + Forge | 9,127 passed / six skips; 42 touched production files at 100%; project pure branch 99.4596%. | Separate Digitakt worktree `35e7a1ce`, not final updater combined coverage. |
| First combined Python run | 9,919 passed / two architecture failures / six skips in 305.37s. All 51 touched production files had 100% line/branch coverage; project pure branch 99.4618395%, combined 99.6949435%. | Failed run at `636e4e4a`; export/index repairs in `a928e0f1` are verified by the final passing run below. |
| Final combined Python and coverage | 9,922 passed / six skips / six warnings in 278.98s at `7cc10e92`. Touched-file gate passed 51 production files at 100% line/branch coverage; pure-branch ratchet passed 99.46% against unchanged 99% floor. Four version declarations agree on 1.34.0. | Final source suite passed; Python lint/type/dead-code checks also passed; hosted review remains separate. |
| Final combined frontend | 1,010 tests / 71 files passed in 40.58s; 3,519 statements, 2,641 branches, 1,203 functions and 3,155 lines all at 100%. ESLint and build passed. | At final validation source `7cc10e92`; updater hosted checks remain pending. |
| Final browser suite | 32 passed / two existing skips in 52.6s. | Skips: keyboard skeleton and virtual-MIDI-dependent armed journey; no updater/native skips. |
| Digitakt hosted CI | All checks passed for `15484906`, including push and pull-request `required-checks`. | `REVIEW_REQUIRED`; protected approval is still outstanding. |
| Final local static/dead-code checks | Ruff, Black (916 files), isort, strict Pyright (51 modules), Rust format/test/clippy and Vulture all passed. | Test-only cleanup `ae60f111` retained fixture execution/assertions; 80 targeted release tests passed in 0.65s. |
| Replacement publication/hosted checks | Pending. | Local gates do not supply hosted checks, owner exception approval or protected merge. |

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
missing-key history are repaired and the current 186-test Rust suite and
32-case native matrix passed. Doctor queries the snapshot on export and includes a 50-row native
journal tail, or null when unavailable, independently of Updates panel mounting.
Consent and skips remain process-local. The actual Windows handoff used combined
frontend/backend `54a13ab0` and the native binary from the same Rust source at
`70e50605`. Fixture preparation fix `f256db40` compiled and signed inputs in
`handoff-inputs-20260913c`. Installer SHA-256 is
`bc2909b33d558f64c837c46d63ad62e6682f12edf128bbf775ec3d0a970383e0`;
successor SHA-256 is
`28c8df8ef5761ef28bb31dc8e49276578942cebb56a95ef200da985286beca96`.
Both real plugin install choices passed. This closes that PE handoff evidence
gap; production NSIS, macOS/Linux installation, GitHub/CDN delivery, production
signing credentials and required approvals remain separate.

Read-only GitHub inspection on September 13 returned 404 for the `releases`
branch endpoint. Repository Actions variable-name and secret-name listings both
succeeded and were empty. Production distribution activation remains an owner
release-configuration task; no secret values were inspected and no production
release was published.

Gate 9 requires explicit owner approval for the inherited `_version.py`
top-level exception, `cockpit.ws -> _version` dependency edge and
`releases_branch_seed` root-directory exception.
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

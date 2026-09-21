# Updater review and repair ledger — September 21 checkpoint

Original review baseline: #239 `218f18a4`, #241 `ab8c9b58`, #242 `47d0ce94`,
#243 `6d1c6228`. Later author history through `a270ff11` is preserved by merge
`59dfb07e`, together with the merged Forge baseline. The verified replacement is
[PR #248](https://github.com/buzzijose-hub/RytmRandomizer/pull/248), based on
`modularize-v1.34`. Original PRs #239/#241/#242/#243 were closed as superseded
on September 21 after their latest heads were verified as ancestors of #248
`e2e46d6e`; their branches and authorship are preserved. No production update is published.

## Confirmed findings and dispositions

| Finding | Repaired behavior | Evidence and remaining check |
| --- | --- | --- |
| Launch/four-hour dispatch missing | Monotonic schedule starts after transport attachment, with no catch-up burst. | Current 186-test default Rust suite and 32-case native matrix passed. |
| Reconstructed manifest erased rollout/hardware metadata | Pass plugin `raw_json` to policy. | Real native matrix covers eligibility, cohort and hardware warning. |
| Second check could select a different artifact | Retain checked Update/version/URL/signature and verified bytes through install. | Real plugin verifier and modified-byte/wrong-key native cases passed. |
| Overlapping checks and late callbacks replaced state | Single-flight operations and stale-callback refusal. | Unit regressions and native in-flight/cancellation cases passed. |
| Restart choice and sidecar teardown diverged | Accepted exact consent uses shared teardown; wait for supervisor and child exit. | Native quit/now/crash/failure cases passed with recorded installer terminal. Separate actual Windows PE install-on-quit/install-now cases both passed; production installers remain outside that scope. |
| Failed teardown left reusable consent | Revoke failed/used consent and serialize repeated exits. | Unit/native lifecycle checkpoint passed. |
| Frontend settings were local-only | Render native launch channel/freeze with restart guidance. | Final combined frontend 1,010/71 files, all configured coverage metrics 100%. |
| Startup event/activity could be missed | Subscribe through actual Tauri IPC, then read snapshot; refuse stale replies. | SDK-level IPC tests and native hydrate/reload/reconnect cases passed. |
| Consent disappeared before native acceptance | Await explicit boolean acknowledgment for the same version/choice. | Frontend retry/stale-ack and native consent cases passed. |
| Native failed/skipped states were discarded | Recognize actual native vocabulary and keyless metadata-only discovery. | State regressions included in the final 1,010-test frontend checkpoint. |
| Beta versions used incomplete comparison | Use one SemVer parser/precedence path; ignore build metadata for ordering. | Source repaired through `075416ae`; current 186-test default Rust suite and native matrix passed. |
| Key detection read an unset compile-time variable | Read the actual bundled `tauri.conf.json`. | Keyless native case confirms no download; production key remains empty. |
| Loopback override accepted lookalike hosts | Validate parsed host/scheme, credentials/query/fragment and redirects. | Native fixture supplies explicit loopback transport; production signature/host rules remain. |
| Release signing claimed success from secret presence | Generate actual Tauri signatures and verify collected bytes, source, version and four targets. | Merged 695-test Python suite covers release repairs; genuine Minisign positive/tamper-negative self-test passed earlier. |
| Linux package formats and cached bundles could mismatch manifests | Select AppImage for the desktop Linux update contract; clean only validated bundle output. | Source repairs in `7cc6d442`; existing Deb/RPM desktop installs need manual AppImage migration. |
| Stable promotion lost verified release metadata | Preserve verified notes/hardware flags/signatures and shared hardware-path detection. | `67418040` and `e614129a`; merged 695-test Python suite passed. |
| Fleet omitted releases beyond 100 | Continue release pagination until exhausted. | Fleet/dashboard cases passed in the merged 695-test Python suite. |
| “Guaranteed lower bound” misrepresented counters | Explain offline/opt-out undercounts and repeated/public-request inflation. | Dashboard/snapshot assertions passed; no unique-device claim. |
| Regex HTML extraction tripped CodeQL | Use HTMLParser, including uppercase-tag/attribute cases. | Focused Python tests and hosted CodeQL passed at `e2e46d6e`. |
| Windows child test assumed Unix `true` | Use platform-native trivial child process. | Native unit checkpoint passed. |
| Beacon completions never reached history | Asynchronous closed success/failure callback; no retry or update gating. | Current 186-test Rust suite and 32-case native matrix passed, including repaired journal behavior. |
| Missing signing key had no journal reason | Record existing categorical keyless refusal alongside discovery state. | Current 186-test Rust suite and 32-case native matrix passed; keyless discovery remains download-disabled. |
| Concurrent rotation could lose journal rows | Share a writer lock across rotation and append, outside policy-state lock. | Concurrent-write regression passed in the current 186-test Rust suite. |
| Doctor export omitted native activity | Read shared snapshot on export, project at most 50 sanitized rows; unavailable becomes null. | Doctor/SDK outcome tests passed in the final combined frontend suite: 1,010 tests, all configured coverage 100%. |
| A native CI timeout had insufficient diagnostic evidence; pending IPC could outlive the polling deadline | Debug-only acceptance observes state/journal together, bounds pending IPC by the existing 25-second deadline, reports bootstrap failures and report entry, and captures bounded credential-redacted timeout evidence before cleanup. | Seven focused tests, native TypeScript/targeted ESLint, Rust format/strict native-test Clippy, all 32 native cases (55.3s) and two actual PE handoffs (8.6s) passed. Fresh hosted checks remain pending; the original hang's cause is still unproven. |

## Evidence boundary

Current validation source `7cc10e929ece79ec2f67b1342c547597529652f0`
passed **9,922 Python tests / six skips in 278.98s**, including the repaired
architecture checks. All **51 touched production files** passed the actual
100% line/branch gate; the **99.46%** pure-branch result clears the unchanged
**99%** floor. Earlier release/fleet/data/CI/store-registry regressions passed
695 tests. Version sync confirms four declarations at 1.34.0.

Final combined frontend passed **1,010 tests / 71 files in 40.58s**, all configured
coverage **100%** (3,519 statements, 2,641 branches, 1,203 functions, 3,155 lines).
ESLint and build passed. Browser passed **32 cases / two existing skips in
52.6s**: keyboard skeleton and an armed journey requiring unavailable virtual
MIDI. No updater/native cases are skipped.

The current **32 real Wry/WebView2 cases passed in 53.5s**, using the real shell,
IPC and plugin signature verifier with recorded terminal operations. Separately,
**both actual Windows PE handoffs passed in 8.2s**: install on quit and install
now, with compiled/signed installer and successor processes. The
[run report](superpowers/plans/2026-09-08-release-closeout_RUN_REPORT.md) identifies
both SHA-256 hashes and the exact source/input set. This proves actual Windows
plugin/PE handoff, not production NSIS/MSI, macOS/Linux installation, publisher
signing/notarization or production GitHub/CDN delivery.

Final default Rust tests passed **186 cases**; formatting and all-target Clippy
with warnings denied also passed. Ruff, Black, isort, strict Pyright on all 51 production modules and the required
Vulture scan also passed after test-only fixture cleanup `ae60f111`; the 80
focused release tests passed in 0.65s with setup and assertions preserved.
Replacement #248 is published. All hosted checks passed at
`e2e46d6ec086a5f86a52a3bb080be4bfcbe9da5d`, including both `required-checks`
aggregates, CodeQL and Windows native compilation/typechecking plus the 32-case
recorder matrix and two actual PE handoffs. The
[push run](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/34769559471)
and [PR run](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/34769561768)
retain the hosted receipts. Required owner review, including explicit
architecture-exception approval, remains pending.

At the later documentation-only head `124a3129`, results diverged: the
[PR Windows job](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/35614910454/job/106383099423)
passed 31 native cases, then `rollout_out` hit the existing 65-second process
timeout; the later two-PE step was skipped because the job had failed. The
[push Windows job](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/35614905361/job/106383072742)
passed all 32 native cases in 1.5 minutes and both PE cases in 10 seconds.
Twenty unchanged local `rollout_out` repetitions passed in 33.6 seconds.
The original hang's cause remains unproven. The subsequent debug-acceptance
repairs preserve production behavior, timeout values, retry policy and skip
conditions. The candidate harness passed seven focused tests, native TypeScript
and targeted ESLint, Rust formatting and strict all-target Clippy with
`native-test` enabled. A fresh debug build completed in 16.44 seconds; all
32 native cases passed in 55.3 seconds and both actual PE handoffs in 8.6 seconds.
The ordinary app/runtime is unchanged. The run report records the candidate
binary hash; new-head hosted checks remain pending until commit/push. These
passing receipts do not establish a fixed hang or erase the failed PR receipt.

Read-only GitHub inspection on September 13 returned **404** for the `releases`
branch endpoint. Repository Actions variable-name and secret-name listings both
succeeded and were empty. Production distribution activation therefore remains
an owner release-configuration task; no secret values were inspected and no
production release was published. See the
[state](superpowers/plans/2026-09-08-release-closeout_STATE.json) for pending gates.

The current separate Forge studio artifact is `show-kit-forge-studio-c79597b69d05`,
source `c79597b69d055c32b8175fd665c77f20c384677c`, tree-identical to #245 `38397dbb`.
Its real packaged smoke and all 14 handoff-file hashes passed. #238 merged after
Eddie's approval; #245 checks are green with its own review required. No software
receipt fills the blank Rytm/A4 audition, source restore, manual save or recapture
observations. A4 SEND and persistent Cockpit SAVE remain blocked.

## Sources and ownership

The repair uses the existing [Tauri Update API](https://docs.rs/tauri-plugin-updater/latest/tauri_plugin_updater/struct.Update.html)
for raw manifest data and verified bytes, its
[builder](https://docs.rs/tauri-plugin-updater/latest/tauri_plugin_updater/struct.UpdaterBuilder.html)
for endpoint/target/timeout/version hooks, and the reference Minisign verifier.
The [architecture delta](superpowers/plans/2026-09-08-release-closeout_ARCHITECTURE_BEFORE_AFTER.md)
records ownership; the [collaborator guide](superpowers/plans/2026-09-08-release-closeout_REBASE_GUIDE.md)
records replacement rules. Detailed machine receipts remain in the orchestrator's
`release-closeout-evidence` directory; no private credentials are copied here.

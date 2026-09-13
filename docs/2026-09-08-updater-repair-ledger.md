# Updater review and repair ledger — September 13 checkpoint

Original review baseline: #239 `218f18a4`, #241 `ab8c9b58`, #242 `47d0ce94`,
#243 `6d1c6228`. Later author history through `a270ff11` is preserved by merge
`59dfb07e`, together with the merged Forge baseline. The original stack remains
open until one verified replacement exists. No production update is published.

## Confirmed findings and dispositions

| Finding | Repaired behavior | Evidence and remaining check |
| --- | --- | --- |
| Launch/four-hour dispatch missing | Monotonic schedule starts after transport attachment, with no catch-up burst. | 183-unit pre-merge checkpoint; final composed run pending. |
| Reconstructed manifest erased rollout/hardware metadata | Pass plugin `raw_json` to policy. | Real native matrix covers eligibility, cohort and hardware warning. |
| Second check could select a different artifact | Retain checked Update/version/URL/signature and verified bytes through install. | Real plugin verifier and modified-byte/wrong-key native cases passed. |
| Overlapping checks and late callbacks replaced state | Single-flight operations and stale-callback refusal. | Unit regressions and native in-flight/cancellation cases passed. |
| Restart choice and sidecar teardown diverged | Accepted exact consent uses shared teardown; wait for supervisor and child exit. | Native quit/now/crash/failure cases passed with recorded installer terminal. Actual OS install remains untested. |
| Failed teardown left reusable consent | Revoke failed/used consent and serialize repeated exits. | Unit/native lifecycle checkpoint passed. |
| Frontend settings were local-only | Render native launch channel/freeze with restart guidance. | Merged frontend 1,009/71 files, all configured coverage metrics 100%. |
| Startup event/activity could be missed | Subscribe through actual Tauri IPC, then read snapshot; refuse stale replies. | SDK-level IPC tests and native hydrate/reload/reconnect cases passed. |
| Consent disappeared before native acceptance | Await explicit boolean acknowledgment for the same version/choice. | Frontend retry/stale-ack and native consent cases passed. |
| Native failed/skipped states were discarded | Recognize actual native vocabulary and keyless metadata-only discovery. | State regressions included in the merged 1,009-test frontend checkpoint. |
| Beta versions used incomplete comparison | Use one SemVer parser/precedence path; ignore build metadata for ordering. | Source repaired through `075416ae`; final native/unit regression pending. |
| Key detection read an unset compile-time variable | Read the actual bundled `tauri.conf.json`. | Keyless native case confirms no download; production key remains empty. |
| Loopback override accepted lookalike hosts | Validate parsed host/scheme, credentials/query/fragment and redirects. | Native fixture supplies explicit loopback transport; production signature/host rules remain. |
| Release signing claimed success from secret presence | Generate actual Tauri signatures and verify collected bytes, source, version and four targets. | Merged 695-test Python suite covers release repairs; genuine Minisign positive/tamper-negative self-test passed earlier. |
| Linux package formats and cached bundles could mismatch manifests | Select AppImage for the desktop Linux update contract; clean only validated bundle output. | Source repairs in `7cc6d442`; existing Deb/RPM desktop installs need manual AppImage migration. |
| Stable promotion lost verified release metadata | Preserve verified notes/hardware flags/signatures and shared hardware-path detection. | `67418040` and `e614129a`; merged 695-test Python suite passed. |
| Fleet omitted releases beyond 100 | Continue release pagination until exhausted. | Fleet/dashboard cases passed in the merged 695-test Python suite. |
| “Guaranteed lower bound” misrepresented counters | Explain offline/opt-out undercounts and repeated/public-request inflation. | Dashboard/snapshot assertions passed; no unique-device claim. |
| Regex HTML extraction tripped CodeQL | Use HTMLParser, including uppercase-tag/attribute cases. | Focused Python tests passed; final hosted CodeQL remains required. |
| Windows child test assumed Unix `true` | Use platform-native trivial child process. | Native unit checkpoint passed. |
| Beacon completions never reached history | Asynchronous closed success/failure callback; no retry or update gating. | Source repaired; final native journal regression pending. |
| Missing signing key had no journal reason | Record existing categorical keyless refusal alongside discovery state. | Source repaired; final native regression pending. |
| Concurrent rotation could lose journal rows | Share a writer lock across rotation and append, outside policy-state lock. | Source repaired; final concurrent-write regression pending. |
| Doctor export omitted native activity | Read shared snapshot on export, project at most 50 sanitized rows; unavailable becomes null. | Doctor/SDK outcome tests passed in merged frontend suite: 1,009 tests, all configured coverage 100%. |

## Evidence boundary

The September 8 native acceptance run passed **32 actual Wry/WebView2 cases in
53.9s**, using the real shell, IPC and plugin signature verifier. Terminal OS
installation/restart was recorded with harmless signed bytes. It does not prove
an actual updater installation, Apple notarization, Windows publisher signing
or production GitHub/CDN delivery. Missing native prerequisites fail; retired
skipped browser placeholders are not counted as passing cases. The existing
Windows desktop-shell CI job now includes native compilation/typechecking and
these cases; hosted execution remains evidence to collect.

The September 13 pre-merge checkpoints were **183 Rust unit tests** and **885
frontend tests / 67 files**, with all configured frontend coverage at **100%**.
These precede Doctor and the final author/main merge. The merged frontend then
passed **1,009 tests / 71 files in 50.72s**, with all configured coverage at
**100%** (3,519 statements, 2,638 branches, 1,203 functions, 3,155 lines). Merged
release/fleet/data/CI/store-registry Python tests passed **695 cases in 9.46s**.
Combined full Python and final native/platform/hosted checks remain required; see the [run report](superpowers/plans/2026-09-08-release-closeout_RUN_REPORT.md)
and [state](superpowers/plans/2026-09-08-release-closeout_STATE.json).

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

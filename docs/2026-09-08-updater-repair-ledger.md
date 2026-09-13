# Updater review and repair ledger — September 8

Review baseline: #239 `218f18a4`, #241 `ab8c9b58`, #242 `47d0ce94`, #243 `6d1c6228`. Original authorship is retained in the replacement bundle. The original stack stays open until a verified replacement is available. This is software preparation, not a production update publication.

## Confirmed defects and repairs

| Finding | Repair | Verification status |
| --- | --- | --- |
| No launch/four-hour dispatch | Monotonic schedule starts only after transport attachment; no catch-up burst | Native schedule tests pass |
| Manifest reconstruction erased rollout and hardware warning | Preserve plugin `raw_json` and send it through the existing policy validator | Native boundary verification still in progress |
| Second check could change artifact after validation | Retain the checked Update; bind version, URL and signature before download; retain verified bytes through install | Identity tests pass; signed integration pending |
| Parallel checks and late callbacks could replace staged state | One active check/download; ignore callbacks outside their operation | Native regression passes |
| Windows install-on-quit could restart unexpectedly | Pass the accepted restart choice to the plugin | Native integration pending |
| Install-now never shut down the sidecar | Route accepted consent through shared teardown and restart; wait for supervisor before checking the child | Native lifecycle verification in progress |
| Shutdown failure could leave reusable consent | Void consent after failed shutdown; serialize teardown | Native failed-shutdown/repeated-exit regression passes |
| Frontend freeze/channel were local-only controls | Display resolved shell settings and explicit environment/restart instructions | Frontend checks in progress |
| Initial IPC event could be missed; activity never hydrated | Subscribe then request authoritative snapshot; deserialize bounded journal through closed types | Journal native test passes; frontend checks in progress |
| Consent UI disappeared before shell accepted | Await a boolean acknowledgment; retain retry and reject stale responses | Frontend checks in progress |
| Beta-to-beta updates were skipped | Use SemVer precedence; build metadata does not affect ordering | Native regression passes |
| Signing presence inspected an unset compile-time variable | Read the same bundled configuration the plugin uses | Config tests pass with current empty key |
| Loopback override accepted lookalike hosts | Parse URL and compare exact host/scheme; reject credentials/query/fragment | Native regression passes |
| Fleet omitted releases after the first 100 | Fetch every page until exhausted | Targeted Python verification pending |
| Fleet estimator claimed a guaranteed lower bound | State that opt-outs undercount while launches/manual/public requests can inflate the estimate | Targeted Python verification pending |
| CodeQL flagged regex HTML script extraction | Reuse HTMLParser and test uppercase tags/attributes | Targeted Python/CodeQL verification pending |
| Unix-only child test failed on Windows | Launch a trivial process through the platform's native command | Native regression passes |

The first Windows native run exposed the `true` executable assumption. The next run exposed a test sending two terminal failure callbacks for one attempt; it now starts a second real attempt and separately verifies stale callbacks are ignored. Assertions and gates were retained.

## Verification and non-claims

Latest native run: 181 tests passed with Cargo jobs 2. The production transport is compiled during tests. No real MIDI or production installer ran. The repository's public signing key remains empty; signed production installation is unavailable until the project configures its release signing credentials. Test-only signing and a safe install boundary are still required for full end-to-end evidence. The inherited skipped browser scenarios are not evidence of completion.

The current operator artifact remains Forge source `076ef67a3276bdd27ec6657f9dff77ccf207a5e2`, not this unverified updater bundle. Both its shell/backend hashes match its build manifest. No hardware save, A4 live conversion, or SEND authority is inferred from software tests.

## Source references

The [Tauri Update API](https://docs.rs/tauri-plugin-updater/latest/tauri_plugin_updater/struct.Update.html) exposes raw manifest data and verified downloaded bytes; Windows install exits the application, while other platforms require relaunch. The [builder API](https://docs.rs/tauri-plugin-updater/latest/tauri_plugin_updater/struct.UpdaterBuilder.html) provides endpoint, target, timeout and version-comparison hooks. The repair reuses those capabilities rather than implementing signature verification itself.

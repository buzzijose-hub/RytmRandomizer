# Native updater acceptance target

This target replaces the 24 deferred updater client cases in the ordinary browser
suite. Playwright runs the fixture server and assertions; the UI runs inside an
actual Wry/WebView2 shell. No `Page`, injected fake IPC, synthetic update events,
or simulated Zustand update state is used.

Prerequisites: Windows desktop session with WebView2, the normal Rust/MSVC desktop
toolchain, installed web dependencies, and an existing Python environment with
the repository's backend dependencies. Tests run serially and open hidden windows.

From `desktop/shell`, build `cargo build --features native-test`. Copy the resulting
debug executable to a dedicated `native-test` output directory and record its hash
with the tested source revision. Reusing Cargo's cache is fine; never label that
feature-enabled executable as the ordinary production debug binary. The feature
is off by default and a release build with it fails at compile time.

From `desktop/web`, set `RYTM_NATIVE_TEST_BINARY` to that absolute executable path
and `PYTHON` to the existing absolute Python executable, then run:

```text
npx tsc --noEmit -p tsconfig.native.json
npx playwright test --config playwright.native.config.ts
```

For the first build, `--grep staged_ui` is a useful smoke check. Missing native
prerequisites fail this explicit target; they do not silently skip cases. The
ordinary browser config retains schema, copy and rollout-vector tests, and does
not claim to test native installation boundaries.

The fixture builds a temporary entry script from the current repository's
`scripts.build_sidecar_binary.entry_source()`. The real native supervisor launches
that script with the existing Python executable. This executes the same current
backend composition and stdin shutdown contract as the packaged sidecar, without
running PyInstaller. MIDI is forced off; backend sessions must remain disarmed.
The restart case kills that owned passive backend, checks that both native
credential bridges rotate, rejects the old WebSocket token and authenticates the
replacement backend from the same page.

The manifest travels over loopback through the actual updater plugin. Policy
validates canonical GitHub artifact identity before a feature-only routing hook
points the download at the local fixture. The real plugin verifies the signed
bytes using its normal minisign verifier. Successful terminal installation is
recorded with version, consent choice and SHA-256; the bytes are the harmless
four-byte string `test`. No installer or production update runs. Real installer
packaging, GitHub/CDN connectivity and hardware revalidation remain separate
release checks.

Cases cover native event/snapshot hydration, visible staged UI and journal,
process freeze, rollout boundary and expansion, beacon failures/hangs, malformed
manifest, altered signed bytes, wrong key, keyless discovery, stale consent,
exactly-once clean shutdown, install failure, crash/relaunch without replaying
consent, skip/reload/new version, backend authentication restart, concurrent
checks and cancellation during manifest/download work. Fixture roots isolate
WebView storage, update journals, tokens and ARM secrets. The runner reaps its
owned process tree on failure and removes its temporary directory.

The key/signature test vector comes from `minisign-verify` 0.2.5's upstream test
`verify_prehashed` in `src/lib.rs` (Frank Denis; MIT). It uses public test data;
no private release signing key is needed. The license is reproduced in
`minisign-vector-LICENSE.txt` beside this document.

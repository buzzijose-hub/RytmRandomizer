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
recorded with version, consent choice and SHA-256 in these 32 cases; the bytes are
the harmless four-byte string `test`. The additional Windows target below exercises
the plugin's actual installer process handoff.

Cases cover native event/snapshot hydration, visible staged UI and journal,
process freeze, rollout boundary and expansion, beacon failures/hangs, malformed
manifest, altered signed bytes, wrong key, keyless discovery, stale consent,
exactly-once clean shutdown, install failure, crash/relaunch without replaying
consent, skip/reload/new version, backend authentication restart, concurrent
checks and cancellation during manifest/download work. Fixture roots isolate
WebView storage, update journals, tokens and ARM secrets. The runner reaps its
owned process tree on failure and removes its temporary directory. A failed real
handoff retains its isolated directory so it cannot remove files still owned by
the bounded installer process.

The acceptance driver observes rollout state and its decision journal together.
Its existing 25-second polling deadline also bounds a pending IPC predicate;
the outer 65-second process deadline is unchanged. A bootstrap failure reports
a categorical error through the already-injected native bridge. The native
report handler writes `report-started.json` before teardown; `result.json` still
means teardown completed, so the marker alone never proves success. Before a
timeout cleanup, the runner captures bounded request paths, journal event names,
report/credential-presence flags and credential-redacted output. Test retries,
skips and deadlines are not increased to hide a failing case. These diagnostics
improve evidence collection without establishing the cause of an earlier hang.

The key/signature test vector comes from `minisign-verify` 0.2.5's upstream test
`verify_prehashed` in `src/lib.rs` (Frank Denis; MIT). It uses public test data;
no private release signing key is needed. The license is reproduced in
`minisign-vector-LICENSE.txt` beside this document.

## Actual Windows install and restart

The two cases in `native-install-e2e` use the same debug shell, native UI, passive
backend and real updater plugin. Prepare an ephemeral signed fixture with the
Windows .NET Framework compiler and official Minisign 0.12. The preparation script
finds `csc.exe` under the operating system's `WINDIR` (Framework64/v4.0.30319),
requires an explicit fresh absolute output directory and signer path, and never
reads production signing secrets. From the repository root, in PowerShell:

```powershell
& ./desktop/web/native-e2e/installer-fixture/prepare.ps1 `
  -OutputDirectory 'C:/absolute/fresh/handoff-inputs' `
  -Minisign 'C:/absolute/minisign-win64/x86_64/minisign.exe'
$env:RYTM_NATIVE_HANDOFF_INPUTS = 'C:/absolute/fresh/handoff-inputs/handoff-inputs.json'
# Keep PYTHON and RYTM_NATIVE_TEST_BINARY set as described above.
Set-Location desktop/web
npx playwright test --config playwright.native-install.config.ts --workers=1
```

The input manifest binds the artifact, embedded successor and current fixture
sources by SHA-256. Each case copies the native shell into a fresh
`rytm-native-update-*` directory, sets the plugin's `TEMP`/`TMP` there, and supplies
a fixture nonce. The inert windowless installer refuses paths outside that root,
reparse points, unexpected bytes, a live backend or an unexpected native process.
It waits for the plugin to exit the parent before replacing only `fixture-shell.exe`
with its embedded inert successor. Neither program uses installation directories,
registry writes, MIDI or elevation.

Assertions require the actual signed artifact to reach the plugin, one installer
launch, native parent exit, backend teardown before handoff, and the changed file
hash. Install on quit must launch no successor; Install now must launch the actual
replacement exactly once and receive its versioned receipt. The runner waits for
both processes to exit before accepting the external receipts and cleaning up.
Missing preparation fails this explicit target; the original 32 cases do not
require it. CI runs both targets serially in the existing Windows desktop job and
uploads their separate reports.

This verifies the Windows plugin's PE extraction, launch arguments, process exit
and restart handoff. Production NSIS packaging and UI, OS installer rollback,
macOS/Linux installation, GitHub/CDN connectivity and hardware validation remain
separate release checks. The inert successor does not run the production startup
journal confirmation; these cases do not claim `install_ok` from the launch alone.

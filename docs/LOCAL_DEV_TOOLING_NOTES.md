# Local Dev Tooling Notes

## Incremental strict production typing

`just typecheck` runs Pyright 1.1.411 (the version pinned in `pyproject.toml`'s
development extra — keep this number in sync with that pin) against every
production module discovered
by `scripts/typecheck_touched.py` from the committed branch diff, working tree,
and untracked files. The bare command is `python scripts/typecheck_touched.py`.
The development extra pins Pyright and the shared pre-push review gate plus CI
invoke the same script. Dynamic test-harness typing is intentionally outside
this incremental production gate and remains tracked as separate cleanup debt.
Base-ref precedence is:

1. `TYPECHECK_BASE_REF` when a developer explicitly names a fetched ref.
2. GitHub Actions' `GITHUB_BASE_REF`, resolved as `origin/<branch>`.
3. The safe default `origin/modularize-v1.34`.

Use `TYPECHECK_BASE_REF` only to reproduce a real alternate integration target,
never to narrow the changed-file set or bypass a typing failure.

## Atomic no-overwrite filesystem support

POSIX no-overwrite publication uses a hard link for race-safe destination
creation. Filesystems without hard-link support, including some FAT/exFAT and
network mounts, fail closed with a write error rather than silently weakening
the no-overwrite guarantee. Windows uses its race-safe rename path and does not
require hard-link support.

## 1. Purpose

Track small local developer tools that can help RytmRandomizer development
without adding project dependencies or changing runtime behavior.

This note is local-tooling guidance only.

It does not add package metadata, runtime dependencies, MIDI behavior, port
opening, active execution, CLI execution, or hardware behavior.

## 2. Current Tool Check

Checked from the project workspace on May 11, 2026.

Available locally:

- `pytest`
  - version checked: `pytest 9.0.3`
  - useful for focused red/green test runs
- `ripgrep` / `rg`
  - version checked: `ripgrep 15.1.0`
  - useful for fast code and docs search
- GitHub CLI / `gh`
  - version checked: `gh version 2.92.0`
  - useful later for push/PR workflow

Not currently installed:

- `ruff`
  - useful later for lint/format checks
  - not needed before the next runtime-state implementation/review slices

## 3. Current Recommendation

Use now:

- `pytest`
- `rg`

Keep available for later:

- `gh`

Defer for now:

- `ruff`
- heavier automation
- new package metadata
- managed dev dependency files

## 4. Why Defer Ruff

`ruff` will likely be useful once implementation volume grows.

It is intentionally deferred because the current project priority is:

- preserve V1.34 behavior reference
- keep closeout stable
- implement tiny runtime-state modules test-first
- avoid adding tool noise during the first runtime-state implementation slices

## 5. Future Possible Tooling Slice

A future local-tooling slice may:

- create a project `.venv`
- install `ruff` locally
- run `ruff check` experimentally without committing configuration
- decide whether to add a `ruff` config only after reviewing actual findings

That future slice should not:

- add `ruff` to package metadata without explicit approval
- add pre-commit hooks without explicit approval
- change runtime dependencies
- change MIDI, ports, active behavior, or hardware behavior

## 6. Safety Boundaries

Local tooling must not introduce:

- real MIDI
- `mido`
- port opening
- MIDI sending
- active execution
- runtime execution
- hardware behavior
- package metadata changes
- V1.34 reference changes

## 7. Environment variables

This section is the canonical index for every env var the project reads.
See [`docs/COCKPIT_QUICKSTART.md`](COCKPIT_QUICKSTART.md) for the
operator-facing walkthrough and [`docs/ARCHITECTURE.md` §6.5](ARCHITECTURE.md#65-cockpit-websocket-security-contract-post-code_reviewmd-sweep-2026-05) for the WebSocket security contract.

### Installer workflow variables (build only)

`installers.yml` sets `TAURI_CLI_VERSION=2.11.4` for its pinned prebuilt npm
CLI. Its Python build steps read `STUDIO_WINDOWS`, supplied by the boolean
`studio_windows` dispatch input (default false). When true, the workflow builds
only the Windows portable Cockpit and identifies its window/artifact by commit.
Neither variable is read by the shipped application or changes MIDI authority.
See [Building installers](BUILDING_INSTALLERS.md#identified-windows-cockpit-studio-copy).

### 7a. Cockpit sidecar / desktop shell (runtime)

| Env var | Default | Purpose |
|---|---|---|
| `RYTM_RAND_WS_PORT` | `4317` | Loopback port the Cockpit WebSocket binds. The Tauri shell passes the selected port to the frontend through per-launch bootstrap; the frontend must use that port for its connection. |
| `RYTM_RAND_WS_TOKEN_FILE` | `~/.rytm-randomizer/cockpit-ws-token` | Path the sidecar writes the per-launch HMAC handshake token to (`0o600`). The Tauri shell sets this to a path under its app-data dir and reads the token back to seed the first WS frame. PR 1 (C1) of the CODE_REVIEW.md sweep. |
| `RYTM_RAND_WS_MAX_MESSAGE_BYTES` | `1048576` (1 MiB) | Per-message size cap for WebSocket frames; oversize frames are rejected before `json.loads`. PR 1 (SX1). |
| `WIZARD_SOURCE_ROOTS` | `~/.rytm-randomizer/wizard-sources` | `os.pathsep`-separated allow-list of root dirs the wizard's `WizardPathPolicy` will accept as `InspirationSource.location` values. Empty value falls back to the default so a typo never disables the policy. PR 2 (C2). |
| `RYTM_RAND_SIDECAR_BIN` | unset | Absolute path to a sidecar executable, read by the Tauri shell (`desktop/shell/src/sidecar.rs`). Highest-priority entry in the launch-resolution order: this override → bundled binary next to the executable / in the resource dir → a `python` on `PATH`. That last fallback is a **development** affordance (`cargo run` against a source checkout); a shipped bundle finds its bundled binary and never reaches it. |
| `RYTM_RAND_MIDI_BACKEND` | `auto` | `off` (case-insensitive) forces the `NullPortEnumerator`, so the cockpit boots with zero MIDI ports and the connection phase pinned at `searching`. Any other value behaves as `auto`. The deterministic escape hatch for CI / headless hosts and for a wedged OS MIDI service — python-rtmidi 1.5.8 can abort the whole process from its C++ layer when the OS MIDI client cannot be created (seen on macOS as `MidiInCore::initialize ... (-304)`), which no Python `except` can catch. Turning the backend off keeps the cockpit alive so the Connection Doctor can explain the situation. |
| `GITHUB_ACTIONS` | unset / false outside GitHub-hosted CI | Standard external-runner signal read only by the native A4 audio integration test. On Windows GitHub Actions the test skips the real decoder-plus-subprocess proof because the hosted runner cannot guarantee a stable native decoder process; unit coverage and crash-containment checks still run. Unset is the safe local and non-GitHub-runner default, and this variable never enables MIDI or hardware access. |

The frontend resolves its default WebSocket target on each dial, rather than
freezing it when the client is constructed. It first checks the shell-injected
`window.__RYTM_RAND_WS_PORT__`, then the `rytm-rand-ws-port` storage entry. A port
must be an integer from 1 through 65535, supplied as a number or a digits-only
string; invalid values cannot inject a host or path. If no injected port is valid
and storage supplies no valid port or cannot be read, the default is
`ws://127.0.0.1:4317/ws`. Discovered
ports always use `ws://127.0.0.1:<port>/ws`. These bootstrap/storage values are
not new environment variables. An explicit `CockpitClientOptions.url` wins
over discovery. `getUrl()` reports the actual target while a socket exists and
the next dial's resolved target while disconnected.

### 7b. Test / gate tooling (never set in production)

These control fixture capture and gate base-refs. The two `*_CAPTURE` vars
**rewrite committed golden files** — they are deliberate, reviewed acts, never
something to set to make a red gate go green.

| Env var | Default | Purpose |
|---|---|---|
| `RYTM_REPORT_GOLDEN_CAPTURE` | unset | `1` puts `scripts/capture_report_goldens.py` into capture mode, rewriting the byte-frozen report-command goldens that `tests/test_report_command_goldens.py` checks. Regenerate with `RYTM_REPORT_GOLDEN_CAPTURE=1 .venv/bin/python scripts/capture_report_goldens.py` and review the diff; a golden diff in an unrelated change set is a regression, not a refresh. |
| `RYTM_DATA_DUMP_CAPTURE` | unset | `1` puts `scripts/capture_data_layer_dumps.py` into capture mode, rewriting the data-layer dumps that `tests/test_data_layer_drift.py` guards. Same discipline as above: `RYTM_DATA_DUMP_CAPTURE=1 python scripts/capture_data_layer_dumps.py`, then review. |
| `TOUCHED_COV_BASE_REF` | `origin/modularize-v1.34` | Base ref for the Gate-1 touched-file coverage check (`scripts/check_touched_coverage.py`). Precedence: `GITHUB_BASE_REF` on PR events → this override → the default. Use it only to reproduce a real alternate integration target, never to narrow the touched-file set past a coverage failure (the sibling rule to `TYPECHECK_BASE_REF`, §"Incremental strict production typing"). |
| `TYPECHECK_BASE_REF` | `origin/modularize-v1.34` | Base ref for the strict-typing gate (`scripts/typecheck_touched.py`). Same precedence and same caveat — see §"Incremental strict production typing". |
| `PARITY_CAPTURE_MODE` | unset | `1` rewrites **every** V1.34 parity golden under `tests/fixtures/v134_parity/` from current engine output. A hard stop: it requires explicit maintainer go-ahead and its own isolated PR. See [`.claude/rules/parity-fixture-discipline.md`](../.claude/rules/parity-fixture-discipline.md). |
| `SOURCE_DATE_EPOCH` | unset | Optional Unix epoch used by the passive AL16 Rytm kit exporter to freeze manifest timestamps for reproducible evidence. When unset, the exporter uses Unix epoch 0 for deterministic evidence. It never enables MIDI or hardware access. |
| `RYTM_TEST_REFERENCE` | unset | Optional path to a private local initialized Analog Rytm saved-kit SysEx dump used only by the opt-in codec integration test. When unset, the test skips. Never commit the referenced dump; this variable does not enable MIDI or hardware access. |

### Desktop update and release configuration

Channel, freeze and beacon settings are resolved when the desktop shell starts.
The Updates panel displays those settings; change the environment and restart
rather than treating a local UI value as native configuration. None of these
settings grants MIDI or hardware-save authority.

| Variable/configuration | Unset/default | Reader and effect |
| --- | --- | --- |
| `RYTM_RAND_UPDATES` | Enabled | Shell launch: trimmed, case-insensitive `off` freezes checks, artifact downloads, installs and check-ins. Other values leave checking enabled. |
| `RYTM_RAND_UPDATE_BEACON` | Enabled when updates are enabled | Shell launch: `off` disables the separate check-in request; freeze takes precedence. |
| `RYTM_RAND_UPDATE_CHANNEL` | `stable` | Shell launch: accepts `stable`/`beta`, trimming and ignoring case; unknown values fall back to `stable`. |
| `RYTM_RAND_UPDATE_MANIFEST_URL` | `https://raw.githubusercontent.com/buzzijose-hub/RytmRandomizer/releases` | Base URL read for each check; appends the channel filename. Invalid values fall back. The parser accepts HTTPS and exact loopback HTTP hosts, rejects credentials/query/fragment, and does not bypass artifact or signature validation. The debug native fixture separately enables loopback HTTP transport. |
| `XDG_CONFIG_HOME`, `APPDATA`, `HOME`, `USERPROFILE` | First available, in that order; otherwise process temporary directory | Update state root: `XDG_CONFIG_HOME/RytmRandomizer`, else `APPDATA/RytmRandomizer`, else `(HOME or USERPROFILE)/.config/RytmRandomizer`, else `temp/RytmRandomizer`. Stores the local rollout ID and journal. |
| `TAURI_SIGNING_PUBLIC_KEY` | Empty | Actions repository variable, passed as the reusable workflow's public-key input and as an environment value to `release_artifacts.py`. Configures the actual bundled `tauri.conf.json`; a keyless client can discover metadata but cannot download or install artifacts. |
| `TAURI_SIGNING_PRIVATE_KEY` | Empty | Actions secret explicitly passed to the Tauri build. Without it, updater-artifact production is disabled; ordinary distributions can still build. Never commit this value. |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Empty | Optional password for the Tauri signing key, supplied only to the signing build. |
| `MINISIGN` | `minisign` on PATH | Executable used by `release_artifacts.py` for the genuine signature self-test and assembled-artifact verification. Missing verifier refuses signed assembly. |
| `RYTM_PUB_DATE` | No implicit current-time fallback | Lower-level `release_lib.py` manifest generation uses `--pub-date` first, then this RFC3339 timestamp; missing date refuses generation. The release assembly instead receives a reproducible source-commit epoch. |
| `RYTM_SIGNATURE_<TARGET>` | No signature for that target | Lower-level manifest generation reads a signature, e.g. `RYTM_SIGNATURE_WINDOWS_X86_64`; it does not generate one. With no signed targets it refuses. The release assembly reads and verifies actual signature sidecars. |
| `GITHUB_REPOSITORY` | Empty outside Actions | Artifact/provenance URL owner. Manifest generation requires it; fleet collection can use `--repo`. |
| `GITHUB_TOKEN` | Anonymous API access when absent | GitHub workflow/fleet access; never enters a client manifest, journal or check-in. |
| `GITHUB_SHA`, `GITHUB_RUN_ID`, `GITHUB_WORKFLOW_SHA` | Empty outside Actions; workflow SHA falls back to source SHA | Release source/run provenance. Explicit local artifact collection must supply valid source identity. |
| `GITHUB_STEP_SUMMARY`, `GITHUB_OUTPUT` | No extra output file | Optional Actions summary/output destinations. These do not enable application or hardware behavior. |

Workflow step-local variables such as `BUILD_REF`, `BUILD_SIGN`,
`BUILD_UPDATER_ARTIFACTS`, `RUNNER_OS_LABEL`, `UPDATER_REQUESTED`,
`DRY_RUN_INPUT`, `REF_TYPE`, `EVENT_NAME`, `INTEGRATION_BRANCH`, `PROMOTE_VERSION`, `PROMOTE_ROLLOUT_PERCENT`, `RELEASE_SIGNED` and `RELEASE_DRY_RUN` are bound from workflow
inputs or verified outputs, not desktop settings. Manual release dispatch
uses `dry_run=true` by default. Secret presence alone never establishes a
signed release: assembly verifies the collected bytes, signatures, version,
source and complete target set before setting `signed=true`.

The runtime verification key is bundled at `plugins.updater.pubkey` in
`desktop/shell/tauri.conf.json`; `RYTM_RAND_UPDATER_PUBKEY` is not read.
The old browser fixture's `RYTM_RAND_UPDATE_FORCED_INSTALL_ID`,
`RYTM_RAND_UPDATE_CURRENT_VERSION` and `RYTM_RAND_UPDATE_CONFIG_DIR` names
are not supported production overrides. Consent and skipped versions last
for the running process; the diagnostic journal does not restore them.

#### Native acceptance fixture (development only)

| Variable | Default | Purpose |
| --- | --- | --- |
| `RYTM_NATIVE_TEST_BINARY` | Unset: native runner refuses | Absolute path to the isolated debug shell built with `--features native-test`. |
| `PYTHON`, then `PYTHON_EXECUTABLE` | Unset: native runner refuses | Absolute existing Python executable for the fixture's passive sidecar. |
| `RYTM_RAND_NATIVE_TEST_CONFIG` | Unset: feature-enabled shell refuses | Runner-generated JSON configuration under its temporary root. Ordinary builds do not include this reader. |
| `RYTM_RAND_MIDI_BACKEND` | Fixture requires exactly `off` | Prevents real MIDI in native acceptance; the normal application's documented backend setting is unchanged. |
| `CI` | Unset/false locally | Native Playwright reporter and development-server reuse choice. |

The fixture supplies its own loopback origin, config/WebView roots, test
public key and rollout ID, and isolates terminal install/restart operations.
A `native-test` release build is rejected at compile time. Missing native
prerequisites fail rather than turn safety cases into skipped tests. The
September 8 checkpoint records 32 actual Wry/WebView2 cases passing in 53.9
seconds and strict native TypeScript passing. Terminal installation is recorded,
not performed against the operating system. See `desktop/web/native-e2e/README.md` for the recipe.

See [Building installers](BUILDING_INSTALLERS.md#verified-updater-release-assembly), [native acceptance](../desktop/web/native-e2e/README.md) and [the current closeout](superpowers/plans/2026-09-08-release-closeout.md).

## 8. Pre-push hook hardening (Windows Store python shim)

The repo's pre-push hook (`.githooks/pre-push`) runs `scripts/code_review_gate.py --mode git-hook` to enforce the mechanical gates. On Windows, the bare `python` / `py` / `python3` commands frequently resolve to the Windows Store shim under `%LOCALAPPDATA%\Microsoft\WindowsApps\` — those shim executables throw "specified disk or diskette cannot be accessed" when invoked from non-interactive subprocesses (which is exactly what a git hook is).

The pre-push hook has been hardened (PR #110, landed separately from the CODE_REVIEW.md bundle) to skip the Store shim and locate a real interpreter via:

1. `PYTHON` env var if set.
2. `where python` / `where python3` filtered to exclude paths matching `Microsoft\WindowsApps`.
3. A scan of `%LOCALAPPDATA%\Programs\Python\` for an installed Python.
4. Falling back to the venv's interpreter (`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` elsewhere) when present.

The same pattern is documented in `.claude/skills/python-on-windows/SKILL.md`. Any new shell-driven tooling (CI scripts, hooks, just recipes) should consult that skill before invoking `python` directly on Windows.

### Native audio test subprocess controls

The real tone/noise integration proof passes these variables as `1` only to its
isolated CLI subprocess: `BLIS_NUM_THREADS`, `MKL_NUM_THREADS`,
`NUMBA_NUM_THREADS`, `NUMEXPR_NUM_THREADS`, `OMP_NUM_THREADS`,
`OPENBLAS_NUM_THREADS`, and `VECLIB_MAXIMUM_THREADS`. They prevent native math
libraries from creating a second thread pool under pytest-xdist. They are test
controls, not runtime configuration, and do not affect MIDI or hardware.

Production A4 audio inference also isolates native decoding in a spawned child
process. The parent owns the private audio and SysEx staging directory, converts
an abnormal child exit into a bounded `inference_failed` result, and removes
that staging directory on failure. The Windows native decoder may still fail
safely in this test; crash containment and cleanup are verified, but reliable
Windows decoding is not claimed.

## 9. Next Project Task

The next project task remains:

- docs-only review/acceptance gate for the selected target state implementation

Tooling should stay in service of that work, not replace it.

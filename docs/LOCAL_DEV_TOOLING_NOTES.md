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

### 7a. Cockpit sidecar / desktop shell (runtime)

| Env var | Default | Purpose |
|---|---|---|
| `RYTM_RAND_WS_PORT` | `4317` | Loopback port the cockpit WebSocket binds. |
| `RYTM_RAND_WS_TOKEN_FILE` | `~/.rytm-randomizer/cockpit-ws-token` | Path the sidecar writes the per-launch HMAC handshake token to (`0o600`). The Tauri shell sets this to a path under its app-data dir and reads the token back to seed the first WS frame. PR 1 (C1) of the CODE_REVIEW.md sweep. |
| `RYTM_RAND_WS_MAX_MESSAGE_BYTES` | `1048576` (1 MiB) | Per-message size cap for WebSocket frames; oversize frames are rejected before `json.loads`. PR 1 (SX1). |
| `WIZARD_SOURCE_ROOTS` | `~/.rytm-randomizer/wizard-sources` | `os.pathsep`-separated allow-list of root dirs the wizard's `WizardPathPolicy` will accept as `InspirationSource.location` values. Empty value falls back to the default so a typo never disables the policy. PR 2 (C2). |
| `RYTM_RAND_SIDECAR_BIN` | unset | Absolute path to a sidecar executable, read by the Tauri shell (`desktop/shell/src/sidecar.rs`). Highest-priority entry in the launch-resolution order: this override → bundled binary next to the executable / in the resource dir → a `python` on `PATH`. That last fallback is a **development** affordance (`cargo run` against a source checkout); a shipped bundle finds its bundled binary and never reaches it. |
| `RYTM_RAND_MIDI_BACKEND` | `auto` | `off` (case-insensitive) forces the `NullPortEnumerator`, so the cockpit boots with zero MIDI ports and the connection phase pinned at `searching`. Any other value behaves as `auto`. The deterministic escape hatch for CI / headless hosts and for a wedged OS MIDI service — python-rtmidi 1.5.8 can abort the whole process from its C++ layer when the OS MIDI client cannot be created (seen on macOS as `MidiInCore::initialize ... (-304)`), which no Python `except` can catch. Turning the backend off keeps the cockpit alive so the Connection Doctor can explain the situation. |
| `GITHUB_ACTIONS` | unset / false outside GitHub-hosted CI | Standard external-runner signal read only by the native A4 audio integration test. On Windows GitHub Actions the test skips the real decoder-plus-subprocess proof because the hosted runner cannot guarantee a stable native decoder process; unit coverage and crash-containment checks still run. Unset is the safe local and non-GitHub-runner default, and this variable never enables MIDI or hardware access. |

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

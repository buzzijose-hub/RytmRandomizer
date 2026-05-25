# Local Dev Tooling Notes

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

## 7. Cockpit env vars

The cockpit sidecar now reads four env vars at boot. See [`docs/COCKPIT_QUICKSTART.md`](COCKPIT_QUICKSTART.md) for the operator-facing walkthrough and [`docs/ARCHITECTURE.md` §6.5](ARCHITECTURE.md#65-cockpit-websocket-security-contract-post-code_reviewmd-sweep-2026-05) for the contract.

| Env var | Default | Purpose |
|---|---|---|
| `RYTM_RAND_WS_PORT` | `4317` | Loopback port the cockpit WebSocket binds. |
| `RYTM_RAND_WS_TOKEN_FILE` | `~/.rytm-randomizer/cockpit-ws-token` | Path the sidecar writes the per-launch HMAC handshake token to (`0o600`). The Tauri shell sets this to a path under its app-data dir and reads the token back to seed the first WS frame. PR 1 (C1) of the CODE_REVIEW.md sweep. |
| `RYTM_RAND_WS_MAX_MESSAGE_BYTES` | `1048576` (1 MiB) | Per-message size cap for WebSocket frames; oversize frames are rejected before `json.loads`. PR 1 (SX1). |
| `WIZARD_SOURCE_ROOTS` | `~/.rytm-randomizer/wizard-sources` | `os.pathsep`-separated allow-list of root dirs the wizard's `WizardPathPolicy` will accept as `InspirationSource.location` values. Empty value falls back to the default so a typo never disables the policy. PR 2 (C2). |

## 8. Pre-push hook hardening (Windows Store python shim)

The repo's pre-push hook (`.githooks/pre-push`) runs `scripts/code_review_gate.py --mode git-hook` to enforce the mechanical gates. On Windows, the bare `python` / `py` / `python3` commands frequently resolve to the Windows Store shim under `%LOCALAPPDATA%\Microsoft\WindowsApps\` — those shim executables throw "specified disk or diskette cannot be accessed" when invoked from non-interactive subprocesses (which is exactly what a git hook is).

The pre-push hook has been hardened (PR #110, landed separately from the CODE_REVIEW.md bundle) to skip the Store shim and locate a real interpreter via:

1. `PYTHON` env var if set.
2. `where python` / `where python3` filtered to exclude paths matching `Microsoft\WindowsApps`.
3. A scan of `%LOCALAPPDATA%\Programs\Python\` for an installed Python.
4. Falling back to the venv's interpreter (`.venv/Scripts/python.exe` on Windows, `.venv/bin/python` elsewhere) when present.

The same pattern is documented in `.claude/skills/python-on-windows/SKILL.md`. Any new shell-driven tooling (CI scripts, hooks, just recipes) should consult that skill before invoking `python` directly on Windows.

## 9. Next Project Task

The next project task remains:

- docs-only review/acceptance gate for the selected target state implementation

Tooling should stay in service of that work, not replace it.

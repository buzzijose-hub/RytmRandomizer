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

## 7. Reserved Future Cockpit Env Var

`RYTM_RAND_WS_PORT` is reserved for a future cockpit Python sidecar/WebSocket
port. The current runtime does not read this variable, start a server, open a
port, launch a GUI, or send MIDI because of it.

Before any future implementation reads `RYTM_RAND_WS_PORT`, the PR must document:

- the default port
- valid override values
- local developer setup
- CI behavior
- installer behavior
- how the existing Python CLI remains passive and dependency-light

## 8. Next Project Task

The next project task remains:

- docs-only review/acceptance gate for the selected target state implementation

Tooling should stay in service of that work, not replace it.

# CLAUDE.md — repo-level system prompt for Claude Code

> This file is automatically loaded by Claude Code at the start of every
> session in this repository. It exists alongside [`AGENTS.md`](AGENTS.md)
> (which is the GitHub-convention agent index) so Claude Code's automatic
> context injection picks up the conventions whether or not the user
> explicitly references AGENTS.md.

## Read order at session start

1. **This file** — operational guardrails.
2. **[`AGENTS.md`](AGENTS.md)** — folder map, test commands, anti-patterns, cross-reference index.
3. **[`agent-memory/INDEX.md`](agent-memory/INDEX.md)** — shared agent memory (workflow feedback, project facts, reference). Same shape as Claude Code's local memory (`~/.claude/projects/<id>/memory/`); the in-repo store is the canonical version so every agent on every machine reads the same observations. Individual memories are read on demand when their `description` matches the current task.
4. **[`CONTRIBUTING.md`](CONTRIBUTING.md)** — full developer handbook (read on demand; AGENTS.md links into the right sections).
5. **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** + **[`docs/ARCHITECTURE_DIAGRAMS.md`](docs/ARCHITECTURE_DIAGRAMS.md)** — architecture standard + current Mermaid maps.
6. **[`.claude/rules/`](.claude/rules/)** — mandatory rules (architecture, autonomous execution, cascade bundling, codex contribution, coverage, Device/strategy, hardware pins, live-but-passive MIDI, parallel-agent composition, parallelization, parity, PR-body conformance, README freshness, skill routing, and targeted-mutation safety).
7. **[`.claude/skills/`](.claude/skills/)** — repo-specific and learned task skills, invokable via `/<skill-name>`.

## Operational guardrails — apply on every task

### Hard rules (never bend without explicit user approval)

1. **V1.34 parity is byte-frozen.** Never regenerate `tests/fixtures/v134_parity/*.json` without `PARITY_CAPTURE_MODE=1` and the user's explicit go-ahead. 505 JSON files; 685 parametrized pytest test items. See [`.claude/rules/parity-fixture-discipline.md`](.claude/rules/parity-fixture-discipline.md).
2. **`mido==1.3.3` and `python-rtmidi==1.5.8` are pinned.** Do not bump even for CVEs. See [`.claude/rules/hardware-pinned-packages.md`](.claude/rules/hardware-pinned-packages.md).
3. **No stacked PRs.** A PR's base must be the integration branch (`modularize-v1.34` until `main` lands), not another open PR's head. See [`.claude/rules/cascade-merge-pattern.md`](.claude/rules/cascade-merge-pattern.md).
4. **No new top-level modules** under `rytm_randomizer/`. Use a subpackage. Enforced by `test_no_new_top_level_modules.py`.
5. **No new sibling device subpackages.** Adding an Elektron device family = one `devices/<family>.py` + three strategy modules under `devices/strategies/`. See [`.claude/rules/device-protocol-strategy.md`](.claude/rules/device-protocol-strategy.md).
6. **No bare `Any`.** Use `Protocol`, generic dataclasses, or explicit types.
7. **MIDI import boundary.** `mido`/`python-rtmidi` import only inside `real_midi_adapter.py`, `mido_provider.py`, and (lazily, in-method) `midi_io.py`. Top-level `mido` imports are banned everywhere. Enforced repo-wide by `tests/architecture/test_repo_root_perimeter.py`.
8. **Live-but-Passive MIDI.** Launch may enumerate ports and open MIDI **inputs** freely (read-only listening — never interrupts device sound output). Every **cockpit** output/transmit routes through the `senders` ArmedApply seam behind an explicit in-UI arm + per-action confirmation, and never auto-re-arms after reconnect. This is a cockpit/live-surface guarantee, **not repo-wide**: exactly one module is exempt — the legacy V1.34 CLI entry point `app.py` (10 `open_output` sites), which opens its own output ports under the CLI's `--arm` discipline and is named in the shrinking allowlist `_LEGACY_V134_TRANSMIT_MODULES` in `tests/architecture/test_armed_entry_points.py`. It cannot be re-pointed at the seam as-is: `app.py` sends via `midi_io.send_cc` (which paces each message by `MIDI_MESSAGE_SETTLE_SECONDS` and records `record_cc_sent`) whereas the seam writes raw triples unpaced, so migrating would change observable wire timing. `shell.py` came OFF the list — it never transmitted; its two "sites" were docstring prose quoting the monolith. Persistent kit/sound writes are **refused** (`KitMutationUnsupportedError`) because real capture-before-write and restore do not exist; only RAM-only live-dial CC/NRPN sends are permitted. Enforced by `tests/architecture/test_armed_entry_points.py` + `test_repo_root_perimeter.py`. See [`.claude/rules/live-but-passive-midi.md`](.claude/rules/live-but-passive-midi.md).
9. **No `--no-verify`.** Never bypass pre-commit hooks. Fix the underlying issue.
10. **PR body must include the 18-gate conformance checklist.** See [`.claude/rules/pr-body-conformance-checklist.md`](.claude/rules/pr-body-conformance-checklist.md).
11. **Do not pause on chained steps.** Once a multi-step task is approved, execute through to a hard stop (push, PR open, merge, force-push, dep bump, fixture regen). Hard stops are enumerated in [`.claude/rules/autonomous-agent-execution.md`](.claude/rules/autonomous-agent-execution.md).
12. **Dispatch independent work in parallel.** Batch independent reads, searches, and subagent invocations into a single message. See [`.claude/rules/maximize-parallelization.md`](.claude/rules/maximize-parallelization.md).
13. **Parallel agents: a green report that did not run is a RED report.** Verify composition, not just each agent. Parse the runner's summary (collection errors / skips / zero-collected), fail cross-track guards closed, take one integration checkpoint at first cross-agent import, and give every cross-language seam a drift guard naming the CALL FORM. See [`.claude/rules/parallel-agent-composition.md`](.claude/rules/parallel-agent-composition.md).
14. **On `codex/*` branches, follow the codex contribution guide.** Cascade ordering, redo-branch discipline, and PR-body provenance differ from normal feature branches. See [`.claude/rules/codex-contribution-guide.md`](.claude/rules/codex-contribution-guide.md).

### Tool defaults

- **Running tests:** `python -m pytest` (default `-n auto` xdist parallelization). Never `-o addopts=''` outside `PARITY_CAPTURE_MODE=1` — 3× slowdown.
- **Lint:** `python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .` (must all pass before push).
- **Task runner:** prefer `just <task>` if [`Justfile`](Justfile) is present (`just test`, `just fast`, `just lint`, `just check`, `just pr`).
- **PRs:** `python scripts/create_pr.py --title "..." --body-file path/to/body.md` so `edward-rosado` is requested automatically. Raw fallback: `gh pr create --base modularize-v1.34 --reviewer edward-rosado --title "..." --body-file path/to/body.md`. Body must include conformance checklist.

### Default to small reversible changes

- Editing files / running tests = freely allowed.
- Pushing branches / opening PRs / commenting on PRs / merging = always confirm with user first unless they explicitly authorized the broader action.
- Force-pushing, deleting branches, dropping CODEOWNERS approval, bumping pinned deps = refuse without explicit user instruction.

### When in doubt

1. Search `.claude/rules/` and `.claude/skills/` first.
2. Then `CONTRIBUTING.md` + `AGENTS.md`.
3. Then `docs/ARCHITECTURE.md` + `docs/ARCHITECTURE_DIAGRAMS.md`.
4. Then ask the user.

## What's NEW relative to typical Python projects

This repo has unusually strict invariants because it talks to physical hardware (Elektron Analog Rytm MK2). Key surprises that bite agents who skip the read order:

- **685/505 distinction.** "685 parity tests" = pytest items; "505 goldens" = JSON files (parametrized).
- **`-o addopts=''` is a 3× speed trap.** The pyproject default of `-n auto` is the fast path; don't override it.
- **CONTRIBUTING.md's 18 plan-requirement gates** are mandatory in every PR body. The PR template (`.github/PULL_REQUEST_TEMPLATE.md`) auto-fills the structure.
- **The Strategy seam on `Device`** (PR #43) is the canonical cross-machine abstraction. The codex dual-machine cascade (PRs #21, #36-#41) is closed; PR #36 is the redo target.
- **Parallel agent runs are verified at the seams, not per agent.** Eleven individually-green agents produced 21 merge failures; the worked example and its seven blockers are in [`docs/AUTOUPDATE_PARALLEL_RUN_REPORT.md`](docs/AUTOUPDATE_PARALLEL_RUN_REPORT.md).
- **macOS is dropped from the PR-event CI matrix by design** (queue waits). It runs on push events. See `.github/workflows/test.yml:288-296`.

## How to know which skill applies

The [`.claude/rules/skill-routing.md`](.claude/rules/skill-routing.md) table maps task types to specific skills. For example: adding a CC parameter → `add-pad-command`; adding a data table → `extend-data-layer`; reviewing code post-push → `code-review`; updating docs → `docs-update-with-pr`. See [`docs/AGENT_TASK_RECIPES.md`](docs/AGENT_TASK_RECIPES.md) for step-by-step recipes for the most common tasks.

## Anti-patterns to refuse

Refuse these patterns by default; require explicit user override to proceed.

1. **Stacked PRs.** Basing a PR on another open PR's head instead of the integration branch. See cascade-merge-pattern.
2. **Parallel sibling device subpackages.** Adding `devices/<family>/` as a new subpackage instead of one `devices/<family>.py` + three strategies. See device-protocol-strategy.
3. **Cross-family private imports.** Importing `_internal`/underscore-prefixed names across device families or layer boundaries. See architecture + device-protocol-strategy.
4. **Fork envelope helpers.** Duplicating SysEx envelope helpers per device family instead of routing through the shared strategy seam. See device-protocol-strategy.
5. **Bare `Any` in new code.** Use `Protocol`, generic dataclasses, or explicit types instead.
6. **`--no-verify` on commits or pushes.** Pre-commit hooks must pass; fix the underlying issue.
7. **Suppressing xdist with `-o addopts=''` outside parity capture.** 3× slowdown trap; only valid under `PARITY_CAPTURE_MODE=1`. See parity-fixture-discipline.
8. **Bumping `mido` / `python-rtmidi` pins.** Pinned for hardware compatibility, not security. See hardware-pinned-packages.
9. **Regenerating parity fixtures without `PARITY_CAPTURE_MODE=1` and user go-ahead.** See parity-fixture-discipline.
10. **Pausing mid-cascade to re-confirm previously approved steps.** Run to a hard stop. See autonomous-agent-execution.

---

This file is kept short on purpose. The full context lives in CONTRIBUTING + AGENTS + the rules / skills / diagrams. Update this file only when a new project-wide guardrail lands.

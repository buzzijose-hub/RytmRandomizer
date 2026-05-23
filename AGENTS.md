# AGENTS.md — RytmRandomizer agent guide

> One-page entry point for AI agents (Claude Code, codex, etc.) doing work in this repo.
> Humans should read [`CONTRIBUTING.md`](CONTRIBUTING.md) first; this file is a navigation index, not a replacement.

> **Looking for the fastest path to a working PR?** Read [`docs/AGENT_TASK_RECIPES.md`](docs/AGENT_TASK_RECIPES.md) — 10 step-by-step recipes for the most common tasks (add a pad command, extend the data layer, add an Elektron device family, regenerate parity fixtures, bundle a multi-WS PR, etc.). Each recipe links back here for the rules it enforces.

## For codex-namespace branches

If you are operating under the OpenAI `codex` agent (or any agent working on a `codex/...` branch), read these **before any other action**:

- [`.claude/rules/codex-contribution-guide.md`](.claude/rules/codex-contribution-guide.md) — codex-specific pre-flight checklist mapping past anti-patterns (stacked PR cascades, parallel sibling subpackages, cross-family private-API imports, oversized PRs without a plan doc, missing 18-gate conformance checklist) to the rule that catches them.
- [`docs/CODEX_CONTRIBUTING.md`](docs/CODEX_CONTRIBUTING.md) — the longer codex-facing contribution guide with concrete fix recipes for each anti-pattern. (Authored separately; may not yet exist at the time you read this — check the link.)

All other agents (Claude Code, etc.) follow the same rules; the codex guide simply surfaces the specific patterns codex has historically gotten wrong on this repo.

### Post-push code review — automatic for codex, zero setup

The code review runs **automatically after every `git push`** — no manual step. Codex reads [`.codex/hooks.json`](.codex/hooks.json) from the repo root automatically (the codex analogue of Claude Code's `.claude/settings.json`). Its `PostToolUse` hook runs [`scripts/code_review_gate.py`](scripts/code_review_gate.py), which executes the mechanical gates (lint + architecture + V1.34 parity) and then — via the hook's `additionalContext` channel — **re-prompts you to run the review as one targeted agent per dimension** (per the "Execution model" section of [`.claude/skills/code-review/SKILL.md`](.claude/skills/code-review/SKILL.md)) — not one wide agent. Each dimension agent covers its slice (architecture, house style, parity/tests, side effects, observability, abstraction reuse, docs freshness, and string-literal/env/maintainability/learning). When the hook re-prompts you, run the fan-out, **synthesize the per-dimension findings**, and **post the consolidated verdict (with the Abstraction and Docs sections) as a PR comment.**

A second backstop: [`.githooks/pre-push`](.githooks/pre-push) runs the mechanical gates on *every* `git push` (any tool) and blocks the push if they fail. It is activated by `git config core.hooksPath .githooks`, which `just install` and the dev container run for you — so after `just install` the gate is live.

You can also run the full review on demand with `just review` (it env-detects the agent and dispatches it — no copy-paste). Full rationale, the 4-layer enforcement model, and how to disable a hook locally: [`docs/CODE_REVIEW_HOOK_SETUP.md`](docs/CODE_REVIEW_HOOK_SETUP.md).

### Skills — codex auto-discovers them from `.agents/skills/`

This repo's reusable "learned skills" live in [`.claude/skills/learned/`](.claude/skills/learned/) (Claude Code's location). Codex does **not** read `.claude/skills/` — it scans `$REPO_ROOT/.agents/skills/`. So the repo ships a symlink: **`.agents/skills` → `.claude/skills/learned`**. Codex auto-discovers every learned skill through it (the `SKILL.md` + frontmatter format is identical for both agents), and the model auto-invokes a skill when your task matches its `description`. One source of truth — edit a skill in `.claude/skills/learned/`, and codex sees the change.

**One-time setup if the symlink did not materialize.** The symlink is committed as a git symlink (mode `120000`). On Linux/macOS and in the dev container it checks out as a real symlink automatically. On a Windows clone with `core.symlinks=false` it may check out as a plain text file containing `../.claude/skills/learned` — if so, enable symlinks and re-check-out:

```bash
git config core.symlinks true
git checkout -- .agents/skills      # re-materialize as a real symlink
# (Windows may also need Developer Mode enabled, or run the shell as admin.)
```

Verify with `ls .agents/skills/` — it should list the learned-skill directories. If your environment genuinely cannot use symlinks, read the skills directly from [`.claude/skills/learned/`](.claude/skills/learned/); the catalog is in [`CONTRIBUTING.md` § Skill catalog](CONTRIBUTING.md#skill-catalog).

## Before you do anything

1. **Read [`CONTRIBUTING.md`](CONTRIBUTING.md)** — the developer handbook. It has 22 sections; the most load-bearing are:
   - § **Strict rules — non-negotiables** (15 hard rules every PR must satisfy)
   - § **Plan requirements — the 18 gates every PR must satisfy**
   - § **PR bundling — one PR per logical change, not per commit**
   - § **Running tests fast** (the inner-loop pytest commands; **do not suppress `pytest-xdist` with `-o addopts=''`** unless you are in `PARITY_CAPTURE_MODE=1` — it's a 3× slowdown)
2. **Skim [`docs/ARCHITECTURE.md` §6](docs/ARCHITECTURE.md#6-where-to-put-new-work)** — the "Where to put new work" table maps every change type to (module, skill).
3. **Look at [`docs/ARCHITECTURE_DIAGRAMS.md`](docs/ARCHITECTURE_DIAGRAMS.md)** — 27 mermaid diagrams. The most important ones up front:
   - §1 Repository-Level System Map · §2 Package Layer Map (orient yourself)
   - §3 Device + Strategy Capability Stack · §4 Snapshot → Plan → Render Lifecycle (the cross-machine abstraction)
   - §10 Architecture Test Enforcement Graph (what CI mechanically rejects)
   - §17 Cascade vs Bundled PR Flow (don't open stacked PRs)
   - §18 Future Codex PR Shape (target shape for dual-machine redo)
4. **Inspect [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md)** — the 18 gates. Every PR body must include a conformance checklist.

## What you must know about this codebase

| Fact | Implication |
|---|---|
| **V1.34 parity is byte-frozen.** 505 JSON golden files at `tests/fixtures/v134_parity/` (parametrized into 685 pytest test items). | Any change that alters byte-for-byte output of `Pad{1-4}Engine`, `group_runner`, or `scene_runner` fails parity. Regenerate fixtures ONLY with `PARITY_CAPTURE_MODE=1` and explicit approval. |
| **Hardware-pinned packages.** `mido==1.3.3`, `python-rtmidi==1.5.8`. | Do not bump even for CVEs. These versions encode the byte-level wire format the Analog Rytm MK2 accepts. |
| **Passive default.** `python -m rytm_randomizer.cli ...` must NEVER open a real port. | Only `python -m rytm_randomizer.app --arm` is allowed to touch real MIDI. Enforced by `test_real_midi_passive_cli_safety.py`. |
| **Lazy MIDI imports.** `mido` and `python-rtmidi` import lazily inside `real_midi_adapter.py` + `mido_provider.py`. | Never `import mido` at module top-level anywhere else. Enforced by `test_no_side_effects.py`. |
| **`Device` Protocol is the cross-machine boundary.** 9 attrs (5 identity + 4 capability strategies) + 4 convenience methods. | Adding an Elektron device family = one `devices/<family>.py` + three strategy modules under `devices/strategies/`. Do NOT create parallel sibling subpackages at the package root (`analog_four/`, `dual_machine/`). Enforced by `test_device_protocol_enforcement.py`. |
| **No `Any` escape hatches.** Use `Protocol`, generic dataclasses, or explicit types. | Enforced by `test_no_any_escape_hatches.py`. Allowlist is drained. |
| **No new top-level modules** under `rytm_randomizer/`. | Use a subpackage. Enforced by `test_no_new_top_level_modules.py`. |
| **CODEOWNERS-gated merges.** `@buzzijose-hub` must approve every PR. | Do not open stacked PRs (one PR's base = another open PR's head). Bundle multi-workstream work into one PR via an integration branch. |

## Folder map (where things live)

```
RytmRandomizer/
├─ AGENTS.md                       ← you are here
├─ CLAUDE.md                       ← per-session guardrails for Claude Code (mirrors the hard rules)
├─ CONTRIBUTING.md                 ← developer handbook (read first)
├─ README.md
├─ CHANGELOG.md
├─ Justfile                        ← task runner (`just check`, `just test`, `just lint`, `just review`, `just pr`, `just watch`)
├─ pyproject.toml                  ← deps + pytest addopts (-n auto)
├─ .coveragerc                     ← coverage ratchet floor
├─ .pre-commit-config.yaml
├─ .python-version
├─ .gitattributes                  ← line-ending + diff rules (keeps fixtures byte-stable cross-platform)
├─ .devcontainer/
│  └─ devcontainer.json            ← reproducible dev container (matches CI Python + tooling)
│
├─ rytm_randomizer/                ← the package (10 subpackages, 86 modules)
│  ├─ app.py                       ← entry point (--arm / --dry-run / passive)
│  ├─ cli.py                       ← passive CLI
│  ├─ shell.py                     ← interactive shell
│  ├─ midi_io.py                   ← MIDI primitives (send_cc, send_param)
│  ├─ real_midi_adapter.py         ← real MIDI boundary (lazy mido)
│  ├─ mido_provider.py             ← mido lazy-import provider
│  ├─ mock_midi.py                 ← MockMidiSender for tests
│  ├─ randomization.py             ← randomization core
│  ├─ scene_runner.py + group_runner.py
│  ├─ behavior/                    ← 8 modules; passive evaluators
│  ├─ data/                        ← single source of truth (param_maps, profiles, scenes, modes, plans)
│  ├─ devices/                     ← Device Protocol + registry + AnalogRytmDevice
│  │  └─ strategies/               ← per-device strategy implementations
│  ├─ engines/                     ← Pad{1-4}Engine + _runtime mixins
│  ├─ guardrails/                  ← safety/policy layer (resolver, store, schema, validation)
│  ├─ observability/               ← logging, tracing, metrics, errors
│  ├─ reports/                     ← passive read-only reports
│  ├─ snapshot/                    ← Elektron SysEx envelope + WS-S6 Protocols
│  ├─ state/                       ← state dataclasses + validators
│  └─ style_analysis/
│
├─ tests/
│  ├─ test_*.py                    ← unit / behavior / device tests
│  ├─ architecture/                ← 15 mechanical-enforcement tests
│  ├─ fixtures/v134_parity/        ← 505 byte-frozen JSON goldens
│  ├─ conftest.py                  ← shared fixtures (Gate 11)
│  └─ _parity_worker.py            ← capture/diff modes
│
├─ scripts/                        ← Python cross-platform tools (preferred)
│  ├─ closeout_check.py
│  ├─ code_review_gate.py          ← shared mechanical review gate (cli / codex-hook / git-hook modes)
│  ├─ coverage_check.py
│  └─ coverage_ratchet.py
├─ Scripts/                        ← PowerShell-only tools (Windows legacy)
│  └─ closeout_check.ps1
│
├─ .githooks/                      ← versioned git hooks (activate: git config core.hooksPath .githooks)
│  └─ pre-push                     ← runs the mechanical review gate on every push, any tool
│
├─ .codex/
│  └─ hooks.json                   ← codex PostToolUse hook — post-push code review (codex analogue of .claude/settings.json)
│
├─ .agents/
│  └─ skills                       ← symlink → .claude/skills/learned (so codex auto-discovers the learned skills)
│
├─ docs/
│  ├─ README.md                    ← doc index
│  ├─ ARCHITECTURE.md              ← architecture standard (§3 deps, §5 parity, §6 where to add, §6.1 Device+Strategy)
│  ├─ ARCHITECTURE_DIAGRAMS.md     ← 27 mermaid diagrams
│  ├─ PLAN_REQUIREMENTS.md         ← 18 mandatory gates
│  ├─ STATUS.md                    ← recent cleanup log (hand-authored, never appended)
│  ├─ OBSERVABILITY.md
│  ├─ COVERAGE_POLICY.md
│  ├─ BUILDING_INSTALLERS.md
│  ├─ MANUAL_HARDWARE_VALIDATION.md
│  ├─ LOCAL_DEV_TOOLING_NOTES.md
│  ├─ BRANCH_PROTECTION.md
│  ├─ V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md
│  ├─ STYLE_ANALYSIS.md
│  └─ archive/                     ← process exhaust (don't read on first pass)
│
└─ .claude/
   ├─ agents/                      ← agent role definitions (code-reviewer, etc.)
   ├─ rules/                       ← 11 mandatory rule files (read on every task)
   │  ├─ architecture.md                    ← agent-facing distillation of `docs/ARCHITECTURE.md` (layer order, direction rules)
   │  ├─ autonomous-agent-execution.md      ← drive chained tasks to completion without per-step confirmation
   │  ├─ cascade-merge-pattern.md           ← Gate 16 — bundle multi-WS work into one PR under approval-gated branches
   │  ├─ codex-contribution-guide.md        ← codex-specific pre-flight checklist (read for any `codex/...` branch)
   │  ├─ coverage-gate-100pct.md            ← Gate 1 — 100% branch coverage on touched files
   │  ├─ device-protocol-strategy.md        ← every Elektron device family routes through `devices/` + `devices/strategies/`
   │  ├─ hardware-pinned-packages.md        ← do not bump `mido==1.3.3` or `python-rtmidi==1.5.8` without hardware re-validation
   │  ├─ maximize-parallelization.md        ← dispatch independent tool calls / agents in one message, not serially
   │  ├─ parity-fixture-discipline.md       ← when/how to regenerate V1.34 fixtures (and when you absolutely must not)
   │  ├─ pr-body-conformance-checklist.md   ← every PR body carries the 18-gate + strict-rules checklist verbatim
   │  └─ skill-routing.md                   ← which skill applies to which task (consult before starting)
   ├─ settings.json                ← post-push code-reviewer hook config
   └─ skills/                      ← 19 task-specific skill files
      ├─ add-pad-command/SKILL.md       ← adding a V1.34-equivalent command
      ├─ extend-data-layer/SKILL.md     ← adding a new fact table
      ├─ code-review/SKILL.md           ← post-push code review pattern
      ├─ ci-workflow-invariants/SKILL.md
      ├─ coverage-ratchet/SKILL.md
      ├─ docs-update-with-pr/SKILL.md
      ├─ python-on-windows/SKILL.md     ← Windows PowerShell gotchas
      ├─ DataAnalysisGuardrails/SKILL.md
      ├─ MusicLibraryGuardrails/SKILL.md
      └─ learned/                       ← skills extracted from past runs (12 entries; codex reads them via the .agents/skills symlink)
```

## Test commands (use these, not your own)

```bash
# Default: full suite with xdist parallelization (~30s on 4+ cores)
python -m pytest

# Fast inner loop (skips 685 parity goldens; ~25s)
python -m pytest -m fast

# Architecture gate only (~10s; preflight before push)
python -m pytest tests/architecture/ -q

# One file (xdist worker spawn > test time; disable parallelism)
python -m pytest tests/test_foo.py -n 0

# Full suite with coverage (matches CI; slowest)
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing

# Lint trio (must all pass before push)
python -m ruff check . && \
python -m black --check --target-version=py311 . && \
python -m isort --profile black --check-only .

# Parity-fixture capture (ONLY when intentionally changing reference output)
PARITY_CAPTURE_MODE=1 python -m pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -o addopts=''
```

**Do not run** `pytest -o addopts=''` for normal work — it disables `-n auto` xdist and runs ~3× slower. The only legitimate use is the `PARITY_CAPTURE_MODE=1` capture path (concurrent xdist workers have a TOCTOU concern with the fixture writer).

## Skills you can invoke (`/<name>` in Claude Code)

| Skill | When |
|---|---|
| [`add-pad-command`](.claude/skills/add-pad-command/SKILL.md) | Adding a V1.34-equivalent shell command |
| [`extend-data-layer`](.claude/skills/extend-data-layer/SKILL.md) | Adding a new fact table to `data/` |
| [`code-review`](.claude/skills/code-review/SKILL.md) | Post-push standardized review |
| [`coverage-ratchet`](.claude/skills/coverage-ratchet/SKILL.md) | Updating the coverage floor |
| [`docs-update-with-pr`](.claude/skills/docs-update-with-pr/SKILL.md) | Updating docs as part of a PR |
| [`ci-workflow-invariants`](.claude/skills/ci-workflow-invariants/SKILL.md) | Editing `.github/workflows/*.yml` safely |
| [`python-on-windows`](.claude/skills/python-on-windows/SKILL.md) | Working around PowerShell gotchas |
| [`DataAnalysisGuardrails`](.claude/skills/DataAnalysisGuardrails/SKILL.md) | Safe data analysis (no hardware I/O) |
| [`MusicLibraryGuardrails`](.claude/skills/MusicLibraryGuardrails/SKILL.md) | Working with music-library data safely |

12 additional "learned" skills (extracted from past runs) live under `.claude/skills/learned/` — see [`CONTRIBUTING.md` § Skill catalog](CONTRIBUTING.md#skill-catalog) for the full table. Codex auto-discovers them via the `.agents/skills` → `.claude/skills/learned` symlink (see [§ Skills](#skills--codex-auto-discovers-them-from-agentsskills) above).

## How to open a PR (autonomous-agent compatible)

Prefer the `Justfile` task runner — it bundles the exact commands CI runs and keeps the agent path identical to the human path.

```bash
# 1. Branch off the integration target
git fetch origin
git checkout modularize-v1.34
git pull --ff-only
git checkout -b <type>/<short-slug>

# 2. Implement (TDD where applicable)
just watch            # optional: re-run fast tests on file change during inner-loop work

# 3. Verify locally (one command bundles tests + architecture gate + lint trio)
just check            # = `just test` + `just lint` (matches CI; the canonical pre-push gate)
# or run the pieces individually:
just test             # full pytest suite (with -n auto xdist parallelization)
just lint             # ruff + black --check + isort --check-only

# 4. Code review — REQUIRED. Claude Code's post-push hook does this
#    automatically; codex and other agents must run it explicitly.
just review           # lint + architecture + V1.34 parity (the mechanical gates)
                      # then walk the 8-step .claude/skills/code-review/SKILL.md by
                      # hand (Steps 7-8 are judgment calls) and post the verdict on
                      # the PR. See docs/CODE_REVIEW_HOOK_SETUP.md.

# 5. Push + open PR with conformance checklist
just pr               # prints the canonical helper command; run
                      # `python scripts/create_pr.py --title "..." --body-file path/to/body.md`
                      # so edward-rosado is requested automatically. After
                      # updating an existing PR, run
                      # `python scripts/create_pr.py --request-review-for <PR#>`.
```

If you need to fall back to raw commands (e.g., the dev container is unavailable), the underlying invocations are still:

```bash
python -m pytest
python -m pytest tests/architecture/ -q
python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .
git push -u origin <your-branch>
python scripts/create_pr.py --title "..." --body-file path/to/body.md
# Re-request review after updating an existing PR:
python scripts/create_pr.py --request-review-for <PR#>
# Raw fallback:
gh pr create --base modularize-v1.34 --reviewer edward-rosado --title "..." --body-file path/to/body.md
```

PR body must include (enforced by `.claude/rules/pr-body-conformance-checklist.md`):

- What changed and why
- Test plan (checklist of what was verified)
- Plan-requirements conformance checklist for all 18 gates (`[x]` or `[ ] Gate N — N/A: <reason>`)
- Strict-rules confirmation block (6 lines, all `[x]` for a normal PR)
- Link to any plan doc under `docs/superpowers/plans/`

## Cross-reference index

| If you need to know | Read |
|---|---|
| "What is this project?" | [`README.md`](README.md) |
| "How do I contribute?" | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| "Where do I add X?" | [`docs/ARCHITECTURE.md` §6](docs/ARCHITECTURE.md#6-where-to-put-new-work) |
| "What are the 18 mandatory gates?" | [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md) |
| "What does the architecture look like?" | [`docs/ARCHITECTURE_DIAGRAMS.md`](docs/ARCHITECTURE_DIAGRAMS.md) (27 mermaid diagrams) |
| "What's the latest project status?" | [`docs/STATUS.md`](docs/STATUS.md) |
| "How does observability work?" | [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) |
| "How does the V1.34 parity rule work?" | [`.claude/rules/parity-fixture-discipline.md`](.claude/rules/parity-fixture-discipline.md) |
| "Why isn't there an auto-merge?" | CODEOWNERS-gated; see [`docs/BRANCH_PROTECTION.md`](docs/BRANCH_PROTECTION.md) |
| "How do I build the installers?" | [`docs/BUILDING_INSTALLERS.md`](docs/BUILDING_INSTALLERS.md) |
| "What's the hardware-validation procedure?" | [`docs/MANUAL_HARDWARE_VALIDATION.md`](docs/MANUAL_HARDWARE_VALIDATION.md) |
| "What's a Device family + Strategy seam?" | [`docs/ARCHITECTURE.md` §6.1](docs/ARCHITECTURE.md#61-device-protocol--strategy-seam-ws-s5--strategy) + [`docs/ARCHITECTURE_DIAGRAMS.md` §§3-5, 18, 19](docs/ARCHITECTURE_DIAGRAMS.md#3-device--strategy-capability-stack-ws-s5--strategy) |

## Anti-patterns to refuse

If asked to do any of these, refuse and point at the relevant rule:

1. **Open a PR whose base is another open PR's head** (stacked PR cascade). See `.claude/rules/cascade-merge-pattern.md`.
2. **Add a new top-level module** under `rytm_randomizer/`. Use a subpackage. Enforced by `test_no_new_top_level_modules.py`.
3. **Create a parallel device subpackage** (`analog_four/`, `dual_machine/`, etc.) at the package root. Use `devices/<family>.py` + `devices/strategies/`. Enforced by `test_device_protocol_enforcement.py`.
4. **Bump `mido` or `python-rtmidi` versions** without explicit hardware-validation approval.
5. **Bypass pre-commit hooks** with `--no-verify` / `--no-gpg-sign`. Fix the underlying issue instead.
6. **Suppress `pytest-xdist`** with `-o addopts=''` for normal runs. Only `PARITY_CAPTURE_MODE=1` justifies it.
7. **Regenerate V1.34 parity fixtures** without explicit approval AND a documented reason.
8. **Use `Any` escape hatches** instead of Protocols / generic dataclasses.
9. **Import `mido`** at module top-level anywhere outside `real_midi_adapter.py` / `mido_provider.py`.
10. **Skip the conformance checklist** in a PR body.

---

This file is the agent-facing entry point. Humans should follow [`CONTRIBUTING.md`](CONTRIBUTING.md) which has more depth and explanation. Both are kept in sync by the docs-update process (`.claude/skills/docs-update-with-pr`).

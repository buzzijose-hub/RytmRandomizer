# AGENTS.md — RytmRandomizer agent guide

> One-page entry point for AI agents (Claude Code, codex, etc.) doing work in this repo.
> Humans should read [`CONTRIBUTING.md`](CONTRIBUTING.md) first; this file is a navigation index, not a replacement.

## Before you do anything

1. **Read [`CONTRIBUTING.md`](CONTRIBUTING.md)** — the developer handbook. It has 22 sections; the most load-bearing are:
   - § **Strict rules — non-negotiables** (15 hard rules every PR must satisfy)
   - § **Plan requirements — the 16 gates every PR must satisfy**
   - § **PR bundling — one PR per logical change, not per commit**
   - § **Running tests fast** (the inner-loop pytest commands; **do not suppress `pytest-xdist` with `-o addopts=''`** unless you are in `PARITY_CAPTURE_MODE=1` — it's a 3× slowdown)
2. **Skim [`docs/ARCHITECTURE.md` §6](docs/ARCHITECTURE.md#6-where-to-put-new-work)** — the "Where to put new work" table maps every change type to (module, skill).
3. **Look at [`docs/ARCHITECTURE_DIAGRAMS.md`](docs/ARCHITECTURE_DIAGRAMS.md)** — 27 mermaid diagrams. The most important ones up front:
   - §1 Repository-Level System Map · §2 Package Layer Map (orient yourself)
   - §3 Device + Strategy Capability Stack · §4 Snapshot → Plan → Render Lifecycle (the cross-machine abstraction)
   - §10 Architecture Test Enforcement Graph (what CI mechanically rejects)
   - §17 Cascade vs Bundled PR Flow (don't open stacked PRs)
   - §18 Future Codex PR Shape (target shape for dual-machine redo)
4. **Inspect [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md)** — the 16 gates. Every PR body must include a conformance checklist.

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
├─ CONTRIBUTING.md                 ← developer handbook (read first)
├─ README.md
├─ CHANGELOG.md
├─ pyproject.toml                  ← deps + pytest addopts (-n auto)
├─ .coveragerc                     ← coverage ratchet floor
├─ .pre-commit-config.yaml
├─ .python-version
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
│  ├─ coverage_check.py
│  └─ coverage_ratchet.py
├─ Scripts/                        ← PowerShell-only tools (Windows legacy)
│  └─ closeout_check.ps1
│
├─ docs/
│  ├─ README.md                    ← doc index
│  ├─ ARCHITECTURE.md              ← architecture standard (§3 deps, §5 parity, §6 where to add, §6.1 Device+Strategy)
│  ├─ ARCHITECTURE_DIAGRAMS.md     ← 27 mermaid diagrams
│  ├─ PLAN_REQUIREMENTS.md         ← 16 mandatory gates
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
   ├─ rules/                       ← 5 mandatory rule files (read on every task)
   │  ├─ architecture.md           ← agent-facing architecture distillation
   │  ├─ cascade-merge-pattern.md  ← Gate 16 — no stacked PRs under approval-gated branches
   │  ├─ coverage-gate-100pct.md   ← Gate 1 — coverage details
   │  ├─ parity-fixture-discipline.md ← when/how to regenerate V1.34 fixtures
   │  └─ skill-routing.md          ← which skill applies to which task
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
      └─ learned/                       ← skills extracted from past runs (10 entries)
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

10 additional "learned" skills (extracted from past runs) live under `.claude/skills/learned/` — see [`CONTRIBUTING.md` § Skill catalog](CONTRIBUTING.md#skill-catalog) for the full table.

## How to open a PR (autonomous-agent compatible)

```bash
# 1. Branch off the integration target
git fetch origin
git checkout modularize-v1.34
git pull --ff-only
git checkout -b <type>/<short-slug>

# 2. Implement (TDD where applicable)

# 3. Verify locally
python -m pytest
python -m pytest tests/architecture/ -q
python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .

# 4. Push
git push -u origin <your-branch>

# 5. Open PR with conformance checklist
gh pr create --base modularize-v1.34 --title "..." --body-file path/to/body.md
```

PR body must include:

- What changed and why
- Test plan (checklist of what was verified)
- Plan-requirements conformance checklist for all 16 gates (`[x]` or `[ ] N/A — reason`)
- Link to any plan doc under `docs/superpowers/plans/`

## Cross-reference index

| If you need to know | Read |
|---|---|
| "What is this project?" | [`README.md`](README.md) |
| "How do I contribute?" | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| "Where do I add X?" | [`docs/ARCHITECTURE.md` §6](docs/ARCHITECTURE.md#6-where-to-put-new-work) |
| "What are the 16 mandatory gates?" | [`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md) |
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

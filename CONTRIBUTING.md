# Contributing to RytmRandomizer

## Branching model

- `main` is the integration target. (The `main` branch is being created by a parallel workstream; until it lands, integration happens on the active modularization branch.)
- Do work on feature branches.
- Feature branches merge into the integration target via pull request — no direct pushes to the integration branch.

## Verification gate

Before opening a PR, run the verification gate:

```bash
pytest
```

All tests must pass. There is also `Scripts/closeout_check.ps1`, a PowerShell-only closeout check. A cross-platform equivalent is being added; until then, run the PowerShell script on Windows or rely on `pytest` elsewhere.

## Plan requirements — the 16 gates every PR must satisfy

[`docs/PLAN_REQUIREMENTS.md`](docs/PLAN_REQUIREMENTS.md) is the contract
for **every** non-trivial PR, not just an internal "plan" PR. It defines 16
gates covering coverage, V1.34 parity, lint/format/type cleanliness,
dead-code purge, docs updates, type-system hygiene, observability adoption,
test hygiene, module-organization hygiene, string-literal dispatch hygiene,
shared fixtures, `Final` constants, env-var docs, maintainability review,
learning capture, and execution shape.

**Before opening a PR**, read `docs/PLAN_REQUIREMENTS.md` and include a
conformance checklist in the PR body (one line per gate, `[x]` or `[ ]
N/A — reason`). PR #35 (the Wave-1 simplification bundle) is the canonical
example of a fully-conformant PR body.

Sub-rules and learned skills extend the 16 gates:

- [`.claude/rules/parity-fixture-discipline.md`](.claude/rules/parity-fixture-discipline.md) — when and how to regenerate V1.34 fixtures.
- [`.claude/rules/coverage-gate-100pct.md`](.claude/rules/coverage-gate-100pct.md) — Gate 1 details, including branch coverage and the per-file ratchet.
- [`.claude/rules/cascade-merge-pattern.md`](.claude/rules/cascade-merge-pattern.md) — Gate 16 enforcement for autonomous multi-WS runs.

Architecture-enforcement tests under `tests/architecture/` mechanically
verify a subset of these gates on every CI run; do not skip them locally.

## Common contributor tasks

For "where do I add X?" answers, the source of truth is
[`docs/ARCHITECTURE.md` §6](docs/ARCHITECTURE.md#6-where-to-put-new-work).
The table there maps change types to the right module and the right skill.

Quick links for the most common tasks:

- **Add a new V1.34-equivalent command** — `shell.py` dispatch + relevant
  runner/engine. Skill: `add-pad-command`.
- **Add a new fact table** — a new module under `rytm_randomizer/data/` plus
  the re-export in `__init__.py`. Skill: `extend-data-layer`.
- **Change MIDI primitives** — `midi_io.py`. Keep `mido` lazy. Requires
  architecture review.
- **Add a passive read-only report** — extend `reports/` (the post-WS-S4
  subpackage) and wire it through `cli.py`. The passive CLI never opens a
  MIDI port; see `docs/ARCHITECTURE.md` §2.

For the full list of change types, see `docs/ARCHITECTURE.md` §6.

The 16 plan-requirements gates that apply to every PR (not just the most
common task types listed above) are documented in the
[Plan requirements section](#plan-requirements--the-16-gates-every-pr-must-satisfy)
above.

## Preserve parity with the V1.34 reference

The V1.34 hardware-validated musical behavior is the baseline of truth. It was validated against the actual Analog Rytm MK2. **Any change must preserve parity with that behavior.**

As of Wave 4 / WS-O the modular package owns the interactive runtime end-to-end (`rytm_randomizer.app` -> `rytm_randomizer.shell`). The V1.34 monolith (`rytm_hybrid_randomizer_v134.py`) has been retired; its byte-for-byte reference behavior is preserved as JSON goldens under `tests/fixtures/v134_parity/` and asserted by the parity tests (`tests/test_engines_pad*`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`) via `tests/_parity_worker.py`.

Concretely:

- The committed JSON goldens under `tests/fixtures/v134_parity/` are the authoritative V1.34 reference. New behavior lives in the `rytm_randomizer/` package and is locked against the goldens by the parity tests. Regenerate fixtures with `PARITY_CAPTURE_MODE=1 pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py` only when an intentional reference-output change is being committed.
- The following are **not allowed** without explicit approval:
  - New MIDI CC mappings.
  - New pad profiles or machines.
  - Pads 5-12 expansion.
  - Parameter range changes.
  - Command behavior changes (the shell's command alphabet mirrors the V1.34 reference exactly).
- **Allowed:** further refactoring within the package; readability improvements that do not change behavior; new tests; documentation updates.
- Add tests when you split code. Test after each major split.

## Commit conventions

- Short, imperative summaries (e.g. `Split scene plans into scenes module`).
- Commit in small steps.

## PR bundling — one PR per logical change, not per commit

Commit in small steps, but open **one bundled PR** for related work rather
than a cascade of small PRs stacked on each other. The base branch
(`modularize-v1.34` until `main` lands) requires CODEOWNERS review on every
PR, so a 5-deep cascade is N approvals; a bundled PR is 1.

**Specifically:**

- If your change spans multiple workstreams (e.g. dual-machine = Rytm + A4 +
  shared orchestration), implement each workstream on its own feature branch
  in parallel, then bundle them into one integration branch via
  `git merge --no-ff` and open **one** PR. See
  [`.claude/rules/cascade-merge-pattern.md`](.claude/rules/cascade-merge-pattern.md)
  for the operational recipe.
- Do not open a PR whose base is another open PR's head (a "stacked PR"). If
  the second piece truly cannot land without the first, finish the first
  PR first; otherwise merge them in the source branch.
- **Exception:** if the base branch is unprotected (no CODEOWNERS gate), the
  per-PR cascade is fine — it gives independent revert capability and
  finer-grained reviewer attention. The bundling rule is specifically for
  approval-gated branches.

If you are an autonomous agent (codex, claude-code, etc.) wired to open
one PR per workstream under an approval-gated branch, **the orchestrator
configuration is wrong**, not the policy — fix it to bundle before merging
the next PR. The PR #35 run is the canonical example
([`docs/SIMPLIFICATION_RUN_REPORT.md`](docs/SIMPLIFICATION_RUN_REPORT.md)).

## Data vs code

Anything that is "a table of facts" — commands, parameters, scenes, pad profiles — should live as **data** (a dataclass registry or a data file), not as bespoke per-item functions. Prefer one generic handler driven by a registry over many near-identical hand-written functions.

## Definition of done includes docs

Any structural change must update the docs it affects. A change is not done until the `README.md`, this file, and any relevant `Docs/` entries reflect the new reality.

## Architecture standard

The codebase has a fixed architecture documented in `docs/ARCHITECTURE.md`
and enforced by tests under `tests/architecture/`. Read both before any
non-trivial change.

The agent-facing distillation lives in `.claude/rules/architecture.md` and the
skill-routing table is in `.claude/rules/skill-routing.md`. Repo-specific
skills (`code-review`, `add-pad-command`, `extend-data-layer`) live under
`.claude/skills/`.

### Verification gate (architecture)

Before opening a PR, in addition to the full suite:

```bash
pytest tests/architecture/ -q
```

This is also a required CI check (see `.github/workflows/test.yml`) and is
listed in `scripts/apply-branch-protection.sh`.

## Automated post-push code review

The repo-local `.claude/settings.json` configures a `PostToolUse` hook that
fires the `code-reviewer` agent (`.claude/agents/code-reviewer.md`) after any
`git push` invocation made through the Claude Code harness. The agent reads
the diff, runs the architecture gate (`pytest tests/architecture/`), and
returns a structured Critical / Important / Minor verdict.

**Harness fallback.** If your harness version does not yet support the
`Agent` action type for hooks, the hook is silently ignored. You can run the
same review manually:

```
/agent code-reviewer
```

or invoke the skill directly:

```
/skill code-review
```

The hook config is committed at `.claude/settings.json`; you can override it
locally in `.claude/settings.local.json` if you prefer a different trigger.

## Releasing

RytmRandomizer follows [Semantic Versioning](https://semver.org/). The release
process is defined and repeatable — there is **no version-in-filename** (the
old `v131` / `v132` / `v134` naming is historical only).

**Single source of version truth:** the `[project] version` field in
`pyproject.toml`. Nothing else declares the version.

To cut a release `vX.Y.Z`:

1. **Bump the version** — update `[project] version` in `pyproject.toml` to
   `X.Y.Z`.
2. **Update the changelog** — in `CHANGELOG.md`, move the entries under
   `## [Unreleased]` into a new `## [X.Y.Z] - YYYY-MM-DD` section, leave fresh
   empty `Added` / `Changed` / `Fixed` subsections under `[Unreleased]`, and
   update the link references at the bottom of the file.
3. **Commit** the `pyproject.toml` and `CHANGELOG.md` changes (e.g.
   `Release vX.Y.Z`).
4. **Tag** the commit: `git tag vX.Y.Z`.
5. **Push the tag**: `git push origin vX.Y.Z`.

Pushing a `v*` tag triggers `.github/workflows/release.yml`, which builds the
wheel + sdist from `pyproject.toml`, runs the `pytest` gate (a release cannot
ship if tests fail), and publishes a GitHub Release with the `dist/*` artifacts
attached.

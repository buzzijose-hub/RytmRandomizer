# Skill routing

> "If you are doing X, use skill Y." Agents working on this repo MUST consult
> this table before starting a change.

## Routing table

| Trigger / request                                                            | Skill                              | Notes                                                                                                                                  |
| ---------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Python invocation **on a Windows machine only**                              | `python-on-windows`                | Windows-only: the Windows Store ships `python.exe` shims that crash from non-interactive subprocesses. This repo currently develops on macOS — just use the repo venv interpreter (`.venv/bin/python`). See `.claude/skills/python-on-windows/SKILL.md`. |
| "Add a pad command", "wire up a new V1.34 command", "extend the shell"        | `add-pad-command`                  | Touches `shell.py` (dispatch) + the relevant runner / engine + tests. Do not bypass the architecture rules.                            |
| "Add a new fact table", "extend the data layer", "add a profile / scene"      | `extend-data-layer`                | New facts live ONLY under `data/`. Re-export through `data/__init__.py`. Update `tests/test_data_layer.py` drift-guard.                |
| "Review this code", "is this PR good?", "look at my diff"                     | `code-review`                      | Auto-invoked by the description (see SKILL frontmatter). Produces Critical / Important / Minor + verdict.                              |
| "Refactor", "change architecture", "move a module", "rename layer"            | (consult `architecture.md`)        | Read `docs/ARCHITECTURE.md` and `.claude/rules/architecture.md` FIRST. Run `pytest tests/architecture/` after any change.                |
| "Analyze track / library / 'rolling techno' / style description"              | `MusicLibraryGuardrails`           | Audio + style path. Produces a DRAFT `GuardrailProfile` against `rytm_randomizer/guardrails/schema.py`. Auto-invokes via its description frontmatter. Reads `reference.md` on demand. |
| "Analyze SysEx / MIDI capture / mutation log / factory sound study"           | `DataAnalysisGuardrails`           | Parameter / capture-data path. Sibling of `MusicLibraryGuardrails`; same DRAFT `GuardrailProfile` output, different input class. Reads `reference.md` on demand.                        |
| "Dispatch parallel agents", "fan out workstreams", "run a multi-agent bundle"     | (consult `parallel-agent-composition.md`) | Dispatch per `maximize-parallelization`, but VERIFY per `.claude/rules/parallel-agent-composition.md`: reject any agent whose suite did not run (`scripts/check_agent_report.py`), take one integration checkpoint at first cross-agent import, and give every cross-language seam a drift guard. See `docs/AUTOUPDATE_PARALLEL_RUN_REPORT.md`. |
| "Open a PR", "create pull request", "push for review"                         | `open-pr` (global)                 | After all architecture tests pass locally. Use `scripts/create_pr.py` or include `--reviewer edward-rosado` in raw `gh pr create`.       |

## Architecture-affecting changes (gate)

If the change touches any of:

* `rytm_randomizer/data/*`
* `rytm_randomizer/state/*`
* `rytm_randomizer/engines/*`
* `rytm_randomizer/scene_runner.py`, `group_runner.py`, `shell.py`, `app.py`,
  `cli.py`, `midi_io.py`, `randomization.py`, `real_midi_adapter.py`,
  `mido_provider.py`, `reports.py`, `inspection.py`
* `tests/architecture/*`
* `docs/ARCHITECTURE.md`, `.claude/rules/architecture.md`

then it is **architecture-affecting**. Before AND after the change:

1. Re-read `docs/ARCHITECTURE.md` (the human-readable canonical version).
2. Re-read `.claude/rules/architecture.md` (the agent-facing distillation).
3. Run `pytest tests/architecture/ -q`.
4. Run the full suite (`pytest -q`). The full suite must stay 1279+ green.
5. Invoke the `code-review` skill on the resulting diff.

## Parity-touching changes (extra gate)

If the change touches any of:

* `rytm_randomizer/engines/*`
* `rytm_randomizer/group_runner.py`
* `rytm_randomizer/scene_runner.py`
* `tests/fixtures/v134_parity/*.json` (the V1.34 reference goldens)

then it is **parity-touching**. In addition to the architecture gate, the
characterization tests under `tests/test_engines_pad*.py`,
`tests/test_group_runner.py`, `tests/test_scene_runner.py` must pass
byte-for-byte against the V1.34 JSON goldens. Do not regenerate the goldens
casually -- `PARITY_CAPTURE_MODE=1 pytest ...` rewrites them from the current
engine output, and that is only appropriate when an intentional
reference-output change is being committed.

## Default workflow when starting any change

1. Read this file (`.claude/rules/skill-routing.md`).
2. Pick a skill from the table above.
3. If architecture-affecting, follow the architecture gate.
4. If parity-touching, follow the parity gate.
5. Code review with the `code-review` skill before commit.

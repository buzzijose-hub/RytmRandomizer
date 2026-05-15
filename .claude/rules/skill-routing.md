# Skill routing

> "If you are doing X, use skill Y." Agents working on this repo MUST consult
> this table before starting a change.

## Routing table

| Trigger / request                                                            | Skill                              | Notes                                                                                                                                  |
| ---------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| "Add a pad command", "wire up a new V1.34 command", "extend the shell"        | `add-pad-command`                  | Touches `shell.py` (dispatch) + the relevant runner / engine + tests. Do not bypass the architecture rules.                            |
| "Add a new fact table", "extend the data layer", "add a profile / scene"      | `extend-data-layer`                | New facts live ONLY under `data/`. Re-export through `data/__init__.py`. Update `tests/test_data_layer.py` drift-guard.                |
| "Review this code", "is this PR good?", "look at my diff"                     | `code-review`                      | Auto-invoked by the description (see SKILL frontmatter). Produces Critical / Important / Minor + verdict.                              |
| "Refactor", "change architecture", "move a module", "rename layer"            | (consult `architecture.md`)        | Read `docs/ARCHITECTURE.md` and `.claude/rules/architecture.md` FIRST. Run `pytest tests/architecture/` after any change.                |
| "Analyze music", "guardrail profile", "music library check"                   | `MusicLibraryGuardrails`           | See `.claude/skills/MusicLibraryGuardrails/SKILL.md`.                                                                                  |
| "Analyze data", "data quality check"                                          | `DataAnalysisGuardrails`           | See `.claude/skills/DataAnalysisGuardrails/SKILL.md`.                                                                                  |
| "Open a PR", "create pull request", "push for review"                         | `open-pr` (global)                 | After all architecture tests pass locally.                                                                                             |

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
* `rytm_hybrid_randomizer_v134.py` (you should not be here — file is frozen)

then it is **parity-touching**. In addition to the architecture gate, the
characterization tests under `tests/test_engines_pad*.py`,
`tests/test_group_runner.py`, `tests/test_scene_runner.py` must pass
byte-for-byte against the monolith. Never edit the monolith.

## Default workflow when starting any change

1. Read this file (`.claude/rules/skill-routing.md`).
2. Pick a skill from the table above.
3. If architecture-affecting, follow the architecture gate.
4. If parity-touching, follow the parity gate.
5. Code review with the `code-review` skill before commit.

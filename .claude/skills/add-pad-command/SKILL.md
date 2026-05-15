---
name: add-pad-command
description: |
  Add a new V1.34-equivalent interactive command to the RytmRandomizer shell
  (a pad command, a scene command, an isolated-pad command, etc.). Use when
  the user asks to "add a command", "wire up a new shell command", "add a
  pad command", "extend the interactive menu", or to surface an existing
  monolith command in the package shell. Walks through the files to touch,
  the imports allowed at each layer, and the tests that must be added.
---

# Add a pad / shell command

This skill walks through adding a new interactive command without violating
the layer rules from `docs/ARCHITECTURE.md`.

## Files to touch (in this order)

1. **(If new fact data is required)** Add or extend the data under
   `rytm_randomizer/data/`. New mutation plans live in `data/plans.py`; new
   profiles in `data/profiles.py`; new param/anchor/delta/zone tables in
   `data/param_maps.py`; new scene presets in `data/scenes.py`. Re-export
   from `data/__init__.py`. See the `extend-data-layer` skill if this step
   is non-trivial.

2. **(If new state is required)** Add or extend a frozen dataclass in
   `rytm_randomizer/state/`. Every transition returns a NEW state instance;
   no in-place mutation.

3. **Implement the runtime logic** in the correct layer:
   * Per-pad discovery -> the relevant `rytm_randomizer/engines/padN.py`.
   * Four-pad group / isolated-pad / intensity -> `group_runner.py`.
   * Scene / preset shortcut -> `scene_runner.py`.
   Inject dependencies (`out` sender, `rng`, `sleep`, profile dict); do NOT
   reach for module globals.

4. **Wire the command into the shell.** Open
   `rytm_randomizer/shell.py` and add the command to the dispatch table.
   Update the help text in `rytm_randomizer/help_text.py`.

5. **Surface in the passive CLI report layer** if the command should appear
   in `cli.py`'s passive listings. Reports live in `reports.py` /
   `inspection.py`. NEVER add runtime behavior to `cli.py` -- it is passive.

6. **Add tests.** Minimum required:
   * Unit test for the new function (in the corresponding engine / runner
     test file).
   * Parity test if the command exists in the V1.34 monolith (compare the
     emitted MIDI message sequence byte-for-byte against the reference).
   * Shell dispatch test in `tests/test_state_package.py` or a new
     `tests/test_shell_*` file.

## Layer rules to remember

* The engine / runner code MUST NOT import `cli`, `shell`, `app`,
  `mido_provider`, or `mido`.
* The shell code MUST NOT import `app` or `cli`.
* The CLI code MUST NOT import any engine, runner, `shell`, `app`,
  `mido_provider`, or `mido`.
* Lazy `mido` only. Real port construction happens in `app.py` under
  `--arm`, and goes through `mido_provider.MidoOutputProvider`.

## Verification gate

```
pytest tests/architecture/ -q
pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -q
pytest -q
```

All green. Coverage holds or rises.

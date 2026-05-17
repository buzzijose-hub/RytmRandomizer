---
name: extend-data-layer
description: |
  Add or modify a fact table inside RytmRandomizer's data layer (CC numbers,
  anchors, deltas, zones, scenes, profiles, mutation plans, the four-pad
  layout). Use when the user asks to "extend the data layer", "add a
  profile", "add a scene", "add a parameter map", "add a mutation plan", or
  to put new "table of facts" content somewhere. Enforces the data-not-code
  rule: facts live under rytm_randomizer/data/ exactly once.
---

# Extend the data layer

The data layer is the single source of truth for every fact in this
codebase. Any "table of facts" lives under `rytm_randomizer/data/` and is
re-exported through `rytm_randomizer/data/__init__.py`. Wrapper modules
(`profiles.py`, `scenes.py`, `constants.py`) and the V1.34 monolith both
import their data from here -- this is what guarantees the two codebases
cannot drift.

## Pick the right module

| Kind of data                            | Module                          |
| --------------------------------------- | ------------------------------- |
| Per-machine CC numbers                  | `data/param_maps.py::MACHINE_CC`|
| Param order tables for a machine        | `data/param_maps.py::*_ORDER`   |
| Anchor states for a profile             | `data/param_maps.py::*_ANCHOR`  |
| Safe ranges / deltas / zones            | `data/param_maps.py`            |
| Discovery profile registry              | `data/profiles.py::PROFILES`    |
| Scene / preset definitions              | `data/scenes.py::SCENE_PRESETS` |
| Four-pad group layout                   | `data/plans.py::GROUP_LAYOUT`   |
| Intensity / page / per-pad mode plans   | `data/plans.py`                 |

If none of those fit, add a new module under `data/` and re-export it from
`data/__init__.py`.

## Procedure

1. **Read the existing module first.** Match the style (dict shape, key
   naming, ordering).
2. **Add the new fact** in the right module. Keep it a plain dict / tuple
   / dataclass with NO behavior.
3. **Re-export from `data/__init__.py`** (both the import and the
   `__all__` list).
4. **Do NOT add the fact anywhere else.** Wrappers must derive their value
   from `data/`. The architecture test
   `tests/architecture/test_data_not_code.py` will fail if a name is
   redefined outside `data/`.
5. **Update the drift-guard.** Add an assertion in
   `tests/test_data_layer.py` that pins the shape or a representative
   value of the new entry. This is what stops a future agent from quietly
   changing it.
6. **The V1.34 monolith is retired.** New facts live in the package's
   `data/` layer and become visible to the engines automatically. The V1.34
   reference behavior is captured as JSON goldens under
   `tests/fixtures/v134_parity/`; if a new fact changes engine output, the
   matching goldens must be regenerated (`PARITY_CAPTURE_MODE=1 pytest
   tests/test_engines_pad*.py tests/test_group_runner.py
   tests/test_scene_runner.py`) and the regeneration justified in the PR.

## Verification gate

```
pytest tests/architecture/test_data_not_code.py tests/test_data_layer.py -q
pytest tests/architecture/ -q
pytest -q
```

All green. Coverage holds.

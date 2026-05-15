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

## Preserve parity with the V1.34 reference

The V1.34 hardware-validated musical behavior is the baseline of truth. It was validated against the actual Analog Rytm MK2. **Any change must preserve parity with that behavior.**

As of Wave 4 / WS-O the modular package owns the interactive runtime end-to-end (`rytm_randomizer.app` -> `rytm_randomizer.shell`). The V1.34 monolith (`rytm_hybrid_randomizer_v134.py`) is retained on disk **only as a frozen byte-parity reference** for the characterization tests (`tests/test_engines_pad*`, `tests/test_group_runner.py`, `tests/test_scene_runner.py`). The monolith file is kept byte-identical to its tagged V1.34 form -- `tests/test_real_midi_import_safety.py::test_v134_reference_has_no_working_tree_diff` enforces this -- and is not invoked by production code paths anymore.

Concretely:

- The V1.34 reference file must stay byte-identical. Do not edit `rytm_hybrid_randomizer_v134.py`. New behavior lives in the `rytm_randomizer/` package and is locked against the reference by the parity tests.
- The following are **not allowed** without explicit approval:
  - New MIDI CC mappings.
  - New pad profiles or machines.
  - Pads 5-12 expansion.
  - Parameter range changes.
  - Command behavior changes (the shell's command alphabet mirrors the V1.34 monolith exactly).
- **Allowed:** further refactoring within the package; readability improvements that do not change behavior; new tests; documentation updates.
- Add tests when you split code. Test after each major split.

## Commit conventions

- Short, imperative summaries (e.g. `Split scene plans into scenes module`).
- Commit in small steps.

## Data vs code

Anything that is "a table of facts" — commands, parameters, scenes, pad profiles — should live as **data** (a dataclass registry or a data file), not as bespoke per-item functions. Prefer one generic handler driven by a registry over many near-identical hand-written functions.

## Definition of done includes docs

Any structural change must update the docs it affects. A change is not done until the `README.md`, this file, and any relevant `Docs/` entries reflect the new reality.

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

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

## Preserve V1.34 behavior

`rytm_hybrid_randomizer_v134.py` is the hardware-validated behavior reference. It was validated against the actual Analog Rytm MK2. **Any change must preserve its validated musical behavior.**

Concretely:

- Build modular code in `rytm_randomizer/` *beside* the monolith, not instead of it. Do not remove the V1.34 script until the modular version is fully validated.
- The following are **not allowed** without explicit approval:
  - New MIDI CC mappings.
  - New pad profiles or machines.
  - Pads 5–12 expansion.
  - Parameter range changes.
  - Command behavior changes.
- **Allowed:** splitting the monolith into modules; moving constants, profiles, MIDI helpers, scene plans, and command handlers into separate files; adding tests that verify command names, profile keys, scene names, and safety guardrails; readability improvements that do not change behavior.
- Add tests when you split code. Test after each major split.

## Commit conventions

- Short, imperative summaries (e.g. `Split scene plans into scenes module`).
- Commit in small steps.

## Data vs code

Anything that is "a table of facts" — commands, parameters, scenes, pad profiles — should live as **data** (a dataclass registry or a data file), not as bespoke per-item functions. Prefer one generic handler driven by a registry over many near-identical hand-written functions.

## Definition of done includes docs

Any structural change must update the docs it affects. A change is not done until the `README.md`, this file, and any relevant `Docs/` entries reflect the new reality.

# RytmRandomizer Modularization Rules

> Note: the contributor-facing rules from this file are also folded into CONTRIBUTING.md.

Current stable baseline:
- Active validated script: rytm_hybrid_randomizer_v134.py
- Stable tag: v1.34-stable-expanded-scene-layer
- Working branch: modularize-v1.34

Primary rule:
Preserve V1.34 behavior exactly.

Allowed:
- Split the monolithic script into modules.
- Move constants, profiles, MIDI helpers, scene plans, and command handlers into separate files.
- Add tests that verify command names, profile keys, scene names, and safety guardrails.
- Improve readability without changing behavior.

Not allowed:
- No new MIDI CC mappings.
- No new pad profiles.
- No new machines.
- No Pads 5-12 yet.
- No GUI yet.
- No parameter range changes.
- No command behavior changes unless explicitly approved.
- Do not remove the working V1.34 script until the modular version is validated.

Required safety:
- Keep rytm_hybrid_randomizer_v134.py as the reference implementation.
- Build modular code beside it, not instead of it.
- Commit small steps.
- Test after each major split.

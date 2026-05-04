# Codex Task Brief - RytmRandomizer Modularization

You are working in the RytmRandomizer repo on branch modularize-v1.34.

Read first:
- Docs/MODULARIZATION_RULES.md
- README.md
- rytm_hybrid_randomizer_v134.py

Primary objective:
Refactor the monolithic V1.34 script into a modular structure while preserving behavior exactly.

Reference implementation:
- rytm_hybrid_randomizer_v134.py is the validated hardware-tested reference.
- Do not delete it.
- Do not rewrite behavior from memory.
- Extract carefully from the existing script.

Strict constraints:
- No new MIDI CC mappings.
- No new parameter ranges.
- No new machines.
- No new pad profiles.
- No Pads 5-12.
- No GUI.
- No command behavior changes.
- No renamed user-facing commands unless explicitly approved.

Suggested first step:
Create a new package folder:

rytm_randomizer/

Suggested module split:
- rytm_randomizer/constants.py
- rytm_randomizer/profiles.py
- rytm_randomizer/midi.py
- rytm_randomizer/state.py
- rytm_randomizer/mutation.py
- rytm_randomizer/scenes.py
- rytm_randomizer/commands.py
- rytm_randomizer/app.py

Create a new runner:
- run_modular.py

Safety expectation:
The original V1.34 script must still run.
The modular runner should eventually expose the same command behavior.

Testing expectation:
Add lightweight tests that do not require hardware:
- profile keys exist
- machine CC15 values are unchanged
- scene command names exist
- main-prompt 1/2/3 guardrail exists
- Pad 3 SY Raw CC mapping remains CC19 = Noise Level and CC23 = Balance
- Pad 1 defaults to BD Hard
- scene variants S1A/S1B/S2A/S2B/S3A/S3B/S4A/S4B exist

Do the work in small commits.

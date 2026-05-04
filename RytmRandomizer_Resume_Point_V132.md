# RytmRandomizer Resume Point — V1.32 Validated

Date: 2026-05-03
Current validated version: V1.32
Active script: `rytm_hybrid_randomizer_v132.py`
Project folder: `C:\Users\Jose Buzzi\Documents\RytmRandomizer`

## Current Milestone

V1.32 is validated as the documentation checkpoint for the scene + global UX system.

Validated behavior:
- `SCN` shows the scene / preset menu.
- `O` loads the full 4-pad anchors.
- `GM` shows the global 4-pad mutation tools.
- `S1` runs the Rolling scene through the validated four-lane global layer.
- `S5` returns all four pads to clean anchors.
- Bare main-prompt `1` sends no MIDI and prints the guardrail warning.
- `Z` returns all four pads to anchors.

## Current Four-Lane Layout

- Pad 1 = BD Hard / protected kick foundation
- Pad 2 = BD Classic / secondary percussion lane
- Pad 3 = SY Raw / bass + synth-percussion motion lane
- Pad 4 = BD Acoustic / body + accent pressure lane

## Current Scene Layer

- `SCN` = show scene / preset tools
- `S0` = Home / Clean anchors
- `S1` = Rolling scene
- `S2` = Deeper scene
- `S3` = Intense scene
- `S4` = Wild scene
- `S5` = Back to Clean anchors

Scene/global commands auto-load anchors if needed.

## Current Safety Guardrail

At the main command prompt, bare `1`, `2`, or `3` no longer sends MIDI.

Use depth values only after a command asks for depth, for example:
- `Y` then `1`
- `V` then `1`
- `N` then `1`

Legacy single-profile full mutations were moved to:
- `M1` = legacy single-profile full micro mutation
- `M2` = legacy single-profile full groove mutation
- `M3` = legacy single-profile full strong mutation

## Recommended Cleanup Before Shutdown

Run from PowerShell:

```powershell
cd "$env:USERPROFILE\Documents\RytmRandomizer"

Move-Item ".\RytmRandomizer_Handoff_2026-05-03_V132.zip" ".\Exports\Handoffs\" -Force
Move-Item ".\rytm_hybrid_randomizer_v131.py" ".\LegacyScripts\" -Force

Get-ChildItem
```

Clean root should show:
- folders
- `README.md`
- `run_current.bat`
- `run_current.ps1`
- `rytm_hybrid_randomizer_v132.py`

## How To Resume

From PowerShell:

```powershell
cd "$env:USERPROFILE\Documents\RytmRandomizer"
python .\rytm_hybrid_randomizer_v132.py
```

Startup choices:

```text
1
1
1
```

Quick resume check:

```text
SCN
GM
Q
```

## Next Recommended Move

V1.33 = scene depth expansion.

Goal: make the scene layer more performance-useful without changing the core safety system. Possible direction:
- Rolling Micro / Rolling Groove
- Deeper Micro / Deeper Groove
- Intense Micro / Intense Groove
- Wild controlled variants
- Keep `S5` as clean reset

Important: do not jump to Pads 5–12 yet. Current priority remains polishing Pads 1–4 scene/global performance flow.

# Live GUI Scene Queue Model Plan

> Status: in-flight

## Goal

Create a passive backend contract for the target GUI's Scenes screen: a deterministic scene rail plus live preview queue derived from the existing V1.34 scene data. The model must stay mock-safe and must not execute scenes, open ports, launch a GUI, write files, or send MIDI.

## Scope

- Add `rytm_randomizer.reports.live_gui_scene_queue_model`.
- Reuse `SCENE_PRESETS` and `INTENSITY_PLANS` as the source of truth.
- Emit GUI-ready scene cards with affected pads, depth summary, dry-run message estimate, status, and operator hint.
- Emit a deterministic preview queue for future UI rendering.
- Add focused tests with 100% branch coverage, including future-scene fallback behavior.

## Out Of Scope

- No frontend component changes.
- No CLI command registration.
- No scene execution.
- No hardware, MIDI, installer, or audio-analyzer changes.

## Verification

- Focused tests and branch coverage for the new module.
- Architecture tests.
- Full pytest suite.
- Full branch coverage run.
- Ruff, Black, isort, touched-file vulture, review gate, and pre-push gate before PR.

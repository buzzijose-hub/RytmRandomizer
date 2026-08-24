# Analog Four Render-Feedback Refinement Plan

Status: in-flight (implemented and locally verified; PR pending)

## Goal

Turn one recorded Analog Four candidate into a finite, explainable decision:
accept a sufficiently close render or generate exactly one corrected follow-up
candidate from measured acoustic residuals.

## Scope

- Extend the existing passive audio-to-patch pipeline in place.
- Reuse the immutable batch manifest, 11-feature acoustic ranker, Analog Four
  candidate inference, and validated offline saved-kit exporter.
- Verify the reference hash and selected candidate before refinement.
- Use a typed, deterministic residual correction with explicit threshold,
  gain, clamping, and duration-preservation behavior.
- Write local JSON and Markdown artifacts for both accepted and refined
  outcomes.
- Keep `python -m rytm_randomizer.app --arm` as the only real MIDI boundary.

## Out Of Scope

- No indefinite optimization loop or model training.
- No claim of exact or forensic sound recreation.
- No new synthesis mappings or unverified SysEx fields.
- No MIDI backend import, port enumeration, hardware access, or transmission.
- No Analog Rytm implementation in this change.

## Verification

- Deterministic accept/refine decisions and normalized clamping tests.
- Manifest, reference-hash, candidate, and artifact failure-path tests.
- Passive CLI parser, JSON, text, and optional offline-export tests.
- Byte-identical artifact reproduction from identical inputs.
- Focused CLI contract, architecture, strict typing, lint, and diff checks.

## Result

The studio workflow now has a bounded second pass that turns one real hardware
render into useful evidence without asking the operator to perform an open-ended
manual calibration sequence. The correction remains an explainable heuristic,
and the operator still decides whether the resulting sound is musically useful.

# Audio-to-Patch Studio Handoff Plan

Status: in-flight

## Goal

Turn the existing passive Analog Four audio-to-patch batch into a finite
studio workflow: generate four deterministic candidates, print guarded
audition commands, record the same phrase for each, and rank the four renders.

## Scope

- Extend the existing `analog-four-audio-patch-batch` command in place.
- Keep generation passive and preserve `python -m rytm_randomizer.app --arm`
  as the only real MIDI boundary.
- Require exactly four candidates and an exact output-port name for the
  generated armed commands.
- Emit full paths so a PowerShell session can run the handoff directly.
- Document that no Rush16 calibration rounds are required.

## Verification

- Focused parser, payload, formatting, validation, and quoting tests.
- 100% statement and branch coverage for the touched production module.
- Architecture, passive-safety, strict typing, lint, V1.34 parity, and full
  test-suite gates.
- Passive end-to-end generation with a synthetic reference WAV and a public
  saved-kit fixture; no MIDI port opened and no MIDI or SysEx transmitted.

## Result

The studio handoff is one bundled CLI/documentation change based directly on
`modularize-v1.34`. It replaces an unbounded calibration loop with four
musically meaningful auditions while retaining every existing hardware guard.

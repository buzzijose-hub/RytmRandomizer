# Analog Four Live-Dial Enum Transport Evidence

Date: 2026-07-17

## Purpose

Resolve the five generated Analog Four DNA rows that already had official NRPN
addresses but lacked validated enum values. These rows were previously marked
screen-only and deliberately skipped by live dial.

This is transport-schema evidence, not a physical full-patch send result. No
MIDI output was available or opened during this inspection.

## Sources

- Elektron Analog Four MKII User Manual, OS 1.55, Appendix E MIDI:
  <https://www.elektron.se/wp-content/uploads/2026/06/Analog-Four-MKII-User-Manual_ENG_OS1.55_260610.pdf>
- Installed Elektron Overbridge 2.25.7 Analog Four VST3:
  `C:\Program Files\Common Files\VST3\Elektron (64bit)\Analog Four.vst3`
- Connected-device logs identified the target firmware as OS 1.55. The plug-in
  was inspected offline with no device selected for the enum-value checks.

## Results

| DNA row | Official NRPN | Overbridge label | Validated value |
|---|---:|---|---:|
| EnvF Gate Length | `1:65` | `Off` (front-panel DNA label `NOTE`) | `0` |
| EnvF Destination A | `1:66` | `None` / DNA label `OFF` | `96` |
| EnvF Destination B | `1:68` | `None` / DNA label `OFF` | `96` |
| LFO1 Destination A | `1:86` | `F1 Frequency` | `34` |
| LFO1 Destination B | `1:88` | `None` / DNA label `OFF` | `96` |

The destination controls use sparse IDs rather than list indices. For example,
Overbridge defaults also exposed EnvF destination raw values `12` and `13` as
Oscillator 1/2 Pulsewidth. The implementation therefore maps only labels
observed through the official plug-in. Any unknown label remains
`screen-only-nrpn` and cannot be sent.

## Outcome

The current closest-reference genome is fully live-routable:

- 39 DNA rows
- 29 CC events
- 10 NRPN events
- 59 transport messages
- 0 manual rows

The direct NRPN sender and four-track routing had already been confirmed on the
physical A4 using Filter2 Resonance values. The next hardware validation is one
complete candidate sent from a hash-verified batch sidecar, followed by a page
review and an audio recording for acoustic ranking.

## Boundary

- This evidence does not authorize any additional saved-kit SysEx field.
- Saved-kit export remains limited to Filter2 Resonance.
- It does not claim every possible A4 destination enum is known.
- It does not claim Synthplant-equivalent acoustic accuracy.

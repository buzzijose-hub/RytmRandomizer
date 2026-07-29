# Analog Four Live-Dial Enum Transport Evidence

Original offline inspection: 2026-07-17

Physical correction: 2026-07-29

## Purpose

Record the offline evidence that originally promoted five generated Analog
Four DNA rows, then preserve the physical rehearsal that disproved those
promotions and one LFO multiplier value.

The 2026-07-17 material was transport-schema evidence only. No MIDI output was
available or opened during that inspection. The later physical rehearsal is
the authoritative result for send readiness.

## Sources

- Elektron Analog Four MKII User Manual, OS 1.55, Appendix E MIDI:
  <https://www.elektron.se/wp-content/uploads/2026/06/Analog-Four-MKII-User-Manual_ENG_OS1.55_260610.pdf>
- Installed Elektron Overbridge 2.25.7 Analog Four VST3:
  `C:\Program Files\Common Files\VST3\Elektron (64bit)\Analog Four.vst3`
- Connected-device logs identified the target firmware as OS 1.55. The plug-in
  was inspected offline with no device selected for the enum-value checks.

## Original offline inference

| DNA row | Official NRPN | Overbridge label | Plug-in-observed raw value |
|---|---:|---|---:|
| EnvF Gate Length | `1:65` | `Off` (front-panel DNA label `NOTE`) | `0` |
| EnvF Destination A | `1:66` | `None` / DNA label `OFF` | `96` |
| EnvF Destination B | `1:68` | `None` / DNA label `OFF` | `96` |
| LFO1 Destination A | `1:86` | `F1 Frequency` | `34` |
| LFO1 Destination B | `1:88` | `None` / DNA label `OFF` | `96` |

The plug-in evidence suggested sparse IDs rather than list indices. That
inference was plausible but was not sufficient to authorize hardware output.

## Physical rehearsal correction

The hash-verified candidate was sent through the sole armed boundary,
`python -m rytm_randomizer.app --arm`. The command completed all 33 planned
rows / 53 MIDI messages. The A4 front panel then showed:

| DNA row | Planned target | Observed after send | Result |
|---|---|---|---|
| EnvF Gate Length | `NOTE` via raw `0` | `OFF` | disproved |
| EnvF Destination A | `OFF` via raw `96` | raw `96` | disproved |
| EnvF Destination B | `OFF` via raw `96` | raw `96` | disproved |
| LFO1 Speed Multiplier | `x1` via raw `64` | `2K` | disproved |
| LFO1 Destination A | `Filter1 Frequency` via raw `34` | raw `34` | disproved |
| LFO1 Destination B | `OFF` via raw `96` | raw `96` | disproved |

The same page review confirmed the still-sendable enum targets:

- EnvA shape: triangle.
- EnvF shape: triangle.
- LFO1 mode: `TRG`.
- LFO1 waveform: triangle.
- Filter2 type: `HP2`.

Continuous CC targets visible on the oscillator, filter, AMP, ENVF, and LFO1
pages also matched. This supports the address/routing path while isolating the
failure to enum-value interpretation.

### Session record

- Analog Four MKII firmware: OS 1.55, corroborated by the connected-device log
  and current official manual; no firmware-screen photograph was taken during
  the rehearsal.
- Elektron Transfer: 1.9.5.
- Elektron Overbridge: 2.25.7.
- Generation: `b9ead39abab516cb1a13a91b11938878`.
- Reviewed manifest SHA-256:
  `ef2d474348415ef98b2278b28e7f10620c71a2856fe473a7cd78f5afd055376e`.
- Candidate: 1, Closest reference.
- Delivery: app reported 33 rows / 53 messages complete. MIDI provides no
  per-message device acknowledgment.
- Persistence: no Program Change, transport, SysEx, save, kit-write,
  pattern-write, song-write, chain-write, or project-write message was sent.
- Recovery: the operator reloaded the clean initialized kit without saving.
- Verdict: controlled partial pass and semantic failure; not merge-ready.

## Outcome

The six disproved rows now have no sendable raw ordinal and compile to manual
events with a calibration-required reason. The corrected guarded plan is:

- 39 DNA rows
- 22 sendable CC events
- 5 NRPN events
- 37 transport messages
- 12 manual rows: six disproved enums plus six paired-CC rows pending 14-bit
  hardware verification

The next hardware validation is a supervised replay of a newly generated,
hash-reviewed 27-row / 37-message candidate, followed by the same page review.
Audio recording and acoustic ranking remain separate pending work.

## Boundary

- This evidence does not authorize any additional saved-kit SysEx field.
- Saved-kit export remains limited to Filter2 Resonance.
- It does not claim every possible A4 destination enum is known.
- It does not claim Synthplant-equivalent acoustic accuracy.

# Analog Four Live-Dial Enum Transport Evidence

Original offline inspection: 2026-07-17

Physical correction: 2026-07-29

## Purpose

Record the offline evidence that originally promoted generated Analog Four DNA
rows, then preserve the physical rehearsals that disproved six enum values and
the independently inferred LFO1 Mode value.

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

The initial page review appeared to confirm these still-sendable enum targets:

- EnvA shape: triangle.
- EnvF shape: triangle.
- LFO1 waveform: triangle.
- Filter2 type: `HP2`.

Later review of the retained photographs showed that LFO1 Mode had actually
remained `FREE`; it was not `TRG`. That observation supersedes the initial
session note.

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
- Verdict: controlled partial pass and semantic failure; corrected replay
  required.

## Corrected physical rehearsal

A newly generated, hash-reviewed successor plan was then sent through the same
armed boundary. The app reported all 27 rows / 37 MIDI messages delivered.
Front-panel photographs showed that all 26 mappings retained by the final
policy matched their planned values across OSC1, OSC2, Filters, AMP, ENVF, and
LFO1. The remaining row, LFO1 Mode, did not:

| DNA row | Planned target | Observed after send | Result |
|---|---|---|---|
| LFO1 Mode | `TRG` via raw `0` | `FREE` | disproved |

### Corrected session record

- Analog Four MKII firmware: OS 1.55.
- Elektron Transfer: 1.9.5.
- Elektron Overbridge: 2.25.7.
- Tested generation: `2c142e93007854db41dc3f32836204bb`.
- Reviewed manifest SHA-256:
  `83c87935d034a646b294f7b6c30e212e15898e77f7a4e86e4b4d555caa9bd280`.
- Candidate: 1, Closest reference.
- Delivery: app reported 27 rows / 37 messages complete. MIDI provides no
  per-message device acknowledgment.
- Semantic result: 26 retained mappings matched; LFO1 Mode remained `FREE`.
- Persistence: no Program Change, transport, SysEx, save, kit-write,
  pattern-write, song-write, chain-write, or project-write message was sent.
- Recovery: the operator reloaded the clean initialized kit without saving.
- Verdict: the retained routed subset passed; LFO1 Mode was demoted.

## Outcome

The seven disproved rows now have no sendable raw ordinal and compile to manual
events with a calibration-required reason. The final guarded plan is:

- 39 DNA rows
- 22 sendable CC events
- 4 NRPN events
- 34 transport messages
- 13 manual rows: seven disproved enums plus six paired-CC rows pending 14-bit
  hardware verification

The final policy was regenerated passively as generation
`26dcc4058b0272a1e910d5b2b960a765`, manifest SHA-256
`d503eac35e7468e9446505482ba55641cd96c55a0c095150888c35f3fa88a17e`.
Its dry-run captured the expected 34 messages without opening a port. A second
physical send is unnecessary because the preceding 27-row rehearsal already
verified every one of the 26 rows retained in this policy. Audio recording and
acoustic ranking remain separate pending work.

## Boundary

- This evidence does not authorize any additional saved-kit SysEx field.
- Saved-kit export remains limited to Filter2 Resonance.
- It does not claim every possible A4 destination enum is known.
- LFO2 Mode is absent from the current candidate and remains manual because no
  independent physical ordinal evidence has been recorded for it.
- It does not claim Synthplant-equivalent acoustic accuracy.

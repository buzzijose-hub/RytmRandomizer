# Outbound 12-Track CC Hardware Validation Results

Date: 2026-05-26

## Purpose

Validate the smallest real outbound MIDI path against an Elektron Analog Rytm
MKII: one explicit CC message per track, one track at a time, with operator
observation after every send.

This evidence file records a hardware validation pass only. It does not widen
the runtime mutation scope, add 12-pad mutation behavior, add scenes, add
SysEx, or authorize unattended hardware sends.

## Setup

- Target hardware: Elektron Analog Rytm MKII
- Connection: USB MIDI
- Output port selected: `Elektron Analog Rytm MKII 1`
- Command path:
  `python -m rytm_randomizer.app --arm --validate-one-cc --channel N --control 17 --value 64`
- Port prompt input: `1`
- Analog Four: not targeted
- Validation mode: explicit armed hardware validation
- Send shape: exactly one MIDI CC per track

## Safety Boundaries

- No scene execution
- No group mutation
- No pattern change
- No transport change
- No clock change
- No kit save
- No project write
- No SysEx
- No Analog Four send
- No unattended send loop
- Operator observation required after each track

## Results

| Rytm Track | Pad | mido channel | MIDI channel meaning | CC | Value | Observation |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 0 | 1 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 2 | 2 | 1 | 2 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 3 | 3 | 2 | 3 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 4 | 4 | 3 | 4 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 5 | 5 | 4 | 5 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 6 | 6 | 5 | 6 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 7 | 7 | 6 | 7 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 8 | 8 | 7 | 8 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 9 | 9 | 8 | 9 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 10 | 10 | 9 | 10 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 11 | 11 | 10 | 11 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |
| 12 | 12 | 11 | 12 | 17 | 64 | Pad changed; no other pad changed; no weird behavior. |

## Outcome

Passed.

The validation confirmed that explicit outbound CC sends using mido channels
0 through 11 target Rytm tracks 1 through 12 respectively in this studio setup.
Each send changed only the expected pad, and the operator observed no
cross-pad changes or unexpected hardware behavior.

## What This Proves

- The armed one-CC validation path can open the selected Rytm output, send one
  CC, close the output, and exit.
- The per-track channel model worked for all 12 Rytm tracks in this setup.
- Track N responded to mido channel N - 1 for this CC validation pass.
- CC 17 / value 64 was safe enough for the disposable-kit validation pass.

## What This Does Not Prove

- It does not prove full 12-pad mutation behavior.
- It does not prove every CC for every machine.
- It does not prove scene, group, pattern, transport, clock, kit-save, project,
  or SysEx behavior.
- It does not authorize unattended active sends.
- It does not validate Analog Four behavior.

## Next Safe Step

Use this evidence to design the next mock-first expansion carefully:

- keep the existing passive/default behavior unchanged;
- preserve the explicit `--arm` boundary;
- add any future 12-track behavior behind tests and review gates;
- validate real hardware only in small, reversible steps.

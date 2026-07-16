# RUSH01 Device-Assisted MIDI Build Report

## Scope

This phase compiles the RUSH01 semantic YAML into documented MIDI CC, CC14,
and NRPN plans for the active kits of an Analog Rytm MKII and Analog Four
MKII. It does not mutate a saved kit, transmit SysEx, save a kit, generate a
pattern/song/project, or alter either approved reference dump. The existing
reference-bound SysEx codecs remain available and their byte-identical
round-trip tests remain in the suite.

No physical MIDI provider was constructed while producing these artifacts.
No MIDI port was opened and no MIDI data was sent.

## Static Plan Summary

The checked-in plans intentionally have no port or channel configuration:

| Device | Total | Ready mappings | Preserve | Manual | Learn | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| Analog Rytm MKII | 313 | 305 | 1 | 4 | 3 | 0 |
| Analog Four MKII | 245 | 149 | 4 | 1 | 85 | 6 |

`ready` means the semantic value, conversion, and MIDI address are positively
mapped. In the checked-in JSON, its channel and ordered bytes remain `null`
with `configuration_issue` because the user's exact port names and track
channels were not supplied. This is deliberate: the compiler will not invent
device configuration. With any valid explicit config, the Rytm plan contains
305 ordered messages and the A4 plan contains 179 ordered messages for its 149
ready fields.

Both JSON plans state `dry_run: true`, `midi_sent: false`, and
`configuration_ready: false`.

Each plan was compiled and serialized twice from the same semantic YAML. The
two byte streams were identical, and validation asserted that the output port,
every channel, every user channel, and every ordered byte sequence remained
`null` in the unconfigured artifacts:

- `RUSH01_RYTM_midi_plan.json` SHA-256:
  `9cfdd5a05322597ce5f52f99ec184acbbb3518bfdc85cadd388c1fc407cc3901`
- `RUSH01_A4_midi_plan.json` SHA-256:
  `6ab2c945e94c10d9144d801a6da460d7772e4d495f31b3c6b388f4bb72d11c64`

## Rytm Corrections

- BT Classic `SNP: 24` was removed. `Snap Type` is a typed enum and currently
  preserves the active-kit value pending calibration.
- CB Metallic `PW1` and `PW2` were removed. Its source fields are exactly
  Level, Tune, Decay Time, and Detune.
- LT, MT, and HT machine IDs were removed and replaced by explicit manual
  XT Classic selection steps.
- Every source control resolves by machine name plus semantic parameter name.
  For example, BD Sharp maps Sweep Depth, Sweep Time, and Hold Time to CC19,
  CC20, and CC21 respectively; YAML order is not used as an address source.
- All twelve sample playback levels compile to CC31 value 0. The specification
  declares no external sample dependency.

### Rytm Manual Setup

1. Name the active kit `RUSH01` at the front panel after validation.
2. Select XT Classic manually on LT.
3. Select XT Classic manually on MT.
4. Select XT Classic manually on HT.

### Rytm Learn Required

- `tracks.BD.synth.Waveform`
- `tracks.CH.synth.Osc Reset`
- `tracks.CY.synth.Cymbal Type`

`tracks.BT.synth.Snap Type` is separately marked `preserve_reference`.

## Analog Four Status

The A4 plan does not approximate high-resolution pitch/filter values,
booleans, waveform/sub-oscillator/sync/envelope enums, linear detune, or Noise
Color. Its 85 learn-required fields group as follows:

The remaining A4 manual setup requirement is to name the validated active kit
`RUSH01` at the front panel. The compiler never issues a save command.

- 24 high-resolution pitch and filter-frequency conversions
- 8 linear-detune conversions
- 20 boolean conversions
- 29 typed enum conversions
- 4 unmapped Noise Color values

### A4 Learn Required

T1:

```text
tracks.T1.oscillator_1.coarse_tune_semitones
tracks.T1.oscillator_1.fine_tune_cents
tracks.T1.oscillator_1.linear_detune_hz
tracks.T1.oscillator_1.keytrack
tracks.T1.oscillator_1.waveform
tracks.T1.oscillator_1.sub_oscillator
tracks.T1.oscillator_2.coarse_tune_semitones
tracks.T1.oscillator_2.fine_tune_cents
tracks.T1.oscillator_2.linear_detune_hz
tracks.T1.oscillator_2.keytrack
tracks.T1.oscillator_2.waveform
tracks.T1.oscillator_2.sub_oscillator
tracks.T1.oscillator_common.osc1_am
tracks.T1.oscillator_common.sync_mode
tracks.T1.oscillator_common.osc2_am
tracks.T1.oscillator_common.oscillator_retrigger
tracks.T1.noise.color
tracks.T1.filter_1.frequency
tracks.T1.filter_2.frequency
tracks.T1.amp.envelope_shape
tracks.T1.filter_envelope.envelope_shape
```

T2:

```text
tracks.T2.oscillator_1.coarse_tune_semitones
tracks.T2.oscillator_1.fine_tune_cents
tracks.T2.oscillator_1.linear_detune_hz
tracks.T2.oscillator_1.keytrack
tracks.T2.oscillator_1.waveform
tracks.T2.oscillator_1.sub_oscillator
tracks.T2.oscillator_2.coarse_tune_semitones
tracks.T2.oscillator_2.fine_tune_cents
tracks.T2.oscillator_2.linear_detune_hz
tracks.T2.oscillator_2.keytrack
tracks.T2.oscillator_2.waveform
tracks.T2.oscillator_2.sub_oscillator
tracks.T2.oscillator_common.osc1_am
tracks.T2.oscillator_common.sync_mode
tracks.T2.oscillator_common.osc2_am
tracks.T2.oscillator_common.oscillator_retrigger
tracks.T2.noise.color
tracks.T2.filter_1.frequency
tracks.T2.filter_2.frequency
tracks.T2.amp.envelope_shape
tracks.T2.filter_envelope.envelope_shape
```

T3:

```text
tracks.T3.oscillator_1.coarse_tune_semitones
tracks.T3.oscillator_1.fine_tune_cents
tracks.T3.oscillator_1.linear_detune_hz
tracks.T3.oscillator_1.keytrack
tracks.T3.oscillator_1.waveform
tracks.T3.oscillator_1.sub_oscillator
tracks.T3.oscillator_2.coarse_tune_semitones
tracks.T3.oscillator_2.fine_tune_cents
tracks.T3.oscillator_2.linear_detune_hz
tracks.T3.oscillator_2.keytrack
tracks.T3.oscillator_2.waveform
tracks.T3.oscillator_2.sub_oscillator
tracks.T3.oscillator_common.osc1_am
tracks.T3.oscillator_common.sync_mode
tracks.T3.oscillator_common.osc2_am
tracks.T3.oscillator_common.oscillator_retrigger
tracks.T3.noise.color
tracks.T3.filter_1.frequency
tracks.T3.filter_2.frequency
tracks.T3.filter_2.type
tracks.T3.amp.envelope_shape
tracks.T3.filter_envelope.envelope_shape
```

T4:

```text
tracks.T4.oscillator_1.coarse_tune_semitones
tracks.T4.oscillator_1.fine_tune_cents
tracks.T4.oscillator_1.linear_detune_hz
tracks.T4.oscillator_1.keytrack
tracks.T4.oscillator_1.waveform
tracks.T4.oscillator_1.sub_oscillator
tracks.T4.oscillator_2.coarse_tune_semitones
tracks.T4.oscillator_2.fine_tune_cents
tracks.T4.oscillator_2.linear_detune_hz
tracks.T4.oscillator_2.keytrack
tracks.T4.oscillator_2.waveform
tracks.T4.oscillator_2.sub_oscillator
tracks.T4.oscillator_common.osc1_am
tracks.T4.oscillator_common.sync_mode
tracks.T4.oscillator_common.osc2_am
tracks.T4.oscillator_common.oscillator_retrigger
tracks.T4.noise.color
tracks.T4.filter_1.frequency
tracks.T4.filter_2.frequency
tracks.T4.amp.envelope_shape
tracks.T4.filter_envelope.envelope_shape
```

The six invalid display-semantic values are retained as explicit
`invalid_spec_field` rows and block `--apply` before port discovery:

- `tracks.T1.oscillator_1.pulse_width`: 64
- `tracks.T2.oscillator_1.pulse_width`: 76
- `tracks.T2.filter_1.envelope_depth`: 64
- `tracks.T3.oscillator_2.pulse_width`: 74
- `tracks.T4.oscillator_1.pulse_width`: 64
- `tracks.T4.oscillator_2.pulse_width`: 64

The repository's verified A4 bipolar display converter accepts `-64..63`.
These requests are not clamped or reinterpreted as raw MIDI.

## Dry-Run Commands

Populate `config/rush01_midi_channels.yaml` from the example with exact port
names and user-facing channels 1-16, then run:

```powershell
& .\.venv\Scripts\python.exe .\tools\rush01_midi_apply.py --device rytm --config .\config\rush01_midi_channels.yaml --dry-run --output .\output\RUSH01_RYTM_midi_plan.json
& .\.venv\Scripts\python.exe .\tools\rush01_midi_apply.py --device a4 --config .\config\rush01_midi_channels.yaml --dry-run --output .\output\RUSH01_A4_midi_plan.json
```

The default is already dry-run; the explicit flag is shown for operator
clarity. These commands compile and write exact channelized byte sequences
without opening an output port.

## List-Port Commands

```powershell
& .\.venv\Scripts\python.exe .\tools\rush01_midi_apply.py --list-ports
& .\.venv\Scripts\python.exe .\tools\rush01_midi_learn.py --list-ports
```

The first command lists input and output names. The second lists input names.
Neither command opens a port or transmits MIDI.

## Calibration Commands

Input capture is exact-name and input-only. Example targeted observations:

```powershell
& .\.venv\Scripts\python.exe .\tools\rush01_midi_learn.py --device rytm --input-port "EXACT INPUT NAME" --parameter "tracks.BD.synth.Waveform" --point enum --enum-label "OBSERVED LABEL"
& .\.venv\Scripts\python.exe .\tools\rush01_midi_learn.py --device a4 --input-port "EXACT INPUT NAME" --parameter "tracks.T1.oscillator_1.coarse_tune_semitones" --point center
```

Observations remain `observed_only`; the learner never promotes one capture
to a verified converter.

## Safety Enforcement

- Exactly one `--device` is accepted per invocation.
- Output and input selection require one exact, unique name; fuzzy matching is
  rejected.
- Dry-run constructs no MIDI provider and opens no output.
- Apply requires a final confirmation unless the explicit long-form bypass is
  supplied.
- Invalid specification fields block apply before port discovery.
- The transport accepts only three-byte Control Change packets with data bytes
  in `0..127` and controllers in `0..119`. Program Change, transport, SysEx,
  channel-mode, save, and project messages cannot enter the compiled plan.
- Ctrl+C closes any explicitly opened input or output in `finally` cleanup.

## Verification

- Ruff, Black, and isort checks pass repository-wide. Black reported only a
  sandbox cache-read warning; all 696 files were unchanged by its check.
- Architecture gates: 671 passed. The existing generic-`main` abstraction
  warning remains warn-only; pytest also reported its sandbox cache warning.
- Focused compiler, validation, transport, observation, reference-codec, and
  data-layer suite: 147 passed.
- Touched-file branch coverage: 140 passed, 100.00% statements and branches
  across the data bindings, compiler, transport, observation reducer, and both
  CLIs.
- Complete repository suite: 6255 passed, 3 skipped, 0 failed in 181.22
  seconds using four xdist workers. The default 24-worker attempt exhausted
  two architecture-scanner workers; the lower-concurrency rerun passed all
  6258 collected items.

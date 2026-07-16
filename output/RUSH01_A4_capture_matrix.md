# Analog Four MKII RUSH01 Saved-Kit Capture Matrix

This is a calibration workbench, not the final delivery path. Do not run the
operator commands during the coding phase. Each future capture changes exactly
one semantic parameter and exports one saved/current KIT dump.

## Status

- Reference: `reference/A4_Test1_Init_Kit.syx`
- Reference round trip byte-identical: `true`
- Critical fields: `244`
- Mapped: `0`
- Preserve reference: `4`
- Capture required: `228`
- Candidate only: `12`
- Unresolved critical fields: `240`
- Minimal changed-dump captures: `254`
- Supplied differential dumps decoded in this run: `0`
- Writer ready: `false`

## Reused Components

- Rytm one-control mutation: `python -m rytm_randomizer.app --arm --validate-one-cc`; this calls `rytm_randomizer.midi_io.send_cc`.
- A4 one-parameter mutation: `--a4-send-param` or `--a4-send-nrpn-param`; these call `rytm_randomizer.midi_io.send_cc` / `send_nrpn`.
- Existing generic plan sender: `rytm_randomizer.senders.midi_event_plan.send_cc_nrpn_event_plan`.
- Current-kit receive API: `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`.
- Existing live receiver wrapper: `rytm_randomizer.app._capture_rytm_snapshot_shell_anchor_from_live_input`.
- File framing/decoding: `snapshot.sysex_file.extract_sysex_payloads` plus the reference-bound Elektron kit codec.

The receiver currently decodes live Rytm frames in memory; it does not persist a
capture filename. For calibration, call the existing receiver API directly and write
the returned complete frame to the exact matrix filename. No second transport is needed.

## Operator Protocol

1. Restore the approved initialized kit represented by the reference dump.
2. Change only the listed semantic parameter, using the existing command when one is supplied; otherwise use the front panel.
3. Export only the current/saved KIT to the exact changed-dump filename.
4. Restore the baseline before the next observation.
5. Do not promote a location from one track. A second-track witness is mandatory.
6. Do not derive signed, bipolar, enum, boolean, or high-resolution conversion from a single observation.

## Capture Groups

### `a4.track_level`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `track_levels.T1` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>100 / raw 100 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_track_levels_t1_min.syx`<br>`calibration/sysex/a4/A4_T1_track_levels_t1_mid.syx`<br>`calibration/sysex/a4/A4_T1_track_levels_t1_max.syx`<br>`calibration/sysex/a4/A4_T1_track_levels_t1_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Track Level |
| `track_levels.T2` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_track_levels_t2_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Track Level |
| `track_levels.T3` | T3 | `direct_7bit` | reuse `track_levels.T1` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `track_levels.T1` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Track Level |
| `track_levels.T4` | T4 | `direct_7bit` | reuse `track_levels.T1` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `track_levels.T1` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Track Level |

Commands:

- `track_levels.T1` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-param --parameter "Track Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `track_levels.T1` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-param --parameter "Track Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `track_levels.T1` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-param --parameter "Track Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `track_levels.T1` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-param --parameter "Track Level" --channel <T1_CHANNEL_0_BASED> --value 100
- `track_levels.T2` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-param --parameter "Track Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.coarse_tune_semitones`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.coarse_tune_semitones` | T1 | `high_resolution` | one exact encoder step below baseline / raw unknown<br>one exact encoder step above baseline / raw unknown<br>0 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_coarse_tune_semitones_step_down.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_coarse_tune_semitones_step_up.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_coarse_tune_semitones_requested.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T2.oscillator_1.coarse_tune_semitones` | T2 | `high_resolution` | one exact encoder step below baseline / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_coarse_tune_semitones_stride_step_down.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T3.oscillator_1.coarse_tune_semitones` | T3 | `high_resolution` | reuse `tracks.T1.oscillator_1.coarse_tune_semitones` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.coarse_tune_semitones` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T4.oscillator_1.coarse_tune_semitones` | T4 | `high_resolution` | reuse `tracks.T1.oscillator_1.coarse_tune_semitones` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.coarse_tune_semitones` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |

Commands:

- `tracks.T1.oscillator_1.coarse_tune_semitones` / `step_down`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.coarse_tune_semitones` / `step_up`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.coarse_tune_semitones` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_1.coarse_tune_semitones` / `step_down`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.fine_tune_cents`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.fine_tune_cents` | T1 | `high_resolution` | one exact encoder step below baseline / raw unknown<br>one exact encoder step above baseline / raw unknown<br>0 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_fine_tune_cents_step_down.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_fine_tune_cents_step_up.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_fine_tune_cents_requested.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T2.oscillator_1.fine_tune_cents` | T2 | `high_resolution` | one exact encoder step below baseline / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_fine_tune_cents_stride_step_down.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T3.oscillator_1.fine_tune_cents` | T3 | `high_resolution` | reuse `tracks.T1.oscillator_1.fine_tune_cents` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.fine_tune_cents` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T4.oscillator_1.fine_tune_cents` | T4 | `high_resolution` | reuse `tracks.T1.oscillator_1.fine_tune_cents` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.fine_tune_cents` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |

Commands:

- `tracks.T1.oscillator_1.fine_tune_cents` / `step_down`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.fine_tune_cents` / `step_up`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.fine_tune_cents` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_1.fine_tune_cents` / `step_down`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.linear_detune_hz`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.linear_detune_hz` | T1 | `unverified_conversion` | one exact front-panel step below baseline / raw unknown<br>one exact front-panel step above baseline / raw unknown<br>0 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_linear_detune_hz_step_down.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_linear_detune_hz_step_up.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_linear_detune_hz_requested.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T2.oscillator_1.linear_detune_hz` | T2 | `unverified_conversion` | one exact front-panel step below baseline / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_linear_detune_hz_stride_step_down.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T3.oscillator_1.linear_detune_hz` | T3 | `unverified_conversion` | reuse `tracks.T1.oscillator_1.linear_detune_hz` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.linear_detune_hz` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T4.oscillator_1.linear_detune_hz` | T4 | `unverified_conversion` | reuse `tracks.T1.oscillator_1.linear_detune_hz` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.linear_detune_hz` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |

Commands:

- `tracks.T1.oscillator_1.linear_detune_hz` / `step_down`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.linear_detune_hz` / `step_up`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.linear_detune_hz` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_1.linear_detune_hz` / `step_down`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.keytrack`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.keytrack` | T1 | `boolean` | false/off / raw unknown<br>true/on / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_keytrack_false.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_keytrack_true.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T2.oscillator_1.keytrack` | T2 | `boolean` | false/off / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_keytrack_stride_false.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T3.oscillator_1.keytrack` | T3 | `boolean` | reuse `tracks.T1.oscillator_1.keytrack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.keytrack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T4.oscillator_1.keytrack` | T4 | `boolean` | reuse `tracks.T1.oscillator_1.keytrack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.keytrack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |

Commands:

- `tracks.T1.oscillator_1.keytrack` / `false`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.keytrack` / `true`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_1.keytrack` / `false`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.level`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.level` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>96 / raw 96 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_level_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_level_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_level_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_level_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for OSC1 Level |
| `tracks.T2.oscillator_1.level` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_level_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for OSC1 Level |
| `tracks.T3.oscillator_1.level` | T3 | `direct_7bit` | reuse `tracks.T1.oscillator_1.level` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.level` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for OSC1 Level |
| `tracks.T4.oscillator_1.level` | T4 | `direct_7bit` | reuse `tracks.T1.oscillator_1.level` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.level` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for OSC1 Level |

Commands:

- `tracks.T1.oscillator_1.level` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_1.level` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_1.level` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.oscillator_1.level` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Level" --channel <T1_CHANNEL_0_BASED> --value 96
- `tracks.T2.oscillator_1.level` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.waveform`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.waveform` | T1 | `enum` | one named option other than the request / raw unknown<br>triangle / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_waveform_baseline_alternative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_waveform_requested.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T2.oscillator_1.waveform` | T2 | `enum` | one named option other than the request / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_waveform_stride_baseline_alternative.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T3.oscillator_1.waveform` | T3 | `enum` | reuse `tracks.T1.oscillator_1.waveform` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.waveform` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T4.oscillator_1.waveform` | T4 | `enum` | reuse `tracks.T1.oscillator_1.waveform` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.waveform` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |

Commands:

- `tracks.T1.oscillator_1.waveform` / `baseline_alternative`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.waveform` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_1.waveform` / `baseline_alternative`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.sub_oscillator`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.sub_oscillator` | T1 | `enum` | one named option other than the request / raw unknown<br>off / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_sub_oscillator_baseline_alternative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_sub_oscillator_requested.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T2.oscillator_1.sub_oscillator` | T2 | `enum` | one named option other than the request / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_sub_oscillator_stride_baseline_alternative.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T3.oscillator_1.sub_oscillator` | T3 | `enum` | reuse `tracks.T1.oscillator_1.sub_oscillator` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.sub_oscillator` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T4.oscillator_1.sub_oscillator` | T4 | `enum` | reuse `tracks.T1.oscillator_1.sub_oscillator` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.sub_oscillator` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |

Commands:

- `tracks.T1.oscillator_1.sub_oscillator` / `baseline_alternative`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_1.sub_oscillator` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_1.sub_oscillator` / `baseline_alternative`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.pulse_width`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.pulse_width` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pulse_width_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pulse_width_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pulse_width_positive.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.oscillator_1.pulse_width` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_pulse_width_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.oscillator_1.pulse_width` | T3 | `bipolar_7bit` | reuse `tracks.T1.oscillator_1.pulse_width` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.pulse_width` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.oscillator_1.pulse_width` | T4 | `bipolar_7bit` | reuse `tracks.T1.oscillator_1.pulse_width` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.pulse_width` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.oscillator_1.pulse_width` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Pulsewidth" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_1.pulse_width` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Pulsewidth" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_1.pulse_width` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Pulsewidth" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_1.pulse_width` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 Pulsewidth" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.pwm_speed`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.pwm_speed` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pwm_speed_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pwm_speed_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pwm_speed_positive.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.oscillator_1.pwm_speed` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_pwm_speed_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.oscillator_1.pwm_speed` | T3 | `bipolar_7bit` | reuse `tracks.T1.oscillator_1.pwm_speed` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.pwm_speed` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.oscillator_1.pwm_speed` | T4 | `bipolar_7bit` | reuse `tracks.T1.oscillator_1.pwm_speed` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.pwm_speed` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.oscillator_1.pwm_speed` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 PWM Speed" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_1.pwm_speed` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 PWM Speed" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_1.pwm_speed` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 PWM Speed" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_1.pwm_speed` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 PWM Speed" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_1.pwm_depth`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_1.pwm_depth` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pwm_depth_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pwm_depth_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_1_pwm_depth_positive.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.oscillator_1.pwm_depth` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_1_pwm_depth_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.oscillator_1.pwm_depth` | T3 | `bipolar_7bit` | reuse `tracks.T1.oscillator_1.pwm_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.pwm_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.oscillator_1.pwm_depth` | T4 | `bipolar_7bit` | reuse `tracks.T1.oscillator_1.pwm_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_1.pwm_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.oscillator_1.pwm_depth` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 PWM Depth" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_1.pwm_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 PWM Depth" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_1.pwm_depth` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 PWM Depth" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_1.pwm_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC1 PWM Depth" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.coarse_tune_semitones`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.coarse_tune_semitones` | T1 | `high_resolution` | one exact encoder step below baseline / raw unknown<br>one exact encoder step above baseline / raw unknown<br>12 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_coarse_tune_semitones_step_down.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_coarse_tune_semitones_step_up.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_coarse_tune_semitones_requested.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T2.oscillator_2.coarse_tune_semitones` | T2 | `high_resolution` | one exact encoder step below baseline / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_coarse_tune_semitones_stride_step_down.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T3.oscillator_2.coarse_tune_semitones` | T3 | `high_resolution` | reuse `tracks.T1.oscillator_2.coarse_tune_semitones` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.coarse_tune_semitones` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T4.oscillator_2.coarse_tune_semitones` | T4 | `high_resolution` | reuse `tracks.T1.oscillator_2.coarse_tune_semitones` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.coarse_tune_semitones` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |

Commands:

- `tracks.T1.oscillator_2.coarse_tune_semitones` / `step_down`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.coarse_tune_semitones` / `step_up`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.coarse_tune_semitones` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_2.coarse_tune_semitones` / `step_down`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.fine_tune_cents`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.fine_tune_cents` | T1 | `high_resolution` | one exact encoder step below baseline / raw unknown<br>one exact encoder step above baseline / raw unknown<br>-6 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_fine_tune_cents_step_down.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_fine_tune_cents_step_up.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_fine_tune_cents_requested.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T2.oscillator_2.fine_tune_cents` | T2 | `high_resolution` | one exact encoder step below baseline / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_fine_tune_cents_stride_step_down.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T3.oscillator_2.fine_tune_cents` | T3 | `high_resolution` | reuse `tracks.T1.oscillator_2.fine_tune_cents` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.fine_tune_cents` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |
| `tracks.T4.oscillator_2.fine_tune_cents` | T4 | `high_resolution` | reuse `tracks.T1.oscillator_2.fine_tune_cents` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.fine_tune_cents` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>coarse and fine-step observations proving the full-resolution encoding |

Commands:

- `tracks.T1.oscillator_2.fine_tune_cents` / `step_down`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.fine_tune_cents` / `step_up`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.fine_tune_cents` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_2.fine_tune_cents` / `step_down`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.linear_detune_hz`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.linear_detune_hz` | T1 | `unverified_conversion` | one exact front-panel step below baseline / raw unknown<br>one exact front-panel step above baseline / raw unknown<br>0 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_linear_detune_hz_step_down.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_linear_detune_hz_step_up.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_linear_detune_hz_requested.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T2.oscillator_2.linear_detune_hz` | T2 | `unverified_conversion` | one exact front-panel step below baseline / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_linear_detune_hz_stride_step_down.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T3.oscillator_2.linear_detune_hz` | T3 | `unverified_conversion` | reuse `tracks.T1.oscillator_2.linear_detune_hz` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.linear_detune_hz` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T4.oscillator_2.linear_detune_hz` | T4 | `unverified_conversion` | reuse `tracks.T1.oscillator_2.linear_detune_hz` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.linear_detune_hz` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |

Commands:

- `tracks.T1.oscillator_2.linear_detune_hz` / `step_down`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.linear_detune_hz` / `step_up`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.linear_detune_hz` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_2.linear_detune_hz` / `step_down`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.keytrack`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.keytrack` | T1 | `boolean` | false/off / raw unknown<br>true/on / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_keytrack_false.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_keytrack_true.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T2.oscillator_2.keytrack` | T2 | `boolean` | false/off / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_keytrack_stride_false.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T3.oscillator_2.keytrack` | T3 | `boolean` | reuse `tracks.T1.oscillator_2.keytrack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.keytrack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T4.oscillator_2.keytrack` | T4 | `boolean` | reuse `tracks.T1.oscillator_2.keytrack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.keytrack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |

Commands:

- `tracks.T1.oscillator_2.keytrack` / `false`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.keytrack` / `true`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_2.keytrack` / `false`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.level`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.level` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>38 / raw 38 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_level_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_level_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_level_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_level_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for OSC2 Level |
| `tracks.T2.oscillator_2.level` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_level_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for OSC2 Level |
| `tracks.T3.oscillator_2.level` | T3 | `direct_7bit` | reuse `tracks.T1.oscillator_2.level` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.level` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for OSC2 Level |
| `tracks.T4.oscillator_2.level` | T4 | `direct_7bit` | reuse `tracks.T1.oscillator_2.level` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.level` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for OSC2 Level |

Commands:

- `tracks.T1.oscillator_2.level` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_2.level` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_2.level` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.oscillator_2.level` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Level" --channel <T1_CHANNEL_0_BASED> --value 38
- `tracks.T2.oscillator_2.level` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.waveform`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.waveform` | T1 | `enum` | one named option other than the request / raw unknown<br>transistor_pulse / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_waveform_baseline_alternative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_waveform_requested.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T2.oscillator_2.waveform` | T2 | `enum` | one named option other than the request / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_waveform_stride_baseline_alternative.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T3.oscillator_2.waveform` | T3 | `enum` | reuse `tracks.T1.oscillator_2.waveform` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.waveform` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T4.oscillator_2.waveform` | T4 | `enum` | reuse `tracks.T1.oscillator_2.waveform` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.waveform` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |

Commands:

- `tracks.T1.oscillator_2.waveform` / `baseline_alternative`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.waveform` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_2.waveform` / `baseline_alternative`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.sub_oscillator`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.sub_oscillator` | T1 | `enum` | one named option other than the request / raw unknown<br>off / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_sub_oscillator_baseline_alternative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_sub_oscillator_requested.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T2.oscillator_2.sub_oscillator` | T2 | `enum` | one named option other than the request / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_sub_oscillator_stride_baseline_alternative.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T3.oscillator_2.sub_oscillator` | T3 | `enum` | reuse `tracks.T1.oscillator_2.sub_oscillator` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.sub_oscillator` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T4.oscillator_2.sub_oscillator` | T4 | `enum` | reuse `tracks.T1.oscillator_2.sub_oscillator` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.sub_oscillator` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |

Commands:

- `tracks.T1.oscillator_2.sub_oscillator` / `baseline_alternative`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_2.sub_oscillator` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_2.sub_oscillator` / `baseline_alternative`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.pulse_width`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.pulse_width` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127<br>42 / raw 106 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pulse_width_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pulse_width_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pulse_width_positive.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pulse_width_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.oscillator_2.pulse_width` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_pulse_width_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.oscillator_2.pulse_width` | T3 | `bipolar_7bit` | reuse `tracks.T1.oscillator_2.pulse_width` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.pulse_width` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.oscillator_2.pulse_width` | T4 | `bipolar_7bit` | reuse `tracks.T1.oscillator_2.pulse_width` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.pulse_width` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.oscillator_2.pulse_width` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Pulsewidth" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_2.pulse_width` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Pulsewidth" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_2.pulse_width` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Pulsewidth" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.oscillator_2.pulse_width` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Pulsewidth" --channel <T1_CHANNEL_0_BASED> --value 106
- `tracks.T2.oscillator_2.pulse_width` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 Pulsewidth" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.pwm_speed`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.pwm_speed` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pwm_speed_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pwm_speed_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pwm_speed_positive.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.oscillator_2.pwm_speed` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_pwm_speed_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.oscillator_2.pwm_speed` | T3 | `bipolar_7bit` | reuse `tracks.T1.oscillator_2.pwm_speed` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.pwm_speed` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.oscillator_2.pwm_speed` | T4 | `bipolar_7bit` | reuse `tracks.T1.oscillator_2.pwm_speed` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.pwm_speed` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.oscillator_2.pwm_speed` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 PWM Speed" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_2.pwm_speed` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 PWM Speed" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_2.pwm_speed` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 PWM Speed" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_2.pwm_speed` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 PWM Speed" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_2.pwm_depth`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_2.pwm_depth` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pwm_depth_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pwm_depth_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_2_pwm_depth_positive.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.oscillator_2.pwm_depth` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_2_pwm_depth_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.oscillator_2.pwm_depth` | T3 | `bipolar_7bit` | reuse `tracks.T1.oscillator_2.pwm_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.pwm_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.oscillator_2.pwm_depth` | T4 | `bipolar_7bit` | reuse `tracks.T1.oscillator_2.pwm_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_2.pwm_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.oscillator_2.pwm_depth` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 PWM Depth" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_2.pwm_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 PWM Depth" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_2.pwm_depth` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 PWM Depth" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_2.pwm_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "OSC2 PWM Depth" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.osc1_am`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.osc1_am` | T1 | `boolean` | false/off / raw unknown<br>true/on / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_osc1_am_false.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_osc1_am_true.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T2.oscillator_common.osc1_am` | T2 | `boolean` | false/off / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_osc1_am_stride_false.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T3.oscillator_common.osc1_am` | T3 | `boolean` | reuse `tracks.T1.oscillator_common.osc1_am` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.osc1_am` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T4.oscillator_common.osc1_am` | T4 | `boolean` | reuse `tracks.T1.oscillator_common.osc1_am` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.osc1_am` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |

Commands:

- `tracks.T1.oscillator_common.osc1_am` / `false`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_common.osc1_am` / `true`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_common.osc1_am` / `false`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.sync_mode`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.sync_mode` | T1 | `enum` | one named option other than the request / raw unknown<br>off / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_sync_mode_baseline_alternative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_sync_mode_requested.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T2.oscillator_common.sync_mode` | T2 | `enum` | one named option other than the request / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_sync_mode_stride_baseline_alternative.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T3.oscillator_common.sync_mode` | T3 | `enum` | reuse `tracks.T1.oscillator_common.sync_mode` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.sync_mode` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T4.oscillator_common.sync_mode` | T4 | `enum` | reuse `tracks.T1.oscillator_common.sync_mode` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.sync_mode` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |

Commands:

- `tracks.T1.oscillator_common.sync_mode` / `baseline_alternative`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_common.sync_mode` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_common.sync_mode` / `baseline_alternative`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.sync_amount`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.sync_amount` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_sync_amount_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_sync_amount_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_sync_amount_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Sync Amount |
| `tracks.T2.oscillator_common.sync_amount` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_sync_amount_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Sync Amount |
| `tracks.T3.oscillator_common.sync_amount` | T3 | `direct_7bit` | reuse `tracks.T1.oscillator_common.sync_amount` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.sync_amount` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Sync Amount |
| `tracks.T4.oscillator_common.sync_amount` | T4 | `direct_7bit` | reuse `tracks.T1.oscillator_common.sync_amount` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.sync_amount` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Sync Amount |

Commands:

- `tracks.T1.oscillator_common.sync_amount` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Sync Amount" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_common.sync_amount` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Sync Amount" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_common.sync_amount` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Sync Amount" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_common.sync_amount` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Sync Amount" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.bend_depth`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.bend_depth` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127<br>7 / raw 71 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_bend_depth_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_bend_depth_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_bend_depth_positive.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_bend_depth_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.oscillator_common.bend_depth` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_bend_depth_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.oscillator_common.bend_depth` | T3 | `bipolar_7bit` | reuse `tracks.T1.oscillator_common.bend_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.bend_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.oscillator_common.bend_depth` | T4 | `bipolar_7bit` | reuse `tracks.T1.oscillator_common.bend_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.bend_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.oscillator_common.bend_depth` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Bend Amount" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_common.bend_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Bend Amount" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_common.bend_depth` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Bend Amount" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.oscillator_common.bend_depth` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Bend Amount" --channel <T1_CHANNEL_0_BASED> --value 71
- `tracks.T2.oscillator_common.bend_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Bend Amount" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.note_slide_time`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.note_slide_time` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>10 / raw 10 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_note_slide_time_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_note_slide_time_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_note_slide_time_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_note_slide_time_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Slide Time |
| `tracks.T2.oscillator_common.note_slide_time` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_note_slide_time_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Slide Time |
| `tracks.T3.oscillator_common.note_slide_time` | T3 | `direct_7bit` | reuse `tracks.T1.oscillator_common.note_slide_time` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.note_slide_time` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Slide Time |
| `tracks.T4.oscillator_common.note_slide_time` | T4 | `direct_7bit` | reuse `tracks.T1.oscillator_common.note_slide_time` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.note_slide_time` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Slide Time |

Commands:

- `tracks.T1.oscillator_common.note_slide_time` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Slide Time" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_common.note_slide_time` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Slide Time" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_common.note_slide_time` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Slide Time" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.oscillator_common.note_slide_time` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Slide Time" --channel <T1_CHANNEL_0_BASED> --value 10
- `tracks.T2.oscillator_common.note_slide_time` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Slide Time" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.osc2_am`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.osc2_am` | T1 | `boolean` | false/off / raw unknown<br>true/on / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_osc2_am_false.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_osc2_am_true.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T2.oscillator_common.osc2_am` | T2 | `boolean` | false/off / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_osc2_am_stride_false.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T3.oscillator_common.osc2_am` | T3 | `boolean` | reuse `tracks.T1.oscillator_common.osc2_am` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.osc2_am` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T4.oscillator_common.osc2_am` | T4 | `boolean` | reuse `tracks.T1.oscillator_common.osc2_am` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.osc2_am` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |

Commands:

- `tracks.T1.oscillator_common.osc2_am` / `false`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_common.osc2_am` / `true`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_common.osc2_am` / `false`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.oscillator_retrigger`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.oscillator_retrigger` | T1 | `boolean` | false/off / raw unknown<br>true/on / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_oscillator_retrigger_false.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_oscillator_retrigger_true.syx` | 2 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T2.oscillator_common.oscillator_retrigger` | T2 | `boolean` | false/off / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_oscillator_retrigger_stride_false.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T3.oscillator_common.oscillator_retrigger` | T3 | `boolean` | reuse `tracks.T1.oscillator_common.oscillator_retrigger` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.oscillator_retrigger` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |
| `tracks.T4.oscillator_common.oscillator_retrigger` | T4 | `boolean` | reuse `tracks.T1.oscillator_common.oscillator_retrigger` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.oscillator_retrigger` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>both front-panel boolean states |

Commands:

- `tracks.T1.oscillator_common.oscillator_retrigger` / `false`: front panel only; no raw MIDI command emitted
- `tracks.T1.oscillator_common.oscillator_retrigger` / `true`: front panel only; no raw MIDI command emitted
- `tracks.T2.oscillator_common.oscillator_retrigger` / `false`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.vibrato_fade`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.vibrato_fade` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_fade_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_fade_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_fade_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Vibrato Fade |
| `tracks.T2.oscillator_common.vibrato_fade` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_vibrato_fade_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Vibrato Fade |
| `tracks.T3.oscillator_common.vibrato_fade` | T3 | `direct_7bit` | reuse `tracks.T1.oscillator_common.vibrato_fade` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.vibrato_fade` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Vibrato Fade |
| `tracks.T4.oscillator_common.vibrato_fade` | T4 | `direct_7bit` | reuse `tracks.T1.oscillator_common.vibrato_fade` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.vibrato_fade` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Vibrato Fade |

Commands:

- `tracks.T1.oscillator_common.vibrato_fade` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Fade" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_common.vibrato_fade` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Fade" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_common.vibrato_fade` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Fade" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_common.vibrato_fade` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Fade" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.vibrato_speed`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.vibrato_speed` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_speed_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_speed_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_speed_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Vibrato Speed |
| `tracks.T2.oscillator_common.vibrato_speed` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_vibrato_speed_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Vibrato Speed |
| `tracks.T3.oscillator_common.vibrato_speed` | T3 | `direct_7bit` | reuse `tracks.T1.oscillator_common.vibrato_speed` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.vibrato_speed` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Vibrato Speed |
| `tracks.T4.oscillator_common.vibrato_speed` | T4 | `direct_7bit` | reuse `tracks.T1.oscillator_common.vibrato_speed` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.vibrato_speed` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Vibrato Speed |

Commands:

- `tracks.T1.oscillator_common.vibrato_speed` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Speed" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_common.vibrato_speed` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Speed" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_common.vibrato_speed` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Speed" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_common.vibrato_speed` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Speed" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.oscillator_common.vibrato_depth`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.oscillator_common.vibrato_depth` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_depth_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_depth_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_oscillator_common_vibrato_depth_positive.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.oscillator_common.vibrato_depth` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_oscillator_common_vibrato_depth_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.oscillator_common.vibrato_depth` | T3 | `bipolar_7bit` | reuse `tracks.T1.oscillator_common.vibrato_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.vibrato_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.oscillator_common.vibrato_depth` | T4 | `bipolar_7bit` | reuse `tracks.T1.oscillator_common.vibrato_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.oscillator_common.vibrato_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.oscillator_common.vibrato_depth` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Depth" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.oscillator_common.vibrato_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Depth" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.oscillator_common.vibrato_depth` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Depth" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.oscillator_common.vibrato_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Vibrato Depth" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.noise.sample_and_hold`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.noise.sample_and_hold` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_noise_sample_and_hold_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_noise_sample_and_hold_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_noise_sample_and_hold_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise S&H |
| `tracks.T2.noise.sample_and_hold` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_noise_sample_and_hold_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise S&H |
| `tracks.T3.noise.sample_and_hold` | T3 | `direct_7bit` | reuse `tracks.T1.noise.sample_and_hold` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.noise.sample_and_hold` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise S&H |
| `tracks.T4.noise.sample_and_hold` | T4 | `direct_7bit` | reuse `tracks.T1.noise.sample_and_hold` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.noise.sample_and_hold` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise S&H |

Commands:

- `tracks.T1.noise.sample_and_hold` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise S&H" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.noise.sample_and_hold` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise S&H" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.noise.sample_and_hold` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise S&H" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.noise.sample_and_hold` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise S&H" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.noise.color`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.noise.color` | T1 | `unmapped` | one exact front-panel step below baseline / raw unknown<br>one exact front-panel step above baseline / raw unknown<br>0 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_noise_color_step_down.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_noise_color_step_up.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_noise_color_requested.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T2.noise.color` | T2 | `unmapped` | one exact front-panel step below baseline / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_noise_color_stride_step_down.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T3.noise.color` | T3 | `unmapped` | reuse `tracks.T1.noise.color` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.noise.color` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |
| `tracks.T4.noise.color` | T4 | `unmapped` | reuse `tracks.T1.noise.color` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.noise.color` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple front-panel observations; no raw MIDI value may be inferred |

Commands:

- `tracks.T1.noise.color` / `step_down`: front panel only; no raw MIDI command emitted
- `tracks.T1.noise.color` / `step_up`: front panel only; no raw MIDI command emitted
- `tracks.T1.noise.color` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.noise.color` / `step_down`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.noise.fade`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.noise.fade` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_noise_fade_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_noise_fade_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_noise_fade_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise Fade |
| `tracks.T2.noise.fade` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_noise_fade_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise Fade |
| `tracks.T3.noise.fade` | T3 | `direct_7bit` | reuse `tracks.T1.noise.fade` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.noise.fade` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise Fade |
| `tracks.T4.noise.fade` | T4 | `direct_7bit` | reuse `tracks.T1.noise.fade` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.noise.fade` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise Fade |

Commands:

- `tracks.T1.noise.fade` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise Fade" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.noise.fade` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise Fade" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.noise.fade` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise Fade" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.noise.fade` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise Fade" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.noise.level`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.noise.level` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_noise_level_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_noise_level_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_noise_level_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise Level |
| `tracks.T2.noise.level` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_noise_level_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise Level |
| `tracks.T3.noise.level` | T3 | `direct_7bit` | reuse `tracks.T1.noise.level` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.noise.level` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise Level |
| `tracks.T4.noise.level` | T4 | `direct_7bit` | reuse `tracks.T1.noise.level` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.noise.level` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Noise Level |

Commands:

- `tracks.T1.noise.level` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.noise.level` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.noise.level` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.noise.level` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Noise Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_1.frequency`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_1.frequency` | T1 | `high_resolution` | 0.00 / raw unknown<br>one exact encoder step above minimum / raw unknown<br>63.50 / raw unknown<br>127.00 / raw unknown<br>46 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_1_frequency_minimum.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_frequency_fine_step.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_frequency_midpoint.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_frequency_maximum.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_frequency_requested.syx` | 5 | packed `0x009C`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T2.filter_1.frequency` | T2 | `high_resolution` | 0.00 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_1_frequency_stride_minimum.syx` | 1 | packed `0x022C`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T3.filter_1.frequency` | T3 | `high_resolution` | reuse `tracks.T1.filter_1.frequency` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.frequency` | 0 | packed `0x03BC`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T4.filter_1.frequency` | T4 | `high_resolution` | reuse `tracks.T1.filter_1.frequency` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.frequency` | 0 | packed `0x054C`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |

Commands:

- `tracks.T1.filter_1.frequency` / `minimum`: front panel only; no raw MIDI command emitted
- `tracks.T1.filter_1.frequency` / `fine_step`: front panel only; no raw MIDI command emitted
- `tracks.T1.filter_1.frequency` / `midpoint`: front panel only; no raw MIDI command emitted
- `tracks.T1.filter_1.frequency` / `maximum`: front panel only; no raw MIDI command emitted
- `tracks.T1.filter_1.frequency` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.filter_1.frequency` / `minimum`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_1.resonance`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_1.resonance` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>18 / raw 18 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_1_resonance_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_resonance_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_resonance_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_resonance_requested.syx` | 4 | packed `0x009E`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T2.filter_1.resonance` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_1_resonance_stride_mid.syx` | 1 | packed `0x022E`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T3.filter_1.resonance` | T3 | `direct_7bit` | reuse `tracks.T1.filter_1.resonance` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.resonance` | 0 | packed `0x03BE`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T4.filter_1.resonance` | T4 | `direct_7bit` | reuse `tracks.T1.filter_1.resonance` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.resonance` | 0 | packed `0x054E`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |

Commands:

- `tracks.T1.filter_1.resonance` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Resonance" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_1.resonance` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Resonance" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_1.resonance` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Resonance" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.filter_1.resonance` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Resonance" --channel <T1_CHANNEL_0_BASED> --value 18
- `tracks.T2.filter_1.resonance` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Resonance" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_1.overdrive`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_1.overdrive` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127<br>-16 / raw 48 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_1_overdrive_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_overdrive_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_overdrive_positive.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_overdrive_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.filter_1.overdrive` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_1_overdrive_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.filter_1.overdrive` | T3 | `bipolar_7bit` | reuse `tracks.T1.filter_1.overdrive` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.overdrive` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.filter_1.overdrive` | T4 | `bipolar_7bit` | reuse `tracks.T1.filter_1.overdrive` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.overdrive` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.filter_1.overdrive` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter Overdrive" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_1.overdrive` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter Overdrive" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_1.overdrive` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter Overdrive" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.filter_1.overdrive` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter Overdrive" --channel <T1_CHANNEL_0_BASED> --value 48
- `tracks.T2.filter_1.overdrive` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter Overdrive" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_1.keytrack`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_1.keytrack` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>24 / raw 24 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_1_keytrack_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_keytrack_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_keytrack_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_keytrack_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter1 Keytracking |
| `tracks.T2.filter_1.keytrack` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_1_keytrack_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter1 Keytracking |
| `tracks.T3.filter_1.keytrack` | T3 | `direct_7bit` | reuse `tracks.T1.filter_1.keytrack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.keytrack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter1 Keytracking |
| `tracks.T4.filter_1.keytrack` | T4 | `direct_7bit` | reuse `tracks.T1.filter_1.keytrack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.keytrack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter1 Keytracking |

Commands:

- `tracks.T1.filter_1.keytrack` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Keytracking" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_1.keytrack` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Keytracking" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_1.keytrack` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Keytracking" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.filter_1.keytrack` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Keytracking" --channel <T1_CHANNEL_0_BASED> --value 24
- `tracks.T2.filter_1.keytrack` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Keytracking" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_1.envelope_depth`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_1.envelope_depth` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127<br>48 / raw 112 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_1_envelope_depth_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_envelope_depth_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_envelope_depth_positive.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_1_envelope_depth_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.filter_1.envelope_depth` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_1_envelope_depth_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.filter_1.envelope_depth` | T3 | `bipolar_7bit` | reuse `tracks.T1.filter_1.envelope_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.envelope_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.filter_1.envelope_depth` | T4 | `bipolar_7bit` | reuse `tracks.T1.filter_1.envelope_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_1.envelope_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.filter_1.envelope_depth` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Envelope Amount" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_1.envelope_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Envelope Amount" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_1.envelope_depth` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Envelope Amount" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.filter_1.envelope_depth` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Envelope Amount" --channel <T1_CHANNEL_0_BASED> --value 112
- `tracks.T2.filter_1.envelope_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter1 Envelope Amount" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_2.frequency`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_2.frequency` | T1 | `high_resolution` | 0.00 / raw unknown<br>one exact encoder step above minimum / raw unknown<br>63.50 / raw unknown<br>127.00 / raw unknown<br>24 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_2_frequency_minimum.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_frequency_fine_step.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_frequency_midpoint.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_frequency_maximum.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_frequency_requested.syx` | 5 | packed `0x00A7`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T2.filter_2.frequency` | T2 | `high_resolution` | 0.00 / raw unknown | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_2_frequency_stride_minimum.syx` | 1 | packed `0x0237`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T3.filter_2.frequency` | T3 | `high_resolution` | reuse `tracks.T1.filter_2.frequency` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.frequency` | 0 | packed `0x03C7`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |
| `tracks.T4.filter_2.frequency` | T4 | `high_resolution` | reuse `tracks.T1.filter_2.frequency` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.frequency` | 0 | packed `0x0557`; unpacked stride `350`; packed stride `400`; not promoted for this field | supply or reproduce every recorded candidate differential dump<br>observe fine/intermediate values needed for the requested target<br>promote a typed writer only after semantic decode/encode tests pass |

Commands:

- `tracks.T1.filter_2.frequency` / `minimum`: front panel only; no raw MIDI command emitted
- `tracks.T1.filter_2.frequency` / `fine_step`: front panel only; no raw MIDI command emitted
- `tracks.T1.filter_2.frequency` / `midpoint`: front panel only; no raw MIDI command emitted
- `tracks.T1.filter_2.frequency` / `maximum`: front panel only; no raw MIDI command emitted
- `tracks.T1.filter_2.frequency` / `requested`: front panel only; no raw MIDI command emitted
- `tracks.T2.filter_2.frequency` / `minimum`: front panel only; no raw MIDI command emitted

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_2.resonance`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_2.resonance` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>6 / raw 6 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_2_resonance_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_resonance_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_resonance_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_resonance_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter2 Resonance |
| `tracks.T2.filter_2.resonance` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_2_resonance_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter2 Resonance |
| `tracks.T3.filter_2.resonance` | T3 | `direct_7bit` | reuse `tracks.T1.filter_2.resonance` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.resonance` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter2 Resonance |
| `tracks.T4.filter_2.resonance` | T4 | `direct_7bit` | reuse `tracks.T1.filter_2.resonance` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.resonance` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter2 Resonance |

Commands:

- `tracks.T1.filter_2.resonance` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Resonance" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_2.resonance` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Resonance" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_2.resonance` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Resonance" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.filter_2.resonance` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Resonance" --channel <T1_CHANNEL_0_BASED> --value 6
- `tracks.T2.filter_2.resonance` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Resonance" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_2.type`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_2.type` | T1 | `enum` | LP2 / raw 0<br>LP1 / raw 1<br>BP / raw 2<br>HP1 / raw 3<br>HP2 / raw 4<br>BS / raw 5<br>PK / raw 6 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_2_type_lp2.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_type_lp1.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_type_bp.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_type_hp1.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_type_hp2.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_type_bs.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_type_pk.syx` | 7 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T2.filter_2.type` | T2 | `enum` | LP2 / raw 0 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_2_type_stride_lp2.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T3.filter_2.type` | T3 | `enum` | reuse `tracks.T1.filter_2.type` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.type` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T4.filter_2.type` | T4 | `enum` | reuse `tracks.T1.filter_2.type` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.type` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |

Commands:

- `tracks.T1.filter_2.type` / `LP2`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Type" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_2.type` / `LP1`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Type" --channel <T1_CHANNEL_0_BASED> --value 1
- `tracks.T1.filter_2.type` / `BP`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Type" --channel <T1_CHANNEL_0_BASED> --value 2
- `tracks.T1.filter_2.type` / `HP1`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Type" --channel <T1_CHANNEL_0_BASED> --value 3
- `tracks.T1.filter_2.type` / `HP2`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Type" --channel <T1_CHANNEL_0_BASED> --value 4
- `tracks.T1.filter_2.type` / `BS`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Type" --channel <T1_CHANNEL_0_BASED> --value 5
- `tracks.T1.filter_2.type` / `PK`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Type" --channel <T1_CHANNEL_0_BASED> --value 6
- `tracks.T2.filter_2.type` / `LP2`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Type" --channel <T2_CHANNEL_0_BASED> --value 0

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_2.keytrack`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_2.keytrack` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_2_keytrack_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_keytrack_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_keytrack_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter2 Keytracking |
| `tracks.T2.filter_2.keytrack` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_2_keytrack_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter2 Keytracking |
| `tracks.T3.filter_2.keytrack` | T3 | `direct_7bit` | reuse `tracks.T1.filter_2.keytrack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.keytrack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter2 Keytracking |
| `tracks.T4.filter_2.keytrack` | T4 | `direct_7bit` | reuse `tracks.T1.filter_2.keytrack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.keytrack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Filter2 Keytracking |

Commands:

- `tracks.T1.filter_2.keytrack` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Keytracking" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_2.keytrack` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Keytracking" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_2.keytrack` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Keytracking" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.filter_2.keytrack` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Keytracking" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_2.envelope_depth`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_2.envelope_depth` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_2_envelope_depth_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_envelope_depth_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_2_envelope_depth_positive.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.filter_2.envelope_depth` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_2_envelope_depth_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.filter_2.envelope_depth` | T3 | `bipolar_7bit` | reuse `tracks.T1.filter_2.envelope_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.envelope_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.filter_2.envelope_depth` | T4 | `bipolar_7bit` | reuse `tracks.T1.filter_2.envelope_depth` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_2.envelope_depth` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.filter_2.envelope_depth` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Envelope Amount" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_2.envelope_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Envelope Amount" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_2.envelope_depth` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Envelope Amount" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.filter_2.envelope_depth` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Filter2 Envelope Amount" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.attack`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.attack` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_attack_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_attack_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_attack_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Attack Time |
| `tracks.T2.amp.attack` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_attack_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Attack Time |
| `tracks.T3.amp.attack` | T3 | `direct_7bit` | reuse `tracks.T1.amp.attack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.attack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Attack Time |
| `tracks.T4.amp.attack` | T4 | `direct_7bit` | reuse `tracks.T1.amp.attack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.attack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Attack Time |

Commands:

- `tracks.T1.amp.attack` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Attack Time" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.attack` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Attack Time" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.attack` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Attack Time" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.amp.attack` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Attack Time" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.decay`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.decay` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>32 / raw 32 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_decay_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_decay_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_decay_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_decay_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Decay Time |
| `tracks.T2.amp.decay` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_decay_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Decay Time |
| `tracks.T3.amp.decay` | T3 | `direct_7bit` | reuse `tracks.T1.amp.decay` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.decay` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Decay Time |
| `tracks.T4.amp.decay` | T4 | `direct_7bit` | reuse `tracks.T1.amp.decay` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.decay` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Decay Time |

Commands:

- `tracks.T1.amp.decay` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Decay Time" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.decay` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Decay Time" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.decay` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Decay Time" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.amp.decay` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Decay Time" --channel <T1_CHANNEL_0_BASED> --value 32
- `tracks.T2.amp.decay` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Decay Time" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.sustain`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.sustain` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_sustain_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_sustain_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_sustain_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Sustain Level |
| `tracks.T2.amp.sustain` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_sustain_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Sustain Level |
| `tracks.T3.amp.sustain` | T3 | `direct_7bit` | reuse `tracks.T1.amp.sustain` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.sustain` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Sustain Level |
| `tracks.T4.amp.sustain` | T4 | `direct_7bit` | reuse `tracks.T1.amp.sustain` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.sustain` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Sustain Level |

Commands:

- `tracks.T1.amp.sustain` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Sustain Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.sustain` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Sustain Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.sustain` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Sustain Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.amp.sustain` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Sustain Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.release`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.release` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>6 / raw 6 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_release_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_release_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_release_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_release_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Release Time |
| `tracks.T2.amp.release` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_release_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Release Time |
| `tracks.T3.amp.release` | T3 | `direct_7bit` | reuse `tracks.T1.amp.release` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.release` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Release Time |
| `tracks.T4.amp.release` | T4 | `direct_7bit` | reuse `tracks.T1.amp.release` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.release` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvA Release Time |

Commands:

- `tracks.T1.amp.release` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Release Time" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.release` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Release Time" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.release` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Release Time" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.amp.release` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Release Time" --channel <T1_CHANNEL_0_BASED> --value 6
- `tracks.T2.amp.release` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Release Time" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.envelope_shape`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.envelope_shape` | T1 | `enum` | triangle / raw 0<br>exponential / raw 1<br>linear / raw 2 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_envelope_shape_triangle.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_envelope_shape_exponential.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_envelope_shape_linear.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T2.amp.envelope_shape` | T2 | `enum` | triangle / raw 0 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_envelope_shape_stride_triangle.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T3.amp.envelope_shape` | T3 | `enum` | reuse `tracks.T1.amp.envelope_shape` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.envelope_shape` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T4.amp.envelope_shape` | T4 | `enum` | reuse `tracks.T1.amp.envelope_shape` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.envelope_shape` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |

Commands:

- `tracks.T1.amp.envelope_shape` / `triangle`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Env Shape" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.envelope_shape` / `exponential`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Env Shape" --channel <T1_CHANNEL_0_BASED> --value 1
- `tracks.T1.amp.envelope_shape` / `linear`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Env Shape" --channel <T1_CHANNEL_0_BASED> --value 2
- `tracks.T2.amp.envelope_shape` / `triangle`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvA Env Shape" --channel <T2_CHANNEL_0_BASED> --value 0

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.chorus_send`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.chorus_send` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_chorus_send_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_chorus_send_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_chorus_send_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Chorus Send Level |
| `tracks.T2.amp.chorus_send` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_chorus_send_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Chorus Send Level |
| `tracks.T3.amp.chorus_send` | T3 | `direct_7bit` | reuse `tracks.T1.amp.chorus_send` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.chorus_send` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Chorus Send Level |
| `tracks.T4.amp.chorus_send` | T4 | `direct_7bit` | reuse `tracks.T1.amp.chorus_send` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.chorus_send` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Chorus Send Level |

Commands:

- `tracks.T1.amp.chorus_send` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Chorus Send Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.chorus_send` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Chorus Send Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.chorus_send` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Chorus Send Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.amp.chorus_send` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Chorus Send Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.delay_send`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.delay_send` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_delay_send_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_delay_send_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_delay_send_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Delay Send Level |
| `tracks.T2.amp.delay_send` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_delay_send_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Delay Send Level |
| `tracks.T3.amp.delay_send` | T3 | `direct_7bit` | reuse `tracks.T1.amp.delay_send` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.delay_send` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Delay Send Level |
| `tracks.T4.amp.delay_send` | T4 | `direct_7bit` | reuse `tracks.T1.amp.delay_send` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.delay_send` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Delay Send Level |

Commands:

- `tracks.T1.amp.delay_send` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Delay Send Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.delay_send` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Delay Send Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.delay_send` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Delay Send Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.amp.delay_send` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Delay Send Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.reverb_send`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.reverb_send` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_reverb_send_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_reverb_send_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_reverb_send_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Reverb Send Level |
| `tracks.T2.amp.reverb_send` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_reverb_send_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Reverb Send Level |
| `tracks.T3.amp.reverb_send` | T3 | `direct_7bit` | reuse `tracks.T1.amp.reverb_send` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.reverb_send` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Reverb Send Level |
| `tracks.T4.amp.reverb_send` | T4 | `direct_7bit` | reuse `tracks.T1.amp.reverb_send` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.reverb_send` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Reverb Send Level |

Commands:

- `tracks.T1.amp.reverb_send` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Reverb Send Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.reverb_send` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Reverb Send Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.reverb_send` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Reverb Send Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.amp.reverb_send` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Reverb Send Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.pan`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.pan` | T1 | `bipolar_7bit` | -64 / raw 0<br>0 / raw 64<br>+63 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_pan_negative.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_pan_center.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_pan_positive.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T2.amp.pan` | T2 | `bipolar_7bit` | 0 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_pan_stride_center.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T3.amp.pan` | T3 | `bipolar_7bit` | reuse `tracks.T1.amp.pan` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.pan` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |
| `tracks.T4.amp.pan` | T4 | `bipolar_7bit` | reuse `tracks.T1.amp.pan` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.pan` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>negative, center, and positive observations |

Commands:

- `tracks.T1.amp.pan` / `negative`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Pan" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.pan` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Pan" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.pan` / `positive`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Pan" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.amp.pan` / `center`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Pan" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.amp.volume`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.amp.volume` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>100 / raw 100 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_amp_volume_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_volume_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_volume_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_amp_volume_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Volume |
| `tracks.T2.amp.volume` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_amp_volume_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Volume |
| `tracks.T3.amp.volume` | T3 | `direct_7bit` | reuse `tracks.T1.amp.volume` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.volume` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Volume |
| `tracks.T4.amp.volume` | T4 | `direct_7bit` | reuse `tracks.T1.amp.volume` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.amp.volume` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for Volume |

Commands:

- `tracks.T1.amp.volume` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Volume" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.amp.volume` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Volume" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.amp.volume` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Volume" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.amp.volume` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Volume" --channel <T1_CHANNEL_0_BASED> --value 100
- `tracks.T2.amp.volume` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Volume" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_envelope.attack`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_envelope.attack` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_attack_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_attack_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_attack_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Attack Time |
| `tracks.T2.filter_envelope.attack` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_envelope_attack_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Attack Time |
| `tracks.T3.filter_envelope.attack` | T3 | `direct_7bit` | reuse `tracks.T1.filter_envelope.attack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.attack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Attack Time |
| `tracks.T4.filter_envelope.attack` | T4 | `direct_7bit` | reuse `tracks.T1.filter_envelope.attack` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.attack` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Attack Time |

Commands:

- `tracks.T1.filter_envelope.attack` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Attack Time" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_envelope.attack` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Attack Time" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_envelope.attack` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Attack Time" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.filter_envelope.attack` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Attack Time" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_envelope.decay`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_envelope.decay` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>24 / raw 24 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_decay_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_decay_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_decay_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_decay_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Decay Time |
| `tracks.T2.filter_envelope.decay` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_envelope_decay_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Decay Time |
| `tracks.T3.filter_envelope.decay` | T3 | `direct_7bit` | reuse `tracks.T1.filter_envelope.decay` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.decay` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Decay Time |
| `tracks.T4.filter_envelope.decay` | T4 | `direct_7bit` | reuse `tracks.T1.filter_envelope.decay` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.decay` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Decay Time |

Commands:

- `tracks.T1.filter_envelope.decay` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Decay Time" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_envelope.decay` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Decay Time" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_envelope.decay` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Decay Time" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.filter_envelope.decay` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Decay Time" --channel <T1_CHANNEL_0_BASED> --value 24
- `tracks.T2.filter_envelope.decay` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Decay Time" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_envelope.sustain`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_envelope.sustain` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_sustain_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_sustain_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_sustain_max.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Sustain Level |
| `tracks.T2.filter_envelope.sustain` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_envelope_sustain_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Sustain Level |
| `tracks.T3.filter_envelope.sustain` | T3 | `direct_7bit` | reuse `tracks.T1.filter_envelope.sustain` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.sustain` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Sustain Level |
| `tracks.T4.filter_envelope.sustain` | T4 | `direct_7bit` | reuse `tracks.T1.filter_envelope.sustain` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.sustain` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Sustain Level |

Commands:

- `tracks.T1.filter_envelope.sustain` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Sustain Level" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_envelope.sustain` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Sustain Level" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_envelope.sustain` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Sustain Level" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T2.filter_envelope.sustain` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Sustain Level" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_envelope.release`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_envelope.release` | T1 | `direct_7bit` | 0 / raw 0<br>64 / raw 64<br>127 / raw 127<br>5 / raw 5 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_release_min.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_release_mid.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_release_max.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_release_requested.syx` | 4 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Release Time |
| `tracks.T2.filter_envelope.release` | T2 | `direct_7bit` | 64 / raw 64 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_envelope_release_stride_mid.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Release Time |
| `tracks.T3.filter_envelope.release` | T3 | `direct_7bit` | reuse `tracks.T1.filter_envelope.release` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.release` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Release Time |
| `tracks.T4.filter_envelope.release` | T4 | `direct_7bit` | reuse `tracks.T1.filter_envelope.release` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.release` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>minimum, midpoint, maximum observations for EnvF Release Time |

Commands:

- `tracks.T1.filter_envelope.release` / `min`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Release Time" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_envelope.release` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Release Time" --channel <T1_CHANNEL_0_BASED> --value 64
- `tracks.T1.filter_envelope.release` / `max`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Release Time" --channel <T1_CHANNEL_0_BASED> --value 127
- `tracks.T1.filter_envelope.release` / `requested`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Release Time" --channel <T1_CHANNEL_0_BASED> --value 5
- `tracks.T2.filter_envelope.release` / `mid`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Release Time" --channel <T2_CHANNEL_0_BASED> --value 64

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

### `a4.filter_envelope.envelope_shape`

| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `tracks.T1.filter_envelope.envelope_shape` | T1 | `enum` | triangle / raw 0<br>exponential / raw 1<br>linear / raw 2 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_envelope_shape_triangle.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_envelope_shape_exponential.syx`<br>`calibration/sysex/a4/A4_T1_tracks_t1_filter_envelope_envelope_shape_linear.syx` | 3 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T2.filter_envelope.envelope_shape` | T2 | `enum` | triangle / raw 0 | `reference/A4_Test1_Init_Kit.syx` | `calibration/sysex/a4/A4_T2_tracks_t2_filter_envelope_envelope_shape_stride_triangle.syx` | 1 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T3.filter_envelope.envelope_shape` | T3 | `enum` | reuse `tracks.T1.filter_envelope.envelope_shape` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.envelope_shape` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |
| `tracks.T4.filter_envelope.envelope_shape` | T4 | `enum` | reuse `tracks.T1.filter_envelope.envelope_shape` converter/stride evidence | `reference/A4_Test1_Init_Kit.syx` | shared with `tracks.T1.filter_envelope.envelope_shape` | 0 | unknown | one-parameter-at-a-time saved-kit differentials<br>same observation on a second track before promoting a track stride<br>all changed packed and unpacked bytes must be explained<br>multiple named enum observations and an exact typed label table |

Commands:

- `tracks.T1.filter_envelope.envelope_shape` / `triangle`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Env Shape" --channel <T1_CHANNEL_0_BASED> --value 0
- `tracks.T1.filter_envelope.envelope_shape` / `exponential`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Env Shape" --channel <T1_CHANNEL_0_BASED> --value 1
- `tracks.T1.filter_envelope.envelope_shape` / `linear`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Env Shape" --channel <T1_CHANNEL_0_BASED> --value 2
- `tracks.T2.filter_envelope.envelope_shape` / `triangle`: .venv\Scripts\python.exe -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "EnvF Env Shape" --channel <T2_CHANNEL_0_BASED> --value 0

Capture API after each mutation:

- `MidoMidiPortProvider.capture_sysex_messages(exact_input_port, timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)`

## Supplied Differential Results

No differential KIT dump is present under the planned calibration paths.
No offset, stride, converter, or mapping was promoted by this run.

## Safety

- passive local-file analysis only
- no MIDI backend imported
- no MIDI port opened
- no MIDI data transmitted
- no --apply execution
- no final RUSH01 SysEx generated while critical mappings remain unresolved

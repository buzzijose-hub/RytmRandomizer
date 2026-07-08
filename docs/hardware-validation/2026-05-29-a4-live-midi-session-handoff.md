# Analog Four Live MIDI Session Handoff - 2026-05-29

## Session Goal

Use the Analog Four MKII manual as the source of truth, validate outbound MIDI
behavior against real hardware, and move from one-off CC testing toward
four-track kit design that can later be driven intelligently during live
performance.

## Hardware Context

- Device under test: Elektron Analog Four MKII.
- Observed output port list during the session:
  - `0: Microsoft GS Wavetable Synth 0`
  - `1: Elektron Analog Four MKII 1`
  - `2: Elektron Analog Rytm MKII 2`
  - `3: OXI ONE 3`
  - `4: MIDIOUT2 (OXI ONE) 4`
  - `5: MIDIOUT3 (OXI ONE) 5`
- Live A4 sends used output port index `1`.
- Tracks use zero-based MIDI channels in the app:
  - channel `0` = A4 track 1
  - channel `1` = A4 track 2
  - channel `2` = A4 track 3
  - channel `3` = A4 track 4

## Manual Facts Captured

Manual source: `<local-manuals>/Analog-Four-MKII-User-Manual_ENG_OS1.51C_220204-1.pdf`.

The implementation now has manual-backed A4 MIDI data:

- `ANALOG_FOUR_SYNTH_TRACK_CC`: 58 synth-track CC rows.
- `ANALOG_FOUR_MANUAL_CC`: 72 total manual CC rows, including track/common,
  performance, modulation, and synth-track rows.
- `ANALOG_FOUR_SYNTH_TRACK_NRPN`: 91 synth-track NRPN rows.
- NRPN unlock adds 33 synth-track rows that have no direct CC MSB.

Representative pinned rows:

- `OSC1 Pulsewidth`: CC MSB `72`, NRPN `1:7`.
- `OSC1 PWM Speed`: CC MSB `73`, NRPN `1:8`.
- `OSC1 PWM Depth`: CC MSB `74`, NRPN `1:9`.
- `Filter1 Frequency`: CC MSB `18`, CC LSB `50`, NRPN `1:40`.
- `Sync Mode`: NRPN-only row, NRPN `1:31`.
- `LFO1 Waveform`: NRPN-only row, NRPN `1:85`.

Performance macros are intentionally not needed for this workflow right now.
Keep them out of kit-design sends unless explicitly requested later.

## Live Hardware Observations

- Sending manual-backed A4 CCs definitely moved parameters on the hardware.
- Early single-parameter tests exposed a useful naming/UI ambiguity:
  - The manual-backed OSC1 PWM/Pulsewidth area must be treated carefully.
  - The user confirmed visible movement around oscillator 1 pulse width/PWM.
  - One repeat was identified by the user as pulse modulation speed.
  - Next validation should deliberately send `OSC1 Pulsewidth`, `OSC1 PWM Speed`,
    and `OSC1 PWM Depth` one at a time with enough visual time between sends.
- A brand new initialized A4 project was used for later kit testing, so the
  starting state should be assumed to be default/init unless the user changes it.

## Commands Added Or Used

Passive A4 capture:

```powershell
python -m rytm_randomizer.app --arm --a4-soft-capture
```

Single named CC send:

```powershell
python -m rytm_randomizer.app --arm --a4-send-param --parameter "OSC1 PWM Depth" --channel 0 --value 32
```

Kit recipe send over CC:

```powershell
python -m rytm_randomizer.app --arm --a4-kit-recipe bell-techno-expanded
```

Single named NRPN send:

```powershell
python -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Sync Mode" --channel 0 --value 2
```

Kit recipe send over NRPN:

```powershell
python -m rytm_randomizer.app --arm --a4-kit-recipe bell-techno-expanded --a4-kit-recipe-nrpn
```

## Kit Recipe Results

### `detroit-minimal`

- Sent live over CC.
- Event count: 45.
- User feedback: sounded bad.
- Lesson: too few parameters and not enough intelligent shaping across the full
  A4 voice architecture.

### `bell-techno-grid`

- Sent live over CC.
- Event count: 32.
- More controlled than `detroit-minimal`, but still too limited.
- Lesson: a serious A4 kit needs oscillators, filters, amp, envelopes, LFO1,
  LFO2, and sub-page parameters, not just a handful of headline controls.

### `bell-techno-expanded`

- Sent live over CC.
- Event count: 145.
- Track distribution:
  - track 1: 38 events
  - track 2: 40 events
  - track 3: 31 events
  - track 4: 36 events
- Sections covered:
  - `OSC 1`
  - `NOISE`
  - `OSC 2`
  - `OSC COMMON`
  - `FILTERS`
  - `AMP`
  - `ENVF`
  - `ENV2`
  - `LFO1`
  - `LFO2`
- Design intent:
  - track 1: dry low foundation
  - track 2: main bell/stab voice
  - track 3: tick/noise/percussion layer
  - track 4: accent/call-response voice
- Current status: much closer structurally, but still needs listening feedback
  and a likely NRPN-rendered version.

## NRPN Unlock

Added low-level NRPN sending:

- `send_nrpn(out, nrpn_msb, nrpn_lsb, value_msb, value_lsb=None, channel=0)`
- Wire sequence:
  - CC `99` = NRPN parameter MSB
  - CC `98` = NRPN parameter LSB
  - CC `6` = Data Entry MSB
  - optional CC `38` = Data Entry LSB

Live validation sent:

```powershell
python -m rytm_randomizer.app --arm --a4-send-nrpn-param --parameter "Sync Mode" --channel 0 --value 2
```

Result:

- Opened `Elektron Analog Four MKII 1`.
- Sent real MIDI.
- Parameter: `Sync Mode`.
- Section: `OSC COMMON`.
- Channel: `0`.
- NRPN: `1:31`.
- Value MSB: `2`.

## Verification Run

Focused checks that passed after the NRPN work:

```powershell
python -m pytest tests/test_midi_io.py tests/test_app_entry.py tests/test_app_validate_one_cc.py tests/test_data_layer.py::test_analog_four_synth_track_nrpn_table_includes_nrpn_only_subpage_rows -n 0 -q
```

Result: `75 passed`.

Touched-file lint/format checks passed:

```powershell
python -m ruff check rytm_randomizer/midi_io.py rytm_randomizer/app.py rytm_randomizer/data/analog_four_midi.py rytm_randomizer/data/__init__.py tests/test_midi_io.py tests/test_data_layer.py tests/test_app_validate_one_cc.py
python -m black --check --target-version=py311 rytm_randomizer/midi_io.py rytm_randomizer/app.py rytm_randomizer/data/analog_four_midi.py rytm_randomizer/data/__init__.py tests/test_midi_io.py tests/test_data_layer.py tests/test_app_validate_one_cc.py
python -m isort --profile black --check-only rytm_randomizer/midi_io.py rytm_randomizer/app.py rytm_randomizer/data/analog_four_midi.py rytm_randomizer/data/__init__.py tests/test_midi_io.py tests/test_data_layer.py tests/test_app_validate_one_cc.py
```

Full-suite note:

- Do not claim full-suite green from this session.
- There is unrelated in-flight Analog Rytm MIDI catalog work in the tree that
  has previously blocked full-suite and full-repo formatting checks.

## Next Best Moves

1. Re-run a deliberate OSC1 visual validation:
   - `OSC1 Pulsewidth`
   - `OSC1 PWM Speed`
   - `OSC1 PWM Depth`
   - Use one parameter at a time, visible pause between each send.
2. Send `bell-techno-expanded` with `--a4-kit-recipe-nrpn` and compare against
   the CC-rendered version.
3. Add NRPN-only parameters into the kit recipe itself:
   - `Sync Mode`
   - `Filter2 Type`
   - envelope shapes and destinations
   - LFO modes, waveforms, phases, fades, and destinations
4. Build a stronger Jeff Mills / "The Bells"-inspired recipe after listening:
   - keep performance macros out
   - keep track 1 tight and dry
   - make track 2 the hard-sync bell/stab voice
   - use track 3 as short noise/tick motion
   - use track 4 as an accent or answering stab
5. Longer-term: combine passive capture with active mutation:
   - capture all four tracks before a performance move
   - treat that state as the baseline
   - apply bounded CC/NRPN transformations from the captured kit

## Safety Boundaries

- Passive default remains passive.
- Hardware sends require `--arm`.
- A4 soft capture is input-only and sends no MIDI.
- Tests use fake/mocked MIDI; automated tests must not open real ports.
- Avoid performance macros for now.
- Avoid kit/project writes, SysEx writes, transport, and pattern changes until
  explicitly designed and approved.

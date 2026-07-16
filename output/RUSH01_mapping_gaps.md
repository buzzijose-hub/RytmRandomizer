# RUSH01 Mapping Gaps

Generated from the approved local references and semantic specifications on
2026-07-15. Firmware is intentionally recorded as
`UNVERIFIED_FROM_DEVICE`; no firmware version was inferred.

## Build Decisions

| Device | Decision | Reason |
| --- | --- | --- |
| Analog Rytm MKII | BLOCKED | Requested machine changes, track/source/amp levels, documented-only source rows, and untyped selectors do not meet the critical mapping policy. |
| Analog Four MKII | BLOCKED | The repository does not contain promoted SysEx locations and converters for the requested oscillator, noise, filter, amp, and envelope surface. |

No partial kit was generated for either device.

## Analog Rytm MKII Critical Gaps

### Machine Selection Writes

The repository machine catalog verifies every supplied name/ID pair and pad
compatibility. No conflicts were found. Four requested selections differ from
the initialized reference:

| Semantic path | Reference machine | Requested machine | Verified enum result | Missing evidence |
| --- | --- | --- | --- | --- |
| `tracks.BD.machine` | BD Hard (`0`) | BD Sharp (`26`) | Name and ID agree; legal on pad 1 | Machine type is `locked_default`; no before/after kit differential proves how the raw value and adjacent validity byte must be written. |
| `tracks.CH.machine` | CH Classic (`9`) | HH Basic (`24`) | Name and ID agree; legal on pad 9 | Same machine-write and validity-byte gap. |
| `tracks.CY.machine` | CY Classic (`11`) | CY Ride (`25`) | Name and ID agree; legal on pad 11 | Same machine-write and validity-byte gap. |
| `tracks.CB.machine` | CB Classic (`12`) | CB Metallic (`20`) | Name and ID agree; legal on pad 12 | Same machine-write and validity-byte gap. |

The established sound-record machine location is decoded at sound offset
`0x007C`, but reference records show meaningful high bits and adjacent bytes.
Preserving those bytes while changing only the apparent low seven bits would
be an unverified approximation.

### Track, Source, and Amp Levels

- `track_levels.BD`, `SD`, `RS`, `CP`, `BT`, `LT`, `MT`, `HT`, `CH`, `OH`,
  `CY`, and `CB`: the MIDI catalog identifies Track Level as NRPN `1:100`, but
  `RYTM_SOUND_FIELD_BY_NRPN_LSB` has no promoted raw-kit location for `100`.
- `tracks.*.synth.LEV`: source Level is marked `locked_default` for every
  requested machine. A raw sound-record position is structurally associated
  with source parameter 1, but the repository policy does not promote it for
  automatic mutation.
- `tracks.*.amp.VOL`: Amp Volume is marked `locked_default`. The apparent
  NRPN `1:31` sound-record position is not sufficient evidence for an
  automatic critical sound-level write.

These fields directly affect the audible result and therefore cannot be
preserved or approximated while claiming semantic success.

### Machine-Specific Source Rows

The following requested machine source surfaces are present only as
manual-backed `documented_only` CC/NRPN rows, without repository differential
kit dumps proving their SysEx raw representation and dependency/validity bits:

- `tracks.RS.synth.*` for RS Hard
- `tracks.CP.synth.*` for CP Classic
- `tracks.BT.synth.*` for BT Classic
- `tracks.LT.synth.*`, `tracks.MT.synth.*`, and `tracks.HT.synth.*` for XT Classic
- `tracks.CH.synth.*` for HH Basic
- `tracks.OH.synth.*` for OH Classic
- `tracks.CY.synth.*` for CY Ride
- `tracks.CB.synth.*` for CB Metallic

BD Sharp and SD Hard have validated live CC rows for their non-level source
parameters, but that validates outbound MIDI behavior, not every SysEx
raw-object write or neighboring validity byte.

### Missing or Untyped Selectors

The specification supplies arbitrary numeric values for selector fields that
must be typed enumerations under the build policy:

| Semantic path | Numeric request | Repository status |
| --- | ---: | --- |
| `tracks.BD.synth.WAV` | `1` | Range `0..11` is known for BD Sharp, but no verified value-to-waveform-name table is present. |
| `tracks.BT.synth.SNP` | `24` | Snap Type is known to be a selector with range `0..3`; `24` is outside that verified range and has no enum name. |
| `tracks.CH.synth.RST` | `0` | Osc Reset has range `0..1`, but the YAML does not provide a typed enum name and no named enum table is established. |
| `tracks.CY.synth.TYP` | `0` | Cymbal Type has range `0..3`, but the YAML does not provide a typed enum name and no named enum table is established. |

`tracks.BT.synth.SNP: 24` is also semantically invalid for the selected BT
Classic machine according to the established `0..3` selector range.

### Unmapped CB Metallic Fields

- `tracks.CB.synth.PW1`
- `tracks.CB.synth.PW2`

CB Metallic is established with only Level, Tune, Decay Time, and Detune
source rows. `PW1` and `PW2` have no parameter name, CC/NRPN address, raw
offset, scale, or differential capture in the repository. They cannot be
silently assigned to unused source slots.

### Candidate-Only Tom Machine Decode

`tracks.LT.machine`, `tracks.MT.machine`, and `tracks.HT.machine` request XT
Classic (`8`), matching the apparent low seven bits in the reference. The
snapshot decoder intentionally keeps pads 6-8 candidate-only because their
captured machine bytes carry unresolved high-bit behavior. Full requested
critical-field verification therefore remains incomplete even though these
three bytes would otherwise be preserved.

### Rytm Evidence Required to Unblock

1. Before/after kit dumps for each changed machine selection, including the
   same transition on enough tracks to prove the adjacent validity bytes.
2. Track Level captures at minimum, midpoint, and maximum on multiple tracks
   to establish NRPN `1:100` raw location, scale, and flags.
3. Source Level and Amp Volume captures proving their raw representation and
   validity behavior.
4. Differential kit captures for the documented-only machine source rows used
   by this specification.
5. Named selector tables and captures for BD Sharp Waveform, BT Classic Snap
   Type, HH Basic Osc Reset, and CY Ride Cymbal Type.
6. Device/UI evidence identifying whether CB Metallic actually exposes `PW1`
   and `PW2`; if it does, captures proving their exact addresses and encoding.

## Analog Four MKII Critical Gaps

The MIDI catalog and display tables describe many front-panel/transport
parameters, but transport metadata does not establish a saved-kit SysEx byte
location. The saved-kit offset manifest explicitly remains candidate-level.

### Requested Sections Without Promoted SysEx Coverage

For tracks `T1`, `T2`, `T3`, and `T4`, the following requested paths lack a
fully promoted raw saved-kit location and typed writer conversion:

- `track_levels.<track>`
- `tracks.<track>.oscillator_1.coarse_tune_semitones`
- `tracks.<track>.oscillator_1.fine_tune_cents`
- `tracks.<track>.oscillator_1.linear_detune_hz`
- `tracks.<track>.oscillator_1.keytrack`
- `tracks.<track>.oscillator_1.level`
- `tracks.<track>.oscillator_1.waveform`
- `tracks.<track>.oscillator_1.sub_oscillator`
- `tracks.<track>.oscillator_1.pulse_width`
- `tracks.<track>.oscillator_1.pwm_speed`
- `tracks.<track>.oscillator_1.pwm_depth`
- every corresponding `oscillator_2` path
- every requested `oscillator_common` path, including AM, sync mode/amount,
  bend depth, slide time, retrigger, and vibrato fields
- every requested `noise` path
- `filter_1.overdrive`, `filter_1.keytrack`, and
  `filter_1.envelope_depth`
- `filter_2.resonance`, `filter_2.type`, `filter_2.keytrack`, and
  `filter_2.envelope_depth`
- every requested `amp` path
- `filter_envelope.attack`, `decay`, `sustain`, `release`, and
  `envelope_shape`

Signed display values, time scales, booleans, waveforms, sub-oscillator modes,
sync modes, filter types, and envelope shapes therefore cannot be converted
to raw bytes without guessing.

### Candidate-Promoted Filter Captures Are Insufficient for This Build

The repository contains candidate-promoted differential evidence for:

- Filter 1 Frequency
- Filter 1 Resonance
- Filter 2 Frequency

Those captures establish selected endpoint/midpoint observations and track
strides, but the requested values are arbitrary display targets rather than
the captured calibration points. The facts remain explicitly
`candidate-promoted`, and no complete writer conversion has been promoted.
Consequently these paths remain critical gaps for this build:

- `tracks.T1.filter_1.frequency`, `tracks.T2.filter_1.frequency`,
  `tracks.T3.filter_1.frequency`, `tracks.T4.filter_1.frequency`
- the corresponding four Filter 1 Resonance paths
- the corresponding four Filter 2 Frequency paths

### A4 Evidence Required to Unblock

1. Controlled minimum/midpoint/maximum differential kit dumps for every
   requested critical parameter, plus enough intermediate points to prove
   nonlinear display scales and signed conversions.
2. Cross-track captures proving the track stride for every field.
3. Named enum captures for oscillator waveforms, sub-oscillator modes, sync
   modes, Filter 2 type, and envelope shapes.
4. Differential captures proving booleans and any neighboring validity or
   dependency bits.
5. Track Level captures and per-track sound-name captures.
6. A promoted writer contract replacing the current candidate-only offset
   status.

## Unsupported Noncritical Fields

These omissions do not independently block a build, but were preserved by not
emitting a partial output:

- Rytm `tracks.*.sound_name`: no promoted per-track sound-name raw location.
- A4 `tracks.*.sound_name`: no promoted per-track sound-name raw location.
- Both specifications' `design_role` text: semantic documentation only; no
  device field was requested or inferred.

The Rytm and A4 kit-name locations are established, but kit names were not
patched because each device failed its critical-field gate.

## Conditional Sample-Level Result

Rytm Sample Level is associated with NRPN `1:15` and sound offset `0x003A`,
but the mutation catalog marks it `locked_default`. The initialized reference
contains raw value `100` on each sound track. Under the supplied firmware/build
policy, the field was preserved and reported rather than changed to zero in a
blocked partial kit.

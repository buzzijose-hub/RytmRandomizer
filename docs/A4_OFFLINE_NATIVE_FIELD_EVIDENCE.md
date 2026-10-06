# A4 Offline Native Field Evidence

October 6 native capability, integrated from the worker slice based on `a0cb9d22`.
This is local-file capability,
not new hardware evidence, a legacy writer promotion, or live authority.
Studio resolves it through the Device boundary for parameter scope, Forge,
preparation, immutable ShowBank recipes and exact local retention. Its software
and packaged-application acceptance receipts remain source-bound separately.

## Public Contract

`devices.get_analog_four_native_field_capability()` resolves the existing
registered A4 device's optional `AnalogFourNativeFieldCapability`. Mandatory
`Device` is unchanged. The capability provides:

- `native_fields() -> tuple[AnalogFourNativeField, ...]`: canonical native
  snake_case keys, relative native offsets, encoding, exact display quantum,
  native enum code/name pairs, immutable protection and evidence references.
  `metadata.native_encoding.value` is the stable encoding string.
- `read_native_fields(frame: bytes) -> AnalogFourNativeReadback`: verified
  source SHA256, kit identity and per-track typed cells, exact native integer,
  bytes/offsets, screen text, source-known flag, protection and legal domain.
- `render_native_fields(frame, mutations) -> AnalogFourNativeCandidateResult`:
  `AnalogFourNativeMutation(parameter, track, encoded_native)` records only.
  Empty mutations return byte-identical source. Result retains exact source
  and rendered bytes/hashes, readback, approved/changed native and wire
  footprint, protection/evidence, and unconditional local-only authority.

Each mutable cell's `domain` provides `value_count`, `value_at(index)` and
`index_of(encoded_native)`. A seeded caller samples integer **indices**, not
raw values guessed from MIDI ordinals or converter semantics. Numeric domains
are exact integer grids; enum domains contain only canonical native codes.
TUN has a source-dependent 256-unit grid retaining the entire fine residual,
including its hidden half-step. `screen_value` is exact semantic text; it is
not interchangeable with `encoded_native`. Unknown source values have no
sampling domain and cannot be overwritten, even with a known requested code.

## Evidence Boundary

Native offset authority is `data/analog_four_kit_fields.py`, its saved-Sound
address transform in `data/analog_four_saved_kit_layout.py`, and the typed
`A4Sound` converters/native enums. These are not MIDI CC/NRPN addresses.
The executable RIO145 initialized/returned frames and
`specs/rio145/come_to_rio_a4_core.json` establish reference and independent
four-track recipe encoding. Focused OSC FIN captures establish pitch coupling
and hidden precision; ENV2 DEPA +/-1 captures establish centered Q8.7 depths.
The July F2 resonance and August F1 frequency fixtures separately retain
reference, novel-value and all-track regressions. No evidence status is changed.

Unknown bytes, FX/CV/performance/routing,
names, slot/header and protected AMP are preserved, not normalized.

## Passive DTO And Sampling

The v3 DTO should validate shape only in `cockpit/data`: strict non-boolean
integers, strings, bounded offset tuples and no implicit raw/screen coercion.
At the service boundary, resolve the optional capability and read the actual
frame. Compare each DTO's parameter/track, encoded integer, encoding string,
offset tuple and screen text to the matching canonical readback cell before
acceptance, recall or render. Re-render from the retained original with exact
selected mutations and compare the entire candidate frame. Neither imported
metadata nor a rehashed DTO can authorize a field or live output. Do not import
concrete device strategies into passive Cockpit data and do not copy this table
as a second fact source.

Keep F1 v1/v2 calibration, recipes and legacy writer reproducible. The new
native-key algorithm belongs to separately versioned v3 recipes, not a silent
replacement of the original F1 sampler or MIDI/display vocabulary. No mapping
from MIDI ordinals to these native codes is claimed.

```python
capability = get_analog_four_native_field_capability()
source = capability.read_native_fields(frame)
cell = source.value("osc1_tune", 1)
assert cell.mutable and cell.domain is not None
source_index = cell.domain.index_of(cell.encoded_native)
# A seeded caller chooses an in-range domain index, with its own depth policy.
sampled = cell.domain.value_at(source_index + 1)
candidate = capability.render_native_fields(
    frame, (AnalogFourNativeMutation(cell.parameter, cell.track, sampled),)
)
```

No `screen_value` parser or float is needed for sampling. Depth zero passes an
empty mutation tuple. The caller must bound any chosen index; a source already
at the endpoint cannot use `source_index + 1`.

## Exact Domains And Evidence

All offsets below are decimal and relative to a 350-byte synth Sound.
The canonical KIT-object offset for track `t` is `32 + (t - 1) * 350 + offset`.
These are offsets into the codec's 2410-byte object, not into the older
five-metadata-byte-prefixed representation. F1 T1 is `128,129`; F2 resonance
T1 is `140`. Field widths are the number of listed offsets. Header, slot,
names, levels and all nonselected native bytes remain identical.

| Encoding | Exact screen semantics | Evidence/converter |
| --- | --- | --- |
| U7 | raw `0..127`, screen `0..127`, quantum `1` | Explicit continuous-field facts plus `A4Sound.get_u7/set_u7`; RIO145 recipe and returned four-track native object. |
| BIPOLAR | raw `0..127`, screen `-64..63`, quantum `1` | `A4_BIPOLAR_FIELDS`, `get_bipolar/set_bipolar`; RIO145 recipe/return. Native values are not MIDI display conversions. |
| Q8_8 | raw `0..32512`, screen `0..127`, quantum `1/256` | `get_fixed_8_8_raw/set_fixed_8_8_raw`, exact `format_a4_fixed_8_8`; RIO145 recipe/return, F1 isolated captures. Values above `127` are not granted by the accessor's larger storage ceiling. |
| MOD_DEPTH | raw `0..32767`, screen `-128..127.9921875`, quantum `1/128` | `get_mod_depth_raw`, `decode_a4_mod_depth/set_mod_depth`; controlled ENV2 DEPA +/-1 and RIO145 four-track recipe/return. Both listed bytes are one field. |
| TUNE | source-bound raw grid, quantum `256`; screen integer semitones | `get_oscillator_pitch_components/set_oscillator_tune`; controlled FIN +/-1,+/-2 and RIO145 return. Grid retains FIN/residual/hidden half-step. Only coarse byte is approved to change. Endpoint range may shrink to preserve the residual. |
| FINE | read-only display bucket from complete native pitch word | Same pitch converter/captures. No independent FIN edit, no hidden-half-step normalization. |
| ENUM | exact named native codes only; unknown source or requested code refused | Existing `A4_RECIPE_ENUM_FIELDS` / `A4Destination` definitions and RIO145 recipe/return. This does not validate live MIDI ordinals. |
| UNKNOWN | raw bytes only; no semantic display or writable domain | Accessor/layout exists but no approved native domain; preserve immutable. |

Native enum domains use the existing classes, not a second label catalog:
`A4Waveform` codes `0..7`, `A4SubOscillator` `0..4`, `A4SyncMode` `0..3`,
`A4Filter2Type` `0..6`, `A4EnvelopeShape` `0..11`, `A4LfoMode` `0..4`,
`A4LfoWave` `0..6`, `A4LfoMultiplier` `0..35`. Destination codes are the
non-contiguous members of `A4Destination`, returned as exact `(code, name)`
pairs in field metadata; holes are never valid. `A4Portamento` is retained as
read-only metadata: its codec enum lacks retained recipe/cross-track evidence.
Unknown binary selectors and gate-length special selectors stay blocked.

RIO initialized SHA256:
`50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e`.
RIO target return SHA256:
`c22c433fd2721747296d16634cb4e5090b55c212557578e7f59e687dd6f5c270`.
F1 and F2 exact reference/novel/all-track hashes remain pinned by the existing
tests and `tests/fixtures/analog_four_saved_kit/README.md`. Generated novel
native test cases are software evidence only, not new hardware observations.

## Field Inventory

There are **106 mapped keys, 72 mutable field keys / 288 source-known cells**
on the retained initialized source. Protection takes precedence over domain.
Fraction aliases cannot be selected independently, but the approved parent
MOD_DEPTH field owns both bytes. FIN aliases describe the whole pitch word;
their residual must be unchanged during a TUN edit.

| Key | Sound-relative offset(s) | Encoding | Exact native domain | Protection |
| --- | --- | --- | --- | --- |
| osc1_tune | 28,29 | TUNE | source-bound; step 256 | mutable if source known |
| osc1_fine | 28,29 | FINE | none | independently_unsafe_fine |
| osc2_tune | 30,31 | TUNE | source-bound; step 256 | mutable if source known |
| osc2_fine | 30,31 | FINE | none | independently_unsafe_fine |
| osc1_detune | 32 | BIPOLAR | 0..127 step 1 | mutable if source known |
| osc2_detune | 34 | BIPOLAR | 0..127 step 1 | mutable if source known |
| osc1_tracking | 36 | UNKNOWN | none | native_domain_unestablished |
| osc2_tracking | 38 | UNKNOWN | none | native_domain_unestablished |
| osc1_level | 40 | U7 | 0..127 step 1 | mutable if source known |
| osc2_level | 42 | U7 | 0..127 step 1 | mutable if source known |
| osc1_waveform | 44 | ENUM | known enum codes | mutable if source known |
| osc2_waveform | 46 | ENUM | known enum codes | mutable if source known |
| osc1_sub | 48 | ENUM | known enum codes | native_nondefault_evidence_missing |
| osc2_sub | 50 | ENUM | known enum codes | native_nondefault_evidence_missing |
| osc1_pw | 52 | BIPOLAR | 0..127 step 1 | mutable if source known |
| osc2_pw | 54 | BIPOLAR | 0..127 step 1 | mutable if source known |
| osc1_pwm_speed | 56 | U7 | 0..127 step 1 | mutable if source known |
| osc2_pwm_speed | 58 | U7 | 0..127 step 1 | mutable if source known |
| osc1_pwm_depth | 60 | U7 | 0..127 step 1 | mutable if source known |
| osc2_pwm_depth | 62 | U7 | 0..127 step 1 | mutable if source known |
| noise_sample_hold | 70 | U7 | 0..127 step 1 | mutable if source known |
| noise_fade | 72 | BIPOLAR | 0..127 step 1 | mutable if source known |
| noise_level | 74 | U7 | 0..127 step 1 | mutable if source known |
| osc1_am | 76 | UNKNOWN | none | native_domain_unestablished |
| osc2_am | 78 | UNKNOWN | none | native_domain_unestablished |
| sync_mode | 80 | ENUM | known enum codes | mutable if source known |
| sync_amount | 82 | U7 | 0..127 step 1 | mutable if source known |
| bend_depth | 84 | BIPOLAR | 0..127 step 1 | mutable if source known |
| slide_time | 86 | U7 | 0..127 step 1 | mutable if source known |
| osc_retrigger | 88 | UNKNOWN | none | native_domain_unestablished |
| vibrato_fade | 90 | BIPOLAR | 0..127 step 1 | mutable if source known |
| vibrato_speed | 92 | U7 | 0..127 step 1 | mutable if source known |
| vibrato_depth | 94 | U7 | 0..127 step 1 | mutable if source known |
| filter1_frequency | 96,97 | Q8_8 | 0..32512 step 1 | mutable if source known |
| filter1_resonance | 98 | U7 | 0..127 step 1 | mutable if source known |
| filter1_overdrive | 100 | BIPOLAR | 0..127 step 1 | mutable if source known |
| filter1_tracking | 102 | BIPOLAR | 0..127 step 1 | mutable if source known |
| filter1_env_depth | 104 | BIPOLAR | 0..127 step 1 | mutable if source known |
| filter2_frequency | 106,107 | Q8_8 | 0..32512 step 1 | mutable if source known |
| filter2_resonance | 108 | U7 | 0..127 step 1 | mutable if source known |
| filter2_type | 110 | ENUM | known enum codes | mutable if source known |
| filter2_tracking | 112 | BIPOLAR | 0..127 step 1 | mutable if source known |
| filter2_env_depth | 114 | BIPOLAR | 0..127 step 1 | mutable if source known |
| amp_chorus_send | 118 | U7 | 0..127 step 1 | oxi_amp_protection |
| amp_delay_send | 120 | U7 | 0..127 step 1 | oxi_amp_protection |
| amp_reverb_send | 122 | U7 | 0..127 step 1 | oxi_amp_protection |
| amp_pan | 124 | BIPOLAR | 0..127 step 1 | oxi_amp_protection |
| amp_volume | 126 | U7 | 0..127 step 1 | oxi_amp_protection |
| envf_attack | 130 | U7 | 0..127 step 1 | mutable if source known |
| env2_attack | 132 | U7 | 0..127 step 1 | mutable if source known |
| amp_attack | 134 | U7 | 0..127 step 1 | oxi_amp_protection |
| envf_decay | 136 | U7 | 0..127 step 1 | mutable if source known |
| env2_decay | 138 | U7 | 0..127 step 1 | mutable if source known |
| amp_decay | 140 | U7 | 0..127 step 1 | oxi_amp_protection |
| envf_sustain | 142 | U7 | 0..127 step 1 | mutable if source known |
| env2_sustain | 144 | U7 | 0..127 step 1 | mutable if source known |
| amp_sustain | 146 | U7 | 0..127 step 1 | oxi_amp_protection |
| envf_release | 148 | U7 | 0..127 step 1 | mutable if source known |
| env2_release | 150 | U7 | 0..127 step 1 | mutable if source known |
| amp_release | 152 | U7 | 0..127 step 1 | oxi_amp_protection |
| envf_shape | 154 | ENUM | known enum codes | mutable if source known |
| env2_shape | 156 | ENUM | known enum codes | mutable if source known |
| amp_shape | 158 | ENUM | known enum codes | oxi_amp_protection |
| envf_length | 160 | UNKNOWN | none | native_domain_unestablished |
| env2_length | 162 | UNKNOWN | none | native_domain_unestablished |
| envf_destination_a | 164 | ENUM | known enum codes | mutable if source known |
| envf_destination_b | 166 | ENUM | known enum codes | mutable if source known |
| env2_destination_a | 168 | ENUM | known enum codes | mutable if source known |
| env2_destination_b | 170 | ENUM | known enum codes | mutable if source known |
| envf_depth_a | 172,173 | MOD_DEPTH | 0..32767 step 1 | mutable if source known |
| envf_depth_a_fraction | 173 | UNKNOWN | none | hidden_fraction |
| envf_depth_b | 174,175 | MOD_DEPTH | 0..32767 step 1 | mutable if source known |
| envf_depth_b_fraction | 175 | UNKNOWN | none | hidden_fraction |
| env2_depth_a | 176,177 | MOD_DEPTH | 0..32767 step 1 | mutable if source known |
| env2_depth_a_fraction | 177 | UNKNOWN | none | hidden_fraction |
| env2_depth_b | 178,179 | MOD_DEPTH | 0..32767 step 1 | mutable if source known |
| env2_depth_b_fraction | 179 | UNKNOWN | none | hidden_fraction |
| lfo1_speed | 180 | BIPOLAR | 0..127 step 1 | mutable if source known |
| lfo2_speed | 182 | BIPOLAR | 0..127 step 1 | mutable if source known |
| lfo1_multiplier | 184 | ENUM | known enum codes | mutable if source known |
| lfo2_multiplier | 186 | ENUM | known enum codes | mutable if source known |
| lfo1_fade | 188 | BIPOLAR | 0..127 step 1 | mutable if source known |
| lfo2_fade | 190 | BIPOLAR | 0..127 step 1 | mutable if source known |
| lfo1_phase | 192 | U7 | 0..127 step 1 | native_nondefault_evidence_missing |
| lfo2_phase | 194 | U7 | 0..127 step 1 | mutable if source known |
| lfo1_mode | 196 | ENUM | known enum codes | mutable if source known |
| lfo2_mode | 198 | ENUM | known enum codes | mutable if source known |
| lfo1_waveform | 200 | ENUM | known enum codes | mutable if source known |
| lfo2_waveform | 202 | ENUM | known enum codes | mutable if source known |
| lfo1_destination_a | 204 | ENUM | known enum codes | mutable if source known |
| lfo1_destination_b | 206 | ENUM | known enum codes | mutable if source known |
| lfo2_destination_a | 208 | ENUM | known enum codes | mutable if source known |
| lfo2_destination_b | 210 | ENUM | known enum codes | mutable if source known |
| lfo1_depth_a | 212,213 | MOD_DEPTH | 0..32767 step 1 | mutable if source known |
| lfo1_depth_a_fraction | 213 | UNKNOWN | none | hidden_fraction |
| lfo1_depth_b | 214,215 | MOD_DEPTH | 0..32767 step 1 | mutable if source known |
| lfo1_depth_b_fraction | 215 | UNKNOWN | none | hidden_fraction |
| lfo2_depth_a | 216,217 | MOD_DEPTH | 0..32767 step 1 | mutable if source known |
| lfo2_depth_a_fraction | 217 | UNKNOWN | none | hidden_fraction |
| lfo2_depth_b | 218,219 | MOD_DEPTH | 0..32767 step 1 | mutable if source known |
| lfo2_depth_b_fraction | 219 | UNKNOWN | none | hidden_fraction |
| noise_color | 228 | BIPOLAR | 0..127 step 1 | mutable if source known |
| oscillator_drift | 236 | UNKNOWN | none | native_domain_unestablished |
| portamento | 237 | ENUM | known enum codes | native_domain_unestablished |
| legato_mode | 238 | UNKNOWN | none | native_domain_unestablished |
| filter1_resonance_boost | 240 | UNKNOWN | none | native_domain_unestablished |

## Integration Ownership

Coordinator must update architecture prose/diagrams and the generic producer/
consumer tests in the composed delivery. This slice does not edit those shared
documents or DTOs. No full suite, parity recapture, build, hardware enumeration,
port opening, arming, transmission, push or PR is performed here.

## Verification Receipts

All Python invocations used the assigned absolute main-workspace venv
interpreter, with `RYTM_RAND_MIDI_BACKEND=off` and
`PYTEST_XDIST_AUTO_NUM_WORKERS=2`. Every pytest invocation used `-n 0`.

- Native/F1/legacy F2/device focused composition: **154 passed in 6.42s**.
  Files: `test_devices_strategies_analog_four_native_fields.py`,
  `test_devices_strategies_analog_four_filter1_frequency_candidate.py`,
  `test_devices_strategies_analog_four_saved_kit_writer.py`,
  `test_analog_four_device.py`. Coverage recorded zero missed statements,
  zero partial branches and 100% coverage in all five touched production
  modules. The `devices` coverage selector also reported unrelated modules;
  no package-wide coverage claim is made from this focused run.
- Device-protocol/no-new-root-module plus five touched-module isolated-import
  cases: **14 passed in 2.12s**.
- No-Any architecture guard: **1 passed in 0.71s**.
- Strict touched-production typing against `a0cb9d22`: **5 modules; 0 errors,
  0 warnings, 0 informations**. No pin/tool update was performed.
- Touched-file Ruff, Black (`py311`) and isort checks passed; diff whitespace
  check passed.

One attempted architecture command named the obsolete
`tests/test_no_side_effects.py`: **no tests ran**, not a pass. Its corrected
package-wide import matrix expanded beyond the intended focused scope and was
stopped without an accepted runner summary. The explicit five touched-module
isolation cases above replace that attempt. Full architecture, full suite,
parity suite, builds, and all hardware/transport checks were not run in this
worker slice; those are not inferred from the focused receipts.

Abstraction review: metadata consumes the existing layout, field facts, native
enums and converters; source validation and exact canonical repacking are
shared with the existing F1 renderer. No second codec/store/registry or
mandatory Device member was added. The optional capability is deliberately
separate from legacy hardware-gated saved-KIT export and MIDI/live authority.
Remaining domain/evidence blockers are the protected entries above and unknown
source-native values. Coordinator owns algorithm-versioned v3 sampling,
shape-only DTO service verification, full-profile retention, actual workflow
composition, and architecture prose/diagram updates.

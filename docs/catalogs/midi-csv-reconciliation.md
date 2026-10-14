# MIDI Guide CSV Reconciliation

All 552 supplied rows are retained verbatim in `midi-csv-reconciliation.json`.
Reference/adapted data: Pencil Research and MIDI Guide community contributors,
[CC-BY-SA-4.0](https://github.com/pencilresearch/midi/blob/main/LICENSE). Code remains under repository MIT.
No MIDI/USB discovery, ports, arming, mutation or sending occurs.

## Reproduce

From the checkout, using the project interpreter:

```text
python scripts/reconcile_midi_csv.py --check
```

Remove `--check` to regenerate the two documentation artifacts atomically.
Inputs are byte-frozen under `tests/fixtures/midi_guide/`; G: is unnecessary.
Original audit-v2/provenance are retained unchanged. Verified Git blob identities
supplement the earlier unknown-upstream statement rather than rewriting it.

## Source Identity

| Source | Rows | SHA256 | Git Blob |
| --- | ---: | --- | --- |
| Analog Four MKII.csv | 230 | `da38d8ec8df47d4a6c39034b2f1c829475ac301c712d26c0a4b4787ae259ea69` | `53a1a26263782ce8f044b112a33642de27f547cd` |
| Analog Rytm MKII.csv | 322 | `c370aa520117322ef559147b94b9cee9c392f6482a5147f0ea2485a07ace0cc5` | `46cc786dc106f35a00a9412057f8ee63192aa308` |

Dataset commit: `a52a7c9e1a81a4e95f31ec8b6a660071d11ecd6b`.

## Matching And Representation

Exact machine/track context plus all supplied address components are required.
A partial address can match only if unique in context; missing is never zero.
CC and NRPN contradictions, unknown contexts and nonunique candidates stay explicit.
Parameter labels alone are never identity. CSV range/orientation/enum claims are
separate from canonical MIDI, native words, display labels and physical evidence.
Usage intervals remain intervals: overlapping destination defaults are conflicts,
not expanded or flattened into 128 invented enum labels. Units are unknown unless
a canonical binding supplies them; notes and raw cells remain intact.

## Current Counts

```json
{
  "all_rows_retained": true,
  "canonical_omissions": 1,
  "match_status_counts": {
    "matched": 403,
    "partial_address": 24,
    "reference_only": 125
  },
  "per_device_status_counts": {
    "a4": {
      "matched": 105,
      "reference_only": 125
    },
    "rytm": {
      "matched": 298,
      "partial_address": 24
    }
  },
  "rows_with_conflicts_or_missing_evidence": 265,
  "source_rows": 552
}
```

## Reference-Only Rows

| Device | CSV Row | Section | Parameter |
| --- | ---: | --- | --- |
| analog_four_mk2 | 44 | Synth: Noise | Noise: Color |
| analog_four_mk2 | 87 | Envelopes | CV Env1: Attack |
| analog_four_mk2 | 88 | Envelopes | CV Env1: Decay |
| analog_four_mk2 | 89 | Envelopes | CV Env1: Sustain |
| analog_four_mk2 | 90 | Envelopes | CV Env1: Release |
| analog_four_mk2 | 91 | Envelopes | CV Env1: Shape |
| analog_four_mk2 | 92 | Envelopes | CV Env1: Gate Length |
| analog_four_mk2 | 93 | Envelopes | CV Env1: Destination A |
| analog_four_mk2 | 94 | Envelopes | CV Env1: Depth A |
| analog_four_mk2 | 95 | Envelopes | CV Env1: Destination B |
| analog_four_mk2 | 96 | Envelopes | CV Env1: Depth B |
| analog_four_mk2 | 97 | Envelopes | CV Env2: Attack |
| analog_four_mk2 | 98 | Envelopes | CV Env2: Decay |
| analog_four_mk2 | 99 | Envelopes | CV Env2: Sustain |
| analog_four_mk2 | 100 | Envelopes | CV Env2: Release |
| analog_four_mk2 | 101 | Envelopes | CV Env2: Shape |
| analog_four_mk2 | 102 | Envelopes | CV Env2: Gate Length |
| analog_four_mk2 | 103 | Envelopes | CV Env2: Destination A |
| analog_four_mk2 | 104 | Envelopes | CV Env2: Depth A |
| analog_four_mk2 | 105 | Envelopes | CV Env2: Destination B |
| analog_four_mk2 | 106 | Envelopes | CV Env2: Depth B |
| analog_four_mk2 | 127 | LFOs | CV LFO1: Speed |
| analog_four_mk2 | 128 | LFOs | CV LFO1: Multiplier |
| analog_four_mk2 | 129 | LFOs | CV LFO1: Fade In/Out |
| analog_four_mk2 | 130 | LFOs | CV LFO1: Start Phase |
| analog_four_mk2 | 131 | LFOs | CV LFO1: Mode |
| analog_four_mk2 | 132 | LFOs | CV LFO1: Waveform |
| analog_four_mk2 | 133 | LFOs | CV LFO1: Destination A |
| analog_four_mk2 | 134 | LFOs | CV LFO1: Depth A |
| analog_four_mk2 | 135 | LFOs | CV LFO1: Destination B |
| analog_four_mk2 | 136 | LFOs | CV LFO1: Depth B |
| analog_four_mk2 | 137 | LFOs | CV LFO2: Speed |
| analog_four_mk2 | 138 | LFOs | CV LFO2: Multiplier |
| analog_four_mk2 | 139 | LFOs | CV LFO2: Fade In/Out |
| analog_four_mk2 | 140 | LFOs | CV LFO2: Start Phase |
| analog_four_mk2 | 141 | LFOs | CV LFO2: Mode |
| analog_four_mk2 | 142 | LFOs | CV LFO2: Waveform |
| analog_four_mk2 | 143 | LFOs | CV LFO2: Destination A |
| analog_four_mk2 | 144 | LFOs | CV LFO2: Depth A |
| analog_four_mk2 | 145 | LFOs | CV LFO2: Destination B |
| analog_four_mk2 | 146 | LFOs | CV LFO2: Depth B |
| analog_four_mk2 | 147 | FX: Extern In | Ext In: Left Chorus |
| analog_four_mk2 | 148 | FX: Extern In | Ext In: Left Delay |
| analog_four_mk2 | 149 | FX: Extern In | Ext In: Left Reverb |
| analog_four_mk2 | 150 | FX: Extern In | Ext In: Left Pan |
| analog_four_mk2 | 151 | FX: Extern In | Ext In: Left Level |
| analog_four_mk2 | 152 | FX: Extern In | Ext In: Right Chorus |
| analog_four_mk2 | 153 | FX: Extern In | Ext In: Right Delay |
| analog_four_mk2 | 154 | FX: Extern In | Ext In: Right Reverb |
| analog_four_mk2 | 155 | FX: Extern In | Ext In: Right Pan |
| analog_four_mk2 | 156 | FX: Extern In | Ext In: Right Level |
| analog_four_mk2 | 157 | FX: Chorus | Chorus: Pre-Delay |
| analog_four_mk2 | 158 | FX: Chorus | Chorus: Speed |
| analog_four_mk2 | 159 | FX: Chorus | Chorus: Depth |
| analog_four_mk2 | 160 | FX: Chorus | Chorus: Width |
| analog_four_mk2 | 161 | FX: Chorus | Chorus: Feedback |
| analog_four_mk2 | 162 | FX: Chorus | Chorus: HP Filter |
| analog_four_mk2 | 163 | FX: Chorus | Chorus: LP Filter |
| analog_four_mk2 | 164 | FX: Chorus | Chorus: Delay Send |
| analog_four_mk2 | 165 | FX: Chorus | Chorus: Reverb Send |
| analog_four_mk2 | 166 | FX: Chorus | Chorus: Mix Volume |
| analog_four_mk2 | 167 | FX: Delay | Delay: Time |
| analog_four_mk2 | 168 | FX: Delay | Delay: PingPong |
| analog_four_mk2 | 169 | FX: Delay | Delay: Stereo Width |
| analog_four_mk2 | 170 | FX: Delay | Delay: Feedback |
| analog_four_mk2 | 171 | FX: Delay | Delay: HP Filter |
| analog_four_mk2 | 172 | FX: Delay | Delay: LP Filter |
| analog_four_mk2 | 173 | FX: Delay | Delay: Overdrive |
| analog_four_mk2 | 174 | FX: Delay | Delay: Reverb Send |
| analog_four_mk2 | 175 | FX: Delay | Delay: Mix Volume |
| analog_four_mk2 | 176 | FX: Reverb | Reverb: Pre-Delay |
| analog_four_mk2 | 177 | FX: Reverb | Reverb: Decay Time |
| analog_four_mk2 | 178 | FX: Reverb | Reverb: Shelving Freq |
| analog_four_mk2 | 179 | FX: Reverb | Reverb: Shelving Gain |
| analog_four_mk2 | 180 | FX: Reverb | Reverb: HP Filter |
| analog_four_mk2 | 181 | FX: Reverb | Reverb: LP Filter |
| analog_four_mk2 | 182 | FX: Reverb | Reverb: Mix Volume |
| analog_four_mk2 | 183 | FX: LFOs | FX LFO1: Speed |
| analog_four_mk2 | 184 | FX: LFOs | FX LFO1: Multiplier |
| analog_four_mk2 | 185 | FX: LFOs | FX LFO1: Fade In/Out |
| analog_four_mk2 | 186 | FX: LFOs | FX LFO1: Start Phase |
| analog_four_mk2 | 187 | FX: LFOs | FX LFO1: Mode |
| analog_four_mk2 | 188 | FX: LFOs | FX LFO1: Waveform |
| analog_four_mk2 | 189 | FX: LFOs | FX LFO1: Destination A |
| analog_four_mk2 | 190 | FX: LFOs | FX LFO1: Depth A |
| analog_four_mk2 | 191 | FX: LFOs | FX LFO1: Destination B |
| analog_four_mk2 | 192 | FX: LFOs | FX LFO1: Depth B |
| analog_four_mk2 | 193 | FX: LFOs | FX LFO2: Speed |
| analog_four_mk2 | 194 | FX: LFOs | FX LFO2: Multiplier |
| analog_four_mk2 | 195 | FX: LFOs | FX LFO2: Fade In/Out |
| analog_four_mk2 | 196 | FX: LFOs | FX LFO2: Start Phase |
| analog_four_mk2 | 197 | FX: LFOs | FX LFO2: Mode |
| analog_four_mk2 | 198 | FX: LFOs | FX LFO2: Waveform |
| analog_four_mk2 | 199 | FX: LFOs | FX LFO2: Destination A |
| analog_four_mk2 | 200 | FX: LFOs | FX LFO2: Depth A |
| analog_four_mk2 | 201 | FX: LFOs | FX LFO2: Destination B |
| analog_four_mk2 | 202 | FX: LFOs | FX LFO2: Depth B |
| analog_four_mk2 | 203 | CVs | CV A: Coarse Tune |
| analog_four_mk2 | 204 | CVs | CV A: Fine Tune |
| analog_four_mk2 | 205 | CVs | CV A: Value |
| analog_four_mk2 | 206 | CVs | CV A: Clock |
| analog_four_mk2 | 207 | CVs | CV A: Source |
| analog_four_mk2 | 208 | CVs | CV A: Bend Depth |
| analog_four_mk2 | 209 | CVs | CV A: Note Slide Time |
| analog_four_mk2 | 210 | CVs | CV B: Coarse Tune |
| analog_four_mk2 | 211 | CVs | CV B: Fine Tune |
| analog_four_mk2 | 212 | CVs | CV B: Value |
| analog_four_mk2 | 213 | CVs | CV B: Clock |
| analog_four_mk2 | 214 | CVs | CV B: Source |
| analog_four_mk2 | 215 | CVs | CV B: Bend Depth |
| analog_four_mk2 | 216 | CVs | CV B: Note Slide Time |
| analog_four_mk2 | 217 | CVs | CV C: Coarse Tune |
| analog_four_mk2 | 218 | CVs | CV C: Fine Tune |
| analog_four_mk2 | 219 | CVs | CV C: Value |
| analog_four_mk2 | 220 | CVs | CV C: Clock |
| analog_four_mk2 | 221 | CVs | CV C: Source |
| analog_four_mk2 | 222 | CVs | CV C: Bend Depth |
| analog_four_mk2 | 223 | CVs | CV C: Note Slide Time |
| analog_four_mk2 | 224 | CVs | CV D: Coarse Tune |
| analog_four_mk2 | 225 | CVs | CV D: Fine Tune |
| analog_four_mk2 | 226 | CVs | CV D: Value |
| analog_four_mk2 | 227 | CVs | CV D: Clock |
| analog_four_mk2 | 228 | CVs | CV D: Source |
| analog_four_mk2 | 229 | CVs | CV D: Bend Depth |
| analog_four_mk2 | 230 | CVs | CV D: Note Slide Time |

## Canonical Omissions

- rytm:bt_classic:Sweep Depth: canonical row absent from supplied CSV; do not invent a source row

## Conflict Index

| Device | CSV Row | Conflict Fields |
| --- | ---: | --- |
| analog_four_mk2 | 15 | orientation |
| analog_four_mk2 | 16 | orientation |
| analog_four_mk2 | 22 | orientation |
| analog_four_mk2 | 23 | orientation |
| analog_four_mk2 | 25 | orientation |
| analog_four_mk2 | 32 | orientation |
| analog_four_mk2 | 33 | orientation |
| analog_four_mk2 | 40 | orientation |
| analog_four_mk2 | 42 | orientation |
| analog_four_mk2 | 44 | identity_or_usage |
| analog_four_mk2 | 49 | orientation |
| analog_four_mk2 | 50 | orientation |
| analog_four_mk2 | 54 | usage |
| analog_four_mk2 | 55 | orientation |
| analog_four_mk2 | 66 | usage |
| analog_four_mk2 | 71 | usage |
| analog_four_mk2 | 73 | identity_or_usage |
| analog_four_mk2 | 75 | identity_or_usage |
| analog_four_mk2 | 83 | identity_or_usage |
| analog_four_mk2 | 85 | identity_or_usage |
| analog_four_mk2 | 87 | identity_or_usage |
| analog_four_mk2 | 88 | identity_or_usage |
| analog_four_mk2 | 89 | identity_or_usage |
| analog_four_mk2 | 90 | identity_or_usage |
| analog_four_mk2 | 91 | identity_or_usage |
| analog_four_mk2 | 92 | identity_or_usage |
| analog_four_mk2 | 93 | identity_or_usage |
| analog_four_mk2 | 94 | identity_or_usage |
| analog_four_mk2 | 95 | identity_or_usage |
| analog_four_mk2 | 96 | identity_or_usage |
| analog_four_mk2 | 97 | identity_or_usage |
| analog_four_mk2 | 98 | identity_or_usage |
| analog_four_mk2 | 99 | identity_or_usage |
| analog_four_mk2 | 100 | identity_or_usage |
| analog_four_mk2 | 101 | identity_or_usage |
| analog_four_mk2 | 102 | identity_or_usage |
| analog_four_mk2 | 103 | identity_or_usage |
| analog_four_mk2 | 104 | identity_or_usage |
| analog_four_mk2 | 105 | identity_or_usage |
| analog_four_mk2 | 106 | identity_or_usage |
| analog_four_mk2 | 107 | orientation |
| analog_four_mk2 | 109 | orientation |
| analog_four_mk2 | 112 | usage |
| analog_four_mk2 | 113 | identity_or_usage |
| analog_four_mk2 | 115 | identity_or_usage |
| analog_four_mk2 | 117 | orientation |
| analog_four_mk2 | 118 | usage |
| analog_four_mk2 | 119 | orientation |
| analog_four_mk2 | 122 | usage |
| analog_four_mk2 | 123 | identity_or_usage |
| analog_four_mk2 | 125 | identity_or_usage |
| analog_four_mk2 | 127 | identity_or_usage |
| analog_four_mk2 | 128 | identity_or_usage |
| analog_four_mk2 | 129 | identity_or_usage |
| analog_four_mk2 | 130 | identity_or_usage |
| analog_four_mk2 | 131 | identity_or_usage |
| analog_four_mk2 | 132 | identity_or_usage |
| analog_four_mk2 | 133 | identity_or_usage |
| analog_four_mk2 | 134 | identity_or_usage |
| analog_four_mk2 | 135 | identity_or_usage |
| analog_four_mk2 | 136 | identity_or_usage |
| analog_four_mk2 | 137 | identity_or_usage |
| analog_four_mk2 | 138 | identity_or_usage |
| analog_four_mk2 | 139 | identity_or_usage |
| analog_four_mk2 | 140 | identity_or_usage |
| analog_four_mk2 | 141 | identity_or_usage |
| analog_four_mk2 | 142 | identity_or_usage |
| analog_four_mk2 | 143 | identity_or_usage |
| analog_four_mk2 | 144 | identity_or_usage |
| analog_four_mk2 | 145 | identity_or_usage |
| analog_four_mk2 | 146 | identity_or_usage |
| analog_four_mk2 | 147 | identity_or_usage |
| analog_four_mk2 | 148 | identity_or_usage |
| analog_four_mk2 | 149 | identity_or_usage |
| analog_four_mk2 | 150 | identity_or_usage |
| analog_four_mk2 | 151 | identity_or_usage |
| analog_four_mk2 | 152 | identity_or_usage |
| analog_four_mk2 | 153 | identity_or_usage |
| analog_four_mk2 | 154 | identity_or_usage |
| analog_four_mk2 | 155 | identity_or_usage |
| analog_four_mk2 | 156 | identity_or_usage |
| analog_four_mk2 | 157 | identity_or_usage |
| analog_four_mk2 | 158 | identity_or_usage |
| analog_four_mk2 | 159 | identity_or_usage |
| analog_four_mk2 | 160 | identity_or_usage |
| analog_four_mk2 | 161 | identity_or_usage |
| analog_four_mk2 | 162 | identity_or_usage |
| analog_four_mk2 | 163 | identity_or_usage |
| analog_four_mk2 | 164 | identity_or_usage |
| analog_four_mk2 | 165 | identity_or_usage |
| analog_four_mk2 | 166 | identity_or_usage |
| analog_four_mk2 | 167 | identity_or_usage |
| analog_four_mk2 | 168 | identity_or_usage |
| analog_four_mk2 | 169 | identity_or_usage |
| analog_four_mk2 | 170 | identity_or_usage |
| analog_four_mk2 | 171 | identity_or_usage |
| analog_four_mk2 | 172 | identity_or_usage |
| analog_four_mk2 | 173 | identity_or_usage |
| analog_four_mk2 | 174 | identity_or_usage |
| analog_four_mk2 | 175 | identity_or_usage |
| analog_four_mk2 | 176 | identity_or_usage |
| analog_four_mk2 | 177 | identity_or_usage |
| analog_four_mk2 | 178 | identity_or_usage |
| analog_four_mk2 | 179 | identity_or_usage |
| analog_four_mk2 | 180 | identity_or_usage |
| analog_four_mk2 | 181 | identity_or_usage |
| analog_four_mk2 | 182 | identity_or_usage |
| analog_four_mk2 | 183 | identity_or_usage |
| analog_four_mk2 | 184 | identity_or_usage |
| analog_four_mk2 | 185 | identity_or_usage |
| analog_four_mk2 | 186 | identity_or_usage |
| analog_four_mk2 | 187 | identity_or_usage |
| analog_four_mk2 | 188 | identity_or_usage |
| analog_four_mk2 | 189 | identity_or_usage |
| analog_four_mk2 | 190 | identity_or_usage |
| analog_four_mk2 | 191 | identity_or_usage |
| analog_four_mk2 | 192 | identity_or_usage |
| analog_four_mk2 | 193 | identity_or_usage |
| analog_four_mk2 | 194 | identity_or_usage |
| analog_four_mk2 | 195 | identity_or_usage |
| analog_four_mk2 | 196 | identity_or_usage |
| analog_four_mk2 | 197 | identity_or_usage |
| analog_four_mk2 | 198 | identity_or_usage |
| analog_four_mk2 | 199 | identity_or_usage |
| analog_four_mk2 | 200 | identity_or_usage |
| analog_four_mk2 | 201 | identity_or_usage |
| analog_four_mk2 | 202 | identity_or_usage |
| analog_four_mk2 | 203 | identity_or_usage |
| analog_four_mk2 | 204 | identity_or_usage |
| analog_four_mk2 | 205 | identity_or_usage |
| analog_four_mk2 | 206 | identity_or_usage |
| analog_four_mk2 | 207 | identity_or_usage |
| analog_four_mk2 | 208 | identity_or_usage |
| analog_four_mk2 | 209 | identity_or_usage |
| analog_four_mk2 | 210 | identity_or_usage |
| analog_four_mk2 | 211 | identity_or_usage |
| analog_four_mk2 | 212 | identity_or_usage |
| analog_four_mk2 | 213 | identity_or_usage |
| analog_four_mk2 | 214 | identity_or_usage |
| analog_four_mk2 | 215 | identity_or_usage |
| analog_four_mk2 | 216 | identity_or_usage |
| analog_four_mk2 | 217 | identity_or_usage |
| analog_four_mk2 | 218 | identity_or_usage |
| analog_four_mk2 | 219 | identity_or_usage |
| analog_four_mk2 | 220 | identity_or_usage |
| analog_four_mk2 | 221 | identity_or_usage |
| analog_four_mk2 | 222 | identity_or_usage |
| analog_four_mk2 | 223 | identity_or_usage |
| analog_four_mk2 | 224 | identity_or_usage |
| analog_four_mk2 | 225 | identity_or_usage |
| analog_four_mk2 | 226 | identity_or_usage |
| analog_four_mk2 | 227 | identity_or_usage |
| analog_four_mk2 | 228 | identity_or_usage |
| analog_four_mk2 | 229 | identity_or_usage |
| analog_four_mk2 | 230 | identity_or_usage |
| analog_rytm_mk2 | 1 | cc_max, cc_min, nrpn_max, nrpn_min |
| analog_rytm_mk2 | 2 | cc_min, nrpn_min |
| analog_rytm_mk2 | 4 | cc_max, nrpn_max |
| analog_rytm_mk2 | 5 | cc_max, nrpn_max |
| analog_rytm_mk2 | 6 | cc_max, nrpn_max |
| analog_rytm_mk2 | 7 | cc_max, nrpn_max |
| analog_rytm_mk2 | 9 | cc_max, nrpn_max |
| analog_rytm_mk2 | 10 | cc_max, nrpn_max |
| analog_rytm_mk2 | 11 | usage |
| analog_rytm_mk2 | 13 | cc_max, nrpn_max |
| analog_rytm_mk2 | 14 | cc_max, nrpn_max |
| analog_rytm_mk2 | 15 | cc_max, nrpn_max |
| analog_rytm_mk2 | 16 | orientation |
| analog_rytm_mk2 | 17 | orientation |
| analog_rytm_mk2 | 18 | orientation |
| analog_rytm_mk2 | 19 | cc_max, nrpn_max |
| analog_rytm_mk2 | 32 | cc_max, cc_min, nrpn_max, nrpn_min, orientation |
| analog_rytm_mk2 | 33 | orientation |
| analog_rytm_mk2 | 35 | identity_or_usage |
| analog_rytm_mk2 | 36 | cc_max, nrpn_max |
| analog_rytm_mk2 | 37 | cc_max, nrpn_max |
| analog_rytm_mk2 | 38 | cc_max, nrpn_max |
| analog_rytm_mk2 | 46 | usage |
| analog_rytm_mk2 | 59 | cc_max, nrpn_max |
| analog_rytm_mk2 | 60 | usage |
| analog_rytm_mk2 | 62 | usage |
| analog_rytm_mk2 | 65 | cc_max, nrpn_max |
| analog_rytm_mk2 | 66 | orientation |
| analog_rytm_mk2 | 82 | cc_max, nrpn_max |
| analog_rytm_mk2 | 83 | cc_max, nrpn_max |
| analog_rytm_mk2 | 85 | cc_max, nrpn_max |
| analog_rytm_mk2 | 86 | cc_max, nrpn_max |
| analog_rytm_mk2 | 88 | cc_max, nrpn_max |
| analog_rytm_mk2 | 89 | cc_max, nrpn_max |
| analog_rytm_mk2 | 100 | orientation |
| analog_rytm_mk2 | 108 | orientation |
| analog_rytm_mk2 | 114 | usage |
| analog_rytm_mk2 | 116 | orientation |
| analog_rytm_mk2 | 120 | usage |
| analog_rytm_mk2 | 124 | orientation |
| analog_rytm_mk2 | 128 | usage |
| analog_rytm_mk2 | 130 | cc_max, nrpn_max |
| analog_rytm_mk2 | 132 | orientation |
| analog_rytm_mk2 | 140 | orientation |
| analog_rytm_mk2 | 148 | orientation |
| analog_rytm_mk2 | 154 | usage |
| analog_rytm_mk2 | 156 | orientation |
| analog_rytm_mk2 | 164 | orientation |
| analog_rytm_mk2 | 172 | orientation |
| analog_rytm_mk2 | 180 | orientation |
| analog_rytm_mk2 | 181 | orientation |
| analog_rytm_mk2 | 188 | orientation |
| analog_rytm_mk2 | 196 | orientation |
| analog_rytm_mk2 | 204 | orientation |
| analog_rytm_mk2 | 205 | orientation |
| analog_rytm_mk2 | 206 | orientation |
| analog_rytm_mk2 | 208 | orientation |
| analog_rytm_mk2 | 220 | identity_or_usage, orientation |
| analog_rytm_mk2 | 221 | identity_or_usage, orientation |
| analog_rytm_mk2 | 222 | identity_or_usage |
| analog_rytm_mk2 | 223 | identity_or_usage |
| analog_rytm_mk2 | 224 | identity_or_usage, usage |
| analog_rytm_mk2 | 225 | identity_or_usage, orientation |
| analog_rytm_mk2 | 226 | identity_or_usage, orientation |
| analog_rytm_mk2 | 227 | identity_or_usage |
| analog_rytm_mk2 | 228 | identity_or_usage, orientation |
| analog_rytm_mk2 | 229 | identity_or_usage |
| analog_rytm_mk2 | 230 | identity_or_usage |
| analog_rytm_mk2 | 231 | identity_or_usage |
| analog_rytm_mk2 | 232 | cc_max, cc_min, identity_or_usage, orientation |
| analog_rytm_mk2 | 233 | cc_max, cc_min, identity_or_usage, orientation |
| analog_rytm_mk2 | 234 | cc_max, cc_min, identity_or_usage, orientation |
| analog_rytm_mk2 | 235 | identity_or_usage |
| analog_rytm_mk2 | 236 | identity_or_usage |
| analog_rytm_mk2 | 237 | identity_or_usage |
| analog_rytm_mk2 | 238 | identity_or_usage |
| analog_rytm_mk2 | 239 | identity_or_usage |
| analog_rytm_mk2 | 240 | identity_or_usage, usage |
| analog_rytm_mk2 | 241 | identity_or_usage, usage |
| analog_rytm_mk2 | 242 | identity_or_usage |
| analog_rytm_mk2 | 243 | identity_or_usage |
| analog_rytm_mk2 | 244 | orientation |
| analog_rytm_mk2 | 249 | orientation |
| analog_rytm_mk2 | 253 | orientation |
| analog_rytm_mk2 | 257 | orientation |
| analog_rytm_mk2 | 261 | orientation |
| analog_rytm_mk2 | 264 | orientation |
| analog_rytm_mk2 | 266 | orientation |
| analog_rytm_mk2 | 268 | orientation |
| analog_rytm_mk2 | 271 | orientation |
| analog_rytm_mk2 | 272 | orientation |
| analog_rytm_mk2 | 275 | usage |
| analog_rytm_mk2 | 277 | orientation |
| analog_rytm_mk2 | 279 | orientation |
| analog_rytm_mk2 | 280 | orientation |
| analog_rytm_mk2 | 281 | orientation |
| analog_rytm_mk2 | 282 | orientation |
| analog_rytm_mk2 | 283 | orientation |
| analog_rytm_mk2 | 285 | orientation |
| analog_rytm_mk2 | 286 | orientation |
| analog_rytm_mk2 | 290 | orientation |
| analog_rytm_mk2 | 291 | orientation |
| analog_rytm_mk2 | 293 | orientation |
| analog_rytm_mk2 | 295 | orientation |
| analog_rytm_mk2 | 296 | usage |
| analog_rytm_mk2 | 303 | orientation |
| analog_rytm_mk2 | 307 | orientation |
| analog_rytm_mk2 | 314 | identity_or_usage |
| analog_rytm_mk2 | 316 | orientation |
| analog_rytm_mk2 | 321 | cc_max, nrpn_max |

## Holds And Evidence

Runtime binding and inventory evidence are reported, not new eligibility grants.
`validated_runtime` is not a physical receipt. Current source/scope/locks/guardrails
and exact-plan validation remain mandatory, including the limited Pad 2 evidence.
A4/BOTH, paired precision, unsaved-state freshness and automatic restore remain held.
All CY Ride SRC controls remain blocked. The narrow inbound HIT/TYP observations
do not resolve native slot semantics or outbound behavior. A4 seven disproved
live ordinals and the F1 native/wire distinction are preserved in retained evidence.
The 125 extra A4 rows include FX/CV pages and Noise Color: no saved-field or SEND promotion.
Physical audition, save/reload chronology and fresh recapture remain operator work.
Official manual and retained hardware-document links accompany every row.

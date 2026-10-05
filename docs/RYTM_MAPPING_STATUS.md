# Rytm and A4 mapping status

Evidence inventory dated 2026-10-01, inspected at
[PR #252 source `8cfa6f7b6cf9469ffa134598182febb60ecdd1df`](https://github.com/buzzijose-hub/RytmRandomizer/tree/8cfa6f7b6cf9469ffa134598182febb60ecdd1df).
The Pi capability-matrix and offline-projection counts below belong to that
pinned source, not to the Studio PR #254 inventory. Pi-only source and test
links point to the same revision. This document separates existing facts from
promotions still to implement or validate; it is not an output grant. The
accompanying captured-machine repair must record its own completed checks.

## Studio alias closure: descriptive coverage and protected projection

The eighth Studio mapping increment completes compact bindings for the eleven
historically missing families below: **all 224 SRC catalog rows now round-trip
descriptively**, including the 68 previously unnamed rows. Existing keys keep
precedence; fallback keys have the exact form `src_<canonical-machine>_<NRPN-low-byte>`.
SY Dual VCO's label resolves to canonical `dual_vco`. No CC address, native
offset, ordinal domain or physical validation was invented.

One shared conservative policy governs captured projection, canonical-device
mutation, prepared live plans and the passive inventory. Level and SY Raw Noise
Level remain excluded. **Every CY Ride SRC row** is blocked with
`src_cy_ride_slot_unverified`, before the narrower pending, level, pitch or
selector checks and regardless of compact/fallback spelling. The other
disputed/guarded rows below remain blocked.
Newly exposed pitch controls, including Chip Offset 2–4 and HH Lab Tune 1–6,
and selector controls stay protected. These refusals retain their descriptive
names and addresses. They are omitted from captured mutation parameters, and a
constructed changed protected proposal blocks the whole plan through the
existing `candidate_high_risk` reason. Locked or untargeted rows do not block
supported effective-scope changes. Paired LFO Depth keeps its separate refusal.

SRC projection additionally checks exact raw machine identity and canonical pad
compatibility; masked high-bit IDs and unverified tom identities gain no SRC
authority. The saved frame is retained byte-for-byte. The legacy offline engine
corpus uses device spelling `rytm_mk2` and includes arithmetic on `lev`; that
frozen arithmetic is preserved. Canonical captured-device mutation freezes it,
and every live plan refuses changed Level regardless of device/alias spelling.

The October 5 review repair reduces the earlier **29 eligible fallback rows to
25 documented-only primary-byte SRC projections** across ten families, before
unit-specific capture/authority checks. The four removed rows are CY Ride Tail
Decay and Component 1/2/3; none of its eight SRC rows is live-eligible. Unmodified
retained init and RIO return frames project respectively **64/65 SRC values plus
264 common values (328/329 total)** at the pre-repair baseline. After this guard,
the counts are **64/61 SRC plus 264 common (328/325 total)**. The init exposes CY
Classic/CB Classic; the RIO return exposes CB Metallic but omits all CY Ride SRC.
Altered codec fixtures exercise
the remaining families as software contracts only. These counts are software
projection evidence, not outbound hardware, unsaved-state or touring acceptance.
The pinned Pi counts and pre-patch tables below remain historical.

These backend bindings do not establish frontend acceptance. The Pi appliance's SRC
protection screen already renders catalog labels, projected values and blockers;
it needs the repaired backend and a fresh capture. At the pre-October-5 Studio
baseline, pad cards use a fixed Synth definition list and omit the new namespaced
keys, and decorative performance knobs do not display snapshot values. The
separate UI repair owns that display gap and its verification; this backend
audit is not a musician-facing UI acceptance receipt.

The October 5 UI repair derives `src_parameters` display metadata from the
same Python catalog and blockers, showing names, captured values, addresses,
evidence labels and missing/protected reasons. Legacy payloads without metadata
retain their rendering. Imported display metadata is not trusted: serialization
derives it anew. Combined software/build acceptance is recorded separately.

The Studio [Device Support Inventory](DEVICE_SUPPORT_INVENTORY.md) reports
**105 A4 MIDI rows**, including the manual CC catalog, and **91 synth-track
MIDI controls**. The Pi matrix's **112 rows** include those 105 MIDI rows plus
seven native-only semantic controls. Studio separately counts **106 native
locations per track: 98 semantic field names plus eight fraction components**.
Those location counts and the Pi matrix's 98 saved-field projections describe
different dimensions; coupled components are not independent controls.

### October 5 fallback SRC audit

Baseline `0138d00b` had 68 fallback bindings and 29 policy-eligible continuous
rows. The table audits that exact 29-row set against canonical CC/NRPN facts,
saved-sound primary-byte locations and current shared policy. All 29 have
`mutation_status=documented_only`, `value_kind=continuous`, range 0..127,
zero-based orientation and no paired CC. **25 remain documented-only eligible;
4 are now blocked.** Eligible means conditional software projection/CC7 planning,
not hardware validation, semantic calibration or permission to SEND.

Native offsets below are sound-relative **primary bytes**, each followed by a
retained low byte. C = [canonical MIDI catalog](../rytm_randomizer/data/analog_rytm_midi.py);
S = [canonical saved-slot table](../rytm_randomizer/data/analog_rytm_kit_layout.py).
Neither proves full-word/native-to-wire semantics. I/R = unmodified
[initialized/RIO returned frames](../tests/fixtures/rio145) exercised by
[capture tests](../tests/cockpit/test_rytm_alias_capture.py).
T = explicitly synthetic machine substitution in those tests, not a new target
return. [Shared policy](../rytm_randomizer/cockpit/data/rytm_parameter_map.py)
and [inventory](../rytm_randomizer/reports/device_support_inventory.py) determine
the status in every row. CB Metallic Decay also has a typed `DEC` recipe label;
the other 24 eligible rows have slot bindings but no typed machine-source recipe
layout. No missing recipe layout or historical fixture is a live calibration.

<!-- fallback-src-audit -->
| Exact Key | Canonical Name | CC | NRPN | Native Primary | Evidence | Current Policy |
| --- | --- | --- | --- | --- | --- | --- |
| `src_cb_classic_2` | Decay Time | 18 | 1:2 | 0x20 | C/S/I | documented-only eligible |
| `src_cb_metallic_2` | Decay Time | 18 | 1:2 | 0x20 | C/S/R | documented-only eligible |
| `src_cy_classic_2` | Decay | 18 | 1:2 | 0x20 | C/S/I | documented-only eligible |
| `src_cy_classic_3` | Color | 19 | 1:3 | 0x22 | C/S/I | documented-only eligible |
| `src_cy_classic_4` | Tone | 20 | 1:4 | 0x24 | C/S/I | documented-only eligible |
| `src_cy_metallic_2` | Decay Time | 18 | 1:2 | 0x20 | C/S/T | documented-only eligible |
| `src_cy_metallic_3` | Tone | 19 | 1:3 | 0x22 | C/S/T | documented-only eligible |
| `src_cy_metallic_4` | Transient Decay | 20 | 1:4 | 0x24 | C/S/T | documented-only eligible |
| `src_cy_ride_2` | Tail Decay | 18 | 1:2 | 0x20 | C/S/R | src_cy_ride_slot_unverified |
| `src_cy_ride_5` | Component 1 | 21 | 1:5 | 0x26 | C/S/R | src_cy_ride_slot_unverified |
| `src_cy_ride_6` | Component 2 | 22 | 1:6 | 0x28 | C/S/R | src_cy_ride_slot_unverified |
| `src_cy_ride_7` | Component 3 | 23 | 1:7 | 0x2A | C/S/R | src_cy_ride_slot_unverified |
| `src_dual_vco_2` | Osc 1 Decay | 18 | 1:2 | 0x20 | C/S/T | documented-only eligible |
| `src_dual_vco_3` | Balance | 19 | 1:3 | 0x22 | C/S/T | documented-only eligible |
| `src_dual_vco_6` | Osc 2 Decay | 22 | 1:6 | 0x28 | C/S/T | documented-only eligible |
| `src_hh_basic_2` | Decay Time | 18 | 1:2 | 0x20 | C/S/T | documented-only eligible |
| `src_hh_basic_3` | Tone | 19 | 1:3 | 0x22 | C/S/T | documented-only eligible |
| `src_hh_basic_4` | Transient Decay | 20 | 1:4 | 0x24 | C/S/T | documented-only eligible |
| `src_hh_lab_2` | Decay Time | 18 | 1:2 | 0x20 | C/S/T | documented-only eligible |
| `src_sy_chip_2` | Decay | 18 | 1:2 | 0x20 | C/S/T | documented-only eligible |
| `src_ut_impulse_1` | Attack | 17 | 1:1 | 0x1E | C/S/T | documented-only eligible |
| `src_ut_impulse_2` | Decay | 18 | 1:2 | 0x20 | C/S/T | documented-only eligible |
| `src_ut_noise_1` | LP Frequency | 17 | 1:1 | 0x1E | C/S/T | documented-only eligible |
| `src_ut_noise_2` | Decay | 18 | 1:2 | 0x20 | C/S/T | documented-only eligible |
| `src_ut_noise_3` | Sweep Depth | 19 | 1:3 | 0x22 | C/S/T | documented-only eligible |
| `src_ut_noise_4` | Sweep Time | 20 | 1:4 | 0x24 | C/S/T | documented-only eligible |
| `src_ut_noise_5` | LP Resonance | 21 | 1:5 | 0x26 | C/S/T | documented-only eligible |
| `src_ut_noise_6` | HP Frequency | 22 | 1:6 | 0x28 | C/S/T | documented-only eligible |
| `src_ut_noise_7` | Attack | 23 | 1:7 | 0x2A | C/S/T | documented-only eligible |
<!-- /fallback-src-audit -->

Reproduce and check every table cell against the current catalogs/inventory:

```powershell
Set-Location -LiteralPath 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
& .\.venv\Scripts\python.exe -m pytest tests/test_device_support_inventory.py -k fallback_src_audit -n 0 -q
```

The audit test checks all 29 exact bindings and evidence references, recomputes
the complete eligible fallback set (25), checks the four blocked keys and keeps
all 224 descriptive SRC bindings. Capture/planning regressions separately prove
omission, freezing and whole-plan refusal on physically allowed pad 11, including
a mixed common-field proposal. Unknown/reserved and low bytes remain unchanged.

## What is already mapped

The Rytm OS 1.72 MIDI catalog contains **323 rows: 224 machine SRC rows across
all 33 catalog machines, and 99 common rows**. Every SRC row already has a CC
address, NRPN address and a corresponding saved-sound slot. Adding a missing
Cockpit name therefore does not require inventing a new offset or MIDI address.
It also does not prove that a saved native value and a live MIDI value have the
same semantics or that a whole native word can be restored.

Canonical sources:

- [Machine identities and pad compatibility](../rytm_randomizer/data/rytm_machine_catalog.py),
  `RYTM_MACHINE_PROFILES`: 33 identities; value 27 is the separate
  disabled synth state in `RytmMachine`, not a missing 34th sounding machine.
- [Manual MIDI rows and legal domains](../rytm_randomizer/data/analog_rytm_midi.py),
  `ANALOG_RYTM_MACHINE_SRC_BY_MACHINE` and `ANALOG_RYTM_MANUAL_CC` provide the
  rows and value metadata. The `validated_runtime` label denotes established software scope;
  it does not supply a physical receipt for every value on every machine.
- [Saved-sound slot offsets](../rytm_randomizer/data/analog_rytm_kit_layout.py),
  `RYTM_SOUND_FIELD_BY_NRPN_LSB`. SRC NRPN low byte 0..7 maps to
  sound offsets `0x1C, 0x1E, 0x20, 0x22, 0x24, 0x26, 0x28, 0x2A`.
- [Exact typed saved-KIT fields](../rytm_randomizer/data/analog_rytm_kit_fields.py)
  and [codec accessors](../rytm_randomizer/devices/strategies/analog_rytm_kit_fields.py):
  native words and their low bytes remain in the original frame. The existing
  Cockpit projection uses their seven-bit primary byte.
- [Cockpit compact aliases](../rytm_randomizer/cockpit/data/rytm_parameter_map.py),
  `cockpit_parameter_mapping()` and `cockpit_parameter_key()` provide reversible bindings.
- [Pi descriptive capability matrix at the pinned source](https://github.com/buzzijose-hub/RytmRandomizer/blob/8cfa6f7b6cf9469ffa134598182febb60ecdd1df/rytm_randomizer/cockpit/capture/appliance_capabilities.py),
  Rytm row projection at line 222. This matrix is descriptive, not a readiness
  decision or physical validation ledger.

## Pi PR #252 counts and readiness boundaries at the pinned source

| Layer at the pinned PR #252 SHA | Rytm | A4 |
| --- | --- | --- |
| Descriptive catalog/matrix rows | 323 | 112 |
| Matrix rows associated with saved fields | 293 | 98 |
| Rows without a saved-field binding in this matrix | 30 | 14 |
| Descriptive conditional CC7 rows | 155 | 0 |
| Descriptive blocked live rows | 168 | 112 |
| Actual captured Cockpit common fields | 22 per pad | Separate exact offline projection |
| Actual captured Cockpit SRC fields before section repair | 0 | Not applicable |
| Pi scoped appliance live APPLY at the pinned source | Refused | Refused |

The Rytm matrix's 155 conditional rows comprise 134 SRC rows and 21 common
rows. It cannot substitute for composed capture/readiness checks: SY Raw Noise
Level is intentionally omitted by the snapshot shell although the descriptive
matrix currently lists it as conditional. The matrix must eventually consume
that same exclusion rather than advertising a stronger promotion.

The common Rytm projection consists of Filter 8, Amp 7 and LFO 7. **21 are
single-CC rows; the remaining LFO Depth row is paired CC 109/118 and a changed
value blocks the whole prepared plan.** LFO Destination and Amp Volume stay
excluded. Sample 8, generic Synth 8 and FX 28 have stored-field facts but no
current Cockpit live scope. The remaining matrix-unbound rows are Trig 7,
Euclidean 7, Performance 12 and four Common rows. This is a projection gap,
not proof that all 30 native fields are unknown: `RytmKit.track_level()` already
reads Track Level. Sequencing, performance, levels, machine switching and
persistent writes remain protected.

At the inspected SHA, catalog machine rows retain `section=machine_key` in
snapshot-shell events, while `cockpit_parameter_key()` accepts SRC aliases only
for section `SRC`. The bridge therefore drops every machine SRC row, including
families with complete aliases. Pure decoding of the retained 2026-10-01 frame
`5f75b9fb4856e8c7` produced 70 SRC events and zero promoted SRC keys; both RIO145
fixtures reproduced the omission. The isolated accompanying repair owns this
normalization and fixture-proven XT Classic machine facts on pads 6–8. It must
preserve exact reverse CC matching and unrelated/candidate-only facts.

Those zero-SRC bridge counts are **historical pre-patch counts**, not the
expected result of the accompanying narrow repair. Without adding any aliases,
the retained October 1 source should then promote 60 SRC keys plus 264 common
keys, for 324 keys: seven SRC keys on each of pads 1–4 and 6–8, five on pad 5,
three on each of pads 9–10, and none on pads 11–12 because CY Ride/CB Classic
aliases are still absent. Both initialized/RIO returned fixtures should also
promote 60 SRC keys. This expectation must be checked through the composed public
decode/bridge APIs. It does not make the 11 missing alias families complete or
change the paired-control SEND refusal. A passive check of the working repair
confirmed these 324/60 counts for the retained studio frame and both RIO KIT
fixtures, with all three XT rows marked `mutation_ready` and exact frame bytes
preserved. This check used `decode_kit_capture_frame()` and
`cockpit_snapshot_from_rytm_capture()`; it opened no MIDI ports. Final committed
source and whole-suite receipts belong to the accompanying repair record.

## All 33 Rytm families

`C/S/A/E` means **catalog rows / saved-slot bindings / existing compact aliases /
descriptive conditional CC7 rows** at the inspected SHA. E is neither actual
bridge readiness nor a full native-precision claim. All actual SRC bridge
counts are zero before the section repair. Every family's Level row stays
protected, so E normally excludes at least one row.

`N` means accept the exact canonical owning section in the existing reverse
lookup, then verify composed capture → mutation → plan with the existing
fixture seams. `G` means add reversible catalog-derived missing names, preserving
existing compact keys and the exclusions below. Neither action grants a new
physical receipt.

| Machine (stored ID) | C/S/A/E | Existing evidence and concrete next action |
| --- | --- | --- |
| BD Hard (0) | 8/8/8/7 | N; initialized fixture and historical shell use. Current studio trial proved common-page controls only. |
| BD Classic (1) | 8/8/8/7 | N; retain typed Waveform 0..2; obtain a bounded SRC observation before claiming current physical coverage. |
| SD Hard (2) | 8/8/8/7 | N; RIO return and historical KIT 13 SRC observations exist. |
| SD Classic (3) | 8/8/8/7 | N; retain centered/locked tuning policy; current per-field physical proof is absent. |
| RS Hard (4) | 8/8/8/7 | N; initialized/RIO return fixtures already exercise stored machine and slots. |
| RS Classic (5) | 8/8/8/7 | N; preserve separate Tune Osc 1/Osc 2 names and tuning protection. |
| CP Classic (6) | 8/8/8/7 | N; RIO return pins bytes; verify selector-like Clap Rate semantics before treating display steps as linear. |
| BT Classic (7) | 6/6/6/5 | N; typed Snap Type 0..3 and historical shell SRC observations exist. Reconcile native recipe unused slot versus manual Sweep Depth separately. |
| XT Classic (8) | 8/8/8/7 | N plus narrowly promote fixture-proven ID 8 on pads 6–8; initialized and returned fixtures already resolve the label. |
| CH Classic (9) | 4/4/4/3 | N; initialized/RIO return and historical Color/Tune/Decay use exist. |
| OH Classic (10) | 4/4/4/3 | N; initialized/RIO return evidence; obtain isolated current SRC observations. |
| CY Classic (11) | 5/5/0/0 | G for five existing rows; initialized capture already resolves identity and slots. |
| CB Classic (12) | 4/4/0/0 | G for four manual rows; current retained source resolves identity. Keep PW1/PW2 saved-only until their addresses are established. |
| BD FM (13) | 8/8/8/7 | N; preserve FM Tune/tuning protection and exact catalog bounds. |
| SD FM (14) | 8/8/8/7 | N; current retained capture contains this machine; it is not a physical SRC send proof. |
| UT Noise (15) | 8/8/0/0 | G for eight rows; preserve centered Sweep Depth and tuning/routing policy. No new saved offsets needed. |
| UT Impulse (16) | 4/4/0/0 | G for Level/Attack/Decay; keep Polarity blocked until POS/NEG native and MIDI encodings are established. |
| CH Metallic (17) | 3/3/3/2 | N for three manual rows; preserve Level exclusion. |
| OH Metallic (18) | 3/3/3/2 | N for three manual rows; preserve Level exclusion. |
| CY Metallic (19) | 5/5/0/0 | G for five rows; obtain isolated current physical observations. |
| CB Metallic (20) | 4/4/0/0 | G for four manual rows; RIO return exists. Keep additional native PW1/PW2 saved-only. |
| BD Plastic (21) | 8/8/8/7 | N; preserve separate VCO Click/Dust labels and bounds. |
| BD Silky (22) | 8/8/8/7 | N; preserve machine-specific names instead of borrowing BD Hard names. |
| SD Natural (23) | 8/8/8/7 | N; current retained source resolves its eight slots; no current SRC audition claim. |
| HH Basic (24) | 6/6/0/0 | G; Osc Reset already has selector domain 0..1; retain categorical protection. Historical captured identity exists. |
| CY Ride (25) | 8/8/0/0 | G for unambiguous rows; block disputed Hit Decay/Cymbal Type associations until native/MIDI slots are reconciled. RIO return and historical live subset exist. |
| BD Sharp (26) | 8/8/8/7 | N; RIO return and historical live source use exist. Preserve Waveform 0..11. |
| SY Dual VCO (28) | 8/8/0/0 | G plus canonical label→`dual_vco` resolution. Keep Osc 2 Detune outside generic Forge live scope; reuse existing guarded shell evidence. |
| SY Chip (29) | 8/8/0/0 | G only for unambiguous continuous/tuning rows. Keep Waveform and mode-dependent Speed blocked pending legal ordinal tables. |
| BD Acoustic (30) | 8/8/8/7 | N; Waveform 0..11 exists in catalog; historical follow-up explicitly leaves selector discovery pending. |
| SD Acoustic (31) | 8/8/8/7 | N; retain machine-specific Impact/Hold names; require bounded current SRC observations. |
| SY Raw (32) | 8/8/8/7 | N but keep Noise Level omitted and invalid waveform anchors preserved. Actual shell exposure is at most six SRC rows, not matrix E=7. |
| HH Lab (33) | 8/8/0/0 | G; historical Tune 1–6 observations exist; keep all tuning controls protected by default. |

## Eleven historically missing alias families: unchanged catalog contents

These 68 rows now have descriptive compact bindings in Studio. Parameters are
shown in CC order; each first entry is CC 16 and corresponding NRPN is `1:0`.
Subsequent entries advance together through the family’s listed range.

| Family | CC range | Existing parameters |
| --- | --- | --- |
| CY Classic | 16–20 | Level, Tune, Decay, Color, Tone |
| CB Classic | 16–19 | Level, Tune, Decay Time, Detune |
| UT Noise | 16–23 | Level, LP Frequency, Decay, Sweep Depth, Sweep Time, LP Resonance, HP Frequency, Attack |
| UT Impulse | 16–19 | Level, Attack, Decay, Polarity |
| CY Metallic | 16–20 | Level, Tune, Decay Time, Tone, Transient Decay |
| CB Metallic | 16–19 | Level, Tune, Decay Time, Detune |
| HH Basic | 16–21 | Level, Tune, Decay Time, Tone, Transient Decay, Osc Reset |
| CY Ride | 16–23 | Level, Tune, Tail Decay, Hit Decay, Cymbal Type, Component 1, Component 2, Component 3 |
| SY Dual VCO | 16–23 | Level, Osc 1 Tune, Osc 1 Decay, Balance, Osc 2 Detune, Osc Config, Osc 2 Decay, Bend |
| SY Chip | 16–23 | Level, Tune, Decay, Waveform, Speed, Offset 2, Offset 3, Offset 4 |
| HH Lab | 16–23 | Level, Tune 1, Decay Time, Tune 2, Tune 3, Tune 4, Tune 5, Tune 6 |

The closure uses existing aliases first, then stable namespaced SRC
slot keys derived from canonical `(machine, nrpn_lsb)` identity. Reverse lookup
must revalidate the same parameter, CC and native slot. The generic
[mutation engine](../rytm_randomizer/cockpit/engine/mutate.py), `mutate()`, already
clamps mapped values to catalog bounds; the existing
[send-plan builder](../rytm_randomizer/cockpit/engine/send_plan.py), `prepare_send_plan()`,
already selects target-minus-locks and exact catalog CCs. There is no need for
a second randomizer, registry or renderer.

Do not turn uncertainty into a generic numeric key merely because a byte exists.
Keep unsafe rows absent from sendable capture projection while preserving the
original frame, or retain them with a per-control freeze and whole-plan refusal
if changed. Current Forge generic mutation does not implement a per-row shell
detune safety window. A mapped name alone must not bypass that window.

## Semantic discrepancies and facts already available elsewhere

1. **CY Ride:** the manual catalog's `cy_ride` row assigns Hit Decay
   to CC 19/NRPN 1:3 and Cymbal Type to CC 20/NRPN 1:4. The typed native recipe at
   `RYTM_MACHINE_PARAMETER_NAMES` in `data/analog_rytm_kit_fields.py` assigns
   slot 4 `TYP`, slot 5 `HIT`.
   [Elektron’s OS 1.72 manual](https://www.elektron.se/wp-content/uploads/2025/01/Analog-Rytm-MKII-User-Manual_ENG_OS1.72_250130.pdf)
   distinguishes the two controls, but its MIDI appendix does not independently
   establish saved-byte association. Do not swap CCs or saved offsets based on
   the returned recipe alone. Isolated saved changes plus incoming encoder MIDI
   observation resolve this discrepancy without an initial outbound send.
   A subsequent [operator-present inbound check](hardware-validation/2026-10-01-cy-ride-inbound-address-check.md)
   supports TYP CC20 with displayed C/D observed as2/3, and HIT CC19 with
   displayed48–50 observed directly. Manual KIT 01 reload returned C/48.
   No output or SAVE occurred. This resolves the tested live address
   association only; native saved slots, complete selector domains and
   outbound behavior remain unvalidated. The October 5 guard therefore blocks
   **all eight CY Ride SRC rows**, not only Hit/Type, with
   `src_cy_ride_slot_unverified`. It does not swap canonical CCs or offsets.
2. **CB Classic/Metallic:** the same official manual describes two pulse-width
   controls, while its MIDI appendix/current catalog contains only four rows.
   The typed CB Metallic saved recipe includes `PW1/PW2`. Add a saved-only
   inventory entry if needed; do not manufacture CC 20/21 or NRPN addresses.
3. **UT Impulse Polarity:** the official manual describes POS/NEG choices.
   Current catalog metadata falls back to continuous `0..127`, and the word-based
   categorical detector misses this name. A continuous alias must remain blocked
   until actual legal saved and MIDI values are known; a style recipe’s value 64
   is not selector calibration.
4. **SY Chip:** Waveform has mixed waveform choices; Speed combines tempo
   divisions, fixed rates and one-shot modes. Neither has a complete legal
   ordinal table in current metadata. Keep both protected/blocked while deriving
   aliases for other rows. Offset 2–4 are pitch offsets; add explicit tuning
   protection because the current generic name detector does not recognize
   `Offset`. A MIDI address does not prove interpolation semantics.
5. **Dual VCO Osc 2 Detune:** real low-value CC 20 sends previously caused `ERR`.
   The [historical hardware record](hardware-validation/2026-05-29-rytm-live-safe-performance-session.md),
   lines 408–545, later proves only limited center-band movement. The existing
   shell at `analog_rytm_snapshot_shell.py:939` gates pads 2/3 and constrains an
   anchor-relative window within 62..79. Reuse that policy or refuse changed
   values in Forge; do not replace it with the catalog’s full-byte clamp.
6. **Other selectors:** legal facts already exist for Filter Type, LFO Wave,
   LFO Mode, all 24 LFO Multipliers and sparse LFO Destinations in the typed codec.
   Compressor attack/release/ratio/sidechain and FX PRE/POST values already live
   in `data/analog_rytm_kit_fields.py:178`. The matrix’s unproven Ratio,
   Sidechain and routing descriptions can consume these facts while keeping FX
   outside live scope. Sample Loop and Delay Pingpong still need an explicit
   legal-value binding before generic interpolation. Generic Trig and Euclidean
   rows remain outside the OXI-owned sound-mutation scope.

The BT Classic native recipe also contains an unused slot where the manual SRC
catalog names Sweep Depth. This pre-existing disagreement should be checked
before extending *native semantic* authoring, although it is outside the eleven
missing alias families. Existing code/returned bytes do not justify silently
rewriting the manual catalog.

## Precision and recovery gates

- Rytm LFO Depth is the only explicit paired-CC row in this catalog. Changed
  targeted/unlocked values must keep the existing whole-plan refusal; unchanged,
  locked and untargeted paired rows must not block supported single-CC changes.
  Existing native LFO depth helpers describe centered high-resolution words,
  but their documentation explicitly leaves dedicated Rytm +/-1 capture evidence
  pending. That is not an exact CC/NRPN conversion or recovery proof.
- Alias completion proves at most the existing primary-byte CC7 projection.
  It does not prove lossless restoration of unknown low bytes or unsaved RAM.
- The October 1 studio observation proved one bounded 16-message Rytm SEND and
  manual recovery for the checked Filter Frequency, Amp Decay, Overdrive and
  Reverb values, with an untargeted sentinel unchanged. It did not physically
  verify all 16 values, SRC controls, automatic restore, A4/BOTH or Pi hardware.
- Saved KIT dumps preserve saved state. Manual reload, physical checks, a fresh
  matching capture, exact plan preparation, exact output selection and separate
  confirmation remain required; automatic unsaved-state readback/restore is not
  implemented or validated by the alias repair.

## A4: separate evidence layers

The Pi PR #252 matrix at the pinned source contains **112 rows: 58 CC7,
14 paired CC, 33 NRPN-only and 7 native-only controls**. These include the
105 MIDI rows counted separately in the Studio Device Support Inventory.
**98 have saved-field projection; 14 do not.** The latter are Track
Mute/Level, Performance A–J, Modwheel and Breath Controller. Track Level does
already have a typed `A4Kit.track_level()` accessor, so its absence is a matrix
binding limitation rather than unknown storage. Keep sequencing/performance
and OXI AMP ownership protections.

The Pi saved projection retains integer precision for 2 pitch words, 66 U7 fields,
18 bipolar fields, 2 Q8.8 fields, 8 Q8.7 depths and 2 shared FIN components. It
permits offline mutation for 88 of 98 encodings; 8 undocumented boolean-like
domains and 2 independently unsafe FIN components remain immutable. Those eight
are OSC 1/2 Keytracking, OSC 1/2 AM, Note Sync, Oscillator Drift, Legato Mode and
Filter 1 Resonance Boost. Existing native ranges are not verified live ordinals.

Already available evidence:

- [Exact native domains](../rytm_randomizer/data/analog_four_kit_fields.py),
  [Pi catalog-to-field bindings at the pinned source](https://github.com/buzzijose-hub/RytmRandomizer/blob/8cfa6f7b6cf9469ffa134598182febb60ecdd1df/rytm_randomizer/data/appliance_parameter_bindings.py)
  and [Pi offline projection at the pinned source](https://github.com/buzzijose-hub/RytmRandomizer/blob/8cfa6f7b6cf9469ffa134598182febb60ecdd1df/rytm_randomizer/cockpit/capture/appliance_a4.py)
  cover the broad saved-KIT model; do not describe all A4 offsets as unknown.
- [Saved-KIT fixtures](../tests/fixtures/analog_four_saved_kit/README.md) and
  [calibrations](../rytm_randomizer/data/analog_four_sysex_calibration.py), line 453:
  Filter 1 Frequency has exact 0.00/63.50/127.00 capture comparisons, native 1/256
  steps and four-track stride. Its generated scratch fixture remains explicitly
  **pending physical outbound validation**. Filter 1 Resonance and Filter 2
  Frequency have narrower capture-based candidate facts. Filter 2 Resonance has
  operator-confirmed saved-file transfer/return evidence, not general live authority.
- [RIO145 fixtures](../tests/fixtures/rio145) pin oscillator hidden FIN half-steps
  and ENV 2 depth +/-1; do not reuse those as Rytm or live transport calibration.
- [A4 live-dial hardware evidence](hardware-validation/2026-07-17-a4-live-dial-enum-evidence.md)
  records 26 retained routed mappings from a separate legacy DNA rehearsal and
  seven disproved enum interpretations. It is useful real evidence, but does
  not grant captured Forge A4/BOTH output. Six paired rows remained pending in
  that 39-row candidate; the complete Pi matrix has 14 paired rows.

All 112 A4 rows in the pinned Pi matrix remain blocked for captured live send
and restore; general Studio captured Forge A4/BOTH SEND is also blocked. The
existing legacy one-parameter app can send OSC 1 PWM Depth CC 74 after explicit
operator channel/value/output approval, but submitting its output selection
sends immediately; it has no later Cockpit confirmation or captured-plan binding.
It should be used only for the separately supervised bounded probe. Filter 1
Frequency's saved Q8.8 value must not be converted to paired CC 18/50 or NRPN 1:40
by an invented formula. The next general A4 implementation is an evidence-backed
native-to-wire encoder integrated into the existing plan/ArmedApply seams, with
exact order, fractional value, bounds and recovery tests plus controlled hardware
validation. Saved native mappings alone cannot unlock it.

## Verification required for the follow-on closure

The original inventory task ran no tests or hardware actions. Counts were obtained
with the existing inert capability APIs and read-only decoding of already
retained frames. The mapping implementation should extend these existing tests:

- [Catalog tests](../tests/test_analog_rytm_midi_catalog.py) and
  [machine compatibility tests](../tests/test_data_rytm_machine_catalog.py):
  all 33 identities, complete manual rows, no fabricated extra MIDI addresses.
- [Compact-map tests](../tests/cockpit/test_data_rytm_parameter_map.py): preserve
  old keys; all unambiguous missing rows round-trip exact machine/parameter/CC;
  resolve SY Dual VCO label; unknown/excluded fields refuse.
- [Capture-handler tests](../tests/cockpit/test_ws_kit_capture_handlers.py) and
  [snapshot-shell tests](../tests/test_analog_rytm_snapshot_shell.py): use real
  initialized/returned frames, prove SRC survives composed projection, retain
  exact source bytes, omit SY Raw Noise Level and unsafe selectors/transport.
- [Plan tests](../tests/cockpit/test_engine_send_plan.py): target-minus-locks,
  changed paired whole-plan refusal, unsupported-field refusal where retained,
  supported mixed rows and unchanged/locked/untargeted protections.
- [RIO145 fields](../tests/test_devices_strategies_rio145_kit_fields.py) and
  [recipe comparisons](../tests/test_devices_strategies_rio145_kit_recipes.py):
  existing real-byte round trips and no collateral native-byte changes.
- [Pi A4 capability tests at the pinned source](https://github.com/buzzijose-hub/RytmRandomizer/blob/8cfa6f7b6cf9469ffa134598182febb60ecdd1df/tests/cockpit/test_appliance_capabilities.py),
  [Pi projection tests at the pinned source](https://github.com/buzzijose-hub/RytmRandomizer/blob/8cfa6f7b6cf9469ffa134598182febb60ecdd1df/tests/cockpit/test_appliance_a4_projection.py),
  [Studio Filter 1 candidate tests](../tests/test_devices_strategies_analog_four_filter1_frequency_candidate.py)
  and [A4 preparation tests](../tests/cockpit/show_bank/test_a4_preparation.py):
  exact fractions, shared FIN immutability, saved-only evidence and unchanged
  live-authority refusal.

V1.34 byte-frozen fixtures must remain unchanged. Completing projections and
software checks is a useful milestone; road acceptance additionally requires
physical per-control observations, manual recovery, reconnect/restart rehearsal
and actual Pi/touchscreen/offline/full-set validation.

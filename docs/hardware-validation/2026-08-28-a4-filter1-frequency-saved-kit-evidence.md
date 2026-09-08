# Analog Four Filter 1 Frequency Saved-KIT Evidence

Capture date: 2026-08-28

Repository promotion date: 2026-09-04

## Purpose

Record the passive capture evidence that authorizes one narrow capability:
offline generation of Analog Four MKII saved-KIT candidates that change Filter
1 Frequency. This is not hardware-send validation and does not authorize an
A4 transmit path, destination-slot rewrite, persistent save, or any other
saved-KIT field.

## Capture contract

- Device: Elektron Analog Four MKII, observed saved-KIT product/family byte
  `0x06`.
- Disposable initialized KIT: hardware slot 20, native slot byte 19, name
  `KIT 20`.
- Capture mode: input-only current-KIT dump.
- Input port used by the operator capture utility: `Elektron Analog Four MKII 4`.
- Output ports enumerated: no.
- Output ports opened: no.
- Host MIDI messages sent: zero.
- Source evidence record: `A4_FILTER1_FREQUENCY_EVIDENCE.json`, SHA256
  `5df3b7eb57038a33cde26e06d79c3200229612712f154eb0e70b45162bae1de0`.

The unsaved `0.00` control dump was byte-identical to the initialized baseline.
This establishes that this current-KIT dump path reflects the last saved KIT,
not an unsaved front-panel edit. Future operator verification must save the
scratch KIT before requesting the comparison dump.

## Preserved capture fixtures

| Fixture | Display state | SHA256 |
|---|---|---|
| `filter1_freq_127_source.syx` | T1-T4 `127.00` initialized baseline | `3d38dd4369cbd6ea496adcfb7698025cd57e21332ffae1dd5a98e18ae767ea95` |
| `filter1_freq_000_expected.syx` | T1 `0.00`; T2-T4 unchanged | `5c8406010e86d11caeb628935820967d698b739b2d588ae949a807d358c9bde7` |
| `filter1_freq_063_50_expected.syx` | T1 `63.50`; T2-T4 unchanged | `d6710ca7368e59b8ac136081e61282dd538d49cddeaa5f81571dcff972819429` |

Every fixture is a 2,770-byte frame with a 2,755-byte packed body and a
2,410-byte decoded native object. Each capture validates and re-encodes
byte-identically through the canonical A4 saved-KIT codec.

## Verified field mapping

- Encoding: unsigned big-endian Q8.8.
- Physically evidenced values: `0.00` = `00 00`, `63.50` = `3F 80`, and
  `127.00` = `7F 00`.
- Promoted local-candidate range: exactly representable Q8.8 values from
  raw `0x0000` through `0x7F00`, inclusive.
- Track 1 native offsets: `128:130`.
- Track 2 native offsets: `478:480`.
- Track 3 native offsets: `828:830`.
- Track 4 native offsets: `1178:1180`.
- Native track stride: 350 bytes.
- Packed track stride: 400 bytes.
- Full-wire primary integer-byte positions: `157`, `557`, `957`, `1357`.

Relative to the `127.00` baseline, the saved `0.00` capture changes native
offset `128`; its full-wire changes are `157`, `2765`, and `2766`. The saved
`63.50` capture changes native offsets `128` and `129`; its full-wire changes
are `154`, `157`, and `2766`. Packed mask and checksum changes are expected
envelope effects, so isolation is decided on the decoded native object before
canonical repacking.

## Repository capability status

Filter 1 Frequency has status
`offline-captured-kit-mutation-validated`. Its distinctly named renderer:

- accepts only Filter 1 Frequency mutations;
- emits local bytes without file or MIDI I/O;
- validates exact Q8.8 representation and the four-track native stride;
- rebuilds packing, checksum, encoded length, and framing through the canonical
  codec;
- re-decodes the result and reports intended and changed native offsets; and
- always reports `hardware_send_validated = false` and output authority
  `local-file-only`.

The existing Filter 2 Resonance hardware-validated writer remains separate.
Filter 1 Resonance, Filter 2 Frequency, Amp Attack, and all other unsupported
A4 fields remain blocked. The snapshot-wide `offsets_promoted` flag remains
false, and Cockpit A4 SEND remains unavailable.

## Pending generated scratch validation

The repository includes the deterministic local candidate
`filter1_freq_tracks_16_25_48_50_80_75_112_25_pending.syx`:

| Track | Display value | Raw Q8.8 | Native offsets |
|---:|---:|---:|---|
| 1 | `16.25` | `0x1040` | `128, 129` |
| 2 | `48.50` | `0x3080` | `478, 479` |
| 3 | `80.75` | `0x50C0` | `828, 829` |
| 4 | `112.25` | `0x7040` | `1178, 1179` |

- Source SHA256: `3d38dd4369cbd6ea496adcfb7698025cd57e21332ffae1dd5a98e18ae767ea95`.
- Generated SHA256: `829eee0209a248012a968e96df33acd007619a0078255c4fd034b5afda3520dd`.
- Source checksum: 9577.
- Generated checksum: 9533.
- Encoded length: 2760.
- Native changed offsets: `128, 129, 478, 479, 828, 829, 1178, 1179`.
- Status: `pending_physical_outbound_validation`.
- Recorded physical observations: none.

The executable JSON handoff is
`tests/fixtures/analog_four_saved_kit/filter1_frequency_pending_scratch_validation.json`.

## Operator procedure for the pending artifact

1. Manually load the generated file into a disposable A4 scratch slot.
2. Confirm the four Filter 1 Frequency values on the front panel and audition
   the result.
3. Save the KIT on the instrument.
4. Request an input-only current-KIT dump.
5. Compare the returned fingerprint and decoded values with the manifest.
6. Record an observation only after that comparison; do not infer success from
   successful file transfer alone.

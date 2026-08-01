---
name: elektron-sysex-envelope
description: Elektron SysEx and generated-patch transport reference covering canonical 7-bit packing, hardware-validated A4 saved-kit framing, content-addressed batch publication, full-plan validation, pacing, and partial-send recovery.
user-invocable: false
origin: auto-extracted-2026-05-18
---

# Elektron SysEx envelope: 7-bit packing + kit-record layout

**Extracted:** 2026-05-18
**Context:** WS-S6 introduced `rytm_randomizer/snapshot/envelope.py` as the canonical generic-Elektron decoder, lifted out of `rytm-rs` / `libanalogrytm` reference material and PR #21's planned Analog Four work. This skill captures the format for any future device (Analog Four, Digitakt, Digitone, Syntakt) so we don't re-derive it.

## The envelope shape

```
F0 00 20 3C <product_id> <device_id> <message_id> <payload...> <checksum> F7
```

| Byte(s) | Meaning |
|---|---|
| `F0` | SysEx start (universal MIDI) |
| `00 20 3C` | Elektron manufacturer ID. `Final[bytes]` in `snapshot/envelope.py` as `ELEKTRON_MFR_ID`. |
| `<product_id>` (1 byte) | Identifies the device family (e.g. `0x07` Analog Four MKI, `0x0C` Analog Rytm MKII, `0x10` Digitakt). |
| `<device_id>` (1 byte) | Per-device identifier; usually `0x00`. |
| `<message_id>` (1 byte) | Message kind (kit dump, pattern dump, settings, etc.). |
| `<payload...>` | 7-bit-encoded data. See "7-bit packing" below. |
| `<checksum>` (2 bytes) | Sum-of-payload modulo `0x4000`, split into two 7-bit bytes. |
| `F7` | SysEx end. |

### Verified saved-kit variants in this repository

Do not apply one generic header/checksum formula to every Elektron family.
Approved exact-target-unit saved-kit exports currently prove these two
container variants:

| Device/export | Header after `F0` | Decoded object | Checksum | Stored length |
|---|---|---:|---|---|
| Analog Rytm MKII saved kit | `00 20 3C 07 00 52 01 01 <slot>` | 2610 bytes | `sum(packed) & 0x3fff` | `len(packed) + 5` |
| Analog Four MKII saved kit | `00 20 3C 06` | 2415 bytes, beginning with object byte `0x52` | `sum(packed[8:]) & 0x3fff` | `len(packed)` |

The A4 and Rytm bytes `0x06`/`0x07` above are observed saved-kit family bytes.
They are not interchangeable with product/device IDs from other Elektron
message families. Use the device-configured `ElektronKitCodec` instances and
approved reference frames; do not choose a header from the generic product-ID
table below.

## 7-bit packing (the only non-obvious part)

MIDI SysEx payload bytes must all have their high bit clear (top bit reserved as a SysEx-status marker). Elektron's packing turns 8 source bytes into 8 SysEx bytes by:

1. Stripping the high bit from each of 7 consecutive source bytes.
2. Packing those 7 stripped high-bits into a single leading byte (bit 0 = first source byte's MSB, bit 1 = second, ...).
3. The 7 low-7-bit bodies follow.

Result: every 8 SysEx bytes encode 7 source bytes. The canonical inverses are
`pack_elektron_7bit(unpacked: bytes) -> bytes` and
`unpack_elektron_7bit(packed: bytes) -> bytes` in `snapshot/envelope.py`.

```python
# Reference unpack (Python). The canonical implementation lives in
# rytm_randomizer/snapshot/envelope.py:unpack_elektron_7bit and raises
# ValueError on malformed input.

def unpack_elektron_7bit(packed: bytes) -> bytes:
    out = bytearray()
    for chunk_start in range(0, len(packed), 8):
        chunk = packed[chunk_start:chunk_start + 8]
        if not chunk:
            break
        high_bits = chunk[0]
        for i, low7 in enumerate(chunk[1:]):
            byte = low7 | (((high_bits >> i) & 0x01) << 7)
            out.append(byte)
    return bytes(out)
```

## Kit-record layout

A kit dump's payload (after 7-bit unpacking) typically starts with:

| Offset | Bytes | Meaning |
|---|---|---|
| 0..1 | 2 | Record magic / version |
| 2..17 | 16 | ASCII kit name (NUL-padded, max 15 visible chars + NUL) |
| 18+ | varies | Per-track parameter blocks (track count is device-specific) |

`find_kit_record(payload: bytes) -> int` (in `snapshot/envelope.py`) returns the offset of the first kit record in a multi-record dump; `read_ascii_name(payload: bytes, offset: int) -> str` reads and strips the 16-byte name field.

## Per-device product IDs (the ones we care about today)

| Device | Product ID byte |
|---|---|
| Analog Four MKI | `0x07` |
| Analog Four MKII | `0x0A` in the generic product-ID catalog; do not apply this blindly to saved-kit frames |
| Analog Rytm MKI | `0x08` |
| Analog Rytm MKII | `0x0C` |
| Digitakt | `0x10` |
| Digitone | `0x11` |
| Syntakt | `0x14` |

Add new devices by registering with `rytm_randomizer.devices.registry.register_device(...)` and providing the product-ID-matched `decode_snapshot` implementation.

## Hardware-validated Analog Four MKII saved-kit frame

The observed A4 MKII saved-kit export is a device-specific exception to the
generic field sketch above:

```
F0 00 20 3C 06 <2760 packed bytes> <checksum_hi> <checksum_lo> <length_hi> <length_lo> F7
```

- `0x06` is the observed saved-kit family prefix after the manufacturer ID.
  Treat it as a saved-kit wire fact, not as a replacement for every A4 product
  ID in other message families.
- The unpacked body is 2,415 bytes and starts with saved-kit object byte `0x52`.
- The packed body is 2,760 bytes.
- Checksum is `sum(packed[8:]) & 0x3FFF`, encoded high-seven bits then
  low-seven bits. The first eight packed bytes are excluded.
- The final two trailer bytes encode packed length `2760` as a 14-bit value.
- The complete framed file is 2,770 bytes.
- Canonical frame/layout constants live in
  `data/analog_four_saved_kit_layout.py`; shared encode/decode validation lives
  in `devices/strategies/analog_four_saved_kit_codec.py`.

Do not infer a writable parameter from one changed capture. Promote a field
only after three passes: an exact reference-value reconstruction, a novel
uncaptured value, and independent cross-track values proving the track stride.
Store disposable sanitized source/expected frames as executable binary fixtures
so byte identity is tested rather than described only in prose.

## Generated patch batches and live-plan delivery

A complete audio-derived patch is a content-addressed artifact set, not a loose
group of JSON and SysEx files:

1. Snapshot the source audio and initialized kit before inference.
2. Use the audio SHA-256 as the generated plan's `source_hash`; keep the
   feature-report hash as a separate manifest field.
3. Include the audio, source kit, inference model, DNA, send plan, renderer,
   and filenames in the generation identity.
4. Publish immutable generation files first and atomically replace the stable
   manifest last. The manifest is the commit marker.
5. On read, verify outer hashes, nested DNA/send-plan hashes, source identity,
   coverage counts, event order, and every CC/NRPN address against canonical
   device data before opening a MIDI port.
6. For an armed replay, require the operator to supply the SHA-256 printed by
   the reviewed dry-run through a separate command-line value. Verify that
   out-of-band digest before constructing the MIDI provider. Internal manifest
   hashes protect artifact consistency, but they do not prove that a fully
   rehashed replacement is the batch the operator reviewed.
7. Revalidate every stored event against the current transport policy before
   provider construction. A verified CC/NRPN address does not verify an enum
   value's meaning. Enum ordinals require independent physical calibration;
   when a rehearsal disproves one, remove its semantic label, fail it closed,
   and reject older internally valid manifests that still carry it.

For a live plan, prevalidate the whole event sequence and expected wire-message
count before port discovery. Use the named `MIDI_MESSAGE_SETTLE_SECONDS` policy
after every accepted CC. NRPN progress is counted per CC99/CC98/CC6 (and CC38
when present), so a failure reports the exact partial position. The delivery
callback must run only after `out.send()` returns. Wrap catchable send failure
and Ctrl+C in a taxonomy-backed error carrying sent/expected counts, close the
port, tell the operator to reload the last saved Kit/project, and use exit code
130 for interruption.

Successful transport of a partial plan is not semantic verification. Completion
telemetry must retain the sendable/manual counts, a bounded complete/partial
status, and an explicit hardware-verification-required marker.

Complete DNA does not imply complete saved-kit SysEx write coverage. Keep
unproven saved-kit fields deferred while sending manual-backed CC/NRPN rows
through the separately guarded live path.

## When to Use

Trigger conditions:

- Adding a new Elektron device implementation under `rytm_randomizer/devices/`.
- Debugging a SysEx capture where bytes look like ASCII text but are off by one bit position (classic 7-bit-packing oversight).
- Reviewing any change that hand-rolls pack/unpack helpers — point it at the
  canonical `snapshot.envelope` pair instead.
- Promoting an A4 saved-kit field from captured offsets to writable output.
- Publishing or replaying an audio-derived Elektron patch batch.
- Binding an armed replay to an operator-reviewed manifest digest.
- Reviewing live CC/NRPN delivery pacing, accounting, or recovery behavior.

DO NOT use this pattern when:

- The device is non-Elektron (manufacturer ID won't be `00 20 3C`).
- The payload is a raw stream (not a kit/pattern/settings record) — the kit-record layout doesn't apply.

## Cross-references

- `rytm_randomizer/snapshot/envelope.py` — the canonical implementation. Always import from there.
- `rytm_randomizer/data/analog_four_saved_kit_layout.py` — canonical observed A4 saved-kit frame facts.
- `rytm_randomizer/devices/strategies/analog_four_saved_kit_codec.py` — shared A4 saved-kit validator/encoder used by decoder and writer.
- `rytm_randomizer/cockpit/export/analog_four_patch_batch_publication.py` - manifest-last, immutable generation publication.
- `rytm_randomizer/cockpit/export/analog_four_patch_batch_reader.py` - hash and canonical-transport verification before replay.
- `rytm_randomizer/senders/midi_event_plan.py` - prevalidated CC/NRPN delivery and partial progress accounting.
- `docs/hardware-validation/2026-07-16-a4-saved-kit-roundtrip-results.md` — reference, novel-value, and four-track evidence pattern.
- `rytm_randomizer/devices/base.py` — the `Device` Protocol every Elektron device implements.
- PR #21 (codex's Analog Four work) — first downstream consumer.
- External: `rytm-rs` and `libanalogrytm` — reference C/Rust implementations of the same format.

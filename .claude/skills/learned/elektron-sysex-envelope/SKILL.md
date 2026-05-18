---
name: elektron-sysex-envelope
description: Elektron device SysEx envelope reference — 3-byte manufacturer ID `00 20 3C`, 7-bit-encoded payload (8 source bytes packed as 1 high-bit byte + 7 low-7-bit bytes), kit-record layout shared across Analog Rytm / Analog Four / Digitakt / Digitone.
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

## 7-bit packing (the only non-obvious part)

MIDI SysEx payload bytes must all have their high bit clear (top bit reserved as a SysEx-status marker). Elektron's packing turns 8 source bytes into 8 SysEx bytes by:

1. Stripping the high bit from each of 7 consecutive source bytes.
2. Packing those 7 stripped high-bits into a single leading byte (bit 0 = first source byte's MSB, bit 1 = second, ...).
3. The 7 low-7-bit bodies follow.

Result: every 8 SysEx bytes encode 7 source bytes. Inverse: `unpack_elektron_7bit(sysex: bytes) -> bytes` (in `snapshot/envelope.py`).

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
| Analog Four MKII | `0x0A` |
| Analog Rytm MKI | `0x08` |
| Analog Rytm MKII | `0x0C` |
| Digitakt | `0x10` |
| Digitone | `0x11` |
| Syntakt | `0x14` |

Add new devices by registering with `rytm_randomizer.devices.registry.register(...)` and providing the product-ID-matched `decode_snapshot` implementation.

## When to Use

Trigger conditions:

- Adding a new Elektron device implementation under `rytm_randomizer/devices/`.
- Debugging a SysEx capture where bytes look like ASCII text but are off by one bit position (classic 7-bit-packing oversight).
- Reviewing PR #21 (or any successor) that ships a hand-rolled `_unpack_elektron_7bit` — point them at `snapshot.envelope.unpack_elektron_7bit` instead.

DO NOT use this pattern when:

- The device is non-Elektron (manufacturer ID won't be `00 20 3C`).
- The payload is a raw stream (not a kit/pattern/settings record) — the kit-record layout doesn't apply.

## Cross-references

- `rytm_randomizer/snapshot/envelope.py` — the canonical implementation. Always import from there.
- `rytm_randomizer/devices/base.py` — the `Device` Protocol every Elektron device implements.
- PR #21 (codex's Analog Four work) — first downstream consumer.
- External: `rytm-rs` and `libanalogrytm` — reference C/Rust implementations of the same format.

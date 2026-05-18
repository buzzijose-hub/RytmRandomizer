"""Generic Elektron SysEx envelope helpers (WS-S6).

This module is the shared base for every Elektron-device snapshot decoder
that lands in the project (Analog Rytm today; Analog Four, Digitakt,
Digitone, Syntakt, etc. tomorrow). The helpers here are deliberately
device-agnostic — they read the manufacturer-id envelope, unpack the
"every 8 bytes is 7 7-bit data bytes preceded by an MSB header" payload
encoding Elektron's MIDI implementation uses, and surface kit/sound
record bytes for the per-device decoder to interpret.

PR #21 (codex's Analog Four bridge) currently duplicates these helpers
between Rytm and Analog Four. Landing them here once means PR #21's
Analog Four module collapses from 8 files (decoder, planner, mock
runtime, envelope, kit-record reader, ascii-name reader, manufacturer-id
formatter, registration shim) down to 1 (just the device-specific
machinery on top of these generic helpers).

The functions are pure: no I/O, no logging, no module state. They take
``bytes`` in and return ``bytes`` / ``str``, raising :class:`ValueError`
on malformed input so callers can surface a clean error to the operator.

The 7-bit packing scheme matches what Elektron documents in the Analog
Rytm MK2 MIDI Implementation appendix: every 8 bytes of wire format
expand to 7 bytes of payload — the first byte of each 8-byte group
carries the high bit (bit-7) of the following 7 bytes, in order. The
last group may be short; in that case the header still carries the high
bits of the bytes actually present.

Per Gate 6 (PLAN_REQUIREMENTS) the helpers' signatures are concrete
(``bytes``/``str``/``int``); no ``Any`` escape hatches. Per Gate 12 the
manufacturer-id constant is annotated ``Final``.
"""

from __future__ import annotations

from typing import Final

#: Elektron's IEEE-registered 3-byte SysEx manufacturer ID. Documented in
#: every Elektron device MIDI implementation appendix. NOT secret -- this
#: is the same value any sniffer on the MIDI cable will see in every
#: SysEx packet the Rytm / Analog Four / Digitakt sends or receives.
ELEKTRON_MFR_ID: Final[bytes] = bytes([0x00, 0x20, 0x3C])


def unpack_elektron_7bit(packed: bytes) -> bytes:
    """Unpack an Elektron 7-bit-stuffed payload into a flat byte string.

    Elektron's SysEx payload uses the standard MIDI "MSB header" 7-bit
    encoding: every group of up to 8 wire bytes is (1 header byte) +
    (up to 7 data bytes). Each of the 7 low bits of the header byte
    carries the high bit (bit-7) for the corresponding data byte, in
    order. The data bytes themselves are guaranteed by MIDI rules to be
    7-bit (high bit clear); the header reinjects the bit-7 to produce
    the original 8-bit payload byte.

    Empty input returns empty output. A trailing group shorter than 8
    bytes is permitted; only the bits in the header that correspond to
    bytes actually present are consumed.

    Raises :class:`ValueError` if ``packed`` is None or any byte exceeds
    ``0x7F`` (which would mean the upstream wasn't a valid 7-bit MIDI
    payload to begin with — caller should re-check the envelope).
    """

    if packed is None:  # type: ignore[unreachable]
        raise ValueError("unpack_elektron_7bit: packed payload is None")
    for index, byte in enumerate(packed):
        if byte > 0x7F:
            raise ValueError(
                f"unpack_elektron_7bit: byte at offset {index} is 0x{byte:02x}, "
                "which is outside the 7-bit MIDI data range (0x00-0x7f). "
                "Re-check the SysEx envelope before unpacking."
            )

    out = bytearray()
    cursor = 0
    length = len(packed)
    while cursor < length:
        header = packed[cursor]
        cursor += 1
        # A group is up to 7 data bytes; trailing groups may be shorter.
        group_end = min(cursor + 7, length)
        # Reject any lone trailing header byte (a buffer with length % 8 == 1),
        # whether or not the header is zero. A header with no following data
        # bytes is meaningless framing; real Elektron firmware does not emit
        # one, so surfacing the error tells the caller their upstream is
        # corrupted rather than handing back a quietly-truncated payload.
        # (Codex review P2: the earlier ``header != 0`` carve-out treated a
        # lone ``b"\x00"`` as harmless padding -- the spec says it is not.)
        if cursor == length and cursor == group_end:
            raise ValueError(
                f"unpack_elektron_7bit: trailing group at offset "
                f"{cursor - 1} has a header byte (0x{header:02x}) "
                "but no data bytes; this is malformed input -- check "
                "the SysEx envelope framing before unpacking."
            )
        for bit_index, data_index in enumerate(range(cursor, group_end)):
            high_bit = (header >> bit_index) & 0x01
            out.append((high_bit << 7) | packed[data_index])
        cursor = group_end
    return bytes(out)


def find_kit_record(raw: bytes, slot: int, kit_type_byte: int) -> bytes:
    """Locate the kit/sound record for ``slot`` inside a raw SysEx dump.

    Stub for WS-S6: the per-device decoders (PR #21) supply the actual
    offset-and-length table per Elektron machine. This helper exists so
    every device implementation can call ``find_kit_record(raw, slot,
    kit_type_byte)`` and the contract is centralized in one place.

    Today the implementation returns a single record by scanning for the
    Elektron manufacturer-id prefix and returning the contiguous payload
    that follows the type byte; this is the correct shape for the kit /
    pattern dumps the Rytm and Analog Four emit, but per-device offset
    tables override this in their wrapper.

    Raises:
        ValueError: if ``raw`` does not start with the Elektron
            manufacturer ID, if ``slot`` is negative, or if the requested
            ``kit_type_byte`` is not present in the payload.
    """

    if raw is None:  # type: ignore[unreachable]
        raise ValueError("find_kit_record: raw payload is None")
    if slot < 0:
        raise ValueError(f"find_kit_record: slot must be non-negative, got {slot}")
    if not (0 <= kit_type_byte <= 0xFF):
        raise ValueError(
            f"find_kit_record: kit_type_byte must be in 0x00-0xff, got 0x{kit_type_byte:x}"
        )
    if not raw.startswith(ELEKTRON_MFR_ID):
        raise ValueError(
            "find_kit_record: raw payload does not start with Elektron "
            f"manufacturer id 0x{ELEKTRON_MFR_ID.hex()} -- got "
            f"0x{raw[: len(ELEKTRON_MFR_ID)].hex()!r}. Strip the SysEx "
            "F0/F7 framing bytes before passing to find_kit_record."
        )

    # Per-device decoders will replace this scan with an offset table.
    # The scan locates the *first* occurrence of ``kit_type_byte`` after
    # the manufacturer-id prefix; a real decoder uses ``slot`` to pick
    # the N-th occurrence or a fixed offset.
    #
    # Security-review LOW finding: ``slot`` is intentionally unused in
    # this stub. Per-device decoders supply the correct offset table.
    # Reject ``slot > 0`` here so a caller cannot silently receive the
    # wrong kit; force the caller to either pass slot=0 (first
    # occurrence) or wait for per-device decoders to land.
    if slot > 0:
        raise NotImplementedError(
            f"find_kit_record: slot-indexed lookup not yet implemented "
            f"(requested slot={slot}). The per-device decoders supply "
            "an offset table; until they land (PR #21 onward), only "
            "slot=0 (first occurrence) is supported."
        )
    payload_start = len(ELEKTRON_MFR_ID)
    try:
        type_pos = raw.index(kit_type_byte, payload_start)
    except ValueError as exc:
        raise ValueError(
            f"find_kit_record: kit_type_byte 0x{kit_type_byte:02x} not "
            "present in payload after manufacturer-id prefix"
        ) from exc
    return raw[type_pos:]


def read_ascii_name(record: bytes, offset: int, length: int) -> str:
    """Read a fixed-width ASCII name field, stripping trailing NULs.

    Elektron kit / pattern names are stored as fixed-length, NUL-padded
    ASCII fields (typically 16 bytes for kit names, 16 for pattern names,
    4 for track tags). This helper extracts a slice and strips the
    trailing NUL padding so the operator-facing string is clean.

    The returned string is decoded as ``ascii`` with ``errors="replace"``
    — invalid bytes become ``"?"`` rather than raising, because a
    corrupted name field should not crash the whole snapshot decode.

    Raises:
        ValueError: if ``offset`` or ``length`` is negative, or if
            ``offset + length`` extends past ``len(record)``.
    """

    if record is None:  # type: ignore[unreachable]
        raise ValueError("read_ascii_name: record is None")
    if offset < 0:
        raise ValueError(f"read_ascii_name: offset must be non-negative, got {offset}")
    if length < 0:
        raise ValueError(f"read_ascii_name: length must be non-negative, got {length}")
    end = offset + length
    if end > len(record):
        raise ValueError(
            f"read_ascii_name: slice {offset}:{end} extends past record " f"length {len(record)}"
        )

    raw_slice = record[offset:end]
    # Strip trailing NULs (Elektron's padding convention).
    return raw_slice.rstrip(b"\x00").decode("ascii", errors="replace")


def format_manufacturer_id(raw: bytes) -> str:
    """Render a manufacturer-id byte sequence as a colon-delimited hex string.

    Used for human-readable error messages and trace logs. The Elektron
    manufacturer ID renders as ``"00:20:3C"``; a Roland-3-byte renders as
    ``"00:00:0E"``; a single-byte legacy ID renders as ``"41"`` (Roland
    short form) or ``"43"`` (Yamaha short form).

    Empty input returns the empty string.

    Raises:
        ValueError: if ``raw`` is None.
    """

    if raw is None:  # type: ignore[unreachable]
        raise ValueError("format_manufacturer_id: raw is None")
    return ":".join(f"{byte:02X}" for byte in raw)

"""Passive Analog Four MKII saved-kit snapshot decoder.

This module reads already-available bytes only. It does not import MIDI
libraries, open ports, request dumps, receive live SysEx, send messages, or
write SysEx data.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .observability.errors import DataError

A4_DEVICE_FAMILY = 0x06
KIT_OBJECT_TYPE = 0x52
KIT_HEADER_LENGTH = 10
SLOT_INDEX_OFFSET = 9
KIT_NAME_OFFSET = 4
KIT_NAME_LENGTH = 16
TRACK_BLOCK_OFFSETS = (44, 394, 744, 1094)
TRACK_BLOCK_LENGTH = 350
TRACK_NAME_LENGTH = 16
TRACK_COUNT = 4
UNMAPPED_STATUS = "saved_parameter_offsets_unmapped"


class AnalogFourSnapshotDecodeError(DataError, ValueError):
    """Raised when bytes cannot be decoded as a passive Analog Four kit snapshot."""


@dataclass(frozen=True)
class AnalogFourTrackSnapshot:
    """One visible Analog Four saved-kit track block."""

    track: int
    midi_channel: int
    wire_channel: int
    name: str
    block_offset: int
    block_length: int
    sha256_12: str
    mapping_status: str


@dataclass(frozen=True)
class AnalogFourKitSnapshot:
    """Passive inventory for one saved Analog Four kit record."""

    source_path: str | None
    slot_number: int
    kit_name: str
    record_length: int
    decoded_payload_length: int
    manufacturer_id: str
    device_family_byte: int
    object_type: int
    sha256_12: str
    tracks: tuple[AnalogFourTrackSnapshot, ...]


def decode_analog_four_kit_snapshot_file(
    path: str | Path,
    *,
    slot: int,
) -> AnalogFourKitSnapshot:
    """Decode one saved Analog Four kit slot from an existing SysEx file."""

    snapshot = decode_analog_four_kit_snapshot_bytes(Path(path).read_bytes(), slot=slot)
    return AnalogFourKitSnapshot(
        source_path=str(path),
        slot_number=snapshot.slot_number,
        kit_name=snapshot.kit_name,
        record_length=snapshot.record_length,
        decoded_payload_length=snapshot.decoded_payload_length,
        manufacturer_id=snapshot.manufacturer_id,
        device_family_byte=snapshot.device_family_byte,
        object_type=snapshot.object_type,
        sha256_12=snapshot.sha256_12,
        tracks=snapshot.tracks,
    )


def decode_analog_four_kit_snapshot_bytes(data: bytes, *, slot: int) -> AnalogFourKitSnapshot:
    """Decode one saved Analog Four kit slot from raw SysEx bytes."""

    if slot not in range(1, 129):
        raise AnalogFourSnapshotDecodeError("slot must be 1-128")

    record = _find_kit_record(data, slot=slot)
    _validate_a4_kit_record(record)
    payload = _unpack_elektron_7bit(record[KIT_HEADER_LENGTH:-1])
    if len(payload) < TRACK_BLOCK_OFFSETS[-1] + TRACK_BLOCK_LENGTH:
        raise AnalogFourSnapshotDecodeError(
            "Analog Four kit record is too short for four track blocks"
        )

    return AnalogFourKitSnapshot(
        source_path=None,
        slot_number=slot,
        kit_name=_read_ascii_name(payload, KIT_NAME_OFFSET, KIT_NAME_LENGTH),
        record_length=len(record),
        decoded_payload_length=len(payload),
        manufacturer_id=_format_manufacturer_id(record),
        device_family_byte=record[4],
        object_type=record[6],
        sha256_12=sha256(record).hexdigest().upper()[:12],
        tracks=_decode_tracks(payload),
    )


def format_analog_four_kit_snapshot_report(snapshot: AnalogFourKitSnapshot) -> list[str]:
    """Format a deterministic passive Analog Four kit snapshot report."""

    lines = [
        "RytmRandomizer passive Analog Four kit snapshot report",
        f"Source path: {snapshot.source_path or '<bytes>'}",
        f"Slot: {snapshot.slot_number}",
        f"Kit: {snapshot.kit_name or '<blank>'}",
        f"Record length: {snapshot.record_length}",
        f"Decoded payload length: {snapshot.decoded_payload_length}",
        f"Manufacturer ID: {snapshot.manufacturer_id}",
        f"Device family byte: {snapshot.device_family_byte:02X}",
        f"Object type: {snapshot.object_type:02X}",
        f"Record hash: {snapshot.sha256_12}",
        "Track snapshots:",
    ]
    for track in snapshot.tracks:
        lines.append(
            f"- Track {track.track} / MIDI channel {track.midi_channel} / "
            f"wire channel {track.wire_channel} / offset {track.block_offset}: "
            f"{track.name or '<blank>'} / {track.block_length} bytes / "
            f"{track.sha256_12} / {track.mapping_status}"
        )
    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_analog_four_kit_snapshot_error(path: str | Path, message: str) -> list[str]:
    """Format deterministic passive Analog Four snapshot error lines."""

    return [
        "RytmRandomizer passive Analog Four kit snapshot report",
        f"Path: {path}",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _find_kit_record(data: bytes, *, slot: int) -> bytes:
    wanted_slot_index = slot - 1
    for record in _split_complete_sysex_messages(data):
        if len(record) <= SLOT_INDEX_OFFSET:
            continue
        if record[6] == KIT_OBJECT_TYPE and record[SLOT_INDEX_OFFSET] == wanted_slot_index:
            return record
    raise AnalogFourSnapshotDecodeError(f"Analog Four kit slot {slot} not found")


def _split_complete_sysex_messages(data: bytes) -> tuple[bytes, ...]:
    messages: list[bytes] = []
    cursor = 0
    while True:
        start = data.find(bytes([0xF0]), cursor)
        if start == -1:
            break
        end = data.find(bytes([0xF7]), start + 1)
        if end == -1:
            break
        messages.append(data[start : end + 1])
        cursor = end + 1
    if not messages:
        raise AnalogFourSnapshotDecodeError("no complete SysEx messages found")
    return tuple(messages)


def _validate_a4_kit_record(record: bytes) -> None:
    if (
        len(record) <= KIT_HEADER_LENGTH
        or record[0] != 0xF0
        or record[-1] != 0xF7
        or record[4] != A4_DEVICE_FAMILY
        or record[6] != KIT_OBJECT_TYPE
    ):
        raise AnalogFourSnapshotDecodeError("not an Analog Four kit record")


def _unpack_elektron_7bit(packed: bytes) -> bytes:
    decoded = bytearray()
    for index in range(0, len(packed), 8):
        group = packed[index : index + 8]
        if not group:
            continue
        mask = group[0]
        for bit, value in enumerate(group[1:]):
            decoded.append(value | (0x80 if mask & (1 << bit) else 0))
    return bytes(decoded)


def _decode_tracks(payload: bytes) -> tuple[AnalogFourTrackSnapshot, ...]:
    tracks = []
    for track, offset in enumerate(TRACK_BLOCK_OFFSETS, start=1):
        block = payload[offset : offset + TRACK_BLOCK_LENGTH]
        tracks.append(
            AnalogFourTrackSnapshot(
                track=track,
                midi_channel=track,
                wire_channel=track - 1,
                name=_read_ascii_name(payload, offset, TRACK_NAME_LENGTH),
                block_offset=offset,
                block_length=len(block),
                sha256_12=sha256(block).hexdigest().upper()[:12],
                mapping_status=UNMAPPED_STATUS,
            )
        )
    return tuple(tracks)


def _read_ascii_name(payload: bytes, offset: int, length: int) -> str:
    raw = payload[offset : offset + length]
    chars = []
    for value in raw:
        if value == 0:
            break
        if 32 <= value <= 126:
            chars.append(chr(value))
    return "".join(chars).strip()


def _format_manufacturer_id(message: bytes) -> str:
    if len(message) < 4:
        return "<unknown>"
    return " ".join(f"{byte:02X}" for byte in message[1:4])


__all__ = [
    "AnalogFourKitSnapshot",
    "AnalogFourSnapshotDecodeError",
    "AnalogFourTrackSnapshot",
    "decode_analog_four_kit_snapshot_bytes",
    "decode_analog_four_kit_snapshot_file",
    "format_analog_four_kit_snapshot_error",
    "format_analog_four_kit_snapshot_report",
]

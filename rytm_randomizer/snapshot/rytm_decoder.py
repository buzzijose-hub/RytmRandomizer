"""Passive Rytm SysEx kit snapshot decoder.

This module reads already-available bytes only. It does not import MIDI
libraries, open ports, request dumps, receive live SysEx, send messages, or
write SysEx data.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from ..data import param_maps
from ..observability.errors import DataError

RYTM_DEVICE_FAMILY = 0x07
KIT_OBJECT_TYPE = 0x52
KIT_HEADER_LENGTH = 10
KIT_NAME_OFFSET = 4
KIT_NAME_LENGTH = 16
TRACK_BLOCK_START = 46
TRACK_BLOCK_NAME_OFFSET = 0x0C
TRACK_MACHINE_OFFSET = 0x7C
SOUND_BLOCK_START = 58
SOUND_BLOCK_LENGTH = 162
PAD_COUNT = 12

# Saved sound struct offsets follow the public libanalogrytm ar_sound_t layout.
RYTM_MACHINE_LABELS = {
    0: "BD Hard",
    1: "BD Classic",
    2: "SD Hard",
    3: "SD Classic",
    4: "RS Hard",
    5: "RS Classic",
    6: "CP Classic",
    7: "BT Classic",
    8: "XT Classic",
    9: "CH Classic",
    10: "OH Classic",
    11: "CY Classic",
    12: "CB Classic",
    13: "BD FM",
    14: "SD FM",
    15: "UT Noise",
    16: "UT Impulse",
    17: "CH Metallic",
    18: "OH Metallic",
    19: "CY Metallic",
    20: "CB Metallic",
    21: "BD Plastic",
    22: "BD Silky",
    23: "SD Natural",
    24: "HH Basic",
    25: "CY Ride",
    26: "BD Sharp",
    27: "Disabled",
    28: "SY Dual VCO",
    29: "SY Chip",
    30: "BD Acoustic",
    31: "SD Acoustic",
    32: "SY Raw",
    33: "HH Lab",
}

SAVED_CC_OFFSETS = {
    10: 0x58,
    16: 0x1C,
    17: 0x1E,
    18: 0x20,
    19: 0x22,
    20: 0x24,
    21: 0x26,
    22: 0x28,
    23: 0x2A,
    70: 0x3C,
    71: 0x40,
    72: 0x3E,
    73: 0x42,
    74: 0x44,
    75: 0x46,
    76: 0x48,
    77: 0x4A,
    78: 0x4C,
    79: 0x4E,
    80: 0x50,
    81: 0x52,
    82: 0x54,
    83: 0x56,
    102: 0x5E,
    103: 0x60,
    104: 0x62,
    105: 0x64,
    106: 0x66,
    107: 0x68,
    108: 0x6A,
    109: 0x6C,
}

KNOWN_MACHINE_PARAMETER_MAPS = {
    0: (param_maps.BD_HARD_PARAMS, param_maps.BD_HARD_ORDER),
    1: (param_maps.BD_CLASSIC_PARAMS, param_maps.BD_CLASSIC_ORDER),
    2: (param_maps.SD_HARD_PARAMS, param_maps.SD_HARD_ORDER),
    3: (param_maps.SD_CLASSIC_PARAMS, param_maps.SD_CLASSIC_ORDER),
    13: (param_maps.BD_FM_PARAMS, param_maps.BD_FM_ORDER),
    14: (param_maps.SD_FM_PARAMS, param_maps.SD_FM_ORDER),
    21: (param_maps.BD_PLASTIC_PARAMS, param_maps.BD_PLASTIC_ORDER),
    22: (param_maps.BD_SILKY_PARAMS, param_maps.BD_SILKY_ORDER),
    26: (param_maps.BD_SHARP_PARAMS, param_maps.BD_SHARP_ORDER),
    30: (param_maps.BD_ACOUSTIC_PARAMS, param_maps.BD_ACOUSTIC_ORDER),
    32: (param_maps.SY_RAW_PARAMS, param_maps.SY_RAW_ORDER),
}

GENERIC_SAVED_PARAMETER_ORDER = (
    ("SRC Slot 1", 16),
    ("SRC Slot 2", 17),
    ("SRC Slot 3", 18),
    ("SRC Slot 4", 19),
    ("SRC Slot 5", 20),
    ("SRC Slot 6", 21),
    ("SRC Slot 7", 22),
    ("SRC Slot 8", 23),
    ("FLT Attack", 70),
    ("FLT Decay", 71),
    ("FLT Sustain", 72),
    ("FLT Release", 73),
    ("FLT Frequency", 74),
    ("FLT Resonance", 75),
    ("FLT Type", 76),
    ("FLT Env Depth", 77),
    ("AMP Attack", 78),
    ("AMP Hold", 79),
    ("AMP Decay", 80),
    ("AMP Overdrive", 81),
    ("AMP Delay Send", 82),
    ("AMP Reverb Send", 83),
    ("AMP Pan", 10),
    ("LFO Speed", 102),
    ("LFO Multiplier", 103),
    ("LFO Fade", 104),
    ("LFO Destination", 105),
    ("LFO Waveform", 106),
    ("LFO Start Phase", 107),
    ("LFO Trig Mode", 108),
    ("LFO Depth", 109),
)


class SysexSnapshotDecodeError(DataError, ValueError):
    """Raised when bytes cannot be decoded as a passive Rytm kit snapshot."""


@dataclass(frozen=True)
class RytmSnapshotParameter:
    """One editable parameter decoded from a saved pad sound block."""

    name: str
    cc: int
    block_offset: int
    value: int
    source: str


@dataclass(frozen=True)
class RytmSnapshotPad:
    """One raw saved-kit pad sound block."""

    pad: int
    midi_channel: int
    sound_name: str
    track_block_offset: int
    machine_raw_value: int
    machine_value: int
    machine_label: str
    parameter_map_status: str
    parameters: tuple[RytmSnapshotParameter, ...]
    decoded_block_offset: int
    decoded_block_length: int
    raw_block_nonzero_count: int
    sha256_12: str


@dataclass(frozen=True)
class RytmKitSnapshot:
    """Passive snapshot inventory for one saved Rytm kit record."""

    slot_number: int
    header_slot_index: int
    kit_name: str
    device_label: str
    record_length: int
    decoded_payload_length: int
    decode_status: str
    parameter_map_status: str
    pads: tuple[RytmSnapshotPad, ...]

    @property
    def pad_count(self) -> int:
        return len(self.pads)

    @property
    def mapped_parameter_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.parameters)


def decode_rytm_kit_snapshot_file(path: str | Path, *, slot: int) -> RytmKitSnapshot:
    """Decode a selected saved Rytm kit slot from a SysEx file."""

    if slot < 1 or slot > 128:
        raise SysexSnapshotDecodeError("slot must be 1-128")
    for message in _split_complete_sysex_messages(Path(path).read_bytes()):
        if _is_rytm_kit_record(message) and message[9] == slot - 1:
            return decode_rytm_kit_snapshot_record(message)
    raise SysexSnapshotDecodeError(f"Rytm kit slot {slot} not found")


def decode_rytm_kit_snapshot_record(message: bytes) -> RytmKitSnapshot:
    """Decode one packed Rytm kit record into a passive 12-pad raw snapshot."""

    if not _is_rytm_kit_record(message):
        raise SysexSnapshotDecodeError("not an Analog Rytm kit record")

    decoded_payload = unpack_elektron_7bit_payload(message[KIT_HEADER_LENGTH:-1])
    _require_sound_blocks(decoded_payload)
    slot_index = message[9]
    pads = tuple(_decode_pad(decoded_payload, pad) for pad in range(1, PAD_COUNT + 1))
    mapped_parameter_statuses = {pad.parameter_map_status for pad in pads if pad.parameters}

    return RytmKitSnapshot(
        slot_number=slot_index + 1,
        header_slot_index=slot_index,
        kit_name=_decode_ascii_field(
            decoded_payload[KIT_NAME_OFFSET : KIT_NAME_OFFSET + KIT_NAME_LENGTH]
        ),
        device_label="Analog Rytm MKII",
        record_length=len(message),
        decoded_payload_length=len(decoded_payload),
        decode_status=(
            "raw_sound_blocks_with_partial_parameter_map"
            if mapped_parameter_statuses
            else "raw_sound_blocks"
        ),
        parameter_map_status=_parameter_map_status(mapped_parameter_statuses),
        pads=pads,
    )


def unpack_elektron_7bit_payload(packed: bytes) -> bytes:
    """Unpack Elektron SysEx 7-bit data groups into raw bytes."""

    decoded = bytearray()
    for index in range(0, len(packed), 8):
        group = packed[index : index + 8]
        if not group:
            break
        mask = group[0]
        for bit, value in enumerate(group[1:]):
            decoded.append(value | (((mask >> bit) & 1) << 7))
    return bytes(decoded)


def format_rytm_kit_snapshot_report(snapshot: RytmKitSnapshot) -> list[str]:
    """Format a deterministic passive saved-kit snapshot report."""

    lines = [
        "RytmRandomizer passive Rytm kit snapshot report",
        f"Device: {snapshot.device_label}",
        f"Source slot: {snapshot.slot_number}",
        f"Kit: {snapshot.kit_name or '<blank>'}",
        f"Record length: {snapshot.record_length}",
        f"Decoded payload bytes: {snapshot.decoded_payload_length}",
        f"Pad snapshots: {snapshot.pad_count} / {PAD_COUNT}",
        f"Decode status: {snapshot.decode_status}",
        f"Parameter map: {snapshot.parameter_map_status}",
    ]
    if snapshot.mapped_parameter_pad_count:
        lines.append(f"Mapped parameter pads: {snapshot.mapped_parameter_pad_count} / {PAD_COUNT}")
    lines.append("Pads:")
    lines.extend(_format_pad_line(pad) for pad in snapshot.pads)
    if snapshot.mapped_parameter_pad_count:
        lines.append("Decoded parameter preview:")
        for pad in snapshot.pads:
            lines.extend(_format_parameter_line(pad, parameter) for parameter in pad.parameters)
    lines.extend(
        [
            "Live Snapshot relevance:",
            "- saved-kit baseline captured from SysEx bytes",
            "- all 12 pad sound blocks present",
            "- suitable for snapshot-derived mutation planning",
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


def format_rytm_kit_snapshot_error(path: str | Path, message: str) -> list[str]:
    """Format a deterministic passive snapshot decode error."""

    return [
        "RytmRandomizer passive Rytm kit snapshot report",
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


def _decode_pad(decoded_payload: bytes, pad: int) -> RytmSnapshotPad:
    track_offset = TRACK_BLOCK_START + ((pad - 1) * SOUND_BLOCK_LENGTH)
    track_block = decoded_payload[track_offset : track_offset + SOUND_BLOCK_LENGTH]
    offset = SOUND_BLOCK_START + ((pad - 1) * SOUND_BLOCK_LENGTH)
    block = decoded_payload[offset : offset + SOUND_BLOCK_LENGTH]
    machine_raw_value = track_block[TRACK_MACHINE_OFFSET]
    machine_value = _normalize_machine_value(machine_raw_value)
    parameters = _decode_parameters(track_block, machine_value)
    return RytmSnapshotPad(
        pad=pad,
        midi_channel=pad,
        sound_name=(
            _decode_ascii_field(
                track_block[TRACK_BLOCK_NAME_OFFSET : TRACK_BLOCK_NAME_OFFSET + KIT_NAME_LENGTH]
            )
            or _decode_ascii_field(block[:KIT_NAME_LENGTH])
        ),
        track_block_offset=track_offset,
        machine_raw_value=machine_raw_value,
        machine_value=machine_value,
        machine_label=_machine_label(machine_value),
        parameter_map_status=_pad_parameter_map_status(machine_value, parameters),
        parameters=parameters,
        decoded_block_offset=offset,
        decoded_block_length=len(block),
        raw_block_nonzero_count=sum(1 for byte in block if byte != 0),
        sha256_12=sha256(block).hexdigest().upper()[:12],
    )


def _require_sound_blocks(decoded_payload: bytes) -> None:
    required = SOUND_BLOCK_START + (PAD_COUNT * SOUND_BLOCK_LENGTH)
    if len(decoded_payload) < required:
        raise SysexSnapshotDecodeError("Rytm kit record is too short for 12 pad sound blocks")


def _decode_parameters(
    track_block: bytes,
    machine_value: int,
) -> tuple[RytmSnapshotParameter, ...]:
    machine_map = KNOWN_MACHINE_PARAMETER_MAPS.get(machine_value)
    if machine_map is None:
        return _decode_generic_parameters(track_block, machine_value)
    params, order = machine_map
    return tuple(
        RytmSnapshotParameter(
            name=name,
            cc=params[name],
            block_offset=SAVED_CC_OFFSETS[params[name]],
            value=track_block[SAVED_CC_OFFSETS[params[name]]],
            source=f"Rytm saved sound struct / {_machine_label(machine_value)} CC map",
        )
        for name in order
        if params[name] in SAVED_CC_OFFSETS
    )


def _decode_generic_parameters(
    track_block: bytes,
    machine_value: int,
) -> tuple[RytmSnapshotParameter, ...]:
    if machine_value == 27 or machine_value not in RYTM_MACHINE_LABELS:
        return ()
    return tuple(
        RytmSnapshotParameter(
            name=name,
            cc=cc,
            block_offset=SAVED_CC_OFFSETS[cc],
            value=track_block[SAVED_CC_OFFSETS[cc]],
            source=f"Rytm saved sound struct / {_machine_label(machine_value)} generic CC slot map",
        )
        for name, cc in GENERIC_SAVED_PARAMETER_ORDER
    )


def _parameter_map_status(mapped_parameter_statuses: set[str]) -> str:
    if not mapped_parameter_statuses:
        return "not_decoded_yet"
    if mapped_parameter_statuses == {"bd_hard_parameters"}:
        return "partial_bd_hard"
    if mapped_parameter_statuses == {"generic_machine_parameters"}:
        return "partial_generic_machine_maps"
    if "generic_machine_parameters" in mapped_parameter_statuses:
        return "partial_known_and_generic_machine_maps"
    return "partial_known_machine_maps"


def _pad_parameter_map_status(
    machine_value: int,
    parameters: tuple[RytmSnapshotParameter, ...],
) -> str:
    if not parameters:
        return "machine_identified_parameters_pending"
    if machine_value == 0:
        return "bd_hard_parameters"
    if machine_value not in KNOWN_MACHINE_PARAMETER_MAPS:
        return "generic_machine_parameters"
    return "known_machine_parameters"


def _normalize_machine_value(raw_value: int) -> int:
    if raw_value in RYTM_MACHINE_LABELS:
        return raw_value
    masked_value = raw_value & 0x7F
    if masked_value in RYTM_MACHINE_LABELS:
        return masked_value
    return raw_value


def _machine_label(machine_value: int) -> str:
    return RYTM_MACHINE_LABELS.get(machine_value, f"Unknown {machine_value}")


def _is_rytm_kit_record(message: bytes) -> bool:
    return (
        len(message) > KIT_HEADER_LENGTH
        and message[0] == 0xF0
        and message[-1] == 0xF7
        and message[1:4] == bytes([0x00, 0x20, 0x3C])
        and message[4] == RYTM_DEVICE_FAMILY
        and message[6] == KIT_OBJECT_TYPE
    )


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
        raise SysexSnapshotDecodeError("no complete SysEx messages found")
    return tuple(messages)


def _decode_ascii_field(field: bytes) -> str:
    printable = bytes(byte for byte in field if 32 <= byte <= 126)
    return printable.decode("ascii").strip()


def _format_pad_line(pad: RytmSnapshotPad) -> str:
    sound_name = pad.sound_name or "<blank>"
    machine = f"{pad.machine_label} ({pad.machine_value})"
    if pad.machine_raw_value != pad.machine_value:
        machine = f"{pad.machine_label} ({pad.machine_value}; raw {pad.machine_raw_value})"
    return (
        f"- Pad {pad.pad} / MIDI channel {pad.midi_channel}: {sound_name} / "
        f"machine {machine} / "
        f"mapped params {len(pad.parameters)} / "
        f"raw block bytes {pad.decoded_block_length} / sha {pad.sha256_12}"
    )


def _format_parameter_line(
    pad: RytmSnapshotPad,
    parameter: RytmSnapshotParameter,
) -> str:
    return (
        f"- Pad {pad.pad} {pad.machine_label} / {parameter.name}: "
        f"CC{parameter.cc} @0x{parameter.block_offset:04X} -> {parameter.value}"
    )


__all__ = [
    "RytmKitSnapshot",
    "RytmSnapshotPad",
    "RytmSnapshotParameter",
    "SysexSnapshotDecodeError",
    "decode_rytm_kit_snapshot_file",
    "decode_rytm_kit_snapshot_record",
    "format_rytm_kit_snapshot_error",
    "format_rytm_kit_snapshot_report",
    "unpack_elektron_7bit_payload",
]

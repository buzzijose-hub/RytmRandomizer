# Analog Four Snapshot Decoder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Four MKII saved-kit snapshot decoder and CLI report.

**Architecture:** Create one focused decoder module that reads existing SysEx bytes, selects Analog Four kit records, unpacks Elektron 7-bit payloads, and reports kit plus four track-block inventory. Wire it into the existing passive CLI/help style without MIDI imports or hardware side effects.

**Tech Stack:** Python dataclasses, existing passive CLI dispatch, pytest, existing observability error taxonomy.

---

## File Structure

- Create `tests/test_analog_four_snapshot_decoder.py`
  - Synthetic A4 kit SysEx fixture helpers.
  - Decoder tests.
  - CLI happy-path test.
- Create `rytm_randomizer/analog_four_snapshot_decoder.py`
  - Passive A4 kit snapshot dataclasses.
  - SysEx splitting, kit-record selection, Elektron 7-bit unpacking.
  - Deterministic report and error formatting.
- Modify `rytm_randomizer/cli.py`
  - Add `analog-four-kit-snapshot-report <path> --slot <1-128>`.
- Modify `rytm_randomizer/help_text.py`
  - Add command to usage, top-level help, and command-specific help.
- Modify `tests/test_cli.py`
  - Add command help test.
- Modify `tests/fixtures/cli_help_expected.txt`
  - Keep top-level help fixture in sync.
- Modify `tests/architecture/test_observability.py`
  - Add `AnalogFourSnapshotDecodeError` to the taxonomy allow-list.
- Modify `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
  - Add operator command and safety notes.
- Add `docs/ANALOG_FOUR_KIT_SNAPSHOT_DECODER_CHECKPOINT.md`
  - Capture the milestone and next boundary.

## Task 1: Passive Domain Decoder

**Files:**
- Create: `tests/test_analog_four_snapshot_decoder.py`
- Create: `rytm_randomizer/analog_four_snapshot_decoder.py`
- Modify: `tests/architecture/test_observability.py`

- [ ] **Step 1: Write failing decoder tests**

Create `tests/test_analog_four_snapshot_decoder.py` with:

```python
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pack_7bit_payload(payload):
    packed = bytearray()
    for index in range(0, len(payload), 7):
        chunk = payload[index : index + 7]
        mask = 0
        data = bytearray()
        for bit, value in enumerate(chunk):
            if value & 0x80:
                mask |= 1 << bit
            data.append(value & 0x7F)
        packed.append(mask)
        packed.extend(data)
    return bytes(packed)


def make_a4_kit_record(slot_index=0, kit_name="A4 KIT", track_names=None, device_family=0x06):
    track_names = track_names or ("BASS LOW", "STAB HIT", "DRONE PAD", "NOISE FX")
    decoded = bytearray(2414)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for offset, name in zip((44, 394, 744, 1094), track_names):
        decoded[offset : offset + len(name)] = name.encode("ascii")
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, device_family, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def test_importing_analog_four_snapshot_decoder_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four_snapshot_decoder; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_decode_analog_four_kit_snapshot_reads_kit_and_four_track_blocks():
    from rytm_randomizer.analog_four_snapshot_decoder import (
        decode_analog_four_kit_snapshot_bytes,
    )

    snapshot = decode_analog_four_kit_snapshot_bytes(
        make_a4_kit_record(kit_name="WAREHOUSE A4"),
        slot=1,
    )

    assert snapshot.slot_number == 1
    assert snapshot.kit_name == "WAREHOUSE A4"
    assert snapshot.record_length > 0
    assert snapshot.decoded_payload_length == 2414
    assert snapshot.manufacturer_id == "00 20 3C"
    assert snapshot.device_family_byte == 0x06
    assert snapshot.object_type == 0x52
    assert len(snapshot.tracks) == 4
    assert [track.name for track in snapshot.tracks] == [
        "BASS LOW",
        "STAB HIT",
        "DRONE PAD",
        "NOISE FX",
    ]
    assert [track.block_offset for track in snapshot.tracks] == [44, 394, 744, 1094]
    assert {track.mapping_status for track in snapshot.tracks} == {
        "saved_parameter_offsets_unmapped"
    }


def test_decode_analog_four_kit_snapshot_rejects_invalid_slot():
    from rytm_randomizer.analog_four_snapshot_decoder import (
        AnalogFourSnapshotDecodeError,
        decode_analog_four_kit_snapshot_bytes,
    )

    with pytest.raises(AnalogFourSnapshotDecodeError, match="slot must be 1-128"):
        decode_analog_four_kit_snapshot_bytes(make_a4_kit_record(), slot=0)


def test_decode_analog_four_kit_snapshot_rejects_non_a4_kit_record():
    from rytm_randomizer.analog_four_snapshot_decoder import (
        AnalogFourSnapshotDecodeError,
        decode_analog_four_kit_snapshot_bytes,
    )

    with pytest.raises(AnalogFourSnapshotDecodeError, match="not an Analog Four kit record"):
        decode_analog_four_kit_snapshot_bytes(make_a4_kit_record(device_family=0x07), slot=1)


def test_format_analog_four_kit_snapshot_report_states_unmapped_offsets():
    from rytm_randomizer.analog_four_snapshot_decoder import (
        decode_analog_four_kit_snapshot_bytes,
        format_analog_four_kit_snapshot_report,
    )

    snapshot = decode_analog_four_kit_snapshot_bytes(make_a4_kit_record(), slot=1)
    report = "\n".join(format_analog_four_kit_snapshot_report(snapshot))

    assert "RytmRandomizer passive Analog Four kit snapshot report" in report
    assert "Kit: A4 KIT" in report
    assert "Track snapshots:" in report
    assert "- Track 4 / MIDI channel 4 / wire channel 3 / offset 1094" in report
    assert "saved_parameter_offsets_unmapped" in report
    assert "- no MIDI sending" in report
    assert "- no SysEx writes" in report
```

- [ ] **Step 2: Run decoder tests to verify red**

Run:

```powershell
pytest tests\test_analog_four_snapshot_decoder.py -q
```

Expected: fail with `ModuleNotFoundError: No module named 'rytm_randomizer.analog_four_snapshot_decoder'`.

- [ ] **Step 3: Implement minimal decoder module**

Create `rytm_randomizer/analog_four_snapshot_decoder.py`:

```python
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
```

- [ ] **Step 4: Add observability taxonomy allow-list**

Modify `tests/architecture/test_observability.py` in `_TAXONOMY_NAMES`:

```python
        "AnalogFourSnapshotDecodeError",
```

Place it near the passive SysEx/snapshot analysis errors.

- [ ] **Step 5: Run decoder and architecture tests**

Run:

```powershell
pytest tests\test_analog_four_snapshot_decoder.py tests\architecture\test_observability.py::test_raises_use_taxonomy_or_validation_stdlib -q
```

Expected: all tests pass.

## Task 2: CLI And Help

**Files:**
- Modify: `tests/test_analog_four_snapshot_decoder.py`
- Modify: `tests/test_cli.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Add failing CLI tests**

Append to `tests/test_analog_four_snapshot_decoder.py`:

```python
def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_analog_four_kit_snapshot_cli_reads_saved_kit_without_hardware(tmp_path):
    sysex_path = tmp_path / "a4-kits.syx"
    sysex_path.write_bytes(make_a4_kit_record(kit_name="CLI A4"))

    result = run_cli(
        "analog-four-kit-snapshot-report",
        str(sysex_path),
        "--slot",
        "1",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four kit snapshot report" in result.stdout
    assert "Kit: CLI A4" in result.stdout
    assert "Track snapshots:" in result.stdout
    assert "saved_parameter_offsets_unmapped" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no SysEx writes" in result.stdout
    assert result.stderr == ""
```

Add to `tests/test_cli.py`:

```python
def test_analog_four_kit_snapshot_report_help_exits_zero():
    result = run_cli("analog-four-kit-snapshot-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: analog-four-kit-snapshot-report" in result.stdout
    assert "Analog Four kit" in result.stdout
    assert "saved_parameter_offsets_unmapped" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""
```

- [ ] **Step 2: Run CLI tests to verify red**

Run:

```powershell
pytest tests\test_analog_four_snapshot_decoder.py tests\test_cli.py -q
```

Expected: fail because the CLI command/help is not wired yet.

- [ ] **Step 3: Wire CLI dispatch**

In `rytm_randomizer/cli.py`, add this block after the existing snapshot/dual-machine report dispatches:

```python
    if (
        len(args) == 4
        and args[0] == "analog-four-kit-snapshot-report"
        and args[2] == "--slot"
    ):
        from .analog_four_snapshot_decoder import (
            AnalogFourSnapshotDecodeError,
            decode_analog_four_kit_snapshot_file,
            format_analog_four_kit_snapshot_error,
            format_analog_four_kit_snapshot_report,
        )

        try:
            slot = int(args[3])
            snapshot = decode_analog_four_kit_snapshot_file(args[1], slot=slot)
        except FileNotFoundError:
            lines = format_analog_four_kit_snapshot_error(args[1], "File not found")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except AnalogFourSnapshotDecodeError as exc:
            lines = format_analog_four_kit_snapshot_error(args[1], str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1
        except ValueError:
            lines = format_analog_four_kit_snapshot_error(args[1], "Slot must be an integer")
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_kit_snapshot_report(snapshot)))
        sys.stdout.write("\n")
        return 0
```

- [ ] **Step 4: Add help text**

In `rytm_randomizer/help_text.py`:

Add to `USAGE`:

```text
analog-four-kit-snapshot-report <path> --slot <1-128> |
```

Add to top-level `Usage:`:

```text
  python -m rytm_randomizer.cli analog-four-kit-snapshot-report <path> --slot <1-128>
```

Add to top-level `Commands:`:

```text
  analog-four-kit-snapshot-report
                     Decode a saved Analog Four kit into a passive track snapshot.
```

Add command-specific help:

```python
    "analog-four-kit-snapshot-report": """RytmRandomizer passive CLI: analog-four-kit-snapshot-report

Usage:
  python -m rytm_randomizer.cli analog-four-kit-snapshot-report <path> --slot <1-128>
  python -m rytm_randomizer.cli analog-four-kit-snapshot-report --help

Behavior:
  Reads an existing Analog Four MKII kit bank or whole-project SysEx file,
  selects one kit slot, unpacks its saved Elektron 7-bit payload, and prints a
  passive kit plus Track 1-4 inventory. Saved parameter offsets are reported as
  saved_parameter_offsets_unmapped until a later mapper proves the layout. It
  does not request dumps, receive live SysEx, send MIDI, write SysEx, or touch
  hardware.

Safety:
  passive/read-only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
```

- [ ] **Step 5: Update top-level help fixture**

Update `tests/fixtures/cli_help_expected.txt` with the same top-level usage and command entry from Step 4.

- [ ] **Step 6: Run CLI tests to verify green**

Run:

```powershell
pytest tests\test_analog_four_snapshot_decoder.py tests\test_cli.py -q
```

Expected: all tests pass.

## Task 3: Docs And Real File Verification

**Files:**
- Modify: `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Create: `docs/ANALOG_FOUR_KIT_SNAPSHOT_DECODER_CHECKPOINT.md`

- [ ] **Step 1: Add operator quickstart section**

Add this section after the Analog Four reference report section in `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`:

````markdown
## Analog Four Kit Snapshot Report

Decode one saved Analog Four kit slot into a passive Track 1-4 inventory:

```powershell
python -m rytm_randomizer.cli analog-four-kit-snapshot-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --slot 1
```

This command reads an existing Analog Four kit bank or whole-project dump,
unpacks the saved kit payload, and reports the kit name plus four track blocks.
It intentionally marks saved parameter offsets as `saved_parameter_offsets_unmapped`
until a later mapper proves the saved kit layout.

It does not open MIDI ports, send MIDI, receive live SysEx, write SysEx, or
mutate hardware.
````

- [ ] **Step 2: Add checkpoint doc**

Create `docs/ANALOG_FOUR_KIT_SNAPSHOT_DECODER_CHECKPOINT.md`:

```markdown
# Analog Four Kit Snapshot Decoder Checkpoint

Date: 2026-05-17

## What This Milestone Proves

The project can now inspect saved Analog Four MKII kit records without touching
hardware. This is the first step toward moving the A4 side from safe-starter
mock planning to captured-kit mutation planning.

## Current Scope

- Reads saved `.syx` files from disk
- Selects Analog Four kit slots `1-128`
- Unpacks Elektron 7-bit payloads
- Reports kit name and four Track 1-4 snapshot blocks
- Reports per-track block hashes
- Marks saved parameter offsets as `saved_parameter_offsets_unmapped`

## Safety Boundary

- passive/read-only
- no MIDI sending
- no MIDI receive
- no port opening
- no hardware mutation
- no live SysEx receive
- no SysEx writes
- no hardware required

## Next Slice

The next slice is a saved parameter offset mapper using differential evidence
from known kit variations or controlled exports. Captured-value A4 mutation
should wait until that mapper is proven.
```

- [ ] **Step 3: Run focused tests**

Run:

```powershell
pytest tests\test_analog_four_snapshot_decoder.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

Expected: all tests pass.

- [ ] **Step 4: Run real Analog Four project verification**

Run:

```powershell
python -m rytm_randomizer.cli analog-four-kit-snapshot-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --slot 1
```

Expected stdout includes:

```text
RytmRandomizer passive Analog Four kit snapshot report
Slot: 1
Kit: KIT 1
Decoded payload length: 2414
Track snapshots:
saved_parameter_offsets_unmapped
Safety:
- no MIDI sending
- no SysEx writes
```

- [ ] **Step 5: Run repository hygiene checks**

Run:

```powershell
git diff --check
git diff --exit-code -- rytm_hybrid_randomizer_v134.py
```

Expected: both exit `0`. The first command may print Windows LF/CRLF warnings only if Git emits warnings without failing.

- [ ] **Step 6: Commit implementation**

Run:

```powershell
git status --short
git add -- docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md docs/ANALOG_FOUR_KIT_SNAPSHOT_DECODER_CHECKPOINT.md rytm_randomizer/analog_four_snapshot_decoder.py rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/architecture/test_observability.py tests/fixtures/cli_help_expected.txt tests/test_analog_four_snapshot_decoder.py tests/test_cli.py
git commit -m "Add Analog Four kit snapshot decoder"
```

Expected: commit succeeds with only A4 snapshot decoder files staged.

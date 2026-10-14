"""Strict, lossless local CSV parsing; no device or MIDI boundary."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cockpit.export.reader import read_bounded_artifact
from ..data.midi_csv_reconciliation import (
    MIDI_CSV_ADDRESS_COLUMNS,
    MIDI_CSV_ADDRESS_MAX,
    MIDI_CSV_COLUMNS,
    MIDI_CSV_VALUE_MAX,
    MidiCsvSourceSpec,
)
from .formatter import sha256_bytes

_MAX_SOURCE_BYTES: Final[int] = 1024 * 1024
_NUMBER: Final[re.Pattern[str]] = re.compile(r"[+-]?\d+\Z")
_CHOICE: Final[re.Pattern[str]] = re.compile(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*:\s*(.+?)\s*$")


@dataclass(frozen=True)
class CsvChoice:
    """A point or interval claim, never expanded into an authoritative enum."""

    minimum: int
    maximum: int
    label: str


@dataclass(frozen=True)
class MidiCsvRow:
    """Physical CSV record identity plus exact cell and textual content."""

    ordinal: int
    line_start: int
    line_end: int
    cells: tuple[tuple[str, str], ...]
    raw_record: str

    def cell(self, name: str) -> str:
        return dict(self.cells)[name]

    def number(self, name: str) -> int | None:
        return parse_optional_number(self.cell(name))


@dataclass(frozen=True)
class MidiCsvSource:
    spec: MidiCsvSourceSpec
    sha256: str
    git_blob: str
    byte_count: int
    header_record: str
    rows: tuple[MidiCsvRow, ...]


def parse_optional_number(value: str) -> int | None:
    """Do not reinterpret absent cells as zero or silently truncate fractions."""
    if value.strip() == "":
        return None
    if not _NUMBER.fullmatch(value.strip()):
        raise ValueError("CSV numeric cell is not an integer")
    return int(value)


def parse_csv_choices(value: str) -> tuple[tuple[CsvChoice, ...], tuple[str, ...]]:
    """Retain interval overlaps and unparsed claims explicitly."""
    choices: list[CsvChoice] = []
    issues: list[str] = []
    for token in value.split(";") if value.strip() else ():
        match = _CHOICE.fullmatch(token)
        if match is None:
            issues.append("unparsed_usage_claim:" + token.strip())
            continue
        lower = int(match[1])
        upper = int(match[2]) if match[2] is not None else lower
        if not 0 <= lower <= upper <= MIDI_CSV_VALUE_MAX:
            issues.append("usage_claim_outside_domain:" + token.strip())
            continue
        choices.append(CsvChoice(lower, upper, match[3]))
    for index, choice in enumerate(choices):
        if any(
            max(choice.minimum, other.minimum) <= min(choice.maximum, other.maximum)
            for other in choices[:index]
        ):
            issues.append("overlapping_usage_claims")
    return tuple(choices), tuple(dict.fromkeys(issues))


def csv_row_issues(row: MidiCsvRow) -> tuple[str, ...]:
    """Validate supplied bounds without granting native or transport semantics."""
    issues: list[str] = []
    for name in MIDI_CSV_ADDRESS_COLUMNS:
        value = row.number(name)
        if value is not None and not 0 <= value <= MIDI_CSV_ADDRESS_MAX:
            issues.append("address_outside_u7:" + name)
    for prefix in ("cc", "nrpn"):
        lower = row.number(prefix + "_min_value")
        upper = row.number(prefix + "_max_value")
        default = row.number(prefix + "_default_value")
        maximum = MIDI_CSV_VALUE_MAX
        if prefix == "cc" and row.number("cc_lsb") is None:
            maximum = MIDI_CSV_ADDRESS_MAX
        if any(
            value is not None and not 0 <= value <= maximum for value in (lower, upper, default)
        ):
            issues.append("range_outside_midi_domain:" + prefix)
        if lower is not None and upper is not None and lower > upper:
            issues.append("reversed_range:" + prefix)
        if default is not None and (
            (lower is not None and default < lower) or (upper is not None and default > upper)
        ):
            issues.append("default_outside_range:" + prefix)
        if row.number(prefix + "_lsb") is not None and row.number(prefix + "_msb") is None:
            issues.append("address_missing_msb:" + prefix)
    return tuple(issues)


def parse_midi_csv(raw: bytes, spec: MidiCsvSourceSpec) -> MidiCsvSource:
    """Require the pinned input, exact schema and safe device identity."""
    digest = sha256_bytes(raw)
    if len(raw) > _MAX_SOURCE_BYTES or digest != spec.sha256:
        raise ValueError("CSV source hash or size does not match pinned contract")
    content = raw.decode("utf-8-sig")
    lines = content.splitlines(keepends=True)
    reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
    if tuple(reader.fieldnames or ()) != MIDI_CSV_COLUMNS:
        raise ValueError("CSV columns do not match source contract")
    header_end = reader.line_num
    previous_end = header_end
    rows: list[MidiCsvRow] = []
    for ordinal, cells in enumerate(reader, 1):
        if None in cells or any(cell is None for cell in cells.values()):
            raise ValueError("CSV record has missing or extra cells")
        if cells["manufacturer"] != "Elektron" or cells["device"] != spec.device_label:
            raise ValueError("CSV record device identity is unsafe")
        row = MidiCsvRow(
            ordinal,
            previous_end + 1,
            reader.line_num,
            tuple((key, cells[key]) for key in MIDI_CSV_COLUMNS),
            "".join(lines[previous_end : reader.line_num]),
        )
        for name in MIDI_CSV_COLUMNS[5:15]:
            row.number(name)
        rows.append(row)
        previous_end = reader.line_num
    if len(rows) != spec.row_count:
        raise ValueError("CSV row count does not match source contract")
    # Git blob identity is not a security digest; SHA256 above pins the bytes.
    blob = hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw, usedforsecurity=False
    ).hexdigest()
    return MidiCsvSource(spec, digest, blob, len(raw), "".join(lines[:header_end]), tuple(rows))


def read_midi_csv(path: Path, spec: MidiCsvSourceSpec) -> MidiCsvSource:
    """Bounded explicit local read; original input is never modified."""
    raw = read_bounded_artifact(path, maximum=_MAX_SOURCE_BYTES, label="CSV source")
    return parse_midi_csv(raw, spec)

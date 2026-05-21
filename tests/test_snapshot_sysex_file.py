"""Tests for passive SysEx file payload extraction."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import rytm_real_layout_kit_payload

pytestmark = pytest.mark.fast


def test_extract_sysex_payloads_accepts_already_stripped_payload() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    payload = rytm_real_layout_kit_payload(name=b"RAW")

    assert extract_sysex_payloads(payload) == (payload,)


def test_extract_sysex_payloads_strips_single_framed_sysex() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    payload = rytm_real_layout_kit_payload(name=b"FRAMED")

    assert extract_sysex_payloads(bytes([0xF0]) + payload + bytes([0xF7])) == (payload,)


def test_extract_sysex_payloads_returns_all_frames_from_c6_dump() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    first = bytes([0x00, 0x20, 0x3C, 0x05, 0x00])
    second = rytm_real_layout_kit_payload(name=b"BANK")
    raw = bytes([0xF0]) + first + bytes([0xF7, 0xF0]) + second + bytes([0xF7])

    assert extract_sysex_payloads(raw) == (first, second)


def test_extract_sysex_payloads_rejects_empty_input() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    with pytest.raises(ValueError, match="empty"):
        extract_sysex_payloads(b"")


def test_extract_sysex_payloads_rejects_empty_frame() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    with pytest.raises(ValueError, match="empty payload"):
        extract_sysex_payloads(bytes([0xF0, 0xF7]))


def test_extract_sysex_payloads_rejects_unclosed_frame() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    with pytest.raises(ValueError, match="without a closing F7"):
        extract_sysex_payloads(bytes([0xF0, 0x00, 0x20, 0x3C]))


def test_extract_sysex_payloads_rejects_incomplete_end_framing() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    with pytest.raises(ValueError, match="framing is incomplete"):
        extract_sysex_payloads(bytes([0x00, 0x20, 0x3C, 0xF7]))


def test_read_sysex_payloads_from_path_rejects_missing_file(tmp_path: Path) -> None:
    from rytm_randomizer.snapshot.sysex_file import read_sysex_payloads_from_path

    with pytest.raises(ValueError, match="does not exist"):
        read_sysex_payloads_from_path(tmp_path / "missing.syx")


def test_read_sysex_payloads_from_path_rejects_directory(tmp_path: Path) -> None:
    from rytm_randomizer.snapshot.sysex_file import read_sysex_payloads_from_path

    with pytest.raises(ValueError, match="not a file"):
        read_sysex_payloads_from_path(tmp_path)


def test_read_sysex_payloads_from_path_wraps_read_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.snapshot.sysex_file import read_sysex_payloads_from_path

    path = tmp_path / "kit.syx"
    path.write_bytes(b"not reached")

    def _raise_os_error(self: Path) -> bytes:
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_bytes", _raise_os_error)

    with pytest.raises(ValueError, match="Could not read SysEx file"):
        read_sysex_payloads_from_path(path)


def test_read_sysex_payloads_from_path_reads_payloads(tmp_path: Path) -> None:
    from rytm_randomizer.snapshot.sysex_file import read_sysex_payloads_from_path

    payload = rytm_real_layout_kit_payload(name=b"FILE")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    assert read_sysex_payloads_from_path(path) == (payload,)

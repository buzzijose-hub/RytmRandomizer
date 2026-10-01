"""Pin the first real Digitakt MK1 captures, and the intake script that files them.

The two ``.syx`` files under ``tests/fixtures/digitakt_saved_kit/`` came off a
physical Digitakt MK1 (OS 1.52A) via SETTINGS > SYSEX DUMP > SYSEX SEND >
PATTERN. They are the only hardware evidence in the repo for this family, so
the facts they prove are asserted against the bytes themselves here rather
than only through a regenerated constant.

They also exposed that the intake script had never worked on a real file: it
handed the framed dump (leading ``F0``) straight to the decoder. Its tests
below therefore feed it the real framed captures, never a hand-built payload.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.data.digitakt_saved_kit_layout import (
    DIGITAKT_MK1_FAMILY_BYTE,
    DIGITAKT_SNAPSHOT_LAYOUT_PATTERN,
)
from rytm_randomizer.devices import get_device
from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID
from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

pytestmark = pytest.mark.fast

_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_FIXTURES: Final[Path] = _ROOT / "tests" / "fixtures" / "digitakt_saved_kit"
_LOW: Final[Path] = _FIXTURES / "digitakt_mk1_kit_filter_low.syx"
_HIGH: Final[Path] = _FIXTURES / "digitakt_mk1_kit_filter_high.syx"

#: Where track 1 filter frequency landed in the framed dump (0 -> 127).
_FILTER_FREQ_INDEX: Final[int] = 28815
#: Two 7-bit checksum bytes sit before the 2-byte length field and ``F7``.
_CHECKSUM_SLICE: Final[slice] = slice(-5, -3)

_SCRIPT: Final[Path] = _ROOT / "scripts" / "intake_digitakt_capture.py"
_spec = importlib.util.spec_from_file_location("intake_digitakt_capture", _SCRIPT)
assert _spec is not None and _spec.loader is not None
intake = importlib.util.module_from_spec(_spec)
sys.modules["intake_digitakt_capture"] = intake
_spec.loader.exec_module(intake)


def _checksum(framed: bytes) -> int:
    return (framed[-5] << 7) | framed[-4]


# ---------------------------------------------------------------------------
# The hardware evidence
# ---------------------------------------------------------------------------


def test_fixtures_exist_and_match_their_recorded_sha256() -> None:
    readme = (_FIXTURES / "README.md").read_text(encoding="utf-8")
    for path in (_LOW, _HIGH):
        assert path.is_file(), path
        recorded = re.search(rf"`{re.escape(path.name)}`.*?SHA256 `([0-9a-f]{{64}})`", readme)
        assert recorded is not None, f"{path.name} missing from README"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == recorded.group(1)


def test_each_capture_is_exactly_one_elektron_message_with_the_mk1_family_byte() -> None:
    for path in (_LOW, _HIGH):
        framed = path.read_bytes()
        assert framed[0] == 0xF0 and framed[-1] == 0xF7
        (payload,) = extract_sysex_payloads(framed)
        assert payload.startswith(ELEKTRON_MFR_ID)
        # The byte the MK1 constant was corrected to (it was a 0x0C guess).
        assert payload[len(ELEKTRON_MFR_ID)] == DIGITAKT_MK1_FAMILY_BYTE == 0x0A


def test_the_pair_differs_only_in_filter_frequency_and_its_checksum() -> None:
    low, high = _LOW.read_bytes(), _HIGH.read_bytes()
    assert len(low) == len(high)
    changed = [i for i, (a, b) in enumerate(zip(low, high, strict=True)) if a != b]
    checksum_indices = list(range(len(low)))[_CHECKSUM_SLICE]

    assert changed == [_FILTER_FREQ_INDEX, *checksum_indices]
    assert (low[_FILTER_FREQ_INDEX], high[_FILTER_FREQ_INDEX]) == (0, 127)
    assert _checksum(high) - _checksum(low) == 127


@pytest.mark.parametrize("path", [_LOW, _HIGH], ids=["low", "high"])
def test_checksum_is_the_14_bit_sum_of_the_data_bytes(path: Path) -> None:
    framed = path.read_bytes()
    assert _checksum(framed) == sum(framed[10:-5]) & 0x3FFF


def test_mk1_decodes_the_real_capture_and_digitakt_ii_refuses_it() -> None:
    (payload,) = extract_sysex_payloads(_LOW.read_bytes())

    snapshot = get_device("digitakt_mk1").decode_snapshot(payload, 0)
    assert snapshot.snapshot_layout == DIGITAKT_SNAPSHOT_LAYOUT_PATTERN
    assert snapshot.offsets_promoted is False

    with pytest.raises(ValueError, match="got 0x0a"):
        get_device("digitakt_ii").decode_snapshot(payload, 0)


# ---------------------------------------------------------------------------
# The intake script, fed the real framed files
# ---------------------------------------------------------------------------


@pytest.fixture
def fixture_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "tests" / "fixtures" / "digitakt_saved_kit"
    monkeypatch.setattr(intake, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(intake, "FIXTURE_DIR", target)
    return target


def _args(low: Path, high: Path | None = None) -> list[str]:
    argv = [
        "--device",
        "digitakt_mk1",
        "--low",
        str(low),
        "--captured-by",
        "Tester",
        "--os-version",
        "1.52A",
        "--menu-path",
        "SETTINGS > SYSEX DUMP > SYSEX SEND > PATTERN",
    ]
    return argv if high is None else [*argv, "--high", str(high)]


def test_intake_files_a_real_framed_pair(fixture_dir: Path) -> None:
    assert intake.main(_args(_LOW, _HIGH)) == 0

    for name, source in (
        ("digitakt_mk1_kit_filter_low.syx", _LOW),
        ("digitakt_mk1_kit_filter_high.syx", _HIGH),
    ):
        # The framed original is what gets filed, byte for byte.
        assert (fixture_dir / name).read_bytes() == source.read_bytes()
    note = (fixture_dir / "README.md").read_text(encoding="utf-8")
    assert hashlib.sha256(_LOW.read_bytes()).hexdigest() in note
    assert "SYSEX SEND > PATTERN" in note


def test_intake_warns_when_only_one_capture_is_given(
    fixture_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert intake.main(_args(_LOW)) == 0
    assert "no --high capture given" in capsys.readouterr().err
    assert not (fixture_dir / "digitakt_mk1_kit_filter_high.syx").exists()


def _refused(argv: list[str], capsys: pytest.CaptureFixture[str]) -> str:
    with pytest.raises(SystemExit) as excinfo:
        intake.main(argv)
    assert excinfo.value.code == 1
    return capsys.readouterr().err


def test_intake_refuses_two_messages_in_one_file(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doubled = tmp_path / "doubled.syx"
    doubled.write_bytes(_LOW.read_bytes() * 2)
    assert "expected exactly one SysEx message, found 2" in _refused(_args(doubled), capsys)
    assert not fixture_dir.exists()


def test_intake_refuses_a_capture_cut_off_before_its_end_byte(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A listener stopped too early: F0 arrived, the closing F7 never did.
    truncated = tmp_path / "truncated.syx"
    truncated.write_bytes(_LOW.read_bytes()[:-100])
    assert "without a closing F7" in _refused(_args(truncated), capsys)
    assert not fixture_dir.exists()


def test_intake_refuses_a_non_digitakt_dump(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    other = tmp_path / "other.syx"
    framed = bytearray(_LOW.read_bytes())
    framed[4] = 0x7E  # some other Elektron product
    other.write_bytes(bytes(framed))
    assert "not a readable Digitakt dump" in _refused(_args(other), capsys)


def test_intake_refuses_identical_captures_and_writes_nothing(
    fixture_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert "byte-identical" in _refused(_args(_LOW, _LOW), capsys)
    assert not fixture_dir.exists()


def test_intake_refuses_missing_empty_and_oversized_files(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert "no such file" in _refused(_args(tmp_path / "absent.syx"), capsys)

    empty = tmp_path / "empty.syx"
    empty.write_bytes(b"")
    assert "is empty" in _refused(_args(empty), capsys)

    huge = tmp_path / "project.syx"
    huge.write_bytes(bytes(intake.MAX_REASONABLE_KIT_BYTES + 1))
    assert "whole PROJECT" in _refused(_args(huge), capsys)


# ---------------------------------------------------------------------------
# Part C: the four-capture series, built from the real dump
# ---------------------------------------------------------------------------


def _framed_variant(edits: dict[int, int]) -> bytes:
    """Steve's real pattern with unpacked bytes edited, re-encoded and framed."""

    from rytm_randomizer.devices.strategies.digitakt_pattern_codec import (
        DIGITAKT_MK1_PATTERN_LAYOUT,
        decode_digitakt_pattern_payload,
        encode_digitakt_pattern_payload,
    )

    (payload,) = extract_sysex_payloads(_LOW.read_bytes())
    decoded = decode_digitakt_pattern_payload(payload, DIGITAKT_MK1_PATTERN_LAYOUT)
    body = bytearray(decoded.unpacked)
    for offset, value in edits.items():
        body[offset] = value
    encoded = encode_digitakt_pattern_payload(
        decoded.prefix, bytes(body), DIGITAKT_MK1_PATTERN_LAYOUT
    )
    return b"\xf0" + encoded + b"\xf7"


def _write_part_c(directory: Path) -> None:
    """A plausible Part C sitting: each step changes exactly one byte."""

    track1, track2, track8 = 25204, 25364, 26324
    steps = {
        "base.syx": {track1: 127},
        "t1_mid.syx": {track1: 64},
        "t2_low.syx": {track1: 64, track2: 0},
        "t8_low.syx": {track1: 64, track2: 0, track8: 0},
    }
    directory.mkdir(parents=True, exist_ok=True)
    for name, edits in steps.items():
        (directory / name).write_bytes(_framed_variant(edits))


def _part_c_args(from_dir: Path, *extra: str) -> list[str]:
    return [
        "--device",
        "digitakt_mk1",
        "--part-c",
        "--from-dir",
        str(from_dir),
        "--captured-by",
        "Tester",
        "--os-version",
        "1.52A",
        *extra,
    ]


def test_part_c_files_the_series_in_its_own_folder(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    desktop = tmp_path / "Desktop"
    _write_part_c(desktop)
    # Part B's note must survive Part C.
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "README.md").write_text("part b note", encoding="utf-8")

    assert intake.main(_part_c_args(desktop, "--screen-values", "track 1 FREQ 64")) == 0

    part_c = fixture_dir / "part_c"
    for stem in ("base", "t1_mid", "t2_low", "t8_low"):
        filed = part_c / f"digitakt_mk1_partc_{stem}.syx"
        assert filed.read_bytes() == (desktop / f"{stem}.syx").read_bytes()
    note = (part_c / "README.md").read_text(encoding="utf-8")
    assert "Screen values reported: track 1 FREQ 64" in note
    assert "SYSEX SEND > PATTERN" in note  # the default menu path
    assert (fixture_dir / "README.md").read_text(encoding="utf-8") == "part b note"

    out = capsys.readouterr().out
    assert out.count("1 byte(s) changed") == 3


def test_part_c_refuses_a_step_where_nothing_changed(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    desktop = tmp_path / "Desktop"
    _write_part_c(desktop)
    (desktop / "t2_low.syx").write_bytes((desktop / "t1_mid.syx").read_bytes())

    err = _refused(_part_c_args(desktop), capsys)
    assert "t1_mid.syx and t2_low.syx are byte-identical" in err
    assert not fixture_dir.exists()


def test_part_c_names_a_missing_file(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    desktop = tmp_path / "Desktop"
    _write_part_c(desktop)
    (desktop / "t8_low.syx").unlink()

    assert "t8_low.syx" in _refused(_part_c_args(desktop), capsys)
    assert not fixture_dir.exists()


def test_part_c_rejects_high_and_low_mixed_in(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert "--high belongs to the low/high pair" in _refused(
        _part_c_args(tmp_path, "--high", str(_HIGH)), capsys
    )
    with pytest.raises(SystemExit) as excinfo:
        intake.main(_part_c_args(tmp_path, "--low", str(_LOW)))
    assert excinfo.value.code == 2  # argparse: mutually exclusive


def test_part_c_counts_raw_bytes_for_a_generation_without_a_verified_layout() -> None:
    """Digitakt II dumps are undecoded, so the comparison falls back to raw bytes."""

    from rytm_randomizer.data.digitakt_saved_kit_layout import DIGITAKT_II_FAMILY_BYTE

    def framed(body: bytes) -> bytes:
        return (
            b"\xf0" + ELEKTRON_MFR_ID + bytes([DIGITAKT_II_FAMILY_BYTE, 0, 0x50]) + body + b"\xf7"
        )

    assert intake._changed_bytes(framed(b"\x01\x02"), framed(b"\x01\x03"), "digitakt_ii") == 1
    longer = framed(b"\x01\x02\x03")
    # Different lengths: report the longer file's size rather than a misleading count.
    assert intake._changed_bytes(framed(b"\x01"), longer, "digitakt_ii") == len(longer)

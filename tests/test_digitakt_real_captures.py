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

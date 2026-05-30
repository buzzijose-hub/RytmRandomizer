"""Tests for ``rytm_randomizer.cockpit.wizard.sysex_analyzer``.

The Phase 2 sysex analyzer is a deterministic byte-statistics function
on top of the file path -- no SysEx parser, no kit-record decoding.
Tests pin each branch:

* known-bytes -> known-trait mapping (the four statistics);
* empty bytes -> neutral profile;
* single-file path;
* folder of multiple files (equal-weighted averaging);
* folder with no matching files -> neutral profile;
* missing path -> ``FileNotFoundError``;
* non-Path argument -> ``ValueError``;
* non-file / non-dir path -> ``ValueError``.

CODE_REVIEW.md M5: the analyzer emits placeholder trait names
(``_bytes_mean`` / ``_bytes_stddev`` / ``_bytes_density`` /
``_bytes_distinct``) rather than the canonical
:data:`WIZARD_TRAIT_NAMES`, because byte-statistics on a SysEx kit
dump carry no musical meaning. The tests pin the placeholder names
verbatim so a future rename surfaces here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data.profile_model import StyleTrait
from rytm_randomizer.cockpit.wizard.sysex_analyzer import extract_kit_traits

pytestmark = pytest.mark.fast

# Placeholder trait names emitted by the Phase 2 sysex analyzer
# (mirror of :data:`sysex_analyzer._PLACEHOLDER_TRAIT_NAMES`; kept
# duplicated here so tests do not import private names).
_PLACEHOLDER_TRAIT_NAMES: tuple[str, ...] = (
    "_bytes_stddev",
    "_bytes_mean",
    "_bytes_density",
    "_bytes_distinct",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _by_name(traits: tuple[StyleTrait, ...]) -> dict[str, float]:
    return {t.name: t.value for t in traits}


def _is_neutral(traits: tuple[StyleTrait, ...]) -> bool:
    by_name = _by_name(traits)
    return all(by_name.get(n) == pytest.approx(0.5) for n in _PLACEHOLDER_TRAIT_NAMES)


# ---------------------------------------------------------------------------
# Single-file path
# ---------------------------------------------------------------------------


def test_known_bytes_fixture_produces_expected_traits(tmp_path: Path) -> None:
    """A fixture with deterministic bytes produces known trait values.

    Use a 4096-byte all-zero kit: byte mean = 0, stddev = 0,
    distinct = 1, length = 4096.

    Expected (CODE_REVIEW.md M5 — placeholder names):
      * _bytes_mean = 0 / 255 = 0.0
      * _bytes_stddev = 1.0 - (0 / 127.5) = 1.0 (zero variance == max value)
      * _bytes_density = 4096 / 8192 = 0.5
      * _bytes_distinct = 1 / 256 ~= 0.00390625
    """

    path = tmp_path / "all_zero.syx"
    path.write_bytes(bytes(4096))
    traits = extract_kit_traits(path)
    by_name = _by_name(traits)
    assert tuple(t.name for t in traits) == _PLACEHOLDER_TRAIT_NAMES
    assert by_name["_bytes_mean"] == pytest.approx(0.0)
    assert by_name["_bytes_stddev"] == pytest.approx(1.0)
    assert by_name["_bytes_density"] == pytest.approx(0.5)
    assert by_name["_bytes_distinct"] == pytest.approx(1.0 / 256.0)


def test_full_byte_range_fixture_drives_distinct_to_one(tmp_path: Path) -> None:
    """A file containing every byte value 0..255 exactly once.

    Statistics (CODE_REVIEW.md M5 — placeholder names):
      * mean = 127.5 -> _bytes_mean = 0.5
      * stddev = sqrt(((0..255 - 127.5)^2 mean)) ~= 73.9 -> _bytes_stddev = 1.0 - (73.9/127.5)
      * length = 256 -> _bytes_density = 256 / 8192 = 0.03125
      * distinct = 256 -> _bytes_distinct = 1.0
    """

    path = tmp_path / "full_range.syx"
    path.write_bytes(bytes(range(256)))
    traits = extract_kit_traits(path)
    by_name = _by_name(traits)
    assert by_name["_bytes_mean"] == pytest.approx(127.5 / 255.0)
    assert by_name["_bytes_distinct"] == pytest.approx(1.0)
    assert by_name["_bytes_density"] == pytest.approx(256.0 / 8192.0)
    # _bytes_stddev = 1 - (stddev / 127.5); stddev of uniform 0..255 ~= 73.9.
    # Just assert the inverted-stddev branch fires and lands < 1.
    assert 0.0 < by_name["_bytes_stddev"] < 1.0


def test_long_file_clamps_density_to_one(tmp_path: Path) -> None:
    """A kit larger than 8192 bytes saturates ``_bytes_density`` at 1.0."""

    path = tmp_path / "long.syx"
    path.write_bytes(b"\x00" * 16384)
    traits = extract_kit_traits(path)
    by_name = _by_name(traits)
    assert by_name["_bytes_density"] == pytest.approx(1.0)


def test_empty_file_returns_neutral_profile(tmp_path: Path) -> None:
    """An empty kit file carries no information -> neutral profile."""

    path = tmp_path / "empty.syx"
    path.write_bytes(b"")
    traits = extract_kit_traits(path)
    assert _is_neutral(traits)


def test_extreme_byte_split_clamps_stddev_at_zero(tmp_path: Path) -> None:
    """Half-zero / half-255 produces the maximum possible byte stddev (127.5).

    With ``stddev / 127.5`` exactly = 1, ``_bytes_stddev = 1 - 1 = 0.0`` --
    the inverted-stddev branch lands at the clamp's lower edge.
    """

    path = tmp_path / "split.syx"
    path.write_bytes(b"\x00" * 64 + b"\xff" * 64)
    traits = extract_kit_traits(path)
    by_name = _by_name(traits)
    assert by_name["_bytes_stddev"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Folder path
# ---------------------------------------------------------------------------


def test_folder_of_one_syx_matches_single_file(tmp_path: Path) -> None:
    """A folder containing one ``.syx`` produces the same traits as the bare file."""

    payload = bytes(range(256))
    single = tmp_path / "one.syx"
    single.write_bytes(payload)
    single_traits = extract_kit_traits(single)

    folder = tmp_path / "folder"
    folder.mkdir()
    (folder / "same.syx").write_bytes(payload)
    folder_traits = extract_kit_traits(folder)

    assert _by_name(folder_traits) == pytest.approx(_by_name(single_traits))


def test_folder_averages_per_file_results(tmp_path: Path) -> None:
    """Two files with very different stats produce the average traits."""

    folder = tmp_path / "kits"
    folder.mkdir()
    (folder / "a.syx").write_bytes(bytes(4096))  # all zeros
    (folder / "b.syx").write_bytes(b"\xff" * 4096)  # all 0xff

    traits = extract_kit_traits(folder)
    by_name = _by_name(traits)

    # File A: _bytes_mean=0, _bytes_stddev=1, _bytes_density=0.5, _bytes_distinct=1/256
    # File B: _bytes_mean=1, _bytes_stddev=1 (stddev=0 too), _bytes_density=0.5, _bytes_distinct=1/256
    # Averages: _bytes_mean=0.5, _bytes_stddev=1, _bytes_density=0.5, _bytes_distinct=1/256
    assert by_name["_bytes_mean"] == pytest.approx(0.5)
    assert by_name["_bytes_stddev"] == pytest.approx(1.0)
    assert by_name["_bytes_density"] == pytest.approx(0.5)
    assert by_name["_bytes_distinct"] == pytest.approx(1.0 / 256.0)


def test_folder_skips_non_syx_files(tmp_path: Path) -> None:
    """Non-``.syx`` files in the folder must be ignored."""

    folder = tmp_path / "mixed"
    folder.mkdir()
    (folder / "real.syx").write_bytes(bytes(4096))
    # Decoys: should be ignored entirely.
    (folder / "notes.txt").write_bytes(b"this is not sysex")
    (folder / "sample.wav").write_bytes(b"\xff" * 4096)
    (folder / "no_extension").write_bytes(b"\xff" * 4096)

    traits = extract_kit_traits(folder)
    expected = extract_kit_traits(folder / "real.syx")
    assert _by_name(traits) == pytest.approx(_by_name(expected))


def test_folder_matches_uppercase_extension(tmp_path: Path) -> None:
    """Extension match is case-insensitive (``*.SYX`` counts as ``*.syx``)."""

    folder = tmp_path / "case"
    folder.mkdir()
    (folder / "LOUD.SYX").write_bytes(bytes(4096))
    traits = extract_kit_traits(folder)
    expected = extract_kit_traits(folder / "LOUD.SYX")
    assert _by_name(traits) == pytest.approx(_by_name(expected))


def test_folder_with_only_non_syx_returns_neutral(tmp_path: Path) -> None:
    """A folder with no ``.syx`` matches returns the neutral profile."""

    folder = tmp_path / "no_kits"
    folder.mkdir()
    (folder / "notes.txt").write_bytes(b"hello")
    (folder / "sample.wav").write_bytes(b"\x00" * 100)
    traits = extract_kit_traits(folder)
    assert _is_neutral(traits)


def test_folder_skips_subdirectories(tmp_path: Path) -> None:
    """Sub-folders inside the kit folder are ignored (the analyzer is shallow)."""

    folder = tmp_path / "shallow"
    folder.mkdir()
    nested = folder / "deep"
    nested.mkdir()
    (nested / "ignored.syx").write_bytes(b"\xff" * 4096)
    # The shallow folder itself has no .syx -> neutral.
    traits = extract_kit_traits(folder)
    assert _is_neutral(traits)


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_missing_path_raises_filenotfounderror(tmp_path: Path) -> None:
    """A path that does not exist raises ``FileNotFoundError``."""

    with pytest.raises(FileNotFoundError, match="kit path does not exist"):
        extract_kit_traits(tmp_path / "does-not-exist.syx")


def test_non_path_argument_raises_valueerror() -> None:
    """The contract is ``path: pathlib.Path`` -- anything else is a bug.

    Raised as :class:`ValueError` (not :class:`TypeError`) so the wizard
    analyzer surface speaks a single error vocabulary --
    :class:`~rytm_randomizer.cockpit.wizard.errors.WizardSourcePathError`
    for path-policy violations + :class:`ValueError` for every other
    operator-supplied bad value (see ``L11`` reconcile in
    ``sysex_analyzer.extract_kit_traits``).
    """

    with pytest.raises(ValueError, match="path must be a pathlib.Path"):
        extract_kit_traits("string-path-not-allowed")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        extract_kit_traits(42)  # type: ignore[arg-type]


def test_non_file_non_dir_path_raises_valueerror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A path that exists but is neither file nor directory raises ``ValueError``.

    Synthesized via :func:`monkeypatch.setattr` on Path's predicates because
    creating a true device-special file is platform-specific and would
    require root.
    """

    fake = tmp_path / "weird"
    fake.write_bytes(b"")

    monkeypatch.setattr(Path, "is_file", lambda self: False)
    monkeypatch.setattr(Path, "is_dir", lambda self: False)

    with pytest.raises(ValueError, match="kit path is neither a file nor a directory"):
        extract_kit_traits(fake)

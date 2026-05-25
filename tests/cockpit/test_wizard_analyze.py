"""Tests for ``rytm_randomizer.cockpit.wizard.analyze`` -- the dispatcher.

The dispatcher routes :class:`InspirationSource` instances by their
``(kind, mode)`` pair to one of three analyzers
(:mod:`reference_analyzer`, :mod:`sysex_analyzer`, audio path). The
audio path wraps
:func:`rytm_randomizer.style_analysis.extractor.extract_from_audio`,
which requires ``librosa``; tests monkeypatch that import so the
dispatcher exercises end-to-end without the optional extra.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data.profile_model import StyleTrait
from rytm_randomizer.cockpit.wizard import analyze as analyze_mod
from rytm_randomizer.cockpit.wizard.analyze import (
    analyze_source,
    feature_report_to_traits,
)
from rytm_randomizer.cockpit.wizard.state import InspirationSource
from rytm_randomizer.cockpit.wizard.traits import WIZARD_TRAIT_NAMES

pytestmark = pytest.mark.fast

_FIXED_TS = datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


def _source(
    *,
    source_id: str = "01HXY5Q9PJM00000000000SOURCE",
    kind: str = "artist",
    mode: str = "reference",
    location: str = "Surgeon",
    display_name: str = "Surgeon",
) -> InspirationSource:
    return InspirationSource(
        source_id=source_id,
        kind=kind,  # type: ignore[arg-type]
        mode=mode,  # type: ignore[arg-type]
        location=location,
        display_name=display_name,
        added_at=_FIXED_TS,
    )


def _by_name(traits: tuple[StyleTrait, ...]) -> dict[str, float]:
    return {t.name: t.value for t in traits}


def _is_neutral(traits: tuple[StyleTrait, ...]) -> bool:
    by_name = _by_name(traits)
    return all(by_name.get(n) == pytest.approx(0.5) for n in WIZARD_TRAIT_NAMES)


class _FakeReport:
    """Minimal stand-in for :class:`FeatureReport` for projection tests.

    Carries only the fields :func:`feature_report_to_traits` reads -- the
    real :class:`FeatureReport` has more, but the projection is purely
    field-driven so a duck-typed stand-in suffices and keeps the tests
    free of the librosa-dependent extractor.
    """

    def __init__(
        self,
        *,
        low_end_weight: float = 0.0,
        tempo_stability: float = 0.0,
        spectral_brightness: float = 0.0,
        texture_noise: float = 0.0,
        percussion_density: float = 0.0,
    ) -> None:
        self.low_end_weight = low_end_weight
        self.tempo_stability = tempo_stability
        self.spectral_brightness = spectral_brightness
        self.texture_noise = texture_noise
        self.percussion_density = percussion_density


def _fake_extract_factory(report: _FakeReport):
    """Return a stub for ``extract_from_audio`` that always yields ``report``."""

    def _fake_extract(path: Path) -> _FakeReport:
        assert isinstance(path, Path)
        return report

    return _fake_extract


def _fake_extract_byname(per_file: dict[str, _FakeReport]):
    """Return a stub that maps ``path.name`` -> a per-file ``_FakeReport``."""

    def _fake_extract(path: Path) -> _FakeReport:
        return per_file[path.name]

    return _fake_extract


# ---------------------------------------------------------------------------
# feature_report_to_traits projection
# ---------------------------------------------------------------------------


def test_feature_report_projection_maps_fields_to_canonical_traits() -> None:
    """The 4-trait projection averages the documented FeatureReport fields."""

    report = _FakeReport(
        low_end_weight=0.8,
        tempo_stability=0.4,
        spectral_brightness=0.6,
        texture_noise=0.2,
        percussion_density=0.7,
    )
    traits = feature_report_to_traits(report)  # type: ignore[arg-type]
    by_name = _by_name(traits)
    assert tuple(t.name for t in traits) == WIZARD_TRAIT_NAMES
    assert by_name["rolling_low_end"] == pytest.approx((0.8 + 0.4) / 2.0)
    assert by_name["metallic_tension"] == pytest.approx((0.6 + 0.2) / 2.0)
    assert by_name["hat_density"] == pytest.approx(0.7)
    assert by_name["filter_motion"] == pytest.approx(1.0 - 0.4)


def test_feature_report_projection_clamps_into_unit_interval() -> None:
    """Out-of-range inputs are clamped to ``[0.0, 1.0]`` per trait."""

    report = _FakeReport(
        low_end_weight=1.4,
        tempo_stability=1.6,
        spectral_brightness=2.0,
        texture_noise=2.0,
        percussion_density=5.0,
    )
    traits = feature_report_to_traits(report)  # type: ignore[arg-type]
    by_name = _by_name(traits)
    assert by_name["rolling_low_end"] == pytest.approx(1.0)
    assert by_name["metallic_tension"] == pytest.approx(1.0)
    assert by_name["hat_density"] == pytest.approx(1.0)
    # tempo_stability=1.6 -> filter_motion = 1.0 - 1.6 = -0.6 -> clamp to 0.0
    assert by_name["filter_motion"] == pytest.approx(0.0)


def test_feature_report_projection_clamps_negative_inputs_to_zero() -> None:
    """Negative inputs land at the lower clamp edge."""

    report = _FakeReport(
        low_end_weight=-0.4,
        tempo_stability=-0.2,
        spectral_brightness=-0.3,
        texture_noise=-0.1,
        percussion_density=-1.0,
    )
    traits = feature_report_to_traits(report)  # type: ignore[arg-type]
    by_name = _by_name(traits)
    # (negative + negative)/2 = negative -> clamp to 0.0
    assert by_name["rolling_low_end"] == pytest.approx(0.0)
    assert by_name["metallic_tension"] == pytest.approx(0.0)
    assert by_name["hat_density"] == pytest.approx(0.0)
    # 1.0 - (-0.2) = 1.2 -> clamp to 1.0
    assert by_name["filter_motion"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Reference-mode dispatch
# ---------------------------------------------------------------------------


def test_reference_mode_routes_to_reference_analyzer() -> None:
    """``mode="reference"`` returns the curated reference lookup result."""

    source = _source(kind="artist", mode="reference", location="Surgeon")
    traits = analyze_source(source)
    by_name = _by_name(traits)
    assert by_name["rolling_low_end"] == pytest.approx(0.85)
    assert by_name["metallic_tension"] == pytest.approx(0.78)


def test_reference_mode_with_album_kind_still_routes_to_reference_lookup() -> None:
    """``mode="reference"`` wins over ``kind`` -- every kind+reference works."""

    for kind in ("artist", "album", "song"):
        source = _source(kind=kind, mode="reference", location="Daniel Avery")
        traits = analyze_source(source)
        by_name = _by_name(traits)
        # Daniel Avery curated entry: rolling_low_end=0.65, filter_motion=0.75
        assert by_name["rolling_low_end"] == pytest.approx(0.65)
        assert by_name["filter_motion"] == pytest.approx(0.75)


def test_reference_mode_unknown_name_returns_neutral_profile() -> None:
    """An unknown reference handle returns the neutral 4-trait profile."""

    source = _source(kind="artist", mode="reference", location="unknown artist xyz")
    traits = analyze_source(source)
    assert _is_neutral(traits)


# ---------------------------------------------------------------------------
# Kit-mode dispatch (file + folder)
# ---------------------------------------------------------------------------


def test_kit_kind_with_file_mode_routes_to_sysex_analyzer(tmp_path: Path) -> None:
    """``kind="kit", mode="file"`` reads bytes through the sysex analyzer.

    CODE_REVIEW.md M5: the sysex analyzer emits placeholder ``_bytes_*``
    trait names rather than the canonical wizard trait names because the
    byte statistics carry no musical meaning.
    """

    path = tmp_path / "kit.syx"
    path.write_bytes(bytes(4096))
    source = _source(kind="kit", mode="file", location=str(path), display_name="kit.syx")
    traits = analyze_source(source)
    by_name = _by_name(traits)
    # all-zero file -> _bytes_mean 0.0, _bytes_stddev 1.0, _bytes_density 0.5
    assert by_name["_bytes_mean"] == pytest.approx(0.0)
    assert by_name["_bytes_stddev"] == pytest.approx(1.0)
    assert by_name["_bytes_density"] == pytest.approx(0.5)


def test_kit_kind_with_folder_mode_routes_to_sysex_analyzer(tmp_path: Path) -> None:
    """``kind="kit", mode="folder"`` averages every ``.syx`` in the folder."""

    folder = tmp_path / "kits"
    folder.mkdir()
    (folder / "a.syx").write_bytes(bytes(4096))
    (folder / "b.syx").write_bytes(b"\xff" * 4096)
    source = _source(kind="kit", mode="folder", location=str(folder), display_name="kits/")
    traits = analyze_source(source)
    by_name = _by_name(traits)
    # average of all-zero (_bytes_mean=0.0) and all-0xff (_bytes_mean=1.0) -> 0.5
    assert by_name["_bytes_mean"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Audio-mode dispatch (file + folder), librosa-stubbed
# ---------------------------------------------------------------------------


@pytest.fixture
def stubbed_extract(monkeypatch: pytest.MonkeyPatch):
    """Yield a callable that installs a fake ``extract_from_audio`` stub.

    Returns a setter so each test can register its own per-test fake
    (single-report, per-file-mapped, etc.). Patching is done on the
    dispatcher module's bound name so the test does not need to worry
    about ``style_analysis`` having a private re-export.
    """

    def install(stub):
        monkeypatch.setattr(analyze_mod, "extract_from_audio", stub)

    return install


def test_audio_kind_with_file_mode_routes_through_extract_from_audio(
    stubbed_extract, tmp_path: Path
) -> None:
    """``kind in {"sound","song","album"}, mode="file"`` calls the extractor."""

    report = _FakeReport(
        low_end_weight=0.6,
        tempo_stability=0.4,
        spectral_brightness=0.5,
        texture_noise=0.3,
        percussion_density=0.7,
    )
    stubbed_extract(_fake_extract_factory(report))

    audio_path = tmp_path / "track.wav"
    audio_path.write_bytes(b"")
    source = _source(kind="song", mode="file", location=str(audio_path), display_name="track.wav")
    traits = analyze_source(source)
    by_name = _by_name(traits)
    # Mirror feature_report_to_traits arithmetic.
    assert by_name["rolling_low_end"] == pytest.approx(0.5)
    assert by_name["metallic_tension"] == pytest.approx(0.4)
    assert by_name["hat_density"] == pytest.approx(0.7)
    assert by_name["filter_motion"] == pytest.approx(0.6)


def test_audio_kind_with_folder_mode_iterates_matching_files(
    stubbed_extract, tmp_path: Path
) -> None:
    """Folder mode iterates every audio extension and averages the traits."""

    per_file = {
        "a.wav": _FakeReport(
            low_end_weight=0.8,
            tempo_stability=0.4,
            spectral_brightness=0.2,
            texture_noise=0.2,
            percussion_density=0.6,
        ),
        "b.flac": _FakeReport(
            low_end_weight=0.4,
            tempo_stability=0.6,
            spectral_brightness=0.8,
            texture_noise=0.4,
            percussion_density=0.2,
        ),
    }
    stubbed_extract(_fake_extract_byname(per_file))

    folder = tmp_path / "audio"
    folder.mkdir()
    for name in per_file:
        (folder / name).write_bytes(b"")
    # Decoys: should be skipped by the dispatcher's extension filter.
    (folder / "notes.txt").write_bytes(b"")
    (folder / "kit.syx").write_bytes(b"\x00" * 32)

    source = _source(kind="album", mode="folder", location=str(folder), display_name="audio/")
    traits = analyze_source(source)
    by_name = _by_name(traits)

    # Per-file projections:
    # a.wav -> rolling=(0.8+0.4)/2=0.6  metallic=(0.2+0.2)/2=0.2  hats=0.6  motion=1-0.4=0.6
    # b.flac -> rolling=(0.4+0.6)/2=0.5 metallic=(0.8+0.4)/2=0.6  hats=0.2  motion=1-0.6=0.4
    # Averages: rolling=0.55 metallic=0.4 hats=0.4 motion=0.5
    assert by_name["rolling_low_end"] == pytest.approx(0.55)
    assert by_name["metallic_tension"] == pytest.approx(0.4)
    assert by_name["hat_density"] == pytest.approx(0.4)
    assert by_name["filter_motion"] == pytest.approx(0.5)


def test_audio_folder_matches_every_supported_extension(stubbed_extract, tmp_path: Path) -> None:
    """``.wav``, ``.mp3``, ``.flac``, ``.aif``, ``.aiff`` all count as audio.

    Each filename is treated case-insensitively (``.WAV`` matches).
    """

    extensions = ("wav", "WAV", "mp3", "flac", "aif", "aiff")
    report = _FakeReport(
        low_end_weight=0.5,
        tempo_stability=0.5,
        spectral_brightness=0.5,
        texture_noise=0.5,
        percussion_density=0.5,
    )
    stubbed_extract(_fake_extract_factory(report))

    folder = tmp_path / "every-ext"
    folder.mkdir()
    for ext in extensions:
        (folder / f"clip.{ext}").write_bytes(b"")

    source = _source(
        kind="sound",
        mode="folder",
        location=str(folder),
        display_name="every-ext/",
    )
    traits = analyze_source(source)
    by_name = _by_name(traits)
    # Every file projects to the same trait values -> the average equals
    # the single-file projection.
    assert by_name["rolling_low_end"] == pytest.approx(0.5)
    assert by_name["metallic_tension"] == pytest.approx(0.5)
    assert by_name["hat_density"] == pytest.approx(0.5)
    assert by_name["filter_motion"] == pytest.approx(0.5)


def test_audio_folder_with_no_matches_returns_neutral_profile(
    stubbed_extract, tmp_path: Path
) -> None:
    """A folder with no audio files returns the neutral profile.

    The stub MUST NOT be invoked -- if it is, the test will fail loudly.
    """

    def fail_if_called(_path: Path) -> _FakeReport:
        raise AssertionError("extract_from_audio should not be called for empty folder")

    stubbed_extract(fail_if_called)

    folder = tmp_path / "no-audio"
    folder.mkdir()
    (folder / "notes.txt").write_bytes(b"")
    (folder / "kit.syx").write_bytes(b"\x00" * 32)

    source = _source(kind="song", mode="folder", location=str(folder), display_name="no-audio/")
    traits = analyze_source(source)
    assert _is_neutral(traits)


def test_audio_file_missing_path_raises_filenotfounderror(tmp_path: Path) -> None:
    """A missing audio path raises ``FileNotFoundError`` before the extractor."""

    source = _source(
        kind="song",
        mode="file",
        location=str(tmp_path / "missing.wav"),
        display_name="missing.wav",
    )
    with pytest.raises(FileNotFoundError, match="audio path does not exist"):
        analyze_source(source)


def test_audio_path_neither_file_nor_dir_raises_valueerror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A path that exists but is neither file nor dir raises ``ValueError``."""

    weird = tmp_path / "weird"
    weird.write_bytes(b"")
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    monkeypatch.setattr(Path, "is_dir", lambda self: False)

    source = _source(kind="song", mode="file", location=str(weird), display_name="weird")
    with pytest.raises(ValueError, match="audio path is neither a file nor a directory"):
        analyze_source(source)


# ---------------------------------------------------------------------------
# Dispatcher contract: unsupported (kind, mode) combinations
# ---------------------------------------------------------------------------


def test_unsupported_kind_with_file_mode_raises_valueerror(tmp_path: Path) -> None:
    """``kind="artist", mode="file"`` is rejected as malformed input.

    The state layer prevents this in practice (artists only use
    ``mode="reference"``), but the dispatcher is defensive.
    """

    real_file = tmp_path / "anything.bin"
    real_file.write_bytes(b"")
    source = _source(kind="artist", mode="file", location=str(real_file), display_name="anything")
    with pytest.raises(ValueError, match="unsupported \\(kind, mode\\) combination"):
        analyze_source(source)

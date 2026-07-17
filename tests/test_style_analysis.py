"""Tests for the WS-V style analysis package (Layer 1 - measurement).

The style analysis package is a leaf-ish module: it imports
:mod:`rytm_randomizer.guardrails.schema` for the
:class:`~rytm_randomizer.guardrails.schema.SourceType` and
:class:`~rytm_randomizer.guardrails.schema.Confidence` enums, lazy-imports
``librosa`` and ``numpy`` only when an audio path is exercised, and has
no other dependencies.

These tests cover:

* :class:`FeatureReport` schema, immutability, type discipline.
* :func:`compute_feature_report_hash` determinism, content sensitivity,
  exclusion of the report's own ``content_hash`` field from its input,
  type-rejection branches.
* :func:`extract_from_description` end-to-end without ``librosa``.
* :func:`extract_from_partial` empty-input fallback (no librosa).
* :func:`analyze_library` empty-directory fallback (no librosa).
* Lazy-import discipline: a missing-librosa audio call surfaces a clear
  :class:`StyleAnalysisDependencyError`.
* librosa-dependent paths: gated behind ``pytest.importorskip``.
* Package re-export surface mirrors :func:`__init__.__all__`.

The librosa-gated tests pass when the ``style`` optional extra is
installed and skip cleanly otherwise.
"""

from __future__ import annotations

import dataclasses
import hashlib
import sys
from pathlib import Path

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import (
    FeatureReport,
    StyleAnalysisDependencyError,
    analyze_audio,
    analyze_library,
    compute_feature_report_hash,
    extract_from_audio,
    extract_from_description,
    extract_from_partial,
)
from rytm_randomizer.style_analysis import extractor as extractor_module
from rytm_randomizer.style_analysis import feature_report as feature_report_module
from rytm_randomizer.style_analysis import library as library_module

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _build_report(*, content_hash: str = "") -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=128.0,
        tempo_stability=0.95,
        kick_density=0.6,
        percussion_density=0.5,
        low_end_weight=0.7,
        spectral_brightness=0.3,
        texture_noise=0.2,
        energy_arc=(0.1, 0.3, 0.5, 0.7, 0.8, 0.7, 0.5, 0.2),
        content_hash=content_hash,
        derived_at="2026-05-15T12:00:00Z",
    )


# ---------------------------------------------------------------------------
# Schema / immutability
# ---------------------------------------------------------------------------


def test_feature_report_is_frozen():
    report = _build_report()
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.bpm = 130.0  # type: ignore[misc]


def test_feature_report_round_trips_every_field():
    report = _build_report(content_hash="placeholder")
    settled = dataclasses.replace(report, content_hash=compute_feature_report_hash(report))

    assert settled.source_type is SourceType.SINGLE_TRACK
    assert settled.confidence is Confidence.HIGH
    assert settled.bpm == 128.0
    assert settled.tempo_stability == 0.95
    assert settled.kick_density == 0.6
    assert settled.percussion_density == 0.5
    assert settled.low_end_weight == 0.7
    assert settled.spectral_brightness == 0.3
    assert settled.texture_noise == 0.2
    assert settled.energy_arc == (0.1, 0.3, 0.5, 0.7, 0.8, 0.7, 0.5, 0.2)
    assert settled.derived_at == "2026-05-15T12:00:00Z"
    assert isinstance(settled.energy_arc, tuple)


def test_feature_report_energy_arc_is_tuple():
    report = _build_report()
    # tuples in place of lists per house style.
    assert isinstance(report.energy_arc, tuple)


# ---------------------------------------------------------------------------
# Content hash
# ---------------------------------------------------------------------------


def test_compute_feature_report_hash_is_deterministic():
    a = _build_report()
    b = _build_report()
    assert compute_feature_report_hash(a) == compute_feature_report_hash(b)


def test_compute_feature_report_hash_excludes_own_field():
    empty = _build_report(content_hash="")
    digest = compute_feature_report_hash(empty)
    inlined = _build_report(content_hash=digest)
    assert compute_feature_report_hash(inlined) == digest


def test_compute_feature_report_hash_returns_lowercase_hex_sha256():
    digest = compute_feature_report_hash(_build_report())
    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)


def test_compute_feature_report_hash_sensitive_to_bpm_change():
    baseline = _build_report()
    altered = dataclasses.replace(baseline, bpm=130.0)
    assert compute_feature_report_hash(baseline) != compute_feature_report_hash(altered)


def test_compute_feature_report_hash_sensitive_to_source_type():
    baseline = _build_report()
    altered = dataclasses.replace(baseline, source_type=SourceType.FOLDER_LIBRARY)
    assert compute_feature_report_hash(baseline) != compute_feature_report_hash(altered)


def test_compute_feature_report_hash_sensitive_to_energy_arc():
    baseline = _build_report()
    altered_arc = list(baseline.energy_arc)
    altered_arc[0] = 0.99
    altered = dataclasses.replace(baseline, energy_arc=tuple(altered_arc))
    assert compute_feature_report_hash(baseline) != compute_feature_report_hash(altered)


def test_to_canonical_handles_primitive_passthrough():
    # Each primitive arm of the canonicalizer (covers branch lines).
    assert feature_report_module._to_canonical("hello") == "hello"
    assert feature_report_module._to_canonical(7) == 7
    assert feature_report_module._to_canonical(1.5) == 1.5
    assert feature_report_module._to_canonical(True) is True
    assert feature_report_module._to_canonical(None) is None


def test_to_canonical_rejects_unsupported_type():
    @dataclasses.dataclass(frozen=True)
    class _Holder:
        blob: object

    with pytest.raises(TypeError):
        feature_report_module._to_canonical(_Holder(blob=object()))


def test_to_canonical_rejects_dataclass_type_object():
    # The dataclass-class itself (not an instance) goes through the error
    # arm: ``is_dataclass`` is True but ``isinstance(value, type)`` is also
    # True, so the guard routes it past the recursion.
    with pytest.raises(TypeError):
        feature_report_module._to_canonical(FeatureReport)


def test_to_canonical_handles_list_branch():
    @dataclasses.dataclass(frozen=True)
    class _Holder:
        values: list

    canonical = feature_report_module._to_canonical(_Holder(values=[1, 2, 3]))
    assert canonical == {"values": [1, 2, 3]}


def test_to_canonical_handles_enum_branch():
    canonical = feature_report_module._to_canonical(SourceType.SINGLE_TRACK)
    assert canonical == "SINGLE_TRACK"


def test_to_canonical_handles_mapping_branch():
    canonical = feature_report_module._to_canonical({"k": "v", 1: 2})
    assert canonical == {"k": "v", "1": 2}


# ---------------------------------------------------------------------------
# extract_from_description (no librosa required)
# ---------------------------------------------------------------------------


def test_extract_from_description_returns_low_confidence():
    report = extract_from_description("rolling hypnotic techno")
    assert report.confidence is Confidence.LOW
    assert report.source_type is SourceType.STYLE_DESCRIPTION_ONLY


def test_extract_from_description_does_not_require_librosa():
    # Snapshot sys.modules state, confirm the call does NOT import librosa.
    had_librosa = "librosa" in sys.modules
    _ = extract_from_description("just a description")
    if not had_librosa:
        assert "librosa" not in sys.modules


def test_extract_from_description_produces_well_formed_report():
    report = extract_from_description("rolling techno, dark")
    # All numeric fields are well-formed (no NaN, in-range).
    assert isinstance(report.bpm, float)
    assert 0.0 <= report.tempo_stability <= 1.0
    assert 0.0 <= report.kick_density <= 1.0
    assert 0.0 <= report.percussion_density <= 1.0
    assert 0.0 <= report.low_end_weight <= 1.0
    assert 0.0 <= report.spectral_brightness <= 1.0
    assert 0.0 <= report.texture_noise <= 1.0
    assert len(report.energy_arc) == 8
    assert all(0.0 <= v <= 1.0 for v in report.energy_arc)
    # Hash is settled.
    assert report.content_hash == compute_feature_report_hash(report)


def test_extract_from_description_accepts_explicit_source_type():
    report = extract_from_description(
        "user release library", source_type=SourceType.USER_RELEASE_LIBRARY
    )
    assert report.source_type is SourceType.USER_RELEASE_LIBRARY


def test_extract_from_description_rejects_non_string_text():
    with pytest.raises(TypeError):
        extract_from_description(123)  # type: ignore[arg-type]


def test_extract_from_description_rejects_non_enum_source_type():
    with pytest.raises(TypeError):
        extract_from_description("foo", source_type="SINGLE_TRACK")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# extract_from_partial - empty paths fallback
# ---------------------------------------------------------------------------


def test_extract_from_partial_empty_paths_returns_medium_confidence():
    report = extract_from_partial([], notes="user description only")
    assert report.confidence is Confidence.MEDIUM
    # All numeric fields zero placeholders.
    assert report.bpm == 0.0
    assert report.content_hash == compute_feature_report_hash(report)


def test_extract_from_partial_rejects_non_list_paths():
    with pytest.raises(TypeError):
        extract_from_partial("not-a-list", notes="x")  # type: ignore[arg-type]


def test_extract_from_partial_rejects_non_string_notes():
    with pytest.raises(TypeError):
        extract_from_partial([], notes=123)  # type: ignore[arg-type]


def test_extract_from_partial_rejects_non_path_entries():
    with pytest.raises(TypeError):
        extract_from_partial(["not-a-path"], notes="x")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# analyze_library - empty directory fallback (no librosa)
# ---------------------------------------------------------------------------


def test_analyze_library_empty_directory_returns_low_confidence(tmp_path: Path):
    report = analyze_library(tmp_path)
    assert report.confidence is Confidence.LOW
    assert report.source_type is SourceType.FOLDER_LIBRARY
    assert report.content_hash == compute_feature_report_hash(report)


def test_analyze_library_nonexistent_directory_returns_low_confidence(tmp_path: Path):
    missing = tmp_path / "does_not_exist"
    report = analyze_library(missing)
    assert report.confidence is Confidence.LOW
    assert report.source_type is SourceType.FOLDER_LIBRARY


def test_analyze_library_rejects_non_path():
    with pytest.raises(TypeError):
        analyze_library("not-a-path")  # type: ignore[arg-type]


def test_analyze_library_directory_with_only_non_audio_files_returns_low_confidence(
    tmp_path: Path,
):
    # Confirms the extension filter: a text file is not measured.
    (tmp_path / "notes.txt").write_text("session notes")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n")
    report = analyze_library(tmp_path)
    assert report.confidence is Confidence.LOW


# ---------------------------------------------------------------------------
# Lazy-import discipline
# ---------------------------------------------------------------------------


def test_require_librosa_raises_dependency_error_when_librosa_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    """Direct exercise of the lazy-import error arm.

    The helper :func:`_require_librosa` is the gate that converts a
    missing optional dependency into a clear
    :class:`StyleAnalysisDependencyError`. When librosa is already
    installed in the environment, we force the import to fail by
    stubbing ``builtins.__import__`` for the ``librosa`` name -- so this
    test runs regardless of whether the ``style`` extra is present.
    """

    import builtins

    real_import = builtins.__import__

    def _block_librosa(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "librosa":
            raise ImportError(f"forced-missing: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_librosa)

    with pytest.raises(StyleAnalysisDependencyError):
        extractor_module._require_librosa()


def test_require_librosa_raises_dependency_error_when_numpy_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    """The second import (numpy) is also in the gated try-block.

    Block only ``numpy`` to cover the line that imports it -- librosa is
    let through (or pretended through with a fake module) so the import
    succeeds and execution reaches the ``import numpy`` line, where the
    block fires.
    """

    import builtins
    import sys
    import types

    # If librosa is not installed, inject a sentinel module so the first
    # import succeeds. We restore sys.modules state on test teardown via
    # monkeypatch.
    if "librosa" not in sys.modules:
        fake_librosa = types.ModuleType("librosa")
        monkeypatch.setitem(sys.modules, "librosa", fake_librosa)

    real_import = builtins.__import__

    def _block_numpy(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "numpy":
            raise ImportError("forced-missing: numpy")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_numpy)

    with pytest.raises(StyleAnalysisDependencyError):
        extractor_module._require_librosa()


def test_extract_from_audio_rejects_non_path():
    with pytest.raises(TypeError):
        extract_from_audio("path.wav")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        analyze_audio("path.wav")  # type: ignore[arg-type]


def test_analyze_audio_hashes_and_measures_one_immutable_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = b"original-audio-bytes"
    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(original)
    observed_snapshots: list[Path] = []

    def measure(snapshot: Path):
        observed_snapshots.append(snapshot)
        assert snapshot != audio_path
        assert snapshot.read_bytes() == original
        audio_path.write_bytes(b"concurrent-replacement")
        return {
            "bpm": 126.0,
            "tempo_stability": 0.9,
            "kick_density": 0.4,
            "percussion_density": 0.5,
            "low_end_weight": 0.6,
            "spectral_brightness": 0.7,
            "texture_noise": 0.2,
            "energy_arc": (0.2, 0.4, 0.6, 0.8),
            "duration": 0.5,
            "attack": 0.1,
            "decay": 0.2,
            "sustain": 0.3,
            "tail": 0.4,
            "spectral_flatness": 0.2,
            "noise": 0.2,
            "harmonicity": 0.8,
            "transient": 0.4,
            "modulation": 0.3,
        }

    monkeypatch.setattr(extractor_module, "_measure_audio_features", measure)
    analysis = analyze_audio(audio_path)

    assert analysis.audio_sha256 == hashlib.sha256(original).hexdigest()
    assert len(observed_snapshots) == 1
    assert not observed_snapshots[0].exists()


def test_audio_synthesis_measurement_helpers_cover_bounds() -> None:
    assert extractor_module._audio_safe_ratio(1.0, 0.0) == 0.0
    assert extractor_module._audio_safe_ratio(1.0, 2.0) == 0.5
    assert extractor_module._audio_mean([]) == 0.0
    assert extractor_module._audio_mean([1.0, 3.0]) == 2.0
    assert extractor_module._audio_standard_deviation([], 0.0) == 0.0
    assert extractor_module._audio_standard_deviation([1.0, 3.0], 2.0) == 1.0
    assert extractor_module._audio_decay_frames([1.0, 0.2], 0, 1.0) == 1
    assert extractor_module._audio_decay_frames([1.0, 0.9], 0, 1.0) == 1
    assert extractor_module._audio_window_level([], 0.0, 0.4, 0.8) == 0.0
    assert extractor_module._audio_window_level([1.0, 0.5], 1.0, 0.4, 1.0) == 0.75
    assert extractor_module._first_finite([]) == 0.0
    assert extractor_module._first_finite([float("nan")]) == 0.0
    assert extractor_module._first_finite([123.0]) == 123.0
    assert extractor_module._tempo_stability([]) == 0.0
    assert extractor_module._tempo_stability([0.0, 1.0, 2.0]) == 1.0
    assert extractor_module._tempo_stability([1.0, 1.0, 1.0]) == 0.0
    assert extractor_module._spectral_weights([], [], onset_count=0, percussion_density=0.5) == (
        0.0,
        0.0,
    )
    assert extractor_module._spectral_weights(
        [[3.0], [1.0]],
        [100.0, 1000.0],
        onset_count=1,
        percussion_density=0.5,
    ) == (0.75, 0.75)
    assert extractor_module._spectral_weights(
        [[1.0]], [100.0], onset_count=0, percussion_density=0.5
    ) == (1.0, 0.0)
    assert extractor_module._energy_arc([0.5]) == (0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert extractor_module._energy_arc([0.0] * 8) == (0.0,) * 8
    assert extractor_module._energy_arc([float(value) for value in range(1, 9)])[-1] == 1.0


def test_audio_array_conversion_and_empty_measurement_defenses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeArray:
        def __init__(self, value: object) -> None:
            self.value = value

        def reshape(self, *_shape: int):
            return self

        def tolist(self) -> object:
            return self.value

    class FakeNumpy:
        def asarray(self, value: object) -> FakeArray:
            return FakeArray(value)

    class EmptyLibrosa:
        def load(self, *_args: object, **_kwargs: object) -> tuple[list[float], int]:
            return [], 22_050

    numpy = FakeNumpy()
    with pytest.raises(TypeError, match="array must serialize"):
        extractor_module._flat_float_values(numpy, 1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="matrix must serialize"):
        extractor_module._matrix_float_values(numpy, 1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="matrix row"):
        extractor_module._matrix_float_values(numpy, [1.0])  # type: ignore[arg-type]

    monkeypatch.setattr(
        extractor_module,
        "_require_librosa",
        lambda: (EmptyLibrosa(), numpy),
    )
    measurements = extractor_module._measure_audio_features(tmp_path / "empty.wav")
    assert measurements["energy_arc"] == (0.0,) * 8
    assert measurements["harmonicity"] == 0.0


def test_extract_from_audio_raises_dependency_error_when_librosa_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Without ``librosa`` installed, audio extraction must surface a clear error.

    Simulated by injecting a sentinel ``ImportError`` into the lazy-import
    path -- so this test runs regardless of whether ``librosa`` is
    actually installed.
    """

    def _explode() -> tuple[object, object]:
        raise StyleAnalysisDependencyError(
            "Audio feature extraction requires the 'style' optional extra."
        )

    monkeypatch.setattr(extractor_module, "_require_librosa", _explode)

    fake_audio = tmp_path / "fake.wav"
    fake_audio.write_bytes(b"not really audio")

    with pytest.raises(StyleAnalysisDependencyError):
        extract_from_audio(fake_audio)


def test_extract_from_partial_raises_dependency_error_with_audio_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """``extract_from_partial`` with audio paths must lazy-load librosa."""

    def _explode() -> tuple[object, object]:
        raise StyleAnalysisDependencyError("missing dependency")

    monkeypatch.setattr(extractor_module, "_require_librosa", _explode)
    fake_audio = tmp_path / "fake.wav"
    fake_audio.write_bytes(b"x")
    with pytest.raises(StyleAnalysisDependencyError):
        extract_from_partial([fake_audio], notes="x")


def test_analyze_library_raises_dependency_error_with_audio_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """``analyze_library`` with audio files in directory must lazy-load librosa."""

    # Place an audio file so the library is non-empty.
    (tmp_path / "a.wav").write_bytes(b"x")

    def _explode() -> tuple[object, object]:
        raise StyleAnalysisDependencyError("missing dependency")

    # Library imports the helper from extractor; patch via the library
    # module-level name.
    monkeypatch.setattr(library_module, "_require_librosa", _explode)
    with pytest.raises(StyleAnalysisDependencyError):
        analyze_library(tmp_path)


def test_normalize_unit_clamps_below_zero():
    assert extractor_module._normalize_unit(-0.5) == 0.0


def test_normalize_unit_clamps_above_one():
    assert extractor_module._normalize_unit(1.5) == 1.0


def test_normalize_unit_passes_through_in_range():
    assert extractor_module._normalize_unit(0.42) == 0.42


# ---------------------------------------------------------------------------
# Package re-export surface
# ---------------------------------------------------------------------------


def test_package_reexports_public_surface():
    from rytm_randomizer import style_analysis

    expected = {
        "AnalogFourTrackBlueprint",
        "AudioFeatureAnalysis",
        "Confidence",
        "FeatureReport",
        "ReferenceStyleBlueprint",
        "ReferenceTrait",
        "RytmPadBlueprint",
        "SourceType",
        "StyleAnalysisDependencyError",
        "analyze_library",
        "analyze_audio",
        "build_reference_style_blueprint",
        "compute_feature_report_hash",
        "extract_from_audio",
        "extract_from_description",
        "extract_from_partial",
        "reference_style_blueprint_to_dict",
    }
    assert expected == set(style_analysis.__all__)
    for name in expected:
        assert hasattr(style_analysis, name)


def test_package_import_does_not_pull_librosa_into_sys_modules():
    # If librosa is already installed by the dev environment we cannot
    # un-import it cleanly mid-session; the subprocess-level guarantee
    # is enforced by tests/architecture/test_no_side_effects.py. This
    # in-process test is the secondary gate: in a clean Python (the
    # default test invocation), librosa must not be present after import.
    if "librosa" in sys.modules:
        pytest.skip("librosa already imported by test environment")
    import rytm_randomizer.style_analysis  # noqa: F401

    assert "librosa" not in sys.modules


# ---------------------------------------------------------------------------
# librosa-gated tests (real audio feature extraction)
# ---------------------------------------------------------------------------


def _write_sine_wave(path: Path, frequency: float, sr: int, duration: float) -> None:
    """Write a deterministic sine wave WAV file to ``path``.

    Used only by the librosa-gated tests; lazy-imports ``numpy`` so this
    helper does not affect module-level imports of the test file.
    """

    import wave

    import numpy as np  # local import - matches the lazy discipline

    t = np.arange(0, int(sr * duration)) / float(sr)
    samples = (0.5 * np.sin(2.0 * np.pi * frequency * t)).astype(np.float32)
    pcm = (samples * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def test_extract_from_audio_runs_on_synthetic_signal(tmp_path: Path):
    """Real audio extraction -- gated on ``librosa`` being available."""

    pytest.importorskip("librosa")
    pytest.importorskip("numpy")

    wav = tmp_path / "sine.wav"
    _write_sine_wave(wav, frequency=440.0, sr=22050, duration=2.0)

    analysis = analyze_audio(wav)
    report = analysis.feature_report

    assert report.source_type is SourceType.SINGLE_TRACK
    assert report.confidence is Confidence.HIGH
    assert len(report.energy_arc) == 8
    # The hash is settled.
    assert report.content_hash == compute_feature_report_hash(report)
    assert analysis.audio_sha256 == hashlib.sha256(wav.read_bytes()).hexdigest()
    assert 0.0 <= analysis.harmonicity <= 1.0
    assert 0.0 <= analysis.modulation <= 1.0
    # Determinism: a second extraction yields the same hash modulo
    # ``derived_at`` (which is wall-clock). The non-time fields must match.
    second = extract_from_audio(wav)
    assert second.bpm == report.bpm
    assert second.tempo_stability == report.tempo_stability
    assert second.spectral_brightness == report.spectral_brightness
    assert second.energy_arc == report.energy_arc


def test_analyze_library_runs_on_synthetic_signals(tmp_path: Path):
    """Library aggregation -- gated on ``librosa`` being available."""

    pytest.importorskip("librosa")
    pytest.importorskip("numpy")

    _write_sine_wave(tmp_path / "a.wav", frequency=440.0, sr=22050, duration=1.0)
    _write_sine_wave(tmp_path / "b.wav", frequency=880.0, sr=22050, duration=1.0)

    report = analyze_library(tmp_path)
    assert report.source_type is SourceType.FOLDER_LIBRARY
    assert report.confidence is Confidence.HIGH
    assert report.content_hash == compute_feature_report_hash(report)


def test_extract_from_partial_runs_on_synthetic_signal(tmp_path: Path):
    """Partial extraction -- gated on ``librosa`` being available."""

    pytest.importorskip("librosa")
    pytest.importorskip("numpy")

    wav = tmp_path / "a.wav"
    _write_sine_wave(wav, frequency=220.0, sr=22050, duration=1.0)

    report = extract_from_partial([wav], notes="rolling description")
    assert report.confidence is Confidence.MEDIUM
    assert len(report.energy_arc) == 8

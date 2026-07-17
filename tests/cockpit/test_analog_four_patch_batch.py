"""Guarded audio-to-candidate Analog Four batch export tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis.analog_four_patch_genome import (
    AnalogFourPatchGenome,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from rytm_randomizer.style_analysis.feature_report import (
    FeatureReport,
    compute_feature_report_hash,
)

pytestmark = pytest.mark.fast

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "analog_four_saved_kit"
SOURCE_KIT = FIXTURE_DIR / "filter2_res_000_source.syx"
AUDIO_BYTES = b"sanitized-audio-reference-for-mocked-inference\n"
EXPECTED_FILENAMES = (
    "a4-t2-c01-closest-reference.syx",
    "a4-t2-c01-closest-reference.json",
    "a4-t2-c02-brighter-sync.syx",
    "a4-t2-c02-brighter-sync.json",
    "a4-t2-c03-noisy-texture.syx",
    "a4-t2-c03-noisy-texture.json",
    "a4-t2-c04-rounder-bass.syx",
    "a4-t2-c04-rounder-bass.json",
    "a4-t2-audio-patch-batch.json",
)
EXPECTED_SYSEX_SHA256 = (
    "2f6d97445535a1eb1f4b54e234d7b8d96b9c646c2f611a99f0e6e06a39980835",
    "16aee178243000a52cad0031429ca9768924e37c3989d1ad22c757cb7c266847",
    "68e6049f0cd81ad0709ea1e0aff42a11300c4b43e87a5392460fb30d71788788",
    "e1384abed1898010debfedf64386dd45485493cabb28b05f2e5bcd1c72096702",
)
EXPECTED_SIDECAR_SHA256 = (
    "c6adb64e0e75b3c8121c8ffbe53a5377b2c5c7bf538480a1606cebbaf4a184fe",
    "cb096a29460c4c69c5b48e8b587b6bc9c7f525d55358f62063655ba070c177ab",
    "c95ab3e372e827385dab0f57d869f5cc80b13d4653e1bd31350776d5cfecf64c",
    "2e73a3ef5fa93fa4b10dceed64003afbdcd31d2722b32d045abfbcfda0e35648",
)
EXPECTED_MANIFEST_SHA256 = "ec8003ac1ffee60965d1dcc2b5e3f7ca2082da7961d962bf72f2152d71097b28"


def _feature_report() -> FeatureReport:
    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=126.0,
        tempo_stability=0.92,
        kick_density=0.48,
        percussion_density=0.63,
        low_end_weight=0.71,
        spectral_brightness=0.44,
        texture_noise=0.22,
        energy_arc=(0.2, 0.4, 0.7, 0.5),
        content_hash="",
        derived_at="2026-07-16T00:00:00Z",
    )
    return replace(report, content_hash=compute_feature_report_hash(report))


def _inference(*, track: int, candidate_count: int) -> object:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch import _AudioInference

    report = _feature_report()
    genome = build_analog_four_patch_genome(
        report,
        track=track,
        candidate_count=candidate_count,
    )
    return _AudioInference(
        feature_report=report,
        genome=genome,
        audio_features_payload={
            "audio_sha256": "a" * 64,
            "brightness": 0.44,
            "noise": 0.22,
        },
        genome_payload=analog_four_patch_genome_to_dict(genome),
    )


@pytest.fixture
def mocked_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    def fake_build(
        _audio_path: Path,
        *,
        track: int,
        candidate_count: int,
    ) -> object:
        return _inference(track=track, candidate_count=candidate_count)

    monkeypatch.setattr(batch, "_build_audio_inference", fake_build)


def _export(tmp_path: Path, *, candidate_count: int = 4, overwrite: bool = False):
    from rytm_randomizer.cockpit.export.analog_four_patch_batch import (
        export_analog_four_audio_patch_batch,
    )

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)
    return export_analog_four_audio_patch_batch(
        audio_path=audio_path,
        source_kit_path=SOURCE_KIT,
        output_dir=tmp_path / "batch",
        track=2,
        candidate_count=candidate_count,
        overwrite=overwrite,
    )


def test_export_audio_patch_batch_writes_four_pinned_candidates_and_manifest(
    tmp_path: Path,
    mocked_inference: None,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch import (
        FILTER2_RESONANCE_PARAMETER,
        SYSEX_COVERAGE_STATEMENT,
    )

    result = _export(tmp_path)
    output_dir = tmp_path / "batch"

    assert tuple(path.name for path in sorted(output_dir.iterdir())) == tuple(
        sorted(EXPECTED_FILENAMES)
    )
    assert tuple(item.sysex_export.render.sha256 for item in result.candidates) == (
        EXPECTED_SYSEX_SHA256
    )
    assert tuple(item.sidecar_sha256 for item in result.candidates) == EXPECTED_SIDECAR_SHA256
    assert result.manifest_sha256 == EXPECTED_MANIFEST_SHA256
    assert result.selected_track == 2
    assert result.source_hash == result.audio_sha256
    assert result.candidate_outputs == result.candidates
    assert result.safety[0] == SYSEX_COVERAGE_STATEMENT

    expected_resonance = ("24", "28", "20", "18")
    for item, resonance in zip(result.candidates, expected_resonance, strict=True):
        sidecar = json.loads(item.sidecar_path.read_text(encoding="utf-8"))
        assert item.candidate == item.column
        assert item.sysex_path == item.sysex_export.write.path
        assert item.filter2_resonance == resonance
        assert sidecar["candidate_dna"]["column"] == item.column
        assert sidecar["dynamic_send_plan"]["selected_candidate"] == item.column
        assert sidecar["hardware_applied_rows"] == [
            {
                "parameter": FILTER2_RESONANCE_PARAMETER,
                "rendered_unpacked_value": int(resonance),
                "screen_value": resonance,
                "source_unpacked_value": 12,
                "track": 2,
                "unpacked_offset": 495,
            }
        ]
        assert sidecar["coverage_counts"] == {
            "deferred_row_count": item.deferred_count,
            "dna_row_count": item.dna_row_count,
            "manual_row_count": item.manual_count,
            "sendable_row_count": item.live_sendable_count,
            "sysex_encoded_row_count": item.sysex_applied_count,
        }
        assert item.sysex_applied_count == 1
        assert item.deferred_count == item.dna_row_count - 1
        assert sidecar["hardware_export"]["encoded_parameters"] == [FILTER2_RESONANCE_PARAMETER]
        assert sidecar["hardware_export"]["coverage_statement"] == SYSEX_COVERAGE_STATEMENT
        assert len(sidecar["deferred_rows"]) == item.deferred_count

    manifest = json.loads(result.manifest_write.path.read_text(encoding="utf-8"))
    assert manifest["candidate_count"] == 4
    assert [row["filter2_resonance"] for row in manifest["candidates"]] == list(expected_resonance)
    assert manifest["coverage_counts"]["sysex_encoded_row_count"] == 4
    assert manifest["coverage_counts"]["deferred_row_count"] == sum(
        item.deferred_count for item in result.candidates
    )
    assert manifest["safety"][0] == SYSEX_COVERAGE_STATEMENT


def test_export_audio_patch_batch_refuses_any_collision_before_first_write(
    tmp_path: Path,
    mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)
    output_dir = tmp_path / "batch"
    output_dir.mkdir()
    collision = output_dir / "a4-t2-c04-rounder-bass.json"
    collision.write_text("existing", encoding="utf-8")

    def unexpected_export(**_kwargs: object) -> object:
        raise AssertionError("preflight must run before saved-kit export")

    monkeypatch.setattr(batch, "export_analog_four_saved_kit", unexpected_export)

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=output_dir,
            track=2,
        )

    assert tuple(output_dir.iterdir()) == (collision,)
    assert collision.read_text(encoding="utf-8") == "existing"


def test_export_audio_patch_batch_overwrites_only_when_explicitly_enabled(
    tmp_path: Path,
    mocked_inference: None,
) -> None:
    first = _export(tmp_path, candidate_count=1)
    second = _export(tmp_path, candidate_count=1, overwrite=True)

    assert first.candidates[0].sysex_export.write.overwrote_existing is False
    assert second.candidates[0].sysex_export.write.overwrote_existing is True
    assert second.candidates[0].sidecar_write.overwrote_existing is True
    assert second.manifest_write.overwrote_existing is True


@pytest.mark.parametrize(
    ("track", "candidate_count", "message"),
    [
        (0, 4, "track must be in 1..4"),
        (5, 4, "track must be in 1..4"),
        (1, 0, "candidate_count must be in 1..4"),
        (1, 5, "candidate_count must be in 1..4"),
    ],
)
def test_export_audio_patch_batch_rejects_invalid_request_before_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    track: int,
    candidate_count: int,
    message: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)

    def unexpected_inference(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("request validation must precede inference")

    monkeypatch.setattr(batch, "_build_audio_inference", unexpected_inference)
    with pytest.raises(ValueError, match=message):
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
            track=track,
            candidate_count=candidate_count,
        )


def test_export_audio_patch_batch_rejects_output_path_that_is_a_file(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch import (
        export_analog_four_audio_patch_batch,
    )

    output_path = tmp_path / "not-a-directory"
    output_path.write_text("file", encoding="utf-8")
    with pytest.raises(NotADirectoryError, match="output_dir is not a directory"):
        export_analog_four_audio_patch_batch(
            audio_path=tmp_path / "unused.wav",
            source_kit_path=SOURCE_KIT,
            output_dir=output_path,
        )


def test_export_audio_patch_batch_uses_deterministic_safe_candidate_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    inference = _inference(track=2, candidate_count=1)
    genome = inference.genome
    hostile = replace(genome.candidates[0], label="../../LOUD + Wide")
    hostile_genome = replace(genome, candidates=(hostile,))
    settled = replace(
        inference,
        genome=hostile_genome,
        genome_payload=analog_four_patch_genome_to_dict(hostile_genome),
    )
    monkeypatch.setattr(batch, "_build_audio_inference", lambda *_args, **_kwargs: settled)

    result = _export(tmp_path, candidate_count=1)

    assert result.candidates[0].sysex_path.name == "a4-t2-c01-loud-wide.syx"
    assert result.candidates[0].sysex_path.parent == (tmp_path / "batch").resolve()


def test_export_audio_patch_batch_leaves_manifest_absent_when_sidecar_write_fails(
    tmp_path: Path,
    mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    real_atomic_write = batch.atomic_write

    def fail_json(path: Path, data: bytes, *, overwrite: bool = False):
        if path.suffix == ".json":
            raise OSError("disk full")
        return real_atomic_write(path, data, overwrite=overwrite)

    reset_metrics()
    monkeypatch.setattr(batch, "atomic_write", fail_json)
    with pytest.raises(OSError, match="disk full"):
        _export(tmp_path, candidate_count=1)

    output_dir = tmp_path / "batch"
    assert (output_dir / "a4-t2-c01-closest-reference.syx").is_file()
    assert not (output_dir / "a4-t2-c01-closest-reference.json").exists()
    assert not (output_dir / "a4-t2-audio-patch-batch.json").exists()
    assert get_metrics().export_errors_by_code["write_failed"] == 1


def test_export_audio_patch_batch_records_source_and_inference_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    with pytest.raises(FileNotFoundError):
        batch.export_analog_four_audio_patch_batch(
            audio_path=tmp_path / "missing.wav",
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
        )
    assert get_metrics().export_errors_by_code["source_read_failed"] == 1

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)

    def fail_inference(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("inference unavailable")

    monkeypatch.setattr(batch, "_build_audio_inference", fail_inference)
    with pytest.raises(RuntimeError, match="inference unavailable"):
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
        )
    assert get_metrics().export_errors_by_code["inference_failed"] == 1


def test_export_audio_patch_batch_rejects_incomplete_or_invalid_candidate_dna(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)
    inference = _inference(track=2, candidate_count=1)
    candidate = inference.genome.candidates[0]
    without_resonance = replace(
        candidate,
        genes=tuple(
            gene
            for gene in candidate.genes
            if gene.value.parameter != batch.FILTER2_RESONANCE_PARAMETER
        ),
    )
    invalid_genome: AnalogFourPatchGenome = replace(
        inference.genome,
        candidates=(without_resonance,),
    )
    invalid = replace(
        inference,
        genome=invalid_genome,
        genome_payload=analog_four_patch_genome_to_dict(invalid_genome),
    )
    monkeypatch.setattr(batch, "_build_audio_inference", lambda *_args, **_kwargs: invalid)

    with pytest.raises(ValueError, match="must contain exactly one Filter2 Resonance gene"):
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
            track=2,
            candidate_count=1,
        )
    assert not (tmp_path / "batch").exists()


def test_build_audio_inference_uses_public_audio_inference_serializers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.style_analysis import analog_four_patch_inference as public_api

    report = _feature_report()
    genome = build_analog_four_patch_genome(report, track=3, candidate_count=1)
    features = public_api.AnalogFourPatchAudioFeatures(
        audio_sha256="b" * 64,
        duration=0.5,
        attack=0.1,
        decay=0.2,
        sustain=0.7,
        tail=0.4,
        brightness=0.6,
        spectral_flatness=0.2,
        noise=0.3,
        low_end=0.8,
        harmonicity=0.9,
        transient=0.4,
        modulation=0.5,
    )
    public_result = public_api.AnalogFourAudioPatchGenome(
        feature_report=report,
        audio_features=features,
        genome=genome,
    )
    observed: dict[str, object] = {}

    def fake_build(path: Path, *, track: int, candidate_count: int):
        observed.update(path=path, track=track, candidate_count=candidate_count)
        return public_result

    monkeypatch.setattr(public_api, "build_analog_four_audio_patch_genome", fake_build)
    result = batch._build_audio_inference(tmp_path / "audio.wav", track=3, candidate_count=1)

    assert observed == {"path": tmp_path / "audio.wav", "track": 3, "candidate_count": 1}
    assert result.audio_features_payload["audio_sha256"] == "b" * 64
    assert result.genome_payload["selected_track"] == 3

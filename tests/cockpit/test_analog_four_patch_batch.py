"""Guarded audio-to-candidate Analog Four batch export tests."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import struct
import subprocess
import sys
import wave
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.export.analog_four_patch_batch import _AudioInference
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
EXPECTED_GENERATION_ID = "73bfa54f7bbbee9bf1bd62294d6a807e"
EXPECTED_SYSEX_SHA256 = (
    "2f6d97445535a1eb1f4b54e234d7b8d96b9c646c2f611a99f0e6e06a39980835",
    "16aee178243000a52cad0031429ca9768924e37c3989d1ad22c757cb7c266847",
    "68e6049f0cd81ad0709ea1e0aff42a11300c4b43e87a5392460fb30d71788788",
    "e1384abed1898010debfedf64386dd45485493cabb28b05f2e5bcd1c72096702",
)
EXPECTED_SIDECAR_SHA256 = (
    "c73ed7cccb6a38e1c87ef4a4e80aff56788da040da42fa674f0ffcfc11e38343",
    "4500cbfa5da928bccdc165ca62b8b8dd609966e86725c45bc9562b7465086775",
    "b975e279b93609f0724c0b899a4d04a3f2ee02a3e83b87c53439f8bdd34eb24e",
    "62f1fa503c9147a5da42f361f682ddaadd5bebac79a0b837e6a477574634c2f3",
)
EXPECTED_MANIFEST_SHA256 = "a7d3647e0a553bd395638aacef3be8e93f776387c5853499433a1a094047c475"


def _json_payload_sha256(payload: object) -> str:
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _candidate_midi_value(sidecar: dict[str, object], parameter: str) -> int:
    candidate = sidecar["candidate_dna"]
    assert isinstance(candidate, dict)
    genes = candidate["genes"]
    assert isinstance(genes, list)
    for gene in genes:
        assert isinstance(gene, dict)
        value = gene["value"]
        assert isinstance(value, dict)
        if value["parameter"] == parameter:
            midi_value = value["midi_value"]
            assert isinstance(midi_value, int)
            return midi_value
    raise AssertionError(f"missing candidate DNA parameter: {parameter}")


def _write_test_wav(path: Path, *, frequency: float = 220.0) -> None:
    sample_rate = 22_050
    frames = bytearray()
    for index in range(sample_rate):
        sample = int(0.35 * 32_767 * math.sin(2.0 * math.pi * frequency * index / sample_rate))
        frames.extend(struct.pack("<h", sample))
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(frames)


def _write_noise_wav(path: Path) -> None:
    sample_rate = 22_050
    generator = random.Random(42)
    frames = bytearray()
    for _index in range(sample_rate):
        frames.extend(struct.pack("<h", generator.randint(-16_000, 16_000)))
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(frames)


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


def _inference(*, track: int, candidate_count: int) -> _AudioInference:
    report = _feature_report()
    audio_sha256 = hashlib.sha256(AUDIO_BYTES).hexdigest()
    genome = replace(
        build_analog_four_patch_genome(
            report,
            track=track,
            candidate_count=candidate_count,
        ),
        source_hash=audio_sha256,
    )
    return _AudioInference(
        feature_report=report,
        genome=genome,
        audio_features_payload={
            "audio_sha256": audio_sha256,
            "duration": 1.0,
            "attack": 0.1,
            "decay": 0.2,
            "sustain": 0.7,
            "tail": 0.3,
            "brightness": 0.44,
            "spectral_flatness": 0.1,
            "noise": 0.22,
            "low_end": 0.5,
            "harmonicity": 0.8,
            "transient": 0.6,
            "modulation": 0.2,
        },
        genome_payload=analog_four_patch_genome_to_dict(genome),
    )


@pytest.fixture
def _mocked_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    def fake_build(
        _audio_path: Path,
        *,
        track: int,
        candidate_count: int,
    ) -> _AudioInference:
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
    _mocked_inference: None,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch import (
        FILTER2_RESONANCE_PARAMETER,
        SYSEX_COVERAGE_STATEMENT,
    )
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    result = _export(tmp_path)
    output_dir = tmp_path / "batch"
    expected_filenames = (
        f"a4-t2-g{EXPECTED_GENERATION_ID}-c01-closest-reference.syx",
        f"a4-t2-g{EXPECTED_GENERATION_ID}-c01-closest-reference.json",
        f"a4-t2-g{EXPECTED_GENERATION_ID}-c02-brighter-sync.syx",
        f"a4-t2-g{EXPECTED_GENERATION_ID}-c02-brighter-sync.json",
        f"a4-t2-g{EXPECTED_GENERATION_ID}-c03-noisy-texture.syx",
        f"a4-t2-g{EXPECTED_GENERATION_ID}-c03-noisy-texture.json",
        f"a4-t2-g{EXPECTED_GENERATION_ID}-c04-rounder-bass.syx",
        f"a4-t2-g{EXPECTED_GENERATION_ID}-c04-rounder-bass.json",
        "a4-t2-audio-patch-batch.json",
    )

    assert tuple(path.name for path in sorted(output_dir.iterdir())) == tuple(
        sorted(expected_filenames)
    )
    assert result.generation_id == EXPECTED_GENERATION_ID
    assert len(result.generation_id) == 32
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
        assert sidecar["generation_id"] == result.generation_id
        assert f"-g{result.generation_id}-" in item.sysex_path.name
        assert f"-g{result.generation_id}-" in item.sidecar_path.name
        assert hashlib.sha256(item.sysex_path.read_bytes()).hexdigest() == (
            item.sysex_export.render.sha256
        )
        assert hashlib.sha256(item.sidecar_path.read_bytes()).hexdigest() == (item.sidecar_sha256)
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
        assert sidecar["hashes"] == {
            "audio_sha256": result.audio_sha256,
            "candidate_dna_sha256": _json_payload_sha256(sidecar["candidate_dna"]),
            "genome_sha256": result.genome_sha256,
            "send_plan_sha256": _json_payload_sha256(sidecar["dynamic_send_plan"]),
            "source_kit_sha256": result.source_kit_sha256,
            "sysex_sha256": hashlib.sha256(item.sysex_path.read_bytes()).hexdigest(),
        }
        selection = load_analog_four_patch_batch_candidate(
            result.manifest_path,
            candidate=item.column,
        )
        assert selection.plan.selected_candidate == item.column
        assert selection.plan.selected_label == item.label
        assert selection.plan.summary.sendable_count == item.live_sendable_count
        assert selection.plan.summary.manual_count == item.manual_count

    manifest = json.loads(result.manifest_write.path.read_text(encoding="utf-8"))
    assert hashlib.sha256(result.manifest_write.path.read_bytes()).hexdigest() == (
        result.manifest_sha256
    )
    assert manifest["candidate_count"] == 4
    assert manifest["generation_id"] == result.generation_id
    assert [row["filter2_resonance"] for row in manifest["candidates"]] == list(expected_resonance)
    assert manifest["coverage_counts"]["sysex_encoded_row_count"] == 4
    assert manifest["coverage_counts"]["deferred_row_count"] == sum(
        item.deferred_count for item in result.candidates
    )
    assert manifest["feature_report_hash"] == result.feature_report_hash
    assert result.feature_report_hash == _feature_report().content_hash
    assert result.feature_report_hash != result.audio_sha256
    assert manifest["safety"][0] == SYSEX_COVERAGE_STATEMENT
    for row, item in zip(manifest["candidates"], result.candidates, strict=True):
        assert row["sysex_filename"] == item.sysex_path.name
        assert row["sidecar_filename"] == item.sidecar_path.name
        assert row["sysex_sha256"] == hashlib.sha256(item.sysex_path.read_bytes()).hexdigest()
        assert row["sidecar_sha256"] == hashlib.sha256(item.sidecar_path.read_bytes()).hexdigest()


@pytest.mark.skipif(
    sys.platform == "win32" and os.environ.get("GITHUB_ACTIONS") == "true",
    reason="Windows native-audio subprocess proof is not yet reliable on GitHub Actions",
)
def test_real_audio_to_patch_batch_chain_distinguishes_tone_from_noise(tmp_path: Path) -> None:
    tone_path = tmp_path / "real-tone.wav"
    noise_path = tmp_path / "real-noise.wav"
    _write_test_wav(tone_path)
    _write_noise_wav(noise_path)
    environment = os.environ.copy()
    environment.update(
        {
            "BLIS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMBA_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    payloads: list[dict[str, object]] = []
    for audio_path, directory_name in (
        (tone_path, "tone-batch"),
        (noise_path, "noise-batch"),
    ):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "rytm_randomizer.cli",
                "analog-four-audio-patch-batch",
                "--audio",
                str(audio_path),
                "--source-kit",
                str(SOURCE_KIT),
                "--output-dir",
                str(tmp_path / directory_name),
                "--track",
                "1",
                "--candidates",
                "1",
                "--json",
            ],
            capture_output=True,
            check=False,
            env=environment,
            text=True,
            timeout=120,
        )
        if completed.returncode != 0:
            failure = (
                json.loads(completed.stdout)
                if completed.stdout
                else {"error_code": "process_crash", "error": completed.stderr}
            )
            pytest.fail(
                "real audio batch generation failed: "
                f"{failure.get('error_code')}: {failure.get('error')}"
            )
        payloads.append(json.loads(completed.stdout))

    sidecars: list[dict[str, object]] = []
    manifests: list[dict[str, object]] = []
    for payload in payloads:
        manifest_path = Path(str(payload["manifest_path"]))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        candidate_output = payload["candidate_outputs"][0]  # type: ignore[index]
        sidecar_path = Path(str(candidate_output["sidecar_path"]))
        sysex_path = Path(str(candidate_output["sysex_path"]))
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        manifests.append(manifest)
        sidecars.append(sidecar)
        assert len(str(payload["generation_id"])) == 32
        assert manifest["generation_id"] == sidecar["generation_id"] == payload["generation_id"]
        assert len(manifest["feature_report_hash"]) == 64
        assert sidecar["audio_features"]["audio_sha256"] == payload["source_hash"]
        assert manifest["genome_sha256"] == sidecar["hashes"]["genome_sha256"]
        assert (
            manifest["candidates"][0]["sidecar_sha256"]
            == hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
        )
        assert (
            manifest["candidates"][0]["sysex_sha256"]
            == hashlib.sha256(sysex_path.read_bytes()).hexdigest()
        )
        assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == payload["manifest_sha256"]

    tone_features = sidecars[0]["audio_features"]
    noise_features = sidecars[1]["audio_features"]
    assert isinstance(tone_features, dict)
    assert isinstance(noise_features, dict)
    assert float(tone_features["harmonicity"]) > float(noise_features["harmonicity"]) + 0.5
    assert float(noise_features["spectral_flatness"]) > (
        float(tone_features["spectral_flatness"]) + 0.3
    )
    assert float(noise_features["noise"]) > float(tone_features["noise"]) + 0.3
    assert float(noise_features["brightness"]) > float(tone_features["brightness"]) + 0.3
    assert _candidate_midi_value(sidecars[0], "OSC1 Level") > (
        _candidate_midi_value(sidecars[1], "OSC1 Level") + 20
    )
    assert _candidate_midi_value(sidecars[1], "Filter2 Frequency") > (
        _candidate_midi_value(sidecars[0], "Filter2 Frequency") + 30
    )
    assert manifests[0]["genome_sha256"] != manifests[1]["genome_sha256"]
    tone_candidates = manifests[0]["candidates"]
    noise_candidates = manifests[1]["candidates"]
    assert isinstance(tone_candidates, list)
    assert isinstance(noise_candidates, list)
    assert isinstance(tone_candidates[0], dict)
    assert isinstance(noise_candidates[0], dict)
    assert tone_candidates[0]["sysex_sha256"] != noise_candidates[0]["sysex_sha256"]


def test_batch_records_one_export_metric_for_the_complete_transaction(
    tmp_path: Path,
    _mocked_inference: None,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    _export(tmp_path, candidate_count=4)

    assert get_metrics().export_count == 1


def test_batch_export_logs_red_context_and_stable_failure_identity(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import reset_metrics

    info_extras: list[dict[str, object]] = []
    warning_extras: list[dict[str, object]] = []
    reset_metrics()
    monkeypatch.setattr(
        batch._logger,
        "info",
        lambda _message, *, extra: info_extras.append(extra),
    )
    monkeypatch.setattr(
        batch._logger,
        "warning",
        lambda _message, *, extra: warning_extras.append(extra),
    )

    _export(tmp_path, candidate_count=1)
    success = info_extras[-1]
    success_duration = success["duration_ms"]
    assert isinstance(success_duration, (int, float))
    assert float(success_duration) >= 0.0
    assert "export_count=1" in str(success["metrics_summary"])

    failed_root = tmp_path / "failed"
    failed_root.mkdir()
    monkeypatch.setattr(
        batch,
        "_build_audio_inference",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    with pytest.raises(batch.AnalogFourPatchBatchStageError, match="offline"):
        _export(failed_root, candidate_count=1)

    failure = warning_extras[-1]
    assert failure["fingerprint"] == "a4.audio_patch_batch.stage_failed"
    assert failure["error_type"] == "AnalogFourPatchBatchStageError"
    failure_duration = failure["duration_ms"]
    assert isinstance(failure_duration, (int, float))
    assert float(failure_duration) >= 0.0
    assert "export_errors" in str(failure["metrics_summary"])


def test_export_audio_patch_batch_refuses_any_collision_before_first_write(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)
    output_dir = tmp_path / "batch"
    output_dir.mkdir()
    collision = output_dir / "a4-t2-audio-patch-batch.json"
    collision.write_text("existing", encoding="utf-8")

    def unexpected_export(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("preflight must run before saved-kit export")

    monkeypatch.setattr(batch, "get_analog_four_saved_kit_capability", unexpected_export)

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
    _mocked_inference: None,
) -> None:
    first = _export(tmp_path, candidate_count=1)
    second = _export(tmp_path, candidate_count=1, overwrite=True)

    assert first.candidates[0].sysex_export.write.overwrote_existing is False
    assert second.candidates[0].sysex_export.write.overwrote_existing is False
    assert second.candidates[0].sidecar_write.overwrote_existing is False
    assert second.manifest_write.overwrote_existing is True


def test_export_audio_patch_batch_resolves_saved_kit_capability_per_operation(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    real_resolver = batch.get_analog_four_saved_kit_capability
    resolutions = 0

    def resolve_capability():
        nonlocal resolutions
        resolutions += 1
        return real_resolver()

    monkeypatch.setattr(batch, "get_analog_four_saved_kit_capability", resolve_capability)

    _export(tmp_path, candidate_count=1)
    _export(tmp_path, candidate_count=1, overwrite=True)

    assert resolutions == 2


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


@pytest.mark.parametrize(
    ("track", "candidate_count", "message"),
    [
        (1.5, 4, "track must be an int"),
        (True, 4, "track must be an int"),
        (1, 1.5, "candidate_count must be an int"),
        (1, True, "candidate_count must be an int"),
    ],
)
def test_export_audio_patch_batch_rejects_non_integer_selectors_before_inference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    track: object,
    candidate_count: object,
    message: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)

    def unexpected_inference(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("request validation must precede inference")

    monkeypatch.setattr(batch, "_build_audio_inference", unexpected_inference)
    with pytest.raises(TypeError, match=message):
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
            track=track,  # type: ignore[arg-type]
            candidate_count=candidate_count,  # type: ignore[arg-type]
        )


def test_export_audio_patch_batch_rejects_output_path_that_is_a_file(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch import (
        export_analog_four_audio_patch_batch,
    )

    output_path = tmp_path / "not-a-directory"
    output_path.write_text("file", encoding="utf-8")
    with pytest.raises(ValueError, match="output_dir is not a directory"):
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

    assert result.candidates[0].sysex_path.name == (
        f"a4-t2-g{result.generation_id}-c01-loud-wide.syx"
    )
    assert result.candidates[0].sysex_path.parent == (tmp_path / "batch").resolve()


def test_sidecar_failure_leaves_only_an_unreferenced_immutable_sysex(
    tmp_path: Path,
    _mocked_inference: None,
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
    remaining = tuple(output_dir.iterdir())
    assert len(remaining) == 1
    assert remaining[0].suffix == ".syx"
    assert hashlib.sha256(remaining[0].read_bytes()).hexdigest() == EXPECTED_SYSEX_SHA256[0]
    assert not (output_dir / "a4-t2-audio-patch-batch.json").exists()
    assert not (output_dir / ".a4-t2-audio-patch-batch.lock").exists()
    assert get_metrics().export_errors_by_code["write_failed"] == 1


def test_export_audio_patch_batch_records_source_and_inference_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    with pytest.raises(FileNotFoundError) as exc_info:
        batch.export_analog_four_audio_patch_batch(
            audio_path=tmp_path / "missing.wav",
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
        )
    assert exc_info.value.__dict__["error_code"] == "input_not_found"
    assert get_metrics().export_errors_by_code["input_not_found"] == 1

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

    monkeypatch.setattr(
        batch,
        "_build_audio_inference",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ImportError("lazy import failed")),
    )
    with pytest.raises(ImportError, match="lazy import failed") as import_exc:
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
        )
    assert import_exc.value.__dict__["error_code"] == "service_unavailable"
    assert get_metrics().export_errors_by_code["service_unavailable"] == 1


def test_batch_export_failure_classifies_interrupts_and_fatal_write_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    class FatalExportSignal(BaseException):
        pass

    assert (
        batch._batch_export_error_code(
            KeyboardInterrupt(),
            source_reads_complete=True,
            output_phase_started=False,
        )
        == "interrupted"
    )

    reset_metrics()
    monkeypatch.setattr(batch.time, "perf_counter", lambda: 2.0)
    batch._record_batch_export_failure(
        FatalExportSignal("fatal write failure"),
        audio_path=tmp_path / "reference.wav",
        source_kit_path=tmp_path / "source-kit.syx",
        output_dir=tmp_path / "batch",
        started_at=1.0,
        source_reads_complete=True,
        output_phase_started=True,
    )

    assert get_metrics().export_errors_by_code["write_failed"] == 1


def test_export_audio_patch_batch_classifies_missing_audio_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis.extractor import StyleAnalysisDependencyError

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)
    monkeypatch.setattr(
        batch,
        "_build_audio_inference",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            StyleAnalysisDependencyError("style dependency missing")
        ),
    )
    reset_metrics()

    with pytest.raises(batch.AnalogFourPatchBatchStageError, match="dependency missing"):
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
        )

    assert get_metrics().export_errors_by_code["dependency_missing"] == 1


def test_export_audio_patch_batch_classifies_inference_file_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)

    def fail_inference(*_args: object, **_kwargs: object) -> object:
        raise OSError("decoder could not read audio")

    reset_metrics()
    monkeypatch.setattr(batch, "_build_audio_inference", fail_inference)
    with pytest.raises(
        batch.AnalogFourPatchBatchStageError,
        match="decoder could not read audio",
    ):
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
        )

    assert get_metrics().export_errors_by_code["audio_read_failed"] == 1


def test_export_audio_patch_batch_classifies_staging_file_errors_as_write_failures(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    class FailingCapability:
        def render_saved_kit(self, *_args: object, **_kwargs: object) -> object:
            raise OSError("staging disk failed")

    monkeypatch.setattr(
        batch,
        "get_analog_four_saved_kit_capability",
        lambda: FailingCapability(),
    )
    reset_metrics()

    with pytest.raises(batch.AnalogFourPatchBatchStageError) as exc_info:
        _export(tmp_path, candidate_count=1)

    assert exc_info.value.error_code == "write_failed"
    assert get_metrics().export_errors_by_code["write_failed"] == 1


def test_export_audio_patch_batch_classifies_missing_published_artifact_as_write_failure(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    def fail_publication(*_args: object, **_kwargs: object) -> object:
        raise FileNotFoundError("generation artifact disappeared")

    monkeypatch.setattr(batch, "_publish_staged_batch", fail_publication)
    reset_metrics()

    with pytest.raises(FileNotFoundError, match="generation artifact disappeared") as exc_info:
        _export(tmp_path, candidate_count=1)

    assert exc_info.value.__dict__["error_code"] == "write_failed"
    assert get_metrics().export_errors_by_code["write_failed"] == 1


def test_export_audio_patch_batch_rejects_audio_hash_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    inference = _inference(track=2, candidate_count=1)
    inconsistent = replace(
        inference,
        audio_features_payload={**inference.audio_features_payload, "audio_sha256": "0" * 64},
    )
    monkeypatch.setattr(batch, "_build_audio_inference", lambda *_args, **_kwargs: inconsistent)

    with pytest.raises(ValueError, match="snapshot hash"):
        _export(tmp_path, candidate_count=1)

    assert not (tmp_path / "batch").exists()


def test_export_audio_patch_batch_uses_immutable_input_snapshots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    audio_path = tmp_path / "reference.wav"
    source_kit_path = tmp_path / "source.syx"
    audio_path.write_bytes(AUDIO_BYTES)
    source_kit_bytes = SOURCE_KIT.read_bytes()
    source_kit_path.write_bytes(source_kit_bytes)

    def mutate_originals(
        audio_snapshot: Path,
        *,
        track: int,
        candidate_count: int,
    ) -> object:
        assert audio_snapshot.read_bytes() == AUDIO_BYTES
        audio_path.write_bytes(b"changed-after-snapshot")
        source_kit_path.write_bytes(b"changed-after-snapshot")
        return _inference(track=track, candidate_count=candidate_count)

    monkeypatch.setattr(batch, "_build_audio_inference", mutate_originals)
    result = batch.export_analog_four_audio_patch_batch(
        audio_path=audio_path,
        source_kit_path=source_kit_path,
        output_dir=tmp_path / "batch",
        track=2,
        candidate_count=1,
    )

    assert result.audio_sha256 == hashlib.sha256(AUDIO_BYTES).hexdigest()
    assert result.source_kit_sha256 == hashlib.sha256(source_kit_bytes).hexdigest()
    assert result.candidates[0].sysex_export.render.sha256 == EXPECTED_SYSEX_SHA256[0]


@pytest.mark.parametrize("failure_target", ["sidecar", "manifest"])
def test_publication_failure_leaves_prior_manifest_and_generation_unchanged(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
    failure_target: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    first = _export(tmp_path, candidate_count=1)
    output_dir = tmp_path / "batch"
    prior = {path: path.read_bytes() for path in output_dir.iterdir()}
    failure_name = (
        first.candidates[0].sidecar_path.name
        if failure_target == "sidecar"
        else first.manifest_write.path.name
    )
    real_atomic_write = batch.atomic_write

    def fail_selected(path: Path, data: bytes, *, overwrite: bool = False):
        if path.name == failure_name:
            raise OSError("publication failed")
        return real_atomic_write(path, data, overwrite=overwrite)

    monkeypatch.setattr(batch, "atomic_write", fail_selected)
    with pytest.raises(OSError, match="publication failed"):
        _export(tmp_path, candidate_count=1, overwrite=True)

    assert first.manifest_write.path.read_bytes() == prior[first.manifest_write.path]
    assert {path: path.read_bytes() for path in output_dir.iterdir()} == prior


def test_generation_addressing_keeps_prior_manifest_valid_during_interrupt(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    first = _export(tmp_path, candidate_count=1)
    original_manifest = first.manifest_write.path.read_bytes()
    original_sidecar = first.candidates[0].sidecar_path.read_bytes()
    renamed_audio = tmp_path / "renamed-reference.wav"
    renamed_kit = tmp_path / "renamed-source.syx"
    renamed_audio.write_bytes(AUDIO_BYTES)
    renamed_kit.write_bytes(SOURCE_KIT.read_bytes())
    real_atomic_write = batch.atomic_write

    def interrupt_manifest(path: Path, data: bytes, *, overwrite: bool = False):
        if path.resolve() == first.manifest_write.path:
            raise KeyboardInterrupt("simulated process interruption")
        return real_atomic_write(path, data, overwrite=overwrite)

    monkeypatch.setattr(batch, "atomic_write", interrupt_manifest)
    with pytest.raises(KeyboardInterrupt, match="simulated process interruption"):
        batch.export_analog_four_audio_patch_batch(
            audio_path=renamed_audio,
            source_kit_path=renamed_kit,
            output_dir=tmp_path / "batch",
            track=2,
            candidate_count=1,
            overwrite=True,
        )

    assert first.manifest_write.path.read_bytes() == original_manifest
    assert first.candidates[0].sidecar_path.read_bytes() == original_sidecar
    assert not (tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock").exists()
    manifest = json.loads(original_manifest)
    sidecar_path = first.manifest_write.path.parent / manifest["candidates"][0]["sidecar_filename"]
    sysex_path = first.manifest_write.path.parent / manifest["candidates"][0]["sysex_filename"]
    assert hashlib.sha256(sidecar_path.read_bytes()).hexdigest() == (
        manifest["candidates"][0]["sidecar_sha256"]
    )
    assert hashlib.sha256(sysex_path.read_bytes()).hexdigest() == (
        manifest["candidates"][0]["sysex_sha256"]
    )
    orphan_sidecars = tuple(
        path for path in (tmp_path / "batch").glob("a4-t2-g*-c01-*.json") if path != sidecar_path
    )
    assert len(orphan_sidecars) == 1
    assert f"-g{first.generation_id}-" not in orphan_sidecars[0].name


def test_interrupted_first_publication_reuses_exact_orphans_on_retry(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    real_atomic_write = batch.atomic_write
    manifest_name = "a4-t2-audio-patch-batch.json"

    def interrupt_manifest(path: Path, data: bytes, *, overwrite: bool = False):
        if path.name == manifest_name:
            raise KeyboardInterrupt("interrupt first commit")
        return real_atomic_write(path, data, overwrite=overwrite)

    monkeypatch.setattr(batch, "atomic_write", interrupt_manifest)
    with pytest.raises(KeyboardInterrupt, match="interrupt first commit"):
        _export(tmp_path, candidate_count=1)

    output_dir = tmp_path / "batch"
    assert not (output_dir / manifest_name).exists()
    assert len(tuple(output_dir.glob("a4-t2-g*-c01-*"))) == 2
    assert not (output_dir / ".a4-t2-audio-patch-batch.lock").exists()

    monkeypatch.setattr(batch, "atomic_write", real_atomic_write)
    result = _export(tmp_path, candidate_count=1)

    assert result.candidates[0].sysex_export.write.overwrote_existing is False
    assert result.candidates[0].sidecar_write.overwrote_existing is False
    assert result.manifest_path.exists()


def test_interrupt_after_lock_publication_cleans_owned_lock(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    real_acquire = batch._acquire_batch_lock

    def acquire_then_interrupt(lock_path: Path, **kwargs: object):
        real_acquire(lock_path, **kwargs)  # type: ignore[arg-type]
        raise KeyboardInterrupt("interrupt after lock publication")

    monkeypatch.setattr(batch, "_acquire_batch_lock", acquire_then_interrupt)
    reset_metrics()
    with pytest.raises(KeyboardInterrupt, match="interrupt after lock publication"):
        _export(tmp_path, candidate_count=1)

    assert not (tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock").exists()
    assert get_metrics().export_errors_by_code["interrupted"] == 1


def test_native_analysis_crash_cleans_parent_owned_audio_and_sysex_snapshots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.errors import BoundaryError

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)
    observed_staging_dirs: list[Path] = []

    def crash_after_snapshot(
        audio_snapshot: Path,
        *,
        track: int,
        candidate_count: int,
    ) -> object:
        del track, candidate_count
        observed_staging_dirs.append(audio_snapshot.parent)
        assert audio_snapshot.read_bytes() == AUDIO_BYTES
        assert (audio_snapshot.parent / "source-kit.syx").read_bytes() == SOURCE_KIT.read_bytes()
        raise BoundaryError(
            "native worker access violation",
            context={
                "error_code": "inference_failed",
                "exit_code": 0xC0000005,
            },
        )

    monkeypatch.setattr(batch.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(batch, "_build_audio_inference", crash_after_snapshot)

    with pytest.raises(
        batch.AnalogFourPatchBatchStageError,
        match="native worker access violation",
    ) as exc_info:
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
            track=2,
            candidate_count=1,
        )

    assert exc_info.value.error_code == "inference_failed"
    assert len(observed_staging_dirs) == 1
    assert not observed_staging_dirs[0].exists()
    assert tuple(tmp_path.glob("a4-audio-patch-batch-*")) == ()
    assert not (tmp_path / "batch").exists()


def test_batch_service_boundary_traces_terminal_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    audio_path = tmp_path / "reference.wav"
    audio_path.write_bytes(AUDIO_BYTES)
    events: list[str] = []

    @contextmanager
    def observe_operation(name: str, **_kwargs: object) -> Iterator[None]:
        events.append(f"start:{name}")
        try:
            yield
        except BaseException:
            events.append(f"error:{name}")
            raise

    monkeypatch.setattr(batch, "trace_operation", observe_operation)
    monkeypatch.setattr(
        batch,
        "_build_audio_inference",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt("operator cancelled")),
    )

    with pytest.raises(KeyboardInterrupt, match="operator cancelled"):
        batch.export_analog_four_audio_patch_batch(
            audio_path=audio_path,
            source_kit_path=SOURCE_KIT,
            output_dir=tmp_path / "batch",
            candidate_count=1,
        )

    assert events == [
        "start:a4_audio_patch_batch_export",
        "error:a4_audio_patch_batch_export",
    ]


def test_private_staging_is_cleaned_before_publication_lock(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    staged_paths: list[Path] = []
    real_stage = batch._stage_batch
    real_acquire = batch._acquire_batch_lock

    def observe_stage(**kwargs: object):
        staged = real_stage(**kwargs)  # type: ignore[arg-type]
        staged_paths.extend(item.sysex_path for item in staged.candidates)
        return staged

    def assert_cleaned(lock_path: Path, **kwargs: object):
        assert staged_paths
        assert all(not path.exists() for path in staged_paths)
        return real_acquire(lock_path, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(batch, "_stage_batch", observe_stage)
    monkeypatch.setattr(batch, "_acquire_batch_lock", assert_cleaned)

    result = _export(tmp_path, candidate_count=1)
    assert result.candidate_count == 1


def test_immutable_publication_reuses_matching_bytes_and_rejects_collisions(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    artifact = tmp_path / "generation.syx"
    first = batch._publish_immutable_artifact(artifact, b"generation-bytes")
    reused = batch._publish_immutable_artifact(artifact, b"generation-bytes")
    assert first.overwrote_existing is False
    assert reused.overwrote_existing is False

    with pytest.raises(batch.AnalogFourPatchBatchPublicationError) as exc_info:
        batch._publish_immutable_artifact(artifact, b"different-bytes")
    assert exc_info.value.error_code == "write_failed"
    assert artifact.read_bytes() == b"generation-bytes"


def test_publication_failure_surfaces_lock_cleanup_note(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    real_atomic_write = batch.atomic_write

    def fail_sidecar(path: Path, data: bytes, *, overwrite: bool = False):
        if "-c01-" in path.name and path.suffix == ".json":
            raise OSError("publication failed")
        return real_atomic_write(path, data, overwrite=overwrite)

    monkeypatch.setattr(batch, "atomic_write", fail_sidecar)
    monkeypatch.setattr(batch, "_release_batch_lock", lambda _path, **_kwargs: "lock busy")

    with pytest.raises(OSError, match="publication failed") as exc_info:
        _export(tmp_path, candidate_count=1)

    assert "batch lock cleanup failure: lock busy" in exc_info.value.__notes__


def test_release_batch_lock_reports_unlink_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    lock_path = tmp_path / "batch.lock"
    lock_args = {
        "generation_id": "a" * 32,
        "publication_nonce": "b" * 32,
        "audio_sha256": "c" * 64,
        "source_kit_sha256": "d" * 64,
    }
    batch._acquire_batch_lock(lock_path, **lock_args)
    real_unlink = Path.unlink

    def fail_lock_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path == lock_path:
            raise OSError("lock busy")
        real_unlink(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "unlink", fail_lock_unlink)
    assert (
        batch._release_batch_lock(lock_path, **lock_args)
        == f"{lock_path.name}: OSError; lock retained"
    )


def test_batch_lock_contains_recovery_metadata_and_has_distinct_error(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    lock_path = tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock"
    write = batch._acquire_batch_lock(
        lock_path,
        generation_id="a" * 32,
        publication_nonce="1" * 32,
        audio_sha256="b" * 64,
        source_kit_sha256="c" * 64,
    )
    metadata = json.loads(write.path.read_text(encoding="utf-8"))
    assert metadata["generation_id"] == "a" * 32
    assert metadata["publication_nonce"] == "1" * 32
    assert metadata["process_id"] > 0
    assert metadata["audio_sha256"] == "b" * 64

    with pytest.raises(batch.AnalogFourPatchBatchLockedError) as exc_info:
        batch._acquire_batch_lock(
            lock_path,
            generation_id="d" * 32,
            publication_nonce="2" * 32,
            audio_sha256="e" * 64,
            source_kit_sha256="f" * 64,
        )
    assert exc_info.value.error_code == "publication_locked"
    assert "remove it only after confirming its process is no longer running" in str(exc_info.value)


def test_batch_lock_contention_handles_unreadable_recovery_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    lock_path = tmp_path / "batch.lock"
    lock_path.write_bytes(b"locked")
    real_read_text = Path.read_text

    def fail_lock_read(path: Path, *args: object, **kwargs: object) -> str:
        if path == lock_path:
            raise OSError("metadata busy")
        return real_read_text(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "read_text", fail_lock_read)
    with pytest.raises(
        batch.AnalogFourPatchBatchLockedError,
        match="recovery metadata: unavailable",
    ):
        batch._acquire_batch_lock(
            lock_path,
            generation_id="a" * 32,
            publication_nonce="1" * 32,
            audio_sha256="b" * 64,
            source_kit_sha256="c" * 64,
        )


def test_batch_lock_contention_handles_non_utf8_recovery_metadata(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    lock_path = tmp_path / "batch.lock"
    lock_path.write_bytes(b"\xff")
    with pytest.raises(
        batch.AnalogFourPatchBatchLockedError,
        match="recovery metadata: unavailable",
    ):
        batch._acquire_batch_lock(
            lock_path,
            generation_id="a" * 32,
            publication_nonce="1" * 32,
            audio_sha256="b" * 64,
            source_kit_sha256="c" * 64,
        )


def test_batch_error_code_has_bounded_unknown_fallback() -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    assert (
        batch._batch_export_error_code(
            RuntimeWarning("unexpected failure"),
            source_reads_complete=True,
            output_phase_started=False,
        )
        == "inference_failed"
    )


@pytest.mark.parametrize(
    ("error", "source_reads_complete", "output_phase_started", "error_code"),
    [
        (PermissionError("denied"), False, False, "permission_denied"),
        (FileNotFoundError("missing input"), False, False, "input_not_found"),
        (FileNotFoundError("missing inference file"), True, False, "inference_failed"),
        (FileNotFoundError("missing artifact"), True, True, "write_failed"),
        (OSError("read"), False, False, "source_read_failed"),
    ],
)
def test_batch_error_code_covers_permission_and_source_read_failures(
    error: OSError,
    source_reads_complete: bool,
    output_phase_started: bool,
    error_code: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    assert (
        batch._batch_export_error_code(
            error,
            source_reads_complete=source_reads_complete,
            output_phase_started=output_phase_started,
        )
        == error_code
    )


def test_batch_lock_match_rejects_malformed_metadata(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    lock_path = tmp_path / "batch.lock"
    lock_path.write_text("not-json", encoding="utf-8")
    assert not batch._batch_lock_matches_request(
        lock_path,
        generation_id="a" * 32,
        publication_nonce="1" * 32,
        audio_sha256="b" * 64,
        source_kit_sha256="c" * 64,
    )


def test_batch_export_lock_contention_does_not_release_another_process_lock(
    tmp_path: Path,
    _mocked_inference: None,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    lock_path = tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text('{"process_id": 999999}', encoding="utf-8")

    with pytest.raises(batch.AnalogFourPatchBatchLockedError):
        _export(tmp_path, candidate_count=1)

    assert lock_path.read_text(encoding="utf-8") == '{"process_id": 999999}'


def test_interrupted_acquisition_does_not_release_same_process_lock_with_other_nonce(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    real_acquire = batch._acquire_batch_lock

    def publish_other_lock_then_interrupt(lock_path: Path, **kwargs: object):
        other_kwargs = dict(kwargs)
        other_kwargs["publication_nonce"] = "f" * 32
        real_acquire(lock_path, **other_kwargs)  # type: ignore[arg-type]
        raise KeyboardInterrupt("interrupted concurrent acquisition")

    monkeypatch.setattr(batch, "_acquire_batch_lock", publish_other_lock_then_interrupt)
    with pytest.raises(KeyboardInterrupt, match="interrupted concurrent acquisition"):
        _export(tmp_path, candidate_count=1)

    lock_path = tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock"
    metadata = json.loads(lock_path.read_text(encoding="utf-8"))
    assert metadata["publication_nonce"] == "f" * 32


def test_export_audio_patch_batch_surfaces_lock_cleanup_failure(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    logged: list[str] = []
    reset_metrics()
    monkeypatch.setattr(batch, "_release_batch_lock", lambda _path, **_kwargs: "lock busy")
    monkeypatch.setattr(batch._logger, "error", lambda message, **_kwargs: logged.append(message))

    result = _export(tmp_path, candidate_count=1)

    assert logged == ["Analog Four audio patch batch lock cleanup failed"]
    assert result.lock_cleanup_warning is not None
    assert "batch committed successfully" in result.lock_cleanup_warning
    assert get_metrics().errors_by_kind["a4_audio_patch_batch_lock_cleanup"] == 1
    assert get_metrics().export_count == 1
    assert (tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock").exists()
    assert (tmp_path / "batch" / "a4-t2-audio-patch-batch.json").exists()


@pytest.mark.parametrize("signal_type", [KeyboardInterrupt, SystemExit])
def test_post_manifest_cleanup_interrupt_is_a_success_warning(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
    signal_type: type[BaseException],
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    gate_path = tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock.operation"
    real_rmdir = Path.rmdir
    gate_cleanup_attempts = 0

    def interrupt_once(path: Path) -> None:
        nonlocal gate_cleanup_attempts
        if path == gate_path:
            gate_cleanup_attempts += 1
        if path == gate_path and gate_cleanup_attempts == 2:
            raise signal_type("cleanup interrupted after commit")
        real_rmdir(path)

    reset_metrics()
    monkeypatch.setattr(Path, "rmdir", interrupt_once)

    result = _export(tmp_path, candidate_count=1)

    assert gate_cleanup_attempts == 4
    assert result.lock_cleanup_warning is not None
    assert "cleanup interrupted after manifest commit" in result.lock_cleanup_warning
    assert "best-effort cleanup retry completed" in result.lock_cleanup_warning
    assert result.manifest_path.exists()
    assert not (tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock").exists()
    metrics = get_metrics()
    assert metrics.export_count == 1
    assert not metrics.export_errors_by_code


def test_cleanup_interrupt_does_not_mask_pre_manifest_failure(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    real_atomic_write = batch.atomic_write
    real_release = batch._release_batch_lock
    release_attempts = 0

    def interrupt_manifest(path: Path, data: bytes, *, overwrite: bool = False):
        if path.name == "a4-t2-audio-patch-batch.json":
            raise KeyboardInterrupt("manifest interrupted")
        return real_atomic_write(path, data, overwrite=overwrite)

    def interrupt_cleanup_once(lock_path: Path, **owner: str) -> str | None:
        nonlocal release_attempts
        release_attempts += 1
        if release_attempts == 1:
            raise SystemExit("cleanup interrupted")
        return real_release(lock_path, **owner)

    monkeypatch.setattr(batch, "atomic_write", interrupt_manifest)
    monkeypatch.setattr(batch, "_release_batch_lock", interrupt_cleanup_once)

    with pytest.raises(KeyboardInterrupt, match="manifest interrupted") as exc_info:
        _export(tmp_path, candidate_count=1)

    assert release_attempts == 2
    assert "lock cleanup interrupted while publication failed" in exc_info.value.__notes__[0]
    assert not (tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock").exists()


@pytest.mark.parametrize("retry_mode", ["failure", "interrupt"])
def test_post_manifest_cleanup_retry_failure_remains_a_success_warning(
    tmp_path: Path,
    _mocked_inference: None,
    monkeypatch: pytest.MonkeyPatch,
    retry_mode: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    release_attempts = 0

    def fail_cleanup(lock_path: Path, **owner: str) -> str | None:
        nonlocal release_attempts
        del lock_path, owner
        release_attempts += 1
        if release_attempts == 1:
            raise KeyboardInterrupt("cleanup interrupted")
        if retry_mode == "interrupt":
            raise SystemExit("cleanup retry interrupted")
        return "lock retained by test"

    reset_metrics()
    monkeypatch.setattr(batch, "_release_batch_lock", fail_cleanup)

    result = _export(tmp_path, candidate_count=1)

    assert release_attempts == 2
    assert result.lock_cleanup_warning is not None
    assert "retry result" in result.lock_cleanup_warning
    if retry_mode == "interrupt":
        assert "best-effort cleanup retry interrupted" in result.lock_cleanup_warning
    else:
        assert "lock retained by test" in result.lock_cleanup_warning
    assert result.manifest_path.exists()
    lock_path = tmp_path / "batch" / ".a4-t2-audio-patch-batch.lock"
    assert lock_path.exists()
    lock_path.unlink()
    metrics = get_metrics()
    assert metrics.export_count == 1
    assert not metrics.export_errors_by_code


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


@pytest.mark.parametrize(
    ("screen_value", "message"),
    [
        ("not-a-number", "must be a decimal integer"),
        ("01", "must be in 0..127"),
        ("128", "must be in 0..127"),
    ],
)
def test_filter2_resonance_gene_rejects_invalid_screen_values(
    screen_value: str,
    message: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    candidate = _inference(track=2, candidate_count=1).genome.candidates[0]
    resonance = next(
        gene
        for gene in candidate.genes
        if gene.value.parameter == batch.FILTER2_RESONANCE_PARAMETER
    )
    invalid_resonance = replace(
        resonance,
        value=replace(resonance.value, screen_value=screen_value),
    )
    invalid_candidate = replace(
        candidate,
        genes=tuple(invalid_resonance if gene is resonance else gene for gene in candidate.genes),
    )

    with pytest.raises(ValueError, match=message):
        batch._filter2_resonance_gene(invalid_candidate, track=2)


def test_filter2_resonance_gene_rejects_wrong_track() -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    candidate = _inference(track=2, candidate_count=1).genome.candidates[0]
    resonance = next(
        gene
        for gene in candidate.genes
        if gene.value.parameter == batch.FILTER2_RESONANCE_PARAMETER
    )
    invalid_resonance = replace(resonance, track=3)
    invalid_candidate = replace(
        candidate,
        genes=tuple(invalid_resonance if gene is resonance else gene for gene in candidate.genes),
    )

    with pytest.raises(ValueError, match="targets track 3, expected 2"):
        batch._filter2_resonance_gene(invalid_candidate, track=2)


def test_prepare_candidates_requires_requested_contiguous_columns() -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    one_candidate = _inference(track=2, candidate_count=1)
    with pytest.raises(ValueError, match="contiguous candidate columns"):
        batch._prepare_candidates(
            one_candidate,
            track=2,
            candidate_count=2,
        )

    two_candidates = _inference(track=2, candidate_count=2)
    duplicate_columns = replace(
        two_candidates.genome,
        candidates=(
            two_candidates.genome.candidates[0],
            replace(two_candidates.genome.candidates[1], column=1),
        ),
    )
    invalid = replace(two_candidates, genome=duplicate_columns)
    with pytest.raises(ValueError, match="contiguous candidate columns"):
        batch._prepare_candidates(
            invalid,
            track=2,
            candidate_count=2,
        )


def test_preflight_destinations_rejects_duplicate_paths(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch as batch

    duplicate = tmp_path / "candidate.syx"
    with pytest.raises(ValueError, match="destinations are not unique"):
        batch._preflight_destinations((duplicate, duplicate), overwrite=True)


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

    monkeypatch.setattr(public_api, "build_analog_four_audio_patch_genome_isolated", fake_build)
    result = batch._build_audio_inference(tmp_path / "audio.wav", track=3, candidate_count=1)

    assert observed == {"path": tmp_path / "audio.wav", "track": 3, "candidate_count": 1}
    assert result.audio_features_payload["audio_sha256"] == "b" * 64
    assert result.genome_payload["selected_track"] == 3

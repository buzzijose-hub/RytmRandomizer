"""Sample-exact audio and fail-closed local reference-sound persistence."""

from __future__ import annotations

import dataclasses
import json
import stat
import sys
import wave
from io import BytesIO
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from cockpit.conftest import make_reference_pcm

from rytm_randomizer.cockpit.export import reference_sound_store as store_module
from rytm_randomizer.cockpit.export.reference_sound_analysis import (
    sound_analysis_from_dict,
    sound_analysis_to_dict,
    sound_integer,
    sound_mapping,
    sound_number,
    sound_string_tuple,
    sound_text,
)
from rytm_randomizer.cockpit.export.reference_sound_audio import (
    REFERENCE_AUDIO_MAX_BYTES,
    inspect_reference_audio,
    select_reference_segment,
)
from rytm_randomizer.cockpit.export.reference_sound_store import (
    ReferenceSoundStore,
    default_reference_sound_dir,
    reference_sound_digest,
    reference_sound_json,
    require_sound_session_id,
    sound_artifact_name,
)
from rytm_randomizer.observability.errors import BoundaryError, DataError
from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

pytestmark = pytest.mark.fast


_wav = make_reference_pcm


def _payload() -> dict[str, object]:
    return {"schema_version": 1, "session_id": "sound-" + "a" * 32, "favorite": False}


def test_segment_retains_original_identity_and_exact_interleaved_samples() -> None:
    original = _wav(channels=2)
    selected = select_reference_segment(original, start_frame=128, frame_count=512)
    assert selected.original.sha256 == reference_sound_digest(original)
    assert selected.original.to_dict()["seconds"] == 0.1
    assert selected.to_dict()["sha256"] == reference_sound_digest(selected.wav)
    with (
        wave.open(BytesIO(original), "rb") as whole,
        wave.open(BytesIO(selected.wav), "rb") as part,
    ):
        whole.setpos(128)
        assert part.readframes(512) == whole.readframes(512)
        assert part.getparams()[:3] == whole.getparams()[:3]
    assert inspect_reference_audio(original).frame_count == 800


@pytest.mark.parametrize("width", [2, 3, 4])
def test_supported_pcm_widths_preserve_segment_bytes(width: int) -> None:
    samples = tuple(
        (-1 if index % 2 else 1) * (index % 101 + 1) * (1 << (width * 8 - 9))
        for index in range(1600)
    )
    original = _wav(width=width, channels=2, sample_values=samples)
    selected = select_reference_segment(original, start_frame=128, frame_count=512)
    assert inspect_reference_audio(original).sample_width == width
    assert selected.original.sha256 == reference_sound_digest(original)
    expected = b"".join(value.to_bytes(width, "little", signed=True) for value in samples[256:1280])
    with wave.open(BytesIO(selected.wav), "rb") as part:
        assert part.getsampwidth() == width and part.getnchannels() == 2
        assert part.getnframes() == 512
        assert part.readframes(512) == expected


@pytest.mark.parametrize(
    "value",
    [None, b"bad", b"\0" * (REFERENCE_AUDIO_MAX_BYTES + 1), b"RIFF" + b"\0" * 64],
    ids=["wrong-type", "short", "oversize", "invalid-header"],
)
def test_invalid_audio_refuses_before_native_analysis(value: bytes) -> None:
    with pytest.raises(ValueError):
        inspect_reference_audio(value)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rate": 7999},
        {"rate": 96001},
        {"channels": 3},
        {"width": 1},
        {"frames": 0},
        {"frames": 960001},
    ],
)
def test_pcm_header_bounds_are_enforced(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        inspect_reference_audio(_wav(**kwargs))


def test_truncated_pcm_is_not_accepted() -> None:
    with pytest.raises(ValueError, match="truncated"):
        inspect_reference_audio(_wav()[:-10])


@pytest.mark.parametrize(
    "start,count",
    [(True, 500), (-1, 500), (0, True), (0.5, 500), (0, 399), (64900, 801), (0, 64001)],
)
def test_invalid_sample_selection_refuses(start: int, count: int) -> None:
    with pytest.raises(ValueError):
        select_reference_segment(_wav(frames=65000), start_frame=start, frame_count=count)


def test_persistence_reopens_exact_original_and_segment_without_external_source(
    tmp_path: Path,
) -> None:
    store = ReferenceSoundStore(tmp_path / "sounds")
    assert store.catalog() == ()
    audio = _wav()
    digest = reference_sound_digest(audio)
    store.publish(_payload(), {sound_artifact_name(digest, "wav"): audio})
    reopened = ReferenceSoundStore(store.directory)
    assert reopened.load(str(_payload()["session_id"])) == _payload()
    assert reopened.read_artifact(digest, "wav") == audio
    assert reopened.catalog() == (_payload(),)
    store.publish(_payload(), {sound_artifact_name(digest, "wav"): audio})
    assert {path.name for path in store.directory.iterdir()} == {
        sound_artifact_name(digest, "wav"),
        f"{_payload()['session_id']}.sound.json",
        ".sound-publication.lock",
    }


def test_distinct_store_writers_are_serialized_and_stale_manifest_is_refused(
    tmp_path: Path,
) -> None:
    first, second = ReferenceSoundStore(tmp_path), ReferenceSoundStore(tmp_path)
    first.publish(_payload(), {})
    expected = reference_sound_digest(reference_sound_json(_payload()))
    with first._publication_guard():
        with pytest.raises(OSError):
            second.publish({**_payload(), "favorite": True}, {}, expected_manifest=expected)
    assert second.load(str(_payload()["session_id"])) == _payload()
    newer = {**_payload(), "favorite": True}
    second.publish(newer, {}, expected_manifest=expected)
    with pytest.raises(BoundaryError, match="changed while working"):
        first.publish(_payload(), {}, expected_manifest=expected)
    assert first.load(str(_payload()["session_id"])) == newer
    with pytest.raises(BoundaryError, match="changed while working"):
        first.publish(newer, {}, expected_manifest=None)
    with pytest.raises(BoundaryError, match="changed while working"):
        first.publish(
            {**_payload(), "session_id": "sound-" + "b" * 32}, {}, expected_manifest=expected
        )


def test_posix_publication_lock_contract_and_invalid_namespace_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[int, int]] = []
    module = ModuleType("fcntl")
    module.LOCK_EX, module.LOCK_NB, module.LOCK_UN = 1, 2, 4
    module.flock = lambda descriptor, mode: calls.append((descriptor, mode))
    monkeypatch.setitem(sys.modules, "fcntl", module)
    monkeypatch.setattr(store_module, "_WINDOWS_PUBLICATION_LOCK", False)
    with ReferenceSoundStore(tmp_path)._publication_guard():
        assert len(calls) == 1 and calls[0][1] == 3
    assert calls[1] == (calls[0][0], 4)
    monkeypatch.setattr(store_module.os, "fstat", lambda _fd: SimpleNamespace(st_mode=stat.S_IFDIR))
    with pytest.raises(ValueError, match="namespace"):
        with ReferenceSoundStore(tmp_path)._publication_guard():
            pytest.fail("An invalid namespace must not enter publication.")


def test_future_or_malformed_schema_preserves_all_saved_bytes(tmp_path: Path) -> None:
    from rytm_randomizer.observability.errors import PersistedStateVersionError

    store = ReferenceSoundStore(tmp_path)
    store.publish(_payload(), {})
    path = tmp_path / f"{_payload()['session_id']}.sound.json"
    future = {**_payload(), "schema_version": 2}
    future["content_sha256"] = reference_sound_digest(reference_sound_json(future))
    path.write_bytes(reference_sound_json(future))
    before = path.read_bytes()
    with pytest.raises(PersistedStateVersionError):
        store.load(str(_payload()["session_id"]))
    assert path.read_bytes() == before
    path.write_bytes(b"{broken")
    with pytest.raises(DataError, match="corrupt"):
        store.load(str(_payload()["session_id"]))
    assert path.read_bytes() == b"{broken"


def test_failed_publication_preserves_existing_favorite_and_all_retained_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ReferenceSoundStore(tmp_path)
    store.publish(_payload(), {})
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("private path must not become a user-facing error")

    monkeypatch.setattr(store_module, "atomic_write_set", fail)
    with pytest.raises(OSError):
        store.publish({**_payload(), "favorite": True}, {})
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_artifact_drift_and_manifest_corruption_refuse(tmp_path: Path) -> None:
    store = ReferenceSoundStore(tmp_path)
    data = _wav()
    digest = reference_sound_digest(data)
    name = sound_artifact_name(digest, "wav")
    store.publish(_payload(), {name: data})
    (tmp_path / name).write_bytes(_wav(frames=801))
    with pytest.raises(DataError, match="changed"):
        store.read_artifact(digest, "wav")
    path = tmp_path / f"{_payload()['session_id']}.sound.json"
    document = json.loads(path.read_text())
    document["favorite"] = True
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="corrupt"):
        store.load(str(_payload()["session_id"]))


@pytest.mark.parametrize("value", ["../escape", "sound-a", None])
def test_session_ids_never_become_arbitrary_paths(value: str) -> None:
    with pytest.raises(ValueError):
        require_sound_session_id(value)


@pytest.mark.parametrize(
    "digest,extension", [("../escape", "wav"), ("a" * 64, "json"), ("A" * 64, "syx")]
)
def test_artifact_paths_require_hashes_and_known_extensions(digest: str, extension: str) -> None:
    with pytest.raises(ValueError):
        sound_artifact_name(digest, extension)


def test_analysis_roundtrip_preserves_native_measurements(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    assert (
        sound_analysis_from_dict(sound_analysis_to_dict(audio_patch_dna_analysis))
        == audio_patch_dna_analysis
    )
    unresolved = dataclasses.replace(
        audio_patch_dna_analysis,
        dna_evidence=dataclasses.replace(
            audio_patch_dna_analysis.dna_evidence, dominant_frequency_hz=None, dominant_note=None
        ),
    )
    assert sound_analysis_from_dict(sound_analysis_to_dict(unresolved)) == unresolved


@pytest.mark.parametrize(
    "parser,value",
    [
        (sound_mapping, []),
        (sound_text, ""),
        (sound_text, 1),
        (sound_text, "a" * 1025),
        (sound_number, True),
        (sound_number, float("nan")),
        (sound_number, "1"),
        (sound_integer, 1.1),
        (sound_integer, True),
        (sound_string_tuple, "a"),
        (sound_string_tuple, ["a", "a"]),
        (sound_string_tuple, ["x"] * 257),
    ],
    ids=[f"invalid-metadata-{index}" for index in range(12)],
)
def test_corrupt_typed_metadata_is_not_coerced(parser: object, value: object) -> None:
    with pytest.raises(ValueError):
        parser(value)


def test_scalar_parsers_and_default_directory() -> None:
    assert sound_integer(1) == 1
    assert sound_string_tuple(["a", "b"]) == ("a", "b")
    assert ReferenceSoundStore().directory == default_reference_sound_dir()
    assert reference_sound_json({"a": 1}) == b'{"a":1}\n'


@pytest.mark.parametrize("schema", [True, 2])
def test_schema_version_must_be_the_exact_integer(tmp_path: Path, schema: object) -> None:
    with pytest.raises(ValueError, match="incompatible"):
        ReferenceSoundStore(tmp_path).publish({**_payload(), "schema_version": schema}, {})


@pytest.mark.parametrize(
    "kind", ["manifest", "existing-files", "sessions", "new-files", "storage", "catalog"]
)
def test_storage_limits_refuse_without_overwriting_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    store = ReferenceSoundStore(tmp_path)
    store.publish(_payload(), {})
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    payload = {**_payload(), "session_id": "sound-" + "b" * 32}
    if kind == "manifest":
        monkeypatch.setattr(store_module, "REFERENCE_SOUND_MAX_MANIFEST_BYTES", 1)
    elif kind == "existing-files":
        monkeypatch.setattr(store_module, "REFERENCE_SOUND_MAX_FILES", 0)
    elif kind == "new-files":
        monkeypatch.setattr(store_module, "REFERENCE_SOUND_MAX_FILES", 1)
    elif kind == "storage":
        monkeypatch.setattr(store_module, "REFERENCE_SOUND_MAX_TOTAL_BYTES", 1)
    else:
        monkeypatch.setattr(store_module, "REFERENCE_SOUND_MAX_SESSIONS", 0)
    with pytest.raises(BoundaryError) as refused:
        if kind == "catalog":
            store.catalog()
        else:
            store.publish(payload, {})
    assert refused.value.context["error_code"] == (
        "manifest_limit"
        if kind == "manifest"
        else "session_limit" if kind in ("sessions", "catalog") else "storage_limit"
    )
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize(
    "name,data",
    [
        ("escape", b"a"),
        ("a" * 64 + ".wav", b""),
        ("a" * 64 + ".wav", "a"),
        ("a" * 64 + ".wav", b"wrong-hash"),
    ],
    ids=["invalid-name", "empty", "wrong-type", "hash-mismatch"],
)
def test_invalid_artifact_publication_preserves_previous_manifest(
    tmp_path: Path, name: str, data: bytes
) -> None:
    store = ReferenceSoundStore(tmp_path)
    store.publish(_payload(), {})
    before = store.load(str(_payload()["session_id"]))
    with pytest.raises(ValueError):
        store.publish({**_payload(), "favorite": True}, {name: data})
    assert store.load(str(_payload()["session_id"])) == before


def test_corrupt_nonobject_manifest_refuses(tmp_path: Path) -> None:
    (tmp_path / f"{_payload()['session_id']}.sound.json").write_text("[]")
    with pytest.raises(DataError, match="corrupt"):
        ReferenceSoundStore(tmp_path).load(str(_payload()["session_id"]))


def test_non_directory_storage_refuses(tmp_path: Path) -> None:
    path = tmp_path / "not-a-directory"
    path.write_bytes(b"no")
    with pytest.raises(ValueError, match="regular directory"):
        ReferenceSoundStore(path).read_artifact("a" * 64, "wav")


@pytest.mark.parametrize("arc", [None, [0.0] * 33])
def test_invalid_energy_arc_refuses(
    audio_patch_dna_analysis: AudioFeatureAnalysis, arc: object
) -> None:
    payload = sound_analysis_to_dict(audio_patch_dna_analysis)
    payload["report"]["energy_arc"] = arc
    with pytest.raises(ValueError, match="energy"):
        sound_analysis_from_dict(payload)

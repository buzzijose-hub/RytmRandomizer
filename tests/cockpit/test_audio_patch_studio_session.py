"""Tests for the resumable passive Audio-to-Patch studio session."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

import pytest

from rytm_randomizer.cockpit.export import audio_patch_studio_session as service
from rytm_randomizer.cockpit.export.analog_four_export_contracts import (
    analog_four_export_error_code,
)

pytestmark = pytest.mark.fast


@dataclass(frozen=True)
class _SelectedDirection:
    column: int = 6
    key: str = "atmospheric"
    label: str = "Atmospheric"
    role: str = "spacious slower-motion interpretation"
    closeness: int = 76


@dataclass(frozen=True)
class _RenderedSysex:
    sha256: str


@dataclass(frozen=True)
class _SysexExport:
    render: _RenderedSysex


@dataclass(frozen=True)
class _ExportCandidate:
    column: int
    sysex_path: Path
    sidecar_path: Path
    sysex_export: _SysexExport
    sidecar_sha256: str

    @property
    def candidate(self) -> int:
        return self.column


@dataclass(frozen=True)
class _A4Export:
    generation_id: str
    manifest_path: Path
    candidates: tuple[_ExportCandidate, ...]
    candidate_count: int
    track: int
    audio_sha256: str
    source_kit_sha256: str
    manifest_sha256: str


@dataclass(frozen=True)
class _DnaResult:
    json_path: Path
    markdown_path: Path
    selected_candidate: _SelectedDirection | None
    analog_four_export: _A4Export | None


@dataclass(frozen=True)
class _RefinementPlan:
    action: Literal["accept", "refine"]
    similarity: int


@dataclass(frozen=True)
class _RefinementResult:
    plan: _RefinementPlan
    json_path: Path
    markdown_path: Path
    analog_four_export: _A4Export | None
    payload: dict[str, object]


def _write(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _artifact_hash(path: Path) -> str:
    return service._sha256_file(path)


def _a4_export(
    output_dir: Path,
    *,
    generation_id: str,
    audio_sha256: str,
    source_kit_sha256: str,
    candidate: int = 1,
    candidate_count: int = 1,
    track: int = 2,
    sysex_content: bytes = b"offline-sysex",
) -> _A4Export:
    manifest_path = _write(
        output_dir / "manifest.json",
        json.dumps({"candidate": candidate}).encode("utf-8") + b"\n",
    )
    sysex_path = _write(output_dir / "candidate.syx", sysex_content)
    sidecar_path = _write(output_dir / "candidate.json", b"{}\n")
    return _A4Export(
        generation_id=generation_id,
        manifest_path=manifest_path,
        candidates=(
            _ExportCandidate(
                column=candidate,
                sysex_path=sysex_path,
                sidecar_path=sidecar_path,
                sysex_export=_SysexExport(render=_RenderedSysex(sha256=_artifact_hash(sysex_path))),
                sidecar_sha256=_artifact_hash(sidecar_path),
            ),
        ),
        candidate_count=candidate_count,
        track=track,
        audio_sha256=audio_sha256,
        source_kit_sha256=source_kit_sha256,
        manifest_sha256=_artifact_hash(manifest_path),
    )


def _dna_result(
    output_dir: Path,
    *,
    audio_sha256: str,
    source_kit_sha256: str,
    candidate: int = 1,
) -> _DnaResult:
    selected_dir = output_dir / "selected-a4"
    return _DnaResult(
        json_path=_write(output_dir / "audio-patch-dna.json", b'{"directions": 8}\n'),
        markdown_path=_write(output_dir / "audio-patch-dna.md", b"# DNA\n"),
        selected_candidate=_SelectedDirection(),
        analog_four_export=_a4_export(
            selected_dir,
            generation_id="generation-selected",
            audio_sha256=audio_sha256,
            source_kit_sha256=source_kit_sha256,
            candidate=candidate,
        ),
    )


def _start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    manifest_candidate: int = 1,
) -> tuple[service.AudioPatchStudioSessionResult, Path, Path, list[dict[str, object]]]:
    reference = _write(tmp_path / "reference.wav", b"reference-audio")
    source_kit = _write(tmp_path / "source.syx", b"source-kit")
    session_root = tmp_path / "session"
    calls: list[dict[str, object]] = []

    def fake_export(**kwargs: object) -> _DnaResult:
        calls.append(kwargs)
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        return _dna_result(
            output_dir,
            audio_sha256=_artifact_hash(reference),
            source_kit_sha256=_artifact_hash(source_kit),
            candidate=manifest_candidate,
        )

    monkeypatch.setattr(service, "export_audio_patch_dna_workspace", fake_export)
    result = service.start_audio_patch_studio_session(
        reference_audio_path=reference,
        source_kit_path=source_kit,
        selection=6,
        output_dir=session_root,
        track=2,
    )
    return result, reference, source_kit, calls


def _refinement_result(
    output_dir: Path,
    *,
    action: Literal["accept", "refine"],
    reference_sha256: str,
    render_sha256: str,
    source_kit_sha256: str,
    correction_gain: float = 0.35,
    accept_similarity: int = 88,
    candidate: int = 1,
    track: int = 2,
) -> _RefinementResult:
    next_export: _A4Export | None = None
    similarity = 94 if action == "accept" else 72
    if action == "refine":
        next_dir = output_dir / "refined-a4"
        next_export = _a4_export(
            next_dir,
            generation_id="generation-refined",
            audio_sha256=reference_sha256,
            source_kit_sha256=source_kit_sha256,
            candidate=candidate,
            track=track,
            sysex_content=b"refined-sysex",
        )
    next_payload = None
    if next_export is not None:
        next_payload = {
            "generation_id": next_export.generation_id,
            "manifest_path": str(next_export.manifest_path),
            "manifest_sha256": next_export.manifest_sha256,
            "sysex_path": str(next_export.candidates[0].sysex_path),
            "sidecar_path": str(next_export.candidates[0].sidecar_path),
            "safety": [],
        }
    return _RefinementResult(
        plan=_RefinementPlan(action=action, similarity=similarity),
        json_path=_write(output_dir / "analog-four-patch-refinement.json", b"{}\n"),
        markdown_path=_write(output_dir / "analog-four-patch-refinement.md", b"# Result\n"),
        analog_four_export=next_export,
        payload={
            "schema_version": "test",
            "selection": {
                "generation_id": "generation-selected",
                "manifest_path": "manifest.json",
                "candidate": candidate,
                "label": "Atmospheric",
                "track": track,
            },
            "reference_audio": {
                "path": "reference.wav",
                "sha256": reference_sha256,
            },
            "render_audio": {"path": "render.wav", "sha256": render_sha256},
            "plan": {
                "action": action,
                "similarity": similarity,
                "candidate": candidate,
                "label": "Atmospheric",
                "selected_track": track,
                "correction_gain": correction_gain,
                "accept_similarity": accept_similarity,
                "residuals": [],
                "corrected_features": {},
                "next_candidate": None,
            },
            "next_export": next_payload,
            "safety": [],
        },
    )


def _refinement_result_for_request(
    output_dir: Path,
    *,
    action: Literal["accept", "refine"],
    request: dict[str, object],
) -> _RefinementResult:
    reference_path = request["reference_audio_path"]
    render_path = request["render_audio_path"]
    source_kit_path = request["source_kit_path"]
    correction_gain = request["correction_gain"]
    accept_similarity = request["accept_similarity"]
    assert isinstance(reference_path, Path)
    assert isinstance(render_path, Path)
    assert isinstance(source_kit_path, Path)
    assert isinstance(correction_gain, float)
    assert isinstance(accept_similarity, int)
    return _refinement_result(
        output_dir,
        action=action,
        reference_sha256=_artifact_hash(reference_path),
        render_sha256=_artifact_hash(render_path),
        source_kit_sha256=_artifact_hash(source_kit_path),
        correction_gain=correction_gain,
        accept_similarity=accept_similarity,
    )


def test_start_commits_relative_hash_bound_state_and_distinct_candidate_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, reference, source_kit, calls = _start(tmp_path, monkeypatch)

    payload = result.payload
    assert len(calls) == 1
    assert calls[0]["audio_path"] == reference
    assert calls[0]["source_kit_path"] == source_kit
    assert payload["status"] == "waiting_for_render"
    assert payload["selection"]["dna_candidate"] == 6
    assert payload["selection"]["manifest_candidate"] == 1
    assert payload["selection"]["track"] == 2
    assert payload["workspace"]["json"]["path"] == "workspace/audio-patch-dna.json"
    assert payload["selected_export"]["sysex"]["path"].endswith("candidate.syx")
    assert all(not Path(item["path"]).is_absolute() for item in payload["workspace"].values())
    assert json.loads(result.json_path.read_text(encoding="utf-8"))["session_id"].startswith(
        "studio-"
    )
    assert "no MIDI ports enumerated or opened" in result.markdown_path.read_text(encoding="utf-8")
    assert not (
        result.json_path.parent
        / service.AUDIO_PATCH_STUDIO_SESSION_WORKSPACE_DIR_NAME
        / service._OUTPUT_GUARD_NAME
    ).exists()


def test_start_persists_the_exported_manifest_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, _reference, _source_kit, _calls = _start(
        tmp_path,
        monkeypatch,
        manifest_candidate=3,
    )

    assert result.payload["selection"]["dna_candidate"] == 6
    assert result.payload["selection"]["manifest_candidate"] == 3


def test_start_is_idempotent_and_rejects_tampered_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, reference, source_kit, calls = _start(tmp_path, monkeypatch)

    second = service.start_audio_patch_studio_session(
        reference_audio_path=reference,
        source_kit_path=source_kit,
        selection=6,
        output_dir=first.json_path.parent,
        track=2,
    )
    assert len(calls) == 1
    assert second.payload == first.payload

    (first.json_path.parent / "workspace" / "selected-a4" / "candidate.syx").write_bytes(
        b"tampered"
    )
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=first.json_path.parent,
            track=2,
        )


@pytest.mark.parametrize(
    ("action", "expected_status", "has_next_export"),
    [("accept", "accepted", False), ("refine", "refined", True)],
)
def test_resume_uses_manifest_candidate_one_and_commits_terminal_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: Literal["accept", "refine"],
    expected_status: str,
    has_next_export: bool,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    render = _write(tmp_path / "render.wav", b"hardware-render")
    refinement_calls: list[dict[str, object]] = []

    def fake_refinement(**kwargs: object) -> _RefinementResult:
        refinement_calls.append(kwargs)
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        return _refinement_result_for_request(
            output_dir,
            action=action,
            request=kwargs,
        )

    monkeypatch.setattr(service, "export_analog_four_patch_refinement", fake_refinement)
    result = service.resume_audio_patch_studio_session(
        session_path=started.json_path,
        reference_audio_path=reference,
        source_kit_path=source_kit,
        render_audio_path=render,
    )
    reopened = service.resume_audio_patch_studio_session(
        session_path=started.json_path,
        reference_audio_path=reference,
        source_kit_path=source_kit,
        render_audio_path=render,
    )

    assert len(refinement_calls) == 1
    assert refinement_calls[0]["candidate"] == 1
    assert refinement_calls[0]["manifest_path"] == (
        started.json_path.parent / "workspace" / "selected-a4" / "manifest.json"
    )
    assert result.payload["status"] == expected_status
    refinement = result.payload["refinement"]
    assert refinement["action"] == action
    assert ("next_export" in refinement) is has_next_export
    assert reopened.payload == result.payload
    assert service.load_audio_patch_studio_session(result.json_path).payload == result.payload


def test_resume_is_idempotent_for_same_render_and_rejects_a_different_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    render = _write(tmp_path / "render.wav", b"render-one")
    refinement_calls = 0

    def fake_refinement(**kwargs: object) -> _RefinementResult:
        nonlocal refinement_calls
        refinement_calls += 1
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        return _refinement_result_for_request(
            output_dir,
            action="accept",
            request=kwargs,
        )

    monkeypatch.setattr(service, "export_analog_four_patch_refinement", fake_refinement)
    completed = service.resume_audio_patch_studio_session(
        session_path=started.json_path,
        reference_audio_path=reference,
        source_kit_path=source_kit,
        render_audio_path=render,
    )
    reopened = service.resume_audio_patch_studio_session(
        session_path=started.json_path,
        reference_audio_path=reference,
        source_kit_path=source_kit,
        render_audio_path=render,
    )

    assert refinement_calls == 1
    assert reopened.payload == completed.payload
    other_render = _write(tmp_path / "other.wav", b"render-two")
    with pytest.raises(ValueError, match="already complete for a different render"):
        service.resume_audio_patch_studio_session(
            session_path=started.json_path,
            reference_audio_path=reference,
            source_kit_path=source_kit,
            render_audio_path=other_render,
        )
    for changed_policy in (
        {"correction_gain": 0.2},
        {"accept_similarity": 90},
    ):
        with pytest.raises(ValueError, match="different render or refinement policy"):
            service.resume_audio_patch_studio_session(
                session_path=started.json_path,
                reference_audio_path=reference,
                source_kit_path=source_kit,
                render_audio_path=render,
                **changed_policy,
            )
    assert refinement_calls == 1


def test_failed_refinement_does_not_advance_the_committed_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    render = _write(tmp_path / "render.wav", b"render")
    before = started.json_path.read_bytes()

    def fail_refinement(**_kwargs: object) -> _RefinementResult:
        raise RuntimeError("analysis failed")

    monkeypatch.setattr(service, "export_analog_four_patch_refinement", fail_refinement)
    with pytest.raises(RuntimeError, match="analysis failed"):
        service.resume_audio_patch_studio_session(
            session_path=started.json_path,
            reference_audio_path=reference,
            source_kit_path=source_kit,
            render_audio_path=render,
        )

    assert started.json_path.read_bytes() == before
    assert service.load_audio_patch_studio_session(started.json_path).payload["status"] == (
        "waiting_for_render"
    )


def test_existing_session_rejects_artifact_path_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    decoded = json.loads(started.json_path.read_text(encoding="utf-8"))
    decoded["selected_export"]["manifest"]["path"] = "../manifest.json"
    started.json_path.write_text(json.dumps(decoded), encoding="utf-8")

    with pytest.raises(ValueError, match="canonical relative POSIX path"):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=started.json_path.parent,
            track=2,
        )


def test_load_rejects_a_noncanonical_filename_and_tampered_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, _reference, _source_kit, _calls = _start(tmp_path, monkeypatch)
    renamed = started.json_path.with_name("renamed-session.json")
    renamed.write_bytes(started.json_path.read_bytes())

    with pytest.raises(ValueError, match="filename must be studio-session.json"):
        service.load_audio_patch_studio_session(renamed)

    started.markdown_path.write_text("# Tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Markdown does not match"):
        service.load_audio_patch_studio_session(started.json_path)


def test_load_uses_the_committed_markdown_digest_across_renderer_updates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, _reference, _source_kit, _calls = _start(tmp_path, monkeypatch)
    original_markdown = started.markdown_path.read_bytes()

    monkeypatch.setattr(
        service,
        "_render_session_markdown",
        lambda _payload: "# A future presentation format\n",
    )

    loaded = service.load_audio_patch_studio_session(started.json_path)

    assert loaded.payload == started.payload
    assert loaded.markdown_path.read_bytes() == original_markdown


def test_load_rejects_unexpected_nested_keys_and_cross_state_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, _reference, _source_kit, _calls = _start(tmp_path, monkeypatch)
    decoded = json.loads(started.json_path.read_text(encoding="utf-8"))
    decoded["selection"]["unexpected"] = True
    started.json_path.write_text(json.dumps(decoded), encoding="utf-8")
    with pytest.raises(ValueError, match="selection keys are invalid"):
        service.load_audio_patch_studio_session(started.json_path)

    decoded = dict(started.payload)
    decoded["refinement"] = {}
    started.json_path.write_text(json.dumps(decoded), encoding="utf-8")
    with pytest.raises(ValueError, match="waiting studio session must not contain refinement"):
        service.load_audio_patch_studio_session(started.json_path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", "future", "schema version"),
        ("status", "unknown", "status is invalid"),
        ("session_id", 1, "id is invalid"),
        ("selection", None, "selection must be an object"),
        ("safety", "passive", "safety declaration"),
        ("status", "accepted", "refinement must be an object"),
    ],
)
def test_load_rejects_malformed_committed_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
) -> None:
    started, _reference, _source_kit, _calls = _start(tmp_path, monkeypatch)
    decoded = json.loads(started.json_path.read_text(encoding="utf-8"))
    decoded[field] = value
    started.json_path.write_text(json.dumps(decoded), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        service.load_audio_patch_studio_session(started.json_path)


@pytest.mark.parametrize(
    ("content", "message"),
    [("{", "JSON is invalid"), ("[]", "must contain an object")],
)
def test_load_rejects_invalid_json_document(
    tmp_path: Path,
    content: str,
    message: str,
) -> None:
    session_path = tmp_path / "studio-session.json"
    session_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        service.load_audio_patch_studio_session(session_path)


@pytest.mark.parametrize(
    ("selection", "track"),
    [(5, 2), (6, 3)],
)
def test_existing_session_rejects_a_different_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selection: int,
    track: int,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="requested selection"):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=selection,
            output_dir=started.json_path.parent,
            track=track,
        )


@pytest.mark.parametrize("changed_file", ["reference", "source"])
def test_existing_session_rejects_changed_external_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changed_file: str,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    changed_path = reference if changed_file == "reference" else source_kit
    changed_path.write_bytes(b"changed")

    with pytest.raises(ValueError, match=f"{changed_file}.*does not match"):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=started.json_path.parent,
            track=2,
        )


@pytest.mark.parametrize("failure", ["missing_selected", "missing_export", "multiple"])
def test_start_rejects_an_invalid_dna_export_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    reference = _write(tmp_path / "reference.wav", b"reference")
    source_kit = _write(tmp_path / "source.syx", b"source")

    def fake_export(**kwargs: object) -> _DnaResult:
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        valid = _dna_result(
            output_dir,
            audio_sha256=_artifact_hash(reference),
            source_kit_sha256=_artifact_hash(source_kit),
        )
        if failure == "missing_selected":
            return _DnaResult(valid.json_path, valid.markdown_path, None, valid.analog_four_export)
        if failure == "missing_export":
            return _DnaResult(valid.json_path, valid.markdown_path, valid.selected_candidate, None)
        export = valid.analog_four_export
        assert export is not None
        return _DnaResult(
            valid.json_path,
            valid.markdown_path,
            valid.selected_candidate,
            replace(export, candidates=export.candidates * 2),
        )

    monkeypatch.setattr(service, "export_audio_patch_dna_workspace", fake_export)
    message = "requires one selected" if failure != "multiple" else "exactly one candidate"
    with pytest.raises(ValueError, match=message):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=tmp_path / "session",
            track=2,
        )


def test_start_rejects_mismatched_child_provenance_without_committing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = _write(tmp_path / "reference.wav", b"reference")
    source_kit = _write(tmp_path / "source.syx", b"source")
    session_root = tmp_path / "session"

    def fake_export(**kwargs: object) -> _DnaResult:
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        return _dna_result(
            output_dir,
            audio_sha256="0" * 64,
            source_kit_sha256=_artifact_hash(source_kit),
        )

    monkeypatch.setattr(service, "export_audio_patch_dna_workspace", fake_export)
    with pytest.raises(ValueError, match="selected export reference audio hash"):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=session_root,
            track=2,
        )

    assert not (session_root / service.AUDIO_PATCH_STUDIO_SESSION_JSON_NAME).exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("track", 1, "track does not match"),
        ("candidate_count", 2, "candidate count does not match"),
    ],
)
def test_start_rejects_a_child_export_for_a_different_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: int,
    message: str,
) -> None:
    reference = _write(tmp_path / "reference.wav", b"reference")
    source_kit = _write(tmp_path / "source.syx", b"source")
    session_root = tmp_path / "session"

    def fake_export(**kwargs: object) -> _DnaResult:
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        valid = _dna_result(
            output_dir,
            audio_sha256=_artifact_hash(reference),
            source_kit_sha256=_artifact_hash(source_kit),
        )
        export = valid.analog_four_export
        assert export is not None
        return replace(
            valid,
            analog_four_export=replace(export, **{field: value}),
        )

    monkeypatch.setattr(service, "export_audio_patch_dna_workspace", fake_export)
    with pytest.raises(ValueError, match=message):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=session_root,
            track=2,
        )

    assert not (session_root / service.AUDIO_PATCH_STUDIO_SESSION_JSON_NAME).exists()


def test_start_rejects_external_input_mutation_before_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = _write(tmp_path / "reference.wav", b"reference")
    source_kit = _write(tmp_path / "source.syx", b"source")
    session_root = tmp_path / "session"

    def fake_export(**kwargs: object) -> _DnaResult:
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        result = _dna_result(
            output_dir,
            audio_sha256=_artifact_hash(reference),
            source_kit_sha256=_artifact_hash(source_kit),
        )
        reference.write_bytes(b"mutated")
        return result

    monkeypatch.setattr(service, "export_audio_patch_dna_workspace", fake_export)
    with pytest.raises(ValueError, match="reference audio hash"):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=session_root,
            track=2,
        )

    assert not (session_root / service.AUDIO_PATCH_STUDIO_SESSION_JSON_NAME).exists()


def test_start_rejects_a_symlinked_workspace_before_child_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = _write(tmp_path / "reference.wav", b"reference")
    source_kit = _write(tmp_path / "source.syx", b"source")
    session_root = tmp_path / "session"
    outside = tmp_path / "outside"
    session_root.mkdir()
    outside.mkdir()
    try:
        (session_root / "workspace").symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")
    child_called = False

    def fake_export(**_kwargs: object) -> _DnaResult:
        nonlocal child_called
        child_called = True
        raise AssertionError("unsafe output tree reached the child exporter")

    monkeypatch.setattr(service, "export_audio_patch_dna_workspace", fake_export)
    with pytest.raises(ValueError, match="escaped the session root"):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=session_root,
            track=2,
        )

    assert child_called is False


def test_refinement_rejects_multiple_export_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    render = _write(tmp_path / "render.wav", b"render")

    def fake_refinement(**kwargs: object) -> _RefinementResult:
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        valid = _refinement_result_for_request(
            output_dir,
            action="refine",
            request=kwargs,
        )
        export = valid.analog_four_export
        assert export is not None
        return replace(
            valid,
            analog_four_export=replace(export, candidates=export.candidates * 2),
        )

    monkeypatch.setattr(service, "export_analog_four_patch_refinement", fake_refinement)
    with pytest.raises(ValueError, match="exactly one candidate"):
        service.resume_audio_patch_studio_session(
            session_path=started.json_path,
            reference_audio_path=reference,
            source_kit_path=source_kit,
            render_audio_path=render,
        )


def test_artifact_helpers_reject_absolute_and_outside_paths(tmp_path: Path) -> None:
    outside = _write(tmp_path / "outside.json", b"{}")
    session_root = tmp_path / "session"
    session_root.mkdir()

    with pytest.raises(ValueError, match="escaped the session root"):
        service._artifact_payload(session_root, outside)
    with pytest.raises(ValueError, match="path must be relative"):
        service._resolve_artifact(
            session_root,
            {"path": str(outside.resolve()), "sha256": service._sha256_file(outside)},
        )


def test_completed_markdown_requires_refinement_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, _reference, _source_kit, _calls = _start(tmp_path, monkeypatch)
    invalid = {**started.payload, "status": "accepted"}

    with pytest.raises(ValueError, match="missing refinement state"):
        service._render_session_markdown(invalid)  # type: ignore[arg-type]


def test_session_operation_records_an_interruption() -> None:
    def interrupt() -> service.AudioPatchStudioSessionResult:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        service._run_session_operation(
            operation_name="resume",
            source_path="render.wav",
            output_path="session",
            execute=interrupt,
        )


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: service._require_payload_keys({}, {"required"}, set(), "payload"),
            "missing=required",
        ),
        (
            lambda: service._require_payload_keys(
                {"required": True, "extra": True},
                {"required"},
                set(),
                "payload",
            ),
            "unexpected=extra",
        ),
        (lambda: service._require_mapping({1: "value"}, "payload"), "must be an object"),
        (lambda: service._require_nonempty_string("", "value"), "non-empty string"),
        (
            lambda: service._require_integer(True, "value", lower=0, upper=1),
            "must be an integer",
        ),
        (
            lambda: service._require_integer(2, "value", lower=0, upper=1),
            "must be in 0..1",
        ),
        (
            lambda: service._require_number(True, "value", lower=0.0, upper=1.0),
            "must be a number",
        ),
        (
            lambda: service._require_number(float("inf"), "value", lower=0.0, upper=1.0),
            "must be finite",
        ),
        (lambda: service._validate_sha256(1, "digest"), "lowercase SHA-256"),
        (lambda: service._validate_sha256("not-a-digest", "digest"), "lowercase SHA-256"),
        (lambda: service._validate_filename("../state.json", "filename"), "without directories"),
        (lambda: service._validate_filename("C:state.json", "filename"), "without directories"),
    ],
)
def test_session_value_validators_fail_closed(
    call: object,
    message: str,
) -> None:
    assert callable(call)
    with pytest.raises(ValueError, match=message):
        call()


def test_load_rejects_a_recomputed_session_id_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, _reference, _source_kit, _calls = _start(tmp_path, monkeypatch)
    decoded = json.loads(started.json_path.read_text(encoding="utf-8"))
    decoded["session_id"] = "studio-0000000000000000"
    started.json_path.write_text(json.dumps(decoded), encoding="utf-8")

    with pytest.raises(ValueError, match="id does not match"):
        service.load_audio_patch_studio_session(started.json_path)


def test_refinement_state_validation_rejects_invalid_action_and_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    render = _write(tmp_path / "render.wav", b"render")

    def fake_refinement(**kwargs: object) -> _RefinementResult:
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        return _refinement_result_for_request(
            output_dir,
            action="accept",
            request=kwargs,
        )

    monkeypatch.setattr(service, "export_analog_four_patch_refinement", fake_refinement)
    completed = service.resume_audio_patch_studio_session(
        session_path=started.json_path,
        reference_audio_path=reference,
        source_kit_path=source_kit,
        render_audio_path=render,
    )
    refinement = completed.payload["refinement"]
    assert refinement is not None

    invalid_action = dict(refinement)
    invalid_action["action"] = "unknown"
    with pytest.raises(ValueError, match="action is invalid"):
        service._validate_refinement_payload(invalid_action, status="accepted")

    inconsistent_accepted = dict(refinement)
    inconsistent_accepted["action"] = "refine"
    with pytest.raises(ValueError, match="similarity threshold"):
        service._validate_refinement_payload(inconsistent_accepted, status="accepted")

    inconsistent_accepted["similarity"] = 72
    with pytest.raises(ValueError, match="accepted studio session"):
        service._validate_refinement_payload(inconsistent_accepted, status="accepted")

    with pytest.raises(ValueError, match="refined studio session"):
        service._validate_refinement_payload(dict(refinement), status="refined")


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        ("selection", "selection does not match"),
        ("plan", "plan does not match"),
        ("missing_next", "omitted next-export provenance"),
        ("unexpected_next", "unexpected next export"),
        ("track", "track does not match"),
        ("candidate_count", "candidate count does not match"),
    ],
)
def test_resume_rejects_inconsistent_child_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    message: str,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    render = _write(tmp_path / "render.wav", b"render")

    def fake_refinement(**kwargs: object) -> _RefinementResult:
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        action: Literal["accept", "refine"] = "accept" if failure == "unexpected_next" else "refine"
        valid = _refinement_result_for_request(
            output_dir,
            action=action,
            request=kwargs,
        )
        payload = dict(valid.payload)
        if failure == "selection":
            selection = dict(payload["selection"])  # type: ignore[arg-type]
            selection["candidate"] = 2
            payload["selection"] = selection
        elif failure == "plan":
            plan = dict(payload["plan"])  # type: ignore[arg-type]
            plan["correction_gain"] = 0.2
            payload["plan"] = plan
        elif failure == "missing_next":
            payload["next_export"] = None
        elif failure in {"track", "candidate_count"}:
            export = valid.analog_four_export
            assert export is not None
            value = 1 if failure == "track" else 2
            return replace(valid, analog_four_export=replace(export, **{failure: value}))
        else:
            payload["next_export"] = {"unexpected": True}
        return replace(valid, payload=payload)

    monkeypatch.setattr(service, "export_analog_four_patch_refinement", fake_refinement)
    with pytest.raises(ValueError, match=message):
        service.resume_audio_patch_studio_session(
            session_path=started.json_path,
            reference_audio_path=reference,
            source_kit_path=source_kit,
            render_audio_path=render,
        )


def test_output_tree_validation_accepts_contained_files_and_rejects_escape(
    tmp_path: Path,
) -> None:
    session_root = tmp_path / "session"
    output_dir = session_root / "refinement"
    _write(output_dir / "nested" / "artifact.json", b"{}\n")

    service._validate_output_tree(session_root, output_dir)
    with pytest.raises(ValueError, match="output escaped"):
        service._validate_output_tree(session_root, tmp_path / "outside")


def test_output_tree_validation_propagates_walk_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_root = tmp_path / "session"
    output_dir = session_root / "workspace"
    output_dir.mkdir(parents=True)

    def fail_walk(
        _path: Path,
        *,
        followlinks: bool,
        onerror: object,
    ) -> object:
        assert followlinks is False
        assert callable(onerror)
        onerror(PermissionError("blocked subtree"))
        return iter(())

    monkeypatch.setattr(service.os, "walk", fail_walk)
    with pytest.raises(
        ValueError,
        match="studio session output traversal failed",
    ) as raised:
        service._validate_output_tree(session_root, output_dir)
    assert isinstance(raised.value.__cause__, PermissionError)
    assert str(raised.value.__cause__) == "blocked subtree"


def test_guarded_output_tree_removes_its_marker_after_child_failure(
    tmp_path: Path,
) -> None:
    session_root = tmp_path / "session"
    output_dir = session_root / "workspace"

    def fail() -> None:
        raise RuntimeError("child failed")

    with pytest.raises(RuntimeError, match="child failed"):
        service._run_in_guarded_output_tree(
            session_root,
            output_dir,
            execute=fail,
        )

    assert not (output_dir / service._OUTPUT_GUARD_NAME).exists()


def test_directory_identity_rejects_a_non_directory(tmp_path: Path) -> None:
    artifact = _write(tmp_path / "artifact.json", b"{}\n")

    with pytest.raises(ValueError, match="must remain a directory"):
        service._directory_identity(artifact)


def test_guarded_output_tree_rejects_identity_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_root = tmp_path / "session"
    output_dir = session_root / "workspace"
    identities = iter(((1, 1), (1, 2), (1, 2)))
    monkeypatch.setattr(service, "_directory_identity", lambda _path: next(identities))

    with pytest.raises(ValueError, match="identity changed"):
        service._run_in_guarded_output_tree(
            session_root,
            output_dir,
            execute=lambda: "result",
        )

    (output_dir / service._OUTPUT_GUARD_NAME).unlink()


def test_guarded_output_tree_preserves_marker_when_cleanup_identity_is_unreadable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_root = tmp_path / "session"
    output_dir = session_root / "workspace"
    calls = 0

    def identity(_path: Path) -> tuple[int, int]:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise PermissionError("metadata unavailable")
        return (1, 1)

    monkeypatch.setattr(service, "_directory_identity", identity)
    assert (
        service._run_in_guarded_output_tree(
            session_root,
            output_dir,
            execute=lambda: "result",
        )
        == "result"
    )

    guard_path = output_dir / service._OUTPUT_GUARD_NAME
    assert guard_path.exists()
    guard_path.unlink()


@pytest.mark.parametrize("reader", [service._read_text, service._sha256_file])
def test_session_file_readers_classify_missing_sources(
    tmp_path: Path,
    reader: object,
) -> None:
    assert callable(reader)
    with pytest.raises(OSError) as raised:
        reader(tmp_path / "missing")
    assert analog_four_export_error_code(raised.value) == "input_not_found"
    assert getattr(raised.value, service._SESSION_FAILURE_SOURCE_ATTR) == tmp_path / "missing"

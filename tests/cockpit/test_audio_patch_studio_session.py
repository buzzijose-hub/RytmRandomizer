"""Tests for the resumable passive Audio-to-Patch studio session."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest

from rytm_randomizer.cockpit.export import audio_patch_studio_session as service

pytestmark = pytest.mark.fast


@dataclass(frozen=True)
class _SelectedDirection:
    column: int = 6
    key: str = "atmospheric"
    label: str = "Atmospheric"
    role: str = "spacious slower-motion interpretation"
    closeness: int = 76


@dataclass(frozen=True)
class _ExportCandidate:
    sysex_path: Path
    sidecar_path: Path


@dataclass(frozen=True)
class _A4Export:
    generation_id: str
    manifest_path: Path
    candidates: tuple[_ExportCandidate, ...]


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


def _write(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _dna_result(output_dir: Path) -> _DnaResult:
    selected_dir = output_dir / "selected-a4"
    return _DnaResult(
        json_path=_write(output_dir / "audio-patch-dna.json", b'{"directions": 8}\n'),
        markdown_path=_write(output_dir / "audio-patch-dna.md", b"# DNA\n"),
        selected_candidate=_SelectedDirection(),
        analog_four_export=_A4Export(
            generation_id="generation-selected",
            manifest_path=_write(selected_dir / "manifest.json", b'{"candidate": 1}\n'),
            candidates=(
                _ExportCandidate(
                    sysex_path=_write(selected_dir / "candidate.syx", b"offline-sysex"),
                    sidecar_path=_write(selected_dir / "candidate.json", b"{}\n"),
                ),
            ),
        ),
    )


def _start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[service.AudioPatchStudioSessionResult, Path, Path, list[dict[str, object]]]:
    reference = _write(tmp_path / "reference.wav", b"reference-audio")
    source_kit = _write(tmp_path / "source.syx", b"source-kit")
    session_root = tmp_path / "session"
    calls: list[dict[str, object]] = []

    def fake_export(**kwargs: object) -> _DnaResult:
        calls.append(kwargs)
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        return _dna_result(output_dir)

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
) -> _RefinementResult:
    next_export: _A4Export | None = None
    if action == "refine":
        next_dir = output_dir / "refined-a4"
        next_export = _A4Export(
            generation_id="generation-refined",
            manifest_path=_write(next_dir / "manifest.json", b'{"candidate": 1}\n'),
            candidates=(
                _ExportCandidate(
                    sysex_path=_write(next_dir / "candidate.syx", b"refined-sysex"),
                    sidecar_path=_write(next_dir / "candidate.json", b"{}\n"),
                ),
            ),
        )
    return _RefinementResult(
        plan=_RefinementPlan(action=action, similarity=94 if action == "accept" else 72),
        json_path=_write(output_dir / "analog-four-patch-refinement.json", b"{}\n"),
        markdown_path=_write(output_dir / "analog-four-patch-refinement.md", b"# Result\n"),
        analog_four_export=next_export,
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
        return _refinement_result(output_dir, action=action)

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
        return _refinement_result(output_dir, action="accept")

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

    with pytest.raises(ValueError, match="escaped the session root"):
        service.start_audio_patch_studio_session(
            reference_audio_path=reference,
            source_kit_path=source_kit,
            selection=6,
            output_dir=started.json_path.parent,
            track=2,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", "future", "schema version"),
        ("status", "unknown", "status is invalid"),
        ("session_id", 1, "id is invalid"),
        ("selection", None, "missing required state"),
        ("safety", "passive", "safety declaration"),
        ("status", "accepted", "missing refinement state"),
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
        valid = _dna_result(output_dir)
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
            _A4Export(export.generation_id, export.manifest_path, export.candidates * 2),
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


def test_refinement_rejects_multiple_export_candidates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started, reference, source_kit, _calls = _start(tmp_path, monkeypatch)
    render = _write(tmp_path / "render.wav", b"render")

    def fake_refinement(**kwargs: object) -> _RefinementResult:
        output_dir = kwargs["output_dir"]
        assert isinstance(output_dir, Path)
        valid = _refinement_result(output_dir, action="refine")
        export = valid.analog_four_export
        assert export is not None
        return _RefinementResult(
            plan=valid.plan,
            json_path=valid.json_path,
            markdown_path=valid.markdown_path,
            analog_four_export=_A4Export(
                export.generation_id,
                export.manifest_path,
                export.candidates * 2,
            ),
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

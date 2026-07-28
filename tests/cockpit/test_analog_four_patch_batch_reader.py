"""Verified Analog Four audio-patch batch candidate reader tests."""

from __future__ import annotations

import hashlib
import io
import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from conftest import analog_four_reference_feature_report
from rytm_randomizer.cockpit.export.analog_four_patch_batch_contracts import (
    SYSEX_COVERAGE_STATEMENT,
)
from rytm_randomizer.data.analog_four_sysex_calibration import (
    A4_FILTER2_RESONANCE_PARAMETER,
)
from rytm_randomizer.style_analysis.analog_four_patch_genome import (
    analog_four_patch_candidate_to_dict,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
    AnalogFourPatchManualEvent,
    AnalogFourPatchSendEvent,
    AnalogFourPatchSendPlan,
    AnalogFourPatchSendSummary,
    analog_four_patch_send_plan_to_dict,
    build_analog_four_patch_send_plan_from_genome,
)
from rytm_randomizer.style_analysis.feature_report import FeatureReport

pytestmark = pytest.mark.fast

AUDIO_SHA256 = "a" * 64
SOURCE_KIT_SHA256 = "b" * 64
SYSEX_BYTES = b"\xf0\x00\x20\x3c\x06\x00\x01\x02\x03\xf7"
EXPECTED_CANDIDATE_1_TRANSPORT_SHA256 = (
    "1e121e7a1834cee209502fed4ded31896f9367fb47690b3f293d9a52a0e5e0d3"
)
_COVERAGE_FIELDS = (
    "dna_row_count",
    "sysex_encoded_row_count",
    "deferred_row_count",
    "sendable_row_count",
    "manual_row_count",
)


def test_candidate_coverage_requires_encoded_and_deferred_rows_to_cover_dna() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        _verify_coverage,
    )

    counts = {
        "dna_row_count": 2,
        "sysex_encoded_row_count": 0,
        "deferred_row_count": 0,
        "sendable_row_count": 1,
        "manual_row_count": 1,
    }
    candidate = {"coverage_counts": counts}
    sidecar = {
        "coverage_counts": counts,
        "hardware_applied_rows": [],
        "deferred_rows": [],
    }
    summary = AnalogFourPatchSendSummary(
        total_rows=2,
        sendable_count=1,
        manual_count=1,
        cc_event_count=1,
        nrpn_event_count=0,
        transport_message_count=1,
        ready_percentage=50,
        live_dial_path="app --arm",
        blocking_reason=None,
    )

    with pytest.raises(ValueError, match="do not cover the complete DNA"):
        _verify_coverage(candidate, sidecar, summary)


def test_reader_records_verified_and_failed_outcomes(
    tmp_path: Path,
    isolated_observability: None,
) -> None:
    assert isolated_observability is None
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )
    from rytm_randomizer.observability.logging import configure_logging
    from rytm_randomizer.observability.metrics import get_metrics

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)
    stream = io.StringIO()
    configure_logging(level="DEBUG", json=True, stream=stream)

    load_analog_four_patch_batch_candidate(manifest_path, candidate=1)
    with pytest.raises(TypeError, match="candidate"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=True)

    metrics = get_metrics()
    assert metrics.a4_patch_batch_read_count == 2
    assert metrics.a4_patch_batch_read_errors_by_code["validation"] == 1
    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    terminal = [
        record
        for record in records
        if record.get("message")
        in {
            "Analog Four patch batch candidate verified",
            "Analog Four patch batch candidate verification failed",
        }
    ]
    assert [record["outcome"] for record in terminal] == ["verified", "failed"]
    assert all(record["manifest_name"] == manifest_path.name for record in terminal)


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_reader_records_interrupted_failure_telemetry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_observability: None,
    exception_type: type[BaseException],
) -> None:
    assert isolated_observability is None
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_reader as reader
    from rytm_randomizer.observability.metrics import get_metrics

    def interrupt(_manifest_path: Path, *, candidate: int) -> None:
        del candidate
        raise exception_type()

    monkeypatch.setattr(reader, "_load_analog_four_patch_batch_candidate", interrupt)

    with pytest.raises(exception_type):
        reader.load_analog_four_patch_batch_candidate(
            tmp_path / "batch.json",
            candidate=1,
        )

    metrics = get_metrics()
    assert metrics.a4_patch_batch_read_count == 1
    assert metrics.a4_patch_batch_read_errors_by_code["interrupted"] == 1


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reference_report() -> FeatureReport:
    return analog_four_reference_feature_report(
        derived_at="2026-07-17T00:00:00Z",
    )


def _write_batch(tmp_path: Path) -> tuple[Path, dict[str, object], dict[str, object]]:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch import (
        BATCH_SCHEMA_VERSION,
        CANDIDATE_SCHEMA_VERSION,
    )

    report = _reference_report()
    static_genome = build_analog_four_patch_genome(report, track=2, candidate_count=1)
    feature_report_hash = static_genome.source_hash
    genome = replace(static_genome, source_hash=AUDIO_SHA256)
    genome_payload = analog_four_patch_genome_to_dict(genome)
    genome_sha256 = _sha256(_json_bytes(genome_payload))
    plan = build_analog_four_patch_send_plan_from_genome(
        report,
        genome,
        selected_candidate=1,
    )
    plan_payload = analog_four_patch_send_plan_to_dict(plan)
    dna: dict[str, object] = dict(
        analog_four_patch_candidate_to_dict(plan.learning_packet.selected_patch)
    )
    genes = dna["genes"]
    assert isinstance(genes, list)
    resonance_gene = next(
        gene
        for gene in genes
        if isinstance(gene, dict)
        and isinstance(gene.get("value"), dict)
        and gene["value"].get("parameter") == A4_FILTER2_RESONANCE_PARAMETER
    )
    resonance_value = resonance_gene["value"]
    assert isinstance(resonance_value, dict)
    resonance_screen_value = resonance_value["screen_value"]
    assert isinstance(resonance_screen_value, str)
    deferred_rows = [
        {**gene, "deferred_reason": "not hardware-write-validated for saved-kit SysEx"}
        for gene in genes
        if isinstance(gene, dict)
        and isinstance(gene.get("value"), dict)
        and gene["value"].get("parameter") != A4_FILTER2_RESONANCE_PARAMETER
    ]
    coverage: dict[str, object] = {
        "dna_row_count": plan.summary.total_rows,
        "sysex_encoded_row_count": 1,
        "deferred_row_count": plan.summary.total_rows - 1,
        "sendable_row_count": plan.summary.sendable_count,
        "manual_row_count": plan.summary.manual_count,
    }
    generation_id = "0123456789abcdef0123456789abcdef"
    sysex_name = "candidate-01.syx"
    sysex_sha256 = _sha256(SYSEX_BYTES)
    (tmp_path / sysex_name).write_bytes(SYSEX_BYTES)
    sidecar: dict[str, object] = {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "generation_id": generation_id,
        "audio_source": {"filename": "reference.wav"},
        "source_kit": {"filename": "initialized-kit.syx"},
        "candidate_dna": dna,
        "audio_features": {
            "audio_sha256": AUDIO_SHA256,
            "duration": 1.0,
            "attack": 0.1,
            "decay": 0.2,
            "sustain": 0.7,
            "tail": 0.3,
            "brightness": 0.63,
            "spectral_flatness": 0.11,
            "noise": 0.34,
            "low_end": 0.42,
            "harmonicity": 0.81,
            "transient": 0.74,
            "modulation": 0.22,
        },
        "dynamic_send_plan": plan_payload,
        "hardware_applied_rows": [
            {
                "parameter": A4_FILTER2_RESONANCE_PARAMETER,
                "track": 2,
                "screen_value": resonance_screen_value,
                "unpacked_offset": 495,
                "source_unpacked_value": 12,
                "rendered_unpacked_value": int(resonance_screen_value),
            }
        ],
        "deferred_rows": deferred_rows,
        "coverage_counts": dict(coverage),
        "hardware_export": {
            "sysex_filename": sysex_name,
            "encoded_parameters": [A4_FILTER2_RESONANCE_PARAMETER],
            "coverage_statement": SYSEX_COVERAGE_STATEMENT,
        },
        "hashes": {
            "audio_sha256": AUDIO_SHA256,
            "source_kit_sha256": SOURCE_KIT_SHA256,
            "genome_sha256": genome_sha256,
            "candidate_dna_sha256": _sha256(_json_bytes(dna)),
            "send_plan_sha256": _sha256(_json_bytes(plan_payload)),
            "sysex_sha256": sysex_sha256,
        },
        "safety": [SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed."],
    }
    sidecar_name = "candidate-01.json"
    sidecar_path = tmp_path / sidecar_name
    sidecar_bytes = _json_bytes(sidecar)
    sidecar_path.write_bytes(sidecar_bytes)
    manifest: dict[str, object] = {
        "schema_version": BATCH_SCHEMA_VERSION,
        "generation_id": generation_id,
        "track": 2,
        "candidate_count": 1,
        "audio_source": {"filename": "reference.wav", "sha256": AUDIO_SHA256},
        "source_kit": {
            "filename": "initialized-kit.syx",
            "sha256": SOURCE_KIT_SHA256,
        },
        "feature_report_hash": feature_report_hash,
        "genome_sha256": genome_sha256,
        "genome": genome_payload,
        "candidates": [
            {
                "column": 1,
                "label": plan.selected_label,
                "filter2_resonance": resonance_screen_value,
                "sysex_filename": sysex_name,
                "sidecar_filename": sidecar_name,
                "sysex_sha256": sysex_sha256,
                "sidecar_sha256": _sha256(sidecar_bytes),
                "coverage_counts": dict(coverage),
            }
        ],
        "coverage_counts": dict(coverage),
        "safety": [SYSEX_COVERAGE_STATEMENT, "No MIDI or network operation was performed."],
    }
    manifest_path = tmp_path / "batch.json"
    manifest_path.write_bytes(_json_bytes(manifest))
    return manifest_path, manifest, sidecar


def _rewrite_json(path: Path, payload: object) -> None:
    path.write_bytes(_json_bytes(payload))


def _manifest_candidate(manifest: dict[str, object]) -> dict[str, object]:
    candidates = manifest["candidates"]
    assert isinstance(candidates, list)
    candidate = candidates[0]
    assert isinstance(candidate, dict)
    return candidate


def _object_field(row: dict[str, object], key: str) -> dict[str, object]:
    value = row[key]
    assert isinstance(value, dict)
    return value


def _rehash_sidecar(
    tmp_path: Path,
    manifest_path: Path,
    manifest: dict[str, object],
    sidecar: dict[str, object],
) -> None:
    hashes = sidecar["hashes"]
    assert isinstance(hashes, dict)
    dna = sidecar["candidate_dna"]
    plan = sidecar["dynamic_send_plan"]
    hashes["candidate_dna_sha256"] = _sha256(_json_bytes(dna))
    hashes["send_plan_sha256"] = _sha256(_json_bytes(plan))
    sidecar_bytes = _json_bytes(sidecar)
    (tmp_path / "candidate-01.json").write_bytes(sidecar_bytes)
    _manifest_candidate(manifest)["sidecar_sha256"] = _sha256(sidecar_bytes)
    _rewrite_json(manifest_path, manifest)


def _send_event_and_gene_value(
    sidecar: dict[str, object],
    *,
    message_kind: str,
) -> tuple[dict[str, object], dict[str, object]]:
    plan = sidecar["dynamic_send_plan"]
    dna = sidecar["candidate_dna"]
    assert isinstance(plan, dict)
    assert isinstance(dna, dict)
    events = plan["send_events"]
    genes = dna["genes"]
    assert isinstance(events, list)
    assert isinstance(genes, list)
    event = next(
        row for row in events if isinstance(row, dict) and row.get("message_kind") == message_kind
    )
    sequence = event["sequence"]
    assert isinstance(sequence, int)
    gene = genes[sequence - 1]
    assert isinstance(gene, dict)
    value = gene["value"]
    assert isinstance(value, dict)
    return event, value


def test_load_batch_candidate_verifies_and_reconstructs_complete_plan(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)

    selection = load_analog_four_patch_batch_candidate(manifest_path, candidate=1)

    assert selection.manifest_path == manifest_path.resolve()
    assert selection.sidecar_path == (tmp_path / "candidate-01.json").resolve()
    assert selection.generation_id == "0123456789abcdef0123456789abcdef"
    assert selection.audio_sha256 == AUDIO_SHA256
    assert selection.manifest_sha256 == _sha256(manifest_path.read_bytes())
    assert selection.sidecar_sha256 == _sha256(selection.sidecar_path.read_bytes())
    assert selection.plan.selected_track == 2
    assert selection.plan.selected_candidate == 1
    assert selection.plan.selected_label == "Closest reference"
    assert len(selection.plan.send_events) == 33
    assert len(selection.plan.manual_events) == 6
    assert selection.plan.summary.transport_message_count == 53


def test_app_dry_run_sends_exact_hash_verified_batch_candidate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import app

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)

    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--batch-manifest",
            str(manifest_path),
            "--candidate",
            "1",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "source: batch-manifest generation 0123456789abcdef0123456789abcdef" in captured.out
    assert "track: 2" in captured.out
    assert "candidate: 1 / Closest reference" in captured.out
    assert "Mock sender captured 53 message(s)." in captured.out
    assert "Analog Four patch batch candidate verified" in captured.err


def _expected_transport_messages(plan: AnalogFourPatchSendPlan) -> list[tuple[int, int, int]]:
    send_events = plan.send_events
    expected: list[tuple[int, int, int]] = []
    for event in send_events:
        if event.message_kind == "cc":
            assert event.cc_msb is not None
            expected.append((event.channel, event.cc_msb, event.midi_value))
            continue
        assert event.nrpn_address is not None
        expected.extend(
            (
                (event.channel, 99, event.nrpn_address[0]),
                (event.channel, 98, event.nrpn_address[1]),
                (event.channel, 6, event.midi_value),
            )
        )
    return expected


def test_app_arm_sends_exact_hash_verified_batch_candidate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    fake_mido_session: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    class FakeOutputPort:
        def __init__(self) -> None:
            self.sent: list[object] = []
            self.closed = False

        def send(self, message: object) -> None:
            self.sent.append(message)

        def close(self) -> None:
            self.closed = True

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)
    selection = load_analog_four_patch_batch_candidate(manifest_path, candidate=1)
    fake_port = FakeOutputPort()
    sleep_calls: list[float] = []
    monkeypatch.setattr(app, "_hardware_settle_sleep", sleep_calls.append)
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake A4 Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(
        [
            "--arm",
            "--a4-patch-send-plan",
            "--batch-manifest",
            str(manifest_path),
            "--candidate",
            "1",
            "--confirm-a4-patch-send-plan",
            "--a4-output-port",
            "Fake A4 Out",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "batch-manifest generation 0123456789abcdef0123456789abcdef" in captured.out
    assert "Analog Four patch batch candidate verified" in captured.err
    assert fake_port.closed is True
    from rytm_randomizer.midi_io import MIDI_MESSAGE_SETTLE_SECONDS

    assert sleep_calls == [MIDI_MESSAGE_SETTLE_SECONDS] * 53
    transport_messages = [
        (message.channel, message.control, message.value) for message in fake_port.sent
    ]
    assert transport_messages == _expected_transport_messages(selection.plan)
    assert (
        hashlib.sha256(
            bytes(value for message in transport_messages for value in message)
        ).hexdigest()
        == EXPECTED_CANDIDATE_1_TRANSPORT_SHA256
    )


def test_app_arm_rejects_tampered_batch_before_opening_midi(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    manifest_path, _manifest, sidecar = _write_batch(tmp_path)
    sidecar["generation_id"] = "tampered"
    _rewrite_json(tmp_path / "candidate-01.json", sidecar)

    def fail_midi_call(self, *_args: object) -> None:
        raise AssertionError("invalid manifest must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(
        [
            "--arm",
            "--a4-patch-send-plan",
            "--batch-manifest",
            str(manifest_path),
            "--confirm-a4-patch-send-plan",
            "--a4-output-port",
            "Fake A4 Out",
        ]
    )

    assert exit_code == 1
    assert "sidecar SHA-256" in capsys.readouterr().err


def test_app_arm_reports_partial_batch_send_and_recovery(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    fake_mido_session: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer import app, mido_provider

    class FailingOutputPort:
        def __init__(self) -> None:
            self.sent: list[object] = []
            self.closed = False

        def send(self, message: object) -> None:
            if len(self.sent) == 5:
                raise OSError("cable disconnected")
            self.sent.append(message)

        def close(self) -> None:
            self.closed = True

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)
    fake_port = FailingOutputPort()
    monkeypatch.setattr(app, "_hardware_settle_sleep", lambda _seconds: None)
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        lambda self: ("Fake A4 Out",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_output",
        lambda self, port_name: fake_port,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    exit_code = app.main(
        [
            "--arm",
            "--a4-patch-send-plan",
            "--batch-manifest",
            str(manifest_path),
            "--confirm-a4-patch-send-plan",
            "--a4-output-port",
            "Fake A4 Out",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert len(fake_port.sent) == 5
    assert fake_port.closed is True
    assert "failed after 5 of 53 messages" in captured.err
    assert "reload the last saved Kit or project before retrying" in captured.err


def test_load_batch_candidate_rejects_sidecar_byte_tampering(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, _manifest, sidecar = _write_batch(tmp_path)
    sidecar["generation_id"] = "tampered"
    _rewrite_json(tmp_path / "candidate-01.json", sidecar)

    with pytest.raises(ValueError, match="sidecar SHA-256"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_load_batch_candidate_rejects_rehashed_internal_plan_tampering(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    plan = sidecar["dynamic_send_plan"]
    assert isinstance(plan, dict)
    events = plan["send_events"]
    assert isinstance(events, list)
    first_event = events[0]
    assert isinstance(first_event, dict)
    first_event["midi_value"] = 1
    sidecar_bytes = _json_bytes(sidecar)
    (tmp_path / "candidate-01.json").write_bytes(sidecar_bytes)
    _manifest_candidate(manifest)["sidecar_sha256"] = _sha256(sidecar_bytes)
    _rewrite_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="send plan SHA-256"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_load_batch_candidate_rejects_manifest_genome_byte_tampering(
    tmp_path: Path,
    isolated_observability: None,
) -> None:
    assert isolated_observability is None
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    manifest_path, manifest, _sidecar = _write_batch(tmp_path)
    _object_field(manifest, "genome")["mode"] = "tampered"
    _rewrite_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="genome SHA-256"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)

    assert get_metrics().a4_patch_batch_read_errors_by_code["artifact_validation"] == 1


def test_load_batch_candidate_rejects_rehashed_genome_candidate_drift(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    genome = _object_field(manifest, "genome")
    candidates = genome["candidates"]
    assert isinstance(candidates, list)
    candidate = candidates[0]
    assert isinstance(candidate, dict)
    candidate["label"] = "Tampered candidate"
    genome_sha256 = _sha256(_json_bytes(genome))
    manifest["genome_sha256"] = genome_sha256
    _object_field(sidecar, "hashes")["genome_sha256"] = genome_sha256
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match="candidate DNA does not match"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_load_batch_candidate_rejects_genome_candidate_count_drift(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, _sidecar = _write_batch(tmp_path)
    genome = _object_field(manifest, "genome")
    candidates = genome["candidates"]
    assert isinstance(candidates, list)
    candidate = candidates[0]
    assert isinstance(candidate, dict)
    candidates.append(dict(candidate))
    manifest["genome_sha256"] = _sha256(_json_bytes(genome))
    _rewrite_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="genome candidate_count"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_load_batch_candidate_rejects_candidate_sysex_byte_tampering(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)
    (tmp_path / "candidate-01.syx").write_bytes(SYSEX_BYTES + b"\x00")

    with pytest.raises(ValueError, match="candidate SysEx SHA-256"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda manifest: manifest.pop("genome"), r"batch manifest\.genome"),
        (lambda manifest: manifest.pop("genome_sha256"), "genome_sha256"),
        (lambda manifest: manifest.pop("source_kit"), r"batch manifest\.source_kit"),
        (
            lambda manifest: _object_field(manifest, "source_kit").pop("filename"),
            "source kit.filename",
        ),
        (
            lambda manifest: _object_field(manifest, "source_kit").pop("sha256"),
            "source kit.sha256",
        ),
        (
            lambda manifest: _manifest_candidate(manifest).pop("sysex_filename"),
            "sysex_filename",
        ),
        (
            lambda manifest: _manifest_candidate(manifest).pop("sysex_sha256"),
            "sysex_sha256",
        ),
    ],
)
def test_load_batch_candidate_rejects_missing_manifest_provenance(
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], object],
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, _sidecar = _write_batch(tmp_path)
    mutate(manifest)
    _rewrite_json(manifest_path, manifest)

    with pytest.raises(ValueError, match=expected):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda sidecar: sidecar.pop("audio_source"), r"candidate sidecar\.audio_source"),
        (lambda sidecar: sidecar.pop("source_kit"), r"candidate sidecar\.source_kit"),
        (
            lambda sidecar: _object_field(sidecar, "source_kit").pop("filename"),
            "candidate source kit.filename",
        ),
        (
            lambda sidecar: _object_field(sidecar, "hashes").pop("source_kit_sha256"),
            "candidate hashes.source_kit_sha256",
        ),
        (
            lambda sidecar: _object_field(sidecar, "hashes").pop("genome_sha256"),
            "candidate hashes.genome_sha256",
        ),
        (
            lambda sidecar: _object_field(sidecar, "hashes").pop("sysex_sha256"),
            "candidate hashes.sysex_sha256",
        ),
        (
            lambda sidecar: sidecar.pop("hardware_export"),
            r"candidate sidecar\.hardware_export",
        ),
    ],
)
def test_load_batch_candidate_rejects_missing_sidecar_provenance(
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], object],
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    mutate(sidecar)
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match=expected):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize(
    ("field", "replacement", "expected"),
    [
        ("filename", "different-kit.syx", "candidate source kit.filename"),
        ("sha256", "c" * 64, "candidate hashes.source_kit_sha256"),
    ],
)
def test_load_batch_candidate_rejects_source_kit_identity_drift(
    tmp_path: Path,
    field: str,
    replacement: str,
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, _sidecar = _write_batch(tmp_path)
    _object_field(manifest, "source_kit")[field] = replacement
    _rewrite_json(manifest_path, manifest)

    with pytest.raises(ValueError, match=expected):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda manifest, _sidecar: manifest.update(candidate_count=2), "candidate_count"),
        (
            lambda manifest, _sidecar: _manifest_candidate(manifest).update(
                sidecar_filename="../candidate-01.json"
            ),
            "plain filename",
        ),
        (
            lambda manifest, _sidecar: _manifest_candidate(manifest).update(
                sysex_filename="../candidate-01.syx"
            ),
            "plain filename",
        ),
        (
            lambda manifest, _sidecar: _manifest_candidate(manifest).update(column=2),
            "exactly one candidate 1",
        ),
    ],
)
def test_load_batch_candidate_rejects_invalid_manifest_contract(
    tmp_path: Path,
    mutate: Callable[[dict[str, object], dict[str, object]], None],
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    mutate(manifest, sidecar)
    _rewrite_json(manifest_path, manifest)

    with pytest.raises(ValueError, match=expected):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_app_batch_manifest_rejects_explicit_track_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import app

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)

    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--batch-manifest",
            str(manifest_path),
            "--track",
            "1",
        ]
    )

    assert exit_code == 1
    assert "track does not match the committed batch manifest" in capsys.readouterr().err


def test_app_batch_manifest_reports_reader_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import app
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

    reset_metrics()
    missing_manifest = tmp_path / "missing-batch.json"

    exit_code = app.main(
        [
            "--dry-run",
            "--a4-patch-send-plan",
            "--batch-manifest",
            str(missing_manifest),
        ]
    )

    assert exit_code == 1
    assert "--a4-patch-send-plan failed:" in capsys.readouterr().err
    assert get_metrics().errors_by_kind["a4_patch_send_plan_manifest_validation"] == 1


def test_reader_rejects_wrong_argument_types(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)
    with pytest.raises(TypeError, match="manifest_path"):
        load_analog_four_patch_batch_candidate(str(manifest_path), candidate=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="candidate"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate="1")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="candidate"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=True)


@pytest.mark.parametrize("candidate", [0, 5])
def test_reader_rejects_out_of_range_candidate(
    tmp_path: Path,
    candidate: int,
    monkeypatch: pytest.MonkeyPatch,
    isolated_observability: None,
) -> None:
    assert isolated_observability is None
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_reader as reader
    from rytm_randomizer.observability.metrics import get_metrics

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)
    logged: list[dict[str, object]] = []
    monkeypatch.setattr(
        reader._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )

    with pytest.raises(ValueError, match="candidate must be in 1..4"):
        reader.load_analog_four_patch_batch_candidate(manifest_path, candidate=candidate)

    metrics = get_metrics()
    assert metrics.a4_patch_batch_read_errors_by_code["validation"] == 1
    assert not metrics.a4_patch_batch_read_errors_by_code["artifact_validation"]
    assert logged[0]["fingerprint"] == "a4.patch_batch.read_failed"
    assert logged[0]["error_code"] == "validation"


def test_reader_rejects_resolved_sidecar_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)
    original_resolve = Path.resolve

    def resolve_with_escape(path: Path, strict: bool = False) -> Path:
        if path.name == "candidate-01.json":
            return tmp_path.parent / path.name
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve_with_escape)

    with pytest.raises(ValueError, match="sidecar escapes the batch directory"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_reader_rejects_resolved_sysex_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, _manifest, _sidecar = _write_batch(tmp_path)
    original_resolve = Path.resolve

    def resolve_with_escape(path: Path, strict: bool = False) -> Path:
        if path.name == "candidate-01.syx":
            return tmp_path.parent / path.name
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve_with_escape)

    with pytest.raises(ValueError, match="SysEx escapes the batch directory"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("total_rows", "total_rows"),
        ("sendable_count", "summary counts"),
        ("cc_event_count", "CC count"),
        ("nrpn_event_count", "NRPN count"),
        ("transport_message_count", "transport message count"),
    ],
)
def test_reader_rejects_rehashed_send_plan_summary_drift(
    tmp_path: Path,
    field: str,
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    plan = sidecar["dynamic_send_plan"]
    assert isinstance(plan, dict)
    summary = plan["summary"]
    assert isinstance(summary, dict)
    value = summary[field]
    assert isinstance(value, int)
    summary[field] = value + 1
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match=expected):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda event: event.update(message_kind="invalid"), "unsupported message_kind"),
        (lambda event: event.update(track=1), "track/channel"),
        (lambda event: event.update(channel=0), "track/channel"),
        (lambda event: event.update(cc_msb=None), "missing a CC MSB"),
        (lambda event: event.update(cc_lsb=50), "verified CC14 transport"),
        (lambda event: event.update(nrpn_address=[1, 2]), "must not include an NRPN address"),
        (lambda event: event.update(sequence=999), "sequences are not ordered"),
    ],
)
def test_reader_rejects_rehashed_invalid_send_events(
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], None],
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    plan = sidecar["dynamic_send_plan"]
    assert isinstance(plan, dict)
    events = plan["send_events"]
    assert isinstance(events, list)
    event = events[0]
    assert isinstance(event, dict)
    mutate(event)
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match=expected):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_reader_rejects_canonical_mapping_that_requires_paired_cc() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        _verify_canonical_transport,
    )
    from rytm_randomizer.data.midi_event_kinds import MIDI_EVENT_KIND_CC

    event = AnalogFourPatchSendEvent(
        sequence=1,
        track=1,
        channel=0,
        parameter="Filter1 Frequency",
        section="FILTERS",
        encoder="A",
        screen_value="64.00",
        midi_value=64,
        message_kind=MIDI_EVENT_KIND_CC,
        cc_msb=18,
        cc_lsb=None,
        nrpn_address=None,
        transport_status="cc-ready",
        dial_direction="set to 64.00",
        rationale="coverage",
        confidence="test",
    )

    with pytest.raises(ValueError, match="requires unverified paired-CC transport"):
        _verify_canonical_transport(event)


def test_reader_rejects_rehashed_nrpn_event_without_address(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    plan = sidecar["dynamic_send_plan"]
    assert isinstance(plan, dict)
    events = plan["send_events"]
    assert isinstance(events, list)
    nrpn_event = next(
        event for event in events if isinstance(event, dict) and event.get("message_kind") == "nrpn"
    )
    nrpn_event["nrpn_address"] = None
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match="missing an NRPN address"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_reader_rejects_rehashed_nrpn_event_with_cc_address(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    event, value = _send_event_and_gene_value(sidecar, message_kind="nrpn")
    event["cc_msb"] = 74
    value["cc_msb"] = 74
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match="must not include a CC address"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_reader_rejects_rehashed_send_transport_status_mismatch(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    event, _value = _send_event_and_gene_value(sidecar, message_kind="nrpn")
    event["transport_status"] = "screen-only"
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match="transport_status does not match message_kind"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize(
    ("message_kind", "address_field", "expected"),
    [
        ("cc", "cc_msb", "CC address does not match"),
        ("nrpn", "nrpn_address", "NRPN address does not match"),
    ],
)
def test_reader_rejects_rehashed_noncanonical_hardware_address(
    tmp_path: Path,
    message_kind: str,
    address_field: str,
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    event, value = _send_event_and_gene_value(sidecar, message_kind=message_kind)
    if address_field == "cc_msb":
        original = event[address_field]
        assert isinstance(original, int)
        replacement: object = (original + 1) % 128
    else:
        original = event[address_field]
        assert isinstance(original, list)
        replacement = [original[0], (original[1] + 1) % 128]
    event[address_field] = replacement
    value[address_field] = replacement
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match=expected):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_reader_rejects_rehashed_dna_send_event_value_drift(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    _event, value = _send_event_and_gene_value(sidecar, message_kind="nrpn")
    midi_value = value["midi_value"]
    assert isinstance(midi_value, int)
    value["midi_value"] = (midi_value + 1) % 128
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match="midi_value does not match"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_reader_rejects_rehashed_dna_gene_count_drift(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    dna = sidecar["candidate_dna"]
    assert isinstance(dna, dict)
    genes = dna["genes"]
    assert isinstance(genes, list)
    genes.pop()
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match="gene count does not match"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize(
    ("sequence_index", "replacement", "expected"),
    [
        (1, 1, "sequences must be unique"),
        (-1, 40, "do not cover candidate DNA order"),
    ],
)
def test_reader_rejects_rehashed_sequence_identity_drift(
    tmp_path: Path,
    sequence_index: int,
    replacement: int,
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    plan = sidecar["dynamic_send_plan"]
    assert isinstance(plan, dict)
    events = plan["send_events"]
    assert isinstance(events, list)
    event = events[sequence_index]
    assert isinstance(event, dict)
    event["sequence"] = replacement
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match=expected):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize("message_kind", ["cc", "nrpn"])
def test_reader_rejects_rehashed_parameter_without_canonical_transport(
    tmp_path: Path,
    message_kind: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    event, value = _send_event_and_gene_value(sidecar, message_kind=message_kind)
    event["parameter"] = "Unknown Parameter"
    value["parameter"] = "Unknown Parameter"
    _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)

    with pytest.raises(ValueError, match=f"no canonical A4 {message_kind.upper()}"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize("coverage_owner", ["manifest", "sidecar"])
@pytest.mark.parametrize("coverage_field", _COVERAGE_FIELDS)
def test_reader_rejects_candidate_coverage_drift(
    tmp_path: Path,
    coverage_owner: str,
    coverage_field: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, sidecar = _write_batch(tmp_path)
    owner = _manifest_candidate(manifest) if coverage_owner == "manifest" else sidecar
    coverage = owner["coverage_counts"]
    assert isinstance(coverage, dict)
    value = coverage[coverage_field]
    assert isinstance(value, int)
    coverage[coverage_field] = value + 1
    if coverage_owner == "sidecar":
        _rehash_sidecar(tmp_path, manifest_path, manifest, sidecar)
    else:
        aggregate = _object_field(manifest, "coverage_counts")
        aggregate[coverage_field] = value + 1
        _rewrite_json(manifest_path, manifest)

    with pytest.raises(ValueError, match=f"{coverage_owner} coverage {coverage_field}"):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


@pytest.mark.parametrize("coverage_field", _COVERAGE_FIELDS)
def test_reader_rejects_manifest_aggregate_coverage_drift(
    tmp_path: Path,
    coverage_field: str,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        load_analog_four_patch_batch_candidate,
    )

    manifest_path, manifest, _sidecar = _write_batch(tmp_path)
    aggregate = _object_field(manifest, "coverage_counts")
    value = aggregate[coverage_field]
    assert isinstance(value, int)
    aggregate[coverage_field] = value + 1
    _rewrite_json(manifest_path, manifest)

    with pytest.raises(
        ValueError,
        match=f"manifest aggregate coverage {coverage_field}",
    ):
        load_analog_four_patch_batch_candidate(manifest_path, candidate=1)


def test_reader_parses_manual_event_and_rejects_wrong_track() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        _parse_manual_event,
    )

    row: dict[str, object] = {
        "sequence": 1,
        "track": 2,
        "parameter": "Manual",
        "section": "TEST",
        "encoder": "A",
        "screen_value": "OFF",
        "transport_status": "screen-only",
        "skip_code": "not-transport-ready",
        "skip_reason": "test",
        "dial_direction": "leave at OFF",
        "rationale": "test",
        "confidence": "test",
    }

    assert _parse_manual_event(row, track=2).parameter == "Manual"
    with pytest.raises(ValueError, match="manual event track"):
        _parse_manual_event(row, track=1)
    row["transport_status"] = "unknown"
    with pytest.raises(ValueError, match="sendable or unknown transport_status"):
        _parse_manual_event(row, track=2)
    row["transport_status"] = "cc-ready"
    row["skip_code"] = "paired-cc-unverified"
    row["skip_reason"] = "wording is descriptive, not a discriminator"
    assert _parse_manual_event(row, track=2).transport_status == "cc-ready"
    row["skip_code"] = "unknown"
    with pytest.raises(ValueError, match="unknown skip_code"):
        _parse_manual_event(row, track=2)
    row["skip_code"] = "paired-cc-unverified"
    row["transport_status"] = "screen-only"
    with pytest.raises(ValueError, match="must use CC-ready"):
        _parse_manual_event(row, track=2)


def test_reader_verifies_manual_only_dna_row() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        _verify_plan_against_candidate_dna,
    )

    manual = AnalogFourPatchManualEvent(
        sequence=1,
        track=2,
        parameter="Manual",
        section="TEST",
        encoder="A",
        screen_value="OFF",
        transport_status="screen-only",
        skip_code="not-transport-ready",
        skip_reason="test",
        dial_direction="leave at OFF",
        rationale="test",
        confidence="test",
    )
    dna = {
        "genes": [
            {
                "track": 2,
                "value": {
                    "parameter": "Manual",
                    "section": "TEST",
                    "encoder": "A",
                    "screen_value": "OFF",
                    "transport_status": "screen-only",
                    "dial_direction": "leave at OFF",
                },
                "rationale": "test",
                "confidence": "test",
            }
        ]
    }

    _verify_plan_against_candidate_dna(
        dna,
        track=2,
        send_events=(),
        manual_events=(manual,),
    )

    paired = replace(
        manual,
        transport_status="cc-ready",
        skip_code="paired-cc-unverified",
    )
    paired_dna = {
        "genes": [
            {
                "track": 2,
                "value": {
                    "parameter": "Manual",
                    "section": "TEST",
                    "encoder": "A",
                    "screen_value": "OFF",
                    "transport_status": "cc-ready",
                    "cc_msb": 10,
                    "cc_lsb": 42,
                    "dial_direction": "leave at OFF",
                },
                "rationale": "test",
                "confidence": "test",
            }
        ]
    }
    _verify_plan_against_candidate_dna(
        paired_dna,
        track=2,
        send_events=(),
        manual_events=(paired,),
    )
    with pytest.raises(ValueError, match="skip_code does not match candidate DNA"):
        _verify_plan_against_candidate_dna(
            paired_dna,
            track=2,
            send_events=(),
            manual_events=(replace(paired, skip_code="not-transport-ready"),),
        )


def test_reader_parses_verified_single_cc_event() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_reader import (
        _parse_send_event,
    )

    row: dict[str, object] = {
        "sequence": 1,
        "track": 2,
        "channel": 1,
        "parameter": "Verified single CC",
        "section": "TEST",
        "encoder": "A",
        "screen_value": "64",
        "midi_value": 64,
        "message_kind": "cc",
        "cc_msb": 74,
        "cc_lsb": None,
        "nrpn_address": None,
        "transport_status": "cc-ready",
        "dial_direction": "set to 64",
        "rationale": "test",
        "confidence": "test",
    }

    event = _parse_send_event(row, track=2)
    assert event.message_kind == "cc"
    assert event.cc_msb == 74


def test_batch_codec_rejects_non_object_json() -> None:
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_codec import (
        decode_analog_four_patch_batch_json,
    )

    with pytest.raises(ValueError, match="must be a JSON object"):
        decode_analog_four_patch_batch_json(b"[]", label="test")


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        (lambda reader: reader._json_object(b"not-json", label="test"), "valid UTF-8 JSON"),
        (lambda reader: reader._as_object([], "test"), "JSON object"),
        (lambda reader: reader._as_object({1: "bad"}, "test"), "JSON object"),
        (lambda reader: reader._object_list({}, "rows", "test"), "JSON array"),
        (lambda reader: reader._string({}, "name", "test"), "non-empty string"),
        (
            lambda reader: reader._expect_equal({}, "value", 1, "test"),
            "does not match",
        ),
        (
            lambda reader: reader._batch_reader_bounded_int(
                {"value": True}, "value", "test", low=0, high=1
            ),
            "integer in",
        ),
        (
            lambda reader: reader._batch_reader_positive_int({"value": 0}, "value", "test"),
            "positive",
        ),
        (
            lambda reader: reader._nonnegative_int({"value": -1}, "value", "test"),
            "nonnegative",
        ),
        (
            lambda reader: reader._optional_nrpn_address({"value": [1]}, "value", "test"),
            "two MIDI bytes",
        ),
        (
            lambda reader: reader._optional_nrpn_address({"value": "not-a-list"}, "value", "test"),
            "two MIDI bytes",
        ),
        (
            lambda reader: reader._optional_nrpn_address({"value": [1, 128]}, "value", "test"),
            "two MIDI bytes",
        ),
        (
            lambda reader: reader._sha256_field({"sha": "BAD"}, "sha", "test"),
            "lowercase SHA-256",
        ),
    ],
)
def test_reader_helper_validation_rejections(
    operation: Callable[[object], object],
    expected: str,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_patch_batch_reader as reader

    with pytest.raises(ValueError, match=expected):
        operation(reader)

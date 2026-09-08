"""Operator diagnostics expose authority decisions without private kit contents."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
)
from rytm_randomizer.cockpit.show_bank.export import ShowPackService
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.observability.metrics import get_metrics

from .conftest import build_show_bank_harness as _harness
from .conftest import generate_show_bank_candidates as _generate

pytestmark = pytest.mark.fast


@pytest.fixture
def package_logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    logger = logging.getLogger("rytm_randomizer")
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.DEBUG, logger=logger.name):
            yield caplog
    finally:
        logger.removeHandler(caplog.handler)


def test_generation_and_hardware_claim_revocation_are_traceable(
    tmp_path: Path, package_logs: pytest.LogCaptureFixture
) -> None:
    harness = _harness(tmp_path)
    candidates = _generate(harness)
    workspace = harness.workspace
    workspace.record_live_rytm_audition(candidates[0].candidate_id)
    assert workspace.revoke_hardware_evidence()

    generated = next(
        record for record in package_logs.records if record.msg == "show_kit_candidates_generated"
    )
    assert generated.__dict__["created_count"] == len(candidates)
    assert generated.__dict__["bank_id"] == harness.bank_id
    assert generated.__dict__["outcome"] == "published"
    assert any(
        record.msg == "show_bank_hardware_evidence_revoked"
        and record.__dict__["source_reload_required"] is True
        for record in package_logs.records
    )
    assert any(
        record.__dict__.get("operation") == "show_kit_forge.generate_candidates"
        and "elapsed_ms" in record.__dict__
        for record in package_logs.records
    )


def test_package_publish_import_and_failure_have_safe_logs_and_attempt_metrics(
    tmp_path: Path, package_logs: pytest.LogCaptureFixture
) -> None:
    harness = _harness(tmp_path)
    workspace = harness.workspace
    for device_id in (RYTM_SHOW_KIT_DEVICE_ID, A4_SHOW_KIT_DEVICE_ID):
        workspace.retain_capture(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            capture_kind="source",
            device_id=device_id,
            current_captures=harness.captures,
        )
    bank = workspace.bank(harness.bank_id)
    service = ShowPackService(tmp_path / "private-pack-path", store=harness.store)
    metrics = get_metrics()
    attempts_before = metrics.export_count
    failures_before = metrics.export_errors_by_code["show_pack_export_failed"]
    duration_before = metrics.export_duration_ms_total
    service.export(bank, package_id="stage-pack")
    with pytest.raises(FileExistsError):
        service.export(bank, package_id="stage-pack")
    imported = ShowPackService(
        service.package_root, store=ShowBankStore(tmp_path / "imported")
    ).import_into_store("stage-pack")

    assert imported.bank.entries[0].show_ready_at is None
    assert metrics.export_count == attempts_before + 2
    assert metrics.export_errors_by_code["show_pack_export_failed"] == failures_before + 1
    assert metrics.export_duration_ms_total > duration_before
    decisions = [
        record
        for record in package_logs.records
        if record.msg
        in {
            "show_bank_revision_persisted",
            "show_bank_published",
            "show_pack_published",
            "show_pack_verified",
            "show_pack_imported",
        }
    ]
    assert {record.msg for record in decisions} == {
        "show_bank_revision_persisted",
        "show_bank_published",
        "show_pack_published",
        "show_pack_verified",
        "show_pack_imported",
    }
    assert {record.__dict__["outcome"] for record in decisions} >= {
        "local_file_only",
        "catalog_only",
        "verified",
    }
    for record in decisions:
        assert "private-pack-path" not in repr(record.__dict__)
        assert "BOUNDARY RYTM" not in repr(record.__dict__)
        assert "No hardware I/O." not in repr(record.__dict__)
        assert not any(isinstance(value, bytes) for value in record.__dict__.values())
    assert any(
        record.__dict__.get("operation") == "show_pack.export"
        and record.__dict__.get("exc_type") == "FileExistsError"
        for record in package_logs.records
    )

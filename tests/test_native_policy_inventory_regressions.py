"""Legacy policy migration cannot fabricate retained-source provenance."""

from __future__ import annotations

from copy import deepcopy
from unittest.mock import Mock

import pytest

from rytm_randomizer.data.persisted_state import classify_payload, require_schema_version
from rytm_randomizer.devices import get_analog_four_native_field_capability
from rytm_randomizer.reports import device_support_inventory as inventory_module

pytestmark = pytest.mark.fast


@pytest.mark.parametrize("version", [None, 1, 2])
@pytest.mark.parametrize("claim", ["source_frame", "source_origin"])
def test_legacy_policy_refuses_provenance_claims_without_modifying_input(
    version: int | None, claim: str
) -> None:
    payload = {
        "record_kind": "capture",
        "rehearsal": None,
        claim: {"sha256": "0" * 64} if claim == "source_frame" else "file_import",
    }
    if version is not None:
        payload["schema_version"] = version
    before = deepcopy(payload)
    decision = classify_payload("library_store", payload)
    assert decision.refused and decision.code == "persisted_state.migration_failed"
    assert decision.payload is None
    assert decision.detail == {
        "reason": "migration_raised",
        "failed_from_version": 2,
        "failed_to_version": 3,
    }
    assert payload == before


def test_partial_native_inventory_keeps_unpromoted_catalog_rows_without_studio_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capability = get_analog_four_native_field_capability()
    metadata = capability.native_fields()
    partial = Mock(wraps=capability)
    partial.native_fields.return_value = tuple(
        field for field in metadata if field.parameter != "filter2_resonance"
    )
    monkeypatch.setattr(
        inventory_module, "get_analog_four_native_field_capability", lambda: partial
    )
    report = inventory_module.build_device_support_inventory()
    row = next(
        row
        for row in report["parameters"]
        if row["device"] == "a4"
        and row["surface"] == "native_saved_sound"
        and row["field"] == "filter2_resonance"
    )
    assert row["offline_mutation"] == "typed_recipe_file_only"
    assert row["domain_authority"] == "codec_storage_range_not_complete_display_domain"
    assert "not_exposed_by_general_cockpit_mutation" in row["blockers"]
    assert row["live_send"] == "blocked"
    assert "filter2_resonance" not in {
        field["parameter"] for field in report["a4_studio_native_fields"]
    }
    assert capability.native_fields() == metadata


@pytest.mark.parametrize("version", [None, 1, 2])
def test_legacy_policy_normalizes_absent_metadata_without_inventing_frame_evidence(
    version: int | None,
) -> None:
    payload = {"record_id": "legacy-original", "payload_hex": "retained-legacy-payload"}
    if version is not None:
        payload["schema_version"] = version
    if version == 2:
        payload.update(record_kind="capture", rehearsal=None)
    before = deepcopy(payload)
    decision = classify_payload("library_store", payload)
    assert decision.accepted and decision.code == "persisted_state.migrated"
    assert decision.payload == {
        **before,
        "schema_version": require_schema_version("library_store"),
        "record_kind": "capture",
        "rehearsal": None,
        "source_frame": None,
        "source_origin": None,
    }
    assert decision.from_version == (version or 1)
    assert payload == before

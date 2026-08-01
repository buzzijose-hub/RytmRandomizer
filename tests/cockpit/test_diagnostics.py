"""Tests for ``rytm_randomizer.cockpit.diagnostics`` — journal + health packet."""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.diagnostics import (
    DEFAULT_JOURNAL_CAPACITY,
    ErrorJournal,
    ErrorJournalEntry,
    build_diagnostics_payload,
    driver_hint,
)
from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# ErrorJournal — bounded, in-instance, wire-safe.
# ---------------------------------------------------------------------------


def test_journal_records_entries_with_injected_clock() -> None:
    ticks = iter([100.0, 200.0])
    journal = ErrorJournal(clock=lambda: next(ticks))
    entry = journal.record("midi.port.open_failed", "port refused", {"port": "X"})
    assert entry == ErrorJournalEntry(
        fingerprint="midi.port.open_failed",
        message="port refused",
        context={"port": "X"},
        ts=100.0,
    )
    second = journal.record("midi.armed_apply.refused", "refused")
    assert second.ts == 200.0
    assert second.context == {}
    assert journal.entries == (entry, second)


def test_journal_default_capacity_is_fifty() -> None:
    journal = ErrorJournal()
    assert journal.capacity == DEFAULT_JOURNAL_CAPACITY == 50


def test_journal_is_bounded_drop_oldest() -> None:
    journal = ErrorJournal(capacity=3, clock=lambda: 1.0)
    for index in range(5):
        journal.record(f"fp.{index}", f"m{index}")
    fingerprints = [entry.fingerprint for entry in journal.entries]
    assert fingerprints == ["fp.2", "fp.3", "fp.4"]
    assert journal.capacity == 3


def test_journal_coerces_context_keys_and_values_to_str() -> None:
    journal = ErrorJournal(clock=lambda: 1.0)
    entry = journal.record("fp", "m", {1: 2})  # type: ignore[dict-item]
    assert dict(entry.context) == {"1": "2"}


def test_journal_entry_context_is_frozen() -> None:
    entry = ErrorJournalEntry(fingerprint="fp", message="m", context={"a": "b"}, ts=1.0)
    with pytest.raises(TypeError):
        entry.context["a"] = "c"  # type: ignore[index]


def test_journal_to_dicts_round_trips() -> None:
    journal = ErrorJournal(clock=lambda: 5.0)
    journal.record("fp", "m", {"k": "v"})
    assert journal.to_dicts() == [
        {"fingerprint": "fp", "message": "m", "context": {"k": "v"}, "ts": 5.0}
    ]


# ---------------------------------------------------------------------------
# driver_hint — per-OS hint strings.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("platform", "needle"),
    [
        ("darwin", "CoreMIDI"),
        ("win32", "Windows"),
        ("linux", "ALSA"),
        ("linux2", "ALSA"),
    ],
)
def test_driver_hint_per_platform(platform: str, needle: str) -> None:
    assert needle in driver_hint(platform)


def test_driver_hint_unknown_platform_falls_back() -> None:
    assert "Unknown platform" in driver_hint("plan9")


def test_driver_hint_defaults_to_current_platform() -> None:
    assert isinstance(driver_hint(), str)
    assert driver_hint()  # non-empty


# ---------------------------------------------------------------------------
# build_diagnostics_payload — the read-only diagnostics packet.
# ---------------------------------------------------------------------------


def test_payload_with_journal_and_connection_state() -> None:
    reset_metrics()
    get_metrics().record_error("midi.port.open_failed")
    journal = ErrorJournal(clock=lambda: 9.0)
    journal.record("fp", "m")
    connection = {
        "phase": "listening",
        "available_inputs": ["In A"],
        "available_outputs": ["Out A", "Out B"],
        "selected_input": "In A",
        "selected_output": "Out A",
        "last_error_fingerprint": None,
        "changed_at": 1.0,
    }
    payload = build_diagnostics_payload(
        journal=journal, connection_state=connection, platform="darwin"
    )
    assert payload["journal"] == journal.to_dicts()
    assert payload["errors_by_kind"] == {"midi.port.open_failed": 1}
    assert payload["connection"] == connection
    assert payload["available_inputs"] == ["In A"]
    assert payload["available_outputs"] == ["Out A", "Out B"]
    assert payload["platform"] == "darwin"
    assert "CoreMIDI" in payload["driver_hint"]
    reset_metrics()


def test_payload_without_journal_or_connection() -> None:
    reset_metrics()
    payload = build_diagnostics_payload(journal=None, connection_state=None, platform="win32")
    assert payload["journal"] == []
    assert payload["connection"] is None
    assert payload["available_inputs"] == []
    assert payload["available_outputs"] == []
    assert payload["errors_by_kind"] == {}


def test_payload_tolerates_non_list_port_fields() -> None:
    payload = build_diagnostics_payload(
        journal=None,
        connection_state={"available_inputs": "junk", "available_outputs": 7},
        platform="linux",
    )
    assert payload["available_inputs"] == []
    assert payload["available_outputs"] == []


def test_payload_defaults_platform_to_sys_platform() -> None:
    import sys

    payload = build_diagnostics_payload(journal=None, connection_state=None)
    assert payload["platform"] == sys.platform

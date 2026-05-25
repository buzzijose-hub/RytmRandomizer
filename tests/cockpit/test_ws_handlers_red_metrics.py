"""OBS O2 wiring tests — handle_command must record RED metrics on every path.

The metric record sites in ``cockpit/ws/handlers.handle_command`` are
the contract: every command invocation (success, handler exception,
unknown command, malformed envelope) must produce exactly one
``record_ws_command`` call on the singleton with the right label and
optional ``error_code``.

This test file lives next to the other dispatcher tests so contributors
who touch the dispatcher see the metric expectations alongside the
behavioural ones — silent removal of the recording would break both.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from rytm_randomizer.cockpit.data import (
    PadState,
    ProfileModel,
    Snapshot,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

pytestmark = pytest.mark.fast


@pytest.fixture(autouse=True)
def _reset_metrics_singleton() -> Iterator[None]:
    """Singleton state must not leak between tests."""

    reset_metrics()
    try:
        yield
    finally:
        reset_metrics()


_FIXED_TS = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)


def _snapshot() -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000B",
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(
            PadState(pad_id=1, machine="BD Hard", params={"tun": 30, "dec": 80, "lev": 110}),
            PadState(pad_id=2, machine="SD Acoustic", params={"tun": 40, "dec": 60, "lev": 100}),
        ),
        scene_slot="A01",
        bpm=124.0,
    )


def _profile() -> ProfileModel:
    return ProfileModel(
        profile_id="obs-o2",
        name="OBS O2",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="punchy", value=0.7),),
        pad_mappings=(TraitPadWeight(trait="punchy", pad_id=1, weight=1.0),),
        transition_curve="progressive",
        source_summary="obs o2 wiring test",
    )


def _make_session(tmp_path: Path) -> CockpitSession:
    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    registry.save(_profile())
    return CockpitSession(profile_registry=registry, history_store=history, device=device)


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_successful_command_records_ws_command_no_error(tmp_path: Path) -> None:
    """A successful select_profile bumps count + duration; no error_code."""

    session = _make_session(tmp_path)
    envelope = {
        "request_id": "r1",
        "command": {"type": "select_profile", "profile_id": "obs-o2"},
    }

    ack = _run(handle_command(envelope, session))

    assert ack["ok"] is True
    metrics = get_metrics()
    assert metrics.ws_command_count["select_profile"] == 1
    assert metrics.ws_command_duration_ms_total["select_profile"] >= 0
    assert len(metrics.ws_command_errors_by_code) == 0


def test_unknown_command_records_ws_command_with_unknown_code(tmp_path: Path) -> None:
    """An unknown command bumps count under the command label + ERR_UNKNOWN_COMMAND."""

    session = _make_session(tmp_path)
    envelope = {
        "request_id": "r2",
        "command": {"type": "definitely_not_a_real_command"},
    }

    ack = _run(handle_command(envelope, session))

    assert ack["ok"] is False
    metrics = get_metrics()
    assert metrics.ws_command_count["definitely_not_a_real_command"] == 1
    # The categorical wire code surfaces in the errors_by_code histogram.
    assert metrics.ws_command_errors_by_code["unknown_command"] == 1


def test_malformed_envelope_records_under_malformed_bucket(tmp_path: Path) -> None:
    """An envelope without a ``command`` key records under the ``<malformed>`` bucket.

    The cmd_type label is unknown at this point in the dispatcher (the
    envelope parse failed); the special label prevents an unbounded
    counter explosion and lets operators spot wire-protocol breakage at
    a glance.
    """

    session = _make_session(tmp_path)
    envelope: dict[str, Any] = {"request_id": "r3"}  # missing "command"

    ack = _run(handle_command(envelope, session))

    assert ack["ok"] is False
    metrics = get_metrics()
    assert metrics.ws_command_count["<malformed>"] == 1
    assert metrics.ws_command_errors_by_code["missing_envelope_key"] == 1


def test_handler_exception_records_with_validation_or_internal_code(
    tmp_path: Path,
) -> None:
    """An invalid profile_id triggers KeyError → ERR_VALIDATION bucket."""

    session = _make_session(tmp_path)
    envelope = {
        "request_id": "r4",
        "command": {"type": "select_profile", "profile_id": "no-such-profile"},
    }

    ack = _run(handle_command(envelope, session))

    assert ack["ok"] is False
    metrics = get_metrics()
    assert metrics.ws_command_count["select_profile"] == 1
    # The classifier maps KeyError → validation per the dispatcher's
    # ``_classify_handler_exception`` (PR 14). The exact code lives in
    # the categorical code set, not the message.
    assert sum(metrics.ws_command_errors_by_code.values()) == 1


def test_dispatch_durations_accumulate_across_calls(tmp_path: Path) -> None:
    """Three successful calls produce a count of 3 and a non-decreasing duration."""

    session = _make_session(tmp_path)

    for i in range(3):
        envelope = {
            "request_id": f"r-{i}",
            "command": {"type": "select_profile", "profile_id": "obs-o2"},
        }
        _run(handle_command(envelope, session))

    metrics = get_metrics()
    assert metrics.ws_command_count["select_profile"] == 3
    # Wall-clock duration is non-deterministic but must be non-negative.
    assert metrics.ws_command_duration_ms_total["select_profile"] >= 0

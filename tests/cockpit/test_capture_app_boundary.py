"""Armed app composition tests for the desktop current-kit capture sidecar."""

from __future__ import annotations

from pathlib import Path

import pytest

from rytm_randomizer import app, mido_provider
from rytm_randomizer.cockpit import __main__ as cockpit_main
from rytm_randomizer.cockpit import device as device_boundary
from rytm_randomizer.cockpit.capture import KitCaptureService
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.senders.armed_apply import ArmedApplySession

pytestmark = pytest.mark.fast


class _InputOnlyProvider:
    def list_input_names(self) -> tuple[str, ...]:
        return ("Elektron Input",)

    def capture_sysex_messages(
        self,
        _port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]:
        assert timeout_seconds > 0
        return ()


def test_capture_sidecar_requires_explicit_app_arm(capsys: pytest.CaptureFixture[str]) -> None:
    assert app.main(["--cockpit-kit-capture-sidecar"]) == 1

    captured = capsys.readouterr()
    assert "--cockpit-kit-capture-sidecar requires --arm" in captured.err


def test_armed_capture_sidecar_dispatches_through_app_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        app,
        "_run_cockpit_kit_capture_sidecar",
        lambda: calls.append("capture-sidecar") or 0,
    )

    assert app.main(["--arm", "--cockpit-kit-capture-sidecar"]) == 0
    assert calls == ["capture-sidecar"]


def test_capture_sidecar_composes_injected_input_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _InputOnlyProvider()
    captured: list[KitCaptureService] = []
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: provider,
    )
    monkeypatch.setattr(cockpit_main, "run", captured.append)

    assert app._run_cockpit_kit_capture_sidecar() == 0

    assert len(captured) == 1
    assert captured[0].enabled is True
    assert captured[0].list_input_names() == ("Elektron Input",)


def test_passive_cockpit_session_keeps_capture_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)

    session = cockpit_main.build_session()

    assert session.kit_capture_service.enabled is False
    assert session.kit_capture_service.list_input_names() == ()


def test_cockpit_session_preserves_injected_capture_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    service = KitCaptureService.disabled()

    session = cockpit_main.build_session(service)

    assert session.kit_capture_service is service


def test_cockpit_session_preserves_injected_device_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    device = MockDeviceAdapter(cockpit_main._default_initial_snapshot())

    session = cockpit_main.build_session(device=device)

    assert session.device is device


def test_armed_apply_remains_the_only_real_output_seam() -> None:
    """The cockpit device boundary exposes state projection, never a second port."""

    assert set(device_boundary.__all__) == {"DeviceAdapter", "MockDeviceAdapter"}
    assert not hasattr(device_boundary, "RealMidiDeviceAdapter")
    assert ArmedApplySession.__module__ == "rytm_randomizer.senders.armed_apply"

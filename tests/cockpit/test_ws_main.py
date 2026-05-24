"""Tests for ``rytm_randomizer.cockpit.__main__`` — the uvicorn entrypoint.

The module wires the default collaborators (mock device, on-disk
profiles, fresh history) and starts uvicorn. We don't actually want
to bind a real port in a unit test — every test monkeypatches
:func:`uvicorn.run` to a recorder that captures the host/port/app
arguments. Coverage targets every branch of ``__main__.py`` except the
``if __name__ == "__main__"`` guard (intentionally excluded via
``pragma: no cover``).

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/__main__.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from rytm_randomizer.cockpit import __main__ as cockpit_main
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# build_session — sanity check the wiring.
# ---------------------------------------------------------------------------


def test_build_session_returns_session_with_initialised_history(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """The default session must seed history with a captured snapshot."""

    # Pin the profiles dir under tmp_path so we don't pollute the user's XDG.
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)

    session = cockpit_main.build_session()

    assert isinstance(session, CockpitSession)
    # initial() was called, so history has exactly one entry.
    assert len(session.history_store.current.entries) == 1
    # MockDeviceAdapter (mock-safe default)
    assert session.device.is_armed is False
    # 4 pads as the v10 UX expects
    snapshot = session.device.capture_snapshot()
    assert len(snapshot.pads) == 4
    assert snapshot.bpm == cockpit_main._DEFAULT_BPM


def test_default_initial_snapshot_has_four_pads_with_known_machines() -> None:
    """The helper builds the BD/SD/SY/FX layout the v10 mockup pictures."""

    snapshot = cockpit_main._default_initial_snapshot()

    pads_by_id = {p.pad_id: p for p in snapshot.pads}
    assert set(pads_by_id) == {1, 2, 3, 4}
    assert pads_by_id[1].machine == "BD Hard"
    assert pads_by_id[2].machine == "SD Acoustic"
    assert pads_by_id[3].machine == "SY Raw"
    assert pads_by_id[4].machine == "FX Metal"
    # All pads share the same starter param set
    for pad in snapshot.pads:
        assert set(pad.params) == {"tun", "dec", "lev", "flt"}


def test_default_initial_snapshot_carries_default_device_identifier() -> None:
    snapshot = cockpit_main._default_initial_snapshot()
    assert snapshot.device == cockpit_main._DEFAULT_DEVICE


# ---------------------------------------------------------------------------
# _resolve_port — env var override + default.
# ---------------------------------------------------------------------------


def test_resolve_port_returns_default_when_env_var_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(cockpit_main._PORT_ENV_VAR, raising=False)

    assert cockpit_main._resolve_port() == cockpit_main._DEFAULT_PORT


def test_resolve_port_returns_env_var_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(cockpit_main._PORT_ENV_VAR, "9999")

    assert cockpit_main._resolve_port() == 9999


def test_resolve_port_rejects_non_integer_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-integer values surface as :class:`ValueError` from ``int(...)``."""

    monkeypatch.setenv(cockpit_main._PORT_ENV_VAR, "not-a-number")

    with pytest.raises(ValueError):
        cockpit_main._resolve_port()


# ---------------------------------------------------------------------------
# main() — wires session, app, uvicorn.run with the resolved port.
# ---------------------------------------------------------------------------


def test_main_invokes_uvicorn_run_with_loopback_and_default_port(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """``main()`` must hand ``uvicorn.run`` the loopback host + resolved port."""

    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    monkeypatch.delenv(cockpit_main._PORT_ENV_VAR, raising=False)

    captured: dict[str, Any] = {}

    def _fake_run(app: Any, *, host: str, port: int) -> None:
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setattr(cockpit_main, "uvicorn", type("U", (), {"run": staticmethod(_fake_run)}))

    cockpit_main.main()

    assert captured["host"] == cockpit_main._DEFAULT_HOST
    assert captured["host"] == "127.0.0.1"  # loopback contract
    assert captured["port"] == cockpit_main._DEFAULT_PORT
    # The app object must come from create_app (a FastAPI instance with a /ws route)
    routes = {getattr(r, "path", None) for r in captured["app"].routes}
    assert "/ws" in routes


def test_main_honours_env_var_port_override(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    monkeypatch.setenv(cockpit_main._PORT_ENV_VAR, "4242")

    captured: dict[str, Any] = {}

    def _fake_run(app: Any, *, host: str, port: int) -> None:
        captured["port"] = port

    monkeypatch.setattr(cockpit_main, "uvicorn", type("U", (), {"run": staticmethod(_fake_run)}))

    cockpit_main.main()

    assert captured["port"] == 4242

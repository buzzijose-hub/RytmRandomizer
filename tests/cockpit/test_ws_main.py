"""Tests for ``rytm_randomizer.cockpit.__main__`` — the uvicorn entrypoint.

The module wires the default collaborators (mock device, on-disk
profiles, fresh history), mints the per-launch handshake token, and
starts uvicorn. We don't actually want to bind a real port in a unit
test — every test monkeypatches :func:`uvicorn.run` to a recorder that
captures the host/port/app arguments. The token-provisioning side
effect is redirected to ``tmp_path`` via the
:data:`RYTM_RAND_WS_TOKEN_FILE` env var so a test run never writes into
the developer's ``$HOME``. Coverage targets every branch of
``__main__.py`` except the ``if __name__ == "__main__"`` guard
(intentionally excluded via ``pragma: no cover``).

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/__main__.py``.
"""

from __future__ import annotations

import stat
import sys
from pathlib import Path
from typing import Any

import pytest

from rytm_randomizer.cockpit import __main__ as cockpit_main
from rytm_randomizer.cockpit.device.connection import (
    ConnectionManager,
    ConnectionState,
    NullPortEnumerator,
    ProviderPortEnumerator,
    active_connection_manager,
    set_active_connection_manager,
)
from rytm_randomizer.cockpit.ws.server import ConnectionRegistry
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast


@pytest.fixture(autouse=True)
def _reset_active_connection_manager() -> Any:
    """``main()`` registers a process-level ConnectionManager; never leak it.

    Without this reset, a ``main()`` invocation in one test would leave
    the registered manager visible to every later test in the same
    worker (the handlers' ``session_status`` phase would silently switch
    from the device-derived fallback to the leaked manager's state).
    """

    yield
    set_active_connection_manager(None)


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
    # 12 pads as the dry-run Cockpit expects
    snapshot = session.device.capture_snapshot()
    assert len(snapshot.pads) == 12
    assert snapshot.bpm == cockpit_main._DEFAULT_BPM


def test_default_initial_snapshot_has_twelve_rytm_pads_with_known_machines() -> None:
    """The helper builds the 12-pad Analog Rytm layout the Cockpit pictures."""

    snapshot = cockpit_main._default_initial_snapshot()

    pads_by_id = {p.pad_id: p for p in snapshot.pads}
    assert set(pads_by_id) == set(range(1, 13))
    assert [pad.machine for pad in snapshot.pads] == [
        "BD Hard",
        "SD Classic",
        "CH Closed",
        "OH Open",
        "BT Rim",
        "LT Low",
        "MT Mid",
        "HT High",
        "CP Clap",
        "RS Riser",
        "SY Raw",
        "BD Acoustic",
    ]
    # All pads share the operator-facing starter control surface used by the cockpit.
    for pad in snapshot.pads:
        assert {
            "tun",
            "dec",
            "lev",
            "flt",
            "swt",
            "snap",
            "hold",
            "wave",
            "tick",
            "sample_tune",
            "sample_fine",
            "sample_bit",
            "sample_start",
            "sample_end",
            "filter_attack",
            "filter_decay",
            "filter_sustain",
            "filter_release",
            "filter_resonance",
            "filter_env",
            "amp_attack",
            "amp_hold",
            "amp_decay",
            "overdrive",
            "delay",
            "reverb",
            "lfo_speed",
            "lfo_depth",
        }.issubset(pad.params)


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


def _redirect_token_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect the token file path under ``tmp_path`` for the duration of one test.

    Without this redirect ``main()`` (or ``_provision_token()``) would
    write to ``~/.rytm-randomizer/cockpit-ws-token`` on the developer's
    machine and clobber a real running cockpit's token. Sets the
    canonical env var so the production code path is exercised.
    """

    token_path = tmp_path / "ws-token"
    monkeypatch.setenv(cockpit_main._TOKEN_FILE_ENV_VAR, str(token_path))
    return token_path


def test_main_invokes_uvicorn_run_with_loopback_and_default_port(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``main()`` must hand ``uvicorn.run`` the loopback host + resolved port."""

    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    monkeypatch.delenv(cockpit_main._PORT_ENV_VAR, raising=False)
    _redirect_token_file(monkeypatch, tmp_path)

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


def test_main_honours_env_var_port_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    monkeypatch.setenv(cockpit_main._PORT_ENV_VAR, "4242")
    _redirect_token_file(monkeypatch, tmp_path)

    captured: dict[str, Any] = {}

    def _fake_run(app: Any, *, host: str, port: int) -> None:
        captured["port"] = port

    monkeypatch.setattr(cockpit_main, "uvicorn", type("U", (), {"run": staticmethod(_fake_run)}))

    cockpit_main.main()

    assert captured["port"] == 4242


# ---------------------------------------------------------------------------
# Token provisioning — file shape, env-var override, dev-mode stdout echo.
# ---------------------------------------------------------------------------


def test_resolve_token_path_honours_env_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "custom-token"
    monkeypatch.setenv(cockpit_main._TOKEN_FILE_ENV_VAR, str(target))

    resolved = cockpit_main._resolve_token_path()

    assert resolved == target.absolute()


def test_resolve_token_path_defaults_under_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without the env var the token file lives under ``$HOME``."""

    monkeypatch.delenv(cockpit_main._TOKEN_FILE_ENV_VAR, raising=False)

    resolved = cockpit_main._resolve_token_path()

    assert resolved.name == cockpit_main._DEFAULT_TOKEN_FILE_NAME
    assert cockpit_main._DEFAULT_TOKEN_REL_DIR.name in resolved.parts


def test_provision_token_writes_token_file_with_restrictive_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The minted token lands on disk verbatim; mode is ``0600`` on POSIX."""

    token_path = _redirect_token_file(monkeypatch, tmp_path)

    token = cockpit_main._provision_token()

    assert token_path.read_text(encoding="utf-8") == token
    if sys.platform != "win32":
        mode = stat.S_IMODE(token_path.stat().st_mode)
        assert mode == 0o600


def test_provision_token_returns_a_fresh_token_per_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Every launch mints a brand-new token (stale tokens never survive)."""

    _redirect_token_file(monkeypatch, tmp_path)

    first = cockpit_main._provision_token()
    second = cockpit_main._provision_token()

    assert first != second
    # The latest token overwrites the prior one.
    assert (tmp_path / "ws-token").read_text(encoding="utf-8") == second


def test_provision_token_prints_to_stdout_when_env_var_unset(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dev-mode (no env var) echoes the token on stdout for interactive copy."""

    monkeypatch.delenv(cockpit_main._TOKEN_FILE_ENV_VAR, raising=False)
    # Point the default Home at tmp_path so the dev-mode write stays sandboxed.
    monkeypatch.setattr(cockpit_main.Path, "home", classmethod(lambda cls: tmp_path))

    token = cockpit_main._provision_token()

    captured = capsys.readouterr()
    assert "[cockpit] WS token:" in captured.out
    assert token in captured.out


def test_provision_token_silent_when_env_var_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Production path (env var set) does NOT echo the token on stdout."""

    _redirect_token_file(monkeypatch, tmp_path)

    cockpit_main._provision_token()

    captured = capsys.readouterr()
    assert captured.out == ""


def test_write_token_file_creates_parent_directories(tmp_path: Path) -> None:
    """``_write_token_file`` mkdirs parents on demand for a fresh checkout."""

    nested = tmp_path / "a" / "b" / "c" / "cockpit-ws-token"

    cockpit_main._write_token_file(nested, "abc")

    assert nested.read_text(encoding="utf-8") == "abc"


def test_write_token_file_tolerates_chmod_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A filesystem that rejects ``chmod`` must not abort the launch.

    Windows / exotic mounts can refuse the bit-precise ``0o600``; the
    token still lands on disk (a partially-restricted file beats a
    cockpit that refuses to boot).
    """

    target = tmp_path / "token"

    def _refuse_chmod(self: Path, mode: int) -> None:
        raise OSError("chmod not supported on this filesystem")

    monkeypatch.setattr(cockpit_main.Path, "chmod", _refuse_chmod)

    cockpit_main._write_token_file(target, "tok")

    assert target.read_text(encoding="utf-8") == "tok"


# ---------------------------------------------------------------------------
# Wave 3: passive ConnectionManager wiring (enumerator pick, broadcast
# adapter, lifecycle handlers, main() registration).
# ---------------------------------------------------------------------------


def test_build_port_enumerator_wraps_real_provider_when_mido_present() -> None:
    """The dev venv ships ``mido``: the enumeration-only facade is picked.

    Constructing the facade must NOT import ``mido`` (the provider's
    methods import lazily) and must never open a port — building it is
    pure object wiring.
    """

    import sys

    had_mido = "mido" in sys.modules
    enumerator = cockpit_main._build_port_enumerator()

    assert isinstance(enumerator, ProviderPortEnumerator)
    if not had_mido:
        # Building the facade must not have pulled ``mido`` in.
        assert "mido" not in sys.modules


def test_build_port_enumerator_falls_back_to_null_without_mido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hosts without the hardware extra still boot (null enumerator)."""

    monkeypatch.setattr(cockpit_main.importlib.util, "find_spec", lambda name: None)

    enumerator = cockpit_main._build_port_enumerator()

    assert isinstance(enumerator, NullPortEnumerator)
    assert enumerator.list_input_names() == ()


def test_connection_event_broadcaster_pushes_connection_changed() -> None:
    """The on_change adapter fans one ``connection_changed`` per diff."""

    class _RecordingRegistry:
        def __init__(self) -> None:
            self.events: list[dict] = []

        def broadcast_event(self, event: dict) -> int:
            self.events.append(event)
            return 0

    registry = _RecordingRegistry()
    broadcast = cockpit_main._connection_event_broadcaster(registry)
    state = ConnectionState(
        phase="searching",
        available_inputs=(),
        available_outputs=(),
        selected_input=None,
        selected_output=None,
        last_error_fingerprint=None,
        changed_at=7.0,
    )

    broadcast(state)

    assert len(registry.events) == 1
    event = registry.events[0]
    assert event["type"] == "connection_changed"
    assert event["connection"]["phase"] == "searching"
    assert event["connection"]["changed_at"] == 7.0


def test_install_connection_manager_lifecycle_registers_startup_and_shutdown() -> None:
    from fastapi import FastAPI

    app = FastAPI()
    manager = ConnectionManager(NullPortEnumerator())

    cockpit_main._install_connection_manager_lifecycle(app, manager)

    assert manager.start in app.router.on_startup
    assert manager.stop in app.router.on_shutdown


def test_main_registers_connection_manager_and_registry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``main()`` wires the launch brain without starting its poll loop.

    The poll loop only starts on the app's ``startup`` event (uvicorn is
    monkeypatched away here), so no enumeration happens during the test
    — passive even at wiring time.
    """

    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    monkeypatch.delenv(cockpit_main._PORT_ENV_VAR, raising=False)
    _redirect_token_file(monkeypatch, tmp_path)

    captured: dict[str, Any] = {}

    def _fake_run(app: Any, *, host: str, port: int) -> None:
        captured["app"] = app

    monkeypatch.setattr(cockpit_main, "uvicorn", type("U", (), {"run": staticmethod(_fake_run)}))

    cockpit_main.main()

    manager = active_connection_manager()
    assert manager is not None
    # The manager never polls (and never arms) before uvicorn starts it.
    assert manager.state.phase == "disconnected"
    # The app exposes the same registry the manager broadcasts through.
    app = captured["app"]
    assert isinstance(app.state.connection_registry, ConnectionRegistry)
    # Startup/shutdown lifecycle handlers are installed.
    assert manager.start in app.router.on_startup
    assert manager.stop in app.router.on_shutdown

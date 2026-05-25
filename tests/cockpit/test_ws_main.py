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

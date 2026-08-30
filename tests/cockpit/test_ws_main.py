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
    DEFAULT_FAKE_PORT_NAMES,
    ConnectionManager,
    ConnectionState,
    FakePortEnumerator,
    NullPortEnumerator,
    ProviderPortEnumerator,
    active_connection_manager,
    is_elektron_port_name,
)
from rytm_randomizer.cockpit.ws.server import ConnectionRegistry
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
    """Redirect BOTH per-launch secret files under ``tmp_path`` for one test.

    Without this redirect ``main()`` (or ``_provision_token()`` /
    ``_provision_arm_secret()``) would write to
    ``~/.rytm-randomizer/`` on the developer's machine and clobber a real
    running cockpit's credentials. Sets the canonical env vars so the
    production code paths are exercised.

    Returns the WS handshake-token path (the one most tests assert on);
    the ARM secret lands next to it as ``arm-secret``.
    """

    token_path = tmp_path / "ws-token"
    monkeypatch.setenv(cockpit_main._TOKEN_FILE_ENV_VAR, str(token_path))
    monkeypatch.setenv(cockpit_main._ARM_SECRET_FILE_ENV_VAR, str(tmp_path / "arm-secret"))
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


def test_run_preserves_injected_capture_and_device_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The explicit sidecar path forwards both injected authorities."""

    from rytm_randomizer.cockpit.capture import KitCaptureService
    from rytm_randomizer.cockpit.device import MockDeviceAdapter

    service = KitCaptureService.disabled()
    device = MockDeviceAdapter(cockpit_main._default_initial_snapshot())
    received: list[tuple[KitCaptureService | None, object | None]] = []
    real_build_session = cockpit_main.build_session

    def _capture_build_session(
        capture_service: KitCaptureService | None = None,
        *,
        device: object | None = None,
    ) -> CockpitSession:
        received.append((capture_service, device))
        return real_build_session(capture_service, device=device)

    monkeypatch.setattr(cockpit_main, "build_session", _capture_build_session)
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path / "profiles")
    monkeypatch.setattr(cockpit_main, "default_library_dir", lambda: tmp_path / "library")
    monkeypatch.setattr(cockpit_main, "default_captures_dir", lambda: tmp_path / "captures")
    monkeypatch.setattr(cockpit_main, "_build_input_opener", lambda: None)
    monkeypatch.setattr(
        cockpit_main,
        "uvicorn",
        type("U", (), {"run": staticmethod(lambda _app, *, host, port: None)}),
    )
    _redirect_token_file(monkeypatch, tmp_path)

    cockpit_main.run(service, device=device)

    assert received == [(service, device)]


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


# ---------------------------------------------------------------------------
# The ARM secret — a SECOND, separate per-launch credential.
#
# The handshake token admits a connection; the ARM secret authorises the
# transmit capability. The arm handler used to accept any non-empty
# client-supplied string and then derive the "expected" value from that
# same string, so ``compare_digest`` compared a value with itself. These
# tests pin the server side of the replacement.
# ---------------------------------------------------------------------------


def test_arm_secret_is_written_to_its_own_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A separate file from the WS token, so one can be handed out without the other."""

    token_path = _redirect_token_file(monkeypatch, tmp_path)

    secret = cockpit_main._provision_arm_secret()

    secret_path = tmp_path / "arm-secret"
    assert secret_path.read_text(encoding="utf-8") == secret
    assert secret_path != token_path


def test_arm_secret_is_written_with_restrictive_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """0600 on POSIX — only a process running as the operator can read it."""

    _redirect_token_file(monkeypatch, tmp_path)

    cockpit_main._provision_arm_secret()

    if sys.platform != "win32":
        assert stat.S_IMODE((tmp_path / "arm-secret").stat().st_mode) == 0o600


def test_arm_secret_is_freshly_minted_per_launch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An arm capability must not survive a restart the operator did not authorise."""

    _redirect_token_file(monkeypatch, tmp_path)

    first = cockpit_main._provision_arm_secret()
    second = cockpit_main._provision_arm_secret()

    assert first != second
    assert (tmp_path / "arm-secret").read_text(encoding="utf-8") == second


def test_arm_secret_differs_from_the_handshake_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Two independent credentials, not one value written twice."""

    _redirect_token_file(monkeypatch, tmp_path)

    assert cockpit_main._provision_token() != cockpit_main._provision_arm_secret()


def test_arm_secret_is_echoed_only_in_dev_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Dev-mode prints it for interactive copy; the production path stays silent."""

    monkeypatch.delenv(cockpit_main._ARM_SECRET_FILE_ENV_VAR, raising=False)
    monkeypatch.setattr(cockpit_main.Path, "home", classmethod(lambda cls: tmp_path))
    secret = cockpit_main._provision_arm_secret()
    dev_out = capsys.readouterr().out
    # The dev banner names the FILE, never the value: this secret authorises
    # transmit to hardware, so echoing it would strand a live-fire capability
    # in scrollback / shell history / CI logs. (CodeQL
    # py/clear-text-logging-sensitive-data flagged the old behaviour.)
    assert "[cockpit] ARM secret written to:" in dev_out
    assert secret not in dev_out

    monkeypatch.setenv(cockpit_main._ARM_SECRET_FILE_ENV_VAR, str(tmp_path / "arm-secret"))
    cockpit_main._provision_arm_secret()
    assert capsys.readouterr().out == ""


def test_main_installs_the_arm_secret_on_the_session(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Without this wiring the arm handler fails closed and nobody can arm."""

    _redirect_token_file(monkeypatch, tmp_path)
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path / "profiles")
    monkeypatch.setattr(cockpit_main, "default_library_dir", lambda: tmp_path / "library")
    monkeypatch.setattr(cockpit_main, "default_captures_dir", lambda: tmp_path / "captures")
    captured: dict[str, Any] = {}
    real_create_app = cockpit_main.create_app

    def _spy_create_app(session: Any, **kwargs: Any) -> Any:
        captured["session"] = session
        return real_create_app(session, **kwargs)

    monkeypatch.setattr(cockpit_main, "create_app", _spy_create_app)
    monkeypatch.setattr(cockpit_main.uvicorn, "run", lambda app, *, host, port: None)

    cockpit_main.main()

    on_disk = (tmp_path / "arm-secret").read_text(encoding="utf-8")
    assert on_disk
    # The session the app serves carries exactly the secret written to disk,
    # so a client that can read the 0600 file — and only such a client — arms.
    assert captured["session"].arm_secret == on_disk
    # And it is NOT the handshake token.
    assert captured["session"].arm_secret != (tmp_path / "ws-token").read_text(encoding="utf-8")


def test_arm_secret_path_defaults_under_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fresh checkout works with no env-var dance."""

    monkeypatch.delenv(cockpit_main._ARM_SECRET_FILE_ENV_VAR, raising=False)
    monkeypatch.setattr(cockpit_main.Path, "home", classmethod(lambda cls: Path("/fake/home")))

    resolved = cockpit_main._resolve_arm_secret_path()

    assert resolved.name == "cockpit-arm-secret"
    assert resolved.parent.name == ".rytm-randomizer"


def test_arm_secret_path_honours_its_env_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(cockpit_main._ARM_SECRET_FILE_ENV_VAR, str(tmp_path / "elsewhere"))

    assert cockpit_main._resolve_arm_secret_path() == (tmp_path / "elsewhere").absolute()


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


@pytest.mark.parametrize("value", ["off", "OFF", "  Off  "])
def test_build_port_enumerator_env_kill_switch_forces_null(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """``RYTM_RAND_MIDI_BACKEND=off`` forces the null enumerator even with mido.

    The escape hatch for CI/headless hosts and misbehaving OS MIDI services
    (python-rtmidi can abort the process from C++ when the OS MIDI client
    cannot be created — uncatchable in Python, so prevention is the fix).
    """

    monkeypatch.setenv("RYTM_RAND_MIDI_BACKEND", value)
    # find_spec would say mido exists; the kill switch must win first.
    monkeypatch.setattr(
        cockpit_main.importlib.util,
        "find_spec",
        lambda name: pytest.fail("find_spec must not be consulted when backend=off"),
    )

    enumerator = cockpit_main._build_port_enumerator()

    assert isinstance(enumerator, NullPortEnumerator)


def test_build_port_enumerator_env_auto_keeps_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Values other than ``off`` behave as ``auto`` (mido-absent fallback here)."""

    monkeypatch.setenv("RYTM_RAND_MIDI_BACKEND", "auto")
    monkeypatch.setattr(cockpit_main.importlib.util, "find_spec", lambda name: None)

    enumerator = cockpit_main._build_port_enumerator()

    assert isinstance(enumerator, NullPortEnumerator)


@pytest.mark.parametrize("value", ["fake", "FAKE", "  Fake  "])
def test_build_port_enumerator_env_fake_returns_elektron_shaped_defaults(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """``RYTM_RAND_MIDI_BACKEND=fake`` → the no-hardware e2e seam.

    Default port names must satisfy the Elektron heuristic (so the
    manager reaches ``listening``), appear identically on inputs and
    outputs, and never consult ``mido`` — the fake works on hosts
    without the hardware extra.
    """

    monkeypatch.setenv("RYTM_RAND_MIDI_BACKEND", value)
    monkeypatch.delenv("RYTM_RAND_FAKE_PORTS", raising=False)
    monkeypatch.setattr(
        cockpit_main.importlib.util,
        "find_spec",
        lambda name: pytest.fail("find_spec must not be consulted when backend=fake"),
    )

    enumerator = cockpit_main._build_port_enumerator()

    assert isinstance(enumerator, FakePortEnumerator)
    assert enumerator.list_input_names() == DEFAULT_FAKE_PORT_NAMES
    assert enumerator.list_output_names() == enumerator.list_input_names()
    assert all(is_elektron_port_name(name) for name in enumerator.list_input_names())


def test_build_port_enumerator_fake_ports_env_overrides_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``RYTM_RAND_FAKE_PORTS`` replaces the default fake port list."""

    monkeypatch.setenv("RYTM_RAND_MIDI_BACKEND", "fake")
    monkeypatch.setenv("RYTM_RAND_FAKE_PORTS", "Custom Port A,Custom Port B")

    enumerator = cockpit_main._build_port_enumerator()

    assert isinstance(enumerator, FakePortEnumerator)
    assert enumerator.list_input_names() == ("Custom Port A", "Custom Port B")
    assert enumerator.list_output_names() == ("Custom Port A", "Custom Port B")


def test_build_port_enumerator_fake_ports_empty_string_means_zero_ports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty override → no ports: a ``fake`` launch that starts ``searching``."""

    monkeypatch.setenv("RYTM_RAND_MIDI_BACKEND", "fake")
    monkeypatch.setenv("RYTM_RAND_FAKE_PORTS", "")

    enumerator = cockpit_main._build_port_enumerator()

    assert isinstance(enumerator, FakePortEnumerator)
    assert enumerator.list_input_names() == ()
    assert enumerator.list_output_names() == ()


def test_resolve_fake_port_names_defaults_when_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RYTM_RAND_FAKE_PORTS", raising=False)

    assert cockpit_main._resolve_fake_port_names() == DEFAULT_FAKE_PORT_NAMES


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Elektron Analog Rytm MKII  ", ("Elektron Analog Rytm MKII",)),
        (" , Fake In ,, Fake Out ,", ("Fake In", "Fake Out")),
        (",,,", ()),
        ("   ", ()),
    ],
)
def test_resolve_fake_port_names_strips_whitespace_and_drops_empty_entries(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: tuple[str, ...]
) -> None:
    monkeypatch.setenv("RYTM_RAND_FAKE_PORTS", raw)

    assert cockpit_main._resolve_fake_port_names() == expected


def test_build_port_enumerator_fake_ports_env_ignored_outside_fake_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stray ``RYTM_RAND_FAKE_PORTS`` never leaks into the auto path."""

    monkeypatch.delenv("RYTM_RAND_MIDI_BACKEND", raising=False)
    monkeypatch.setenv("RYTM_RAND_FAKE_PORTS", "Ghost Port")
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


# ---------------------------------------------------------------------------
# Wave 4 — input opener + main() wiring of library / watchdog / monitor.
# ---------------------------------------------------------------------------


def test_build_input_opener_returns_provider_when_mido_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """mido is a required dependency in the dev env: the opener is real."""

    monkeypatch.delenv("RYTM_RAND_MIDI_BACKEND", raising=False)

    opener = cockpit_main._build_input_opener()
    assert opener is not None
    assert callable(getattr(opener, "open_input", None))


def test_build_input_opener_returns_none_when_mido_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RYTM_RAND_MIDI_BACKEND", raising=False)
    monkeypatch.setattr(cockpit_main.importlib.util, "find_spec", lambda _n: None)
    assert cockpit_main._build_input_opener() is None


@pytest.mark.parametrize("value", ["off", "OFF", "  Off  ", "fake", "FAKE", "  Fake  "])
def test_build_input_opener_returns_none_for_fake_and_off_backends(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """``RYTM_RAND_MIDI_BACKEND=fake``/``off`` must never yield a real opener.

    The fake backend enumerates port names no OS MIDI service knows;
    with a real opener the monitor would dial a REAL rtmidi input for a
    nonexistent port the moment the phase reaches ``listening``
    (observed on macOS as the transient CoreMIDI ``-304`` process
    abort; on CI it would target a port that isn't there). Same env
    seam as :func:`_build_port_enumerator` — and like there, ``mido``
    availability must not even be consulted.
    """

    monkeypatch.setenv("RYTM_RAND_MIDI_BACKEND", value)
    monkeypatch.setattr(
        cockpit_main.importlib.util,
        "find_spec",
        lambda name: pytest.fail("find_spec must not be consulted when backend=fake/off"),
    )

    assert cockpit_main._build_input_opener() is None


def test_build_input_opener_env_auto_keeps_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Values other than ``off``/``fake`` behave as ``auto`` (mido-absent here)."""

    monkeypatch.setenv("RYTM_RAND_MIDI_BACKEND", "auto")
    monkeypatch.setattr(cockpit_main.importlib.util, "find_spec", lambda _n: None)

    assert cockpit_main._build_input_opener() is None


def test_main_wires_wave4_library_watchdog_and_monitor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``main()`` injects the library store and registers the Wave-4 hooks."""

    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    monkeypatch.setattr(cockpit_main, "default_library_dir", lambda: tmp_path / "library")
    monkeypatch.setattr(cockpit_main, "default_captures_dir", lambda: tmp_path / "captures")
    monkeypatch.delenv(cockpit_main._PORT_ENV_VAR, raising=False)
    monkeypatch.delenv("RYTM_RAND_MIDI_BACKEND", raising=False)
    _redirect_token_file(monkeypatch, tmp_path)

    captured: dict[str, Any] = {}
    sessions: list[CockpitSession] = []
    real_build_session = cockpit_main.build_session

    def _capture_session() -> CockpitSession:
        session = real_build_session()
        sessions.append(session)
        return session

    def _fake_run(app: Any, *, host: str, port: int) -> None:
        captured["app"] = app

    monkeypatch.setattr(cockpit_main, "build_session", _capture_session)
    monkeypatch.setattr(cockpit_main, "uvicorn", type("U", (), {"run": staticmethod(_fake_run)}))

    cockpit_main.main()

    session = sessions[0]
    # Library store injected with the platform-dir + captures defaults.
    assert session.library_store is not None
    assert session.library_store.library_dir == tmp_path / "library"
    assert session.library_store.captures_dir == tmp_path / "captures"
    # The ConnectionManager carries the session's error journal and the
    # Wave-4 notify hooks (armed watchdog + monitor supervisor when mido
    # is importable — which it is in the dev env).
    manager = active_connection_manager()
    assert manager is not None
    assert manager._journal is session.error_journal
    assert len(manager._notify_hooks) == 2
    # The supervisor's shutdown hook is installed on the app lifecycle.
    app = captured["app"]
    shutdown_names = [getattr(h, "__qualname__", "") for h in app.router.on_shutdown]
    assert any("MidiMonitorSupervisor.aclose" in name for name in shutdown_names)


def test_main_skips_monitor_supervisor_when_mido_absent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    monkeypatch.setattr(cockpit_main, "default_library_dir", lambda: tmp_path / "library")
    monkeypatch.setattr(cockpit_main, "default_captures_dir", lambda: tmp_path / "captures")
    monkeypatch.delenv(cockpit_main._PORT_ENV_VAR, raising=False)
    _redirect_token_file(monkeypatch, tmp_path)
    monkeypatch.setattr(cockpit_main, "_build_input_opener", lambda: None)

    captured: dict[str, Any] = {}

    def _fake_run(app: Any, *, host: str, port: int) -> None:
        captured["app"] = app

    monkeypatch.setattr(cockpit_main, "uvicorn", type("U", (), {"run": staticmethod(_fake_run)}))

    cockpit_main.main()

    manager = active_connection_manager()
    assert manager is not None
    # Only the armed watchdog is registered — no monitor supervisor.
    assert len(manager._notify_hooks) == 1
    app = captured["app"]
    shutdown_names = [getattr(h, "__qualname__", "") for h in app.router.on_shutdown]
    assert not any("MidiMonitorSupervisor" in name for name in shutdown_names)


def test_main_skips_monitor_supervisor_when_backend_is_fake(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A ``fake`` launch must never wire the real-input monitor.

    End-to-end pin of the FIX-1 defect: with ``RYTM_RAND_MIDI_BACKEND=fake``
    the fake enumerator reaches ``listening``, and a wired monitor would
    then open a REAL rtmidi input for the fake port name. ``main()`` must
    therefore skip the supervisor entirely — the fake launch runs with no
    ``midi_activity`` stream, by design.
    """

    monkeypatch.setattr(cockpit_main, "default_profiles_dir", lambda: tmp_path)
    monkeypatch.setattr(cockpit_main, "default_library_dir", lambda: tmp_path / "library")
    monkeypatch.setattr(cockpit_main, "default_captures_dir", lambda: tmp_path / "captures")
    monkeypatch.delenv(cockpit_main._PORT_ENV_VAR, raising=False)
    monkeypatch.setenv("RYTM_RAND_MIDI_BACKEND", "fake")
    _redirect_token_file(monkeypatch, tmp_path)

    captured: dict[str, Any] = {}

    def _fake_run(app: Any, *, host: str, port: int) -> None:
        captured["app"] = app

    monkeypatch.setattr(cockpit_main, "uvicorn", type("U", (), {"run": staticmethod(_fake_run)}))

    cockpit_main.main()

    manager = active_connection_manager()
    assert manager is not None
    # Only the armed watchdog hook — no monitor supervisor for fake backends.
    assert len(manager._notify_hooks) == 1
    app = captured["app"]
    shutdown_names = [getattr(h, "__qualname__", "") for h in app.router.on_shutdown]
    assert not any("MidiMonitorSupervisor" in name for name in shutdown_names)

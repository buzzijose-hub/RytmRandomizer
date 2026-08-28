"""Launch smoke test — the double-click contract, without the binary.

Boots the EXACT process the Tauri shell spawns in dev-fallback mode
(``python -m rytm_randomizer.app --arm --cockpit-kit-capture-sidecar``) as a real subprocess with the
same environment contract the shell uses (``RYTM_RAND_WS_PORT`` +
``RYTM_RAND_WS_TOKEN_FILE``), then walks the full launch health path:

1. Poll ``GET /health`` until the sidecar answers (liveness).
2. Read the freshly-minted handshake token from the token file.
3. Open the WebSocket with the pinned subprotocol, send the ``hello``
   frame, and assert the ack + the 11-frame bootstrap event set (plus
   the wired-launch ``connection_changed`` extra) arrive in order.
4. Shut the process down cleanly (SIGTERM on POSIX — the same signal
   the shell sends — and assert a zero exit).

CI runs this module as the ``launch-smoke`` job in
``.github/workflows/test.yml``; locally it is part of ``pytest -m fast``.

The module also structurally validates ``scripts/build_sidecar_binary.py``
(the PyInstaller bundling script) so its contract with the Rust shell —
the stdin shutdown sentinel, the deterministic entry stub, the env
passthrough — is pinned even on machines where PyInstaller is not
installed. Building the actual binary stays a CI-only (installers.yml)
concern.
"""

from __future__ import annotations

import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_MISSING_RUNTIME_DEPS = [
    name for name in ("fastapi", "uvicorn", "websockets") if importlib.util.find_spec(name) is None
]
if _MISSING_RUNTIME_DEPS:  # pragma: no cover - dep-less checkout only
    pytest.skip(
        "cockpit sidecar runtime deps missing: " + ", ".join(_MISSING_RUNTIME_DEPS),
        allow_module_level=True,
    )

WS_SUBPROTOCOL = "rytm-rand-cockpit-v1"
"""Pinned subprotocol (mirrors rytm_randomizer.cockpit.ws.protocol.WS_SUBPROTOCOL)."""

EXPECTED_BOOTSTRAP_EVENT_TYPES = (
    "session_status",
    "snapshot_changed",
    "profile_changed",
    "profile_catalog_changed",
    "history_updated",
    "patch_genome_changed",
    "kit_captures_changed",
    "mutation_targets_changed",
    "mutation_locks_changed",
    "dual_machine_stage_changed",
    "performance_console_changed",
)
"""The 11 bootstrap events every fresh connection receives, in spec order."""

HEALTH_TIMEOUT_SECS = 90.0
"""Generous ceiling for the subprocess to import + bind + serve on CI."""

SHUTDOWN_TIMEOUT_SECS = 30.0
"""Generous ceiling for uvicorn's graceful shutdown after SIGTERM."""

_POLL_INTERVAL_SECS = 0.25


def _load_build_script() -> ModuleType:
    """Import ``scripts/build_sidecar_binary.py`` from its file path.

    ``scripts/`` is not a package, so the module is loaded directly. The
    script keeps PyInstaller imports inside the build path, so loading it
    never requires PyInstaller.
    """

    script_path = PROJECT_ROOT / "scripts" / "build_sidecar_binary.py"
    spec = importlib.util.spec_from_file_location("build_sidecar_binary", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _free_loopback_port() -> int:
    """Ask the OS for a currently-free ephemeral loopback port."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


# The probe socket above closes before the sidecar re-binds the port, so under
# a heavily parallel suite (xdist workers + other ws tests grabbing ephemeral
# ports) another process can occasionally snatch the port in the gap and
# uvicorn exits at bind time. That specific race is retried with a fresh port;
# every other early exit fails loudly.
_BIND_RACE_MARKERS: tuple[str, ...] = (
    "address already in use",
    "errno 48",  # macOS EADDRINUSE
    "errno 98",  # Linux EADDRINUSE
    "winerror 10048",  # Windows WSAEADDRINUSE
)
_PORT_RETRY_ATTEMPTS = 3


class _SidecarExitedEarly(Exception):
    """The sidecar process died before /health answered."""

    def __init__(self, returncode: int | None, output: str) -> None:
        super().__init__(f"sidecar exited early (returncode={returncode})")
        self.output = output


def _fail_with_process_output(proc: subprocess.Popen, log_path: Path, reason: str) -> None:
    """Kill the sidecar and fail loudly with its captured output."""

    proc.kill()
    proc.wait(timeout=30)
    output = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    pytest.fail(f"{reason}\n--- sidecar output ---\n{output[-8000:]}")


def _wait_for_health(proc: subprocess.Popen, log_path: Path, port: int) -> dict:
    """Poll ``GET /health`` until the sidecar answers; return the payload."""

    deadline = time.monotonic() + HEALTH_TIMEOUT_SECS
    url = f"http://127.0.0.1:{port}/health"
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            output = (
                log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
            )
            raise _SidecarExitedEarly(proc.returncode, output)
        try:
            with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310 - loopback
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    if isinstance(payload, dict):
                        return payload
        except (urllib.error.URLError, OSError, ValueError):
            pass
        time.sleep(_POLL_INTERVAL_SECS)
    _fail_with_process_output(
        proc, log_path, f"GET /health never answered within {HEALTH_TIMEOUT_SECS}s"
    )
    raise AssertionError("unreachable")  # pragma: no cover - _fail always raises


def _read_token(proc: subprocess.Popen, log_path: Path, token_file: Path) -> str:
    """Return the non-empty handshake token the sidecar wrote to disk."""

    deadline = time.monotonic() + HEALTH_TIMEOUT_SECS
    while time.monotonic() < deadline:
        if token_file.exists():
            token = token_file.read_text(encoding="utf-8").strip()
            if token:
                return token
        time.sleep(_POLL_INTERVAL_SECS)
    _fail_with_process_output(proc, log_path, "sidecar never wrote a non-empty token file")
    raise AssertionError("unreachable")  # pragma: no cover - _fail always raises


def test_launch_smoke_end_to_end(tmp_path: Path) -> None:
    """Boot the real sidecar and drive health + handshake + clean shutdown."""

    from websockets.sync.client import connect

    port = _free_loopback_port()
    token_file = tmp_path / "cockpit-ws-token.txt"
    log_path = tmp_path / "sidecar-output.log"
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    env = dict(os.environ)
    env["RYTM_RAND_WS_PORT"] = str(port)
    env["RYTM_RAND_WS_TOKEN_FILE"] = str(token_file)
    # Hermetic profile/library/capture dirs: the sidecar seeds built-in
    # scenes under the user config dir on first boot.
    env["HOME"] = str(home_dir)
    env["USERPROFILE"] = str(home_dir)
    env["XDG_CONFIG_HOME"] = str(home_dir / ".config")
    # Hermetic MIDI backend: this test pins the launch/handshake/shutdown
    # contract, not OS MIDI. With the backend on, python-rtmidi 1.5.8 can
    # abort the sidecar from its C++ layer when the OS MIDI client cannot
    # be created (macOS CoreMIDI -304 under xdist load; headless CI has no
    # MIDI service at all) — an uncatchable libc++abi termination, not a
    # Python exception. The NullPortEnumerator path keeps the launch
    # contract byte-identical (connection_changed still flows).
    env["RYTM_RAND_MIDI_BACKEND"] = "off"

    proc: subprocess.Popen | None = None
    health: dict[str, object] | None = None
    for attempt in range(_PORT_RETRY_ATTEMPTS):
        env["RYTM_RAND_WS_PORT"] = str(port)
        with log_path.open("wb") as log_handle:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "rytm_randomizer.app",
                    "--arm",
                    "--cockpit-kit-capture-sidecar",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                stdin=subprocess.PIPE,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
        try:
            health = _wait_for_health(proc, log_path, port)
            break
        except _SidecarExitedEarly as exc:
            lowered = exc.output.lower()
            if attempt < _PORT_RETRY_ATTEMPTS - 1 and any(
                marker in lowered for marker in _BIND_RACE_MARKERS
            ):
                port = _free_loopback_port()
                continue
            pytest.fail(f"{exc}\n--- sidecar output ---\n{exc.output[-8000:]}")
    assert proc is not None and health is not None  # retry loop always binds these

    try:
        assert "version" in health, f"health payload missing version: {health!r}"
        # A freshly-booted sidecar is passive: never armed at launch.
        assert health.get("mode", "mock") == "mock", health

        token = _read_token(proc, log_path, token_file)

        with connect(
            f"ws://127.0.0.1:{port}/ws",
            subprotocols=[WS_SUBPROTOCOL],
            open_timeout=30,
        ) as ws:
            ws.send(json.dumps({"type": "hello", "token": token}))
            ack = json.loads(ws.recv(timeout=30))
            assert ack == {"ok": True}, f"handshake ack mismatch: {ack!r}"

            bootstrap_events = [
                json.loads(ws.recv(timeout=30)) for _ in EXPECTED_BOOTSTRAP_EVENT_TYPES
            ]
            received_types = [event.get("type") for event in bootstrap_events]
            assert received_types == list(EXPECTED_BOOTSTRAP_EVENT_TYPES), (
                "bootstrap event order drifted: " f"{received_types!r}"
            )
            # The packaged app composition injects input-only KIT capture
            # authority while output remains unarmed. ``MIDI_BACKEND=off``
            # keeps this smoke hermetic; no provider method is invoked.
            session_status = bootstrap_events[0]
            assert session_status.get("capture_enabled") is True, session_status
            assert session_status.get("armed") is False, session_status
            # The wired launch path (__main__ installs a
            # ConnectionManager) appends a connection_changed frame so
            # the header renders plug/unplug truth immediately.
            extra = json.loads(ws.recv(timeout=30))
            assert extra.get("type") == "connection_changed", extra

        # Clean shutdown: SIGTERM on POSIX (what the Tauri shell sends
        # before its 5s kill); Windows has no SIGTERM so terminate().
        if sys.platform == "win32":  # pragma: no cover - POSIX dev/CI
            proc.terminate()
            proc.wait(timeout=SHUTDOWN_TIMEOUT_SECS)
        else:
            proc.send_signal(signal.SIGTERM)
            returncode = proc.wait(timeout=SHUTDOWN_TIMEOUT_SECS)
            # 0 is a plain clean exit; -SIGTERM is uvicorn's convention
            # (it completes its graceful shutdown, then re-raises the
            # captured signal so the OS-level exit status is honest).
            # Either way the log must show the full shutdown sequence.
            assert returncode in (0, -signal.SIGTERM), (
                f"sidecar did not exit cleanly on SIGTERM (returncode={returncode})\n"
                + log_path.read_text(encoding="utf-8", errors="replace")[-8000:]
            )
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            assert "Application shutdown complete" in log_text, log_text[-8000:]
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=30)


# ---------------------------------------------------------------------------
# Structural contract of scripts/build_sidecar_binary.py (no PyInstaller
# required — the bundling itself runs only in installers.yml).
# ---------------------------------------------------------------------------


def test_build_script_entry_stub_is_deterministic_module_equivalent() -> None:
    """The generated stub delegates to the armed input-only app composition."""

    build_script = _load_build_script()
    source = build_script.entry_source()
    assert "from rytm_randomizer.app import main as app_main" in source
    assert 'app_main(["--arm", "--cockpit-kit-capture-sidecar"])' in source
    assert build_script.SHUTDOWN_SENTINEL in source
    # The stub must be valid Python (it is written verbatim at build time).
    compile(source, "rytm_sidecar_entry.py", "exec")


def test_build_script_pyinstaller_command_shape(tmp_path: Path) -> None:
    """One-file build, canonical name, app collected, audio stack excluded."""

    build_script = _load_build_script()
    entry = tmp_path / "rytm_sidecar_entry.py"
    command = build_script.pyinstaller_command(
        entry, output_dir=tmp_path / "dist", work_dir=tmp_path / "work", python="pythonX"
    )
    assert command[:3] == ["pythonX", "-m", "PyInstaller"]
    assert "--onefile" in command
    name_index = command.index("--name")
    assert command[name_index + 1] == build_script.SIDECAR_BINARY_NAME == "rytm-sidecar"
    collected = [command[i + 1] for i, arg in enumerate(command) if arg == "--collect-all"]
    assert "rytm_randomizer" in collected
    assert "uvicorn" in collected and "websockets" in collected
    excluded = [command[i + 1] for i, arg in enumerate(command) if arg == "--exclude-module"]
    assert "librosa" in excluded
    assert command[-1] == str(entry)


def test_build_script_env_passthrough_names_match_cockpit_entrypoint() -> None:
    """The documented passthrough env vars are the cockpit's real ones."""

    build_script = _load_build_script()
    from rytm_randomizer.cockpit import __main__ as cockpit_main

    assert build_script.PORT_ENV_VAR == cockpit_main._PORT_ENV_VAR
    assert build_script.TOKEN_FILE_ENV_VAR == cockpit_main._TOKEN_FILE_ENV_VAR


def test_shutdown_sentinel_pinned_across_python_and_rust() -> None:
    """The stdin shutdown sentinel matches between the build script and the shell."""

    build_script = _load_build_script()
    sidecar_rs = (PROJECT_ROOT / "desktop" / "shell" / "src" / "sidecar.rs").read_text(
        encoding="utf-8"
    )
    expected = f'pub const SHUTDOWN_SENTINEL: &str = "{build_script.SHUTDOWN_SENTINEL}";'
    assert expected in sidecar_rs, (
        "desktop/shell/src/sidecar.rs SHUTDOWN_SENTINEL drifted from "
        "scripts/build_sidecar_binary.py — the Tauri shell's graceful "
        "shutdown channel would silently stop working on Windows."
    )


def test_packaging_extra_ships_pyinstaller() -> None:
    """The `packaging` optional-deps extra exists and pins PyInstaller."""

    tomllib = pytest.importorskip("tomllib")
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = pyproject["project"]["optional-dependencies"]
    assert "packaging" in extras, "pyproject.toml lost the [packaging] extra"
    assert any(dep.startswith("pyinstaller") for dep in extras["packaging"])

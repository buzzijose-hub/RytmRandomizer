"""Build the bundled ``rytm-sidecar`` one-file binary with PyInstaller.

CI-first tool: ``.github/workflows/installers.yml`` runs this script on
each OS of the desktop-bundle matrix and drops the resulting binary into
``desktop/shell/binaries/`` so ``cargo tauri build`` picks it up through
the ``bundle.resources`` glob in ``desktop/shell/tauri.conf.json``. The
Tauri shell then spawns the bundled binary at launch time instead of
requiring a ``python`` on the operator's PATH — that is the whole
double-click story (see docs/BUILDING_INSTALLERS.md § "Bundled Python
sidecar").

Design constraints honoured here:

* **Deterministic entry point.** The generated entry stub is the exact
  equivalent of ``python -m rytm_randomizer.app --arm
  --cockpit-kit-capture-sidecar`` — it imports and calls
  :func:`rytm_randomizer.app.main` with those fixed arguments. No logic
  forks between the dev path and the bundled path.
* **Environment passthrough.** The binary needs zero flags: the cockpit
  reads ``RYTM_RAND_WS_PORT`` and ``RYTM_RAND_WS_TOKEN_FILE`` from the
  environment at runtime (same contract as the dev path), so the Tauri
  shell configures the child identically either way.
* **Cross-platform graceful shutdown.** The entry stub watches stdin for
  the ``RYTM_SIDECAR_SHUTDOWN`` sentinel (or EOF — the pipe closing when
  the shell exits). Either trigger raises ``SIGINT`` in-process so
  uvicorn runs its normal graceful shutdown; a watchdog timer hard-exits
  if the loop wedges. This is what gives Windows — where the shell has
  no SIGTERM — a clean-shutdown channel before the 5-second kill.
* **PyInstaller stays optional.** PyInstaller lives in the ``packaging``
  optional-dependency extra (``pip install -e ".[packaging]"``) and is
  imported nowhere at module level, so this script is importable (and
  structurally testable — see tests/test_launch_smoke.py) in
  environments that never install it.

Usage (from the repo root, with ``.[cockpit,packaging]`` installed)::

    python scripts/build_sidecar_binary.py \
        --output-dir desktop/shell/binaries

The audio stack is bundled for the existing spawned analysis worker. The
entry dispatches multiprocessing children before importing the server or
starting its shutdown watcher. Audio imports remain lazy; collecting assets
does not grant the worker MIDI or server-startup authority.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

SIDECAR_BINARY_NAME: Final[str] = "rytm-sidecar"
"""Basename of the produced binary (PyInstaller adds ``.exe`` on Windows)."""

SHUTDOWN_SENTINEL: Final[str] = "RYTM_SIDECAR_SHUTDOWN"
"""Line the Tauri shell writes to the sidecar's stdin to request shutdown.

Must match ``SHUTDOWN_SENTINEL`` in ``desktop/shell/src/sidecar.rs`` —
tests/test_launch_smoke.py pins the two in lockstep.
"""

PORT_ENV_VAR: Final[str] = "RYTM_RAND_WS_PORT"
"""Runtime port override the cockpit honours (passthrough, not baked in)."""

TOKEN_FILE_ENV_VAR: Final[str] = (
    "RYTM_RAND_WS_TOKEN_FILE"  # noqa: S105 — env var name, not a secret
)
"""Runtime token-file override the cockpit honours (passthrough, not baked in)."""

_FORCE_EXIT_GRACE_SECS: Final[float] = 10.0
"""Watchdog delay between the graceful SIGINT and the hard os._exit fallback."""

#: Packages PyInstaller must collect wholesale. ``rytm_randomizer`` is the
#: app itself (its cockpit tree lazy-imports aggressively, which defeats
#: PyInstaller's static import scan); uvicorn/websockets are the ASGI
#: serving stack with dynamic loader lookups; mido + rtmidi are the
#: passive enumeration/monitor boundary; msgpack backs profile export.
COLLECT_ALL_PACKAGES: Final[tuple[str, ...]] = (
    "rytm_randomizer",
    "uvicorn",
    "websockets",
    "mido",
    "rtmidi",
    "msgpack",
)

#: Only the measured audio surface is explicitly included. librosa exposes
#: these modules through lazy_loader and .pyi stubs, which static scanning
#: alone cannot resolve. Native dependencies use PyInstaller's package hooks.
AUDIO_HIDDEN_IMPORTS: Final[tuple[str, ...]] = (
    "librosa.core.audio",
    "librosa.core.convert",
    "librosa.core.spectrum",
    "librosa.feature.spectral",
    "librosa.filters",
    "librosa.onset",
    "librosa.util.utils",
    "soundfile",
    "soxr",
)
AUDIO_DATA_PACKAGES: Final[tuple[str, ...]] = ("librosa",)
AUDIO_BINARY_PACKAGES: Final[tuple[str, ...]] = ("_soundfile_data", "soxr", "llvmlite")
AUDIO_REQUIRED_PACKAGES: Final[tuple[str, ...]] = (
    "librosa",
    "numpy",
    "scipy",
    "soundfile",
    "soxr",
    "numba",
    "llvmlite",
)

#: Optional plotting/notebook packages do not participate in extraction.
EXCLUDED_PACKAGES: Final[tuple[str, ...]] = (
    "matplotlib",
    "IPython",
)


def audio_hook_source() -> str:
    """Keep librosa source available for Numba stencil compilation in workers."""

    return '''"""Generated hook for the bounded librosa measurement surface."""
from PyInstaller.utils.hooks import collect_data_files

# Numba's stencil compiler reads the original Python function source.
module_collection_mode = {"librosa": "pyz+py"}
datas = collect_data_files("librosa", includes=["*.pyi", "**/*.pyi"])
'''


def entry_source() -> str:
    """Return the deterministic PyInstaller entry-stub source.

    Written to the work directory at build time and handed to
    PyInstaller as the program entry. Kept as a generated string (not a
    committed module) so the stub can never drift into a second
    launch-behaviour fork — the only committed launch contract is
    ``rytm_randomizer.app.main`` capture composition.
    """

    return f'''"""Generated entry stub for the bundled rytm-sidecar binary.

Equivalent to ``python -m rytm_randomizer.app --arm
--cockpit-kit-capture-sidecar`` plus a stdin
shutdown channel for the Tauri shell (cross-platform: works on Windows
where SIGTERM does not exist). Generated by
scripts/build_sidecar_binary.py — do not edit or commit.
"""

import multiprocessing
import os
import signal
import sys
import threading
import time

SHUTDOWN_SENTINEL = {SHUTDOWN_SENTINEL!r}
_FORCE_EXIT_GRACE_SECS = {_FORCE_EXIT_GRACE_SECS!r}


def _wait_for_windows_stdin_pipe() -> bool:
    """Poll pipe bytes without leaving a synchronous ReadFile pending.

    A spawned frozen child inherits the pipe's file object. Python's startup
    seeks its standard streams, which Windows serializes behind a pending
    parent read. A blocking stdin watcher therefore deadlocks child startup.
    """

    if sys.platform != "win32":
        return False
    import ctypes
    import msvcrt
    from ctypes import wintypes

    try:
        descriptor = sys.stdin.fileno()
        handle = msvcrt.get_osfhandle(descriptor)
    except (AttributeError, OSError, ValueError):
        return False
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetFileType.argtypes = [wintypes.HANDLE]
    kernel.GetFileType.restype = wintypes.DWORD
    if kernel.GetFileType(handle) != 3:  # FILE_TYPE_PIPE; consoles/files do not block seeks.
        return False
    kernel.PeekNamedPipe.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
        ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
    ]
    kernel.PeekNamedPipe.restype = wintypes.BOOL
    pending = b""
    while True:
        available = wintypes.DWORD()
        if not kernel.PeekNamedPipe(handle, None, 0, None, ctypes.byref(available), None):
            return True  # Broken pipe/EOF retains the shell-loss shutdown contract.
        if not available.value:
            time.sleep(0.05)
            continue
        chunk = os.read(descriptor, min(available.value, 4096))
        if not chunk:
            return True
        lines = (pending + chunk).split(b"\\n")
        pending = lines.pop()[-4096:]
        if any(line.strip() == SHUTDOWN_SENTINEL.encode("ascii") for line in lines):
            return True


def _watch_stdin() -> None:
    """Block until the shell writes the sentinel (or closes the pipe)."""

    try:
        if not _wait_for_windows_stdin_pipe():
            for line in sys.stdin:
                if line.strip() == SHUTDOWN_SENTINEL:
                    break
    except Exception:  # noqa: BLE001 — any stdin fault means the shell is gone
        pass
    # Graceful first: SIGINT drives uvicorn's normal shutdown path. The
    # watchdog hard-exits if the serving loop wedges past the grace.
    watchdog = threading.Timer(_FORCE_EXIT_GRACE_SECS, os._exit, args=(0,))
    watchdog.daemon = True
    watchdog.start()
    try:
        signal.raise_signal(signal.SIGINT)
    except (ValueError, OSError):
        os._exit(0)


def main() -> None:
    # PyInstaller's runtime hook dispatches workers and exits here. It must
    # run before watcher creation or any app/server/MIDI composition import.
    multiprocessing.freeze_support()
    if sys.stdin is not None:
        threading.Thread(
            target=_watch_stdin, name="sidecar-shutdown-watch", daemon=True
        ).start()
    from rytm_randomizer.app import main as app_main

    app_main(["--arm", "--cockpit-kit-capture-sidecar"])


if __name__ == "__main__":
    main()
'''


def pyinstaller_command(
    entry_path: Path,
    *,
    output_dir: Path,
    work_dir: Path,
    name: str = SIDECAR_BINARY_NAME,
    python: str | None = None,
) -> list[str]:
    """Build the PyInstaller argv (pure — structurally testable without PyInstaller)."""

    interpreter = python if python is not None else sys.executable
    command = [
        interpreter,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        name,
        "--noconfirm",
        "--clean",
        "--console",
        "--distpath",
        str(output_dir),
        "--workpath",
        str(work_dir / "build"),
        "--specpath",
        str(work_dir),
        "--additional-hooks-dir",
        str(work_dir / "hooks"),
        "--add-data",
        f"{PROJECT_ROOT / 'rytm_randomizer/data/MIDI_GUIDE_DATA_NOTICE.txt'}:rytm_randomizer/data",
    ]
    for package in COLLECT_ALL_PACKAGES:
        command.extend(["--collect-all", package])
    for module in AUDIO_HIDDEN_IMPORTS:
        command.extend(["--hidden-import", module])
    for package in AUDIO_DATA_PACKAGES:
        command.extend(["--collect-data", package])
    for package in AUDIO_BINARY_PACKAGES:
        command.extend(["--collect-binaries", package])
    for package in EXCLUDED_PACKAGES:
        command.extend(["--exclude-module", package])
    command.append(str(entry_path))
    return command


def pyinstaller_available() -> bool:
    """True when PyInstaller is importable in the current environment."""

    return importlib.util.find_spec("PyInstaller") is not None


def build(output_dir: Path, work_dir: Path) -> Path:
    """Write the entry stub, run PyInstaller, and return the binary path.

    Raises :class:`RuntimeError` when PyInstaller is missing (install the
    ``packaging`` extra) or when the expected binary does not exist after
    a zero-exit build (a packaging regression worth failing loudly on).
    """

    if not pyinstaller_available():
        raise RuntimeError(
            "PyInstaller is not installed. Install the packaging extra first:\n"
            '    pip install -e ".[cockpit,packaging]"'
        )
    missing = tuple(
        package for package in AUDIO_REQUIRED_PACKAGES if importlib.util.find_spec(package) is None
    )
    if missing:
        raise RuntimeError(
            "Audio analysis dependencies are not installed. Install the cockpit extra first:\n"
            '    pip install -e ".[cockpit,packaging]"'
        )
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    entry_path = work_dir / "rytm_sidecar_entry.py"
    entry_path.write_text(entry_source(), encoding="utf-8")
    hook_dir = work_dir / "hooks"
    hook_dir.mkdir(exist_ok=True)
    (hook_dir / "hook-librosa.py").write_text(audio_hook_source(), encoding="utf-8")
    command = pyinstaller_command(entry_path, output_dir=output_dir, work_dir=work_dir)
    print(f"[build-sidecar] running: {' '.join(command)}", flush=True)
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)
    suffix = ".exe" if sys.platform == "win32" else ""
    binary = output_dir / f"{SIDECAR_BINARY_NAME}{suffix}"
    if not binary.is_file():
        raise RuntimeError(f"PyInstaller reported success but {binary} does not exist")
    print(f"[build-sidecar] built {binary}", flush=True)
    return binary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the CLI surface (kept tiny: an output dir and a work dir)."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "desktop" / "shell" / "binaries",
        help="Directory the one-file binary lands in (default: desktop/shell/binaries).",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=PROJECT_ROOT / "build" / "sidecar-pyinstaller",
        help="Scratch directory for the entry stub, spec file, and PyInstaller work tree.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry: build the binary, return a process exit code."""

    args = parse_args(argv)
    try:
        build(args.output_dir.resolve(), args.work_dir.resolve())
    except (RuntimeError, subprocess.CalledProcessError) as err:
        print(f"[build-sidecar] FAILED: {err}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

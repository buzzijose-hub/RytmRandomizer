"""Bundled worker dispatch and packaging contracts, without running a build."""

from __future__ import annotations

import io
import os
import runpy
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest
from test_launch_smoke import _load_build_script

packaging = _load_build_script()

pytestmark = pytest.mark.fast


def _entry() -> dict[str, object]:
    namespace: dict[str, object] = {"__name__": "entry_contract"}
    # Execute only the repository-generated entry to verify its dispatch ordering.
    exec(  # noqa: S102
        compile(packaging.entry_source(), "rytm_sidecar_entry.py", "exec"), namespace
    )
    return namespace


def test_frozen_worker_dispatch_precedes_watcher_and_app_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import multiprocessing
    import threading

    events: list[str] = []
    original = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object):
        assert name != "rytm_randomizer.app", "worker must not import server/MIDI composition"
        return original(name, *args, **kwargs)

    def dispatch() -> None:
        events.append("worker-dispatched")
        raise SystemExit(0)

    monkeypatch.setattr(multiprocessing, "freeze_support", dispatch)
    monkeypatch.setattr(
        threading, "Thread", lambda **_kwargs: pytest.fail("watcher must not start")
    )
    namespace = _entry()
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(SystemExit) as caught:
        namespace["main"]()
    assert caught.value.code == 0
    assert events == ["worker-dispatched"]


@pytest.mark.parametrize("stdin", (None, io.StringIO("")))
def test_normal_frozen_entry_keeps_existing_sidecar_composition(
    monkeypatch: pytest.MonkeyPatch, stdin: io.StringIO | None
) -> None:
    import multiprocessing
    import threading

    events: list[object] = []

    class Watcher:
        def __init__(self, **kwargs: object) -> None:
            events.append(kwargs["name"])

        def start(self) -> None:
            events.append("watcher-started")

    app = ModuleType("rytm_randomizer.app")
    app.main = lambda argv: events.append(argv)
    monkeypatch.setitem(sys.modules, "rytm_randomizer.app", app)
    monkeypatch.setattr(
        multiprocessing, "freeze_support", lambda: events.append("dispatch-checked")
    )
    monkeypatch.setattr(threading, "Thread", Watcher)
    monkeypatch.setattr(sys, "stdin", stdin)
    _entry()["main"]()
    assert events[0] == "dispatch-checked"
    assert events[-1] == ["--arm", "--cockpit-kit-capture-sidecar"]
    assert ("watcher-started" in events) is (stdin is not None)


@pytest.mark.parametrize("fault", (False, True))
@pytest.mark.parametrize("signal_fault", (False, True))
def test_existing_shutdown_watchdog_remains_functional(
    monkeypatch: pytest.MonkeyPatch, fault: bool, signal_fault: bool
) -> None:
    import os
    import signal
    import threading

    events: list[object] = []

    class Timer:
        def __init__(self, delay: float, action: object, *, args: tuple[int]) -> None:
            assert delay == packaging._FORCE_EXIT_GRACE_SECS
            assert action is os._exit and args == (0,)
            self.daemon = False

        def start(self) -> None:
            assert self.daemon
            events.append("watchdog")

    class BrokenStdin:
        def __iter__(self):
            raise OSError("closed")

    def interrupt(value: int) -> None:
        assert value == signal.SIGINT
        events.append("SIGINT")
        if signal_fault:
            raise OSError("cannot signal")

    monkeypatch.setattr(os, "_exit", lambda value: events.append(value))
    monkeypatch.setattr(signal, "raise_signal", interrupt)
    monkeypatch.setattr(threading, "Timer", Timer)
    monkeypatch.setattr(
        sys,
        "stdin",
        BrokenStdin() if fault else io.StringIO(f"ignored\n{packaging.SHUTDOWN_SENTINEL}\n"),
    )
    _entry()["_watch_stdin"]()
    assert events[:2] == ["watchdog", "SIGINT"]
    assert events[2:] == ([0] if signal_fault else [])


@pytest.mark.parametrize("platform", ("linux", "win32"))
def test_stdin_polling_falls_back_for_non_pipe_streams(
    monkeypatch: pytest.MonkeyPatch, platform: str
) -> None:
    msvcrt = ModuleType("msvcrt")
    monkeypatch.setitem(sys.modules, "msvcrt", msvcrt)
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert _entry()["_wait_for_windows_stdin_pipe"]() is False


def test_shutdown_watcher_uses_polling_pipe_without_blocking_line_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import signal
    import threading
    from types import SimpleNamespace

    namespace = _entry()
    namespace["_wait_for_windows_stdin_pipe"] = lambda: True
    monkeypatch.setattr(sys, "stdin", object())
    monkeypatch.setattr(
        threading, "Timer", lambda *_args, **_kwargs: SimpleNamespace(start=lambda: None)
    )
    signals: list[int] = []
    monkeypatch.setattr(signal, "raise_signal", lambda value: signals.append(value))
    namespace["_watch_stdin"]()
    assert signals == [signal.SIGINT]


class _WindowsFunction:
    def __init__(self, action):
        self.action = action

    def __call__(self, *args):
        return self.action(*args)


@pytest.mark.parametrize("ending", ("sentinel", "broken", "empty"))
def test_windows_stdin_polling_reads_only_available_bytes_and_handles_shutdown(
    monkeypatch: pytest.MonkeyPatch, ending: str
) -> None:
    import ctypes
    import time
    from ctypes import wintypes
    from types import SimpleNamespace

    events: list[object] = []
    chunks = [b"ignored\nRYTM_SIDECAR_", b"SHUTDOWN\r\n"]
    availability = [0, len(chunks[0]), len(chunks[1])]
    if ending != "sentinel":
        chunks = [b"ignored\n", b""]
        availability = [0, len(chunks[0]), 1]

    def peek(_handle, _buffer, _size, _read, available, _left):
        if ending == "broken" and len(availability) == 1:
            return False
        ctypes.cast(available, ctypes.POINTER(wintypes.DWORD)).contents.value = availability.pop(0)
        events.append("peek")
        return True

    def read(descriptor: int, size: int) -> bytes:
        assert descriptor == 42 and size > 0
        chunk = chunks.pop(0)
        assert len(chunk) <= size
        events.append("read")
        return chunk

    kernel = SimpleNamespace(
        GetFileType=_WindowsFunction(lambda handle: 3),
        PeekNamedPipe=_WindowsFunction(peek),
    )
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(fileno=lambda: 42))
    msvcrt = ModuleType("msvcrt")
    msvcrt.get_osfhandle = lambda descriptor: 99
    monkeypatch.setitem(sys.modules, "msvcrt", msvcrt)
    monkeypatch.setattr(ctypes, "WinDLL", lambda *_args, **_kwargs: kernel, raising=False)
    monkeypatch.setattr(time, "sleep", lambda delay: events.append(("sleep", delay)))
    monkeypatch.setattr(os, "read", read)
    assert _entry()["_wait_for_windows_stdin_pipe"]() is True
    assert events[:3] == ["peek", ("sleep", 0.05), "peek"]
    assert events.count("read") == (1 if ending == "broken" else 2)


def test_windows_regular_file_stdin_retains_line_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    import ctypes
    from types import SimpleNamespace

    kernel = SimpleNamespace(GetFileType=_WindowsFunction(lambda _handle: 1))
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(fileno=lambda: 42))
    msvcrt = ModuleType("msvcrt")
    msvcrt.get_osfhandle = lambda _descriptor: 99
    monkeypatch.setitem(sys.modules, "msvcrt", msvcrt)
    monkeypatch.setattr(ctypes, "WinDLL", lambda *_args, **_kwargs: kernel, raising=False)
    assert _entry()["_wait_for_windows_stdin_pipe"]() is False


def test_audio_packaging_is_explicit_and_preserves_lazy_dependencies(tmp_path: Path) -> None:
    command = packaging.pyinstaller_command(
        tmp_path / "entry.py", output_dir=tmp_path / "dist", work_dir=tmp_path / "work"
    )
    hidden = {
        command[index + 1] for index, value in enumerate(command) if value == "--hidden-import"
    }
    collected = {
        command[index + 1] for index, value in enumerate(command) if value == "--collect-all"
    }
    excluded = {
        command[index + 1] for index, value in enumerate(command) if value == "--exclude-module"
    }
    assert hidden == set(packaging.AUDIO_HIDDEN_IMPORTS)
    assert not set(packaging.AUDIO_REQUIRED_PACKAGES) & excluded
    assert "librosa" not in collected and "numba" not in collected
    assert "matplotlib" in excluded and "IPython" in excluded
    assert command[command.index("--collect-data") : command.index("--collect-data") + 2] == [
        "--collect-data",
        "librosa",
    ]
    assert "multiprocessing.freeze_support()" in packaging.entry_source()
    assert "import librosa" not in packaging.entry_source()
    assert command[command.index("--additional-hooks-dir") + 1] == str(tmp_path / "work" / "hooks")
    hook = packaging.audio_hook_source()
    assert '"librosa": "pyz+py"' in hook
    assert '"**/*.pyi"' in hook
    compile(hook, "hook-librosa.py", "exec")


def test_sidecar_bundles_the_attribution_for_derived_midi_reference_data(tmp_path: Path) -> None:
    command = packaging.pyinstaller_command(
        tmp_path / "entry.py", output_dir=tmp_path / "dist", work_dir=tmp_path / "work"
    )
    source = (
        Path(packaging.__file__).resolve().parents[1]
        / "rytm_randomizer/data/MIDI_GUIDE_DATA_NOTICE.txt"
    )
    assert source.is_file()
    assert command[command.index("--add-data") + 1] == (f"{source}:rytm_randomizer/data")
    notice = source.read_text(encoding="utf-8")
    assert "CC-BY-SA-4.0" in notice and "Pencil Research" in notice


@pytest.mark.parametrize("available", (False, True))
def test_pyinstaller_detection_does_not_import_it(
    monkeypatch: pytest.MonkeyPatch, available: bool
) -> None:
    monkeypatch.setattr(
        packaging.importlib.util, "find_spec", lambda _name: object() if available else None
    )
    assert packaging.pyinstaller_available() is available


def test_build_refuses_missing_toolchain_or_audio_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(packaging, "pyinstaller_available", lambda: False)
    with pytest.raises(RuntimeError, match="PyInstaller is not installed"):
        packaging.build(tmp_path / "dist", tmp_path / "work")
    monkeypatch.setattr(packaging, "pyinstaller_available", lambda: True)
    monkeypatch.setattr(packaging.importlib.util, "find_spec", lambda _name: None)
    with pytest.raises(RuntimeError, match="Audio analysis dependencies are not installed"):
        packaging.build(tmp_path / "dist", tmp_path / "work")
    assert not (tmp_path / "work").exists()


@pytest.mark.parametrize("platform", ("win32", "linux"))
def test_build_writes_canonical_entry_and_verifies_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, platform: str
) -> None:
    monkeypatch.setattr(packaging, "pyinstaller_available", lambda: True)
    monkeypatch.setattr(packaging.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(packaging.sys, "platform", platform)
    output = tmp_path / "dist"
    work = tmp_path / "work"
    binary = output / ("rytm-sidecar.exe" if platform == "win32" else "rytm-sidecar")

    def build(command: list[str], *, check: bool, cwd: Path) -> None:
        assert check and cwd == packaging.PROJECT_ROOT
        assert command[-1] == str(work / "rytm_sidecar_entry.py")
        assert (work / "rytm_sidecar_entry.py").read_text("utf-8") == packaging.entry_source()
        assert (work / "hooks" / "hook-librosa.py").read_text(
            "utf-8"
        ) == packaging.audio_hook_source()
        binary.write_bytes(b"test executable")

    monkeypatch.setattr(packaging.subprocess, "run", build)
    assert packaging.build(output, work) == binary
    binary.unlink()
    monkeypatch.setattr(packaging.subprocess, "run", lambda *_args, **_kwargs: None)
    with pytest.raises(RuntimeError, match="reported success"):
        packaging.build(output, work)


def test_build_cli_defaults_arguments_success_and_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    defaults = packaging.parse_args([])
    assert defaults.output_dir == packaging.PROJECT_ROOT / "desktop" / "shell" / "binaries"
    assert defaults.work_dir == packaging.PROJECT_ROOT / "build" / "sidecar-pyinstaller"
    seen: list[tuple[Path, Path]] = []
    monkeypatch.setattr(packaging, "build", lambda output, work: seen.append((output, work)))
    argv = ["--output-dir", str(tmp_path / "dist"), "--work-dir", str(tmp_path / "work")]
    assert packaging.main(argv) == 0
    assert seen == [((tmp_path / "dist").resolve(), (tmp_path / "work").resolve())]

    def fail(*_args: object) -> None:
        raise subprocess.CalledProcessError(1, ["PyInstaller"])

    monkeypatch.setattr(packaging, "build", fail)
    assert packaging.main(argv) == 1


def test_build_script_main_guard_executes_cli_help(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", [str(Path(packaging.__file__)), "--help"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(packaging.__file__, run_name="__main__")
    assert caught.value.code == 0

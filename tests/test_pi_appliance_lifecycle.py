"""Verified deployment bytes and owned process lifecycle on an isolated target facade.

The host is Windows without symlink privilege. Only Linux symlink operations
are represented by private pointer files; archive extraction, release contents,
unit/config files, replacements and preservation checks use real temporary files.
Native commands and browser processes are fakes and cannot modify the host.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import runpy
import signal
import subprocess
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.fast
script = Path(__file__).resolve().parents[1] / "scripts/pi_appliance.py"
spec = importlib.util.spec_from_file_location("pi_lifecycle_cli", script)
assert spec is not None and spec.loader is not None
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class TargetPath(type(Path())):
    """Native temporary paths with an isolated Linux symlink syscall facade."""

    def __str__(self) -> str:
        return super().__str__().replace("\\", "/")

    def is_symlink(self) -> bool:
        if not self.is_file():
            return False
        with self.open("rb") as source:
            return source.read(16) == b"test-linux-link:"

    def symlink_to(self, target: Path, target_is_directory: bool = False) -> None:
        assert target_is_directory
        self.write_text("test-linux-link:" + str(target))

    def resolve(self, strict: bool = False) -> TargetPath:
        if self.is_symlink():
            return TargetPath(self.read_text()[16:]).resolve(strict=strict)
        return super().resolve(strict=strict)


class NativeCommands:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.fail_install = False
        self.fail_check = False

    def __call__(self, command: list[str], **_kwargs: object) -> str:
        self.calls.append(command)
        if command[1:3] == ["-m", "venv"]:
            python = TargetPath(command[3]) / "bin/python"
            python.parent.mkdir(parents=True)
            python.write_text("fake interpreter owned by test")
        elif command[1:4] == ["-m", "pip", "install"] and self.fail_install:
            raise subprocess.CalledProcessError(1, command, stderr="isolated dependency failure")
        elif command[1:4] == ["-m", "pip", "check"] and self.fail_check:
            raise subprocess.CalledProcessError(1, command, output="isolated dependency failure")
        elif command[1:4] == ["-m", "pip", "freeze"]:
            return "mido==1.3.3\npython-rtmidi==1.5.8"
        return ""


@pytest.fixture
def target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[TargetPath, TargetPath, NativeCommands]:
    home = TargetPath(tmp_path / "home")
    home.mkdir()
    prefix = home / "appliance"
    monkeypatch.setattr(cli, "Path", TargetPath)
    monkeypatch.setattr(TargetPath, "home", classmethod(lambda _cls: home))
    monkeypatch.setattr(cli, "supported_target", lambda: True)
    monkeypatch.setattr(cli.os, "getuid", lambda: 1000, raising=False)
    monkeypatch.setattr(cli, "browser_path", lambda: "/usr/bin/chromium")
    monkeypatch.setattr(cli.shutil, "which", lambda _name: "/usr/bin/labwc")
    monkeypatch.setattr(cli.shutil, "disk_usage", lambda _path: SimpleNamespace(free=4 * 1024**3))
    monkeypatch.setattr(cli.platform, "python_version", lambda: "3.11.9")
    commands = NativeCommands()
    monkeypatch.setattr(cli, "checked", commands)
    return home, prefix, commands


def release_archive(
    tmp_path: Path,
    sha: str,
    *,
    wheels: bool = True,
    receipt_patch: dict[str, object] | None = None,
    template_patch: dict[str, bytes] | None = None,
) -> Path:
    files = {
        "src/pyproject.toml": b"verified source fixture",
        "src/rytm_randomizer/cockpit/appliance_runtime.py": b"verified runtime fixture",
        "src/rytm_randomizer/cockpit/ws/handlers.py": b"verified handler fixture",
        "web/index.html": f"<html><head></head><body>{sha}</body></html>".encode(),
        "pi_appliance.py": script.read_bytes(),
    }
    files.update(
        {
            "assets/" + path.name: path.read_bytes()
            for path in cli.ASSETS.iterdir()
            if path.is_file()
        }
    )
    files.update(template_patch or {})
    if wheels:
        files["wheels/fixture.whl"] = b"native wheel fixture; never executed"
        receipt = {
            "source_sha": sha,
            "machine": "aarch64",
            "python": "3.11.9",
            "files": {"fixture.whl": cli.digest(files["wheels/fixture.whl"])},
        }
        receipt.update(receipt_patch or {})
        files["wheels/receipt.json"] = json.dumps(receipt).encode()
    manifest = {
        "format_version": 1,
        "target": "linux-arm64",
        "version": "1.34.0",
        "source_sha": sha,
        "files": {name: cli.digest(data) for name, data in files.items()},
    }
    files["manifest.json"] = json.dumps(manifest).encode()
    path = tmp_path / (sha[:12] + ".tar")
    with tarfile.open(path, "w") as archive:
        for name, data in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    path.with_suffix(".tar.sha256").write_text(cli.digest(path.read_bytes()))
    return path


def test_verified_install_update_idempotency_and_rollback_preserve_user_data(
    target: tuple[TargetPath, TargetPath, NativeCommands], tmp_path: Path
) -> None:
    home, prefix, commands = target
    data = home / ".config/rytm-randomizer/profiles/keep.json"
    data.parent.mkdir(parents=True)
    data.write_text("operator profile and captures remain intact")
    first = release_archive(tmp_path, "a" * 40)
    cli.install(first, prefix=prefix, online=False, autostart=True)
    release_a = prefix / "releases/1.34.0-aaaaaaaaaaaa"
    assert (prefix / "current").resolve() == release_a.resolve()
    assert not (prefix / "previous").exists()
    units = home / ".config/systemd/user"
    assert "@PREFIX@" not in (units / "rytm-appliance-backend.service").read_text()
    assert (
        str(prefix / "current/.venv/bin/python")
        in (units / "rytm-appliance-backend.service").read_text()
    )
    assert (home / ".config/autostart/rytm-appliance.desktop").is_file()
    assert "mido==1.3.3" in (release_a / "installed-requirements.txt").read_text()
    cache = release_a / "src/rytm_randomizer/cockpit/__pycache__/runtime.cpython-311.pyc"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"generated interpreter cache")
    install_command = next(call for call in commands.calls if "install" in call)
    assert "--no-index" in install_command and "--find-links" in install_command
    before = len([call for call in commands.calls if "venv" in call])
    cli.install(first, prefix=prefix, online=False)
    assert len([call for call in commands.calls if "venv" in call]) == before
    assert (prefix / "current").resolve() == release_a.resolve()
    second = release_archive(tmp_path, "b" * 40)
    cli.install(second, prefix=prefix, online=False)
    release_b = prefix / "releases/1.34.0-bbbbbbbbbbbb"
    assert (prefix / "current").resolve() == release_b.resolve()
    assert (prefix / "previous").resolve() == release_a.resolve()
    assert (release_a / "web/index.html").is_file()
    commands.calls.clear()
    cli.rollback(prefix)
    assert (prefix / "current").resolve() == release_a.resolve()
    assert commands.calls[0][1:4] == ["-m", "pip", "check"]
    assert commands.calls[1:] == [
        ["systemctl", "--user", "stop", "rytm-appliance.target"],
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "start", "rytm-appliance.target"],
    ]
    assert data.read_text() == "operator profile and captures remain intact"


@pytest.mark.parametrize("autostart_choice", ["enabled", "never_enabled", "disabled"])
def test_rollback_restores_previous_service_settings_and_keeps_autostart_choice(
    target: tuple[TargetPath, TargetPath, NativeCommands],
    tmp_path: Path,
    autostart_choice: str,
) -> None:
    home, prefix, commands = target

    def templates(restart: int) -> dict[str, bytes]:
        return {
            "assets/rytm-appliance-backend.service": (
                f"[Service]\nRestartSec={restart}\nReadWritePaths=@PREFIX@/runtime-{restart}\n"
            ).encode(),
            "assets/rytm-appliance-kiosk.service": f"[Service]\nRestartSec={restart}\n".encode(),
            "assets/rytm-appliance.target": f"[Unit]\nDescription=Release {restart}\n".encode(),
            "assets/rytm-appliance.desktop": (
                f"[Desktop Entry]\nName=Release {restart}\nExec=@LAUNCHER@ session-start\n"
            ).encode(),
        }

    cli.install(
        release_archive(tmp_path, "a" * 40, template_patch=templates(11)),
        prefix=prefix,
        online=False,
        autostart=autostart_choice != "never_enabled",
    )
    cli.install(
        release_archive(tmp_path, "b" * 40, template_patch=templates(12)),
        prefix=prefix,
        online=False,
    )
    units = home / ".config/systemd/user"
    assert "RestartSec=12" in (units / "rytm-appliance-backend.service").read_text()
    desktop = home / ".config/autostart/rytm-appliance.desktop"
    if autostart_choice == "disabled":
        desktop.unlink()
    elif autostart_choice == "enabled":
        assert "Name=Release 12" in desktop.read_text()
    unrelated = units / "unrelated.service"
    unrelated.write_text("operator-owned unit")
    commands.calls.clear()
    cli.rollback(prefix)
    assert "RestartSec=11" in (units / "rytm-appliance-backend.service").read_text()
    assert str(prefix / "runtime-11") in (units / "rytm-appliance-backend.service").read_text()
    assert "RestartSec=11" in (units / "rytm-appliance-kiosk.service").read_text()
    assert "Description=Release 11" in (units / "rytm-appliance.target").read_text()
    if autostart_choice == "enabled":
        assert "Name=Release 11" in desktop.read_text()
        assert "@LAUNCHER@" not in desktop.read_text()
    else:
        assert not desktop.exists()
    assert unrelated.read_text() == "operator-owned unit"
    assert commands.calls[-2:] == [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "start", "rytm-appliance.target"],
    ]


def test_failed_dependency_update_keeps_current_units_and_previous_release(
    target: tuple[TargetPath, TargetPath, NativeCommands], tmp_path: Path
) -> None:
    home, prefix, commands = target
    cli.install(release_archive(tmp_path, "a" * 40), prefix=prefix, online=False)
    original = (prefix / "current").resolve()
    units = {path.name: path.read_bytes() for path in (home / ".config/systemd/user").iterdir()}
    commands.fail_install = True
    commands.calls.clear()
    with pytest.raises(subprocess.CalledProcessError):
        cli.install(release_archive(tmp_path, "b" * 40), prefix=prefix, online=False)
    assert (prefix / "current").resolve() == original
    assert not (prefix / "releases/1.34.0-bbbbbbbbbbbb").exists()
    assert not list(prefix.glob(".install-*"))
    assert not any(call[0] == "systemctl" for call in commands.calls)
    assert units == {
        path.name: path.read_bytes() for path in (home / ".config/systemd/user").iterdir()
    }


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "tampered",
        "manifest",
        "dependencies",
        "outside",
        "incomplete",
        "path_escape",
        "file_missing",
        "size_limit",
        "invalid_template",
        "omitted_source",
        "added_source",
        "standalone_pyc",
        "metadata_sha",
        "metadata_version",
    ],
)
def test_rollback_refuses_unusable_previous_before_stopping_current(
    target: tuple[TargetPath, TargetPath, NativeCommands],
    tmp_path: Path,
    damage: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, prefix, commands = target
    cli.install(release_archive(tmp_path, "a" * 40), prefix=prefix, online=False)
    cli.install(release_archive(tmp_path, "b" * 40), prefix=prefix, online=False)
    previous, original = (prefix / "previous").resolve(), (prefix / "current").resolve()
    if damage == "missing":
        (prefix / "previous").unlink()
        (prefix / "previous").symlink_to(prefix / "releases/missing", target_is_directory=True)
    elif damage == "tampered":
        (previous / "web/index.html").write_text("changed runtime")
    elif damage == "manifest":
        (previous / "manifest.json").write_text("[]")
    elif damage == "dependencies":
        commands.fail_check = True
    elif damage == "outside":
        (prefix / "previous").unlink()
        (prefix / "previous").symlink_to(TargetPath(tmp_path), target_is_directory=True)
    elif damage == "file_missing":
        (previous / "web/index.html").unlink()
    elif damage == "size_limit":
        monkeypatch.setattr(cli, "MAX_MANIFEST_BYTES", 1)
    elif damage == "invalid_template":
        template = previous / "assets/rytm-appliance-backend.service"
        template.write_bytes(b"\xff")
        manifest = json.loads((previous / "manifest.json").read_text())
        manifest["files"]["assets/rytm-appliance-backend.service"] = cli.digest(b"\xff")
        (previous / "manifest.json").write_text(json.dumps(manifest))
    elif damage == "added_source":
        (previous / "src/rytm_randomizer/cockpit/untracked.py").write_text("changed module")
    elif damage == "standalone_pyc":
        (previous / "src/rytm_randomizer/cockpit/ws/untracked.pyc").write_bytes(
            b"unlisted sourceless import module"
        )
    elif damage in {"omitted_source", "metadata_sha", "metadata_version"}:
        manifest = json.loads((previous / "manifest.json").read_text())
        if damage == "omitted_source":
            manifest["files"].pop("src/rytm_randomizer/cockpit/ws/handlers.py")
            (previous / "src/rytm_randomizer/cockpit/ws/handlers.py").write_text("changed handler")
        elif damage == "metadata_sha":
            manifest["source_sha"] = "f" * 40
        else:
            manifest["version"] = "2.0.0"
        (previous / "manifest.json").write_text(json.dumps(manifest))
    else:
        manifest = json.loads((previous / "manifest.json").read_text())
        if damage == "incomplete":
            manifest["files"] = {}
        else:
            manifest["files"]["../outside"] = "a" * 64
        (previous / "manifest.json").write_text(json.dumps(manifest))
    commands.calls.clear()
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        cli.rollback(prefix)
    assert (prefix / "current").resolve() == original
    assert not any(call[0] == "systemctl" for call in commands.calls)


def test_idempotent_install_refuses_damaged_bytes_and_nonlink_current_before_mutation(
    target: tuple[TargetPath, TargetPath, NativeCommands], tmp_path: Path
) -> None:
    home, prefix, commands = target
    package = release_archive(tmp_path, "a" * 40)
    cli.install(package, prefix=prefix, online=False)
    original = (prefix / "current").resolve()
    (original / "web/index.html").write_text("damaged")
    commands.calls.clear()
    with pytest.raises(ValueError, match="differ"):
        cli.install(package, prefix=prefix, online=False)
    assert commands.calls == []
    units = {path.name: path.read_bytes() for path in (home / ".config/systemd/user").iterdir()}
    (prefix / "current").unlink()
    (prefix / "current").mkdir()
    with pytest.raises(ValueError, match="not a symlink"):
        cli.install(release_archive(tmp_path, "b" * 40), prefix=prefix, online=False)
    assert not (prefix / "releases/1.34.0-bbbbbbbbbbbb").exists()
    assert units == {
        path.name: path.read_bytes() for path in (home / ".config/systemd/user").iterdir()
    }


@pytest.mark.parametrize(
    "receipt_patch", [{"source_sha": "b" * 40}, {"machine": "x86_64"}, {"python": "3.12.1"}]
)
def test_offline_receipt_refused_before_release_publication(
    target: tuple[TargetPath, TargetPath, NativeCommands],
    tmp_path: Path,
    receipt_patch: dict[str, object],
) -> None:
    _, prefix, commands = target
    with pytest.raises(ValueError, match="ABI"):
        cli.install(
            release_archive(tmp_path, "a" * 40, receipt_patch=receipt_patch),
            prefix=prefix,
            online=False,
        )
    assert not (prefix / "current").exists() and commands.calls == []


def test_online_opt_in_and_offline_missing_wheels(
    target: tuple[TargetPath, TargetPath, NativeCommands], tmp_path: Path
) -> None:
    _, prefix, commands = target
    package = release_archive(tmp_path, "a" * 40, wheels=False)
    with pytest.raises(ValueError, match="wheelhouse"):
        cli.install(package, prefix=prefix, online=False)
    assert commands.calls == []
    cli.install(package, prefix=prefix, online=True)
    install_command = next(call for call in commands.calls if "install" in call)
    assert "--no-index" not in install_command
    assert install_command[-1].endswith("/src[cockpit]")


@pytest.mark.parametrize("prerequisite", ["labwc", "disk", "prefix"])
def test_install_prerequisites_refuse_before_user_configuration_is_written(
    target: tuple[TargetPath, TargetPath, NativeCommands],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prerequisite: str,
) -> None:
    home, prefix, commands = target
    if prerequisite == "labwc":
        monkeypatch.setattr(cli.shutil, "which", lambda _name: None)
    elif prerequisite == "disk":
        monkeypatch.setattr(cli.shutil, "disk_usage", lambda _path: SimpleNamespace(free=1))
    else:
        prefix = TargetPath("relative-appliance")
    with pytest.raises(ValueError):
        cli.install(release_archive(tmp_path, "a" * 40), prefix=prefix, online=False)
    assert commands.calls == [] and not (home / ".config").exists()


class BrowserProcess:
    pid = 2468

    def __init__(self, *, stubborn: bool = False) -> None:
        self.returncode: int | None = None
        self.stubborn = stubborn
        self.waits: list[int] = []

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, *, timeout: int) -> int:
        self.waits.append(timeout)
        if self.stubborn and len(self.waits) == 1:
            raise subprocess.TimeoutExpired("owned browser", timeout)
        self.returncode = 0
        return 0


@pytest.mark.parametrize("stubborn", [False, True])
def test_kiosk_rotation_cleans_only_owned_group_then_repeats_new_private_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stubborn: bool
) -> None:
    runtime, profile = tmp_path / "runtime", tmp_path / "browser"
    runtime.mkdir()
    launch = runtime / "launch.html"
    launch.write_text("private credential one")
    processes = [BrowserProcess(stubborn=stubborn), BrowserProcess()]
    launches: list[tuple[list[str], dict[str, object], str]] = []
    killed: list[tuple[int, int]] = []
    monkeypatch.setenv("WAYLAND_DISPLAY", "test-wayland")
    monkeypatch.setattr(cli, "browser_path", lambda: "/usr/bin/chromium")
    monkeypatch.setattr(
        cli.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(b"healthy")
    )
    monkeypatch.setattr(cli.os, "killpg", lambda pid, sig: killed.append((pid, sig)), raising=False)
    monkeypatch.setattr(cli.signal, "SIGKILL", 9, raising=False)

    def popen(command: list[str], **kwargs: object) -> BrowserProcess:
        launches.append((command, kwargs, launch.read_text()))
        return processes[len(launches) - 1]

    def tick(_seconds: float) -> None:
        if len(launches) == 1:
            launch.write_text("private credential two")
        else:
            processes[1].returncode = 0

    monkeypatch.setattr(cli.subprocess, "Popen", popen)
    monkeypatch.setattr(cli.time, "sleep", tick)
    args = argparse.Namespace(runtime_dir=runtime, browser_profile=profile, port=4317)
    cli.kiosk(args)
    cli.kiosk(args)  # The existing service Restart policy invokes a fresh launch.
    assert [text for _, _, text in launches] == ["private credential one", "private credential two"]
    assert killed == [(2468, signal.SIGTERM)] + ([(2468, 9)] if stubborn else [])
    assert processes[0].waits == ([10, 5] if stubborn else [10])
    assert processes[1].waits == []
    for command, options, _ in launches:
        assert options == {"start_new_session": True}
        assert command[-1] == launch.resolve().as_uri()
        assert "--no-sandbox" not in command
        assert "private credential" not in " ".join(command)


def test_kiosk_health_deadline_never_starts_a_browser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WAYLAND_DISPLAY", "test-wayland")
    times = iter([0, 1, 31])
    monkeypatch.setattr(cli.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(cli.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(
        cli.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("not running")),
    )
    monkeypatch.setattr(
        cli.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("browser started")
    )
    with pytest.raises(ValueError, match="30 seconds"):
        cli.kiosk(argparse.Namespace(runtime_dir=tmp_path, port=4317))


def test_kiosk_nonzero_browser_exit_reports_failure_without_killing_unrelated_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "launch.html").write_text("private handoff")
    process = BrowserProcess()
    process.returncode = 7
    monkeypatch.setenv("WAYLAND_DISPLAY", "test-wayland")
    monkeypatch.setattr(cli, "browser_path", lambda: "/usr/bin/chromium")
    monkeypatch.setattr(cli.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO())
    monkeypatch.setattr(cli.subprocess, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(
        cli.os, "killpg", lambda *_args: pytest.fail("unrelated group killed"), raising=False
    )
    with pytest.raises(ValueError, match="code 7"):
        cli.kiosk(
            argparse.Namespace(
                runtime_dir=tmp_path, browser_profile=tmp_path / "browser", port=4317
            )
        )
    assert process.waits == []


@pytest.mark.parametrize("source_state", ["stable", "dirty", "changed"])
def test_wheelhouse_receipt_publishes_only_a_stable_clean_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source_state: str
) -> None:
    directory = tmp_path / "wheels"
    if source_state == "dirty":
        directory.mkdir()
        (directory / "receipt.json").write_text("old receipt")
    calls: list[list[str]] = []
    identities = iter(
        [
            ("/full/git", "a" * 40),
            ("/full/git", "b" * 40 if source_state == "changed" else "a" * 40),
        ]
    )

    def source() -> tuple[str, str]:
        if source_state == "dirty":
            raise ValueError("source is dirty or untracked")
        return next(identities)

    def native(command: list[str], **_kwargs: object) -> str:
        calls.append(command)
        (directory / "project.whl").write_bytes(b"isolated wheel fixture")
        return ""

    monkeypatch.setattr(cli, "committed_source", source)
    monkeypatch.setattr(cli, "supported_target", lambda: True)
    monkeypatch.setattr(cli.platform, "machine", lambda: "aarch64")
    monkeypatch.setattr(cli, "checked", native)
    if source_state == "stable":
        cli.main(["wheelhouse", "--wheelhouse", str(directory)])
        receipt = json.loads((directory / "receipt.json").read_text())
        assert receipt["source_sha"] == "a" * 40
        assert receipt["files"] == {"project.whl": cli.digest(b"isolated wheel fixture")}
        assert receipt["machine"] == "aarch64"
        assert len(calls) == 1 and calls[0][1:4] == ["-m", "pip", "wheel"]
    else:
        with pytest.raises(SystemExit) as error:
            cli.main(["wheelhouse", "--wheelhouse", str(directory)])
        assert error.value.code == 1
        if source_state == "dirty":
            assert calls == [] and (directory / "receipt.json").read_text() == "old receipt"
        else:
            assert len(calls) == 1 and not (directory / "receipt.json").exists()


def test_wheelhouse_refuses_to_certify_preexisting_wheels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "reused-wheels"
    directory.mkdir()
    stale = directory / "rytm_randomizer-1.34.0-99-py3-none-any.whl"
    stale.write_bytes(b"stale project wheel from another source")
    calls: list[list[str]] = []
    monkeypatch.setattr(cli, "committed_source", lambda: ("/full/git", "a" * 40))
    monkeypatch.setattr(cli, "checked", lambda command, **_kwargs: calls.append(command) or "")
    with pytest.raises(ValueError, match="fresh directory"):
        cli.build_wheelhouse(directory)
    assert calls == [] and not (directory / "receipt.json").exists()
    assert stale.read_bytes() == b"stale project wheel from another source"


@pytest.mark.parametrize(
    ("platform_name", "machine", "codename", "expected"),
    [
        ("linux", "aarch64", "bookworm", True),
        ("linux", "arm64", "trixie", True),
        ("linux", "aarch64", "future", False),
        ("linux", "x86_64", "bookworm", False),
        ("win32", "arm64", "trixie", False),
    ],
)
def test_supported_os_detection_reads_only_known_target_configuration(
    monkeypatch: pytest.MonkeyPatch, platform_name: str, machine: str, codename: str, expected: bool
) -> None:
    class ReleasePath(type(Path())):
        def read_text(self, **_kwargs: object) -> str:
            assert str(self).replace("\\", "/").endswith("/etc/os-release")
            return f'VERSION_CODENAME="{codename}"\n'

    monkeypatch.setattr(cli, "Path", ReleasePath)
    monkeypatch.setattr(cli.sys, "platform", platform_name)
    monkeypatch.setattr(cli.platform, "machine", lambda: machine)
    assert cli.supported_target() is expected


@pytest.mark.parametrize("healthy", [False, True])
def test_diagnostics_reports_actual_check_results_without_physical_claims(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, healthy: bool
) -> None:
    monkeypatch.setattr(cli, "supported_target", lambda: True)
    monkeypatch.setattr(cli.shutil, "disk_usage", lambda _path: SimpleNamespace(free=123456))
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/usr/bin/" + name)

    def health(*_args: object, **_kwargs: object) -> io.BytesIO:
        if not healthy:
            raise OSError("offline")
        return io.BytesIO(b'{"status":"passive"}')

    def dependencies(command: list[str], **_kwargs: object) -> str:
        if not healthy:
            raise subprocess.CalledProcessError(
                1, command, output="conflicting installed dependency"
            )
        return "No broken requirements found."

    monkeypatch.setattr(cli.urllib.request, "urlopen", health)
    monkeypatch.setattr(cli, "checked", dependencies)
    result = cli.diagnose(port=4317)
    assert result["physical_validation"] is False
    assert result["free_disk_bytes"] == 123456
    if healthy:
        assert result["backend"] == {"status": "passive"}
        assert result["dependencies"] == "No broken requirements found."
    else:
        assert result["backend"] == "unavailable; start the appliance backend"
        assert result["dependencies"] == "conflicting installed dependency"


def test_browser_package_fallback_and_missing_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli.shutil,
        "which",
        lambda name: "/usr/bin/chromium-browser" if name == "chromium-browser" else None,
    )
    assert cli.browser_path() == "/usr/bin/chromium-browser"
    monkeypatch.setattr(cli.shutil, "which", lambda _name: None)
    with pytest.raises(ValueError, match="Chromium missing"):
        cli.browser_path()


@pytest.mark.parametrize(
    "command",
    [
        "build",
        "package",
        "install",
        "serve",
        "kiosk",
        "diagnose",
        "rollback",
        "uninstall",
        "session-start",
    ],
)
def test_command_line_routes_explicit_operator_actions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    seen: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
    for name in ("build", "package", "install", "serve", "kiosk", "rollback", "uninstall"):

        def fake(*args: object, action: str = name, **kwargs: object) -> None:
            seen.append((action, args, kwargs))

        monkeypatch.setattr(cli, name, fake)
    monkeypatch.setattr(cli, "diagnose", lambda **kwargs: {"physical_validation": False, **kwargs})
    system: list[list[str]] = []
    monkeypatch.setattr(cli, "checked", lambda command, **_kwargs: system.append(command) or "")
    argv = [
        command,
        "--port",
        "4319",
        "--prefix",
        str(tmp_path),
        "--output",
        str(tmp_path / "package.tar"),
    ]
    if command == "install":
        argv += ["--archive", str(tmp_path / "verified.tar"), "--online", "--autostart"]
    cli.main(argv)
    if command == "diagnose":
        assert json.loads(capsys.readouterr().out) == {"physical_validation": False, "port": 4319}
    elif command == "session-start":
        assert system == [
            [
                "systemctl",
                "--user",
                "import-environment",
                "WAYLAND_DISPLAY",
                "DISPLAY",
                "XDG_CURRENT_DESKTOP",
            ],
            ["systemctl", "--user", "restart", "rytm-appliance.target"],
        ]
    else:
        assert len(seen) == 1 and seen[0][0] == command
        if command == "install":
            assert seen[0][2]["online"] is True and seen[0][2]["autostart"] is True
        if command in {"serve", "kiosk"}:
            assert seen[0][1][0].port == 4319


@pytest.mark.parametrize("argv", [["serve", "--port", "1"], ["install"], ["wheelhouse"]])
def test_command_line_refuses_missing_or_unsafe_arguments(
    argv: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "supported_target", lambda: False)
    with pytest.raises(SystemExit) as error:
        cli.main(argv)
    assert error.value.code == 2


def test_real_stdio_helper_and_script_help_have_no_external_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (
        cli.checked([sys.executable, "-c", "print('verified subprocess stdio')"])
        == "verified subprocess stdio"
    )
    monkeypatch.setattr(sys, "argv", [str(script), "--help"])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(script), run_name="__main__")
    assert error.value.code == 0


def test_stdio_capture_uses_utf8_independently_of_windows_locale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def command(_command: list[str], **kwargs: object) -> SimpleNamespace:
        seen.update(kwargs)
        return SimpleNamespace(stdout="Unicode dependency tree: \u2514\u2500\u2500\n")

    monkeypatch.setattr(cli.subprocess, "run", command)
    assert cli.checked(["/full/npm", "run", "build"]).endswith("\u2514\u2500\u2500")
    assert seen["encoding"] == "utf-8" and seen["errors"] == "replace"

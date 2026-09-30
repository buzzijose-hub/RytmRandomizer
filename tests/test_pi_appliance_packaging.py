"""Deployment checks operate on private fixtures and mocked Linux services."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast
script_path = Path(__file__).resolve().parents[1] / "scripts/pi_appliance.py"
spec = importlib.util.spec_from_file_location("pi_appliance_test_cli", script_path)
assert spec is not None and spec.loader is not None
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def archive(
    tmp_path: Path, files: dict[str, bytes], *, manifest: dict[str, object] | None = None
) -> Path:
    metadata = manifest or {
        "format_version": 1,
        "target": "linux-arm64",
        "source_sha": "a" * 40,
        "version": "1.34.0",
        "files": {name: cli.digest(data) for name, data in files.items()},
    }
    entries = {**files, "manifest.json": json.dumps(metadata).encode()}
    path = tmp_path / "fixture.tar"
    with tarfile.open(path, "w") as bundle:
        for name, data in entries.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            bundle.addfile(member, io.BytesIO(data))
    path.with_suffix(".tar.sha256").write_text(cli.digest(path.read_bytes()))
    return path


def test_manifest_verified_round_trip(tmp_path: Path) -> None:
    source = archive(tmp_path, {"web/index.html": b"production", "src/VERSION": b"1.34.0"})
    metadata = cli.unpack_verified(source, tmp_path / "unpacked")
    assert metadata["source_sha"] == "a" * 40
    assert (tmp_path / "unpacked/web/index.html").read_bytes() == b"production"


@pytest.mark.parametrize("name", ["../outside", "/absolute", "a\\outside"])
def test_archive_traversal_refused_before_any_publication(tmp_path: Path, name: str) -> None:
    source = archive(tmp_path, {name: b"hostile"})
    destination = tmp_path / "unpacked"
    with pytest.raises(ValueError, match="Unsafe"):
        cli.unpack_verified(source, destination)
    assert not destination.exists()
    assert not (tmp_path / "outside").exists()


def test_manifest_hash_mismatch_and_transfer_corruption(tmp_path: Path) -> None:
    source = archive(
        tmp_path,
        {"file": b"data"},
        manifest={
            "format_version": 1,
            "target": "linux-arm64",
            "source_sha": "a" * 40,
            "files": {},
        },
    )
    with pytest.raises(ValueError, match="manifest"):
        cli.unpack_verified(source, tmp_path / "unpacked")
    source.write_bytes(source.read_bytes() + b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        cli.unpack_verified(source, tmp_path / "unpacked")


def test_oversized_archive_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = archive(tmp_path, {"file": b"data"})
    monkeypatch.setattr(cli, "MAX_PACKAGE_BYTES", 1)
    with pytest.raises(ValueError, match="size limit"):
        cli.unpack_verified(source, tmp_path / "unpacked")


def test_log_rotation_is_private_and_bounded(tmp_path: Path) -> None:
    path = tmp_path / "log/backend.log"
    stream = cli.RotatingOutput(path)
    stream.handler.maxBytes = 50
    for index in range(12):
        assert stream.write(f"record-{index} {'x' * 25}\n") > 0
    stream.flush()
    stream.close()
    logs = sorted(path.parent.glob("backend.log*"))
    assert len(logs) == 4
    assert "record-11" in path.read_text()
    assert all(log.stat().st_size < 100 for log in logs)


def test_host_install_refused_without_arm64_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "supported_target", lambda: False)
    with pytest.raises(ValueError, match="ARM64"):
        cli.install(tmp_path / "absent.tar", prefix=tmp_path / "install", online=False)
    assert not (tmp_path / "install").exists()


def test_serve_default_never_enters_hardware_boundary_and_removes_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from rytm_randomizer.cockpit import __main__ as sidecar

    observed: list[str] = []

    def passive() -> None:
        observed.append(cli.os.environ["RYTM_RAND_MIDI_BACKEND"])
        assert cli.os.environ["RYTM_RAND_APPLIANCE_SIMULATION"] == "1"
        for name in ("ws-token", "arm-secret", "launch.html"):
            (tmp_path / name).write_text("transient")

    monkeypatch.setattr(sidecar, "run", passive)
    monkeypatch.setattr(cli.os, "environ", dict(cli.os.environ))
    args = argparse.Namespace(
        runtime_dir=tmp_path,
        web_root=tmp_path,
        port=4317,
        hardware_input=False,
        simulation=True,
        log_file=None,
    )
    cli.serve(args)
    assert observed == ["off"]
    assert not list(tmp_path.iterdir())


def test_serve_refuses_mixed_hardware_simulation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli.os, "environ", dict(cli.os.environ))
    args = argparse.Namespace(
        runtime_dir=tmp_path,
        web_root=tmp_path,
        port=4317,
        hardware_input=True,
        simulation=True,
        log_file=None,
    )
    with pytest.raises(ValueError, match="separate"):
        cli.serve(args)


def test_kiosk_missing_graphical_session_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    with pytest.raises(ValueError, match="Wayland graphical session"):
        cli.kiosk(argparse.Namespace(runtime_dir=tmp_path))


def test_uninstall_preserves_every_user_data_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    units = tmp_path / ".config/systemd/user"
    units.mkdir(parents=True)
    for name in (
        "rytm-appliance-backend.service",
        "rytm-appliance-kiosk.service",
        "rytm-appliance.target",
        "unrelated.service",
    ):
        (units / name).write_text("fixture")
    data = tmp_path / ".config/rytm-randomizer/profiles/keep.json"
    data.parent.mkdir(parents=True)
    data.write_text("preserve")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    commands: list[list[str]] = []
    monkeypatch.setattr(cli, "checked", lambda command, **_: commands.append(command) or "")
    cli.uninstall()
    assert data.read_text() == "preserve"
    assert (units / "unrelated.service").exists()
    assert not (units / "rytm-appliance.target").exists()
    assert commands[0] == ["systemctl", "--user", "stop", "rytm-appliance.target"]


def test_versioned_service_assets_preserve_supervision_and_output_boundary() -> None:
    backend = (cli.ASSETS / "rytm-appliance-backend.service").read_text()
    kiosk = (cli.ASSETS / "rytm-appliance-kiosk.service").read_text()
    assert "StartLimitBurst=5" in backend and "StartLimitBurst=5" in kiosk
    assert "RestartSec=10" in backend and "RestartSec=10" in kiosk
    assert "KillSignal=SIGTERM" in backend and "TimeoutStopSec=15" in backend
    assert "--hardware-input" not in backend and "--simulation" not in backend
    assert "--no-sandbox" not in kiosk
    assert "--log-file" in backend and "UMask=0077" in backend

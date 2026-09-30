"""Deployment checks operate on private fixtures and mocked Linux services."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from types import ModuleType, SimpleNamespace

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


def test_passive_serve_activates_backend_decision_logging_into_private_rotating_sink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import logging

    from fastapi.testclient import TestClient

    from rytm_randomizer.cockpit import __main__ as sidecar
    from rytm_randomizer.cockpit.ws.server import create_app

    web, runtime = tmp_path / "web", tmp_path / "runtime"
    web.mkdir()
    (web / "index.html").write_text("<html><head></head><body>production</body></html>")
    secrets = ["private-ws-token", "private-arm-token"]
    original_handlers = list(logging.getLogger("rytm_randomizer").handlers)

    def passive() -> None:
        session = sidecar.build_session()
        session.arm_secret = secrets[1]
        app = create_app(session, token=secrets[0])
        text = (runtime / "launch.html").read_text()
        secrets.append(text.split('name="credential" value="')[1].split('"')[0])
        with TestClient(app, base_url="http://127.0.0.1:4317") as client:
            assert client.get("/appliance").status_code == 403

    monkeypatch.setattr(sidecar, "run", passive)
    monkeypatch.setattr(cli.os, "environ", dict(cli.os.environ))
    log = tmp_path / "logs/backend.log"
    cli.serve(
        argparse.Namespace(
            runtime_dir=runtime,
            web_root=web,
            port=4317,
            hardware_input=False,
            simulation=False,
            log_file=log,
        )
    )
    text = log.read_text()
    records = [json.loads(line) for line in text.splitlines()]
    refusals = [record for record in records if record.get("message") == "appliance_auth_refused"]
    assert len(refusals) == 1
    assert refusals[0]["fingerprint"] == "appliance_auth.session"
    assert refusals[0]["transport"] == "http"
    assert all(secret not in text for secret in secrets)
    assert logging.getLogger("rytm_randomizer").handlers == original_handlers


def test_packaged_launcher_binds_its_source_before_foreign_editable_install(tmp_path: Path) -> None:
    release = tmp_path / "release"
    package = release / "src/rytm_randomizer"
    (package / "cockpit").mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "cockpit/__init__.py").write_text("")
    (package / "observability").mkdir()
    (package / "observability/__init__.py").write_text("")
    (package / "observability/logging.py").write_text(
        "def configure_logging(**kwargs):\n    pass\n"
    )
    marker = tmp_path / "source.txt"
    (package / "cockpit/__main__.py").write_text(
        "from pathlib import Path\n"
        "import os\n"
        "def run():\n"
        "    Path(os.environ['TEST_SOURCE_MARKER']).write_text(__file__)\n"
    )
    (release / "pi_appliance.py").write_bytes(script_path.read_bytes())
    foreign = tmp_path / "foreign/rytm_randomizer"
    foreign.mkdir(parents=True)
    (foreign / "__init__.py").write_text("raise RuntimeError('foreign source imported')\n")
    env = {**os.environ, "PYTHONPATH": str(foreign.parent), "TEST_SOURCE_MARKER": str(marker)}
    subprocess.run(
        [
            sys.executable,
            str(release / "pi_appliance.py"),
            "serve",
            "--simulation",
            "--runtime-dir",
            str(tmp_path / "runtime"),
            "--web-root",
            str(tmp_path / "web"),
        ],
        check=True,
        env=env,
        cwd=tmp_path,
        capture_output=True,
        timeout=10,
    )
    assert Path(marker.read_text()) == package / "cockpit/__main__.py"


def test_loaded_foreign_source_is_refused_without_replacing_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    foreign = ModuleType("rytm_randomizer")
    foreign.__file__ = str(tmp_path / "foreign/rytm_randomizer/__init__.py")
    monkeypatch.setitem(sys.modules, "rytm_randomizer", foreign)
    with pytest.raises(ValueError, match="fresh process"):
        cli.bind_runtime_source()
    assert sys.modules["rytm_randomizer"] is foreign


def test_packaging_missing_git_is_actionable_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli.shutil, "which", lambda _name: None)
    with pytest.raises(ValueError, match="Git is required"):
        cli.package(tmp_path / "artifact.tar", web_root=tmp_path, wheelhouse=None)
    assert not (tmp_path / "artifact.tar").exists()


def test_source_identity_refuses_untracked_frontend_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli.shutil, "which", lambda _name: "/full/git")
    monkeypatch.setattr(
        cli,
        "checked",
        lambda command, **_kwargs: (
            "?? desktop/web/public/untracked.png" if command[1] == "status" else ""
        ),
    )
    with pytest.raises(ValueError, match="untracked files"):
        cli.committed_source()


def web_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    web = tmp_path / "desktop/web"
    web.mkdir(parents=True)
    (web / "package-lock.json").write_text('{"lockfileVersion":3,"packages":{}}')
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "committed_source", lambda: ("/full/git", "a" * 40))
    monkeypatch.setattr(cli.shutil, "which", lambda _name: "/full/npm")
    return web


def fake_web_build(command: list[str], *, cwd: Path, **_kwargs: object) -> str:
    assert command == ["/full/npm", "run", "build"]
    (cwd / "dist/assets").mkdir(parents=True, exist_ok=True)
    (cwd / "dist/index.html").write_text('<script src="/assets/app.js"></script>')
    (cwd / "dist/assets/app.js").write_text("console.log('shared fixture')")
    return ""


def test_build_writes_exact_receipt_only_after_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web = web_project(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, "checked", fake_web_build)
    cli.build()
    receipt = json.loads((web / "dist" / cli.WEB_BUILD_RECEIPT).read_text())
    assert receipt["source_sha"] == "a" * 40
    assert receipt["package_lock_sha256"] == cli.digest((web / "package-lock.json").read_bytes())
    assert set(receipt["files"]) == {"index.html", "assets/app.js"}
    cli.verify_web_receipt(web / "dist", "a" * 40)


@pytest.mark.parametrize("mismatch", ["source", "lock", "asset", "extra", "missing", "schema"])
def test_package_refuses_stale_or_tampered_web_receipt_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mismatch: str
) -> None:
    web = web_project(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, "checked", fake_web_build)
    cli.build()
    receipt_path = web / "dist" / cli.WEB_BUILD_RECEIPT
    if mismatch == "source":
        monkeypatch.setattr(cli, "committed_source", lambda: ("/full/git", "b" * 40))
    elif mismatch == "lock":
        (web / "package-lock.json").write_text('{"packages":{},"changed":true}')
    elif mismatch == "asset":
        (web / "dist/assets/app.js").write_text("tampered")
    elif mismatch == "extra":
        (web / "dist/extra.js").write_text("not in receipt")
    elif mismatch == "missing":
        receipt_path.unlink()
    else:
        receipt = json.loads(receipt_path.read_text())
        receipt["format_version"] = 2
        receipt_path.write_text(json.dumps(receipt))
    output = tmp_path / "artifact.tar"
    with pytest.raises(ValueError, match="receipt"):
        cli.package(output, web_root=web / "dist", wheelhouse=None)
    assert not output.exists() and not output.with_suffix(".tar.sha256").exists()


def test_build_dependency_mismatch_and_source_change_leave_no_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web = web_project(tmp_path, monkeypatch)
    (web / "package-lock.json").write_text(
        '{"packages":{"node_modules/example":{"version":"1.2.3"}}}'
    )
    with pytest.raises(ValueError, match="npm ci"):
        cli.build()
    installed = web / "node_modules/example/package.json"
    installed.parent.mkdir(parents=True)
    installed.write_text('{"version":"1.2.4"}')
    with pytest.raises(ValueError, match="npm ci"):
        cli.build()
    installed.write_text('{"version":"1.2.3"}')
    monkeypatch.setattr(cli, "checked", fake_web_build)
    identities = iter([("/full/git", "a" * 40), ("/full/git", "b" * 40)])
    monkeypatch.setattr(cli, "committed_source", lambda: next(identities))
    with pytest.raises(ValueError, match="changed during build"):
        cli.build()
    assert not (web / "dist" / cli.WEB_BUILD_RECEIPT).exists()


def test_receipt_size_bound_and_nested_receipt_asset_are_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web = web_project(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, "checked", fake_web_build)
    cli.build()
    nested = web / "dist/assets" / cli.WEB_BUILD_RECEIPT
    nested.write_text("unrecorded asset with a reserved basename")
    with pytest.raises(ValueError, match="receipt"):
        cli.verify_web_receipt(web / "dist", "a" * 40)
    monkeypatch.setattr(cli, "MAX_RECEIPT_BYTES", 1)
    with pytest.raises(ValueError, match="oversized"):
        cli.verify_web_receipt(web / "dist", "a" * 40)


def test_valid_build_receipt_is_included_in_verified_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    web = web_project(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, "checked", fake_web_build)
    cli.build()
    (tmp_path / "VERSION").write_text("1.34.0")
    assets = tmp_path / "service-assets"
    assets.mkdir()
    (assets / "fixture.service").write_text("fixture")
    monkeypatch.setattr(cli, "ASSETS", assets)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as source:
        member = tarfile.TarInfo("pyproject.toml")
        member.size = 7
        source.addfile(member, io.BytesIO(b"fixture"))
    monkeypatch.setattr(
        cli.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(stdout=buffer.getvalue())
    )
    output = tmp_path / "artifact.tar"
    cli.package(output, web_root=web / "dist", wheelhouse=None)
    metadata = cli.unpack_verified(output, tmp_path / "verified")
    assert metadata["source_sha"] == "a" * 40
    assert "web/" + cli.WEB_BUILD_RECEIPT in metadata["files"]
    assert (tmp_path / "verified/web/assets/app.js").read_bytes() == (
        web / "dist/assets/app.js"
    ).read_bytes()


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

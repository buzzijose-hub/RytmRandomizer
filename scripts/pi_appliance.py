"""Build, install, supervise and diagnose the shared Cockpit Pi presentation.

No command changes firmware, boot configuration, groups, GPIO pins or MIDI
permissions. Installation is per-user; source packages and dependencies are
verified before the active release pointer changes. Runtime launch uses the
existing passive Cockpit or the explicitly selected app --arm capture seam.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path, PurePosixPath
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
ASSETS: Final[Path] = ROOT / "installer-assets" / "pi-appliance"
DEFAULT_PORT: Final[int] = 4317
MAX_PACKAGE_BYTES: Final[int] = 512 * 1024 * 1024
MAX_PACKAGE_FILES: Final[int] = 12000
WEB_BUILD_RECEIPT: Final[str] = "web-build-receipt.json"
MAX_RECEIPT_BYTES: Final[int] = 256 * 1024


class RotatingOutput(io.TextIOBase):
    """Private bounded stderr/stdout destination using stdlib rotation."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.handler = RotatingFileHandler(
            path, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        path.chmod(0o600)

    def write(self, text: str) -> int:
        for line in text.splitlines():
            if line:
                self.handler.emit(
                    logging.LogRecord("appliance", logging.INFO, "", 0, line[:4096], (), None)
                )
        return len(text)

    def flush(self) -> None:
        self.handler.flush()

    def close(self) -> None:
        self.handler.close()
        super().close()


def checked(command: list[str], *, cwd: Path | None = None, timeout: int = 300) -> str:
    return subprocess.run(
        command, cwd=cwd, check=True, capture_output=True, text=True, timeout=timeout
    ).stdout.strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def committed_source() -> tuple[str, str]:
    """Resolve exact clean HEAD before assigning any artifact source identity."""
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git is required to package exact committed source; install Git first")
    checked([git, "diff", "--exit-code", "HEAD"], cwd=ROOT)
    if checked(
        [git, "status", "--porcelain", "--untracked-files=all", "--", "desktop/web"], cwd=ROOT
    ):
        raise ValueError(
            "Frontend source has uncommitted or untracked files; commit it before building"
        )
    source_sha = checked([git, "rev-parse", "HEAD"], cwd=ROOT)
    return git, source_sha


def web_inventory(web_root: Path) -> dict[str, str]:
    """Hash every bounded regular web asset except the build receipt itself."""
    if not (web_root / "index.html").is_file():
        raise ValueError("Production assets missing: run the appliance build command")
    files: dict[str, str] = {}
    total = 0
    for path in sorted(web_root.rglob("*")):
        if not path.is_file() or path == web_root / WEB_BUILD_RECEIPT:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(web_root.resolve()):
            raise ValueError("Production assets must be contained regular files")
        total += path.stat().st_size
        if total > MAX_PACKAGE_BYTES or len(files) >= MAX_PACKAGE_FILES:
            raise ValueError("Production assets exceed appliance size limits")
        files[path.relative_to(web_root).as_posix()] = digest(path.read_bytes())
    return files


def verify_locked_dependencies(web: Path) -> None:
    """Refuse installed dependency versions that differ from the existing npm lock."""
    lock = json.loads((web / "package-lock.json").read_text())
    packages = lock.get("packages") if isinstance(lock, dict) else None
    if not isinstance(packages, dict):
        raise ValueError("A packages-based npm lockfile is required; run npm ci in desktop/web")
    for name, package in packages.items():
        if not name:
            continue
        if (
            not isinstance(name, str)
            or not name.startswith("node_modules/")
            or ".." in PurePosixPath(name).parts
            or not isinstance(package, dict)
            or not isinstance(package.get("version"), str)
        ):
            raise ValueError("Unsupported npm lockfile entry; run npm ci in desktop/web")
        installed = web / name / "package.json"
        if not installed.is_file() and package.get("optional") is True:
            continue
        if (
            not installed.is_file()
            or json.loads(installed.read_text()).get("version") != package["version"]
        ):
            raise ValueError(
                "Installed frontend dependencies differ from lockfile; run npm ci in desktop/web"
            )


def build() -> None:
    """Build the shared production frontend and bind its exact output to clean HEAD."""
    _, source_sha = committed_source()
    web = ROOT / "desktop/web"
    receipt_path = web / "dist" / WEB_BUILD_RECEIPT
    receipt_path.unlink(missing_ok=True)
    verify_locked_dependencies(web)
    npm = shutil.which("npm")
    if npm is None:
        raise ValueError("npm is required to build the shared production frontend")
    lock_sha = digest((web / "package-lock.json").read_bytes())
    checked([npm, "run", "build"], cwd=web, timeout=300)
    if committed_source()[1] != source_sha:
        raise ValueError("Committed source changed during build; rebuild the final commit")
    if digest((web / "package-lock.json").read_bytes()) != lock_sha:
        raise ValueError("Frontend lockfile changed during build; rebuild the final lockfile")
    receipt = {
        "format_version": 1,
        "source_sha": source_sha,
        "package_lock_sha256": lock_sha,
        "files": web_inventory(web / "dist"),
    }
    data = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    if len(data) > MAX_RECEIPT_BYTES:
        raise ValueError("Web build receipt exceeds the size limit")
    receipt_path.write_bytes(data)
    print(json.dumps({"source_sha": source_sha, "web_build_receipt": str(receipt_path)}))


def verify_web_receipt(web_root: Path, source_sha: str) -> None:
    """Refuse stale or altered production output before packaging publishes bytes."""
    path = web_root / WEB_BUILD_RECEIPT
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_RECEIPT_BYTES:
        raise ValueError("Missing or oversized web build receipt; run the appliance build command")
    receipt = json.loads(path.read_bytes())
    if (
        not isinstance(receipt, dict)
        or receipt.get("format_version") != 1
        or receipt.get("source_sha") != source_sha
        or receipt.get("package_lock_sha256")
        != digest((ROOT / "desktop/web/package-lock.json").read_bytes())
        or receipt.get("files") != web_inventory(web_root)
    ):
        raise ValueError("Production web build receipt does not match this source/assets; rebuild")


def package(output: Path, *, web_root: Path, wheelhouse: Path | None) -> None:
    """Deterministic archive of exact committed source + verified web + optional wheels."""
    git, source_sha = committed_source()
    verify_web_receipt(web_root, source_sha)
    files: dict[str, bytes] = {}
    source_tar = subprocess.run(
        [
            git,
            "archive",
            "--format=tar",
            "HEAD",
            "rytm_randomizer",
            "pyproject.toml",
            "VERSION",
            "README.md",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(source_tar)) as archive:
        for member in archive.getmembers():
            if member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError("Committed source archive contains an unreadable file")
                files[f"src/{member.name}"] = stream.read()
    for prefix, directory in (("web", web_root), ("assets", ASSETS)):
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                if path.is_symlink():
                    raise ValueError("Package assets must be regular files")
                files[f"{prefix}/{path.relative_to(directory).as_posix()}"] = path.read_bytes()
    files["pi_appliance.py"] = Path(__file__).read_bytes()
    if wheelhouse is not None:
        receipt = json.loads((wheelhouse / "receipt.json").read_text())
        if receipt.get("source_sha") != source_sha or receipt.get("machine") not in {
            "aarch64",
            "arm64",
        }:
            raise ValueError("Wheelhouse must have an exact-source ARM64 receipt")
        for path in sorted(wheelhouse.glob("*.whl")):
            if receipt.get("files", {}).get(path.name) != digest(path.read_bytes()):
                raise ValueError("Wheelhouse checksum mismatch")
            files[f"wheels/{path.name}"] = path.read_bytes()
        files["wheels/receipt.json"] = (wheelhouse / "receipt.json").read_bytes()
    manifest = {
        "format_version": 1,
        "source_sha": source_sha,
        "target": "linux-arm64",
        "version": (ROOT / "VERSION").read_text().strip(),
        "presentation": "shared-react-chromium-wayland",
        "physical_validation": False,
        "files": {name: digest(data) for name, data in sorted(files.items())},
    }
    files["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, mode="w") as archive:
        for name, data in sorted(files.items()):
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mode = 0o644
            member.mtime = 0
            archive.addfile(member, io.BytesIO(data))
    output.with_suffix(output.suffix + ".sha256").write_text(digest(output.read_bytes()) + "\n")
    print(json.dumps({"package": str(output), "source_sha": source_sha, "files": len(files)}))


def unpack_verified(archive_path: Path, destination: Path) -> dict[str, object]:
    """Bounded regular-file extraction; manifest must cover every byte-bearing file."""
    if archive_path.stat().st_size > MAX_PACKAGE_BYTES:
        raise ValueError("Appliance package exceeds the size limit")
    data = archive_path.read_bytes()
    expected = archive_path.with_suffix(archive_path.suffix + ".sha256").read_text().strip()
    if not re.fullmatch(r"[a-f0-9]{64}", expected) or digest(data) != expected:
        raise ValueError("Package checksum mismatch; transfer the matching .sha256 file")
    entries: dict[str, bytes] = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            total += member.size
            if (
                not member.isfile()
                or path.is_absolute()
                or ".." in path.parts
                or "\\" in member.name
                or ":" in member.name
                or member.name in entries
                or len(entries) >= MAX_PACKAGE_FILES
                or total > MAX_PACKAGE_BYTES
            ):
                raise ValueError("Unsafe or oversized appliance archive")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("Appliance archive contains an unreadable file")
            entries[member.name] = stream.read()
    if "manifest.json" not in entries:
        raise ValueError("Appliance package manifest is missing")
    manifest = json.loads(entries.pop("manifest.json"))
    if (
        not isinstance(manifest, dict)
        or manifest.get("format_version") != 1
        or manifest.get("target") != "linux-arm64"
    ):
        raise ValueError("Unsupported appliance package format or target")
    actual = {name: digest(content) for name, content in entries.items()}
    sha = manifest.get("source_sha")
    if (
        manifest.get("files") != actual
        or not isinstance(sha, str)
        or not re.fullmatch(r"[a-f0-9]{40}", sha)
    ):
        raise ValueError("Package manifest does not match its contents")
    for name, content in entries.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def supported_target() -> bool:
    if sys.platform != "linux" or platform.machine() not in {"aarch64", "arm64"}:
        return False
    release = Path("/etc/os-release").read_text()
    return bool(re.search(r'^VERSION_CODENAME=(?:"?)(bookworm|trixie)(?:"?)$', release, re.M))


def browser_path() -> str:
    selected = shutil.which("chromium") or shutil.which("chromium-browser")
    if selected is None:
        raise ValueError("Chromium missing: install the supported OS chromium package")
    return selected


def diagnose(*, port: int) -> dict[str, object]:
    report: dict[str, object] = {
        "python": platform.python_version(),
        "machine": platform.machine(),
        "platform": sys.platform,
        "supported_arm64_os": supported_target(),
        "chromium": shutil.which("chromium") or shutil.which("chromium-browser"),
        "labwc": shutil.which("labwc"),
        "wayland_session": bool(os.environ.get("WAYLAND_DISPLAY")),
        "free_disk_bytes": shutil.disk_usage(Path.home()).free,
        "physical_validation": False,
    }
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
            report["backend"] = json.load(response)
    except (OSError, urllib.error.URLError, ValueError):
        report["backend"] = "unavailable; start the appliance backend"
    try:
        report["dependencies"] = checked([sys.executable, "-m", "pip", "check"], timeout=30)
    except subprocess.CalledProcessError as exc:
        report["dependencies"] = exc.stdout.strip() or "dependency check failed"
    return report


def _service_paths(prefix: Path) -> dict[str, str]:
    current = prefix / "current"
    return {
        "@PREFIX@": str(prefix),
        "@PYTHON@": str(current / ".venv/bin/python"),
        "@LAUNCHER@": str(current / "pi_appliance.py"),
    }


def install(archive: Path, *, prefix: Path, online: bool, autostart: bool = False) -> None:
    if not supported_target() or os.getuid() == 0:
        raise ValueError("Install as the graphical-session user on ARM64 Bookworm/Trixie")
    browser_path()
    if not shutil.which("labwc"):
        raise ValueError("labwc is missing; use a supported Raspberry Pi OS desktop image")
    if shutil.disk_usage(Path.home()).free < 2 * 1024**3:
        raise ValueError("At least 2 GiB free disk space is required for staged installation")
    prefix.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (
        any(char in str(prefix) for char in ('"', "%", "\n", "\r", "\\"))
        or not prefix.is_absolute()
    ):
        raise ValueError("Install prefix must be an absolute Linux path suitable for systemd")
    for path in (
        Path.home() / ".config/rytm-randomizer",
        Path.home() / ".local/state/rytm-appliance",
    ):
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix=".install-", dir=prefix) as staging:
        stage = Path(staging)
        manifest = unpack_verified(archive, stage)
        required = {
            "src/pyproject.toml",
            "src/rytm_randomizer/cockpit/appliance_runtime.py",
            "web/index.html",
            "pi_appliance.py",
            "assets/rytm-appliance-backend.service",
            "assets/rytm-appliance-kiosk.service",
            "assets/rytm-appliance.target",
            "assets/rytm-appliance.desktop",
        }
        if not required.issubset(manifest["files"]):
            raise ValueError("Appliance package is missing required runtime files")
        release_name = f"{manifest['version']}-{str(manifest['source_sha'])[:12]}"
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-[a-f0-9]{12}", release_name):
            raise ValueError("Invalid appliance release identity")
        release = prefix / "releases" / release_name
        if release.exists():
            if json.loads((release / "manifest.json").read_text()) != manifest:
                raise ValueError("Existing release identity has different contents")
            checked([str(release / ".venv/bin/python"), "-m", "pip", "check"])
        else:
            if not online and not list((stage / "wheels").glob("*.whl")):
                raise ValueError(
                    "Offline install needs an ARM64 wheelhouse; use wheelhouse on the target first"
                )
            if not online:
                receipt = json.loads((stage / "wheels/receipt.json").read_text())
                if (
                    receipt.get("source_sha") != manifest["source_sha"]
                    or str(receipt.get("python", "")).split(".")[:2]
                    != platform.python_version().split(".")[:2]
                ):
                    raise ValueError("Offline wheelhouse does not match this source/Python ABI")
            release.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(stage), str(release))
            try:
                checked([sys.executable, "-m", "venv", str(release / ".venv")])
                python = str(release / ".venv/bin/python")
                options = [] if online else ["--no-index", "--find-links", str(release / "wheels")]
                requirement = (
                    str(release / "src") + "[cockpit]"
                    if online
                    else f"rytm-randomizer[cockpit]=={manifest['version']}"
                )
                checked([python, "-m", "pip", "install", *options, requirement], timeout=900)
                checked([python, "-m", "pip", "check"])
                (release / "installed-requirements.txt").write_text(
                    checked([python, "-m", "pip", "freeze"]) + "\n"
                )
            except BaseException:
                if release.resolve().is_relative_to((prefix / "releases").resolve()):
                    shutil.rmtree(release)
                raise
        units = Path.home() / ".config/systemd/user"
        units.mkdir(parents=True, exist_ok=True)
        for template in (release / "assets").glob("*.service"):
            content = template.read_text()
            for before, after in _service_paths(prefix).items():
                content = content.replace(before, after)
            (units / template.name).write_text(content)
        (units / "rytm-appliance.target").write_bytes(
            (release / "assets/rytm-appliance.target").read_bytes()
        )
        if autostart:
            desktop = Path.home() / ".config/autostart/rytm-appliance.desktop"
            desktop.parent.mkdir(parents=True, exist_ok=True)
            content = (release / "assets/rytm-appliance.desktop").read_text()
            for before, after in _service_paths(prefix).items():
                content = content.replace(before, after)
            desktop.write_text(content)
        previous = prefix / "previous"
        current = prefix / "current"
        if current.exists() and not current.is_symlink():
            raise ValueError("Active release pointer is not a symlink; refusing to overwrite it")
        if current.is_symlink() and current.resolve() != release:
            replacement = prefix / ".previous-next"
            replacement.unlink(missing_ok=True)
            replacement.symlink_to(current.resolve(), target_is_directory=True)
            replacement.replace(previous)
        replacement = prefix / ".current-next"
        replacement.unlink(missing_ok=True)
        replacement.symlink_to(release, target_is_directory=True)
        replacement.replace(current)
    checked(["systemctl", "--user", "daemon-reload"])
    print(
        f"Installed {release_name}; launch with the session-start command in the graphical session"
    )


def bind_runtime_source() -> Path:
    """Use this checkout/release's verified source, even with another editable install."""
    launcher = Path(__file__).resolve().parent
    source = launcher / "src" if (launcher / "src/rytm_randomizer").is_dir() else ROOT
    package_root = source / "rytm_randomizer"
    if not (package_root / "__init__.py").is_file():
        raise ValueError("This launcher has no colocated appliance source")
    loaded = sys.modules.get("rytm_randomizer")
    if loaded is not None:
        origin = getattr(loaded, "__file__", None)
        if not isinstance(origin, str) or Path(origin).resolve().parent != package_root.resolve():
            raise ValueError(
                "Another RytmRandomizer source is already loaded; start a fresh process"
            )
    sys.path.insert(0, str(source))
    return source


def serve(args: argparse.Namespace) -> None:
    bind_runtime_source()
    runtime = args.runtime_dir.resolve()
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        runtime.chmod(0o700)
    os.environ.update(
        {
            "RYTM_RAND_APPLIANCE_WEB_ROOT": str(args.web_root.resolve()),
            "RYTM_RAND_APPLIANCE_RUNTIME_DIR": str(runtime),
            "RYTM_RAND_WS_TOKEN_FILE": str(runtime / "ws-token"),
            "RYTM_RAND_ARM_SECRET_FILE": str(runtime / "arm-secret"),
            "RYTM_RAND_WS_PORT": str(args.port),
            "RYTM_RAND_MIDI_BACKEND": "auto" if args.hardware_input else "off",
            "RYTM_RAND_APPLIANCE_SIMULATION": "1" if args.simulation else "0",
        }
    )
    if args.hardware_input and args.simulation:
        raise ValueError("Simulation and hardware input are separate launch modes")
    original_stdout, original_stderr = sys.stdout, sys.stderr
    output = RotatingOutput(args.log_file) if args.log_file else None
    if output is not None:
        sys.stdout = sys.stderr = output
    package_logger: logging.Logger | None = None
    prior_handlers: list[logging.Handler] = []
    prior_level, prior_propagate = logging.NOTSET, False
    try:
        from rytm_randomizer.observability.logging import configure_logging

        package_logger = logging.getLogger("rytm_randomizer")
        prior_handlers = list(package_logger.handlers)
        prior_level, prior_propagate = package_logger.level, package_logger.propagate
        configure_logging(json=True, stream=sys.stderr)
        if args.hardware_input:
            from rytm_randomizer.app import main as app_main

            app_main(["--arm", "--cockpit-kit-capture-sidecar"])
        else:
            from rytm_randomizer.cockpit.__main__ import run

            run()
    finally:
        for name in ("ws-token", "arm-secret", "launch.html"):
            (runtime / name).unlink(missing_ok=True)
        sys.stdout, sys.stderr = original_stdout, original_stderr
        if package_logger is not None:
            for handler in list(package_logger.handlers):
                package_logger.removeHandler(handler)
                handler.close()
            for handler in prior_handlers:
                package_logger.addHandler(handler)
            package_logger.setLevel(prior_level)
            package_logger.propagate = prior_propagate
        if output is not None:
            output.close()


def kiosk(args: argparse.Namespace) -> None:
    if not os.environ.get("WAYLAND_DISPLAY"):
        raise ValueError(
            "Launch inside the existing Wayland graphical session; do not invent compositor flags"
        )
    launch = args.runtime_dir.resolve() / "launch.html"
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/health", timeout=1):
                if launch.is_file():
                    break
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.25)
    else:
        raise ValueError("Backend did not become healthy in 30 seconds; run diagnose")
    args.browser_profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    args.browser_profile.chmod(0o700)
    handoff = digest(launch.read_bytes())
    process = subprocess.Popen(
        [
            browser_path(),
            "--kiosk",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-session-crashed-bubble",
            "--ozone-platform=wayland",
            f"--user-data-dir={args.browser_profile.resolve()}",
            launch.as_uri(),
        ],
        start_new_session=True,
    )
    try:
        while process.poll() is None:
            time.sleep(1)
            if launch.is_file() and digest(launch.read_bytes()) != handoff:
                # The new backend has new capabilities; refresh only by repeating
                # the private POST handoff. Do not replay any application action.
                break
        if process.poll() is not None and process.returncode:
            raise ValueError(f"Chromium exited with code {process.returncode}")
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)


def rollback(prefix: Path) -> None:
    previous = prefix / "previous"
    if not previous.is_symlink() or not previous.resolve().is_relative_to(
        (prefix / "releases").resolve()
    ):
        raise ValueError("No valid previous release; user data has not been changed")
    checked(["systemctl", "--user", "stop", "rytm-appliance.target"])
    replacement = prefix / ".rollback-next"
    replacement.unlink(missing_ok=True)
    replacement.symlink_to(previous.resolve(), target_is_directory=True)
    replacement.replace(prefix / "current")
    checked(["systemctl", "--user", "start", "rytm-appliance.target"])


def uninstall() -> None:
    checked(["systemctl", "--user", "stop", "rytm-appliance.target"])
    units = Path.home() / ".config/systemd/user"
    for name in (
        "rytm-appliance-backend.service",
        "rytm-appliance-kiosk.service",
        "rytm-appliance.target",
    ):
        (units / name).unlink(missing_ok=True)
    (Path.home() / ".config/autostart/rytm-appliance.desktop").unlink(missing_ok=True)
    checked(["systemctl", "--user", "daemon-reload"])
    print("Services removed. Releases, profiles, captures and configuration are retained.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "build",
            "package",
            "install",
            "serve",
            "kiosk",
            "diagnose",
            "rollback",
            "uninstall",
            "wheelhouse",
            "session-start",
        ),
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--web-root", type=Path, default=ROOT / "desktop/web/dist")
    parser.add_argument(
        "--runtime-dir",
        type=Path,
        default=Path(os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())) / "rytm-appliance",
    )
    parser.add_argument("--prefix", type=Path, default=Path.home() / ".local/share/rytm-appliance")
    parser.add_argument(
        "--browser-profile", type=Path, default=Path.home() / ".local/state/rytm-appliance/chromium"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "output/rytm-appliance.tar")
    parser.add_argument("--archive", type=Path)
    parser.add_argument(
        "--log-file", type=Path, help="Private rotating log: 2 MiB plus three backups"
    )
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument(
        "--online", action="store_true", help="Permit dependency download during target install"
    )
    parser.add_argument(
        "--autostart", action="store_true", help="Opt in to this user's graphical-session startup"
    )
    parser.add_argument(
        "--hardware-input",
        action="store_true",
        help="Use existing app --arm capture composition; UI arming still required",
    )
    parser.add_argument(
        "--simulation",
        action="store_true",
        help="Explicit disconnected simulation for desktop preview",
    )
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    try:
        if args.command == "build":
            build()
        elif args.command == "package":
            package(args.output, web_root=args.web_root, wheelhouse=args.wheelhouse)
        elif args.command == "install":
            if args.archive is None:
                parser.error("install requires --archive")
            install(args.archive, prefix=args.prefix, online=args.online, autostart=args.autostart)
        elif args.command == "serve":
            serve(args)
        elif args.command == "kiosk":
            kiosk(args)
        elif args.command == "diagnose":
            print(json.dumps(diagnose(port=args.port), indent=2))
        elif args.command == "rollback":
            rollback(args.prefix)
        elif args.command == "uninstall":
            uninstall()
        elif args.command == "session-start":
            checked(
                [
                    "systemctl",
                    "--user",
                    "import-environment",
                    "WAYLAND_DISPLAY",
                    "DISPLAY",
                    "XDG_CURRENT_DESKTOP",
                ]
            )
            checked(["systemctl", "--user", "restart", "rytm-appliance.target"])
        elif args.command == "wheelhouse":
            if not supported_target() or args.wheelhouse is None:
                parser.error("wheelhouse requires target ARM64 OS and --wheelhouse")
            args.wheelhouse.mkdir(parents=True, exist_ok=True)
            checked(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--wheel-dir",
                    str(args.wheelhouse),
                    str(ROOT) + "[cockpit]",
                ],
                timeout=1200,
            )
            receipt = {
                "source_sha": checked(["git", "rev-parse", "HEAD"], cwd=ROOT),
                "machine": platform.machine(),
                "python": platform.python_version(),
                "files": {
                    path.name: digest(path.read_bytes()) for path in args.wheelhouse.glob("*.whl")
                },
            }
            (args.wheelhouse / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Appliance command failed: {exc}\n")


if __name__ == "__main__":
    main()

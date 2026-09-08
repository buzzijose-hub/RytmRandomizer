"""Collect native Tauri bundles and verify exact artifacts before release assembly.

The Tauri bundler signs its native updater files. Minisign verifies the decoded
Tauri signature documents here; secret presence never establishes signed status.
No command in this module publishes a release or modifies a channel branch.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Final
from urllib.parse import quote

from release_lib import SUPPORTED_TARGETS, ReleaseError, generate_manifest, is_valid_version

_DISTRIBUTION_SUFFIXES: Final[tuple[str, ...]] = (
    ".exe",
    ".msi",
    ".dmg",
    ".pkg",
    ".AppImage",
    ".deb",
    ".rpm",
    ".app.tar.gz",
)
_UPDATER_SUFFIXES: Final[Mapping[str, str]] = {
    "windows-x86_64": ".exe",
    "linux-x86_64": ".AppImage",
    "darwin-x86_64": ".app.tar.gz",
    "darwin-aarch64": ".app.tar.gz",
}


def _object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("release metadata must be an object")
    return value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing release field: {name}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def configure(config_path: Path, *, updater_requested: bool, public_key: str) -> bool:
    """Set build-only signing posture; keyless builds retain normal bundles."""
    config = _object(config_path)
    bundle = config.get("bundle")
    plugins = config.get("plugins")
    if not isinstance(bundle, dict) or not isinstance(plugins, dict):
        raise ValueError("Tauri bundle/plugins configuration is missing")
    updater = plugins.get("updater")
    if not isinstance(updater, dict):
        raise ValueError("Tauri updater configuration is missing")
    signing = updater_requested and bool(os.environ.get("TAURI_SIGNING_PRIVATE_KEY", ""))
    if signing and not public_key.strip():
        raise ValueError("updater signing requires the matching public key")
    bundle["createUpdaterArtifacts"] = signing
    updater["pubkey"] = public_key.strip() if signing else ""
    _write_json(config_path, config)
    return signing


def _copy(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError("release artifact must be a regular file")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError(f"duplicate release asset: {destination.name}")
    shutil.copyfile(source, destination)


def collect(
    bundle_root: Path,
    output: Path,
    *,
    target: str,
    version: str,
    source_sha: str,
    config_path: Path,
) -> None:
    """Index native bundles under collision-free, versioned public names."""
    if target not in SUPPORTED_TARGETS or not is_valid_version(version):
        raise ValueError("unsupported release target or version")
    config = _object(config_path)
    if config.get("version") != version:
        raise ValueError("Tauri bundle version differs from VERSION")
    bundle = config.get("bundle")
    plugins = config.get("plugins")
    if not isinstance(bundle, dict) or not isinstance(plugins, dict):
        raise ValueError("Tauri configuration is incomplete")
    updater_config = plugins.get("updater")
    if not isinstance(updater_config, dict):
        raise ValueError("Tauri updater configuration is missing")
    signing = bundle.get("createUpdaterArtifacts") is True
    files = sorted(
        path
        for path in bundle_root.rglob("*")
        if path.is_file()
        and path.name.endswith(_DISTRIBUTION_SUFFIXES)
        and not any(part.endswith(".app") for part in path.parts)
    )
    if not files:
        raise ValueError("no native distributions were built")
    assets: list[dict[str, object]] = []
    updater: dict[str, str] | None = None
    for source in files:
        suffix = next(s for s in _DISTRIBUTION_SUFFIXES if source.name.endswith(s))
        name = f"RytmRandomizer-{version}-{target}{suffix}"
        destination = output / name
        _copy(source, destination)
        assets.append(
            {"name": name, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}
        )
        if signing and suffix == _UPDATER_SUFFIXES[target]:
            if updater is not None:
                raise ValueError("multiple updater artifacts for one target")
            signature_path = source.with_name(source.name + ".sig")
            signature = signature_path.read_text(encoding="utf-8").strip()
            if not signature:
                raise ValueError("updater signature is empty")
            _copy(signature_path, output / (name + ".sig"))
            updater = {"name": name, "signature": signature}
    if signing and updater is None:
        raise ValueError("requested native updater artifact was not built")
    _write_json(
        output / "artifact-index.json",
        {
            "target": target,
            "version": version,
            "source_sha": source_sha,
            "public_key": updater_config.get("pubkey", ""),
            "assets": assets,
            "updater": updater,
        },
    )


def verify_signature(
    artifact: Path, signature: str, public_key: str, *, executable: str = "minisign"
) -> None:
    """Use the reference Minisign verifier over the bytes shipped to clients."""
    with tempfile.TemporaryDirectory(prefix="rytm-release-verify-") as directory:
        root = Path(directory)
        key_path = root / "public.pub"
        signature_path = root / "artifact.minisig"
        key_path.write_bytes(base64.b64decode(public_key, validate=True))
        signature_path.write_bytes(base64.b64decode(signature, validate=True))
        result = subprocess.run(  # noqa: S603 - executable is operator-selected; no shell
            [
                executable,
                "-Vm",
                str(artifact),
                "-p",
                str(key_path),
                "-x",
                str(signature_path),
                "-q",
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode:
            raise ValueError(f"updater signature verification failed: {artifact.name}")


def verify_self_test(fixture: Path, *, executable: str = "minisign") -> None:
    """Require the real verifier to accept a public vector and reject tampering."""
    vector = _object(fixture)
    signature = _text(vector.get("signature"), "signature")
    public_key = _text(vector.get("public_key"), "public_key")
    payload = base64.b64decode(_text(vector.get("payload"), "payload"), validate=True)
    with tempfile.TemporaryDirectory(prefix="rytm-release-vector-") as directory:
        artifact = Path(directory) / "public-test-vector"
        artifact.write_bytes(payload)
        verify_signature(artifact, signature, public_key, executable=executable)
        artifact.write_bytes(payload + b"tampered")
        try:
            verify_signature(artifact, signature, public_key, executable=executable)
        except ValueError:
            return
        raise ValueError("signature verifier accepted modified artifact bytes")


def assemble(
    inputs: Path,
    output: Path,
    *,
    version: str,
    source_sha: str,
    public_key: str,
    repository: str,
    pub_date: str,
    run_url: str,
    workflow_sha: str,
    verifier: str = "minisign",
) -> bool:
    """Assemble all distributions; create a fleet manifest only after verification."""
    if not is_valid_version(version) or not repository or output.exists():
        raise ValueError("invalid version/repository or existing release output")
    indices = sorted(inputs.rglob("artifact-index.json"))
    targets: set[str] = set()
    platforms: dict[str, dict[str, str]] = {}
    sources: list[tuple[Path, str]] = []
    for index_path in indices:
        index = _object(index_path)
        target = _text(index.get("target"), "target")
        if target not in SUPPORTED_TARGETS or target in targets:
            raise ValueError("duplicate or unsupported release target")
        targets.add(target)
        if index.get("version") != version or index.get("source_sha") != source_sha:
            raise ValueError("release artifact provenance mismatch")
        assets = index.get("assets")
        if not isinstance(assets, list) or not assets:
            raise ValueError("release target has no distributions")
        names: set[str] = set()
        for asset in assets:
            if not isinstance(asset, dict):
                raise ValueError("invalid release asset")
            name = _text(asset.get("name"), "asset name")
            if Path(name).name != name or "/" in name or "\\" in name or name in names:
                raise ValueError("unsafe or duplicate release asset name")
            names.add(name)
            source = index_path.parent / name
            if source.is_symlink() or not source.is_file():
                raise ValueError("release asset is missing or linked")
            if hashlib.sha256(source.read_bytes()).hexdigest() != asset.get("sha256"):
                raise ValueError("release artifact hash mismatch")
            sources.append((source, name))
        updater = index.get("updater")
        if updater is not None:
            if (
                not isinstance(updater, dict)
                or not public_key
                or index.get("public_key") != public_key
            ):
                raise ValueError("updater public key mismatch")
            name = _text(updater.get("name"), "updater name")
            signature = _text(updater.get("signature"), "signature")
            if name not in names or not name.endswith(_UPDATER_SUFFIXES[target]):
                raise ValueError("updater is not an indexed native artifact")
            signature_path = index_path.parent / (name + ".sig")
            if (
                signature_path.is_symlink()
                or signature_path.read_text(encoding="utf-8").strip() != signature
            ):
                raise ValueError("signature file differs from artifact index")
            verify_signature(index_path.parent / name, signature, public_key, executable=verifier)
            sources.append((signature_path, name + ".sig"))
            platforms[target] = {
                "url": f"https://github.com/{repository}/releases/download/v{version}/{quote(name)}",
                "signature": signature,
            }
    if targets != set(SUPPORTED_TARGETS):
        raise ValueError("release is missing a supported target")
    if platforms and set(platforms) != targets:
        raise ValueError("mixed signed and unsigned target artifacts")
    manifest = None
    if platforms:
        manifest = generate_manifest(
            channel="beta",
            version=version,
            pub_date=pub_date,
            notes="",
            platforms=platforms,
            source_sha=source_sha,
            workflow_run_url=run_url,
            builder_workflow_sha=workflow_sha,
        )
    # Include wheel/sdist, standalone sidecars and Briefcase installers too.
    for directory in ("python", "sidecars", "installers"):
        source_root = inputs / directory
        extra_files = sorted(p for p in source_root.rglob("*") if p.is_file())
        if not extra_files:
            raise ValueError(f"missing release distribution group: {directory}")
        for source in extra_files:
            relative = source.relative_to(source_root)
            name = (
                source.name if directory == "python" else f"{directory}-{'-'.join(relative.parts)}"
            )
            sources.append((source, name))
    if len({name for _, name in sources}) != len(sources):
        raise ValueError("release asset name collision")
    for source, name in sources:
        _copy(source, output / "dist" / name)
    if manifest is not None:
        _write_json(output / "beta.json", manifest)
        for target in sorted(targets):
            (output / "dist" / f"beacon-{version}-{target}.txt").write_bytes(b".")
    _write_json(
        output / "release-status.json", {"signed": bool(platforms), "targets": sorted(targets)}
    )
    return bool(platforms)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("configure")
    config.add_argument("--config", type=Path, required=True)
    config.add_argument("--updater-requested", choices=("true", "false"), required=True)
    collect_parser = commands.add_parser("collect")
    collect_parser.add_argument("--config", type=Path, required=True)
    collect_parser.add_argument("--bundle-root", type=Path, required=True)
    collect_parser.add_argument("--output", type=Path, required=True)
    collect_parser.add_argument("--target", required=True)
    collect_parser.add_argument("--version", required=True)
    assembly = commands.add_parser("assemble")
    assembly.add_argument("--inputs", type=Path, required=True)
    assembly.add_argument("--output", type=Path, required=True)
    assembly.add_argument("--version", required=True)
    assembly.add_argument("--source-epoch", type=int, required=True)
    self_test = commands.add_parser("verify-self-test")
    self_test.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args(argv)
    public_key = os.environ.get("TAURI_SIGNING_PUBLIC_KEY", "").strip()
    source_sha = os.environ.get("GITHUB_SHA", "")
    try:
        if args.command == "configure":
            configure(
                args.config,
                updater_requested=args.updater_requested == "true",
                public_key=public_key,
            )
        elif args.command == "collect":
            collect(
                args.bundle_root,
                args.output,
                target=args.target,
                version=args.version,
                source_sha=source_sha,
                config_path=args.config,
            )
        elif args.command == "verify-self-test":
            verify_self_test(args.fixture, executable=os.environ.get("MINISIGN", "minisign"))
        else:
            repository = os.environ.get("GITHUB_REPOSITORY", "")
            signed = assemble(
                args.inputs,
                args.output,
                version=args.version,
                source_sha=source_sha,
                public_key=public_key,
                repository=repository,
                pub_date=datetime.fromtimestamp(args.source_epoch, timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                run_url=f"https://github.com/{repository}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
                workflow_sha=os.environ.get("GITHUB_WORKFLOW_SHA", "") or source_sha,
                verifier=os.environ.get("MINISIGN", "minisign"),
            )
            if output_file := os.environ.get("GITHUB_OUTPUT"):
                with Path(output_file).open("a", encoding="utf-8") as stream:
                    stream.write(f"signed={str(signed).lower()}\n")
    except (OSError, ValueError, ReleaseError) as error:
        parser.exit(1, f"release artifact assembly refused: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

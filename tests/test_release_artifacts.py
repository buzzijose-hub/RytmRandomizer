"""Artifact-flow regressions; real Minisign vectors also run in the release job."""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_artifacts as artifacts

pytestmark = pytest.mark.fast
_SHA = "a" * 40
_KEY = base64.b64encode(b"public key document").decode()
_SIGNATURE = base64.b64encode(b"signature document").decode()


def _config(path: Path, signing: bool) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "version": "1.35.0",
                "bundle": {"createUpdaterArtifacts": signing},
                "plugins": {"updater": {"pubkey": _KEY if signing else ""}},
            }
        ),
        encoding="utf-8",
    )
    return path


def _inputs(tmp_path: Path, signing: bool = True) -> Path:
    inputs = tmp_path / "inputs"
    for target, suffix in artifacts._UPDATER_SUFFIXES.items():
        source = tmp_path / "built" / target
        source.mkdir(parents=True)
        # Unsigned macOS publishes its ordinary DMG, not a nonexistent updater archive.
        suffix = ".dmg" if not signing and target.startswith("darwin") else suffix
        bundle = source / ("Cockpit" + suffix)
        bundle.write_bytes(b"native bundle " + target.encode())
        if signing:
            bundle.with_name(bundle.name + ".sig").write_text(_SIGNATURE, encoding="utf-8")
        artifacts.collect(
            source,
            inputs / "bundles" / target,
            target=target,
            version="1.35.0",
            source_sha=_SHA,
            config_path=_config(tmp_path / "configs" / f"{target}.json", signing),
        )
    for group, name in (
        ("python", "project.whl"),
        ("installers", "legacy.msi"),
        ("sidecars", "rytm-sidecar.exe"),
    ):
        path = inputs / group / name
        path.parent.mkdir(parents=True)
        path.write_bytes(group.encode())
    return inputs


def _assemble(inputs: Path, output: Path) -> bool:
    return artifacts.assemble(
        inputs,
        output,
        version="1.35.0",
        source_sha=_SHA,
        public_key=_KEY,
        repository="o/r",
        pub_date="2026-09-08T12:00:00Z",
        notes="Prepared release notes",
        hardware_revalidation=True,
        run_url="https://github.com/o/r/actions/runs/1",
        workflow_sha=_SHA,
    )


def test_configure_keyless_disables_updater_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TAURI_SIGNING_PRIVATE_KEY", raising=False)
    path = _config(tmp_path / "config.json", True)
    assert (
        artifacts.configure(path, target="windows-x86_64", updater_requested=True, public_key=_KEY)
        is False
    )
    assert json.loads(path.read_text())["bundle"]["createUpdaterArtifacts"] is False


def test_configure_requires_public_key_when_signing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TAURI_SIGNING_PRIVATE_KEY", "test-only-secret")
    path = _config(tmp_path / "config.json", False)
    with pytest.raises(ValueError, match="matching public key"):
        artifacts.configure(path, target="windows-x86_64", updater_requested=True, public_key="")
    assert (
        artifacts.configure(path, target="windows-x86_64", updater_requested=True, public_key=_KEY)
        is True
    )
    assert json.loads(path.read_text())["plugins"]["updater"]["pubkey"] == _KEY


@pytest.mark.parametrize("signing", [True, False])
@pytest.mark.parametrize("target", artifacts.SUPPORTED_TARGETS)
def test_linux_desktop_only_ships_the_appimage_format_served_by_its_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, signing: bool, target: str
) -> None:
    monkeypatch.setenv("TAURI_SIGNING_PRIVATE_KEY", "test-only-secret" if signing else "")
    path = _config(tmp_path / "config.json", signing)
    config = json.loads(path.read_text())
    config["bundle"]["targets"] = "all"
    path.write_text(json.dumps(config), encoding="utf-8")
    artifacts.configure(path, target=target, updater_requested=True, public_key=_KEY)
    bundle = json.loads(path.read_text())["bundle"]
    assert bundle["targets"] == (["appimage"] if target == "linux-x86_64" else "all")
    assert bundle["createUpdaterArtifacts"] is signing


def test_configuration_refuses_unknown_target_without_rewriting_file(tmp_path: Path) -> None:
    path = _config(tmp_path / "config.json", False)
    original = path.read_bytes()
    with pytest.raises(ValueError, match="unsupported release target"):
        artifacts.configure(path, target="unknown", updater_requested=True, public_key=_KEY)
    assert path.read_bytes() == original


def _shell(tmp_path: Path) -> Path:
    shell = tmp_path / "desktop" / "shell"
    shell.mkdir(parents=True)
    (shell / "Cargo.toml").write_text("[package]\nname='test'\n", encoding="utf-8")
    _config(shell / "tauri.conf.json", False)
    return shell


def test_bundle_cleanup_removes_stale_installers_and_preserves_compilation_cache(
    tmp_path: Path,
) -> None:
    shell = _shell(tmp_path)
    bundle = shell / "target" / "release" / "bundle"
    for relative in ("old.exe", "old.exe.sig", "subfolder/old.AppImage"):
        path = bundle / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"previous release")
    retained = [
        shell / "target" / directory / "compiled" for directory in ("release/deps", "debug")
    ]
    for path in retained:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"cached object")

    artifacts.clean_bundle_output(shell)
    assert not bundle.exists()
    assert all(path.read_bytes() == b"cached object" for path in retained)
    # A cold-cache/no-bundle invocation is a supported no-op.
    artifacts.clean_bundle_output(shell)
    bundle.mkdir()
    (bundle / "current.exe").write_bytes(b"current release")
    output = tmp_path / "collected"
    artifacts.collect(
        bundle,
        output,
        target="windows-x86_64",
        version="1.35.0",
        source_sha=_SHA,
        config_path=shell / "tauri.conf.json",
    )
    index = json.loads((output / "artifact-index.json").read_text())
    assert len(index["assets"]) == 1
    assert (output / index["assets"][0]["name"]).read_bytes() == b"current release"


@pytest.mark.parametrize("component", ["target", "target/release", "target/release/bundle"])
def test_bundle_cleanup_refuses_resolved_links_and_windows_junctions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str
) -> None:
    shell = _shell(tmp_path)
    bundle = shell / "target" / "release" / "bundle"
    bundle.mkdir(parents=True)
    original = bundle / "keep.exe"
    original.write_bytes(b"preserve")
    outside = tmp_path / "unrelated"
    outside.mkdir()
    private = outside / "keep.txt"
    private.write_bytes(b"unrelated contents")
    resolve = Path.resolve

    def resolve_redirect(path: Path, *args, **kwargs) -> Path:
        # Junctions need no symlink bit: resolved destination is the boundary.
        return outside if path == shell / component else resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve_redirect)
    with pytest.raises(ValueError, match="links or junctions"):
        artifacts.clean_bundle_output(shell)
    assert original.read_bytes() == b"preserve"
    assert private.read_bytes() == b"unrelated contents"


def test_bundle_cleanup_refuses_non_shell_or_non_directory_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Tauri shell directory"):
        artifacts.clean_bundle_output(tmp_path)
    shell = _shell(tmp_path)
    bundle = shell / "target" / "release" / "bundle"
    bundle.parent.mkdir(parents=True)
    bundle.write_bytes(b"not a directory")
    with pytest.raises(ValueError, match="must be a directory"):
        artifacts.clean_bundle_output(shell)
    assert bundle.read_bytes() == b"not a directory"


def test_signed_assembly_verifies_exact_files_before_manifest_and_includes_all_distributions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _inputs(tmp_path)
    verified = []

    def verify(path: Path, signature: str, key: str, *, executable: str) -> None:
        assert signature == _SIGNATURE
        assert key == _KEY
        assert path.read_bytes().startswith(b"native bundle ")
        verified.append(path.name)

    monkeypatch.setattr(artifacts, "verify_signature", verify)
    output = tmp_path / "assembled"
    assert _assemble(inputs, output) is True
    manifest = json.loads((output / "beta.json").read_text())
    assert set(manifest["platforms"]) == set(artifacts.SUPPORTED_TARGETS)
    assert len(verified) == 4
    assert manifest["notes"] == "Prepared release notes"
    assert manifest["hardware_revalidation"] is True
    assert (output / "dist" / "update-manifest.json").read_bytes() == (
        output / "beta.json"
    ).read_bytes()
    for target, entry in manifest["platforms"].items():
        name = entry["url"].rsplit("/", 1)[-1]
        assert name in verified
        assert (output / "dist" / name).is_file()
        assert (output / "dist" / f"beacon-1.35.0-{target}.txt").read_bytes() == b"."
    assert (output / "dist" / "project.whl").read_bytes() == b"python"
    assert (output / "dist" / "installers-legacy.msi").read_bytes() == b"installers"
    assert (output / "dist" / "sidecars-rytm-sidecar.exe").read_bytes() == b"sidecars"


def test_keyless_assembly_produces_draft_assets_without_a_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        artifacts,
        "verify_signature",
        lambda *args, **kwargs: pytest.fail("unsigned build attempted verification"),
    )
    output = tmp_path / "assembled"
    assert _assemble(_inputs(tmp_path, signing=False), output) is False
    assert not (output / "beta.json").exists()
    assert not list((output / "dist").glob("beacon-*"))
    assert json.loads((output / "release-status.json").read_text())["signed"] is False


def test_assembly_refuses_a_missing_target_even_when_other_signatures_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    next(inputs.rglob("artifact-index.json")).unlink()
    monkeypatch.setattr(artifacts, "verify_signature", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="missing a supported target"):
        _assemble(inputs, tmp_path / "assembled")
    assert not (tmp_path / "assembled").exists()


@pytest.mark.parametrize(
    "damage",
    ["bytes", "signature", "public_key", "source_sha", "missing_file", "target", "path", "mixed"],
)
def test_damaged_inputs_never_produce_a_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    inputs = _inputs(tmp_path)
    index_path = next(inputs.rglob("artifact-index.json"))
    index = json.loads(index_path.read_text())
    name = index["assets"][0]["name"]
    if damage == "bytes":
        (index_path.parent / name).write_bytes(b"tampered")
    elif damage == "signature":
        (index_path.parent / (name + ".sig")).write_text("wrong", encoding="utf-8")
    elif damage == "missing_file":
        (index_path.parent / name).unlink()
    elif damage == "path":
        index["assets"][0]["name"] = "../escape"
    elif damage == "mixed":
        index["updater"] = None
    else:
        index[damage] = "wrong"
    index_path.write_text(json.dumps(index), encoding="utf-8")
    monkeypatch.setattr(artifacts, "verify_signature", lambda *args, **kwargs: None)
    output = tmp_path / "assembled"
    with pytest.raises(ValueError):
        _assemble(inputs, output)
    assert not output.exists()


def test_failed_real_verifier_cannot_be_replaced_by_key_presence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path)
    monkeypatch.setenv("TAURI_SIGNING_PRIVATE_KEY", "present-but-not-proof")

    def reject(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, b"", b"invalid signature")

    monkeypatch.setattr(artifacts.subprocess, "run", reject)
    with pytest.raises(ValueError, match="signature verification failed"):
        _assemble(inputs, tmp_path / "assembled")
    assert not (tmp_path / "assembled").exists()


def test_verifier_passes_decoded_documents_and_exact_artifact_to_reference_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = tmp_path / "artifact.exe"
    artifact.write_bytes(b"exact shipped bytes")

    def run(command, **kwargs):
        assert command[0] == "reference-minisign"
        assert Path(command[2]).read_bytes() == b"exact shipped bytes"
        assert Path(command[4]).read_bytes() == b"public key document"
        assert Path(command[6]).read_bytes() == b"signature document"
        assert kwargs == {"check": False, "capture_output": True}
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(artifacts.subprocess, "run", run)
    artifacts.verify_signature(artifact, _SIGNATURE, _KEY, executable="reference-minisign")


def test_reference_self_test_fails_when_verifier_accepts_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vector = Path(__file__).parent / "fixtures" / "release_signature.json"
    monkeypatch.setattr(artifacts, "verify_signature", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="accepted modified"):
        artifacts.verify_self_test(vector)


def test_release_workflow_wires_verified_assembly_and_preserves_draft_gates() -> None:
    root = Path(__file__).resolve().parents[1]
    release = yaml.safe_load((root / ".github/workflows/release.yml").read_text())
    jobs = release["jobs"]
    assert "TAURI_SIGNING_PRIVATE_KEY" in jobs["build"]["secrets"]
    steps = jobs["publish"]["steps"]
    assembly = next(step for step in steps if step.get("id") == "assemble")
    assert "release_artifacts.py assemble" in assembly["run"]
    assert "SOURCE_EPOCH" in assembly["env"]
    publish = next(step for step in steps if "action-gh-release" in step.get("uses", ""))
    assert publish["with"]["files"] == "assembled/dist/*"
    assert "assemble.outputs.signed" in publish["with"]["draft"]
    assert "dry_run != 'true'" in publish["if"]
    assert "signed == 'true'" in jobs["manifest"]["if"]
    assert any("verify-self-test" in step.get("run", "") for step in steps)


def test_desktop_workflow_configures_target_and_cleans_cached_bundles_before_build() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/installers.yml").read_text())
    steps = workflow["jobs"]["desktop-bundle"]["steps"]
    configure = next(
        step for step in steps if "release_artifacts.py configure" in step.get("run", "")
    )
    assert configure["env"]["RELEASE_TARGET"] == "${{ matrix.target }}"
    assert '--target "$RELEASE_TARGET"' in configure["run"]
    cleanup = next(
        step for step in steps if "release_artifacts.py clean-bundle" in step.get("run", "")
    )
    assert "--shell-root desktop/shell" in cleanup["run"]
    cache = next(step for step in steps if "actions/cache" in step.get("uses", ""))
    build = next(step for step in steps if step.get("name") == "Build Tauri bundle")
    collect = next(step for step in steps if "release_artifacts.py collect" in step.get("run", ""))
    assert steps.index(cache) < steps.index(cleanup) < steps.index(build) < steps.index(collect)


def _release_history(
    tmp_path: Path,
    *,
    changed_path: str = "README.md",
    pins: str = "1.3.3",
    annotation: str = "",
    previous: bool = True,
) -> Path:
    root = tmp_path / "history"
    root.mkdir()
    git = shutil.which("git")
    assert git is not None

    def run(*args: str) -> None:
        subprocess.run(
            [git, "-C", str(root), *args], check=True, capture_output=True, encoding="utf-8"
        )

    def project(mido: str) -> str:
        return f'[project]\nname="test"\ndependencies=["mido=={mido}","python-rtmidi==1.5.8"]\n'

    run("init", "--quiet")
    run("config", "user.name", "Release test")
    run("config", "user.email", "release-test@example.invalid")
    (root / "pyproject.toml").write_text(project("1.3.3"), encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        "## [1.34.0] - 2026-01-01\n\nPrevious release\n", encoding="utf-8"
    )
    run("add", ".")
    run("commit", "--quiet", "-m", "initial")
    if previous:
        run("tag", "v1.34.0")
    (root / "CHANGELOG.md").write_text(
        "## [Unreleased]\n\nFuture notes\n\n## [1.35.0] - 2026-09-08\n\n### Fixed\n\n- Current release.\n\n## [1.34.0] - 2026-01-01\n\nOld notes\n",
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(project(pins), encoding="utf-8")
    changed = root / changed_path
    changed.parent.mkdir(parents=True, exist_ok=True)
    changed.write_text("changed\n", encoding="utf-8")
    run("add", ".")
    run("commit", "--quiet", "-m", "release changes")
    if annotation:
        run("tag", "-a", "v1.35.0", "-m", annotation)
    return root


@pytest.mark.parametrize(
    ("path", "pins", "annotation", "requested", "expected"),
    [
        ("README.md", "1.3.3", "", False, False),
        ("rytm_randomizer/engines/pad.py", "1.3.3", "", False, True),
        ("rytm_randomizer/senders/guarded.py", "1.3.3", "", False, True),
        ("rytm_randomizer/app.py", "1.3.3", "", False, True),
        ("tests/fixtures/v134_parity/sample.json", "1.3.3", "", False, True),
        ("README.md", "1.3.4", "", False, True),
        ("README.md", "1.3.3", "release [hw-reval]", False, True),
        ("README.md", "1.3.3", "release notes", False, False),
        ("README.md", "1.3.3", "", True, True),
    ],
)
def test_release_metadata_uses_actual_git_diff_pins_and_additive_flags(
    tmp_path: Path, path: str, pins: str, annotation: str, requested: bool, expected: bool
) -> None:
    root = _release_history(tmp_path, changed_path=path, pins=pins, annotation=annotation)
    metadata = artifacts.release_metadata(
        root, version="1.35.0", tag="v1.35.0" if annotation else "", requested=requested
    )
    assert metadata == {
        "notes": "### Fixed\n\n- Current release.",
        "hardware_revalidation": expected,
        "previous_tag": "v1.34.0",
    }


def test_first_release_without_comparison_tag_keeps_conservative_warning(tmp_path: Path) -> None:
    root = _release_history(tmp_path, previous=False)
    metadata = artifacts.release_metadata(root, version="1.35.0", tag="", requested=False)
    assert metadata["hardware_revalidation"] is True
    assert metadata["previous_tag"] is None


@pytest.mark.parametrize("text", ["## [Unreleased]\nFuture\n", "## [1.35.0]\n\n## [1.34.0]\nOld\n"])
def test_missing_or_empty_release_notes_are_refused(text: str) -> None:
    with pytest.raises(ValueError, match="release version section|notes are empty"):
        artifacts.release_notes(text, "1.35.0")


def _promotion_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    monkeypatch.setattr(artifacts, "verify_signature", lambda *args, **kwargs: None)
    output = tmp_path / "assembled"
    _assemble(_inputs(tmp_path), output)
    manifest = output / "dist" / "update-manifest.json"
    data = json.loads(manifest.read_text())
    data["future_field"] = {"preserve": "value"}
    data["minimum_version"] = "1.30.0"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    release = tmp_path / "published-release.json"
    release.write_text(
        json.dumps(
            {
                "tag_name": "v1.35.0",
                "draft": False,
                "assets": [
                    {"browser_download_url": entry["url"]} for entry in data["platforms"].values()
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest, release


def test_promotion_preserves_exact_artifacts_notes_warning_and_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, release = _promotion_files(tmp_path, monkeypatch)
    output = tmp_path / "stable.json"
    assert (
        artifacts.main(
            [
                "promote",
                "--manifest",
                str(manifest),
                "--release",
                str(release),
                "--version",
                "1.35.0",
                "--rollout-percent",
                "10",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    expected = json.loads(manifest.read_text())
    expected.update(channel="stable", rollout_percent=10)
    assert json.loads(output.read_text()) == expected


@pytest.mark.parametrize(
    "damage",
    [
        "version",
        "draft",
        "release_tag",
        "missing_asset",
        "wrong_asset",
        "invalid_manifest",
        "partial_targets",
        "rollout",
    ],
)
def test_promotion_refuses_unpublished_mismatched_or_incomplete_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    manifest, release = _promotion_files(tmp_path, monkeypatch)
    data = json.loads(manifest.read_text())
    published = json.loads(release.read_text())
    if damage == "version":
        data["version"] = "1.36.0"
    elif damage == "draft":
        published["draft"] = True
    elif damage == "release_tag":
        published["tag_name"] = "v1.34.0"
    elif damage == "missing_asset":
        published["assets"].pop()
    elif damage == "wrong_asset":
        published["assets"][0]["browser_download_url"] += "-not-the-artifact"
    elif damage == "invalid_manifest":
        data["hardware_revalidation"] = "false"
    elif damage == "partial_targets":
        data["platforms"].pop(next(iter(data["platforms"])))
    manifest.write_text(json.dumps(data), encoding="utf-8")
    release.write_text(json.dumps(published), encoding="utf-8")
    output = tmp_path / "stable.json"
    with pytest.raises(ValueError):
        artifacts.promote(
            manifest,
            release,
            output,
            version="1.35.0",
            rollout_percent=101 if damage == "rollout" else 10,
        )
    assert not output.exists()


def test_release_workflows_wire_actual_metadata_and_archived_promotion() -> None:
    root = Path(__file__).resolve().parents[1]
    release = yaml.safe_load((root / ".github/workflows/release.yml").read_text())
    steps = release["jobs"]["publish"]["steps"]
    assert steps[0]["with"]["fetch-depth"] == 0
    metadata = next(
        step for step in steps if "release_artifacts.py metadata" in step.get("run", "")
    )
    assert (
        metadata["env"]["RELEASE_TAG"] == "${{ github.ref_type == 'tag' && github.ref_name || '' }}"
    )
    assembly = next(step for step in steps if step.get("id") == "assemble")
    assert "--metadata release-metadata.json" in assembly["run"]
    assert steps.index(metadata) < steps.index(assembly)
    promotion = yaml.safe_load((root / ".github/workflows/promote.yml").read_text())
    job = promotion["jobs"]["promote"]
    assert job["environment"] == "stable-promote"
    runs = "\n".join(step.get("run", "") for step in job["steps"])
    assert "release_lib.py generate" not in runs
    assert "release_artifacts.py promote" in runs
    assert "gh release download" in runs and "--pattern update-manifest.json" in runs

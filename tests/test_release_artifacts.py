"""Artifact-flow regressions; real Minisign vectors also run in the release job."""

from __future__ import annotations

import base64
import json
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
        run_url="https://github.com/o/r/actions/runs/1",
        workflow_sha=_SHA,
    )


def test_configure_keyless_disables_updater_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TAURI_SIGNING_PRIVATE_KEY", raising=False)
    path = _config(tmp_path / "config.json", True)
    assert artifacts.configure(path, updater_requested=True, public_key=_KEY) is False
    assert json.loads(path.read_text())["bundle"]["createUpdaterArtifacts"] is False


def test_configure_requires_public_key_when_signing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TAURI_SIGNING_PRIVATE_KEY", "test-only-secret")
    path = _config(tmp_path / "config.json", False)
    with pytest.raises(ValueError, match="matching public key"):
        artifacts.configure(path, updater_requested=True, public_key="")
    assert artifacts.configure(path, updater_requested=True, public_key=_KEY) is True
    assert json.loads(path.read_text())["plugins"]["updater"]["pubkey"] == _KEY


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

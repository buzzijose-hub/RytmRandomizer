"""Capture additive replay witnesses by executing the actual pinned old tree.

Run this script in an e30cc84c worktree with --original-source pointing to the
retained Init frame. Only the analyzer is substituted; production codecs,
native accessors, candidate rendering, workspace and store execute unchanged.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave
from dataclasses import asdict, replace
from io import BytesIO
from pathlib import Path
from threading import Event
from typing import Final

SOURCE_COMMIT: Final[str] = "e30cc84cbb9c745654632f71ac827e05007ce320"
ORIGINAL_SHA256: Final[str] = "50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e"
CASES: Final[tuple[tuple[str, int], ...]] = (("mutable_16257", 16257), ("protected_32513", 32513))
RECEIPT_MODULES: Final[tuple[str, ...]] = (
    "rytm_randomizer.cockpit.export.reference_sound_session",
    "rytm_randomizer.cockpit.export.reference_sound_store",
    "rytm_randomizer.cockpit.export.reference_sound_candidates",
    "rytm_randomizer.devices.strategies.analog_four_saved_kit_codec",
    "rytm_randomizer.devices.strategies.analog_four_native_fields",
    "rytm_randomizer.devices.strategies.analog_four_kit_fields",
    "rytm_randomizer.style_analysis.extractor",
)


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], timeout=10)  # noqa: S603,S607


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _verified_file(root: Path, path: Path) -> dict[str, str]:
    relative = path.resolve().relative_to(root).as_posix()
    actual = path.read_bytes()
    # Git's index stores LF; normalize checkout CRLF only for source comparison.
    _require(
        actual.replace(b"\r\n", b"\n") == _git(root, "show", f"{SOURCE_COMMIT}:{relative}"),
        f"Old source differs from pinned Git revision: {relative}",
    )
    return {"path": relative, "sha256": _sha(actual.replace(b"\r\n", b"\n"))}


def _old_helper(root: Path, relative: str, name: str, namespace: dict[str, object]) -> object:
    path = root / relative
    _verified_file(root, path)
    source = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    matches = [
        node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    _require(len(matches) == 1, "Old helper definition is missing or ambiguous")
    function = matches[0]
    function.decorator_list = []
    isolated = ast.Module(body=[function], type_ignores=[])
    # Extract definitions, not the conftest module or any pytest setup/fixtures.
    exec(compile(isolated, relative, "exec"), namespace)  # noqa: S102
    return namespace[name]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-source", type=Path, required=True)
    arguments = parser.parse_args()
    started = time.monotonic()
    root = Path(__file__).resolve().parents[1]
    _require(
        _git(root, "rev-parse", "HEAD").decode().strip() == SOURCE_COMMIT,
        "Capture requires the pinned old Git HEAD",
    )
    original = arguments.original_source.read_bytes()
    _require(_sha(original) == ORIGINAL_SHA256, "Original Init frame hash differs")
    destination = root / "tests/fixtures/native_representation"
    targets = [destination / f"legacy_v1_e30_{name}" for name, _ in CASES]
    _require(not any(target.exists() for target in targets), "Immutable fixtures already exist")
    os.environ["RYTM_RAND_MIDI_BACKEND"] = "off"
    os.environ["RYTM_RAND_UPDATES"] = "off"
    sys.path.insert(0, str(root))
    original_import = builtins.__import__

    def passive_import(name: str, *args: object, **kwargs: object) -> object:
        if name.split(".")[0] in ("mido", "rtmidi"):
            raise RuntimeError("Fixture capture must not import a MIDI backend")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = passive_import
    from rytm_randomizer.cockpit.export.reference_sound_candidates import (
        list_reference_sound_controls,
    )
    from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
    from rytm_randomizer.cockpit.export.reference_sound_store import (
        ReferenceSoundStore,
        reference_sound_json,
    )
    from rytm_randomizer.devices.strategies.analog_four_kit_fields import A4Kit
    from rytm_randomizer.devices.strategies.analog_four_native_fields import (
        read_analog_four_native_fields,
    )
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
        encode_analog_four_saved_kit_payload,
    )

    analysis_helper = _old_helper(root, "tests/conftest.py", "audio_patch_dna_analysis", {})
    pcm_helper = _old_helper(
        root,
        "tests/cockpit/conftest.py",
        "make_reference_pcm",
        {"BytesIO": BytesIO, "wave": wave, "struct": struct},
    )
    analysis = analysis_helper()
    pcm = pcm_helper(frames=3200)

    def analyzer(path: Path, _cancel: Event):
        return replace(
            analysis,
            synthesis_features=replace(
                analysis.synthesis_features, audio_sha256=_sha(path.read_bytes())
            ),
        )

    decoded = decode_analog_four_saved_kit_payload(original[1:-1], require_trailer=True)
    _require(decoded.prefix[5] == 0x52, "Original source must be indexed 0x52")
    captures: list[tuple[Path, Path, dict[str, object]]] = []
    with tempfile.TemporaryDirectory(prefix="native-v1-capture-") as temporary:
        for (name, native), target in zip(CASES, targets, strict=True):
            _require(time.monotonic() - started < 30, "Bounded fixture capture exceeded 30 seconds")
            kit = A4Kit.from_bytes(decoded.unpacked)
            sound = kit.sound(0)
            sound.set_fixed_8_8_raw("filter1_frequency", native)
            kit.replace_sound(0, sound)
            body = kit.to_bytes()
            changed = {
                i
                for i, pair in enumerate(zip(decoded.unpacked, body, strict=True))
                if pair[0] != pair[1]
            }
            _require(changed <= {128, 129}, "Synthetic source changed fields outside T1 F1")
            encoded = encode_analog_four_saved_kit_payload(decoded.prefix, body)
            frame = b"\xf0" + encoded.payload + b"\xf7"
            _require(
                encode_analog_four_saved_kit_payload(
                    decode_analog_four_saved_kit_payload(frame[1:-1], require_trailer=True).prefix,
                    body,
                ).payload
                == frame[1:-1],
                "Old source codec did not round-trip exactly",
            )
            source_value = read_analog_four_native_fields(frame).value("filter1_frequency", 1)
            _require(
                source_value.encoded_native == native,
                "Old accessor disagrees with source native word",
            )
            directory = Path(temporary) / name
            store = ReferenceSoundStore(directory / "store")
            workspace = ReferenceSoundWorkspace(store, analyzer=analyzer)
            imported = workspace.import_reference(pcm, f"Legacy v1 F1 {native}")
            generated = workspace.commit(
                workspace.generate(
                    imported["session_id"],
                    source_frame=frame,
                    device_id="analog_four_mk2",
                    target=1,
                    parameters=("filter1_frequency",),
                    locks=(),
                    strength=0.5,
                    cancel=Event(),
                )
            )
            favorite = generated["candidates"][0]["candidate_id"]
            retained = workspace.select(generated["session_id"], favorite, favorite=True)
            _require(
                workspace.reopen(retained["session_id"]) == retained, "Old workspace replay differs"
            )
            exports = directory / "exports"
            exports.mkdir()
            for candidate in retained["candidates"]:
                patch = workspace.candidate(retained["session_id"], candidate["candidate_id"])
                _require(
                    reference_sound_json(patch.to_dict()) == reference_sound_json(candidate),
                    "Old candidate DTO changed on replay",
                )
                (exports / f"{candidate['candidate_id']}.syx").write_bytes(
                    workspace.export_patch(retained["session_id"], candidate["candidate_id"], 18)
                )
            # Publication locks are transient namespaces, not retained session artifacts.
            (store.directory / ".sound-publication.lock").unlink()
            receipt: dict[str, object] = {
                "fixture_schema": "native-reference-sound-legacy-v1",
                "source_commit": SOURCE_COMMIT,
                "physical_validation": False,
                "hardware_authority": False,
                "evidence_kind": "software-only synthetic replay witness",
                "original_source": {"file": "a4_init_retained.syx", "sha256": ORIGINAL_SHA256},
                "session_id": retained["session_id"],
                "favorite_candidate_id": favorite,
                "candidate_ids": [item["candidate_id"] for item in retained["candidates"]],
                "source_sha256": _sha(frame),
                "source_native": native,
                "target": 1,
                "response_kind": 0x52,
                "parameters": ["filter1_frequency"],
                "locks": [],
                "strength": 0.5,
                "export_slot": 18,
                "source_control": next(
                    item.to_dict()
                    for item in list_reference_sound_controls(frame, "analog_four_mk2", 1)
                    if item.parameter == "filter1_frequency"
                ),
                "source_native_domain": (
                    None if source_value.domain is None else asdict(source_value.domain)
                ),
                "analysis_substitution": "Only analyzer callback replaced; exact old audio_patch_dna_analysis dataclasses, with actual WAV digest",
                "synthetic_wav": {
                    "sha256": _sha(pcm),
                    "frames": 3200,
                    "rate": 8000,
                    "channels": 1,
                    "sample_width": 2,
                },
                "helper_definitions": [
                    _verified_file(root, root / path)
                    for path in ("tests/conftest.py", "tests/cockpit/conftest.py")
                ],
                "artifact_sha256": {
                    path.relative_to(directory).as_posix(): _sha(path.read_bytes())
                    for path in sorted(directory.rglob("*"))
                    if path.is_file()
                },
            }
            captures.append((target, directory, receipt))
        application_files = {
            Path(module.__file__).resolve()
            for name, module in tuple(sys.modules.items())
            if name == "rytm_randomizer" or name.startswith("rytm_randomizer.")
        }
        for path in application_files:
            _verified_file(root, path)
        _require(not {"mido", "rtmidi"}.intersection(sys.modules), "MIDI backend was imported")
        _require(
            _git(root, "rev-parse", "HEAD").decode().strip() == SOURCE_COMMIT,
            "Git HEAD changed during capture",
        )
        _require(
            arguments.original_source.read_bytes() == original,
            "Original source changed during capture",
        )
        modules = [
            _verified_file(root, Path(sys.modules[name].__file__)) for name in RECEIPT_MODULES
        ]
        for target, directory, receipt in captures:
            receipt["application_modules"] = modules
            receipt["all_loaded_application_modules_verified_against_git"] = len(application_files)
            receipt["capture_script_sha256"] = _sha(Path(__file__).read_bytes())
            shutil.copytree(directory, target)
            (target / "provenance.json").write_text(
                json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n"
            )
            print(
                json.dumps(
                    {
                        "fixture": target.name,
                        "provenance_sha256": _sha((target / "provenance.json").read_bytes()),
                        "source_commit": SOURCE_COMMIT,
                        "physical_validation": False,
                    }
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

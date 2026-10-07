"""The explicit QA CLI delegates to real pack/codec verification without hardware."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from rytm_randomizer.cockpit.show_bank.export import ShowPackService
from rytm_randomizer.devices import get_analog_four_native_field_capability
from rytm_randomizer.devices.strategies.analog_four_native_fields import (
    AnalogFourNativeEncoding,
    AnalogFourNativeReadback,
)
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)

from .test_native_offline_journey import _favorite, _generate, _journey

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]
_ROOT: Final[Path] = Path(__file__).resolve().parents[3]


def _run(package: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "verify_offline_rehearsal_pack.py"), str(package)],
        cwd=_ROOT,
        env={**os.environ, "PYTHONPATH": str(_ROOT), "RYTM_RAND_MIDI_BACKEND": "off"},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "rehearsal_pack_verifier_under_test", _ROOT / "scripts" / "verify_offline_rehearsal_pack.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "source_name",
    ["A4_Test2_T1_OSC1_FIN_P1_Kit.syx", "A4_Test3_T1_OSC1_FIN_M1_Kit.syx"],
)
def test_rehearsal_pack_verifier_checks_native_precision_and_reserved_bytes(
    tmp_path: Path, source_name: str
) -> None:
    journey = _journey(tmp_path, source_name)
    candidate = _generate(journey, fields=("osc1_tune",), count=1)[0]
    bank = _favorite(journey, candidate)
    service = ShowPackService(tmp_path / "packs", store=journey.workspace.store)
    exported = service.export(bank, package_id="rehearsal")
    result = _run(exported.package_dir)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verified"] and report["canonical_profile_replay"]
    assert report["native_value_checks"] == 1
    assert report["approved_changed_native_bytes"] == 1
    assert len(report["original_frame_sha256"]) == 2
    assert report["hardware_access"] is False
    assert report["hardware_validation_granted"] is False


@pytest.mark.parametrize(
    "parameter,alias,corrupt_fine",
    [
        ("osc1_tune", "pitch_control", False),
        ("osc1_tune", "pitch_control", True),
        ("env2_depth_a", "effect_tune", False),
    ],
)
def test_rehearsal_pack_verifier_uses_canonical_encoding_not_parameter_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, parameter: str, alias: str, corrupt_fine: bool
) -> None:
    journey = _journey(tmp_path, "A4_Test2_T1_OSC1_FIN_P1_Kit.syx")
    candidate = _generate(journey, fields=(parameter,), count=1)[0]
    service = ShowPackService(tmp_path / "packs", store=journey.workspace.store)
    exported = service.export(_favorite(journey, candidate), package_id="encoding-proof")
    verified = service.verify(exported.package_id)
    native = get_analog_four_native_field_capability()
    artifact_id = candidate.analog_four_candidate.sysex.artifact_id
    frames = dict(verified.frames_by_artifact_id)
    if corrupt_fine:
        decoded = decode_analog_four_saved_kit_payload(
            frames[artifact_id][1:-1], require_trailer=True
        )
        body = bytearray(decoded.unpacked)
        offsets = (
            native.read_native_fields(frames[artifact_id]).value(parameter, 1).unpacked_offsets
        )
        body[offsets[1]] ^= 1
        encoded = encode_analog_four_saved_kit_payload(decoded.prefix, bytes(body))
        frames[artifact_id] = b"\xf0" + encoded.payload + b"\xf7"
    cell = native.read_native_fields(frames[artifact_id]).value(parameter, 1)
    assert cell.metadata.native_encoding is (
        AnalogFourNativeEncoding.TUNE
        if parameter == "osc1_tune"
        else AnalogFourNativeEncoding.MOD_DEPTH
    )
    claim = replace(
        candidate.analog_four_candidate.values[0],
        parameter=alias,
        encoded_native=cell.encoded_native,
        screen_value=cell.screen_value,
    )
    renamed = replace(
        candidate, analog_four_candidate=replace(candidate.analog_four_candidate, values=(claim,))
    )
    entry = replace(verified.bank.entries[0], candidates=(renamed,))
    proof_input = replace(
        verified, bank=replace(verified.bank, entries=(entry,)), frames_by_artifact_id=frames
    )

    class AliasedReader:
        def read_native_fields(self, frame: bytes) -> AnalogFourNativeReadback:
            readback = native.read_native_fields(frame)
            return replace(
                readback,
                values=tuple(
                    (
                        replace(value, metadata=replace(value.metadata, parameter=alias))
                        if value.parameter == parameter
                        else value
                    )
                    for value in readback.values
                ),
            )

    # Alias only the QA proof input after real pack/replay verification, not its authority.
    verifier = _load_verifier()
    monkeypatch.setattr(ShowPackService, "verify", lambda _self, _package_id: proof_input)
    monkeypatch.setattr(verifier, "get_analog_four_native_field_capability", AliasedReader)
    if corrupt_fine:
        with pytest.raises(ValueError, match="coupled pitch precision"):
            verifier.verify_rehearsal_pack(exported.package_dir)
    else:
        report = verifier.verify_rehearsal_pack(exported.package_dir)
        assert report["verified"] and report["native_value_checks"] == 1
        assert report["approved_changed_native_bytes"] == (1 if parameter == "osc1_tune" else 2)
        assert report["hardware_access"] is False


@pytest.mark.parametrize("failure", ["missing", "truncated", "bad-suffix"])
def test_rehearsal_pack_verifier_refuses_bad_packages_without_private_details(
    tmp_path: Path, failure: str
) -> None:
    package = tmp_path / "private-operator-name.show-pack"
    if failure == "bad-suffix":
        package = tmp_path / "private-operator-name"
    elif failure == "truncated":
        package.mkdir()
        (package / "manifest.json").write_bytes(b'{"format":')
    result = _run(package)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["verified"] is False
    assert report["error_type"] in {"DataError", "ValueError"}
    assert str(tmp_path) not in result.stdout and "private-operator-name" not in result.stdout
    assert result.stderr == ""

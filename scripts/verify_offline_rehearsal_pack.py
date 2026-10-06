"""Read-only rehearsal proof using the canonical pack verifier and native codec."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from rytm_randomizer.cockpit.data.show_bank import (
    A4_NATIVE_MUTATION_ALGORITHM,
    AnalogFourNativeCandidateValue,
)
from rytm_randomizer.cockpit.show_bank.export import SHOW_PACK_SUFFIX, ShowPackService
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.devices import get_analog_four_native_field_capability
from rytm_randomizer.devices.strategies.analog_four_kit_fields import decode_a4_pitch_components
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
)
from rytm_randomizer.observability.errors import RytmRandomizerError


def verify_rehearsal_pack(package: Path) -> dict[str, object]:
    """Reverify exact frames/replay, then independently check declared byte isolation."""
    if not package.name.endswith(SHOW_PACK_SUFFIX):
        raise ValueError("expected one show-pack directory")
    package_id = package.name[: -len(SHOW_PACK_SUFFIX)]
    with TemporaryDirectory(prefix="offline-rehearsal-verifier-") as temporary:
        service = ShowPackService(package.parent, store=ShowBankStore(Path(temporary)))
        verified = service.verify(package_id)
    native = get_analog_four_native_field_capability()
    source_hashes: set[str] = set()
    candidate_hashes: set[str] = set()
    native_fields = 0
    changed_bytes = 0
    for entry in verified.bank.entries:
        for capture in (entry.rytm_source, entry.analog_four_source):
            frame = verified.frames_by_artifact_id[capture.sysex.artifact_id]
            digest = hashlib.sha256(frame).hexdigest()
            if digest != capture.sysex.frame_sha256:
                raise ValueError("rehearsal original source identity changed")
            source_hashes.add(digest)
        source = verified.frames_by_artifact_id[entry.analog_four_source.sysex.artifact_id]
        original = native.read_native_fields(source)
        source_body = decode_analog_four_saved_kit_payload(
            source[1:-1], require_trailer=True
        ).unpacked
        for candidate in entry.candidates:
            if candidate.recipe.a4_algorithm != A4_NATIVE_MUTATION_ALGORITHM:
                continue
            generated = verified.frames_by_artifact_id[
                candidate.analog_four_candidate.sysex.artifact_id
            ]
            candidate_hashes.add(hashlib.sha256(generated).hexdigest())
            after = native.read_native_fields(generated)
            body = decode_analog_four_saved_kit_payload(
                generated[1:-1], require_trailer=True
            ).unpacked
            approved: set[int] = set()
            for value in candidate.analog_four_candidate.values:
                if not isinstance(value, AnalogFourNativeCandidateValue):
                    raise ValueError("native candidate contains a legacy value")
                cell = after.value(value.parameter, value.track_id)
                if (
                    cell.encoded_native != value.encoded_native
                    or cell.screen_value != value.screen_value
                    or cell.unpacked_offsets != value.unpacked_offsets
                ):
                    raise ValueError("rehearsal native value disagrees with decoded bytes")
                if value.parameter.endswith("tune"):
                    before_cell = original.value(value.parameter, value.track_id)
                    if (
                        decode_a4_pitch_components(cell.encoded_native)[1:]
                        != decode_a4_pitch_components(before_cell.encoded_native)[1:]
                    ):
                        raise ValueError("rehearsal changed coupled pitch precision")
                approved.update(
                    cell.unpacked_offsets[:1]
                    if value.parameter.endswith("tune")
                    else cell.unpacked_offsets
                )
                native_fields += 1
            differences = {
                offset
                for offset, pair in enumerate(zip(source_body, body, strict=True))
                if pair[0] != pair[1]
            }
            if not differences <= approved:
                raise ValueError("rehearsal changed an undeclared or protected native byte")
            changed_bytes += len(differences)
            for cell in original.values:
                if not set(cell.unpacked_offsets).intersection(approved):
                    if after.value(cell.parameter, cell.track).native_bytes != cell.native_bytes:
                        raise ValueError("rehearsal changed an excluded native field")
    return {
        "verified": True,
        "entry_count": len(verified.bank.entries),
        "candidate_count": sum(len(entry.candidates) for entry in verified.bank.entries),
        "original_frame_sha256": sorted(source_hashes),
        "native_candidate_frame_sha256": sorted(candidate_hashes),
        "native_value_checks": native_fields,
        "approved_changed_native_bytes": changed_bytes,
        "canonical_profile_replay": True,
        "hardware_access": False,
        "hardware_validation_granted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    arguments = parser.parse_args()
    try:
        result = verify_rehearsal_pack(arguments.package)
    except (OSError, ValueError, RuntimeError, RytmRandomizerError) as error:
        print(json.dumps({"verified": False, "error_type": type(error).__name__}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

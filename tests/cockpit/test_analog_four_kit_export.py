"""Tests for guarded Analog Four saved-kit file export."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import analog_four_saved_kit_frame

pytestmark = pytest.mark.fast


def _mutation(
    parameter: str = "Filter2 Resonance",
    screen_value: str = "64",
):
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        AnalogFourSavedKitMutation,
    )

    return AnalogFourSavedKitMutation(
        parameter=parameter,
        track=1,
        screen_value=screen_value,
    )


def test_export_analog_four_saved_kit_writes_rendered_bytes_atomically(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import export_analog_four_saved_kit

    source_path = tmp_path / "source.syx"
    output_path = tmp_path / "nested" / "generated.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())

    result = export_analog_four_saved_kit(
        source_path=source_path,
        output_path=output_path,
        mutations=(_mutation(),),
    )

    assert result.write.path == output_path.resolve()
    assert result.write.bytes_written == 2770
    assert result.write.overwrote_existing is False
    assert output_path.read_bytes() == result.render.framed_sysex
    assert result.render.applied_mutations[0].rendered_unpacked_value == 64


def test_export_analog_four_saved_kit_refuses_silent_overwrite(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import export_analog_four_saved_kit

    source_path = tmp_path / "source.syx"
    output_path = tmp_path / "generated.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())
    output_path.write_bytes(b"existing")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        export_analog_four_saved_kit(
            source_path=source_path,
            output_path=output_path,
            mutations=(_mutation(),),
        )

    assert output_path.read_bytes() == b"existing"


def test_export_analog_four_saved_kit_can_explicitly_overwrite(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import export_analog_four_saved_kit

    source_path = tmp_path / "source.syx"
    output_path = tmp_path / "generated.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())
    output_path.write_bytes(b"existing")

    result = export_analog_four_saved_kit(
        source_path=source_path,
        output_path=output_path,
        mutations=(_mutation(),),
        overwrite=True,
    )

    assert result.write.overwrote_existing is True
    assert output_path.read_bytes() == result.render.framed_sysex


def test_export_analog_four_saved_kit_surfaces_missing_source(tmp_path: Path) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import export_analog_four_saved_kit

    with pytest.raises(FileNotFoundError):
        export_analog_four_saved_kit(
            source_path=tmp_path / "missing.syx",
            output_path=tmp_path / "generated.syx",
            mutations=(_mutation(),),
        )


def test_export_analog_four_saved_kit_rejects_candidate_only_parameter(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import (
        export_analog_four_saved_kit,
    )

    source_path = tmp_path / "source.syx"
    output_path = tmp_path / "generated.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())

    with pytest.raises(ValueError, match="hardware-write-validated"):
        export_analog_four_saved_kit(
            source_path=source_path,
            output_path=output_path,
            mutations=(_mutation("Filter1 Resonance", "20"),),
        )

    assert not output_path.exists()


def test_export_analog_four_saved_kit_reuses_canonical_atomic_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.cockpit.export.analog_four_kit as export_module
    from rytm_randomizer.cockpit.export.writer import WriteResult

    source_path = tmp_path / "source.syx"
    output_path = tmp_path / "generated.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())
    calls: list[tuple[Path, bytes, bool]] = []

    def fake_atomic_write(
        path: Path,
        data: bytes,
        *,
        overwrite: bool = False,
    ) -> WriteResult:
        calls.append((path, data, overwrite))
        return WriteResult(
            path=path.resolve(),
            bytes_written=len(data),
            overwrote_existing=overwrite,
        )

    monkeypatch.setattr(export_module, "atomic_write", fake_atomic_write)

    result = export_module.export_analog_four_saved_kit(
        source_path=source_path,
        output_path=output_path,
        mutations=(_mutation(),),
        overwrite=True,
    )

    assert calls == [(output_path, result.render.framed_sysex, True)]


def test_export_analog_four_saved_kit_rejects_wrong_mutation_record(
    tmp_path: Path,
) -> None:
    from typing import cast

    from rytm_randomizer.cockpit.export.analog_four_kit import (
        export_analog_four_saved_kit,
    )
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        AnalogFourSavedKitMutation,
    )

    with pytest.raises(TypeError, match="must contain AnalogFourSavedKitMutation"):
        export_analog_four_saved_kit(
            source_path=tmp_path / "unused.syx",
            output_path=tmp_path / "generated.syx",
            mutations=cast(tuple[AnalogFourSavedKitMutation, ...], (object(),)),
        )

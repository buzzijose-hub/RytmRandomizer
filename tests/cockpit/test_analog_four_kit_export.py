"""Tests for guarded Analog Four saved-kit file export."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from conftest import (
    analog_four_saved_kit_frame,
)
from conftest import analog_four_saved_kit_mutation as _mutation

pytestmark = [
    pytest.mark.fast,
    pytest.mark.usefixtures("isolated_observability"),
]


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


def test_export_analog_four_saved_kit_records_success_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_kit
    from rytm_randomizer.observability.metrics import get_metrics

    source_path = tmp_path / "source.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())
    traced: list[tuple[str, str]] = []
    logged: list[dict[str, object]] = []

    @contextmanager
    def observe_operation(name: str, **_kwargs: object) -> Iterator[None]:
        traced.append(("start", name))
        yield
        traced.append(("end", name))

    monkeypatch.setattr(analog_four_kit, "operation", observe_operation)
    monkeypatch.setattr(
        analog_four_kit._logger,
        "info",
        lambda _message, *, extra: logged.append(extra),
    )

    analog_four_kit.export_analog_four_saved_kit(
        source_path=source_path,
        output_path=tmp_path / "generated.syx",
        mutations=(_mutation(),),
    )

    metrics = get_metrics()
    assert metrics.export_count == 1
    assert not metrics.export_errors_by_code
    assert traced == [
        ("start", "a4_saved_kit_export"),
        ("end", "a4_saved_kit_export"),
    ]
    assert logged[0]["outcome"] == "completed"
    assert float(logged[0]["duration_ms"]) >= 0.0
    assert "export_count=1" in str(logged[0]["metrics_summary"])


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


def test_export_analog_four_saved_kit_surfaces_missing_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_kit
    from rytm_randomizer.observability.metrics import get_metrics

    logged: list[dict[str, object]] = []
    monkeypatch.setattr(
        analog_four_kit._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )

    with pytest.raises(FileNotFoundError):
        analog_four_kit.export_analog_four_saved_kit(
            source_path=tmp_path / "missing.syx",
            output_path=tmp_path / "generated.syx",
            mutations=(_mutation(),),
        )

    metrics = get_metrics()
    assert metrics.export_count == 1
    assert metrics.export_errors_by_code["input_not_found"] == 1
    assert logged[0]["outcome"] == "failed"
    assert logged[0]["fingerprint"] == "a4.saved_kit_export.failed"
    assert logged[0]["error_code"] == "input_not_found"
    assert float(logged[0]["duration_ms"]) >= 0.0
    assert "input_not_found:1" in str(logged[0]["metrics_summary"])


def test_export_analog_four_saved_kit_records_operator_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import export_analog_four_saved_kit
    from rytm_randomizer.observability.metrics import get_metrics

    source_path = tmp_path / "source.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())

    def interrupt_read(_path: Path) -> bytes:
        raise KeyboardInterrupt("operator cancelled")

    monkeypatch.setattr(Path, "read_bytes", interrupt_read)

    with pytest.raises(KeyboardInterrupt, match="operator cancelled"):
        export_analog_four_saved_kit(
            source_path=source_path,
            output_path=tmp_path / "generated.syx",
            mutations=(_mutation(),),
        )

    metrics = get_metrics()
    assert metrics.export_count == 1
    assert metrics.export_errors_by_code["interrupted"] == 1


def test_export_analog_four_saved_kit_classifies_missing_output_as_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import analog_four_kit
    from rytm_randomizer.observability.metrics import get_metrics

    source_path = tmp_path / "source.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())

    def missing_output(
        _path: Path,
        _data: bytes,
        *,
        overwrite: bool = False,
    ) -> object:
        del overwrite
        raise FileNotFoundError("output parent disappeared")

    monkeypatch.setattr(analog_four_kit, "atomic_write", missing_output)

    with pytest.raises(FileNotFoundError, match="output parent disappeared"):
        analog_four_kit.export_analog_four_saved_kit(
            source_path=source_path,
            output_path=tmp_path / "missing" / "generated.syx",
            mutations=(_mutation(),),
        )

    assert get_metrics().export_errors_by_code["write_failed"] == 1


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (("source_path", "source.syx"), ("output_path", "output.syx")),
)
def test_export_analog_four_saved_kit_records_invalid_path_types(
    field_name: str,
    invalid_value: object,
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import (
        export_analog_four_saved_kit,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    source_path: object = tmp_path / "source.syx"
    output_path: object = tmp_path / "output.syx"
    if field_name == "source_path":
        source_path = invalid_value
    else:
        output_path = invalid_value

    with pytest.raises(TypeError, match=field_name):
        export_analog_four_saved_kit(
            source_path=source_path,  # type: ignore[arg-type]
            output_path=output_path,  # type: ignore[arg-type]
            mutations=(_mutation(),),
        )

    assert get_metrics().export_errors_by_code["validation"] == 1


def test_export_analog_four_saved_kit_rejects_candidate_only_parameter(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.export.analog_four_kit import (
        export_analog_four_saved_kit,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    source_path = tmp_path / "source.syx"
    output_path = tmp_path / "generated.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())

    with pytest.raises(ValueError, match="hardware-write-validated"):
        export_analog_four_saved_kit(
            source_path=source_path,
            output_path=output_path,
            mutations=(
                _mutation(
                    parameter="Filter1 Resonance",
                    screen_value="20",
                ),
            ),
        )

    assert not output_path.exists()
    metrics = get_metrics()
    assert metrics.export_count == 1
    assert metrics.export_errors_by_code["validation"] == 1


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

    source_path = tmp_path / "source.syx"
    source_path.write_bytes(analog_four_saved_kit_frame())

    with pytest.raises(TypeError, match="must contain AnalogFourSavedKitMutation"):
        export_analog_four_saved_kit(
            source_path=source_path,
            output_path=tmp_path / "generated.syx",
            mutations=cast(tuple[AnalogFourSavedKitMutation, ...], (object(),)),
        )

"""Read supplied A4 experiment files and serialize passive inspection only."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from ..data.analog_four_saved_kit_layout import A4_SAVED_KIT_FRAMED_SIZE
from ..devices.strategies.analog_four_working_kit_comparison import (
    AnalogFourExperimentEvidenceOrigin,
    AnalogFourWorkingKitComparison,
    AnalogFourWorkingKitFrames,
    AnalogFourWorkingKitRole,
    compare_analog_four_working_kit,
)


@dataclass(frozen=True)
class AnalogFourWorkingKitFiles:
    manual_indexed_baseline: Path
    queried_indexed_baseline: Path
    working_first: Path
    working_repeat: Path
    post_save_indexed: Path
    recovered_indexed: Path

    def ordered(self) -> tuple[Path, ...]:
        return (
            self.manual_indexed_baseline,
            self.queried_indexed_baseline,
            self.working_first,
            self.working_repeat,
            self.post_save_indexed,
            self.recovered_indexed,
        )


def _read_frame(role: AnalogFourWorkingKitRole, path: Path) -> bytes:
    try:
        with path.open("rb") as source:
            raw = source.read(A4_SAVED_KIT_FRAMED_SIZE + 1)
    except OSError as exc:
        raise ValueError(f"{role.value}: input file is missing or unreadable") from exc
    if len(raw) != A4_SAVED_KIT_FRAMED_SIZE:
        raise ValueError(f"{role.value}: input file must contain one complete A4 frame")
    return raw


def build_analog_four_working_kit_comparison_report(
    files: AnalogFourWorkingKitFiles,
    *,
    track: int,
    evidence_origin: AnalogFourExperimentEvidenceOrigin | str,
    baseline_label: str | None = None,
    changed_label: str | None = None,
) -> AnalogFourWorkingKitComparison:
    """Read bounded files without writing originals or claiming chronology."""
    frames = AnalogFourWorkingKitFrames(
        *(
            _read_frame(role, path)
            for role, path in zip(AnalogFourWorkingKitRole, files.ordered(), strict=True)
        )
    )
    return compare_analog_four_working_kit(
        frames,
        track=track,
        evidence_origin=evidence_origin,
        baseline_label=baseline_label,
        changed_label=changed_label,
    )


def to_analog_four_working_kit_comparison_json(report: AnalogFourWorkingKitComparison) -> str:
    """JSON contains exact hashes/diffs and immutable no-authority declarations."""
    return json.dumps(asdict(report), indent=2, sort_keys=True)


__all__ = (
    "AnalogFourWorkingKitFiles",
    "build_analog_four_working_kit_comparison_report",
    "to_analog_four_working_kit_comparison_json",
)

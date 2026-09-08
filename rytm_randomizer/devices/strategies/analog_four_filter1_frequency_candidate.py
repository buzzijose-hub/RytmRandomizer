"""Filter 1 Frequency adapter for the shared offline saved-KIT renderer."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeGuard

from ...data.analog_four_sysex_calibration import A4_FILTER1_FREQUENCY_PARAMETER
from .analog_four_saved_kit_candidate import (
    AnalogFourSavedKitCandidateAppliedMutation as AnalogFourFilter1FrequencyCandidateAppliedMutation,
)
from .analog_four_saved_kit_candidate import (
    AnalogFourSavedKitCandidateMutation,
)
from .analog_four_saved_kit_candidate import (
    AnalogFourSavedKitCandidateResult as AnalogFourFilter1FrequencyCandidateResult,
)
from .analog_four_saved_kit_candidate import (
    render_analog_four_saved_kit_candidate,
)


@dataclass(frozen=True)
class AnalogFourFilter1FrequencyCandidateMutation:
    """One local-only Filter 1 Frequency edit for an A4 synth track."""

    track: int
    screen_value: str


def is_analog_four_filter1_frequency_candidate_mutation(
    value: object,
) -> TypeGuard[AnalogFourFilter1FrequencyCandidateMutation]:
    """Return whether ``value`` is the narrow offline mutation record."""

    return isinstance(value, AnalogFourFilter1FrequencyCandidateMutation)


def render_analog_four_filter1_frequency_candidate(
    source_sysex: bytes,
    mutations: Sequence[AnalogFourFilter1FrequencyCandidateMutation],
) -> AnalogFourFilter1FrequencyCandidateResult:
    """Render a local-only Filter 1 Frequency candidate through shared fields."""

    prepared: list[AnalogFourSavedKitCandidateMutation] = []
    for mutation in mutations:
        if not is_analog_four_filter1_frequency_candidate_mutation(mutation):
            raise TypeError(
                "mutations must contain AnalogFourFilter1FrequencyCandidateMutation records"
            )
        prepared.append(
            AnalogFourSavedKitCandidateMutation(
                parameter=A4_FILTER1_FREQUENCY_PARAMETER,
                track=mutation.track,
                screen_value=mutation.screen_value,
            )
        )
    return render_analog_four_saved_kit_candidate(source_sysex, prepared)


__all__ = [
    "AnalogFourFilter1FrequencyCandidateAppliedMutation",
    "AnalogFourFilter1FrequencyCandidateMutation",
    "AnalogFourFilter1FrequencyCandidateResult",
    "is_analog_four_filter1_frequency_candidate_mutation",
    "render_analog_four_filter1_frequency_candidate",
]

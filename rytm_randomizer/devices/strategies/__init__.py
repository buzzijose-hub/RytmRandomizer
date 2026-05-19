"""Per-device Strategy implementations satisfying the capability Protocols.

Each module in this subpackage implements one strategy slot
(``SnapshotDecoder``, ``MutationPlanner``, ``MessageRenderer``) for one
device family. The concrete ``Device`` classes (``AnalogRytmDevice`` and,
later, ``AnalogFourDevice``) compose strategies from here -- they do not
implement the bodies inline.

Single-responsibility: every strategy module owns exactly one capability
for one device. Dependencies fan one-way: ``devices/strategies/`` only
imports from ``snapshot/``, ``data/``, ``mock_midi``, ``guardrails/``,
and other ``strategies/`` modules; strategies never import from
``devices/analog_rytm.py`` or from each other across device families.
"""

from __future__ import annotations

from .analog_four_snapshot_decoder import (
    A4_CANDIDATE_KIT_TYPE_BYTE,
    AnalogFourKitSnapshot,
    AnalogFourSnapshotDecoder,
)
from .analog_four_mutation_planner import (
    MAX_A4_DEPTH,
    AnalogFourMutationPlan,
    AnalogFourMutationPlanner,
    AnalogFourPlanEvent,
)
from .analog_rytm_message_renderer import AnalogRytmMessageRenderer
from .analog_rytm_mutation_planner import (
    MAX_DEPTH,
    AnalogRytmMutationPlanner,
    RytmMutationPlan,
    RytmPlanEvent,
)
from .analog_rytm_snapshot_decoder import (
    RYTM_KIT_TYPE_BYTE,
    AnalogRytmSnapshotDecoder,
    RytmKitSnapshot,
)

__all__ = [
    "A4_CANDIDATE_KIT_TYPE_BYTE",
    "MAX_A4_DEPTH",
    "MAX_DEPTH",
    "RYTM_KIT_TYPE_BYTE",
    "AnalogFourKitSnapshot",
    "AnalogFourMutationPlan",
    "AnalogFourMutationPlanner",
    "AnalogFourPlanEvent",
    "AnalogFourSnapshotDecoder",
    "AnalogRytmMessageRenderer",
    "AnalogRytmMutationPlanner",
    "AnalogRytmSnapshotDecoder",
    "RytmKitSnapshot",
    "RytmMutationPlan",
    "RytmPlanEvent",
]

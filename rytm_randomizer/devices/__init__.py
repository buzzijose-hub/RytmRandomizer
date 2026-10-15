"""Device protocol + registry for cross-machine support.

The ``devices`` subpackage is the cross-machine abstraction layer added by
WS-S5 (per docs/SIMPLIFICATION_PLAN.md). It declares a single ``Device``
``Protocol`` and an in-memory registry so adding support for a new Elektron
device (e.g. PR #21's Analog Four) is "one new module that registers a
``Device`` instance", not "33 new top-level files that hand-roll the same
contract per device".

The existing Rytm-specific code under ``rytm_randomizer/engines``,
``rytm_randomizer/randomization``, etc. is unchanged. ``AnalogRytmDevice``
is a thin wrapper that re-exposes the existing Rytm operations through the
new Protocol so the registry is non-empty out of the box.
"""

from __future__ import annotations

# Importing concrete device modules triggers their import-time
# ``register_device`` calls so ``get_device("<device_id>")`` resolves out
# of the box. Side-effect import is the documented registry pattern.
from . import analog_four  # pyright: ignore[reportUnusedImport]  # noqa: F401 - registration
from . import analog_rytm  # pyright: ignore[reportUnusedImport]  # noqa: F401 - registration
from .analog_four import (
    AnalogFourFilter1FrequencyCandidateCapability,
    AnalogFourFilter1FrequencyCandidateMutation,
    AnalogFourFilter1FrequencyCandidateResult,
    AnalogFourNativeFieldCapability,
    get_analog_four_filter1_frequency_candidate_capability,
    get_analog_four_native_field_capability,
)
from .base import Device, MessageRenderer, MidiOutbox, MutationPlanner, SnapshotDecoder
from .registry import all_devices, get_device, register_device
from .saved_kit_capture import (
    RegisteredSavedKitCaptureCapability,
    SavedKitCaptureCapability,
    SavedKitCaptureFrame,
    resolve_saved_kit_capture_capability,
)
from .strategies import (
    AnalogFourKitSnapshot,
    RytmKitSnapshot,
    analog_four_snapshot_payload_fingerprint,
    rytm_snapshot_payload_fingerprint,
)
from .strategies.analog_four_f1_representation import native_to_screen as a4_f1_native_to_screen
from .strategies.analog_four_f1_representation import represent as a4_f1_represent
from .strategies.analog_four_kit_fields import encode_bipolar
from .strategies.analog_four_native_fields import (
    AnalogFourNativeAppliedMutation,
    AnalogFourNativeCandidateResult,
    AnalogFourNativeDomain,
    AnalogFourNativeEncoding,
    AnalogFourNativeField,
    AnalogFourNativeMutation,
    AnalogFourNativeReadback,
    AnalogFourNativeValue,
)
from .strategies.analog_four_native_transport import (
    AnalogFourNativeTransportChange,
    AnalogFourNativeTransportPreview,
    AnalogFourNativeTransportPreviewDict,
    preview_analog_four_native_cc_transport,
)
from .strategies.analog_four_saved_kit_candidate import (
    validate_analog_four_candidate_source as validate_analog_four_indexed_source,
)
from .strategies.analog_four_working_kit_comparison import (
    AnalogFourExperimentEvidenceOrigin,
    AnalogFourWorkingKitComparison,
    AnalogFourWorkingKitFrames,
    compare_analog_four_working_kit,
)
from .strategies.analog_rytm_kit_fields import RytmKit

__all__ = [
    "AnalogFourNativeTransportChange",
    "AnalogFourNativeTransportPreview",
    "AnalogFourNativeTransportPreviewDict",
    "preview_analog_four_native_cc_transport",
    "Device",
    "AnalogFourExperimentEvidenceOrigin",
    "AnalogFourWorkingKitComparison",
    "AnalogFourWorkingKitFrames",
    "compare_analog_four_working_kit",
    "RytmKit",
    "encode_bipolar",
    "AnalogFourFilter1FrequencyCandidateCapability",
    "AnalogFourFilter1FrequencyCandidateMutation",
    "AnalogFourFilter1FrequencyCandidateResult",
    "AnalogFourKitSnapshot",
    "AnalogFourNativeAppliedMutation",
    "AnalogFourNativeCandidateResult",
    "AnalogFourNativeDomain",
    "AnalogFourNativeEncoding",
    "AnalogFourNativeField",
    "AnalogFourNativeFieldCapability",
    "AnalogFourNativeMutation",
    "AnalogFourNativeReadback",
    "AnalogFourNativeValue",
    "MessageRenderer",
    "MidiOutbox",
    "MutationPlanner",
    "RegisteredSavedKitCaptureCapability",
    "RytmKitSnapshot",
    "SavedKitCaptureCapability",
    "SavedKitCaptureFrame",
    "SnapshotDecoder",
    "all_devices",
    "a4_f1_native_to_screen",
    "a4_f1_represent",
    "analog_four_snapshot_payload_fingerprint",
    "get_device",
    "get_analog_four_filter1_frequency_candidate_capability",
    "get_analog_four_native_field_capability",
    "register_device",
    "resolve_saved_kit_capture_capability",
    "rytm_snapshot_payload_fingerprint",
    "validate_analog_four_indexed_source",
]

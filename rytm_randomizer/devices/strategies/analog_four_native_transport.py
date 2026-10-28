"""Exact bounded native-to-CC7 review; no transport events or output authority."""

from __future__ import annotations

from ...data.analog_four_display import (
    ANALOG_FOUR_PARAMETER_DISPLAY,
    DISPLAY_SCALE_BIPOLAR,
    DISPLAY_SCALE_UNIPOLAR,
    make_a4_patch_value,
    midi_to_a4_signed_screen,
    signed_screen_to_a4_midi,
)
from ...data.analog_four_kit_fields import A4_BIPOLAR_FIELDS
from ...data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC
from ...data.analog_four_native_transport import (
    A4_NATIVE_CC7_BINDINGS,
    A4_NATIVE_TRANSPORT_CONFLICTS,
    A4_NATIVE_TRANSPORT_CONTRACT_REASON,
    A4_NATIVE_TRANSPORT_ENUM_REASON,
    A4_NATIVE_TRANSPORT_PAIRED_REASON,
    A4_NATIVE_TRANSPORT_UNMAPPED_REASON,
    AnalogFourNativeTransportChange,
    AnalogFourNativeTransportPreview,
    AnalogFourNativeTransportPreviewDict,
)
from ...guardrails.input_validation import require_int, require_text
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ..analog_four import get_analog_four_native_field_capability
from .analog_four_kit_fields import decode_bipolar, encode_bipolar
from .analog_four_native_fields import (
    AnalogFourNativeEncoding,
    AnalogFourNativeMutation,
    AnalogFourNativeValue,
)

_logger = get_logger(__name__)


def _unsupported_reason(value: AnalogFourNativeValue) -> str | None:
    conflict = A4_NATIVE_TRANSPORT_CONFLICTS.get(value.parameter)
    if conflict is not None:
        return conflict.blocking_reason
    encoding = value.metadata.native_encoding
    if encoding in (
        AnalogFourNativeEncoding.Q8_8,
        AnalogFourNativeEncoding.MOD_DEPTH,
        AnalogFourNativeEncoding.TUNE,
        AnalogFourNativeEncoding.FINE,
    ):
        return A4_NATIVE_TRANSPORT_PAIRED_REASON
    if encoding is AnalogFourNativeEncoding.ENUM:
        return A4_NATIVE_TRANSPORT_ENUM_REASON
    if value.parameter not in A4_NATIVE_CC7_BINDINGS:
        return A4_NATIVE_TRANSPORT_UNMAPPED_REASON
    manual_name = A4_NATIVE_CC7_BINDINGS[value.parameter]
    mapping = ANALOG_FOUR_SYNTH_TRACK_CC[manual_name]
    display = ANALOG_FOUR_PARAMETER_DISPLAY[manual_name]
    bipolar = value.parameter in A4_BIPOLAR_FIELDS
    expected = AnalogFourNativeEncoding.BIPOLAR if bipolar else AnalogFourNativeEncoding.U7
    if (
        encoding is not expected
        or mapping.cc_msb is None
        or mapping.cc_lsb is not None
        or not display.transport_ready
        or display.display_scale != (DISPLAY_SCALE_BIPOLAR if bipolar else DISPLAY_SCALE_UNIPOLAR)
    ):
        return A4_NATIVE_TRANSPORT_CONTRACT_REASON
    return None


def _project_cc7(value: AnalogFourNativeValue) -> tuple[int, bool]:
    native = require_int(value.encoded_native, "encoded_native")
    if value.parameter in A4_BIPOLAR_FIELDS:
        cc7 = signed_screen_to_a4_midi(decode_bipolar(native))
        return cc7, encode_bipolar(midi_to_a4_signed_screen(cc7)) == native
    projected = make_a4_patch_value(A4_NATIVE_CC7_BINDINGS[value.parameter], screen_target=native)
    cc7 = require_int(projected.midi_value, "projected CC7")
    return cc7, cc7 == native


def _change_row(
    before: AnalogFourNativeValue, after: AnalogFourNativeValue
) -> AnalogFourNativeTransportChange:
    reason = _unsupported_reason(before) or _unsupported_reason(after)
    if reason is not None:
        return AnalogFourNativeTransportChange(
            before.track,
            before.parameter,
            before.encoded_native,
            after.encoded_native,
            None,
            None,
            None,
            False,
            (reason,),
        )
    before_cc7, before_exact = _project_cc7(before)
    after_cc7, after_exact = _project_cc7(after)
    if not before_exact or not after_exact:
        return AnalogFourNativeTransportChange(
            before.track,
            before.parameter,
            before.encoded_native,
            after.encoded_native,
            None,
            None,
            None,
            False,
            (A4_NATIVE_TRANSPORT_CONTRACT_REASON,),
        )
    return AnalogFourNativeTransportChange(
        before.track,
        before.parameter,
        before.encoded_native,
        after.encoded_native,
        ANALOG_FOUR_SYNTH_TRACK_CC[A4_NATIVE_CC7_BINDINGS[before.parameter]].cc_msb,
        before_cc7,
        after_cc7,
        True,
        (),
    )


def preview_analog_four_native_cc_transport(
    source_frame: bytes, mutations: tuple[AnalogFourNativeMutation, ...]
) -> AnalogFourNativeTransportPreview:
    """Re-render indexed native changes and describe only established CC7 scalars.

    Native-invalid/protected requests fail canonical rendering. Valid native
    changes with unsupported transport remain visible, without any CC scalar.
    No-op requests are omitted; even complete mappings remain offline reviews.
    """
    try:
        if type(source_frame) is not bytes:
            raise TypeError("source_frame must be bytes")
        if type(mutations) is not tuple:
            raise TypeError("mutations must be a tuple of native mutation records")
        for mutation in mutations:
            if type(mutation) is not AnalogFourNativeMutation:
                raise TypeError("mutations must contain AnalogFourNativeMutation records")
            require_int(mutation.track, "track")
            require_int(mutation.encoded_native, "encoded_native")
            require_text(mutation.parameter, "parameter")
        rendered = get_analog_four_native_field_capability().render_native_fields(
            source_frame, mutations
        )
        preview = AnalogFourNativeTransportPreview(
            tuple(
                _change_row(applied.source, applied.rendered)
                for applied in rendered.applied_mutations
                if applied.source.encoded_native != applied.rendered.encoded_native
            )
        )
    except (TypeError, ValueError):
        get_metrics().record_error("a4_native_transport_invalid_request")
        _logger.warning("a4_native_transport_refused", extra={"reason": "invalid_native_request"})
        raise
    if not preview.mapping_complete:
        get_metrics().record_error("a4_native_transport_mapping_incomplete")
    _logger.info(
        "a4_native_transport_reviewed",
        extra={"change_count": len(preview.changes), "mapping_complete": preview.mapping_complete},
    )
    return preview


__all__ = [
    "AnalogFourNativeTransportChange",
    "AnalogFourNativeTransportPreview",
    "AnalogFourNativeTransportPreviewDict",
    "preview_analog_four_native_cc_transport",
]

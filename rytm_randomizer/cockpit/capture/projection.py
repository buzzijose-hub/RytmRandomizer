"""Pure versioned Rytm value views for exact historical recipe replay."""

from __future__ import annotations

from dataclasses import replace

from ...data.analog_rytm_midi import (
    RYTM_CAPTURE_PROJECTION_V1,
    RYTM_CAPTURE_PROJECTIONS,
    RytmCaptureProjection,
)
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ..data import Snapshot

_logger = get_logger(__name__)


def project_rytm_capture_snapshot(
    snapshot: Snapshot, projection: RytmCaptureProjection
) -> Snapshot:
    """Keep V1's mapped domain; never infer a version from candidate values.

    Raw retained frames, snapshot identity and unrelated values stay exact.
    V2 is the current capture domain. This view grants no output authority.
    """
    if projection not in RYTM_CAPTURE_PROJECTIONS:
        get_metrics().record_error("rytm_capture_projection_invalid")
        _logger.warning("rytm_capture_projection_refused", extra={"reason": "unknown_version"})
        raise ValueError("unsupported Rytm capture projection")
    legacy = projection == RYTM_CAPTURE_PROJECTION_V1
    result = (
        replace(
            snapshot,
            pads=tuple(
                replace(
                    pad,
                    params={key: value for key, value in pad.params.items() if key != "sample_bit"},
                )
                for pad in snapshot.pads
            ),
        )
        if legacy
        else snapshot
    )
    _logger.debug(
        "rytm_capture_projection_selected",
        extra={"projection": projection, "legacy_domain": legacy, "pad_count": len(result.pads)},
    )
    return result

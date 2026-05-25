"""Guardrail Profile resolver (WS-W Layer 4).

The resolver is the bridge between a *validated* Guardrail Profile and the
randomizer engines. It produces a :class:`ResolvedBounds` value object that
maps ``(pad, parameter) -> (low, high, GuardrailClass)`` -- the effective
mutation envelope the engines clamp against.

Two failure modes (spec section 16):

* **Lifecycle-state mismatch -> hard refuse.** If a profile's
  :class:`ProfileState` does not meet the mode's minimum (e.g. a
  ``VALIDATED`` profile asked to drive ``LIVE_SAFE`` performance), the
  resolver raises :class:`GuardrailResolutionError`. The session does
  not start.
* **Per-bound conflict -> drop to ``LOCKED_DEFAULT``.** When a bound's
  range, intersected with the hardware envelope, is empty (or the
  parameter / pad does not exist on the hardware, or the bound is
  already ``FORBIDDEN``), that single parameter does not mutate. The
  rest of the profile still resolves -- the session runs.

The resolved bounds are always a *narrowing* of the hardware envelope from
``rytm_randomizer/data/``; the resolver can never widen them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, ClassVar

from ..observability.errors import BoundaryError
from ..observability.logging import get_logger
from .schema import GuardrailBound, GuardrailClass, GuardrailProfile, ProfileState
from .validation import PAD_PROFILE_KEY

__all__ = [
    "GuardrailResolutionError",
    "MODE_LIVE_SAFE",
    "MODE_STUDIO_DISCOVERY",
    "MODE_EXPERIMENTAL",
    "MODE_STATE_REQUIREMENTS",
    "ResolvedBound",
    "ResolvedBounds",
    "default_hardware_ranges_for_pad",
    "resolve",
]


_logger = get_logger(__name__)


MODE_LIVE_SAFE: str = "LIVE_SAFE"
MODE_STUDIO_DISCOVERY: str = "STUDIO_DISCOVERY"
MODE_EXPERIMENTAL: str = "EXPERIMENTAL"


MODE_STATE_REQUIREMENTS: Mapping[str, frozenset[ProfileState]] = MappingProxyType(
    {
        # LIVE_SAFE performance mode: only a LIVE_APPROVED profile may drive it
        # (the spec section 4.3 promotion path). STUDIO_TESTED is one rung
        # below; it must NOT be used live until hardware-validated.
        MODE_LIVE_SAFE: frozenset({ProfileState.LIVE_APPROVED}),
        # STUDIO_DISCOVERY: any profile that has cleared the validator (i.e.
        # is not still a DRAFT and not REJECTED/ARCHIVED) may drive it.
        MODE_STUDIO_DISCOVERY: frozenset(
            {
                ProfileState.VALIDATED,
                ProfileState.STUDIO_TESTED,
                ProfileState.LIVE_APPROVED,
            }
        ),
        # EXPERIMENTAL: same baseline as STUDIO_DISCOVERY -- it is a studio
        # mode with explicit opt-in; the lifecycle requirement is the same.
        MODE_EXPERIMENTAL: frozenset(
            {
                ProfileState.VALIDATED,
                ProfileState.STUDIO_TESTED,
                ProfileState.LIVE_APPROVED,
            }
        ),
    }
)
"""Lifecycle states that satisfy each resolver mode.

Per spec section 4.3 + 16: the resolver hard-refuses (does not start a
session) when a profile's state is not in the set for the requested mode.
"""


class GuardrailResolutionError(BoundaryError):
    """Raised by :func:`resolve` when a profile cannot drive the requested mode.

    A member of the
    :class:`~rytm_randomizer.observability.errors.BoundaryError` family so
    a caller can ``except BoundaryError`` and catch every guardrails
    boundary failure (validation + resolution) uniformly.
    """

    fingerprint: ClassVar[str] = "guardrail.resolve.failed"


@dataclass(frozen=True)
class ResolvedBound:
    """A single resolved ``(low, high, class)`` for one ``(pad, parameter)``.

    ``guardrail_class`` is the class assigned after intersection: a bound
    that conflicted with the hardware envelope drops to
    :attr:`GuardrailClass.LOCKED_DEFAULT` even if the profile asked for a
    mutating class.
    """

    low: int
    high: int
    guardrail_class: GuardrailClass


@dataclass(frozen=True)
class ResolvedBounds:
    """The effective per-pad/param bounds for a profile + mode.

    Wraps a frozen ``Mapping[tuple[int, str], ResolvedBound]`` so the table
    is addressable by ``(pad, parameter)`` and immutable once constructed.

    The engines hold a reference to this object via their optional
    ``resolved_bounds`` parameter; when set, they clamp each parameter
    value to :py:meth:`clamp_value` before sending it. When ``None``, the
    engines fall back to the hardware-only ``data/`` envelope (full
    backward compatibility).
    """

    by_pad_param: Mapping[tuple[int, str], ResolvedBound]
    mode: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "by_pad_param", MappingProxyType(dict(self.by_pad_param)))

    def get(self, pad: int, parameter: str) -> ResolvedBound | None:
        """Return the bound for ``(pad, parameter)`` or ``None`` if absent."""

        return self.by_pad_param.get((pad, parameter))

    def clamp_value(self, pad: int, parameter: str, value: int) -> int | None:
        """Clamp ``value`` to the resolved envelope for ``(pad, parameter)``.

        Returns ``None`` when the parameter is :attr:`GuardrailClass.LOCKED_DEFAULT`
        or :attr:`GuardrailClass.FORBIDDEN` -- the engine should treat that
        as "do not send this CC". Returns the clamped int otherwise. When
        the ``(pad, parameter)`` is not in the table at all the value is
        passed through unchanged: the resolver only narrows; it does not
        invent constraints.
        """

        bound = self.by_pad_param.get((pad, parameter))
        if bound is None:
            return value
        if bound.guardrail_class in (
            GuardrailClass.LOCKED_DEFAULT,
            GuardrailClass.FORBIDDEN,
        ):
            return None
        return max(bound.low, min(bound.high, value))


# ---------------------------------------------------------------------------
# Default hardware-range adapter
# ---------------------------------------------------------------------------


def default_hardware_ranges_for_pad(pad: int) -> Mapping[str, tuple[int, int]]:
    """Return the hardware ``safe`` table for the default profile of ``pad``.

    The :data:`rytm_randomizer.guardrails.validation.PAD_PROFILE_KEY`
    mapping points each pad at the canonical V1.34 profile; the returned
    table is that profile's ``safe`` dict (a static
    ``Mapping[str, (low, high)]``). Used as the ``hardware_ranges_for_pad``
    callback in :func:`resolve` when callers do not supply their own.

    Lazily imports :mod:`rytm_randomizer.data` so this module stays a
    leaf-or-near-leaf at import time -- the architecture conformance tests
    enforce that the guardrails package depends on ``data/`` but does not
    drag the runtime into ``import`` graphs.
    """

    profile_key = PAD_PROFILE_KEY.get(pad)
    if profile_key is None:
        return {}
    from ..data import PROFILES  # noqa: PLC0415 - lazy import per docstring

    profile = PROFILES.get(profile_key)
    if profile is None:  # pragma: no cover - defensive
        return {}
    return profile["safe"]


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------


def _check_lifecycle(profile: GuardrailProfile, mode: str) -> None:
    """Raise :class:`GuardrailResolutionError` on a lifecycle-state mismatch."""

    allowed = MODE_STATE_REQUIREMENTS.get(mode)
    if allowed is None:
        raise GuardrailResolutionError(
            "unknown resolver mode",
            context={
                "mode": mode,
                "known_modes": sorted(MODE_STATE_REQUIREMENTS),
            },
        )
    if profile.state not in allowed:
        raise GuardrailResolutionError(
            "profile lifecycle state does not permit requested mode",
            context={
                "mode": mode,
                "profile_state": profile.state.value,
                "required_one_of": sorted(s.value for s in allowed),
                "profile_name": profile.provenance.profile_name,
            },
        )


def _resolve_one(
    bound: GuardrailBound,
    hardware_range: tuple[int, int] | None,
) -> ResolvedBound:
    """Intersect ``bound`` with the hardware range -> a :class:`ResolvedBound`.

    The hardware range is the authoritative envelope; if it is ``None``
    (parameter does not exist on the pad) OR the intersection is empty OR
    the bound is already ``FORBIDDEN``, the resolved class drops to
    ``LOCKED_DEFAULT`` (or stays ``FORBIDDEN`` for forbidden bounds), and
    the conflict is logged at WARNING via the package logger.

    Returns a :class:`ResolvedBound` for the *every* path (including the
    LOCKED_DEFAULT path) so the engines have one uniform table to consult.
    """

    if bound.guardrail_class is GuardrailClass.FORBIDDEN:
        # FORBIDDEN stays FORBIDDEN; the range becomes degenerate (low==high
        # at the bound's nominal low) so a downstream consumer that ignores
        # the class still sees a tight range.
        return ResolvedBound(
            low=bound.low,
            high=bound.low,
            guardrail_class=GuardrailClass.FORBIDDEN,
        )

    if hardware_range is None:
        _logger.warning(
            "guardrails.resolve conflict: parameter not on pad",
            extra={
                "kind": "guardrails_resolve_conflict",
                "reason": "parameter_not_on_pad",
                "pad": bound.pad,
                "parameter": bound.parameter,
                "requested_class": bound.guardrail_class.value,
            },
        )
        return ResolvedBound(
            low=bound.low,
            high=bound.high,
            guardrail_class=GuardrailClass.LOCKED_DEFAULT,
        )

    hw_low, hw_high = hardware_range
    intersected_low = max(bound.low, hw_low)
    intersected_high = min(bound.high, hw_high)

    if intersected_low > intersected_high:
        _logger.warning(
            "guardrails.resolve conflict: empty intersection",
            extra={
                "kind": "guardrails_resolve_conflict",
                "reason": "empty_intersection",
                "pad": bound.pad,
                "parameter": bound.parameter,
                "bound_range": (bound.low, bound.high),
                "hardware_range": (hw_low, hw_high),
            },
        )
        # Drop to LOCKED_DEFAULT with the hardware range so the entry
        # still has a coherent (low, high) pair for inspection.
        return ResolvedBound(
            low=hw_low,
            high=hw_high,
            guardrail_class=GuardrailClass.LOCKED_DEFAULT,
        )

    # The bound's mutating class survives, narrowed to the intersection.
    # LOCKED_DEFAULT bounds keep LOCKED_DEFAULT (they were not mutating to
    # begin with) so the engines uniformly skip them.
    return ResolvedBound(
        low=intersected_low,
        high=intersected_high,
        guardrail_class=bound.guardrail_class,
    )


def resolve(
    profile: GuardrailProfile,
    mode: str,
    *,
    hardware_ranges_for_pad: Callable[[int], Mapping[str, tuple[int, int]]] | None = None,
) -> ResolvedBounds:
    """Resolve ``profile`` into :class:`ResolvedBounds` for ``mode``.

    Steps:

    1. Hard-refuse if ``profile.state`` does not satisfy
       :data:`MODE_STATE_REQUIREMENTS` for ``mode`` -- raises
       :class:`GuardrailResolutionError`.
    2. For every :class:`GuardrailBound`, intersect its range with the
       hardware range returned by ``hardware_ranges_for_pad``. Empty
       intersection or unknown parameter drops the bound to
       :attr:`GuardrailClass.LOCKED_DEFAULT`; the rest still resolve.

    The ``hardware_ranges_for_pad`` callback lets tests inject custom
    hardware envelopes. When omitted, :func:`default_hardware_ranges_for_pad`
    is used.

    The returned :class:`ResolvedBounds` is always ⊆ the hardware envelope
    -- the resolver only narrows.
    """

    _check_lifecycle(profile, mode)

    if hardware_ranges_for_pad is None:
        hardware_ranges_for_pad = default_hardware_ranges_for_pad

    table: dict[tuple[int, str], ResolvedBound] = {}
    # Cache the hardware-ranges-per-pad lookups so the callback runs once
    # per pad even when many bounds touch the same pad.
    hw_cache: dict[int, Mapping[str, tuple[int, int]]] = {}

    for bound in profile.bounds:
        pad_ranges = hw_cache.get(bound.pad)
        if pad_ranges is None:
            pad_ranges = hardware_ranges_for_pad(bound.pad)
            hw_cache[bound.pad] = pad_ranges
        hw_range = pad_ranges.get(bound.parameter)
        table[(bound.pad, bound.parameter)] = _resolve_one(bound, hw_range)

    _logger.info(
        "guardrails.resolve",
        extra={
            "kind": "guardrails_resolve",
            "mode": mode,
            "profile_name": profile.provenance.profile_name,
            "profile_state": profile.state.value,
            "bound_count": len(table),
        },
    )
    return ResolvedBounds(by_pad_param=table, mode=mode)

"""Passive reference/discovery slider policy for style routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

STYLE_DISCOVERY_AMOUNT_MIN: Final[int] = 0
STYLE_DISCOVERY_AMOUNT_MAX: Final[int] = 100
DEFAULT_STYLE_DISCOVERY_AMOUNT: Final[int] = 45


@dataclass(frozen=True)
class StyleDiscoveryBand:
    """One bounded band in the reference/discovery slider."""

    band: str
    min_amount: int
    max_amount: int
    zone_limit: int
    candidate_limit: int
    machine_switching_allowed: bool
    mutation_depth: str
    summary: str


@dataclass(frozen=True)
class StyleDiscoveryPolicy:
    """Resolved slider policy for one requested discovery amount."""

    amount: int
    band: str
    zone_limit: int
    candidate_limit: int
    machine_switching_allowed: bool
    mutation_depth: str
    summary: str


STYLE_DISCOVERY_BANDS: Final[tuple[StyleDiscoveryBand, ...]] = (
    StyleDiscoveryBand(
        band="reference",
        min_amount=0,
        max_amount=20,
        zone_limit=2,
        candidate_limit=1,
        machine_switching_allowed=False,
        mutation_depth="micro",
        summary="preserve current machines and apply tiny style pressure",
    ),
    StyleDiscoveryBand(
        band="balanced",
        min_amount=21,
        max_amount=60,
        zone_limit=3,
        candidate_limit=3,
        machine_switching_allowed=False,
        mutation_depth="groove",
        summary="keep the live kit identity while widening style movement",
    ),
    StyleDiscoveryBand(
        band="discovery",
        min_amount=61,
        max_amount=85,
        zone_limit=4,
        candidate_limit=5,
        machine_switching_allowed=True,
        mutation_depth="strong",
        summary="allow broader compatible candidates and stronger zone movement",
    ),
    StyleDiscoveryBand(
        band="wild_discovery",
        min_amount=86,
        max_amount=100,
        zone_limit=5,
        candidate_limit=7,
        machine_switching_allowed=True,
        mutation_depth="wild",
        summary="maximum guardrailed exploration inside compatibility limits",
    ),
)


def style_discovery_policy(
    amount: int = DEFAULT_STYLE_DISCOVERY_AMOUNT,
) -> StyleDiscoveryPolicy:
    """Return the passive slider policy for ``amount`` in the 0-100 range."""

    if amount < STYLE_DISCOVERY_AMOUNT_MIN or amount > STYLE_DISCOVERY_AMOUNT_MAX:
        raise ValueError("discovery amount must be between 0 and 100")
    for band in STYLE_DISCOVERY_BANDS:
        if band.min_amount <= amount <= band.max_amount:
            return StyleDiscoveryPolicy(
                amount=amount,
                band=band.band,
                zone_limit=band.zone_limit,
                candidate_limit=band.candidate_limit,
                machine_switching_allowed=band.machine_switching_allowed,
                mutation_depth=band.mutation_depth,
                summary=band.summary,
            )
    raise ValueError(f"no discovery band covers amount {amount}")


__all__ = [
    "DEFAULT_STYLE_DISCOVERY_AMOUNT",
    "STYLE_DISCOVERY_AMOUNT_MAX",
    "STYLE_DISCOVERY_AMOUNT_MIN",
    "STYLE_DISCOVERY_BANDS",
    "StyleDiscoveryBand",
    "StyleDiscoveryPolicy",
    "style_discovery_policy",
]

"""Device-neutral include targets and lock-aware mutation scope.

Explicit targets are include-lists. An empty include-list preserves the
historical all-item behavior, and locks are always a deny-list applied last:
``(targets or available) - locks``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from ..guardrails.identifier_sets import validated_id_set


@dataclass(frozen=True)
class MutationScope:
    """One device's explicit include-list plus its lock deny-list."""

    target_ids: frozenset[int] = frozenset()
    locked_ids: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        for field_name, values in (
            ("target_ids", self.target_ids),
            ("locked_ids", self.locked_ids),
        ):
            object.__setattr__(
                self,
                field_name,
                validated_id_set(values, field_name=field_name),
            )

    def effective_ids(
        self,
        available_ids: Iterable[int],
    ) -> frozenset[int]:
        """Resolve ``(targets or available) - locks`` over current items."""

        available = frozenset(available_ids)
        included = self.target_ids or available
        return frozenset((included & available) - self.locked_ids)

    def validated_effective_ids(
        self,
        available_ids: Iterable[int],
        *,
        item_label: str,
    ) -> frozenset[int]:
        """Reject unknown scope ids, then resolve the canonical equation."""

        available = frozenset(available_ids)
        unknown_targets = sorted(self.target_ids - available)
        unknown_locks = sorted(self.locked_ids - available)
        if unknown_targets:
            raise ValueError(f"target {item_label} ids are unavailable: {unknown_targets}")
        if unknown_locks:
            raise ValueError(f"locked {item_label} ids are unavailable: {unknown_locks}")
        return self.effective_ids(available)


def registered_mutation_ids(device_id: str) -> frozenset[int]:
    """Resolve the target domain from the canonical registered Device.

    The import is deliberately lazy: Device composition imports MutationScope
    while the registry is being initialized. Domain resolution happens only
    after composition, when a DTO or stage policy validates actual inputs.
    """
    from ..devices import get_device

    device = get_device(device_id)
    return frozenset(range(1, device.track_count + 1))


DEFAULT_MUTATION_SCOPE: Final[MutationScope] = MutationScope()
"""Immutable no-explicit-target/no-lock scope used by planner defaults."""


__all__ = ["DEFAULT_MUTATION_SCOPE", "MutationScope", "registered_mutation_ids"]

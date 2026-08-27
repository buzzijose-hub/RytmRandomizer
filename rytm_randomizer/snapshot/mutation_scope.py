"""Device-neutral include targets and lock-aware mutation scope.

Explicit targets are include-lists. An empty include-list preserves the
historical all-item behavior, and locks are always a deny-list applied last:
``(targets or available) - locks``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final


def _validated_positive_ids(values: Iterable[object], *, field_name: str) -> frozenset[int]:
    normalized = frozenset(values)
    invalid: list[object] = []
    valid: set[int] = set()
    for value in normalized:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            invalid.append(value)
        else:
            valid.add(value)
    if invalid:
        rendered = sorted(repr(value) for value in invalid)
        raise ValueError(f"{field_name} must contain positive integer ids; got {rendered}")
    return frozenset(valid)


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
                _validated_positive_ids(values, field_name=field_name),
            )

    def effective_ids(
        self,
        available_ids: Iterable[int],
        *,
        item_label: str,
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
        return self.effective_ids(available, item_label=item_label)


DEFAULT_MUTATION_SCOPE: Final[MutationScope] = MutationScope()
"""Immutable no-explicit-target/no-lock scope used by planner defaults."""


__all__ = ["DEFAULT_MUTATION_SCOPE", "MutationScope"]

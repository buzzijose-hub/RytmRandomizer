"""Immutable parameter-cell selection; null means legacy-all, empty means none."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypedDict, cast

from ...guardrails.input_validation import require_int, require_text

_MAX_PARAMETER_KEY: Final[int] = 128
_MAX_PARAMETER_CELLS: Final[int] = 2048


class ParameterCellDict(TypedDict):
    item_id: int
    parameter_key: str


@dataclass(frozen=True, order=True)
class ParameterCell:
    item_id: int
    parameter_key: str

    def __post_init__(self) -> None:
        if require_int(self.item_id, "item_id") < 1:
            raise ValueError("parameter item_id must be positive")
        key = require_text(self.parameter_key, "parameter_key")
        if not key.strip() or len(key) > _MAX_PARAMETER_KEY:
            raise ValueError("parameter_key must be nonempty and bounded")

    def to_dict(self) -> ParameterCellDict:
        return {"item_id": self.item_id, "parameter_key": self.parameter_key}


@dataclass(frozen=True)
class ParameterSelection:
    """An explicit include-list, independent of pad locks or output authority."""

    cells: tuple[ParameterCell, ...] | None = None

    def __post_init__(self) -> None:
        if self.cells is None:
            return
        if not isinstance(self.cells, tuple) or any(
            not isinstance(cell, ParameterCell) for cell in self.cells
        ):
            raise TypeError("parameter cells must be an immutable typed tuple")
        if len(self.cells) > _MAX_PARAMETER_CELLS or len(set(self.cells)) != len(self.cells):
            raise ValueError("parameter cells must be bounded and unique")
        object.__setattr__(self, "cells", tuple(sorted(self.cells)))

    def includes(self, item_id: int, parameter_key: str) -> bool:
        return self.cells is None or ParameterCell(item_id, parameter_key) in self.cells

    def to_list(self) -> list[ParameterCellDict] | None:
        return None if self.cells is None else [cell.to_dict() for cell in self.cells]

    @classmethod
    def parse(cls, value: object) -> ParameterSelection:
        if value is None:
            return cls()
        if not isinstance(value, list) or len(value) > _MAX_PARAMETER_CELLS:
            raise ValueError("parameter_cells must be null or a bounded array")
        cells: list[ParameterCell] = []
        for raw in cast(list[object], value):
            if not isinstance(raw, dict) or set(raw) != {"item_id", "parameter_key"}:
                raise ValueError("parameter cell requires exactly item_id and parameter_key")
            cell = cast(dict[str, object], raw)
            cells.append(
                ParameterCell(
                    require_int(cell["item_id"], "item_id"),
                    require_text(cell["parameter_key"], "parameter_key"),
                )
            )
        return cls(tuple(cells))


class PerformanceParameterControl(TypedDict):
    device_id: str
    item_id: int
    machine: str
    parameter_key: str
    page: str
    name: str
    value: int | None
    display_value: str | None
    minimum: int | None
    maximum: int | None
    native_precision: str
    mutation_supported: bool
    send_supported: bool
    protected: bool
    reasons: list[str]
    evidence_level: str


__all__ = [
    "ParameterCell",
    "ParameterCellDict",
    "ParameterSelection",
    "PerformanceParameterControl",
]

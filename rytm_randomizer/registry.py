"""Unified passive registry view for existing scaffold metadata."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Final, TypedDict, cast

from .commands import COMMANDS
from .profiles import GROUP_PROFILE_METADATA
from .scenes import SCENE_COMMANDS

REGISTRY_SECTIONS: Final[tuple[str, ...]] = ("commands", "scenes", "group_profiles")


class RegistrySectionReport(TypedDict):
    exists: bool
    section: str
    items: Mapping[str, Mapping[str, object]] | None
    count: int


class RegistryItemReport(TypedDict):
    exists: bool
    section_exists: bool
    section: str
    key: str
    metadata: Mapping[str, object] | None


class RegistrySummaryReport(TypedDict):
    sections: tuple[str, ...]
    section_counts: dict[str, int]
    total_items: int


def _source_registry() -> dict[str, Mapping[str, Mapping[str, object]]]:
    return {
        "commands": cast(Mapping[str, Mapping[str, object]], COMMANDS),
        "scenes": cast(Mapping[str, Mapping[str, object]], SCENE_COMMANDS),
        "group_profiles": cast(
            Mapping[str, Mapping[str, object]],
            GROUP_PROFILE_METADATA,
        ),
    }


def _normalize_section(section_name: object) -> str:
    return str(section_name).lower()


def _normalize_key(section_name: str, key: object) -> str:
    if section_name in ("commands", "scenes"):
        return str(key).upper()
    return str(key)


def build_registry() -> dict[str, Mapping[str, Mapping[str, object]]]:
    """Return a copied registry containing existing passive metadata sections."""
    return deepcopy(_source_registry())


def list_registry_sections() -> tuple[str, ...]:
    """Return the supported passive registry section names."""
    return REGISTRY_SECTIONS


def get_registry_section(section_name: object) -> RegistrySectionReport:
    """Return a copied registry section or passive not-found result."""
    normalized_section = _normalize_section(section_name)
    registry = _source_registry()
    section = registry.get(normalized_section)

    if section is None:
        return {
            "exists": False,
            "section": normalized_section,
            "items": None,
            "count": 0,
        }

    items = deepcopy(section)
    return {
        "exists": True,
        "section": normalized_section,
        "items": items,
        "count": len(items),
    }


def get_registry_item(section_name: object, key: object) -> RegistryItemReport:
    """Return a copied registry item or passive not-found result."""
    normalized_section = _normalize_section(section_name)
    normalized_key = _normalize_key(normalized_section, key)
    section = _source_registry().get(normalized_section)

    if section is None:
        return {
            "exists": False,
            "section_exists": False,
            "section": normalized_section,
            "key": normalized_key,
            "metadata": None,
        }

    metadata = section.get(normalized_key)
    if metadata is None:
        return {
            "exists": False,
            "section_exists": True,
            "section": normalized_section,
            "key": normalized_key,
            "metadata": None,
        }

    return {
        "exists": True,
        "section_exists": True,
        "section": normalized_section,
        "key": normalized_key,
        "metadata": deepcopy(metadata),
    }


def summarize_registry() -> RegistrySummaryReport:
    """Return a passive summary of section counts and total item count."""
    registry = _source_registry()
    section_counts = {
        section_name: len(registry[section_name]) for section_name in REGISTRY_SECTIONS
    }
    return {
        "sections": REGISTRY_SECTIONS,
        "section_counts": section_counts,
        "total_items": sum(section_counts.values()),
    }

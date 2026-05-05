"""Passive registry audit reports."""

from .preview import SAFETY_SUMMARY
from .validation import validate_command_registry


def audit_command_registry(registry, registry_name="COMMANDS"):
    """Return a passive summary report for a command metadata registry."""
    categories = {}
    scopes = {}
    pads = {}

    all_non_executable = True
    all_scaffold_only = True

    for metadata in registry.values():
        if not isinstance(metadata, dict):
            all_non_executable = False
            all_scaffold_only = False
            continue

        _increment(categories, metadata.get("type"))
        _increment(scopes, metadata.get("scope"))

        pad = metadata.get("pad")
        if pad in (1, 2, 3, 4):
            _increment(pads, pad)

        if metadata.get("executable") is not False:
            all_non_executable = False

        if metadata.get("scaffold_only") is not True:
            all_scaffold_only = False

    return {
        "registry_name": registry_name,
        "command_count": len(registry),
        "validation": validate_command_registry(registry),
        "categories": categories,
        "scopes": scopes,
        "pads": pads,
        "all_non_executable": all_non_executable,
        "all_scaffold_only": all_scaffold_only,
        "safety_summary": SAFETY_SUMMARY,
    }


def _increment(counts, key):
    if key is None:
        return

    counts[key] = counts.get(key, 0) + 1

"""Consolidated passive command-metadata inspection helpers.

This module unifies the previously separate ``inspection``, ``preview``, and
``audit`` modules. Every helper here is passive and in-memory only: it reads
command metadata and returns copied dry-run reports without sending MIDI,
opening ports, dispatching commands, or executing anything.

The original public names (``inspect_command``, ``preview_command``,
``audit_command_registry``, ``SAFETY_SUMMARY``) are preserved and re-exported
from thin ``preview`` and ``audit`` shim modules so existing imports and the
CLI keep working unchanged.
"""

from __future__ import annotations

from copy import deepcopy

from .validation import validate_command_registry

SAFETY_SUMMARY = "No MIDI would be sent. No command would execute."


# ---------------------------------------------------------------------------
# Command inspection
# ---------------------------------------------------------------------------


def inspect_command(registry, command):
    """Return a read-only dry-run report for command metadata."""
    validation = validate_command_registry(registry)

    if command not in registry:
        return {
            "exists": False,
            "command": command,
            "metadata": None,
            "validation": validation,
        }

    metadata = deepcopy(registry[command])

    return {
        "exists": True,
        "command": command,
        "metadata": metadata,
        "executable": metadata.get("executable"),
        "scaffold_only": metadata.get("scaffold_only"),
        "v134_reference_command": metadata.get("v134_reference_command"),
        "scope": metadata.get("scope"),
        "pad": metadata.get("pad"),
        "type": metadata.get("type"),
        "label": metadata.get("label"),
        "validation": validation,
    }


# ---------------------------------------------------------------------------
# Command preview
# ---------------------------------------------------------------------------


def _target_from_metadata(scope, pad):
    if pad is not None:
        return f"pad_{pad}"

    return scope


def _is_forbidden_or_no_touch(metadata):
    return metadata.get("status") == "forbidden_by_default"


def preview_command(registry, command):
    """Return a passive dry-run preview for a command metadata lookup."""
    inspection = inspect_command(registry, command)

    if not inspection["exists"]:
        return {
            "command": command,
            "exists": False,
            "category": None,
            "scope": None,
            "target": None,
            "pad": None,
            "scaffold_only": None,
            "executable": None,
            "forbidden_or_no_touch": False,
            "validation": inspection["validation"],
            "safety_summary": SAFETY_SUMMARY,
        }

    metadata = inspection["metadata"]
    scope = inspection["scope"]
    pad = inspection["pad"]

    return {
        "command": command,
        "exists": True,
        "category": inspection["type"],
        "scope": scope,
        "target": _target_from_metadata(scope, pad),
        "pad": pad,
        "scaffold_only": inspection["scaffold_only"],
        "executable": inspection["executable"],
        "forbidden_or_no_touch": _is_forbidden_or_no_touch(metadata),
        "validation": inspection["validation"],
        "safety_summary": SAFETY_SUMMARY,
    }


# ---------------------------------------------------------------------------
# Command registry audit
# ---------------------------------------------------------------------------


def _increment(counts, key):
    if key is None:
        return

    counts[key] = counts.get(key, 0) + 1


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


__all__ = [
    "SAFETY_SUMMARY",
    "audit_command_registry",
    "inspect_command",
    "preview_command",
]

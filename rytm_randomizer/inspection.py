"""Passive command metadata inspection helpers."""

from copy import deepcopy

from .validation import validate_command_registry


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

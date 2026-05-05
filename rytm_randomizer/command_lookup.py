"""Passive lookup helpers for existing V1.34 command metadata."""

from copy import deepcopy

from .commands import COMMANDS


def list_command_keys(command_registry=COMMANDS):
    """Return existing command keys without modifying command metadata."""
    return tuple(command_registry.keys())


def describe_command(command_key, command_registry=COMMANDS):
    """Return a passive copied description for a known command key."""
    normalized_key = str(command_key).upper()
    metadata = command_registry.get(normalized_key)

    if metadata is None:
        return {
            "exists": False,
            "command_key": normalized_key,
            "metadata": None,
        }

    metadata_copy = deepcopy(metadata)
    return {
        "exists": True,
        "command_key": normalized_key,
        "type": metadata_copy.get("type"),
        "scope": metadata_copy.get("scope"),
        "pad": metadata_copy.get("pad"),
        "label": metadata_copy.get("label"),
        "name": metadata_copy.get("name"),
        "executable": metadata_copy.get("executable"),
        "v134_reference_command": metadata_copy.get("v134_reference_command"),
        "scaffold_only": metadata_copy.get("scaffold_only"),
        "metadata": metadata_copy,
    }


def get_command_type(command_key, command_registry=COMMANDS):
    """Return the command type metadata for a known command key, or None."""
    description = describe_command(command_key, command_registry)
    if not description["exists"]:
        return None
    return description["type"]


def get_command_label(command_key, command_registry=COMMANDS):
    """Return the command label or scene name for a known command key, or None."""
    description = describe_command(command_key, command_registry)
    if not description["exists"]:
        return None
    return description["label"] or description["name"]

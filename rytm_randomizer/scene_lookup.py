"""Passive lookup helpers for existing V1.34 scene metadata."""

from copy import deepcopy

from .scenes import SCENE_COMMANDS


def list_scene_keys(scene_registry=SCENE_COMMANDS):
    """Return existing scene keys without modifying scene metadata."""
    return tuple(scene_registry.keys())


def describe_scene(scene_key, scene_registry=SCENE_COMMANDS):
    """Return a passive copied description for a known scene key."""
    normalized_key = str(scene_key).upper()
    metadata = scene_registry.get(normalized_key)

    if metadata is None:
        return {
            "exists": False,
            "scene_key": normalized_key,
            "metadata": None,
        }

    metadata_copy = deepcopy(metadata)
    return {
        "exists": True,
        "scene_key": normalized_key,
        "name": metadata_copy["name"],
        "description": metadata_copy["description"],
        "action": metadata_copy["action"],
        "scope": metadata_copy["scope"],
        "executable": metadata_copy["executable"],
        "v134_reference_command": metadata_copy["v134_reference_command"],
        "scaffold_only": metadata_copy["scaffold_only"],
        "metadata": metadata_copy,
    }


def get_scene_name(scene_key, scene_registry=SCENE_COMMANDS):
    """Return the scene name for a known scene key, or None."""
    description = describe_scene(scene_key, scene_registry)
    if not description["exists"]:
        return None
    return description["name"]


def get_scene_action(scene_key, scene_registry=SCENE_COMMANDS):
    """Return the scene action metadata for a known scene key, or None."""
    description = describe_scene(scene_key, scene_registry)
    if not description["exists"]:
        return None
    return description["action"]

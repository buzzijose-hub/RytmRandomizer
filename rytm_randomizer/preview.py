"""Passive dry-run command preview reports."""

from .inspection import inspect_command

SAFETY_SUMMARY = "No MIDI would be sent. No command would execute."


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


def _target_from_metadata(scope, pad):
    if pad is not None:
        return f"pad_{pad}"

    return scope


def _is_forbidden_or_no_touch(metadata):
    return metadata.get("status") == "forbidden_by_default"

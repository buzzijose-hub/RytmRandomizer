"""Passive metadata validation helpers for the modular scaffold."""

import re

FORBIDDEN_EXECUTION_FIELDS = frozenset(
    {"handler", "callable", "execute", "function", "callback"}
)
FORBIDDEN_PADS = frozenset(range(5, 13))
PAD_TEXT_PATTERN = re.compile(r"\bPads?\s+(5|6|7|8|9|10|11|12)\b")
PAD_SCOPE_PATTERN = re.compile(r"\bpad_(5|6|7|8|9|10|11|12)\b")


def validate_command_registry(registry):
    """Return passive validation results for command metadata dictionaries."""
    errors = []

    for command, metadata in registry.items():
        if not isinstance(metadata, dict):
            errors.append(f"{command}: metadata must be a dictionary")
            continue

        if metadata.get("executable") is True:
            errors.append(f"{command}: executable must not be True")

        forbidden_fields = FORBIDDEN_EXECUTION_FIELDS.intersection(metadata)
        for field in sorted(forbidden_fields):
            errors.append(f"{command}: forbidden execution field {field!r}")

        if metadata.get("scaffold_only") is not True:
            errors.append(f"{command}: scaffold_only must be True")

        if metadata.get("v134_reference_command") is not True:
            errors.append(f"{command}: v134_reference_command must be True")

        for path, value in _walk_metadata(metadata):
            if _is_forbidden_pad_reference(path, value):
                errors.append(f"{command}: forbidden pad reference at {path}")

    return {
        "ok": not errors,
        "errors": errors,
    }


def _walk_metadata(value, path="metadata"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield child_path, child
            yield from _walk_metadata(child, child_path)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from _walk_metadata(child, child_path)


def _is_forbidden_pad_reference(path, value):
    path_name = path.rsplit(".", 1)[-1]

    if path_name in {"pad", "group_pad"} and value in FORBIDDEN_PADS:
        return True

    if path_name == "pads" and _contains_forbidden_pad(value):
        return True

    if isinstance(value, str):
        return bool(PAD_TEXT_PATTERN.search(value) or PAD_SCOPE_PATTERN.search(value))

    return False


def _contains_forbidden_pad(value):
    if isinstance(value, dict):
        return any(_contains_forbidden_pad(child) for child in value.values())

    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_forbidden_pad(child) for child in value)

    if value in FORBIDDEN_PADS:
        return True

    return False

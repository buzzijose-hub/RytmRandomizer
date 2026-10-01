"""Passive lookup helpers for existing V1.34 group profile metadata."""

from collections.abc import Mapping
from copy import deepcopy

from .profiles import GROUP_PROFILE_METADATA


def describe_group_profile(
    profile_key: object,
    group_profiles: Mapping[str, Mapping[str, object]] = GROUP_PROFILE_METADATA,
) -> dict[str, object]:
    """Return a passive copied description for a known group profile key."""
    normalized_key = str(profile_key)
    metadata = group_profiles.get(normalized_key)

    if metadata is None:
        return {
            "exists": False,
            "profile_key": normalized_key,
            "metadata": None,
        }

    metadata_copy = deepcopy(metadata)
    return {
        "exists": True,
        "profile_key": normalized_key,
        "name": metadata_copy["name"],
        "machine_value": metadata_copy["machine_value"],
        "group_pad": metadata_copy["group_pad"],
        "metadata": metadata_copy,
    }

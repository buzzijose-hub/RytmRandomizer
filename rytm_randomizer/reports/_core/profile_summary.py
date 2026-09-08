"""Shared profile-summary helpers (active boundary + mock mapper reports).

Extracted from the former monolithic ``rytm_randomizer.reports`` module when
it reached the 1500-LOC comprehensibility cap.

**Typing note.** The summaries are plain dicts on the wire but have fixed,
known key sets, so they are declared as ``TypedDict`` rather than
``dict[str, object]``. That is what keeps the module strict-clean without
runtime narrowing helpers; see ``registry.py`` for the same pattern.
"""

from __future__ import annotations

from typing import TypedDict


class ProfileSummaryDict(TypedDict):
    """One group-profile summary row."""

    profile_key: str
    name: str | None
    group_pad: int | None
    machine_value: int | None
    target: str | None


class UnsupportedProfileSummaryDict(ProfileSummaryDict):
    """A profile summary carrying the reason it is unsupported."""

    reason: str


def _target_concept(profile: ProfileSummaryDict) -> str:
    source_name = str(profile["name"])
    target_name = source_name[3:] if source_name.startswith("My ") else source_name
    return f"Pad {profile['group_pad']} / {target_name}"


def profile_summary_row(profile_key: str) -> ProfileSummaryDict:
    from ...profile_lookup import describe_group_profile

    described = dict(describe_group_profile(profile_key))
    if not described["exists"]:
        return {
            "profile_key": str(profile_key),
            "name": None,
            "group_pad": None,
            "machine_value": None,
            "target": None,
        }

    profile: ProfileSummaryDict = {
        "profile_key": str(described["profile_key"]),
        "name": str(described["name"]),
        "group_pad": int(str(described["group_pad"])),
        "machine_value": int(str(described["machine_value"])),
        "target": None,
    }
    profile["target"] = _target_concept(profile)
    return profile

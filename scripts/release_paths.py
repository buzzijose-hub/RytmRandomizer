"""Conservative hardware-revalidation paths shared by release assembly and CI."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

HARDWARE_PATHS: Final[tuple[str, ...]] = (
    "rytm_randomizer/engines/",
    "rytm_randomizer/senders/",
    "rytm_randomizer/app.py",
    "rytm_randomizer/midi_io.py",
    "rytm_randomizer/real_midi_adapter.py",
    "rytm_randomizer/mido_provider.py",
    "tests/fixtures/v134_parity/",
)
HARDWARE_TAG_MARKER: Final[str] = "[hw-reval]"


def is_hardware_path(path: str) -> bool:
    """Match directories by prefix and individual modules exactly."""
    return any(
        path.startswith(watched) if watched.endswith("/") else path == watched
        for watched in HARDWARE_PATHS
    )


def hardware_revalidation_required(
    paths: Iterable[str], *, pins_changed: bool, tag_annotation: str, requested: bool
) -> bool:
    """A manual flag can only add a warning; it cannot clear detected changes."""
    return (
        requested
        or pins_changed
        or HARDWARE_TAG_MARKER in tag_annotation
        or any(is_hardware_path(path) for path in paths)
    )

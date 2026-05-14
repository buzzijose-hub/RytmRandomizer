"""Passive dry-run command preview reports.

Thin shim over :mod:`rytm_randomizer.inspection`. The preview logic was
consolidated into ``inspection.py``; this module preserves the original public
names.
"""

from .inspection import SAFETY_SUMMARY, preview_command

__all__ = [
    "SAFETY_SUMMARY",
    "preview_command",
]

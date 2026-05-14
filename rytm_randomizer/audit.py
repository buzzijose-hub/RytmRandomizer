"""Passive registry audit reports.

Thin shim over :mod:`rytm_randomizer.inspection`. The audit logic was
consolidated into ``inspection.py``; this module preserves the original public
names.
"""

from .inspection import audit_command_registry

__all__ = [
    "audit_command_registry",
]

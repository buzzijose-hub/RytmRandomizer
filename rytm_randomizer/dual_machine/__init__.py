"""Dual-machine orchestration helpers."""

from __future__ import annotations

from .reports import target_report
from .targets import resolve_target_devices

__all__ = ["resolve_target_devices", "target_report"]

"""Bounded local artifact reads shared by independent persistence stores."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Literal, NoReturn

from ...observability.errors import DataError


def _refuse(
    path: Path, category: Literal["missing", "access", "path", "size"], message: str
) -> NoReturn:
    raise DataError(message, context={"category": category, "artifact_name": path.name})


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def decode_json_rejecting_duplicate_keys(payload: bytes) -> object:
    """Decode UTF-8 JSON while rejecting every duplicate object key."""
    return json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_json_object)


def read_bounded_artifact(path: Path, *, maximum: int, label: str = "local artifact") -> bytes:
    """Reject nonregular files, oversize reads and identity changes while reading."""
    try:
        before = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        _refuse(path, "missing", f"{label} is missing")
    except OSError as exc:
        raise DataError(
            f"{label} cannot be inspected",
            context={"category": "access", "artifact_name": path.name},
        ) from exc
    if not stat.S_ISREG(before.st_mode):
        _refuse(path, "path", f"{label} is not a regular file")
    if before.st_size < 1 or before.st_size > maximum:
        _refuse(path, "size", f"{label} size is outside the supported bound")
    try:
        flags = (
            os.O_RDONLY
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_NOINHERIT", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                before.st_dev,
                before.st_ino,
            ):
                _refuse(path, "access", f"{label} changed during open")
            payload = handle.read(maximum + 1)
        after = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise DataError(
            f"{label} cannot be read",
            context={"category": "access", "artifact_name": path.name},
        ) from exc
    if len(payload) > maximum:
        _refuse(path, "size", f"{label} exceeds the supported bound")
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity:
        _refuse(path, "access", f"{label} changed while it was read")
    return payload


__all__ = ["decode_json_rejecting_duplicate_keys", "read_bounded_artifact"]

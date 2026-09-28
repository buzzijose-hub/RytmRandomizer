"""Desktop shell Cargo resolver pins.

``desktop/shell/Cargo.lock`` **is** committed now, so CI no longer re-resolves
transitive crates from crates.io on every run. That changes what this guard is
for, so read the history before touching it.

This file was written after 2026-06-14, when a fresh ``alloc-no-stdlib`` 3.x
release entered the ``brotli`` graph through ``brotli-decompressor`` /
``alloc-stdlib`` and broke ``desktop-shell`` before any project Rust code
compiled. The same shape recurred on 2026-09-28: the tauri crates published
releases requiring ``rustc 1.90`` while CI pins 1.88.0, and every Rust job on
every branch went red with no Rust change anywhere. Twice is a pattern, and the
lockfile is the general fix the ``=`` pins below were a per-crate workaround for.

The pins are kept because they are load-bearing for a *different* reason: they
document which exact versions the brotli allocator bridge needs, and a lockfile
records that without explaining it. Removing them is safe only once the upstream
graph is compatible again — and that is a deliberate PR, not a drive-by.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
SHELL_CARGO_TOML: Final[Path] = PROJECT_ROOT / "desktop" / "shell" / "Cargo.toml"


def test_desktop_shell_pins_brotli_allocator_bridge() -> None:
    """The shell must force the whole ``brotli`` allocator bridge for now."""

    cargo_config = tomllib.loads(SHELL_CARGO_TOML.read_text(encoding="utf-8"))
    dependencies = cargo_config["dependencies"]

    assert dependencies.get("brotli-decompressor") == "=5.0.1"
    assert dependencies.get("alloc-stdlib") == "=0.2.2"
    assert dependencies.get("alloc-no-stdlib") == "=2.0.4"

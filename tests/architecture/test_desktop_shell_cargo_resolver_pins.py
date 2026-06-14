"""Desktop shell Cargo resolver pins.

The Tauri shell is a Rust application, but this repo intentionally does not
commit ``desktop/shell/Cargo.lock`` yet. That means CI resolves transitive
crates from crates.io on every run. On 2026-06-14, a fresh
``alloc-no-stdlib`` 3.x release entered the ``brotli`` transitive graph through
``brotli-decompressor`` / ``alloc-stdlib`` and broke ``desktop-shell`` before
any project Rust code compiled.

Keep this test narrow: it is a tripwire for the explicit resolver pin in
``desktop/shell/Cargo.toml``. When the upstream ``brotli`` graph is compatible
again, remove both the pin and this guard in the same PR.
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

"""Version single-source guard — the auto-update spec's §2 drift guard.

Spec: ``docs/superpowers/plans/2026-08-03-autoupdate-distribution.md``.

This test is **self-upgrading** across the spec's U1 workstream:

* **Pre-U1 (today)** — no ``VERSION`` file exists. The tree carries five
  independent version declarations with two different values (measured
  2026-09-07). This mode pins that exact inventory as a drainable
  baseline so the drift can only shrink: a NEW version-declaration
  site, or a changed value that does not go through U1, fails loudly
  and points at the spec.
* **Post-U1** — the moment a ``VERSION`` file lands at the repo root,
  this test automatically switches to the full single-source contract:
  strict SemVer in ``VERSION``, all derived files equal to it, and
  exactly one ``version =`` occurrence left in ``pyproject.toml``.

Feature PRs should never touch any of these declarations; per the
spec's developer contract (§11), version bumps are derived by
release-prep, not hand-authored.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
VERSION_FILE: Final[Path] = PROJECT_ROOT / "VERSION"

_SEMVER_RE: Final[re.Pattern[str]] = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-beta\.(0|[1-9]\d*))?$"
)


def _pyproject_versions() -> list[str]:
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.findall(r'^version = "([^"]+)"', text, flags=re.MULTILINE)


def _briefcase_version() -> str | None:
    """The ``[tool.briefcase] version`` literal, or ``None`` if absent.

    briefcase reads this to stamp the ``.msi`` / ``.pkg`` / AppImage that
    ``.github/workflows/installers.yml`` builds. It is a real second
    consumer, **not** a stale duplicate of ``[project] version`` — deleting
    it silently breaks the installer build, which no other test covers.
    """
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(
        r'^\[tool\.briefcase\]$.*?^version = "([^"]+)"',
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else None


def _cargo_version() -> str:
    text = (PROJECT_ROOT / "desktop/shell/Cargo.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', text, flags=re.MULTILINE)
    assert match is not None, "desktop/shell/Cargo.toml has no package version"
    return match.group(1)


def _json_version(relative: str) -> str:
    data = json.loads((PROJECT_ROOT / relative).read_text(encoding="utf-8"))
    version = data.get("version")
    assert isinstance(version, str), f"{relative} has no top-level version string"
    return version


# The measured pre-U1 inventory. U1 deletes this baseline when it
# creates VERSION; until then it may only shrink toward agreement.
_PRE_U1_BASELINE: Final[dict[str, tuple[str, ...]]] = {
    "pyproject.toml": ("1.34.0", "1.34.0"),
    "desktop/shell/Cargo.toml": ("0.1.0",),
    "desktop/shell/tauri.conf.json": ("0.1.0",),
    "desktop/web/package.json": ("0.1.0",),
}


def _current_inventory() -> dict[str, tuple[str, ...]]:
    return {
        "pyproject.toml": tuple(_pyproject_versions()),
        "desktop/shell/Cargo.toml": (_cargo_version(),),
        "desktop/shell/tauri.conf.json": (_json_version("desktop/shell/tauri.conf.json"),),
        "desktop/web/package.json": (_json_version("desktop/web/package.json"),),
    }


def test_version_declarations_do_not_drift() -> None:
    inventory = _current_inventory()

    if not VERSION_FILE.is_file():
        # Pre-U1 ratchet: the known inventory, exactly. Any new site or
        # value change must go through the spec's U1 workstream.
        assert inventory == _PRE_U1_BASELINE, (
            "Version declarations drifted from the recorded pre-U1 "
            "baseline. Do not hand-edit version fields; implement (or "
            "extend) U1 of docs/superpowers/plans/"
            "2026-08-03-autoupdate-distribution.md instead.\n"
            f"expected: {_PRE_U1_BASELINE}\n"
            f"actual:   {inventory}"
        )
        return

    # Post-U1 contract: single source of truth.
    canonical = VERSION_FILE.read_text(encoding="utf-8").strip()
    assert _SEMVER_RE.match(canonical), f"VERSION must be strict SemVer (got {canonical!r})"
    assert inventory["pyproject.toml"] in ((), (canonical,)), (
        "pyproject.toml must derive its version from VERSION "
        "(dynamic) or carry exactly one matching declaration; got "
        f"{inventory['pyproject.toml']}"
    )
    # The one pyproject literal that must SURVIVE U1: briefcase's. The plan
    # originally told U1 to "delete the duplicate declaration" at line 305 —
    # but that line is [tool.briefcase] version, which briefcase reads to
    # stamp the installers. Deleting it breaks installers.yml, and the
    # assertion above would happily accept the resulting empty tuple.
    briefcase = _briefcase_version()
    assert briefcase is not None, (
        "[tool.briefcase] version disappeared from pyproject.toml. It is "
        "NOT a duplicate of [project] version — briefcase reads it to stamp "
        "the .msi/.pkg/AppImage built by .github/workflows/installers.yml. "
        "Restore it and add it to scripts/sync_version.py's targets."
    )
    assert briefcase == canonical, (
        f"[tool.briefcase] version is {briefcase!r}, expected {canonical!r} "
        "— run scripts/sync_version.py"
    )
    for relative in (
        "desktop/shell/Cargo.toml",
        "desktop/shell/tauri.conf.json",
        "desktop/web/package.json",
    ):
        assert inventory[relative] == (canonical,), (
            f"{relative} declares {inventory[relative]}, expected "
            f"({canonical!r},) — run scripts/sync_version.py"
        )

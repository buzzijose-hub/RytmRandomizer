"""Every invalid manifest fixture must be REFUSED by the Python validator.

The corpus under ``tests/fixtures/update_manifest/invalid/`` is a
cross-language contract: the README beside it states that both the Python
validator and the Rust serde/policy layer refuse every file. Before this
module existed, nothing in either language asserted that — Python iterated the
corpus twice but only checked *structure* (single-field minimality, naming),
never rejection, and the Rust loop was wrapped in
``if let Ok(entries) = read_dir(...)`` so it silently did nothing when the
directory was absent from that agent's worktree.

Five of the 33 fixtures validated clean as a result, including one
(``platform_url_version_mismatch``) that would ship the wrong binary to an
entire channel with a signature that still verifies.

This module fails closed: the directory and a non-zero fixture count are
asserted OUTSIDE any conditional, so an absent corpus is a red test rather
than a silent skip.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_FIXTURES: Final[Path] = _ROOT / "tests" / "fixtures" / "update_manifest"
_INVALID: Final[Path] = _FIXTURES / "invalid"
_RELEASE_LIB: Final[Path] = _ROOT / "scripts" / "release_lib.py"


def _load_release_lib():
    """Import the ONE release_lib, reusing any copy already in sys.modules.

    Loading a second module object under the same key would give the test suite
    two distinct `release_lib`s: sibling suites monkeypatch
    ``release_lib.PROJECT_ROOT`` on the copy *they* imported, while the code
    under test reads the copy registered here — so the patch silently applies
    to nothing and those tests fail only when run together with this module.
    Reuse first; register before exec only when we are genuinely the first
    importer (release_lib defines frozen slots dataclasses, and dataclasses
    resolves ``__module__`` through sys.modules while building the class).
    """
    cached = sys.modules.get("release_lib")
    if cached is not None:
        return cached
    if str(_RELEASE_LIB.parent) not in sys.path:
        sys.path.insert(0, str(_RELEASE_LIB.parent))
    import release_lib as module  # noqa: PLC0415  (deliberate late import)

    return module


# Fail closed — an absent corpus or toolkit is a failure, never a skip.
assert _RELEASE_LIB.is_file(), f"release toolkit missing: {_RELEASE_LIB}"
assert _INVALID.is_dir(), f"invalid-manifest corpus missing: {_INVALID}"

_INVALID_FIXTURES: Final[tuple[Path, ...]] = tuple(sorted(_INVALID.glob("*.json")))
assert _INVALID_FIXTURES, f"invalid-manifest corpus is empty: {_INVALID}"

release_lib = _load_release_lib()


@pytest.mark.parametrize("fixture", _INVALID_FIXTURES, ids=lambda p: p.stem)
def test_every_invalid_fixture_is_refused(fixture: Path) -> None:
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    violations = release_lib.validate_manifest(payload)
    assert not release_lib.manifest_is_acceptable(violations), (
        f"{fixture.name} validated CLEAN but the corpus declares it invalid.\n"
        "Either the validator is missing a rule (add the ViolationCode and the "
        "check), or the fixture no longer represents a real defect (remove it). "
        "A fixture that passes is a rule nobody is enforcing."
    )


def test_the_valid_fixture_is_accepted() -> None:
    """The corpus is only meaningful if the positive case still passes."""
    payload = json.loads((_FIXTURES / "manifest.v1.json").read_text(encoding="utf-8"))
    violations = release_lib.validate_manifest(payload)
    assert release_lib.manifest_is_acceptable(violations), (
        "The canonical valid manifest was refused: "
        f"{[v.code.value for v in violations if not v.is_advisory]}"
    )


def test_corpus_is_not_silently_empty() -> None:
    """Guards the guard: a shrinking corpus must be a deliberate act."""
    assert len(_INVALID_FIXTURES) >= 30, (
        f"the invalid corpus has {len(_INVALID_FIXTURES)} fixtures; it had 30. "
        "Removing a fixture removes a rule from the cross-language contract. "
        "(Three originals moved to ../advisory/ — spec §4 makes provenance, "
        "unknown fields, and minimum_version non-blocking; see that README.)"
    )

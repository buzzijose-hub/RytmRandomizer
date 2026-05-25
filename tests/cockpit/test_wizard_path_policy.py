"""Tests for ``rytm_randomizer.cockpit.wizard.path_policy`` (CODE_REVIEW PR 2 / C2).

The path policy is the choke point that keeps a hostile WS peer from
asking the cockpit to fingerprint arbitrary files (e.g. ``/etc/passwd``).
Every test below pins one rejection or acceptance lane:

* ``from_env`` parses :data:`WIZARD_SOURCE_ROOTS_ENV` (or falls back to
  the safe default ``~/.rytm-randomizer/wizard-sources/``).
* :meth:`WizardPathPolicy.validate` accepts in-root paths, rejects
  out-of-root paths, symlinks, missing paths, and empty strings.
* Rejection raises :class:`WizardSourcePathRejected` with a CATEGORICAL
  message that NEVER includes the offending path (so the WS ack can
  surface ``str(exc)`` directly without leaking the rejected path back
  to a hostile caller).
* The exception participates in the RytmRandomizerError taxonomy AND
  satisfies ``except ValueError:`` callers (dual-inheritance).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.wizard.path_policy import (
    DEFAULT_WIZARD_SOURCE_ROOT,
    WIZARD_SOURCE_ROOTS_ENV,
    WizardPathPolicy,
    WizardSourcePathRejected,
)
from rytm_randomizer.observability.errors import DataError

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# from_env: defaults + parsing
# ---------------------------------------------------------------------------


def test_from_env_unset_falls_back_to_default_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without :data:`WIZARD_SOURCE_ROOTS_ENV` the policy uses the default root."""

    monkeypatch.delenv(WIZARD_SOURCE_ROOTS_ENV, raising=False)
    policy = WizardPathPolicy.from_env()
    expected = Path(DEFAULT_WIZARD_SOURCE_ROOT).expanduser().resolve()
    assert policy.roots == (expected,)


def test_from_env_blank_value_falls_back_to_default_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A whitespace-only env value cannot accidentally disable the policy."""

    monkeypatch.setenv(WIZARD_SOURCE_ROOTS_ENV, "   ")
    policy = WizardPathPolicy.from_env()
    expected = Path(DEFAULT_WIZARD_SOURCE_ROOT).expanduser().resolve()
    assert policy.roots == (expected,)


def test_from_env_parses_multiple_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``os.pathsep`` separated paths are all listed in :attr:`roots`."""

    root_a = tmp_path / "root_a"
    root_b = tmp_path / "root_b"
    root_a.mkdir()
    root_b.mkdir()
    env_value = os.pathsep.join((str(root_a), str(root_b)))
    monkeypatch.setenv(WIZARD_SOURCE_ROOTS_ENV, env_value)

    policy = WizardPathPolicy.from_env()

    assert root_a.resolve() in policy.roots
    assert root_b.resolve() in policy.roots
    # Both candidates and only the candidates landed (no default leak).
    assert len(policy.roots) == 2


def test_from_env_skips_empty_segments(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``"<root><sep><sep>"`` does not introduce a phantom empty root."""

    root = tmp_path / "kept"
    root.mkdir()
    env_value = f"{root}{os.pathsep}{os.pathsep}"
    monkeypatch.setenv(WIZARD_SOURCE_ROOTS_ENV, env_value)

    policy = WizardPathPolicy.from_env()

    assert policy.roots == (root.resolve(),)


def test_from_env_expands_user_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``~``-prefixed value is expanded relative to the operator's home."""

    monkeypatch.setenv(WIZARD_SOURCE_ROOTS_ENV, "~/example-wizard-root")

    policy = WizardPathPolicy.from_env()

    expected = (Path.home() / "example-wizard-root").resolve()
    assert policy.roots == (expected,)


# ---------------------------------------------------------------------------
# validate: happy path
# ---------------------------------------------------------------------------


def test_validate_returns_resolved_path_for_in_root_file(tmp_path: Path) -> None:
    """A real file inside a root is accepted; the resolved Path is returned."""

    policy = WizardPathPolicy(roots=(tmp_path.resolve(),))
    target = tmp_path / "kit.syx"
    target.write_bytes(b"\x00")

    accepted = policy.validate(str(target))

    assert accepted == target.resolve()


def test_validate_returns_resolved_path_for_in_root_directory(tmp_path: Path) -> None:
    """A directory under a root is accepted (kit folders are legal)."""

    policy = WizardPathPolicy(roots=(tmp_path.resolve(),))
    folder = tmp_path / "kits"
    folder.mkdir()

    accepted = policy.validate(str(folder))

    assert accepted == folder.resolve()


def test_validate_accepts_path_in_any_of_multiple_roots(tmp_path: Path) -> None:
    """A multi-root policy accepts a path in either root."""

    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    policy = WizardPathPolicy(roots=(root_a.resolve(), root_b.resolve()))

    target_b = root_b / "song.wav"
    target_b.write_bytes(b"\x00")

    assert policy.validate(str(target_b)) == target_b.resolve()


# ---------------------------------------------------------------------------
# validate: rejection lanes
# ---------------------------------------------------------------------------


def test_validate_rejects_empty_string(tmp_path: Path) -> None:
    """An empty location string is rejected categorically."""

    policy = WizardPathPolicy(roots=(tmp_path.resolve(),))
    with pytest.raises(WizardSourcePathRejected, match="empty"):
        policy.validate("")


def test_validate_rejects_absolute_path_outside_root(tmp_path: Path) -> None:
    """An absolute path outside the allow-list is rejected."""

    root = tmp_path / "blessed"
    root.mkdir()
    outside = tmp_path / "forbidden.txt"
    outside.write_bytes(b"secret")
    policy = WizardPathPolicy(roots=(root.resolve(),))

    with pytest.raises(WizardSourcePathRejected, match="outside the allowed roots"):
        policy.validate(str(outside))


def test_validate_rejects_traversal_attempt(tmp_path: Path) -> None:
    """``../../`` traversal that escapes the root is rejected on the resolved path."""

    root = tmp_path / "blessed"
    root.mkdir()
    outside = tmp_path / "forbidden.txt"
    outside.write_bytes(b"secret")
    policy = WizardPathPolicy(roots=(root.resolve(),))

    traversal = str(root / ".." / "forbidden.txt")

    with pytest.raises(WizardSourcePathRejected, match="outside the allowed roots"):
        policy.validate(traversal)


def test_validate_rejects_missing_path(tmp_path: Path) -> None:
    """A path that resolves inside a root but does not exist is rejected."""

    policy = WizardPathPolicy(roots=(tmp_path.resolve(),))

    with pytest.raises(WizardSourcePathRejected, match="does not exist"):
        policy.validate(str(tmp_path / "ghost.syx"))


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="symlinks require elevated privileges on Windows; covered on POSIX",
)
def test_validate_rejects_symlinked_path(tmp_path: Path) -> None:
    """A symlink at the leaf -- even pointing inside the root -- is rejected.

    The policy refuses to chase the link so the operator-visible reasoning
    is local to the path they typed, not the resolved target.
    """

    root = tmp_path / "blessed"
    root.mkdir()
    target = root / "real.syx"
    target.write_bytes(b"\x00")
    link = root / "link.syx"
    link.symlink_to(target)
    policy = WizardPathPolicy(roots=(root.resolve(),))

    with pytest.raises(WizardSourcePathRejected, match="symlink"):
        policy.validate(str(link))


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="symlinks require elevated privileges on Windows; covered on POSIX",
)
def test_validate_rejects_path_with_symlinked_parent(tmp_path: Path) -> None:
    """A symlinked parent component is rejected even if the leaf is not a link."""

    root = tmp_path / "blessed"
    root.mkdir()
    inner = root / "inner"
    inner.mkdir()
    (inner / "kit.syx").write_bytes(b"\x00")
    link_parent = root / "via_link"
    link_parent.symlink_to(inner)

    policy = WizardPathPolicy(roots=(root.resolve(),))

    with pytest.raises(WizardSourcePathRejected, match="symlink"):
        policy.validate(str(link_parent / "kit.syx"))


# ---------------------------------------------------------------------------
# Categorical message guarantee — paths are NEVER echoed back
# ---------------------------------------------------------------------------


def test_rejection_messages_never_include_offending_path(tmp_path: Path) -> None:
    """Every rejection message excludes the rejected path (information disclosure)."""

    root = tmp_path / "blessed"
    root.mkdir()
    policy = WizardPathPolicy(roots=(root.resolve(),))
    forbidden = tmp_path / "forbidden-secrets.txt"
    forbidden.write_bytes(b"")

    forbidden_str = str(forbidden)

    # 1) Out-of-root path.
    with pytest.raises(WizardSourcePathRejected) as exc_out:
        policy.validate(forbidden_str)
    assert forbidden_str not in str(exc_out.value)
    assert "forbidden-secrets" not in str(exc_out.value)

    # 2) Missing path (path-shaped but absent inside root).
    with pytest.raises(WizardSourcePathRejected) as exc_missing:
        policy.validate(str(root / "absent.syx"))
    assert "absent.syx" not in str(exc_missing.value)

    # 3) Empty location.
    with pytest.raises(WizardSourcePathRejected) as exc_empty:
        policy.validate("")
    # The message is just "path is empty" -- no input to leak.
    assert str(exc_empty.value) == "path is empty"


# ---------------------------------------------------------------------------
# Exception taxonomy contract
# ---------------------------------------------------------------------------


def test_wizard_source_path_rejected_is_a_data_error() -> None:
    """The exception participates in the RytmRandomizerError taxonomy.

    ``DataError`` membership is what the observability conformance test
    keys on; without it every ``raise WizardSourcePathRejected`` would
    fail :func:`tests.architecture.test_observability.
    test_raises_use_taxonomy_or_validation_stdlib`.
    """

    assert issubclass(WizardSourcePathRejected, DataError)


def test_wizard_source_path_rejected_is_a_value_error() -> None:
    """``except ValueError:`` callers continue to work without import changes."""

    assert issubclass(WizardSourcePathRejected, ValueError)
    try:
        raise WizardSourcePathRejected("path is empty")
    except ValueError as exc:
        assert str(exc) == "path is empty"

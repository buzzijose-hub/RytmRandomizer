"""Allow-list policy for wizard ``InspirationSource`` filesystem locations.

The wizard accepts ``location`` strings straight off the wire and hands
them to analyzers that call :meth:`Path.read_bytes` /
:meth:`Path.iterdir`. Without this policy a hostile WebSocket peer (or a
hostile ``.rymp`` payload) could ask the cockpit to fingerprint arbitrary
files the cockpit's OS user can read -- ``/etc/passwd``, ``~/.ssh/*``,
private documents, etc. The analyzer's byte statistics would then leak
back over the wire encoded as four floats per source: a textbook oracle.

:class:`WizardPathPolicy` is the choke point. Every accepted location
must resolve to a path **inside** at least one of the policy's roots,
must exist on disk, and must not be a symlink (a symlink would let a
caller stash a same-name link inside an allowed root that points
outside -- ``resolve`` would chase the link, but the policy enforces the
guarantee explicitly so the reasoning is local to the file the operator
dropped, not the resolved target).

Default policy
--------------

When ``WIZARD_SOURCE_ROOTS`` is unset, the single default root is
``~/.rytm-randomizer/wizard-sources/`` -- a per-operator directory the
desktop shell can create with safe permissions. This satisfies Gate 13
("documented, safe default"): the cockpit ships with a working
allow-list out of the box and the operator can extend it via env without
touching code.

The env var is parsed with :data:`os.pathsep` (``:`` on POSIX, ``;`` on
Windows) so the same value works across platforms. Empty roots are
skipped silently; an env value of all-empty entries falls back to the
default so a typo never disables the policy.

Categorical errors
------------------

Rejected paths raise :class:`WizardSourcePathRejected` with a CATEGORICAL
message that never echoes the rejected path -- the path goes to the
server log via the analyzer surface, not back to the WS caller. This
plugs the H4 information-disclosure path (see PR 2 of the code review).

The exception inherits from both
:class:`~rytm_randomizer.observability.errors.DataError` (so the
taxonomy conformance test counts it as a member) and stdlib
:class:`ValueError` (so ``except ValueError:`` callers continue to work).
This mirrors the existing :class:`EmptyAnalysisError` /
:class:`WizardSourcePathError` dual-inheritance pattern in the wizard
subpackage.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Final

from ...observability.errors import DataError

__all__ = [
    "DEFAULT_WIZARD_SOURCE_ROOT",
    "WIZARD_SOURCE_ROOTS_ENV",
    "WizardPathPolicy",
    "WizardSourcePathRejected",
]


WIZARD_SOURCE_ROOTS_ENV: Final[str] = "WIZARD_SOURCE_ROOTS"
"""Env var name parsed by :meth:`WizardPathPolicy.from_env`.

Value is a :data:`os.pathsep` separated list of paths. Each entry is
``Path.expanduser().resolve()`` so ``~`` works and the policy stores
absolute resolved paths.
"""


DEFAULT_WIZARD_SOURCE_ROOT: Final[str] = "~/.rytm-randomizer/wizard-sources"
"""Default root when :data:`WIZARD_SOURCE_ROOTS_ENV` is unset.

Per-operator directory the desktop shell creates with safe permissions
on first run. Using the user's home directory means the cockpit ships
with a working allow-list out of the box (Gate 13: documented, safe
default).
"""


class WizardSourcePathRejected(DataError, ValueError):
    """Raised when an :class:`InspirationSource` location violates the policy.

    The message is intentionally categorical -- ``"path outside allowed
    roots"`` / ``"path does not exist"`` / ``"path is a symlink"`` /
    ``"path is empty"`` -- so the WS ack the operator's browser sees
    never carries the offending path. The full detail (including the
    path) is logged server-side by the WS handler, not raised here.

    Multi-inheritance via :class:`DataError` (the RytmRandomizerError
    taxonomy branch for missing / malformed data) AND :class:`ValueError`
    (stdlib) means:

    * ``except ValueError:`` callers continue to work without import
      changes (idiomatic Python validation-error handling);
    * The observability conformance test
      (``tests/architecture/test_observability.py``) recognises the raise
      as a taxonomy member.

    Mirrors :class:`rytm_randomizer.cockpit.wizard.builder.
    EmptyAnalysisError` and :class:`rytm_randomizer.cockpit.wizard.
    errors.WizardSourcePathError`, both of which use the same dual-
    inheritance pattern.
    """

    fingerprint: ClassVar[str] = "wizard.source.path_rejected"


@dataclass(frozen=True)
class WizardPathPolicy:
    """Frozen allow-list of root directories permitted as wizard sources.

    Construct via :meth:`from_env` (production / test) or directly with a
    pre-resolved tuple of roots (tests that want to pin a tmp_path
    directory). Every root is stored as an absolute resolved path so
    :meth:`validate` can perform a single :meth:`Path.is_relative_to`
    check per root.

    The policy is immutable and side-effect-free -- safe to share across
    coroutines and store on the WS session without defensive copying.
    """

    roots: tuple[Path, ...]

    @classmethod
    def from_env(cls, env_var: str = WIZARD_SOURCE_ROOTS_ENV) -> WizardPathPolicy:
        """Build a policy from ``env_var`` (or the default root if unset).

        The env value is split on :data:`os.pathsep` so the same string
        works on POSIX (``:``) and Windows (``;``). Empty entries are
        skipped silently; an empty-or-whitespace value falls back to the
        default so a typo cannot accidentally disable the policy.

        Args:
            env_var: Env var name to read. Defaults to
                :data:`WIZARD_SOURCE_ROOTS_ENV`. Override for testing
                without polluting the real env.

        Returns:
            A frozen :class:`WizardPathPolicy` whose roots are absolute
            resolved Paths (``~`` expanded).
        """

        raw = os.environ.get(env_var, "").strip()
        if not raw:
            return cls(roots=(Path(DEFAULT_WIZARD_SOURCE_ROOT).expanduser().resolve(),))
        candidates = [seg.strip() for seg in raw.split(os.pathsep) if seg.strip()]
        if not candidates:
            return cls(roots=(Path(DEFAULT_WIZARD_SOURCE_ROOT).expanduser().resolve(),))
        roots = tuple(Path(seg).expanduser().resolve() for seg in candidates)
        return cls(roots=roots)

    def validate(self, location: str) -> Path:
        """Return the resolved Path iff ``location`` satisfies the policy.

        Validation order is fixed so the categorical reason is stable
        across callers:

        1. ``location`` must be a non-empty string.
        2. ``Path(location).expanduser()`` must not be a symlink at the
           given segment (chasing a symlink defeats the allow-list).
        3. The resolved path must exist on disk (``strict=False`` on the
           ``resolve`` call so a clean error is raised here, not deep
           inside the analyzer).
        4. The resolved path must be inside at least one root via
           :meth:`Path.is_relative_to`.

        Raises:
            WizardSourcePathRejected: With a categorical message. The
                offending path is NEVER included in the message -- the
                WS handler logs it server-side via the module logger.
        """

        if not location:
            raise WizardSourcePathRejected("path is empty")

        # Reject symlinks *before* resolve() would chase them. We check
        # the user-supplied path AND every parent component so a hostile
        # symlink anywhere in the chain is rejected.
        raw_path = Path(location).expanduser()
        if raw_path.is_symlink() or any(parent.is_symlink() for parent in raw_path.parents):
            raise WizardSourcePathRejected("path traverses a symlink")

        resolved = raw_path.resolve(strict=False)

        if not resolved.exists():
            raise WizardSourcePathRejected("path does not exist")

        for root in self.roots:
            if _is_inside(resolved, root):
                return resolved

        raise WizardSourcePathRejected("path is outside the allowed roots")


def _is_inside(candidate: Path, root: Path) -> bool:
    """Return ``True`` iff ``candidate`` is ``root`` or a descendant of it.

    Uses :meth:`Path.is_relative_to` (Python 3.9+); the
    :class:`ValueError` fallback would only matter on Python <3.9, which
    this project does not support (CI pins 3.11+).
    """

    try:
        return candidate.is_relative_to(root)
    except ValueError:  # pragma: no cover - defensive on legacy interpreters
        return False

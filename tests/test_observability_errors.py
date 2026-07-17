"""Coverage tests for ``rytm_randomizer.observability.errors`` (taxonomy + re-export).

The errors module is the raises-taxonomy "umbrella" on top of the package's
existing concrete exception classes. The PEP-562 ``__getattr__`` re-exports
five legacy error classes (``RealMidiDependencyError``, ``RealMidiPortError``,
``RealMidiSendError``, ``MockMessageMappingError``, ``ActiveBoundaryError``)
under the new taxonomy bases so ``isinstance(exc, MidiError)`` works for any
real-midi-adapter exception, etc.

These tests exercise:

* ``RytmRandomizerError`` context handling (message vs. message+context).
* ``__getattr__`` for each of the five legacy re-exports.
* ``__getattr__`` for an unknown name (raises ``AttributeError``).
* OBS O4 -- every concrete taxonomy subclass declares a non-empty,
  unique, dot-path ``fingerprint`` class attribute. The fingerprint is
  the stable aggregator string an operator ``grep``s for in logs and a
  future Sentry / alerting tier groups on.

Test naming: ``test_<unit>_<behavior>_when_<condition>`` per Gate 8.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


#: Regex matching the ``<a>.<b>(.<c>...)*`` dot-path shape every taxonomy
#: fingerprint must satisfy. Leading segment starts with a lowercase
#: letter; characters are ``[a-z0-9_]``; segments separated by literal
#: dots. At least two segments so every fingerprint carries
#: subsystem + action.
_FINGERPRINT_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


# ---------------------------------------------------------------------------
# 1. RytmRandomizerError: message-only vs. message+context rendering
# ---------------------------------------------------------------------------


def test_rytm_randomizer_error_with_no_context_renders_message_only() -> None:
    from rytm_randomizer.observability.errors import RytmRandomizerError

    err = RytmRandomizerError("boom")
    assert err.message == "boom"
    assert dict(err.context) == {}
    assert str(err) == "boom"


def test_rytm_randomizer_error_with_context_appends_context_tail() -> None:
    from rytm_randomizer.observability.errors import RytmRandomizerError

    err = RytmRandomizerError("boom", context={"pad": 1, "param": "FLT Frequency"})
    assert err.message == "boom"
    rendered = str(err)
    assert rendered.startswith("boom [context: ")
    assert "pad=1" in rendered
    assert "param='FLT Frequency'" in rendered


def test_rytm_randomizer_error_context_is_read_only_mapping() -> None:
    from rytm_randomizer.observability.errors import RytmRandomizerError

    err = RytmRandomizerError("boom", context={"key": "value"})
    # MappingProxyType raises TypeError on assignment.
    with pytest.raises(TypeError):
        err.context["key"] = "other"  # type: ignore[index]


# ---------------------------------------------------------------------------
# 2. Taxonomy bases are importable and distinct
# ---------------------------------------------------------------------------


def test_taxonomy_bases_are_exported_and_subclass_root() -> None:
    from rytm_randomizer.observability.errors import (
        BoundaryError,
        ConfigError,
        DataError,
        MidiError,
        RytmRandomizerError,
        StateError,
    )

    for cls in (MidiError, StateError, DataError, BoundaryError, ConfigError):
        assert issubclass(cls, RytmRandomizerError)


# ---------------------------------------------------------------------------
# 3. PEP-562 __getattr__: lazy re-exports
# ---------------------------------------------------------------------------


def test_module_getattr_resolves_real_midi_dependency_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import MidiError

    cls = errors_mod.RealMidiDependencyError
    assert issubclass(cls, MidiError)


def test_module_getattr_resolves_real_midi_port_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import MidiError

    cls = errors_mod.RealMidiPortError
    assert issubclass(cls, MidiError)


def test_module_getattr_resolves_real_midi_send_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import MidiError

    cls = errors_mod.RealMidiSendError
    assert issubclass(cls, MidiError)


def test_module_getattr_resolves_mock_message_mapping_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import DataError

    cls = errors_mod.MockMessageMappingError
    assert issubclass(cls, DataError)


def test_module_getattr_resolves_active_boundary_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import BoundaryError

    cls = errors_mod.ActiveBoundaryError
    assert issubclass(cls, BoundaryError)


def test_module_getattr_raises_attribute_error_on_unknown_name() -> None:
    from rytm_randomizer.observability import errors as errors_mod

    with pytest.raises(AttributeError, match="DoesNotExistError"):
        errors_mod.DoesNotExistError  # noqa: B018 - intentional attribute access


# ---------------------------------------------------------------------------
# 4. OBS O4 -- fingerprint discipline across the taxonomy
# ---------------------------------------------------------------------------
#
# Every concrete RytmRandomizerError subclass declares a stable, short
# ``fingerprint`` class attribute. The three invariants enforced below
# are: (a) non-empty, (b) globally unique across all subclasses, (c)
# matches a strict ``[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+`` dot-path so
# the vocabulary stays operator-greppable.
#
# The discovery helper imports every module known to carry a taxonomy
# subclass so ``__subclasses__()`` returns the full set rather than
# whatever Python happened to have imported into ``sys.modules``.


def _import_taxonomy_modules() -> None:
    """Import every module that defines a ``RytmRandomizerError`` subclass.

    Subclass discovery via ``cls.__subclasses__()`` only sees classes
    Python has already imported. Tests in this file may otherwise run
    against a partially-loaded taxonomy if a subclass module has never
    been imported in the current pytest worker.
    """

    # Base + taxonomy bases (imports the module itself).
    import rytm_randomizer.observability.errors  # noqa: F401 - side-effect import

    # Lazy-resolved re-exports (PEP-562 ``__getattr__`` triggers the
    # original-module import). Reading the attribute is enough.
    from rytm_randomizer.observability import (  # noqa: F401 - side-effect import
        errors as errors_mod,
    )

    errors_mod.RealMidiDependencyError  # noqa: B018 - side-effect attribute access
    errors_mod.RealMidiPortError  # noqa: B018
    errors_mod.RealMidiSendError  # noqa: B018
    errors_mod.MockMessageMappingError  # noqa: B018
    errors_mod.ActiveBoundaryError  # noqa: B018

    # Subclass modules outside the re-export chain.
    import rytm_randomizer.cockpit.export.writer  # noqa: F401
    import rytm_randomizer.cockpit.profiles.registry  # noqa: F401
    import rytm_randomizer.cockpit.wizard.builder  # noqa: F401
    import rytm_randomizer.cockpit.wizard.errors  # noqa: F401
    import rytm_randomizer.cockpit.wizard.path_policy  # noqa: F401
    import rytm_randomizer.guardrails.resolver  # noqa: F401
    import rytm_randomizer.guardrails.store  # noqa: F401
    import rytm_randomizer.guardrails.validation  # noqa: F401
    import rytm_randomizer.local_ai.provider  # noqa: F401
    import rytm_randomizer.style_analysis.extractor  # noqa: F401


def _all_taxonomy_subclasses() -> list[type]:
    """Return every concrete ``RytmRandomizerError`` subclass in the package.

    Walks ``__subclasses__()`` recursively so a grandchild class (e.g.
    a subclass of :class:`DataError`) is included alongside its direct
    parent. Order is import-order, which keeps the assertion output
    diff-friendly across runs.
    """

    from rytm_randomizer.observability.errors import RytmRandomizerError

    _import_taxonomy_modules()
    seen: list[type] = []
    stack: list[type] = list(RytmRandomizerError.__subclasses__())
    while stack:
        cls = stack.pop(0)
        if cls in seen:
            continue
        seen.append(cls)
        stack.extend(cls.__subclasses__())
    return seen


def test_every_concrete_taxonomy_subclass_declares_a_non_empty_fingerprint() -> None:
    """OBS O4: every taxonomy subclass MUST own a non-empty fingerprint.

    A subclass that inherits its parent's fingerprint verbatim defeats
    the aggregator (two raises grouped under the same key are no more
    actionable than one), so the check also verifies that each subclass
    declares its OWN string rather than inheriting silently.
    """

    subclasses = _all_taxonomy_subclasses()
    assert subclasses, "no taxonomy subclasses found -- discovery is broken"

    for cls in subclasses:
        assert (
            isinstance(cls.fingerprint, str) and cls.fingerprint
        ), f"{cls.__module__}.{cls.__qualname__} has no fingerprint declared"
        # The immediate-parent fingerprint set: if cls.fingerprint matches
        # any of them, the subclass is inheriting silently and the
        # aggregator collapses.
        parent_fingerprints = {
            base.fingerprint
            for base in cls.__mro__[1:]
            if isinstance(getattr(base, "fingerprint", None), str)
        }
        if cls.fingerprint in parent_fingerprints:
            pytest.fail(
                f"{cls.__module__}.{cls.__qualname__} inherits fingerprint "
                f"{cls.fingerprint!r} from a parent rather than declaring "
                "its own; that defeats the aggregator"
            )


def test_taxonomy_fingerprints_are_globally_unique() -> None:
    """OBS O4: no two taxonomy classes share a fingerprint.

    Include the root :class:`RytmRandomizerError` in the check too --
    a subclass colliding with the root would also defeat the aggregator.
    """

    from rytm_randomizer.observability.errors import RytmRandomizerError

    subclasses = _all_taxonomy_subclasses()
    all_classes = [RytmRandomizerError, *subclasses]
    by_fingerprint: dict[str, list[str]] = {}
    for cls in all_classes:
        by_fingerprint.setdefault(cls.fingerprint, []).append(
            f"{cls.__module__}.{cls.__qualname__}"
        )
    duplicates = {fp: members for fp, members in by_fingerprint.items() if len(members) > 1}
    assert not duplicates, "taxonomy fingerprints must be unique; duplicates found: " + repr(
        duplicates
    )


def test_taxonomy_fingerprints_match_dotpath_regex() -> None:
    """OBS O4: every fingerprint matches ``[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+``.

    The regex enforces lowercase, dot-separated, ``[a-z0-9_]``-only
    segments with at least two segments (subsystem + verb). Any
    fingerprint that fails the check is a vocabulary violation -- the
    operator should be able to ``grep -F '<subsystem>.'`` and find
    every member of that family.
    """

    from rytm_randomizer.observability.errors import RytmRandomizerError

    subclasses = _all_taxonomy_subclasses()
    for cls in [RytmRandomizerError, *subclasses]:
        assert _FINGERPRINT_RE.match(cls.fingerprint), (
            f"{cls.__module__}.{cls.__qualname__} fingerprint "
            f"{cls.fingerprint!r} does not match the dot-path regex "
            f"{_FINGERPRINT_RE.pattern!r}"
        )


def test_taxonomy_fingerprint_is_accessible_via_class_and_instance() -> None:
    """OBS O4: ``fingerprint`` is a class attr usable from both surfaces.

    The structured-log call sites read ``exc.fingerprint`` (instance
    access); future metric-label assembly would read
    ``ExceptionCls.fingerprint`` (class access). Both must return the
    same string.
    """

    from rytm_randomizer.cockpit.export.writer import WriteError

    instance = WriteError("disk full")
    assert WriteError.fingerprint == instance.fingerprint == "export.write.failed"

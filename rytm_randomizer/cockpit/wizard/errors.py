"""Profile-Wizard-local exception taxonomy.

The wizard's analysis adapter raises one custom exception when an
:class:`~rytm_randomizer.cockpit.wizard.state.InspirationSource` points
at a path that does not exist. Multi-inheritance via
:class:`~rytm_randomizer.observability.errors.DataError` (the
RytmRandomizerError taxonomy branch for missing / malformed data) AND
:class:`FileNotFoundError` (stdlib) means:

* ``except FileNotFoundError:`` callers continue to work without import
  changes (idiomatic Python file-missing handling);
* The observability conformance test
  (``tests/architecture/test_observability.py``) recognises the raise as
  a taxonomy member, satisfying the per-PR check that every package
  ``raise`` either uses the taxonomy or an allowlisted stdlib class.

The pattern mirrors
:class:`rytm_randomizer.style_analysis.extractor.
StyleAnalysisDependencyError`, which uses the same
``DataError`` + ``RuntimeError`` multi-inheritance.
"""

from __future__ import annotations

from typing import ClassVar

from ...observability.errors import DataError


class WizardSourcePathError(DataError, FileNotFoundError):
    """Raised when an analyzer's input path does not exist on disk.

    Carries both taxonomy and stdlib-FileNotFoundError membership so the
    error reads naturally from a caller's perspective and counts as a
    taxonomy member from the conformance-test perspective.
    """

    fingerprint: ClassVar[str] = "wizard.source.path_not_found"


__all__ = ["WizardSourcePathError"]

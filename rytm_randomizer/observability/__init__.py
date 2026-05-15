"""World-class observability for the RytmRandomizer package (Wave 4 / WS-U).

This sub-package owns three concerns:

* **Logging** -- a single configured ``logging`` setup with named loggers per
  package module. See :mod:`rytm_randomizer.observability.logging` for the
  ``configure_logging`` / ``get_logger`` public API plus the structured and
  JSON formatters.
* **Error taxonomy** -- a single root :class:`RytmRandomizerError` with a
  small hierarchy that the existing module-local error classes are re-homed
  under via multi-inheritance, so ``except`` clauses can target one base
  while existing call sites keep working. See
  :mod:`rytm_randomizer.observability.errors`.
* **Tracing** -- a context manager and decorator for instrumenting
  meaningful operation boundaries (scene runs, group mutations, engine
  loads, port opens, parity round-trips). See
  :mod:`rytm_randomizer.observability.tracing`.

Import-safety: importing this sub-package attaches a :class:`logging.NullHandler`
to the package root logger so a stray ``logger.warning(...)`` from any package
module never writes to ``stderr`` until the caller opts in by calling
:func:`configure_logging`. Importing this module opens no I/O, touches no
hardware, and pulls in no real MIDI library.

Layering: this sub-package is a leaf -- it imports nothing from
``rytm_randomizer/`` except optional :mod:`rytm_randomizer.data` constants.
That keeps the dependency graph one-directional and the architecture
conformance tests in ``tests/architecture/test_observability.py`` enforce it.
"""

from __future__ import annotations

import logging as _logging

from .errors import (
    BoundaryError,
    ConfigError,
    DataError,
    MidiError,
    RytmRandomizerError,
    StateError,
)
from .logging import (
    JSON_FORMAT_NAME,
    LOG_FORMAT,
    PACKAGE_LOGGER_NAME,
    configure_logging,
    get_logger,
)
from .tracing import operation, trace

__all__ = [
    "BoundaryError",
    "ConfigError",
    "DataError",
    "JSON_FORMAT_NAME",
    "LOG_FORMAT",
    "MidiError",
    "PACKAGE_LOGGER_NAME",
    "RytmRandomizerError",
    "StateError",
    "configure_logging",
    "get_logger",
    "operation",
    "trace",
]


# Attach a NullHandler at import time so a stray log call from anywhere in the
# package never writes to stderr until the caller explicitly opts in via
# :func:`configure_logging`. This mirrors the stdlib library-author guidance
# and keeps ``import rytm_randomizer.*`` silent for the package-import-safety
# tests (``tests/architecture/test_no_side_effects.py``).
#
# We also turn off propagation to the root logger because the stdlib's
# ``logging.lastResort`` handler emits WARNING+ records to stderr by default
# for any logger that lacks a configured ancestor handler. With propagation
# off and a local NullHandler attached, a stray ``logger.warning`` from any
# package module is fully swallowed until the caller calls
# :func:`configure_logging`. (``configure_logging`` re-sets ``propagate=False``
# explicitly for the same reason.)
_package_logger = _logging.getLogger(PACKAGE_LOGGER_NAME)
if not any(isinstance(h, _logging.NullHandler) for h in _package_logger.handlers):
    _package_logger.addHandler(_logging.NullHandler())
_package_logger.propagate = False

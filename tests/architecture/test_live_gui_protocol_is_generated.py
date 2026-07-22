"""The live-GUI TS protocol and the performance-console JSON fixture are generated.

``desktop/web/src/types/live_gui_protocol.ts`` and
``desktop/web/tests/cockpit/fixtures/performance_console.json`` are artifacts
of ``scripts/generate_live_gui_protocol_ts.py``. These tests run the generator
in-process and fail when either committed artifact drifts from the Python
TypedDict contracts (the single source of truth). The sibling test module
``test_live_gui_protocol_ts_matches_python_typeddicts.py`` stays as the
field-level parity net; this module pins the whole file byte-for-byte.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

from rytm_randomizer.reports.live_gui_performance_console_model import (
    live_gui_performance_console_model_payload,
)

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
GENERATOR_PATH: Final[Path] = PROJECT_ROOT / "scripts" / "generate_live_gui_protocol_ts.py"
PROTOCOL_TS_PATH: Final[Path] = (
    PROJECT_ROOT / "desktop" / "web" / "src" / "types" / "live_gui_protocol.ts"
)
FIXTURE_JSON_PATH: Final[Path] = (
    PROJECT_ROOT / "desktop" / "web" / "tests" / "cockpit" / "fixtures" / "performance_console.json"
)
_GENERATOR_MODULE_NAME: Final[str] = "_generate_live_gui_protocol_ts_under_test"
_REGENERATE_HINT: Final[str] = (
    "regenerate with: python scripts/generate_live_gui_protocol_ts.py --fixture"
)


def _load_generator() -> ModuleType:
    assert GENERATOR_PATH.is_file(), f"missing generator script: {GENERATOR_PATH}"
    spec = importlib.util.spec_from_file_location(_GENERATOR_MODULE_NAME, GENERATOR_PATH)
    assert (
        spec is not None and spec.loader is not None
    ), f"could not build an import spec for {GENERATOR_PATH}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[_GENERATOR_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(_GENERATOR_MODULE_NAME, None)
    return module


def test_committed_protocol_ts_matches_generator_output() -> None:
    """live_gui_protocol.ts is byte-identical to the in-process generator output."""

    generator = _load_generator()
    committed = PROTOCOL_TS_PATH.read_text(encoding="utf-8")
    generated = generator.render_live_gui_protocol_ts()

    assert committed == generated, (
        "desktop/web/src/types/live_gui_protocol.ts is stale relative to the "
        f"Python TypedDict contracts; {_REGENERATE_HINT}"
    )


def test_committed_protocol_ts_carries_generated_banner() -> None:
    """The committed TS file declares itself generated so nobody hand-edits it."""

    committed = PROTOCOL_TS_PATH.read_text(encoding="utf-8")

    assert "GENERATED" in committed and "generate_live_gui_protocol_ts.py" in committed, (
        "desktop/web/src/types/live_gui_protocol.ts must keep the GENERATED banner "
        "pointing at scripts/generate_live_gui_protocol_ts.py"
    )


def test_committed_fixture_matches_generator_output() -> None:
    """The performance-console JSON fixture is byte-identical to the generator output."""

    generator = _load_generator()
    committed = FIXTURE_JSON_PATH.read_text(encoding="utf-8")
    generated = generator.render_performance_console_fixture_json()

    assert committed == generated, (
        "desktop/web/tests/cockpit/fixtures/performance_console.json is stale; "
        f"{_REGENERATE_HINT}"
    )


def test_committed_fixture_matches_live_payload() -> None:
    """The JSON fixture equals the live passive payload, not just its formatting."""

    committed = json.loads(FIXTURE_JSON_PATH.read_text(encoding="utf-8"))
    # Normalize the payload through JSON semantics (tuples become arrays) so
    # the comparison checks content, not Python container types.
    live_payload = json.loads(json.dumps(live_gui_performance_console_model_payload()))

    assert committed == live_payload, (
        "desktop/web/tests/cockpit/fixtures/performance_console.json no longer "
        "matches live_gui_performance_console_model_payload(); "
        f"{_REGENERATE_HINT}"
    )

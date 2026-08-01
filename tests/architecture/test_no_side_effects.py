"""Enforce no I/O at module import time across the package.

The package contract (see ``docs/ARCHITECTURE.md`` section 4 "House-style
rules") is that importing any ``rytm_randomizer.*`` submodule must:

* produce nothing on stdout,
* produce nothing on stderr,
* open no MIDI port,
* not call ``input()``,
* not pull ``mido`` / ``rtmidi`` into ``sys.modules``.

This is the property test that locks down the contract for the WHOLE package
(an extension of the per-module pattern in
``tests/test_real_midi_import_safety.py``). Construction of the runtime stack
must happen explicitly from ``app.py`` via the ``--arm`` flag.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"
PACKAGE_NAME = "rytm_randomizer"
RUSH01_TOOL_PATHS = (
    PROJECT_ROOT / "scripts" / "rush01_midi_apply.py",
    PROJECT_ROOT / "scripts" / "rush01_midi_learn.py",
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _all_package_modules() -> list[str]:
    """Return every fully-qualified module name under ``rytm_randomizer/``."""

    out: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        rel = path.relative_to(PROJECT_ROOT).with_suffix("")
        parts = rel.parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        out.append(".".join(parts))
    return sorted(set(out))


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# Importing every package module is silent
# ---------------------------------------------------------------------------


def test_importing_every_package_module_is_silent() -> None:
    """No stdout / stderr / exit-code drift from importing any package module."""

    imports = "\n".join(f"import {m}" for m in _all_package_modules())
    result = _run_python(imports)

    assert result.returncode == 0, (
        f"Importing the package produced a non-zero exit code:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout == "", (
        "Importing rytm_randomizer.* must produce no stdout. Got:\n" + result.stdout
    )
    assert result.stderr == "", (
        "Importing rytm_randomizer.* must produce no stderr. Got:\n" + result.stderr
    )


# ---------------------------------------------------------------------------
# Importing every package module does NOT pull mido / rtmidi into sys.modules
# ---------------------------------------------------------------------------


def test_importing_every_package_module_does_not_pull_mido() -> None:
    """Importing the package must NEVER eagerly load mido / rtmidi."""

    imports = "\n".join(f"import {m}" for m in _all_package_modules())
    code = (
        "import sys\n"
        f"{imports}\n"
        'for module_name in ("mido", "rtmidi", "pythonrtmidi"):\n'
        "    assert module_name not in sys.modules, module_name\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


# ---------------------------------------------------------------------------
# Importing every package module does NOT call input()
# ---------------------------------------------------------------------------


def test_importing_every_package_module_does_not_call_input() -> None:
    """If any module called ``input()`` at import time, the subprocess would block."""

    imports = "\n".join(f"import {m}" for m in _all_package_modules())
    code = (
        "import builtins\n"
        "def _no_input(prompt=''):\n"
        "    raise AssertionError('input() must not be called at import time')\n"
        "builtins.input = _no_input\n"
        f"{imports}\n"
        "print('ok')\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, (
        f"input() was called at import time (or another import-time error fired):\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "ok"


# ---------------------------------------------------------------------------
# Importing every package module does NOT open any MIDI port
# ---------------------------------------------------------------------------


def test_importing_every_package_module_does_not_open_ports() -> None:
    """Even with a fake ``mido`` injected, no open_output / open_input call is made."""

    imports = "\n".join(f"import {m}" for m in _all_package_modules())
    code = (
        "import sys\n"
        "import types\n"
        "fake_mido = types.ModuleType('mido')\n"
        "def _explode(*a, **kw):\n"
        "    raise AssertionError('MIDI port opened at import time: ' + str(a))\n"
        "fake_mido.open_output = _explode\n"
        "fake_mido.open_input = _explode\n"
        "fake_mido.get_output_names = _explode\n"
        "fake_mido.get_input_names = _explode\n"
        "sys.modules['mido'] = fake_mido\n"
        f"{imports}\n"
        "print('ok')\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, (
        f"A MIDI port was opened at import time:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout.strip() == "ok"


# ---------------------------------------------------------------------------
# Per-module sanity: each module imports cleanly in isolation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_name", _all_package_modules())
def test_each_module_imports_cleanly_in_isolation(module_name: str) -> None:
    """Each module must import in a fresh Python without stdout / stderr."""

    result = _run_python(f"import {module_name}")
    assert result.returncode == 0, (
        f"Importing {module_name} failed:\n" f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout == "", f"{module_name} produced stdout: {result.stdout!r}"
    assert result.stderr == "", f"{module_name} produced stderr: {result.stderr!r}"


@pytest.mark.parametrize("tool_path", RUSH01_TOOL_PATHS, ids=lambda path: path.stem)
def test_rush01_top_level_tools_have_no_active_midi_calls(tool_path: Path) -> None:
    """Standalone RUSH01 tools remain passive by construction."""

    tree = ast.parse(tool_path.read_text(encoding="utf-8"), filename=str(tool_path))
    forbidden_imports: list[str] = []
    forbidden_calls: list[str] = []
    forbidden_names = {
        "MidoMidiPortProvider",
        "build_mido_midi_port_provider",
        "open_input",
        "open_output",
        "send_cc",
        "send_param",
        "send_nrpn",
        "apply_rush01_plan",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            forbidden_imports.extend(
                alias.name for alias in node.names if alias.name.split(".")[0] in {"mido", "rtmidi"}
            )
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in {
            "mido",
            "rtmidi",
        }:
            forbidden_imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                forbidden_calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute) and node.func.attr in forbidden_names:
                forbidden_calls.append(node.func.attr)

    assert forbidden_imports == []
    assert forbidden_calls == []


@pytest.mark.parametrize(
    ("tool_path", "expected_code"),
    ((RUSH01_TOOL_PATHS[0], 2), (RUSH01_TOOL_PATHS[1], 0)),
    ids=("rush01_midi_apply", "rush01_midi_learn"),
)
def test_rush01_tool_default_paths_open_nothing(
    tool_path: Path,
    expected_code: int,
) -> None:
    """Import and default execution remain hardware-free with a hostile fake backend."""

    code = f"""
import sys
import types
import importlib.util
fake_mido = types.ModuleType('mido')
def explode(*args, **kwargs):
    raise AssertionError('standalone RUSH01 tool touched MIDI')
fake_mido.open_output = explode
fake_mido.open_input = explode
fake_mido.get_output_names = explode
fake_mido.get_input_names = explode
sys.modules['mido'] = fake_mido
spec = importlib.util.spec_from_file_location('rush01_tool_under_test', {str(tool_path)!r})
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from io import StringIO
result = module.run((), stdout=StringIO(), stderr=StringIO())
assert result == {expected_code}, result
"""
    result = _run_python(code)
    assert result.returncode == 0, result.stderr

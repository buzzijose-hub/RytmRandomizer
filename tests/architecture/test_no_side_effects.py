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

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"
PACKAGE_NAME = "rytm_randomizer"

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
        "Importing rytm_randomizer.* must produce no stdout. Got:\n"
        + result.stdout
    )
    assert result.stderr == "", (
        "Importing rytm_randomizer.* must produce no stderr. Got:\n"
        + result.stderr
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
        f"Importing {module_name} failed:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert result.stdout == "", f"{module_name} produced stdout: {result.stdout!r}"
    assert result.stderr == "", f"{module_name} produced stderr: {result.stderr!r}"

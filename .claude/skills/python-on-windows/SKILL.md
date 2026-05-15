---
name: python-on-windows
description: How to reliably invoke Python in this Windows repo environment. **MUST be consulted before ANY Python invocation in a subagent or background command** — the bare `python`/`python.exe`/`py`/`python3` commands frequently fail with "specified disk or diskette cannot be accessed" because Windows Store ships shim executables in `%LOCALAPPDATA%\Microsoft\WindowsApps\` that throw when invoked from non-interactive subprocesses. Use this skill whenever you need to run pytest, install packages, or execute any Python script.
---

# Python invocation on this Windows environment

## The problem

This repo runs on a Windows machine where Python is installed via the Microsoft Store. Windows ships **stub executables** at `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe` (and `python3.exe`, `py.exe`) that are *Store shims*, not real interpreters. Calling them from a non-interactive subprocess (the way agents and background tasks invoke Python) frequently throws:

> The system cannot find the path specified.
> OR
> The specified disk or diskette cannot be accessed.

Agents have repeatedly failed verification runs by invoking `python` and hitting this trap.

## The reliable invocations (use these)

### Option 1 (preferred for one-off invocations) — the real interpreter's absolute path

```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" --version
```

This is the real installed interpreter. It bypasses the Store shim entirely.

A reusable shell variable approach:

```bash
PYTHON="/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe"
"$PYTHON" --version
"$PYTHON" -m pytest -q
"$PYTHON" -m pip install -e ".[dev]"
```

### Option 2 (preferred for repeated work) — create and activate a venv

If you're doing multiple Python invocations (installing deps, running pytest several times), create a venv once and reuse it:

```bash
"/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe" -m venv .venv
source .venv/Scripts/activate    # git-bash on Windows
# .venv\Scripts\Activate.ps1     # PowerShell
# .venv\Scripts\activate.bat     # cmd
python -m pip install -e ".[dev]"
python -m pytest -q
```

Inside an activated venv, the bare `python` / `pip` commands work reliably — they resolve to the venv's own `python.exe`, not the Store shim.

`.venv/` is in `.gitignore`.

### Option 3 (when the working directory is the main repo and git-bash is the shell) — bare `python` *sometimes* works

From an interactive git-bash session in the main repo, `where python` may resolve through `PATH` to the real interpreter. But this is **not reliable from agent subprocesses or background commands**. Use Option 1 or 2 instead — do not rely on `python` alone.

## What NOT to do

- ❌ `python -m pytest` (from an agent/subprocess context)
- ❌ `python.exe ...`
- ❌ `py ...`
- ❌ `python3 ...` (same Store shim issue)
- ❌ `& python.exe` in PowerShell

When you see "specified disk or diskette cannot be accessed", you've hit the shim. Stop and use Option 1 above.

## Verifying you have the real interpreter

```bash
"$PYTHON" -c "import sys; print(sys.executable)"
```

The output should be a path under `C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.13_*\python3.13.exe` (or your venv's path). If it's anything under `WindowsApps\` *without* `PythonSoftwareFoundation.` — that's the shim, and you'll hit the error.

## When to invoke this skill

- **Any time you write `python ...` in a Bash, PowerShell, or shell tool call** — consult this skill first.
- **Any time a previous run failed with "cannot find path", "specified disk", or "Microsoft Store" Python-related errors** — switch to Option 1.
- **Any time you're about to install pip packages or run pytest in a background task** — use Option 1 or 2 explicitly.
- **In agent prompts** — when delegating Python work to a subagent, include the absolute path or a venv setup as the first instruction.

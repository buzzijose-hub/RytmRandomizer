---
name: reference-pre-push-hook-windows-shim
description: RytmRandomizer .githooks/pre-push fails on Windows Store python shim; PR
metadata: 
  node_type: memory
  type: reference
  originSessionId: b2a9f27a-6737-437c-b063-6015a588d52d
---

RytmRandomizer's `.githooks/pre-push` hook had a long-standing Windows-only bug: it resolved python via plain `command -v` which on Windows returns the Microsoft Store stub executables under `%LOCALAPPDATA%\Microsoft\WindowsApps\`. Those stubs throw "Permission denied" / "The system cannot find the path specified" when invoked from a subprocess.

**Fix (PR #110, 2026-05-25):** the hook now probes each candidate (`python3`, `python`, `py`, then explicit `/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_*/python3.13.exe` fallbacks) with `--version` before accepting it. If none works, the hook logs and exits 0 (CI's architecture job remains the server-side backstop).

**How to apply:**
- If a Windows push fails with the shim error, PR #110's fix is the canonical resolution
- If you're on `modularize-v1.34` from before PR #110 merged, the hook still has the broken discovery — use `--no-verify` for non-code commits (docs, tracker updates) and run the gate manually via `scripts/code_review_gate.py --mode git-hook` with the absolute Python path for code commits
- Absolute Python on the Windows dev box: `/c/Program Files/WindowsApps/PythonSoftwareFoundation.Python.3.13_3.13.3568.0_x64__qbz5n2kfra8p0/python3.13.exe`

Related: [[python_tooling_pitfalls]] covers the broader Windows Store Python trap.

#!/usr/bin/env python3
"""Run strict Pyright on every production module touched by the current branch."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CONFIG_PATH: Final[Path] = REPO_ROOT / "pyrightconfig.strict.json"
DEFAULT_BASE_REF: Final[str] = "origin/modularize-v1.34"
BASE_REF_ENV: Final[str] = "TYPECHECK_BASE_REF"
GITHUB_BASE_REF_ENV: Final[str] = "GITHUB_BASE_REF"
PRODUCTION_ROOT: Final[str] = "rytm_randomizer"
PYTHON_SUFFIX: Final[str] = ".py"
GIT_EXECUTABLE: Final[str | None] = shutil.which("git")


def _run_git(arguments: Sequence[str], *, repo_root: Path) -> tuple[str, ...]:
    """Run one read-only Git query and return its non-empty output lines."""

    if GIT_EXECUTABLE is None:
        raise RuntimeError("git executable was not found on PATH")
    completed = subprocess.run(
        [GIT_EXECUTABLE, *arguments],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return tuple(line.strip() for line in completed.stdout.splitlines() if line.strip())


def resolve_base_ref(environment: dict[str, str] | None = None) -> str:
    """Resolve the explicit, GitHub, or repository-default integration base."""

    values = os.environ if environment is None else environment
    explicit = values.get(BASE_REF_ENV, "").strip()
    if explicit:
        return explicit
    github_base = values.get(GITHUB_BASE_REF_ENV, "").strip()
    if github_base:
        return f"origin/{github_base}"
    return DEFAULT_BASE_REF


def _is_production_python(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(f"{PRODUCTION_ROOT}/") and normalized.endswith(PYTHON_SUFFIX)


def _existing_production_paths(paths: Sequence[str], *, repo_root: Path) -> set[str]:
    selected: set[str] = set()
    for path in paths:
        normalized = path.replace("\\", "/")
        if not _is_production_python(normalized):
            continue
        candidate = repo_root / Path(normalized)
        if candidate.is_file():
            selected.add(normalized)
    return selected


def collect_touched_production_files(
    *,
    repo_root: Path = REPO_ROOT,
    base_ref: str | None = None,
) -> tuple[str, ...]:
    """Return committed, working-tree, and untracked touched production modules."""

    resolved_base = resolve_base_ref() if base_ref is None else base_ref
    merge_base_lines = _run_git(
        ("merge-base", "HEAD", resolved_base),
        repo_root=repo_root,
    )
    if len(merge_base_lines) != 1:
        raise RuntimeError(f"could not resolve one merge base for {resolved_base}")
    merge_base = merge_base_lines[0]
    pathspec = ("--", f"{PRODUCTION_ROOT}/**/*.py", f"{PRODUCTION_ROOT}/*.py")
    committed = _run_git(
        (
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            f"{merge_base}...HEAD",
            *pathspec,
        ),
        repo_root=repo_root,
    )
    working = _run_git(
        ("diff", "--name-only", "--diff-filter=ACMR", "HEAD", *pathspec),
        repo_root=repo_root,
    )
    untracked = _run_git(
        ("ls-files", "--others", "--exclude-standard", *pathspec),
        repo_root=repo_root,
    )
    selected = _existing_production_paths(
        (*committed, *working, *untracked),
        repo_root=repo_root,
    )
    return tuple(sorted(selected))


def _validate_config(config_path: Path = CONFIG_PATH) -> None:
    """Fail clearly when the strict config is missing or no longer strict."""

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("strict Pyright config must contain a JSON object")
    if payload.get("typeCheckingMode") != "strict":
        raise ValueError("strict Pyright config must set typeCheckingMode to strict")
    if payload.get("pythonVersion") != "3.11":
        raise ValueError("strict Pyright config must target Python 3.11")


def main() -> int:
    """Run the pinned Pyright module on the dynamic production diff."""

    try:
        _validate_config()
        files = collect_touched_production_files()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Strict production typecheck setup failed: {exc}", file=sys.stderr)
        return 2

    print(f"Strict production typecheck: {len(files)} touched module(s)", flush=True)
    for path in files:
        print(f"  {path}", flush=True)
    if not files:
        return 0

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--project",
            str(CONFIG_PATH),
            "--pythonpath",
            sys.executable,
            *files,
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

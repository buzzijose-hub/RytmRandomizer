"""Dependency invariants for cockpit and packaged sidecar runtime paths."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAFE_FASTAPI_REQUIREMENT = "fastapi>=0.110.0,<0.136.3"


def _pyproject() -> dict[str, object]:
    return tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _optional_dependencies(pyproject: dict[str, object]) -> dict[str, list[str]]:
    project = pyproject["project"]
    assert isinstance(project, dict)
    optional = project["optional-dependencies"]
    assert isinstance(optional, dict)
    return optional


def _briefcase_requires(pyproject: dict[str, object]) -> dict[str, list[str]]:
    tool = pyproject["tool"]
    assert isinstance(tool, dict)
    briefcase = tool["briefcase"]
    assert isinstance(briefcase, dict)
    apps = briefcase["app"]
    assert isinstance(apps, dict)
    app = apps["rytm-randomizer"]
    assert isinstance(app, dict)
    return {
        "default": app["requires"],
        "macOS": app["macOS"]["requires"],
        "linux": app["linux"]["requires"],
        "windows": app["windows"]["requires"],
    }


def test_dev_extra_contains_cockpit_and_style_runtime_dependencies() -> None:
    pyproject = _pyproject()
    optional = _optional_dependencies(pyproject)

    expected = set(optional["cockpit"]) | set(optional["style"])
    missing = expected.difference(optional["dev"])

    assert missing == set()


def test_briefcase_runtime_contains_cockpit_and_style_dependencies() -> None:
    pyproject = _pyproject()
    optional = _optional_dependencies(pyproject)
    expected = set(optional["cockpit"]) | set(optional["style"])

    missing_by_target = {
        target: sorted(expected.difference(requirements))
        for target, requirements in _briefcase_requires(pyproject).items()
    }

    assert missing_by_target == {
        "default": [],
        "macOS": [],
        "linux": [],
        "windows": [],
    }


def test_cockpit_fastapi_requirement_excludes_flagged_release() -> None:
    pyproject = _pyproject()
    optional = _optional_dependencies(pyproject)
    runtime_targets = {
        "dev": optional["dev"],
        "cockpit": optional["cockpit"],
        **_briefcase_requires(pyproject),
    }

    fastapi_requirements = {
        target: [requirement for requirement in requirements if requirement.startswith("fastapi")]
        for target, requirements in runtime_targets.items()
    }

    assert fastapi_requirements == {
        "dev": [SAFE_FASTAPI_REQUIREMENT],
        "cockpit": [SAFE_FASTAPI_REQUIREMENT],
        "default": [SAFE_FASTAPI_REQUIREMENT],
        "macOS": [SAFE_FASTAPI_REQUIREMENT],
        "linux": [SAFE_FASTAPI_REQUIREMENT],
        "windows": [SAFE_FASTAPI_REQUIREMENT],
    }

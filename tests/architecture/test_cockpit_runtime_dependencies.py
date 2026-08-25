"""Dependency invariants for cockpit and packaged sidecar runtime paths."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAFE_FASTAPI_REQUIREMENT = "fastapi>=0.110.0,!=0.136.3,<0.141.2"
DEPENDABOT_CONFIG = PROJECT_ROOT / ".github" / "dependabot.yml"
# The single FastAPI release pip-audit flags as MAL-2026-4750. Excluded from
# SAFE_FASTAPI_REQUIREMENT via `!=` and mirrored in the dependabot ignore
# list; the tie-test below keeps the two exclusions from drifting apart.
FLAGGED_FASTAPI_VERSION = "0.136.3"


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


def test_safe_fastapi_requirement_excludes_flagged_release() -> None:
    """The canonical requirement must reject the MAL-2026-4750 release.

    If SAFE_FASTAPI_REQUIREMENT is ever edited so the flagged version
    slips back inside the allowed range, this fails before pip-audit
    would catch it in CI.
    """

    from packaging.requirements import Requirement
    from packaging.version import Version

    requirement = Requirement(SAFE_FASTAPI_REQUIREMENT)
    assert Version(FLAGGED_FASTAPI_VERSION) not in requirement.specifier, (
        f"SAFE_FASTAPI_REQUIREMENT ({SAFE_FASTAPI_REQUIREMENT!r}) admits "
        f"fastapi {FLAGGED_FASTAPI_VERSION}, which pip-audit flags as "
        f"MAL-2026-4750. Restore the `!={FLAGGED_FASTAPI_VERSION}` "
        f"exclusion (or a cap below it)."
    )


def test_dependabot_ignore_covers_flagged_fastapi_release() -> None:
    """The dependabot ignore list mirrors the pyproject fastapi exclusion.

    Tie-test: the `!=0.136.3` exclusion in pyproject.toml and the fastapi
    ignore entry in .github/dependabot.yml must never drift apart. Without
    the ignore entry, dependabot would open a PR proposing the flagged
    release; without the pyproject exclusion, pip could resolve it.
    """

    yaml = pytest.importorskip("yaml")
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    config = yaml.safe_load(DEPENDABOT_CONFIG.read_text(encoding="utf-8"))
    updates = config.get("updates") or []
    pip_updates = [update for update in updates if update.get("package-ecosystem") == "pip"]
    assert pip_updates, (
        ".github/dependabot.yml has no pip package-ecosystem update block; "
        "the fastapi ignore entry has nowhere to live."
    )

    fastapi_entries = [
        entry
        for update in pip_updates
        for entry in (update.get("ignore") or [])
        if entry.get("dependency-name") == "fastapi"
    ]
    assert fastapi_entries, (
        ".github/dependabot.yml's pip ignore list has no fastapi entry. "
        f"pyproject.toml excludes fastapi {FLAGGED_FASTAPI_VERSION} "
        "(MAL-2026-4750); dependabot must mirror that exclusion or it "
        "will keep proposing the flagged release."
    )

    flagged = Version(FLAGGED_FASTAPI_VERSION)
    covered = any(
        flagged in SpecifierSet(spec)
        for entry in fastapi_entries
        for spec in (entry.get("versions") or [])
    )
    assert covered, (
        "The fastapi ignore entry in .github/dependabot.yml does not cover "
        f"version {FLAGGED_FASTAPI_VERSION}. Its `versions:` specifiers "
        f"must match the flagged release, e.g. "
        f'[">={FLAGGED_FASTAPI_VERSION}, <0.136.4"].'
    )

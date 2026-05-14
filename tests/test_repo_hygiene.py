from __future__ import annotations

from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_repo_hygiene_files_exist():
    expected_paths = (
        "README.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "SECURITY.md",
        "CHANGELOG.md",
        "pyproject.toml",
        ".python-version",
        ".github/CODEOWNERS",
        ".github/pull_request_template.md",
        ".github/workflows/test.yml",
        ".github/workflows/codeql.yml",
        ".github/workflows/release.yml",
        ".github/dependabot.yml",
        "Docs/STATUS.md",
    )

    for relative_path in expected_paths:
        assert (PROJECT_ROOT / relative_path).exists(), relative_path


def test_repo_hygiene_docs_name_current_branch_and_safety_boundaries():
    status = (PROJECT_ROOT / "Docs/STATUS.md").read_text(encoding="utf-8")

    assert "codex/execute-eddie-plan" in status
    assert "real MIDI: absent in modular passive commands" in status
    assert "port opening: absent in modular passive commands" in status
    assert "active execution: absent in modular passive commands" in status
    assert "hardware required: no for tests and passive CLI" in status


def test_pull_request_template_requires_safety_evidence():
    template = (PROJECT_ROOT / ".github/pull_request_template.md").read_text(
        encoding="utf-8"
    )

    assert "Closeout" in template
    assert "V1.34" in template
    assert "MIDI" in template
    assert "hardware" in template


def test_codeql_workflow_is_manual_until_code_scanning_is_enabled():
    workflow = (PROJECT_ROOT / ".github/workflows/codeql.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "push:" not in workflow
    assert "schedule:" not in workflow


def test_test_workflow_installs_linux_midi_build_dependency():
    workflow = (PROJECT_ROOT / ".github/workflows/test.yml").read_text(
        encoding="utf-8"
    )

    assert "Install Ubuntu MIDI build dependencies" in workflow
    assert "runner.os == 'Linux'" in workflow
    assert "libasound2-dev" in workflow


def test_quality_gate_dependencies_and_coverage_config_are_declared():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    dev_dependencies = pyproject["project"]["optional-dependencies"]["dev"]
    assert "pytest-cov>=5,<8" in dev_dependencies

    coverage_run = pyproject["tool"]["coverage"]["run"]
    assert coverage_run["branch"] is True
    assert coverage_run["source"] == ["rytm_randomizer"]

    coverage_report = pyproject["tool"]["coverage"]["report"]
    assert coverage_report["fail_under"] == 84
    assert coverage_report["show_missing"] is True


def test_test_workflow_runs_package_coverage_gate():
    workflow = (PROJECT_ROOT / ".github/workflows/test.yml").read_text(
        encoding="utf-8"
    )

    assert "Run package coverage gate" in workflow
    assert "python -m pytest --cov=rytm_randomizer --cov-branch --cov-fail-under=84" in workflow


def test_pre_commit_configuration_declares_house_style_tools():
    config = (PROJECT_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "pre-commit-hooks" in config
    assert "black" in config
    assert "ruff-pre-commit" in config
    assert "mirrors-isort" in config
    assert "trailing-whitespace" in config
    assert "end-of-file-fixer" in config


def test_package_build_gate_is_declared_for_distribution_safety():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    workflow = (PROJECT_ROOT / ".github/workflows/test.yml").read_text(
        encoding="utf-8"
    )
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    dev_dependencies = pyproject["project"]["optional-dependencies"]["dev"]
    assert "build>=1,<2" in dev_dependencies
    assert "Build package artifacts" in workflow
    assert "python -m build" in workflow
    assert "python -m build" in readme

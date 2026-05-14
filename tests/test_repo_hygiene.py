from __future__ import annotations

from pathlib import Path


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

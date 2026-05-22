"""Tests for the repository PR creation helper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CREATE_PR_PATH = PROJECT_ROOT / "scripts" / "create_pr.py"


def _load_create_pr():
    """Import scripts/create_pr.py as a one-off module for testing."""

    spec = importlib.util.spec_from_file_location("create_pr_under_test", CREATE_PR_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_create_command_requests_eddie(tmp_path):
    """Default PR creation must request Eddie without a manual GitHub click."""

    create_pr = _load_create_pr()
    body_file = tmp_path / "body.md"
    options = create_pr.PullRequestOptions(title="chore: demo", body_file=body_file)

    command = create_pr.build_create_command(options)

    assert command == [
        "gh",
        "pr",
        "create",
        "--base",
        "modularize-v1.34",
        "--reviewer",
        "edward-rosado",
        "--title",
        "chore: demo",
        "--body-file",
        str(body_file),
    ]


def test_reviewer_normalization_keeps_default_first_and_dedupes():
    """Additional reviewers are allowed, but Eddie stays the default first request."""

    create_pr = _load_create_pr()

    reviewers = create_pr.normalize_reviewers(
        ["edward-rosado", "buzzijose-hub", "", "buzzijose-hub"]
    )

    assert reviewers == ("edward-rosado", "buzzijose-hub")


def test_dry_run_prints_shell_quoted_command(tmp_path, capsys):
    """Dry-run mode lets humans verify the reviewer flag without creating a PR."""

    create_pr = _load_create_pr()
    body_file = tmp_path / "body with spaces.md"

    result = create_pr.main(
        [
            "--title",
            "chore: reviewer request",
            "--body-file",
            str(body_file),
            "--dry-run",
        ]
    )

    assert result == 0
    out = capsys.readouterr().out
    assert "gh pr create --base modularize-v1.34" in out
    assert "--reviewer edward-rosado" in out
    assert "'chore: reviewer request'" in out
    assert "body with spaces.md'" in out


def test_main_delegates_constructed_command_to_runner(tmp_path):
    """The CLI entry point should pass the exact command to the supplied runner."""

    create_pr = _load_create_pr()
    body_file = tmp_path / "body.md"
    calls: list[tuple[str, ...]] = []

    def fake_runner(command):
        calls.append(tuple(command))
        return 17

    result = create_pr.main(
        [
            "--title",
            "chore: reviewer request",
            "--body-file",
            str(body_file),
            "--head",
            "codex/demo",
            "--reviewer",
            "buzzijose-hub",
            "--draft",
        ],
        runner=fake_runner,
    )

    assert result == 17
    assert calls == [
        (
            "gh",
            "pr",
            "create",
            "--base",
            "modularize-v1.34",
            "--head",
            "codex/demo",
            "--reviewer",
            "edward-rosado",
            "--reviewer",
            "buzzijose-hub",
            "--title",
            "chore: reviewer request",
            "--body-file",
            str(body_file),
            "--draft",
        )
    ]

"""Create repository PRs with the required default reviewer request."""

from __future__ import annotations

import argparse
import shlex
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

DEFAULT_BASE: Final[str] = "modularize-v1.34"
DEFAULT_REVIEWER: Final[str] = "edward-rosado"

Runner = Callable[[Sequence[str]], int]


@dataclass(frozen=True)
class PullRequestOptions:
    """Inputs needed to build the repository's `gh pr create` command."""

    title: str
    body_file: Path
    base: str = DEFAULT_BASE
    reviewers: tuple[str, ...] = (DEFAULT_REVIEWER,)
    head: str | None = None
    draft: bool = False


def normalize_reviewers(reviewers: Sequence[str] = ()) -> tuple[str, ...]:
    """Return reviewers with the required default first and duplicates removed."""

    normalized: list[str] = []
    seen: set[str] = set()

    for candidate in (DEFAULT_REVIEWER, *reviewers):
        reviewer = candidate.strip()
        if not reviewer or reviewer in seen:
            continue
        normalized.append(reviewer)
        seen.add(reviewer)

    return tuple(normalized)


def build_create_command(options: PullRequestOptions) -> list[str]:
    """Build the `gh pr create` command without running it."""

    command = ["gh", "pr", "create", "--base", options.base]
    if options.head is not None:
        command.extend(["--head", options.head])
    for reviewer in normalize_reviewers(options.reviewers):
        command.extend(["--reviewer", reviewer])
    command.extend(["--title", options.title, "--body-file", str(options.body_file)])
    if options.draft:
        command.append("--draft")
    return command


def run_command(command: Sequence[str]) -> int:
    """Run a prepared subprocess command and return its exit code."""

    completed = subprocess.run(list(command), check=False)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Create a GitHub PR against the integration branch while requesting "
            "the repository's default reviewer."
        )
    )
    parser.add_argument("--title", required=True, help="Pull request title.")
    parser.add_argument(
        "--body-file",
        required=True,
        type=Path,
        help="Path to the pull request body markdown file.",
    )
    parser.add_argument(
        "--base",
        default=DEFAULT_BASE,
        help=f"Base branch for the pull request. Defaults to {DEFAULT_BASE}.",
    )
    parser.add_argument("--head", help="Optional head branch override.")
    parser.add_argument(
        "--reviewer",
        action="append",
        default=[],
        help=(
            "Additional reviewer to request. The default reviewer "
            f"{DEFAULT_REVIEWER} is always included first."
        ),
    )
    parser.add_argument("--draft", action="store_true", help="Open the PR as a draft.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the gh command without creating a pull request.",
    )
    return parser


def main(argv: Sequence[str] | None = None, *, runner: Runner = run_command) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    options = PullRequestOptions(
        title=args.title,
        body_file=args.body_file,
        base=args.base,
        reviewers=normalize_reviewers(args.reviewer),
        head=args.head,
        draft=args.draft,
    )
    command = build_create_command(options)
    if args.dry_run:
        print(shlex.join(command))
        return 0
    return runner(command)


if __name__ == "__main__":
    raise SystemExit(main())

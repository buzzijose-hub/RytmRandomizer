"""Tests for shared passive live-GUI report helpers."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_live_gui_common_formats_cli_errors_and_status_severity():
    from rytm_randomizer.reports.live_gui_common import format_cli_error, status_severity

    assert format_cli_error(ValueError("missing source")) == "Error: missing source"
    assert status_severity("blocked") == "critical"
    assert status_severity("review-needed") == "warning"
    assert status_severity("ready") == "info"


def test_live_gui_common_pops_option_values_or_raises_usage():
    from rytm_randomizer.reports.live_gui_common import pop_option_value

    remaining = ["warehouse"]

    assert pop_option_value(remaining, usage="usage text") == "warehouse"
    assert remaining == []
    with pytest.raises(ValueError, match="usage text"):
        pop_option_value(remaining, usage="usage text")


def test_live_gui_common_rewrites_replay_commands_with_quoted_extra_options():
    from rytm_randomizer.reports.live_gui_common import replace_replay_command

    command = "python -m rytm_randomizer.cli source-report --description 'x'"

    rewritten = replace_replay_command(
        command,
        source_command="source-report",
        target_command="target-report",
        extra_options=(
            ("--label", "Main warehouse label"),
            ("--selector-prefix", "studio"),
        ),
    )

    assert rewritten == (
        "python -m rytm_randomizer.cli target-report --description 'x' "
        "--label 'Main warehouse label' --selector-prefix studio"
    )
    assert (
        replace_replay_command(
            command,
            source_command="missing-report",
            target_command="target-report",
            extra_options=(),
        )
        is None
    )

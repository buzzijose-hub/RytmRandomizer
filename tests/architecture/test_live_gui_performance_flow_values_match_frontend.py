"""The cockpit performance-flow default must mirror the Python report values.

PR #155 promoted the cockpit performance flow (PR #153/#154) into a passive
Python report and declared it the repo-owned source of truth. The
TypedDict<->interface mirror in
``test_live_gui_protocol_ts_matches_python_typeddicts.py`` pins the *field
names*, but not the *values*. This guard pins the actual step data and replay
commands so the frontend default
(``desktop/web/src/cockpit/LiveReadinessPanel.tsx`` ->
``DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL``) cannot silently drift from
``rytm_randomizer/reports/live_gui_performance_flow_model.py``.

``safety_lines`` are intentionally *not* pinned: the frontend reuses a shared
``PASSIVE_SAFETY`` constant across many surfaces, while the Python report carries
its own report-specific lines. The flow steps and replay commands are the
load-bearing payload and must stay aligned.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
REPORT_PY: Final[Path] = (
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_performance_flow_model.py"
)
PANEL_TS: Final[Path] = (
    PROJECT_ROOT / "desktop" / "web" / "src" / "cockpit" / "LiveReadinessPanel.tsx"
)

# The frontend flowStep(...) positional argument order, which is the same field
# order the Python LiveGuiPerformanceFlowStep dataclass declares.
_STEP_FIELDS: Final[tuple[str, ...]] = (
    "key",
    "order",
    "label",
    "phase",
    "rytm_command",
    "analog_four_action",
    "send_policy",
    "recovery_action",
    "status",
)


def _python_default_steps_and_replay() -> tuple[tuple[tuple[object, ...], ...], tuple[str, ...]]:
    tree = ast.parse(REPORT_PY.read_text(encoding="utf-8"))
    steps: list[tuple[object, ...]] = []
    replay: tuple[str, ...] | None = None
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == "LiveGuiPerformanceFlowStep"
        ):
            keywords = {
                kw.arg: kw.value.value for kw in node.keywords if isinstance(kw.value, ast.Constant)
            }
            steps.append(tuple(keywords[name] for name in _STEP_FIELDS))
        if isinstance(node, ast.Assign):
            target_names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_names = [node.target.id]
            value = node.value
        else:
            continue
        if "REPLAY_COMMANDS" in target_names and isinstance(value, ast.Tuple):
            replay = tuple(
                element.value for element in value.elts if isinstance(element, ast.Constant)
            )
    assert steps, "could not parse DEFAULT_STEPS from the Python report"
    assert replay is not None, "could not parse REPLAY_COMMANDS from the Python report"
    return tuple(steps), replay


def _frontend_default_block() -> str:
    source = PANEL_TS.read_text(encoding="utf-8")
    match = re.search(
        r"DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL.*?\n\};",
        source,
        re.DOTALL,
    )
    assert match, "could not locate DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL in LiveReadinessPanel.tsx"
    return match.group(0)


def _frontend_steps(block: str) -> tuple[tuple[object, ...], ...]:
    steps: list[tuple[object, ...]] = []
    for call in re.finditer(r"flowStep\(([^)]*)\)", block):
        raw = [arg.strip() for arg in call.group(1).split(",")]
        raw = [arg for arg in raw if arg != ""]
        if len(raw) != len(_STEP_FIELDS):
            continue
        key = raw[0].strip("'")
        order = int(raw[1])
        rest = [arg.strip("'") for arg in raw[2:]]
        steps.append((key, order, *rest))
    return tuple(steps)


def _frontend_replay(block: str) -> tuple[str, ...]:
    match = re.search(r"replay_commands:\s*\[([^\]]*)\]", block, re.DOTALL)
    assert match, "could not locate replay_commands array in the frontend default"
    return tuple(item.strip().strip("'\"") for item in match.group(1).split(",") if item.strip())


def test_frontend_performance_flow_steps_match_python_report() -> None:
    """Frontend default flow steps mirror the Python report DEFAULT_STEPS."""

    python_steps, _ = _python_default_steps_and_replay()
    frontend_steps = _frontend_steps(_frontend_default_block())
    assert frontend_steps == python_steps, (
        "LiveReadinessPanel.tsx DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL steps must mirror "
        "rytm_randomizer/reports/live_gui_performance_flow_model.py DEFAULT_STEPS "
        f"value-for-value.\nPython:   {python_steps!r}\nFrontend: {frontend_steps!r}"
    )


def test_frontend_performance_flow_replay_commands_match_python_report() -> None:
    """Frontend default replay commands mirror the Python report REPLAY_COMMANDS."""

    _, python_replay = _python_default_steps_and_replay()
    frontend_replay = _frontend_replay(_frontend_default_block())
    assert frontend_replay == python_replay, (
        "LiveReadinessPanel.tsx DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL replay_commands must "
        "mirror the Python report REPLAY_COMMANDS (each must be a runnable passive CLI "
        f"command).\nPython:   {python_replay!r}\nFrontend: {frontend_replay!r}"
    )

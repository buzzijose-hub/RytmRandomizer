# WS-S4 — PassiveReportFormatter

**Worktree:** `RytmRandomizer-worktrees/ws-s4-passive-report-formatter`
**Branch:** `refactor/passive-report-formatter`
**Base:** `modularize-v1.34 @ 0bd46aa`

Per `docs/PLAN_REQUIREMENTS.md`: all 16 gates. Special focus on Gate 9 (subpackage by default).

## Overview

Extract the duplicated "Safety:" footer rendering + per-report header convention from `reports.py` (1265 LOC), `project_status_report.py`, `inspection.py` into `rytm_randomizer/reports/formatter.py`. Convert `reports.py` → `reports/__init__.py` to follow Gate 9 subpackage discipline (matches existing `data/`, `engines/`, `state/` patterns).

## Inventory: 7 footer call sites

| # | File | Line | Owning formatter | Pattern |
|---|---|---|---|---|
| 1 | reports.py | 120-121 | `format_registry_report` | trailing 2-line Source/InMemory |
| 2 | reports.py | 321-337 | `format_active_boundary_report` | "Active Boundary Safety:" custom — NOT migrated |
| 3 | reports.py | 440-441 | `format_mock_mapper_report` | trailing 2-line Source/InMemory |
| 4 | reports.py | 613-626 | `format_runtime_plan_report` | "Runtime Plan Safety:" + trailing 2-line |
| 5 | reports.py | 932-934 | `format_anchor_profile_report` | "Safety:" + iterate `source_report["safety"]` |
| 6 | reports.py | 1421-1434 | `format_mock_runtime_active_bridge_report` | "Safety:" hand-listed + trailing 2-line |
| 7 | project_status_report.py | 466-476 | `format_project_status_report` | "Safety:" + iterate + literal trailing Source: block |

5/7 use the trailing `"Source: rytm_randomizer.X" / "In-memory only: True"` pair.
2/7 use the `for key, value in source_report["safety"].items()` iterate pattern.
4/7 use hand-rendered safety bodies (kept as-is).

## Formatter API (new `rytm_randomizer/reports/formatter.py`)

```python
SAFETY_SECTION_HEADER: Final[str] = "Safety:"
PASSIVE_FOOTER_SOURCE_TEMPLATE: Final[str] = "Source: rytm_randomizer.{module}"
PASSIVE_FOOTER_MEMORY_LINE: Final[str] = "In-memory only: True"
PASSIVE_FOOTER: Final[tuple[str, str]] = (PASSIVE_FOOTER_SOURCE_TEMPLATE, PASSIVE_FOOTER_MEMORY_LINE)

@dataclass(frozen=True)
class PassiveReportHeader:
    title: str
    source_module: str | None = None
    include_memory_line: bool = True

def safety_section_lines(safety: Mapping[str, object]) -> list[str]: ...
def passive_footer_lines(source_module: str, *, include_memory_line: bool = True) -> list[str]: ...
def render_passive_report(header: PassiveReportHeader, body_lines: Iterable[str]) -> str: ...
def passive_report_lines(header: PassiveReportHeader, body_lines: Iterable[str]) -> list[str]: ...
```

Per Gate 6: frozen dataclass, no `Any`, no `Mapping[str, Any]` DTOs. Per Gate 12: all module-level constants `Final`.

## Decision: convert `reports.py` to `reports/__init__.py`

**Option C** (chosen): `git mv rytm_randomizer/reports.py rytm_randomizer/reports/__init__.py`; add `rytm_randomizer/reports/formatter.py`. Matches existing subpackage precedent (`data/`, `engines/`, `state/`). All 8 caller import paths (`from rytm_randomizer.reports import ...`) continue to work unchanged.

Option A (flat new `reports_formatter.py`) rejected — violates Gate 9.
Option B (subpackage co-existing with reports.py) rejected — Python forbids it.

## Migration phases (8 steps)

1. `git mv reports.py reports/__init__.py` (file move only).
2. Add docstring paragraph + placeholder `from .formatter import ...` line.
3. Write `rytm_randomizer/reports/formatter.py` (full content above).
4. Migrate `format_registry_report` first (smallest, no Safety: literal).
5a-5c. Migrate `format_mock_mapper_report`, `format_runtime_plan_report`, `format_mock_runtime_active_bridge_report` (trailing 2-line pattern).
6a-6b. Migrate `format_anchor_profile_report`, `format_project_status_report` (iterate pattern).
7. Promote `fixture_text()` / `normalize_newlines()` to `tests/conftest.py` (Gate 11 prep — WS-M4 coordinates).
8. doc-updater + acceptance + PR open.

## Byte-for-byte invariant

7 golden fixtures in `tests/fixtures/cli_*_report_expected.txt` are the source of truth. Every commit re-runs:

```powershell
pytest tests/test_registry_report.py tests/test_registry_report_cli.py tests/test_active_boundary_report.py tests/test_mock_mapper_report.py tests/test_runtime_plan_report.py tests/test_behavior_anchor_profile_report.py tests/test_mock_runtime_active_bridge_report.py tests/test_behavior_parity_coverage_report.py tests/test_project_status_report.py tests/test_active_runtime_report_alignment.py -v
```

Any single byte differs → revert that commit, re-dispatch tdd-guide.

## TDD: failing tests written FIRST

New file `tests/test_reports_formatter.py` (~150 LOC) covering:
- Module public surface (`__all__` exports).
- Constants exactly match canonical literals.
- `PassiveReportHeader` is frozen dataclass.
- `safety_section_lines` preserves insertion order; empty dict → header-only.
- `passive_footer_lines` with/without `include_memory_line`.
- `render_passive_report` + `passive_report_lines` round-trip.
- Import safety: no mido/rtmidi pulled in; no `_logger` attached (Gate 7 carve-out for pure text rendering).

## Acceptance commands

```powershell
# Byte-identical golden fixtures
pytest tests/test_registry_report.py tests/test_registry_report_cli.py tests/test_active_boundary_report.py tests/test_mock_mapper_report.py tests/test_runtime_plan_report.py tests/test_behavior_anchor_profile_report.py tests/test_mock_runtime_active_bridge_report.py tests/test_behavior_parity_coverage_report.py tests/test_project_status_report.py tests/test_active_runtime_report_alignment.py -v

# New formatter tests
pytest tests/test_reports_formatter.py -v

# Gate 1 (100% branch on touched)
pytest --cov=rytm_randomizer.reports --cov=rytm_randomizer.reports.formatter --cov=rytm_randomizer.project_status_report --cov-branch --cov-fail-under=100

# Gate 4 (dead code)
vulture rytm_randomizer/reports rytm_randomizer/project_status_report.py --min-confidence 80
ruff check --select F401,F811,F841,ARG001,ARG002,ERA001 rytm_randomizer/reports rytm_randomizer/project_status_report.py

# Gate 3 (lint/format/type)
ruff check rytm_randomizer/reports rytm_randomizer/project_status_report.py tests/test_reports_formatter.py
black --check ...
isort --profile black --check-only ...
pyright --strict rytm_randomizer/reports rytm_randomizer/project_status_report.py

# Gate 2 (parity)
pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py

# Smoke
pytest -x --no-header -q
```

## Risks

| Risk | Mitigation |
|---|---|
| `git mv` loses blame history | Single explicit `git mv`; verify with `git log --follow`. |
| Custom-header report ("Active Boundary Safety:") accidentally migrated to `safety_section_lines` | Section 2 mapping table explicitly excludes; step 5d codifies "no formatter changes" for active_boundary. |
| `format_project_status_report`'s trailing literal Source: block tempts API expansion | Documented carve-out; not in scope. |
| Cascade-rebase conflict on docs/STATUS.md | Gate 16 keep-both rule auto-resolves. |

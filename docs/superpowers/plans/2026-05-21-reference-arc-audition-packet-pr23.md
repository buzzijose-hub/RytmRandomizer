# Reference Arc Audition Packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one passive operator command that evaluates the reference-arc readiness matrix, chooses the best arc for the supplied saved kit banks, and prints the selected timed set-plan preview in the same report.

**Architecture:** Reuse the merged `build_style_performance_arc_readiness_report()` and `format_style_performance_arc_set_plan_report()` paths. Keep the implementation inside `rytm_randomizer/reports/style_performance_arcs.py` plus existing passive CLI/help/docs surfaces. Do not render real MIDI, open ports, or create new top-level modules.

**Tech Stack:** Python 3.13, frozen dataclasses, existing passive CLI registry/help, existing dual-machine style performance planner, pytest, ruff, black, isort, vulture, and repo review gates.

---

### Task 1: Add Audition Packet Tests

**Files:**
- Modify: `tests/test_style_performance_arcs_report.py`

- [x] **Step 1: Add report build/format/JSON tests**

Add a test named `test_style_performance_arc_audition_packet_selects_best_arc_and_embeds_plan`.

The test should:
- create the existing `_arc_bank_files(tmp_path)` Rytm/A4 fixtures
- call `build_style_performance_arc_audition_packet_report()`
- assert the selected entry exists and belongs to the readiness matrix
- assert the selected set plan equals the selected entry plan
- assert formatted text includes the packet title, selected arc, readiness matrix summary, selected set-plan section, and passive safety lines
- assert JSON includes `selected`, `readiness_matrix`, `selected_set_plan`, and `safety`

- [x] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_audition_packet_selects_best_arc_and_embeds_plan -n 0
```

Expected: fail with `ImportError` because the packet API does not exist yet.

### Task 2: Implement Audition Packet Core

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`

- [x] **Step 1: Add report dataclass**

Add:

```python
@dataclass(frozen=True)
class StylePerformanceArcAuditionPacketReport:
    readiness_report: StylePerformanceArcReadinessReport
    selected_entry: StylePerformanceArcReadinessEntry
```

- [x] **Step 2: Add builder**

Add `build_style_performance_arc_audition_packet_report()` with the same matrix arguments:

```python
arc_keys: Sequence[str] | None = None
rytm_sysex_path: Path | None = None
analog_four_sysex_path: Path | None = None
scope: str | None = None
selection_rank: int | None = None
total_minutes: int | None = None
segment_minutes: int | None = None
discovery_start: int | None = None
discovery_end: int | None = None
```

It should call the readiness report builder and select the first ranked entry. If there are no entries, raise a clear `ValueError`.

- [x] **Step 3: Add formatter and JSON**

Add:

```python
format_style_performance_arc_audition_packet_report(
    report: StylePerformanceArcAuditionPacketReport,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]

to_style_performance_arc_audition_packet_json(
    report: StylePerformanceArcAuditionPacketReport,
) -> dict[str, object]
```

Formatter should include a compact packet summary, readiness totals, selected arc action, and selected set-plan lines. JSON should reuse existing readiness and set-plan serializers.

- [x] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_audition_packet_selects_best_arc_and_embeds_plan -n 0
```

Expected: pass.

### Task 3: Add CLI Command

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_style_performance_arcs_report.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add parser/handler and CLI tests**

Add parser/handler tests for `_parse_arc_audition_packet_cli_args()` and `_handle_style_performance_arc_audition_packet_report()`.

Add CLI dispatch coverage for:

```bash
python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --rytm <syx-path> --analog-four <syx-path> --events --limit 1
```

- [x] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py -n 0
```

Expected: fail until parser/handler/CLI/help are wired.

- [x] **Step 3: Wire command**

Add `STYLE_PERFORMANCE_ARC_AUDITION_PACKET_CLI_COMMAND`, register it, add lazy CLI mapping, and add help text.

Syntax:

```bash
python -m rytm_randomizer.cli style-performance-arc-audition-packet-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
```

- [x] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: pass.

### Task 4: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Update docs**

Add README example and status entry describing the passive audition packet.

- [x] **Step 2: Run closeout gates**

Run:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest tests/test_style_performance_arcs_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m vulture rytm_randomizer/cli.py rytm_randomizer/help_text.py rytm_randomizer/reports/style_performance_arcs.py tests/test_cli.py tests/test_style_performance_arcs_report.py --min-confidence 80
python scripts/code_review_gate.py --mode cli
```

Expected: all pass.

### Task 5: Publish PR

**Files:**
- Stage only the files listed in this plan.

- [ ] **Step 1: Commit**

```bash
git add README.md docs/STATUS.md docs/superpowers/plans/2026-05-21-reference-arc-audition-packet-pr23.md rytm_randomizer/cli.py rytm_randomizer/help_text.py rytm_randomizer/reports/style_performance_arcs.py tests/fixtures/cli_help_expected.txt tests/test_cli.py tests/test_style_performance_arcs_report.py
git commit -m "feat: add reference arc audition packet"
```

- [ ] **Step 2: Push and open PR**

Push `codex/reference-arc-audition-packet-pr23` and open a ready PR against `modularize-v1.34`.

- [ ] **Step 3: Watch CI and post review comment**

Watch checks, post the Codex self-review comment, and merge only if review/checks allow it.

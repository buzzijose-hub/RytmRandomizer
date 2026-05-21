# Rytm Snapshot Mutation Operator Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make the passive Rytm snapshot mutation preview actionable by optionally showing the exact mock CC rows the guarded planner would render.

**Architecture:** Extend the existing `reports/rytm_snapshot_mutation_preview.py` report in place. The report will continue to decode a selected `.syx` slot, route snapshot machine facts through `AnalogRytmDevice.mutation_planner`, and render through `guarded_send`; the new detail mode only formats the already-rendered mock messages and never opens MIDI or imports real MIDI libraries.

**Tech Stack:** Python 3.11+ / 3.13 local, pytest, existing `Device` Strategy seam, existing passive CLI registry, existing mock MIDI message shape.

---

## Scope

This is one PR against `modularize-v1.34`, not a stacked PR.

In scope:

- Add optional `--events` output to `rytm-snapshot-mutation-preview-report`.
- Add optional `--limit N` cap for event rows; default to a bounded value when events are requested.
- Preserve the current summary-only output when `--events` is omitted.
- Include event rows with pad, profile key, parameter, channel, CC, and value.
- Keep all behavior passive/mock-only.

Out of scope:

- Real hardware sends.
- Continuous live snapshot tracking.
- SysEx capture from connected devices.
- Analog Four snapshot mutation details.
- New top-level modules or new device abstractions.

## File Map

- Modify `rytm_randomizer/reports/rytm_snapshot_mutation_preview.py`
  - Add an immutable event row DTO.
  - Store event rows in `RytmSnapshotMutationPreviewReport`.
  - Add `include_events` and `event_limit` formatting controls.
  - Parse `--events` and `--limit N`.
- Modify `rytm_randomizer/help_text.py`
  - Update command-specific help for the new flags.
- Modify `tests/test_rytm_snapshot_mutation_preview_report.py`
  - Add unit tests for event rows, limits, default behavior, and parser errors.
- Modify `tests/test_cli.py`
  - Add subprocess CLI tests for `--events` and README freshness.
- Keep `tests/test_cli_coverage.py` unchanged unless coverage exposes a CLI branch gap.
  - Parser branch coverage lives in `tests/test_rytm_snapshot_mutation_preview_report.py`.
- Modify `tests/fixtures/cli_rytm_snapshot_mutation_preview_report_help_expected.txt`
  - Update help fixture.
- Modify `README.md`
  - Document the operator event-detail mode.
- Modify `docs/STATUS.md`
  - Add a concise recent cleanup entry.

## Task 1: Event Row Contract

- [x] **Step 1: Write failing unit tests**

Add tests proving:

```python
lines = format_rytm_snapshot_mutation_preview_report(
    _promoted_snapshot_for_mutable_pads(),
    depth=1,
    include_events=True,
    event_limit=3,
)
assert "Event preview:" in lines
assert "- Showing first 3 of " in "\n".join(lines)
assert any("Pad 1 | profile 2 | SRC Tune | ch 0 | CC17 ->" in line for line in lines)
```

Also assert summary-only output does not include `Event preview:`.

- [x] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_rytm_snapshot_mutation_preview_report.py -n 0
```

Expected: fail because `include_events` / `event_limit` do not exist yet.

- [x] **Step 3: Implement event rows**

Add:

```python
@dataclass(frozen=True)
class RytmSnapshotMutationPreviewEvent:
    pad: int
    profile_key: str
    parameter: str
    channel: int
    control: int
    value: int
```

Build rows from `GuardedSendResult.messages`, reading metadata from `MidiMessage.metadata`.

- [x] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest tests/test_rytm_snapshot_mutation_preview_report.py -n 0
```

Expected: pass.

## Task 2: CLI Flags

- [x] **Step 1: Write failing parser/CLI tests**

Add tests proving:

```python
parsed = _parse_cli_args(["kit.syx", "--events", "--limit", "4"])
assert parsed["include_events"] is True
assert parsed["event_limit"] == 4
```

And reject:

```python
["kit.syx", "--limit"]
["kit.syx", "--limit", "not-int"]
["kit.syx", "--limit", "-1"]
```

- [x] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_rytm_snapshot_mutation_preview_report.py tests/test_cli.py -n 0
```

Expected: fail on missing parser support.

- [x] **Step 3: Implement parser support**

Update `_parse_cli_args()` to accept order-independent `--events` and `--limit N`. `--limit 0` means show all event rows; positive limits show the first N rows.

- [x] **Step 4: Verify GREEN**

Run:

```bash
python -m pytest tests/test_rytm_snapshot_mutation_preview_report.py tests/test_cli.py -n 0
```

Expected: pass.

## Task 3: Help, Docs, Safety

- [x] **Step 1: Update help fixture and README**

Add usage lines:

```text
python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --events
python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --events --limit N
```

Document that event rows are mock-only and capped for readability.

- [x] **Step 2: Run focused CLI and passive safety tests**

Run:

```bash
python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py tests/test_rytm_snapshot_mutation_preview_report.py -n 0
```

Expected: pass.

## Task 4: Closeout

- [x] **Step 1: Run full verification**

Run:

```bash
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python scripts\code_review_gate.py --mode cli
python -m vulture rytm_randomizer/reports/rytm_snapshot_mutation_preview.py tests/test_rytm_snapshot_mutation_preview_report.py tests/test_cli.py tests/test_cli_coverage.py --min-confidence 80
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
```

- [ ] **Step 2: Commit, push, and open PR**

Stage only the intentional paths. Include this plan doc in the PR and link it from the PR body.

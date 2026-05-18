# PR #21 Rebase Guide — Codex Hand-off

**For:** the codex agent owning `codex/dual-machine-mock-bridge` (PR #21).
**From:** `modularize-v1.34` post-PR #35 (Wave 1 bundle merged).
**Expected diff after rebase:** ~5-8k LOC (down from ~30k pre-rebase).

This guide is the **in-repo** authoritative migration plan per Gate 15 (`docs/PLAN_REQUIREMENTS.md`). GitHub issues can be closed; this file is forever.

---

## 1. Why this rebase exists

PR #21 ships an Analog Four implementation alongside the existing Analog Rytm one. Pre-rebase, the PR adds ~33 new top-level files because four abstractions didn't exist on base:

- No `Device` Protocol → each new device duplicates its boilerplate.
- No `SnapshotDecoder` / `MutationPlanner` base → each device re-implements the same decode/plan shape.
- No CLI command registry → every new command grows `cli.py` inline (PR #21 had +1,313 LOC on `cli.py` alone).
- No `PassiveReportFormatter` → "Safety:" + "Source:" + "In-memory only: True" strings duplicated across N modules.
- No generic Elektron SysEx envelope → `_find_kit_record` / `_unpack_elektron_7bit` / `_read_ascii_name` duplicated per device.
- No observability metrics → per-CC counters hand-rolled in each device.

PR #35 lands all six abstractions. PR #21 rebases onto them and the diff collapses.

---

## 2. The eight collapse points

### 2.1 `Device` Protocol (`rytm_randomizer/devices/base.py`)

**What it is:** a `@runtime_checkable` Protocol declaring the cross-machine boundary — `device_id`, `display_name`, `default_midi_channel`, `track_count`, `sysex_manufacturer_id`, plus `decode_snapshot(...)`, `plan_mutation(...)`, `to_mock_messages(...)`, `to_cc_messages(...)`.

**What collapses:** PR #21's 8 `analog_four_*.py` files collapse into one `rytm_randomizer/devices/analog_four.py` (mirrors `rytm_randomizer/devices/analog_rytm.py`).

**Migration steps:**

1. Create `rytm_randomizer/devices/analog_four.py`.
2. Define `class AnalogFourDevice:` with the 5 Protocol attributes (`device_id="analog_four_mk2"`, `display_name="Analog Four MKII"`, `default_midi_channel=...`, `track_count=4`, `sysex_manufacturer_id=ELEKTRON_MFR_ID`).
3. Implement the 4 Protocol methods (decode_snapshot, plan_mutation, to_mock_messages, to_cc_messages) by pulling the bodies from the 8 `analog_four_*.py` files in PR #21.
4. Register at import time: `register(AnalogFourDevice())` (the `devices/__init__.py` pattern).
5. Delete all 8 `analog_four_*.py` files; their content is now inside `devices/analog_four.py`.

**Expected LOC change:** -2,400 (8 files * ~300 LOC each = 2,400) → +400 (one consolidated file) = **-2,000 net.**

### 2.2 `MidiSender` Protocol (`rytm_randomizer/midi_io.py`)

**What it is:** the canonical `Protocol` for any object that can `send_cc(channel, cc, value)`. Replaced 6 `Sender = Any` aliases.

**What collapses:** PR #21's hand-written sender shims (e.g. `_AnalogFourSender`, `_DualMachineBridge`) now have a canonical contract; PR #21's local shims either are deleted (if they were just `Any`-typed wrappers) or annotate themselves as implementing `MidiSender`.

**Migration steps:**

1. Grep PR #21 for `Sender = Any` or untyped sender parameters: `grep -rn 'Sender\s*=\s*Any' codex-fork/`.
2. Replace each with `from rytm_randomizer.midi_io import MidiSender` + `Sender = MidiSender`.
3. For each hand-written sender shim, either delete (if redundant) or add `class XSender:` (no inheritance — Protocol is structural) with the matching `send_cc` signature.

**Expected LOC change:** -150.

### 2.3 `snapshot/envelope.py` (`rytm_randomizer/snapshot/envelope.py`)

**What it is:** generic Elektron SysEx envelope decoder — `ELEKTRON_MFR_ID: Final[bytes]` constant + pure helpers `unpack_elektron_7bit`, `find_kit_record`, `read_ascii_name`, `format_manufacturer_id`. All raise `ValueError` on malformed input. See `.claude/skills/learned/elektron-sysex-envelope/` for the format reference.

**What collapses:** PR #21's duplicated `_find_kit_record` / `_unpack_elektron_7bit` / `_read_ascii_name` helpers (currently appearing in 4 places across the Analog Four files) collapse to single-line imports.

**Migration steps:**

1. Grep PR #21 for the duplicated helpers: `grep -rn '_unpack_elektron_7bit\|_find_kit_record\|_read_ascii_name' codex-fork/`.
2. Replace each definition with `from rytm_randomizer.snapshot.envelope import unpack_elektron_7bit, find_kit_record, read_ascii_name`.
3. Delete the duplicate function bodies.
4. Update call sites: rename to use the canonical names (no leading underscore).

**Expected LOC change:** -300 (4 duplications * ~75 LOC each).

### 2.4 `snapshot/decoder.py` + `snapshot/planner.py` + `snapshot/mock_runtime.py`

**What they are:**

- `SnapshotDecoder(@runtime_checkable Protocol)` — `decode(payload: bytes) -> Mapping[str, object]`.
- `MutationPlanner(@runtime_checkable Protocol)` — `plan(state, intensity) -> Mapping[str, object]`.
- `MockRuntime(@runtime_checkable Protocol)` + `BaseMockRuntime(ABC)` — common mock runtime base taking a `MidiOutbox`.

**What collapses:** PR #21's per-device decoder / planner / mock-runtime classes inherit / satisfy these Protocols instead of redefining the contract.

**Migration steps:**

1. PR #21's `AnalogFourSnapshotDecoder` → make it a regular class with a `decode(payload)` method matching the Protocol.
2. PR #21's `AnalogFourMutationPlanner` → same shape as `SnapshotDecoder`.
3. PR #21's `AnalogFourMockRuntime` → inherit from `BaseMockRuntime` instead of redefining the constructor / message-buffer logic.

**Expected LOC change:** -500.

### 2.5 `cli_registry.py` (`rytm_randomizer/cli_registry.py`)

**What it is:** `CliCommand` frozen dataclass + `register` / `get` / `all_commands` / `default_error_formatter` registry surface.

**What collapses:** PR #21's +1,313 LOC diff on `cli.py` becomes `register(CliCommand(name="...", handler=...))` calls per command. The CLI dispatcher itself (the consumer of the registry) is a deferred refactor on base — but the registry is in place, so PR #21's commands register instead of growing `cli.py` inline.

**Migration steps:**

1. For each new command PR #21 adds to `cli.py`, extract the handler into its own module under `rytm_randomizer/cli_commands/` (or alongside the device module).
2. Replace the inline `cli.py` arm with `from .cli_registry import register, CliCommand` + a `register(CliCommand(...))` call.
3. Delete the inline `cli.py` additions.

**Expected LOC change:** -1,100 (PR #21's cli.py diff was +1,313; collapses to ~200 LOC of registry calls + handler modules).

### 2.6 `reports/formatter.py` (`rytm_randomizer/reports/formatter.py`)

**What it is:** the canonical "Safety:" / "Source:" / "In-memory only: True" strings + `PassiveReportHeader` frozen dataclass + helpers `safety_section_lines` / `passive_footer_lines` / `render_passive_report` / `passive_report_lines`.

**What collapses:** PR #21's duplicated `"Safety:"` and `"In-memory only: True"` literals across its new device's reports collapse to `from rytm_randomizer.reports.formatter import render_passive_report` and a single call.

**Migration steps:**

1. Grep PR #21 for the literals: `grep -rn '"Safety:"\|"In-memory only: True"' codex-fork/`.
2. Replace each duplicated render block with a call to `render_passive_report(header=PassiveReportHeader(...))`.

**Expected LOC change:** -200.

### 2.7 `observability/metrics.py` (`rytm_randomizer/observability/metrics.py`)

**What it is:** `MidiMetrics` dataclass with `Counter` fields (`cc_sent_by_channel`, `cc_blocked_by_guardrail_by_pad`, `errors_by_kind`) + `record_*` methods + `format_summary()` + module-level singleton via `get_metrics()` / `reset_metrics()`.

**What collapses:** PR #21's per-CC counters (hand-rolled `_count_cc_sent` dicts on the Analog Four runtime) integrate into the central singleton via `get_metrics().record_cc_sent(channel)`.

**Migration steps:**

1. Grep PR #21 for per-device counter dicts: `grep -rn '_cc_sent\|_cc_blocked\|self\..*= 0$' codex-fork/devices/`.
2. Replace each with `from rytm_randomizer.observability.metrics import get_metrics` + a single `get_metrics().record_cc_sent(channel=...)` call per send-site.
3. Delete the per-device counters and their `_format_metrics` helpers.

**Expected LOC change:** -250.

### 2.8 `data/modes.py` (`rytm_randomizer/data/modes.py`)

**What it is:** `IntensityMode`/`PageMode`/`MutationKind`/`Pad1Mode`/`ZoneName` `Literal` aliases + `INTENSITY_MODES`/`PAGE_MODES`/`MUTATION_KINDS`/`PAD1_MODES`/`ZONE_NAMES` `Final[tuple]` constants.

**What collapses:** any new string-equality dispatch PR #21 introduces (probably on `"analog_four"` vs `"analog_rytm"` device-kind) goes through the `data/modes.py` pattern from the start, not as a follow-up cleanup.

**Migration steps:**

1. If PR #21 introduces any new dispatch strings, add them to `data/modes.py` as a `Literal[...]` alias + `Final[tuple]` constant.
2. Use the alias in type hints; use the tuple as the dispatch keys.

**Expected LOC change:** +50 (new `DeviceKind` literal addition), but adds Gate 10 compliance.

---

## 3. The mechanical rebase

```powershell
# 1. Fetch the new base.
git fetch origin modularize-v1.34

# 2. Identify codex's actual commits (not the 91 phantom commits — see
#    .claude/skills/learned/rebase-after-squash-merge/).
$mb = git merge-base origin/modularize-v1.34 HEAD
git log --oneline "$mb..HEAD"   # find the real codex commits

# 3. Reset to the new base; cherry-pick the real commits.
git reset --hard origin/modularize-v1.34
git cherry-pick <real-commit-1> <real-commit-2> ...

# 4. Work through the 8 collapse points above, file by file.
#    Run the parity tests after each collapse: pytest tests/test_engines_pad*.py -q
#    Run the architecture tests: pytest tests/architecture/ -q
#    Run the full suite: pytest -q

# 5. Force-push (you own this branch).
git push --force-with-lease
```

---

## 4. Acceptance criteria (PR #21 ready for review)

- [ ] All 8 collapse points applied; PR #21's new top-level file count drops from 33 → <10.
- [ ] All 685 V1.34 parity fixtures still byte-identical.
- [ ] `pytest tests/architecture/` green (no `Sender = Any` re-introduced, no string-literal dispatch outside `data/modes.py`, etc.).
- [ ] `python -m pyright --strict <touched paths>` clean.
- [ ] `python -m ruff check .` + `python -m black --check .` clean.
- [ ] PR #21 body cites this guide and updates `docs/PR21_MODULE_MAPPING.md` if any of the 8 collapse points needed adjustment.

---

## 5. If something doesn't fit

If a PR #21 module genuinely doesn't fit any of the 8 collapse points, **do not** invent a new top-level module. Either:

- Extend an existing Protocol (e.g. add a method to `Device` if every device needs it), OR
- Add a new subpackage with an `architect` agent sign-off, OR
- File a follow-up issue and leave the module in PR #21 with a TODO comment citing the issue.

The Gate 9 rule (no new top-level modules without architect sign-off) is binding even during the rebase.

---

## 6. Cross-references

- `docs/PR21_MODULE_MAPPING.md` — file-by-file mapping table.
- `docs/ARCHITECTURE_BEFORE_AFTER.md` — the new Protocol / dataclass surface in detail.
- `.claude/skills/learned/elektron-sysex-envelope/` — the format reference for any new device.
- `.claude/skills/learned/rebase-after-squash-merge/` — the mechanical rebase pattern.
- `docs/PLAN_REQUIREMENTS.md` — the 16 gates PR #21 inherits.

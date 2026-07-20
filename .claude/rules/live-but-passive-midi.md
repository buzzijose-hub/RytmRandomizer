# Live-but-Passive MIDI safety model — mandatory rule

**Authority:** This file + [`docs/superpowers/plans/2026-07-18-rival-program.md`](../../docs/superpowers/plans/2026-07-18-rival-program.md) §1 (maintainer-approved 2026-07-18) + `tests/architecture/test_armed_entry_points.py` and `tests/architecture/test_repo_root_perimeter.py` (mechanical enforcement).
**Scope:** Any code — package, tooling, scripts, tests, cockpit — that enumerates MIDI ports, opens a MIDI port, or sends a single outbound byte toward the Elektron hardware.

## The rule

The application is **live but passive** by default:

- **Inputs are free.** Launch may enumerate ports (`list_input_names`, `list_output_names`) and open MIDI **inputs** at any time, without arming and without confirmation. Read-only listening (including SysEx capture) never interrupts the device's sound output and gives the operator immediate connection-health feedback. This half of the model is never restricted.
- **Outputs are armed.** Every **outbound** transmit — constructing a real output port, defining a hardware send — routes through the `senders` ArmedApply seam, behind an explicit **in-UI arm action + confirmation**. There is no "transmit because a port happened to be open" path.
- **Arming never survives a disconnect.** After a device reconnect (cable pull, power cycle, backend restart), the app returns to the passive state. Never auto-re-arm.
- **Backup before mutation.** Any kit/sound mutation transmitted to hardware is preceded by an automatic pre-write backup of the affected kit/sound, so every armed write is reversible.

## What you MUST do

1. **Route all outbound MIDI through the `senders` ArmedApply seam** (`rytm_randomizer/senders/guarded.py` + `senders/hardware.py`). Engines, runners, and plans call `midi_io.send_cc` on a **dependency-injected** `Sender` protocol; whether that sender is a mock or a real port is decided at the armed boundary, never at the call site.
2. **Keep the transmit whitelist shrinking.** `_ALLOWED_TRANSMIT_MODULES` in `tests/architecture/test_armed_entry_points.py` is the frozen set of modules allowed to construct real output ports or define the hardware send. Adding an entry requires reviewer sign-off recorded in the PR body; the long-term direction is that WS-4 folds entry points into the seam and entries come OFF the list.
3. **Keep `import mido` / `import rtmidi` inside the boundary modules only** — `real_midi_adapter.py`, `mido_provider.py`, and (lazily, in-method) `midi_io.py`. Enforced repo-wide (not just package-wide) by `test_repo_root_perimeter.py`.
4. **Precede every hardware kit/sound write with an automatic backup** of the target, taken through the passive read path.
5. **Run both enforcement modules before pushing anything MIDI-adjacent:**
   ```bash
   .venv/bin/python -m pytest tests/architecture/test_armed_entry_points.py tests/architecture/test_repo_root_perimeter.py -q
   ```

## What you MUST NOT do

- **Do not gate input opening or port enumeration behind arming.** Passive listening is the product's connection-health signal; restricting it breaks the model in the other direction.
- **Do not construct a real output port or define a hardware send outside the whitelist.** No new top-level `tools/` script with its own `open_output(...)` (the PR #213 failure mode); no per-feature "quick send" helpers.
- **Do not auto-re-arm after reconnect,** persist an armed flag across sessions, or arm implicitly as a side effect of another action. Arming is an explicit, per-session, in-UI operator decision.
- **Do not transmit a kit/sound mutation without the pre-write backup.**
- **Do not put `import mido` / `from mido` at module top level anywhere in the repo,** including tooling and tests.
- **Do not fork a second guarded-send implementation.** One ArmedApply seam; devices plug in via the `devices/` registry.

## When this rule applies

- Any PR touching `rytm_randomizer/senders/`, `mido_provider.py`, `real_midi_adapter.py`, `midi_io.py`, `app.py`, `shell.py`, or `cockpit/device/`.
- Any new operator entry point (CLI command, cockpit action, script) that could reach hardware.
- Any change to `tests/architecture/test_armed_entry_points.py` or `test_repo_root_perimeter.py` allowlists.

## When this rule does NOT apply

- Pure mock-path work (`mock_midi`, engines, runners against injected mock senders) — no arming involved, nothing to gate.
- Passive read-only tooling that only enumerates ports or captures input.

## Cross-references

- `tests/architecture/test_armed_entry_points.py` — the transmit-path whitelist (output construction + hardware-send definitions).
- `tests/architecture/test_repo_root_perimeter.py` — repo-wide mido/rtmidi import scan + top-level directory allowlist.
- [`docs/superpowers/plans/2026-07-18-rival-program.md`](../../docs/superpowers/plans/2026-07-18-rival-program.md) §1 — the approved safety model.
- [`.claude/rules/architecture.md`](architecture.md) — layer map + direction rule 9 (import boundary).
- [`CLAUDE.md`](../../CLAUDE.md) hard rules 7–8 — the per-session distillation of this rule.
- [`.claude/rules/device-protocol-strategy.md`](device-protocol-strategy.md) — devices plug into the generic guarded sender via `plan.ready` / `readiness_reason`.

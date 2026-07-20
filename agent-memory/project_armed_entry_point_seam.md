---
name: project-armed-entry-point-seam
description: "Live-but-Passive MIDI boundary: inputs open freely, all transmit via senders ArmedApply seam; enforced by test_armed_entry_points.py + test_repo_root_perimeter.py"
metadata:
  node_type: memory
  type: project
---

# Armed entry-point seam (Live-but-Passive MIDI boundary)

Maintainer-approved 2026-07-18 (rival-program plan §1): the app is **live but
passive** — launch may enumerate ports and open MIDI **inputs** freely
(read-only listening, never interrupts the device's sound output), while every
**output/transmit** routes through the `senders` ArmedApply seam behind an
explicit in-UI arm + confirmation. Never auto-re-arm after a reconnect; take an
automatic pre-write backup before any kit/sound mutation.

## The two enforcing tests

1. `tests/architecture/test_armed_entry_points.py` — transmit-path whitelist.
   Scans `rytm_randomizer/` for `open_output(` / `def hardware_send` /
   `def guarded*(`; only `_ALLOWED_TRANSMIT_MODULES` (mido_provider,
   real_midi_adapter, senders/hardware, senders/guarded, plus armed
   entrypoints app.py / shell.py / cockpit/device/real.py pending WS-4) may
   match. The whitelist only ever SHRINKS. Injected `send_cc(sender, ...)`
   calls and all input/enumeration APIs are deliberately NOT flagged.
2. `tests/architecture/test_repo_root_perimeter.py` — repo-WIDE (not just
   package) `import mido`/`rtmidi` scan. Boundary =
   `real_midi_adapter.py`, `mido_provider.py`, and (lazy, in-method)
   `midi_io.py`. Also enforces the top-level-directory allowlist that would
   have caught PR #213's rogue `tools/` armed script.

## When adding MIDI-adjacent code

Route outbound bytes through the ArmedApply seam; never add a new
`open_output` call site. Whitelist additions require reviewer sign-off in the
PR body. Canonical rule: `.claude/rules/live-but-passive-midi.md`.

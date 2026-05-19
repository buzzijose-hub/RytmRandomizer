# Hardware-pinned packages — mandatory rule

**Authority:** This file + [`pyproject.toml`](../../pyproject.toml) `[project] dependencies` + [`CONTRIBUTING.md` § Strict rules](../../CONTRIBUTING.md#strict-rules--non-negotiables) rule 7.
**Scope:** The two MIDI-stack packages whose exact versions affect the byte-level wire format the Elektron Analog Rytm MK2 receives.

## The rule

Two packages are exact-version-pinned in `pyproject.toml`:

```toml
dependencies = [
    "mido==1.3.3",
    "python-rtmidi==1.5.8",
    ...
]
```

**Do not bump these versions** — not for a CVE, not for a Python version bump, not for a transitive-dep complaint from pip-audit, not because dependabot opened a PR. Bumps require explicit user approval AND hardware re-validation against a physical Analog Rytm MK2.

## Why

These two packages encode the **byte-level MIDI wire format** the Rytm hardware accepts over the cable:

- `mido==1.3.3` is the message-construction layer. The exact byte sequence it produces for `Message('control_change', channel=0, control=74, value=42)` has been validated against the live Rytm MK2 in V1.34. A newer mido may format identically — but until that's validated on hardware, the parity guarantee breaks.
- `python-rtmidi==1.5.8` is the C-extension layer that talks to the OS MIDI driver (ALSA on Linux, CoreMIDI on macOS, WinMM/MMSystem on Windows). Newer versions have known regressions on Windows where the MIDI driver hand-off introduces inter-byte gaps that the Rytm MK2 firmware sometimes interprets as separate messages. This was observed during V1.34 validation in early 2025.

A version bump that "works on my machine" can silently break wire-format on a real Rytm — and the test suite cannot catch it, because the suite uses `MockMidiSender`, not the real hardware. The only check that catches a regression is a hardware validation pass against the device.

## What you MUST do

- **Leave `pyproject.toml` `dependencies` alone** for these two packages.
- **Suppress dependabot PRs** that target them (see `.github/dependabot.yml` ignore list, if added).
- **If pip-audit reports a CVE on a pinned version:**
  1. Confirm the CVE doesn't affect the project's use of the library (most CVEs are in code paths the project doesn't exercise — e.g. server-side parsers).
  2. Document the CVE + analysis in `docs/SECURITY.md` or `SECURITY.md`.
  3. Coordinate with the user / @buzzijose-hub before any bump. **Never bump unilaterally.**
- **If a Python version bump (CI matrix) requires bumping mido or python-rtmidi** (e.g. the pinned version no longer has a wheel on the new Python), open an issue describing the conflict; do NOT bump and ship. The CI matrix is pinned at py3.11 currently; this is a real constraint.

## What you MUST NOT do

- **Do not** include `mido` or `python-rtmidi` in any "auto-bump latest" tooling output (renovate, dependabot auto-merge, `pip install --upgrade`).
- **Do not** use the latest mido API surface (`message.bin()` improvements, new metadata fields). The project sticks to the 1.3.3 API exactly.
- **Do not** wrap mido's `Message` construction in a way that depends on internal mido behavior. Use the project's `mock_midi.build_cc_message()` + `real_midi_adapter.RealMidiSender` boundaries.

## Exceptions

The only way to legitimately bump these versions is:

1. User-initiated proposal (issue or PR).
2. Hardware validation pass per [`docs/MANUAL_HARDWARE_VALIDATION.md`](../../docs/MANUAL_HARDWARE_VALIDATION.md) — operator runs the V1.34 reference command sequence against a real Rytm MK2 and confirms output matches goldens byte-for-byte.
3. Bump applied to `pyproject.toml` + this rule updated with the new pinned version + the validation evidence linked.

This is not a paperwork hurdle — it is the only known way to catch wire-format regressions, because the test suite is mock-only.

## Adjacent dependencies (not pinned, but watch them)

These pull in mido / python-rtmidi as transitive deps OR interact with the MIDI boundary:

- `pytest-xdist` — affects test parallelization; if it interferes with `MockMidiSender` recording order, tests get flaky. Currently safe; flag if it changes.
- `pytest` itself — fixture-collection order changes have rarely shifted parity test results. Currently safe.
- Python interpreter version — sticking to py3.11 keeps mido + python-rtmidi wheels stable. A py3.12 / py3.13 jump may force a pinned-version bump.

## When this rule applies

- Any PR that touches `pyproject.toml` `[project] dependencies`.
- Any PR that adds, removes, or modifies imports of `mido` or `python-rtmidi`.
- Any dependabot or renovate PR.
- Any CVE remediation pass that proposes a version bump.

## Cross-references

- [`pyproject.toml`](../../pyproject.toml) — the source of truth for the pins.
- [`docs/MANUAL_HARDWARE_VALIDATION.md`](../../docs/MANUAL_HARDWARE_VALIDATION.md) — the hardware-validation procedure.
- [`CONTRIBUTING.md` Strict rule 7](../../CONTRIBUTING.md#strict-rules--non-negotiables) — the contributor-facing version of this rule.
- `.claude/skills/learned/pip-audit-editable-install/SKILL.md` — running pip-audit cleanly with the hardware pins.
- `.github/dependabot.yml` — dependabot ignore list for these packages.

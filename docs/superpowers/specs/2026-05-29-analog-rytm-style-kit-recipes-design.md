# Analog Rytm Style Kit Recipes Design

## Purpose

Add curated, named Analog Rytm MKII style-kit recipes that can render a full
12-pad kit and send it through the existing explicit `--dry-run` / `--arm`
application boundary.

The feature is for musical direction, not artist cloning. Recipe names describe
feel and pressure: Detroit depth, rolling hypnosis, hard-groove drive, warehouse
force, and high-speed minimal urgency.

## Scope

This slice adds deterministic curated recipes and an active sender for them. It
does not add free-text prompt parsing, sample-slot selection, performance macro
programming, transport, pattern changes, kit save/project write behavior,
SysEx writes, unattended sends, or NRPN sending. The first active version sends
CC MSB messages only.

## Command Shape

Dry run:

```powershell
python -m rytm_randomizer.app --dry-run --rytm-kit-style detroit-deep
```

Armed hardware send:

```powershell
python -m rytm_randomizer.app --arm --rytm-kit-style detroit-deep --confirm-rytm-kit-send
```

The armed path must refuse to run without `--confirm-rytm-kit-send`.

## Recipes

Initial curated styles:

- `detroit-deep`
- `deeper-rolling`
- `hard-groove`
- `banging-warehouse`
- `hypnotic-pressure`
- `mills-drive`

Every recipe covers pads 1 through 12. Each pad chooses a legal machine from
`data/rytm_machine_catalog.py`, emits a machine-select CC15 event, then emits
manual-backed parameter events from `data/analog_rytm_midi.py`.

## Safety Boundary

Allowed in this slice:

- Track machine type via CC15, because full kit generation requires selecting
  machines.
- Machine SRC tone parameters except source `Level`.
- Filter parameters.
- Amp shaping parameters and amp delay/reverb sends, except `Amp Volume`.
- LFO parameters except `LFO Destination`.

Excluded in this slice:

- Samples and sample slots.
- Performance macros.
- Track level, track mute, track solo.
- Source `Level`.
- `Amp Volume`.
- Global FX mix/output level controls.
- Transport, clock, pattern/project/kit writes, and SysEx.

High-risk rows may appear only when a recipe explicitly needs them and the
sender is behind `--arm --confirm-rytm-kit-send`. The first recipes keep
volume-like rows out entirely.

## Architecture

- Add `rytm_randomizer/data/analog_rytm_style_recipes.py` for pure recipe facts
  and renderer helpers.
- Re-export `ANALOG_RYTM_STYLE_RECIPES` from `data/__init__.py`.
- Extend `rytm_randomizer/app.py` with `--rytm-kit-style` and
  `--confirm-rytm-kit-send`.
- Reuse `midi_io.send_cc` for both mock and real sends.
- Reuse the existing mido provider, output-port prompt, and close behavior.

## Validation

Tests pin that every curated recipe:

- Covers all 12 pads.
- Selects only legal pad/machine combinations.
- Resolves only manual-backed CC MSB rows.
- Avoids samples, performance macros, source level, track level, and amp volume.
- Produces deterministic rendered messages.
- Dry-runs without importing real MIDI libraries.
- Refuses armed sends without explicit confirmation.
- Sends the expected fake mido messages when armed under the test seam.

## Success Criteria

- A user can dry-run any curated Rytm kit style and see the full rendered event
  count.
- A user can intentionally arm and send a curated Rytm kit style with one extra
  confirmation flag.
- The command always closes the output port.
- Existing passive defaults and parity behavior remain unchanged.

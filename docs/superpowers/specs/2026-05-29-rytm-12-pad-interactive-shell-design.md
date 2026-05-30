# Analog Rytm 12-Pad Interactive Shell Design

## Purpose

Add an all-12-pad interactive mutation shell for the Analog Rytm MKII. This is
the 12-pad counterpart to the older V1.34 interactive command surface, but it
does not stretch that 4-pad runtime. It starts from the curated 12-pad style
recipes and lets the operator apply role-aware mutations across every pad.

## Operator Shape

Dry-run:

```powershell
python -m rytm_randomizer.app --dry-run --rytm-12-pad-shell
```

Armed hardware:

```powershell
python -m rytm_randomizer.app --arm --rytm-12-pad-shell --confirm-rytm-12-pad-send
```

The shell accepts compact commands:

- `styles` / `ls` lists curated 12-pad style anchors.
- `load <style>` loads a style anchor into the shell state.
- `preview` / `p` shows the currently staged full-kit plan.
- `send` / `s` sends the staged full-kit plan.
- `roll` / `r` applies a rolling mutation.
- `deep` / `d` applies a deeper mutation.
- `grit` / `g` applies a grit mutation.
- `intense` / `i` applies an intense mutation.
- `warehouse` / `w` applies a warehouse mutation.
- `undo` / `u` returns to the previous staged plan.
- `reset` / `z` returns to the loaded style anchor.
- `help` / `?` shows commands.
- `quit` / `q` exits.

## Safety Boundary

The first shell version is absolute-value, CC-MSB only, and recipe-grounded.
It does not parse free text, read samples, write performance macros, write
SysEx, save kits, change patterns, use transport, or touch track/source/amp
volume rows.

The kick-filter hardware finding is now a hard constraint: any mutation that
encounters a BD machine `Filter Frequency` keeps it at or below the sub-safe
ceiling. Mutations must affect all 12 pads, but they must do it by role:
kicks, snares, toms, hats, cymbals/bells, and synth/utility pads receive
different value movements.

## Architecture

Add a new engine module under `rytm_randomizer/engines/`:

- The module owns pure mutation helpers and an interactive shell class.
- It consumes `AnalogRytmRenderedStyleEvent` values produced by
  `data/analog_rytm_style_recipes.py`.
- It sends through `midi_io.send_cc` only when the operator uses `send`.
- It receives an already-created sender from `app.py`; it never opens ports or
  imports real MIDI libraries.

`rytm_randomizer.app` owns the active boundary:

- `--dry-run --rytm-12-pad-shell` creates a `MockMidiSender`.
- `--arm --rytm-12-pad-shell --confirm-rytm-12-pad-send` opens one selected
  Rytm output, runs the shell, and closes the port.
- `--arm --rytm-12-pad-shell` without confirmation refuses before listing or
  opening any MIDI port.

## Mutation Semantics

The first command set is deterministic and reversible inside the shell session.
Each mutation transforms the currently staged plan and stores the previous plan
for one-level undo.

Every mutation skips machine-select events. It mutates source/manual parameter
events with role-specific deltas and clamps every value to `[0, 127]`.

BD filter frequency never rises above `32`; if a loaded or mutated BD event is
above that ceiling, the shell clamps it to `25`.

## Validation

Tests cover:

- Loading `detroit-deep` produces all 12 pads and no sent messages.
- Each mutation changes at least one non-machine event on every pad.
- BD `Filter Frequency` stays sub-safe after every mutation.
- Preview includes style name, mutation state, pad count, and event count.
- `send` sends the staged plan to the injected sender.
- `undo` and `reset` restore the expected staged plan.
- Dry-run app mode imports no real MIDI library.
- Armed app mode requires `--confirm-rytm-12-pad-send` before touching ports.
- Armed app mode runs against fake mido, sends messages, and closes the port.

## Success Criteria

The operator can launch an all-12-pad shell, load a curated style, mutate it
across every pad, preview the plan, send it, undo, and reset. Dry-run remains
hardware-free. Armed sends require both `--arm` and
`--confirm-rytm-12-pad-send`.

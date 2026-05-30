# Analog Rytm Snapshot Shell Design

## Goal

Build the first live-safe all-12-pad snapshot performance shell for Analog Rytm
MKII. The operator provides a current-kit SysEx dump, the shell treats that dump
as the anchor, and old V1.34-style commands mutate all 12 pads from that anchor.

## First Version Scope

This first version is live-safe only:

- Use a current-kit `.syx` file as the session anchor.
- Cover all 12 pads.
- Keep machine switching off by default.
- Send only CC MSB values through the existing sender boundary.
- Support the old performance vocabulary: `S1A`, `S3A`, `S3B`, `S4B`, `4`,
  `Y`, `V`, `N`, `Z`, `U`, `preview`, `send`, and `Q`.
- Support depth prompts for `Y`, `V`, and `N`: `micro`, `groove`, `strong`.
- Keep samples, performance macros, source level, track level, amp volume,
  SysEx writes, transport, pattern changes, kit saves, and project writes out
  of scope.

## Data Model

The manual-backed Rytm MIDI catalog provides parameter identity: CC number,
NRPN address, section, name, risk, and mutation status. The kit SysEx dump
provides current values. The first implementation promotes only the current
values that are already structurally supported by the observed kit layout:

- Current machine value per pad.
- General per-track rows whose NRPN LSB maps directly to the track sound record:
  filter, amp shaping/sends/pan, and LFO safe rows.
- Machine SRC parameters for the current machine where the manual-backed catalog
  has promoted mappings.

Rows outside this promoted subset remain untouched.

## Shell Behavior

The shell starts with the captured snapshot anchor already loaded. It does not
require `load <style>`. Commands mutate a staged plan; `send` is the only command
that writes to the injected sender.

`Z` restores the captured anchor for promoted safe rows. `U` restores the
previous staged plan. `preview` prints the current mutation, event count, pads
touched, and pad 1 kick filter values so the operator can catch a bad plan before
arming hardware.

## Safety

The dry-run path must import no real MIDI library and open no port. The armed
path must require `--confirm-rytm-snapshot-shell-send` before listing or opening
real output ports. Tests must use fake/mocked MIDI only.

Pad 1 kick guardrails remain stricter than the rest of the kit. Live-safe
mutations keep kick filter frequency near the captured anchor and never jump to
the midrange unless the captured anchor itself is already there.

## Commands

Dry-run:

```powershell
python -m rytm_randomizer.app --dry-run --rytm-snapshot-shell captures\current-kit.syx
```

Armed:

```powershell
python -m rytm_randomizer.app --arm --rytm-snapshot-shell captures\current-kit.syx --confirm-rytm-snapshot-shell-send
```

## Acceptance Criteria

- A valid captured Rytm kit dump starts the shell with all 12 pads anchored.
- `S1A`, `S3A`, `S3B`, `S4B`, and `4` mutate all 12 pads without machine
  switching.
- `Y`, `V`, and `N` prompt for depth and apply section-focused mutations.
- `Z` returns promoted rows to the captured anchor.
- `send` sends the current staged events through the injected sender only.
- Dry-run never imports `mido`, `rtmidi`, or `pythonrtmidi`.
- Armed mode refuses to list or open ports without the explicit confirmation
  flag.
